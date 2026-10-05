import { useCallback, useEffect, useRef } from 'react';
import type { Anchor, Document } from './contracts';

export function displayedBox(
  box: number[],
  width: number,
  height: number,
  rotation: number,
): number[] {
  const [x0, y0, x1, y1] = box;
  if (rotation === 90) return [width - y1, x0, width - y0, x1];
  if (rotation === 180) return [width - x1, height - y1, width - x0, height - y0];
  if (rotation === 270) return [y0, height - x1, y1, height - x0];
  return box;
}

export function SourcePanel({
  document,
  paperId,
  pageNumber,
  anchor,
  onPage,
  onSpan,
}: {
  document: Document;
  paperId: string;
  pageNumber: number;
  anchor: Anchor | null;
  onPage: (page: number) => void;
  onSpan: (id: string) => void;
}) {
  const highlight = useRef<HTMLDivElement>(null);
  const pdfScroll = useRef<HTMLDivElement>(null);
  const textScroll = useRef<HTMLDivElement>(null);
  const scrollToEvidence = useCallback(() => {
    requestAnimationFrame(() => {
      const target = highlight.current;
      const pane = pdfScroll.current;
      if (target && pane) pane.scrollTop = Math.max(0, target.offsetTop - pane.clientHeight / 3);
      const text = textScroll.current;
      const selected = text?.querySelector<HTMLButtonElement>('.source-span.active');
      if (text && selected) text.scrollTop = Math.max(0, selected.offsetTop - text.offsetTop - 20);
    });
  }, []);
  const page = document.pages.find((p) => p.number === pageNumber);
  useEffect(() => {
    scrollToEvidence();
  }, [anchor?.id, pageNumber, scrollToEvidence]);
  if (!page)
    return (
      <section className="source-panel">
        <p className="muted">Original pages appear after parsing.</p>
      </section>
    );
  const box =
    anchor?.page_number === pageNumber
      ? displayedBox(anchor.bbox, page.width, page.height, page.rotation)
      : null;
  return (
    <section className="source-panel" aria-label="Original source">
      <div className="panel-title">
        <span>ORIGINAL SOURCE</span>
        <div className="page-controls">
          <button
            aria-label="Previous page"
            disabled={pageNumber <= 1}
            onClick={() => onPage(pageNumber - 1)}
          >
            ‹
          </button>
          <label>
            Page{' '}
            <select
              aria-label="PDF page"
              value={pageNumber}
              onChange={(e) => onPage(Number(e.target.value))}
            >
              {document.pages.map((p) => (
                <option key={p.number}>{p.number}</option>
              ))}
            </select>{' '}
            / {document.pages.length}
          </label>
          <button
            aria-label="Next page"
            disabled={pageNumber >= document.pages.length}
            onClick={() => onPage(pageNumber + 1)}
          >
            ›
          </button>
          <a
            href={`/api/papers/${paperId}/pdf#page=${pageNumber}`}
            target="_blank"
            rel="noreferrer"
          >
            Open PDF ↗
          </a>
        </div>
      </div>
      <div className="source-body">
        <div ref={pdfScroll} className="pdf-scroll">
          <div className="pdf-page" style={{ aspectRatio: `${page.width} / ${page.height}` }}>
            <img
              src={`/api/papers/${paperId}/pages/${pageNumber}/image`}
              alt={`Original PDF page ${pageNumber}`}
              onLoad={scrollToEvidence}
            />
            {box && (
              <div
                ref={highlight}
                className="source-highlight"
                data-testid="source-highlight"
                style={{
                  left: `${(100 * box[0]) / page.width}%`,
                  top: `${(100 * box[1]) / page.height}%`,
                  width: `${(100 * (box[2] - box[0])) / page.width}%`,
                  height: `${(100 * (box[3] - box[1])) / page.height}%`,
                }}
              />
            )}
          </div>
        </div>
        <div ref={textScroll} className="source-text">
          <p className="eyebrow">EXTRACTED TEXT · CLICK TO EXPLORE</p>
          {page.spans.map((span) => (
            <button
              className={`source-span ${span.id === anchor?.span_id ? 'active' : ''}`}
              key={span.id}
              onClick={() => onSpan(span.anchor_id)}
            >
              {span.text}
            </button>
          ))}
          {!page.spans.length && <p>No extractable text on this page. OCR is not configured.</p>}
        </div>
      </div>
    </section>
  );
}
