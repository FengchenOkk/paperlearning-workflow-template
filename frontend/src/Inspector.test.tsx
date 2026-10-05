// @vitest-environment jsdom
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { EvidenceBundle, Paper } from './contracts';
import { Inspector } from './Inspector';

afterEach(cleanup);
const id = '00000000-0000-0000-0000-000000000001';
const anchorId = '00000000-0000-0000-0000-000000000002';
const paper: Paper = {
  id,
  title: 'Isolated UI fixture',
  source_hash: '0'.repeat(64),
  page_count: 1,
  created_at: '2026-10-05',
  job_id: id,
};
function inspect(
  scientific_object: EvidenceBundle['scientific_object'],
  type: EvidenceBundle['node']['type'],
) {
  const bundle: EvidenceBundle = {
    node: {
      id,
      paper_id: id,
      type,
      layer: type === 'CLAIM' ? 'ARGUMENT' : 'SOURCE',
      label: 'Source candidate',
      text: 'Controlled fixture source wording.',
      epistemic_status: 'AUTHOR_CLAIM',
      verification_status: 'VERIFIED',
      review_current: true,
      verification_scope: 'SOURCE_ATTRIBUTION',
      confidence: 0.6,
      uncertainty_reason: 'Scientific meaning has not been assessed.',
      provenance: [anchorId],
      created_by: 'test-only',
      model: 'none',
      prompt_version: 'none',
      created_at: '2026-10-05',
      updated_at: '2026-10-05',
      version: 2,
    },
    evidence: [],
    scientific_object,
  };
  render(
    <Inspector
      bundle={bundle}
      paper={paper}
      onAnchor={vi.fn()}
      onExpand={vi.fn()}
      onVerify={vi.fn()}
    />,
  );
}

describe('scientific inspector integrity', () => {
  it('keeps source verification separate from claim support', () => {
    inspect(
      {
        kind: 'CLAIM',
        node_id: id,
        source_anchor_id: anchorId,
        claim_type: 'CLAIM',
        qualifiers: [],
        support_strength: 'NOT_ASSESSED',
        assumption_node_ids: [],
        evidence_node_ids: [],
      },
      'CLAIM',
    );
    expect(screen.getByText('SOURCE ATTRIBUTION')).toBeTruthy();
    expect(screen.getByText('Scientific support: NOT ASSESSED')).toBeTruthy();
    expect(screen.getByRole('region', { name: 'Claim structure' })).toBeTruthy();
  });
  it('does not invent equation LaTeX or derivation from extracted text', () => {
    inspect(
      {
        kind: 'EQUATION',
        node_id: id,
        source_anchor_id: anchorId,
        original_expression: 'x = y',
        equation_number: null,
        normalized_expression: null,
        latex: null,
        symbols: [],
        mathematical_meaning: null,
        physical_meaning: null,
        definition_node_ids: [],
        assumption_node_ids: [],
        approximation_node_ids: [],
        derivation_edge_ids: [],
        used_by_node_ids: [],
      },
      'EQUATION',
    );
    expect(screen.getByText('LaTeX: Not reconstructed')).toBeTruthy();
    expect(screen.getByText('Equation (number unknown)')).toBeTruthy();
  });
  it('labels a localized caption without implying visual analysis', () => {
    inspect(
      {
        kind: 'FIGURE',
        node_id: id,
        source_anchor_id: anchorId,
        figure_number: '1',
        caption_explicit: 'A test caption.',
        visual_anchor_id: null,
        surrounding_text: [],
        visual_observations: [],
        interpretations: [],
        observation_node_ids: [],
        claim_node_ids: [],
      },
      'FIGURE',
    );
    expect(screen.getByText('Caption explicitly states: A test caption.')).toBeTruthy();
    expect(screen.getByText(/Figure image region.*have not been established/)).toBeTruthy();
  });
});
