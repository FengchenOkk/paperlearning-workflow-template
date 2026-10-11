"""Add source typography observations without rewriting text or existing reviews.

Revision ID: 35c8d2ea0003
Revises: 24b7c1d9a002
"""

import sqlalchemy as sa
from alembic import op

revision = "35c8d2ea0003"
down_revision = "24b7c1d9a002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "source_spans", sa.Column("section_titles", sa.JSON(), nullable=False, server_default="[]")
    )
    op.add_column(
        "source_spans", sa.Column("notation", sa.JSON(), nullable=False, server_default="[]")
    )
    op.add_column(
        "source_spans", sa.Column("notation_issues", sa.JSON(), nullable=False, server_default="[]")
    )


def downgrade() -> None:
    op.drop_column("source_spans", "section_titles")
    op.drop_column("source_spans", "notation_issues")
    op.drop_column("source_spans", "notation")
