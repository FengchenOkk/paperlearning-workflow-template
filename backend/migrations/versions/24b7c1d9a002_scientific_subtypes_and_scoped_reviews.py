"""Add scientific node subtypes and scoped reviews without replacing existing graph rows."""

import re

import sqlalchemy as sa
from alembic import op

revision = "24b7c1d9a002"
down_revision = "10f9a4e1b6e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "source_anchors",
        sa.Column(
            "localization_precision", sa.String(), nullable=False, server_default="TEXT_BLOCK"
        ),
    )
    for table in ("knowledge_nodes", "knowledge_edges"):
        op.add_column(table, sa.Column("verification_scope", sa.String(), nullable=True))
    op.add_column(
        "knowledge_edges",
        sa.Column("epistemic_status", sa.String(), nullable=False, server_default="UNVERIFIED"),
    )
    op.execute(
        "UPDATE knowledge_edges SET epistemic_status='PAPER_EXPLICIT' WHERE relation_type='CONTAINS' AND created_by='document-parser'"
    )
    op.add_column(
        "verification_records",
        sa.Column("scope", sa.String(), nullable=False, server_default="SOURCE_ATTRIBUTION"),
    )
    # Old decisions are preserved, but never silently promoted to a new scoped scientific review.
    op.execute("UPDATE verification_records SET scope='LEGACY_UNSCOPED'")
    op.add_column("verification_records", sa.Column("scientific_basis", sa.Text(), nullable=True))
    op.add_column(
        "verification_records", sa.Column("evidence_fingerprint", sa.String(64), nullable=True)
    )
    op.create_table(
        "claims",
        sa.Column("node_id", sa.String(36), sa.ForeignKey("knowledge_nodes.id"), primary_key=True),
        sa.Column(
            "source_anchor_id", sa.String(36), sa.ForeignKey("source_anchors.id"), nullable=False
        ),
        sa.Column("claim_type", sa.String(), nullable=False),
        sa.Column("qualifiers", sa.JSON(), nullable=False),
        sa.Column("support_strength", sa.String(), nullable=False),
    )
    op.create_table(
        "equations",
        sa.Column("node_id", sa.String(36), sa.ForeignKey("knowledge_nodes.id"), primary_key=True),
        sa.Column(
            "source_anchor_id", sa.String(36), sa.ForeignKey("source_anchors.id"), nullable=False
        ),
        sa.Column("equation_number", sa.String(), nullable=True),
        sa.Column("normalized_expression", sa.Text(), nullable=True),
        sa.Column("latex", sa.Text(), nullable=True),
        sa.Column("symbols", sa.JSON(), nullable=False),
        sa.Column("mathematical_meaning", sa.JSON(), nullable=True),
        sa.Column("physical_meaning", sa.JSON(), nullable=True),
    )
    op.create_table(
        "figures",
        sa.Column("node_id", sa.String(36), sa.ForeignKey("knowledge_nodes.id"), primary_key=True),
        sa.Column(
            "source_anchor_id", sa.String(36), sa.ForeignKey("source_anchors.id"), nullable=False
        ),
        sa.Column("figure_number", sa.String(), nullable=True),
        sa.Column(
            "visual_anchor_id", sa.String(36), sa.ForeignKey("source_anchors.id"), nullable=True
        ),
        sa.Column("surrounding_text", sa.JSON(), nullable=False),
        sa.Column("visual_observations", sa.JSON(), nullable=False),
        sa.Column("interpretations", sa.JSON(), nullable=False),
    )
    connection = op.get_bind()
    metadata = sa.MetaData()
    nodes = sa.Table("knowledge_nodes", metadata, autoload_with=connection)
    anchors = sa.Table("source_anchors", metadata, autoload_with=connection)
    tables = {
        name: sa.Table(name, metadata, autoload_with=connection)
        for name in ("claims", "equations", "figures")
    }
    for node in connection.execute(
        sa.select(nodes).where(
            nodes.c.type.in_(["CLAIM", "RESULT", "CONCLUSION", "HYPOTHESIS", "EQUATION", "FIGURE"])
        )
    ).mappings():
        ids = node["provenance"]
        if not ids:
            continue
        anchor = connection.execute(
            sa.select(anchors).where(anchors.c.id == ids[0], anchors.c.paper_id == node["paper_id"])
        ).first()
        if anchor is None:
            continue  # Missing evidence is an integrity error, never guessed by migration.
        fields = {"node_id": node["id"], "source_anchor_id": ids[0]}
        if node["type"] == "EQUATION":
            number = re.search(r"\((\d+[a-z]?)\)\s*$", " ".join(node["text"].split()))
            fields.update(
                equation_number=number[1] if number else None,
                normalized_expression=None,
                latex=None,
                symbols=[],
                mathematical_meaning=None,
                physical_meaning=None,
            )
            table = tables["equations"]
        elif node["type"] == "FIGURE":
            number = re.match(r"(?i)^fig(?:ure)?\.?\s*(\d+)", " ".join(node["text"].split()))
            fields.update(
                figure_number=number[1] if number else None,
                visual_anchor_id=None,
                surrounding_text=[],
                visual_observations=[],
                interpretations=[],
            )
            table = tables["figures"]
        else:
            fields.update(claim_type=node["type"], qualifiers=[], support_strength="NOT_ASSESSED")
            table = tables["claims"]
        connection.execute(table.insert().values(**fields))


def downgrade() -> None:
    raise RuntimeError(
        "This migration adds scientific records; restore a reviewed backup instead of dropping them"
    )
