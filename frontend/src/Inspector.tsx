import { useState } from 'react';
import type { Anchor, EvidenceBundle, Paper, Verification } from './contracts';

export function Inspector({
  bundle,
  paper,
  onAnchor,
  onExpand,
  onVerify,
}: {
  bundle: EvidenceBundle | null;
  paper: Paper | null;
  onAnchor: (anchor: Anchor) => void;
  onExpand: () => void;
  onVerify: (review: Verification) => Promise<void>;
}) {
  const [reviewing, setReviewing] = useState(false);
  const [reviewer, setReviewer] = useState('');
  const [reason, setReason] = useState('');
  const [decision, setDecision] = useState<Verification['decision']>('DISPUTED');
  const [scope, setScope] = useState<NonNullable<Verification['scope']>>('SOURCE_ATTRIBUTION');
  const [scientificBasis, setScientificBasis] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  if (!bundle || !paper)
    return (
      <aside className="inspector">
        <div className="panel-title">SCIENTIFIC INSPECTOR</div>
        <div className="inspector-empty">
          <span className="crosshair">⌖</span>
          <h3>Follow the evidence</h3>
          <p>Select a node to inspect its source, scientific status and uncertainty.</p>
        </div>
      </aside>
    );
  const node = bundle.node;
  return (
    <aside className="inspector" aria-label="Scientific inspector">
      <div className="panel-title">
        SCIENTIFIC INSPECTOR <span>v{node.version}</span>
      </div>
      <div className="inspector-content">
        <p className="eyebrow">
          {node.type.replaceAll('_', ' ')} · {node.layer}
        </p>
        <h2>{node.label}</h2>
        <div className="badges">
          <span
            className={
              node.verification_status === 'VERIFIED' && node.review_current === true
                ? 'verified'
                : 'candidate'
            }
          >
            {node.verification_status === 'VERIFIED' && node.review_current !== true
              ? 'REVIEW RECHECK REQUIRED'
              : node.verification_status}
          </span>
          <span>{node.epistemic_status.replaceAll('_', ' ')}</span>
          {node.verification_scope && <span>{node.verification_scope.replaceAll('_', ' ')}</span>}
        </div>
        <h4>Source wording / annotation</h4>
        <p className="node-text">{node.text}</p>
        <h4>Uncertainty</h4>
        {node.review_current === false && (
          <p className="muted">
            Stored review is stale, unscoped or inconsistent. Recheck current evidence.
          </p>
        )}
        <p className="muted">{node.uncertainty_reason || 'No additional uncertainty recorded.'}</p>
        <p className="confidence">
          Extraction confidence {Math.round(node.confidence * 100)}% · confidence does not verify a
          claim
        </p>
        {bundle.scientific_object?.kind === 'CLAIM' && (
          <section aria-label="Claim structure">
            <h4>Claim structure</h4>
            <p>Type: {bundle.scientific_object.claim_type}</p>
            <p>
              Scientific support: {bundle.scientific_object.support_strength.replaceAll('_', ' ')}
            </p>
            <p className="muted">
              Source attribution records what the paper says. Support strength and assumptions have
              not been assessed.
            </p>
          </section>
        )}
        {bundle.scientific_object?.kind === 'EQUATION' && (
          <section aria-label="Equation structure">
            <h4>Equation {bundle.scientific_object.equation_number ?? '(number unknown)'}</h4>
            <p>LaTeX: {bundle.scientific_object.latex ?? 'Not reconstructed'}</p>
            {bundle.scientific_object.mathematical_meaning && (
              <p>
                Mathematical meaning ·{' '}
                {bundle.scientific_object.mathematical_meaning.epistemic_status}:{' '}
                {bundle.scientific_object.mathematical_meaning.text}
              </p>
            )}
            {bundle.scientific_object.physical_meaning && (
              <p>
                Physical meaning · {bundle.scientific_object.physical_meaning.epistemic_status}:{' '}
                {bundle.scientific_object.physical_meaning.text}
              </p>
            )}
            <p className="muted">
              Original expression preserved above. Symbols, assumptions, meanings and derivations
              require separate analysis.
            </p>
          </section>
        )}
        {bundle.scientific_object?.kind === 'FIGURE' && (
          <section aria-label="Figure evidence channels">
            <h4>Figure {bundle.scientific_object.figure_number ?? '(number unknown)'}</h4>
            <p>Caption explicitly states: {bundle.scientific_object.caption_explicit}</p>
            {bundle.scientific_object.surrounding_text.map((statement, index) => (
              <p key={`surrounding-${index}`}>
                Surrounding text · {statement.epistemic_status}: {statement.text}
              </p>
            ))}
            {bundle.scientific_object.interpretations.map((statement, index) => (
              <p key={`interpretation-${index}`}>
                Interpretation · {statement.epistemic_status}: {statement.text}
              </p>
            ))}
            <p className="muted">
              Caption block localized. Figure image region and visual observations have not been
              established. Missing analysis fields remain unknown.
            </p>
          </section>
        )}
        <h4>
          Evidence <span className="muted">{bundle.evidence.length}</span>
        </h4>
        {bundle.evidence.map((e) => (
          <button key={e.id} className="evidence" onClick={() => onAnchor(e.anchor)}>
            <span>↗ Page {e.anchor.page_number} · original text block</span>
            <blockquote>{e.anchor.text}</blockquote>
            <small>{e.note}</small>
          </button>
        ))}
        {!bundle.evidence.length && (
          <p className="muted">
            No evidence is stored. This object cannot be scientifically verified.
          </p>
        )}
        <h4>Explore</h4>
        <button onClick={onExpand}>Focus stored neighborhood</button>
        <p className="muted small">
          Only stored relations are shown. Prerequisite and innovation engines are pending.
        </p>
        <details>
          <summary>Provenance</summary>
          <p className="small">
            Created by {node.created_by}
            <br />
            Model: {node.model}
            <br />
            Prompt: {node.prompt_version}
            <br />
            {node.created_at}
          </p>
        </details>
        {node.type !== 'PAPER' && (
          <button
            className="review-button"
            onClick={() => {
              setReviewing(!reviewing);
              setError('');
            }}
          >
            Review scientific status
          </button>
        )}
        {reviewing && (
          <form
            className="review-form"
            onSubmit={async (e) => {
              e.preventDefault();
              setSaving(true);
              setError('');
              try {
                await onVerify({
                  decision,
                  reviewer,
                  reason,
                  source_hash: paper.source_hash,
                  expected_version: node.version,
                  scope,
                  scientific_basis:
                    scope === 'SCIENTIFIC_VALIDITY' ? scientificBasis || null : null,
                });
                setReviewing(false);
              } catch (error) {
                setError(error instanceof Error ? error.message : 'Review failed');
              } finally {
                setSaving(false);
              }
            }}
          >
            <p>
              Record your judgment after checking the original evidence. This is a human review, not
              an independent model verdict.
            </p>
            <label>
              Reviewer
              <input required value={reviewer} onChange={(e) => setReviewer(e.target.value)} />
            </label>
            <label>
              Decision
              <select
                value={decision}
                onChange={(e) => setDecision(e.target.value as Verification['decision'])}
              >
                <option>DISPUTED</option>
                <option>VERIFIED</option>
                <option>REJECTED</option>
              </select>
            </label>
            <label>
              Review scope
              <select
                value={scope}
                onChange={(e) => setScope(e.target.value as NonNullable<Verification['scope']>)}
              >
                <option value="SOURCE_ATTRIBUTION">Source attribution</option>
                <option value="SCIENTIFIC_VALIDITY">Scientific validity</option>
              </select>
            </label>
            <p>
              Source attribution confirms wording and location. Scientific validity requires a
              separate assessment of evidence, assumptions and limits.
            </p>
            {scope === 'SCIENTIFIC_VALIDITY' && (
              <label>
                Scientific evidence assessment
                <textarea
                  required={decision === 'VERIFIED'}
                  minLength={20}
                  value={scientificBasis}
                  onChange={(e) => setScientificBasis(e.target.value)}
                />
              </label>
            )}
            <label>
              Reason
              <textarea
                required
                minLength={10}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
              />
            </label>
            {error && <p role="alert">{error}</p>}
            <button disabled={saving}>{saving ? 'Saving…' : 'Save review'}</button>
          </form>
        )}
      </div>
    </aside>
  );
}
