import { lazy, Suspense, useCallback, useEffect, useRef, useState } from 'react';
import type {
  Anchor,
  Document,
  EvidenceBundle,
  Graph,
  Job,
  Paper,
  SearchHit,
  Verification,
} from './contracts';
import { api } from './api';
import { Inspector } from './Inspector';
import { SourcePanel } from './SourcePanel';

const emptyGraph: Graph = { nodes: [], edges: [], total_nodes: 0, truncated: false };
const GraphCanvas = lazy(() =>
  import('./GraphCanvas').then((module) => ({ default: module.GraphCanvas })),
);

export function App() {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [paperId, setPaperId] = useState(localStorage.getItem('papergraph.paper') ?? '');
  const [paper, setPaper] = useState<Paper | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [document, setDocument] = useState<Document | null>(null);
  const [graph, setGraph] = useState<Graph>(emptyGraph);
  const [bundle, setBundle] = useState<EvidenceBundle | null>(null);
  const [anchor, setAnchor] = useState<Anchor | null>(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [view, setView] = useState('knowledge');
  const [limit, setLimit] = useState(40);
  const [query, setQuery] = useState('');
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [dark, setDark] = useState(localStorage.getItem('papergraph.theme') !== 'light');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [history, setHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const input = useRef<HTMLInputElement>(null);
  const selectionEpoch = useRef(0);

  useEffect(() => {
    api
      .papers()
      .then(setPapers)
      .catch((e) => setError(String(e)));
  }, []);
  useEffect(() => {
    localStorage.setItem('papergraph.theme', dark ? 'dark' : 'light');
  }, [dark]);

  useEffect(() => {
    if (!paperId) return;
    let disposed = false;
    let timer: ReturnType<typeof setTimeout>;
    selectionEpoch.current++;
    setBundle(null);
    setDocument(null);
    setAnchor(null);
    setGraph(emptyGraph);
    setHits([]);
    setHistory([]);
    setHistoryIndex(-1);
    setError('');
    setJob(null);
    setPaper(null);
    localStorage.setItem('papergraph.paper', paperId);
    async function poll() {
      const epoch = selectionEpoch.current;
      try {
        const p = await api.paper(paperId);
        const j = await api.job(p.job_id);
        if (disposed) return;
        setPaper(p);
        setJob(j);
        if (j.status === 'READY' || j.status === 'PARTIAL') {
          const [d, g] = await Promise.all([
            api.document(paperId),
            api.graph(paperId, view, limit),
          ]);
          if (disposed) return;
          setDocument(d);
          setGraph(g);
          const saved = localStorage.getItem(`papergraph.selection.${paperId}`);
          if (saved) {
            try {
              const restored = await api.evidence(saved);
              if (
                !disposed &&
                selectionEpoch.current === epoch &&
                restored.node.paper_id === paperId &&
                g.nodes.some((node) => node.id === saved)
              ) {
                setBundle(restored);
                const source = restored.evidence[0]?.anchor;
                if (source) {
                  setAnchor(source);
                  setPageNumber(source.page_number);
                }
              }
            } catch {
              localStorage.removeItem(`papergraph.selection.${paperId}`);
            }
          }
          setPapers((list) => list.map((old) => (old.id === p.id ? p : old)));
        } else if (j.status !== 'FAILED') timer = setTimeout(poll, 800);
      } catch (e) {
        if (!disposed) setError(e instanceof Error ? e.message : 'Unable to load paper');
      }
    }
    void poll();
    return () => {
      disposed = true;
      clearTimeout(timer);
    };
  }, [paperId, view, limit]);

  const selectNode = useCallback(async (id: string) => {
    const epoch = ++selectionEpoch.current;
    try {
      const evidence = await api.evidence(id);
      if (selectionEpoch.current !== epoch) return;
      setBundle(evidence);
      localStorage.setItem(`papergraph.selection.${evidence.node.paper_id}`, id);
      if (evidence.evidence[0]) {
        setAnchor(evidence.evidence[0].anchor);
        setPageNumber(evidence.evidence[0].anchor.page_number);
      }
    } catch (e) {
      if (selectionEpoch.current === epoch) setError(String(e));
    }
  }, []);

  const chooseNode = useCallback(
    (id: string) => {
      void selectNode(id);
      setHistoryIndex((index) => {
        setHistory((previous) => [...previous.slice(0, index + 1), id]);
        return index + 1;
      });
    },
    [selectNode],
  );

  function showAnchor(source: Anchor) {
    setAnchor(source);
    setPageNumber(source.page_number);
  }

  async function chooseSource(id: string, preferredNodeId?: string) {
    const epoch = ++selectionEpoch.current;
    try {
      const [source, nodes] = await Promise.all([api.anchor(id), api.associated(id)]);
      if (selectionEpoch.current !== epoch) return;
      const semantic =
        nodes.find((n) => n.id === preferredNodeId) ??
        nodes.find((n) => n.id === bundle?.node.id) ??
        nodes.find((n) => n.type !== 'PAPER') ??
        nodes[0];
      if (semantic) {
        const [evidence, expanded] = await Promise.all([
          api.evidence(semantic.id),
          graph.nodes.some((n) => n.id === semantic.id)
            ? Promise.resolve(null)
            : api.neighborhood(semantic.id, 1),
        ]);
        if (selectionEpoch.current !== epoch) return;
        setBundle(evidence);
        if (expanded) setGraph(expanded);
        localStorage.setItem(`papergraph.selection.${source.paper_id}`, semantic.id);
      } else setBundle(null);
      showAnchor(source);
    } catch (e) {
      if (selectionEpoch.current === epoch) setError(String(e));
    }
  }

  async function upload(file: File) {
    setUploading(true);
    setError('');
    try {
      const result = await api.upload(file);
      setPapers(await api.papers());
      setPaperId(result.paper.id);
      if (paperId === result.paper.id) setJob(result.job);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Upload failed');
    } finally {
      setUploading(false);
      if (input.current) input.current.value = '';
    }
  }

  async function verify(review: Verification) {
    if (!bundle) return;
    const epoch = selectionEpoch.current;
    await api.verify(bundle.node.id, review);
    if (selectionEpoch.current !== epoch) return;
    const [updated, projection] = await Promise.all([
      api.evidence(bundle.node.id),
      api.graph(paperId, view, limit),
    ]);
    if (selectionEpoch.current !== epoch) return;
    setBundle(updated);
    setGraph(projection);
  }

  return (
    <main className={dark ? 'workspace dark' : 'workspace light'}>
      <header className="topbar">
        <a className="brand" href="/">
          ⌘ <strong>PaperGraph</strong>
          <span>RESEARCH WORKSPACE</span>
        </a>
        <div className="top-actions">
          <span className="local-mode">
            <i />
            Local processing
          </span>
          <button onClick={() => setDark(!dark)} aria-label="Toggle theme">
            {dark ? '☀ Light' : '☾ Dark'}
          </button>
          <button
            className="upload-button"
            onClick={() => input.current?.click()}
            disabled={uploading}
          >
            {uploading ? 'Uploading…' : '+ Open PDF'}
          </button>
          <input
            ref={input}
            type="file"
            accept=".pdf,application/pdf"
            aria-label="Upload PDF"
            hidden
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) void upload(f);
            }}
          />
        </div>
      </header>
      {error && (
        <div role="alert" className="error-banner">
          {error}
          <button onClick={() => setError('')}>Dismiss</button>
        </div>
      )}
      <div className="workspace-toolbar">
        <div className="paper-title">
          {paper?.title ?? 'Scientific understanding, connected to evidence'}
        </div>
        <form
          className="search"
          onSubmit={async (e) => {
            e.preventDefault();
            if (!paperId || query.trim().length < 2) return;
            try {
              const epoch = selectionEpoch.current;
              const results = await api.search(paperId, query.trim());
              if (selectionEpoch.current === epoch) setHits(results);
            } catch (e) {
              setError(String(e));
            }
          }}
        >
          <input
            aria-label="Search paper and graph"
            placeholder="Search source, methods, equations…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button disabled={!paperId}>Search</button>
        </form>
      </div>
      <div className="main-grid">
        <nav className="navigator" aria-label="Paper navigator">
          <div className="panel-title">
            PAPERS <span>{papers.length}</span>
          </div>
          <div className="paper-list">
            {papers.map((p) => (
              <button
                className={p.id === paperId ? 'paper-item active' : 'paper-item'}
                key={p.id}
                onClick={() => setPaperId(p.id)}
              >
                <span>▤</span>
                {p.title}
              </button>
            ))}
          </div>
          {document && (
            <>
              <div className="panel-title">SOURCE STRUCTURE</div>
              <div className="section-list">
                {document.pages.flatMap((p) =>
                  p.spans
                    .filter((s) => s.kind === 'heading')
                    .map((s) => (
                      <button key={s.id} onClick={() => void chooseSource(s.anchor_id)}>
                        <span>{s.text}</span>
                        <small>{p.number}</small>
                      </button>
                    )),
                )}
              </div>
            </>
          )}
          <div className="navigator-note">
            <p className="eyebrow">EVIDENCE FIRST</p>
            <p>
              Original wording stays separate from interpretation. Candidate labels require review.
            </p>
          </div>
        </nav>
        <section className="graph-region">
          <div className="viewbar">
            <div className="view-tabs">
              {['knowledge', 'argument', 'innovation', 'learning'].map((v) => (
                <button key={v} className={view === v ? 'active' : ''} onClick={() => setView(v)}>
                  {v[0].toUpperCase() + v.slice(1)}
                </button>
              ))}
            </div>
            <select
              aria-label="Graph depth"
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
            >
              <option value={40}>Overview</option>
              <option value={80}>Standard</option>
              <option value={300}>Deep</option>
            </select>
          </div>
          {['argument', 'innovation'].includes(view) && (
            <p className="projection-note">
              Filtered candidates · {view} analysis has not been performed.
            </p>
          )}
          {!paperId ? (
            <div className="welcome">
              <div className="welcome-symbol">
                ○──○
                <br />╲ │ ╱<br />
                ○──○
              </div>
              <p className="eyebrow">PAPER → GRAPH → EVIDENCE</p>
              <h1>
                Read the structure.
                <br />
                Inspect the source.
              </h1>
              <p>
                Open a scientific PDF to explore its methods, results and original evidence in one
                connected workspace.
              </p>
              <button onClick={() => input.current?.click()}>Open a PDF</button>
              <small>Runs locally · No AI key required · No external document transmission</small>
            </div>
          ) : job && !['READY', 'PARTIAL'].includes(job.status) ? (
            <div className="processing">
              <p className="eyebrow">DOCUMENT PROCESSING</p>
              <h2>{job.status.replaceAll('_', ' ')}</h2>
              <progress value={job.progress} max={100} />
              <p>{job.error ?? 'A background worker parses and persists the original source.'}</p>
              {job.status === 'FAILED' && (
                <button
                  onClick={async () => {
                    try {
                      await api.retry(job.id);
                      setPaperId('');
                      setTimeout(() => setPaperId(paperId), 0);
                    } catch (e) {
                      setError(String(e));
                    }
                  }}
                >
                  Retry parsing
                </button>
              )}
            </div>
          ) : graph.nodes.length ? (
            <Suspense fallback={<div className="processing">Loading graph renderer…</div>}>
              <GraphCanvas
                graph={graph}
                selected={bundle?.node.id ?? ''}
                onSelect={chooseNode}
                dark={dark}
              />
            </Suspense>
          ) : (
            <div className="processing">
              <h2>
                {view === 'learning'
                  ? 'Prerequisites have not been analyzed'
                  : 'No stored nodes in this view'}
              </h2>
              <p>Scientific relations appear only when backed by stored evidence.</p>
            </div>
          )}
          {hits.length > 0 && (
            <div className="search-results">
              <div className="panel-title">
                SEARCH RESULTS<button onClick={() => setHits([])}>Close</button>
              </div>
              {hits.map((hit, index) => (
                <button
                  key={`${hit.anchor_id}-${index}`}
                  onClick={() => {
                    void chooseSource(hit.anchor_id, hit.node_id ?? undefined);
                    setHits([]);
                  }}
                >
                  <small>
                    {hit.kind} · Page {hit.page_number}
                  </small>
                  <span>{hit.text.slice(0, 240)}</span>
                </button>
              ))}
            </div>
          )}
          <div className="graph-status">
            <div>
              <button
                aria-label="Previous graph selection"
                disabled={historyIndex <= 0}
                onClick={() => {
                  setHistoryIndex(historyIndex - 1);
                  void selectNode(history[historyIndex - 1]);
                }}
              >
                ←
              </button>
              <button
                aria-label="Next graph selection"
                disabled={historyIndex >= history.length - 1}
                onClick={() => {
                  setHistoryIndex(historyIndex + 1);
                  void selectNode(history[historyIndex + 1]);
                }}
              >
                →
              </button>
            </div>
            <span>
              {graph.nodes.length} / {graph.total_nodes} nodes · {graph.edges.length} directed
              relations
            </span>
            <span>{graph.truncated ? 'Bounded view' : 'Candidate extraction'}</span>
          </div>
        </section>
        <Inspector
          key={bundle?.node.id ?? 'empty'}
          bundle={bundle}
          paper={paper}
          onAnchor={showAnchor}
          onExpand={async () => {
            if (!bundle) return;
            try {
              const epoch = selectionEpoch.current;
              const projection = await api.neighborhood(bundle.node.id, 1);
              if (selectionEpoch.current === epoch) setGraph(projection);
            } catch (e) {
              setError(String(e));
            }
          }}
          onVerify={verify}
        />
      </div>
      {document && (
        <SourcePanel
          document={document}
          paperId={paperId}
          pageNumber={pageNumber}
          anchor={anchor}
          onPage={(page) => {
            setPageNumber(page);
            setAnchor(null);
          }}
          onSpan={(id) => void chooseSource(id)}
        />
      )}
      <footer>
        {document
          ? `${document.parser} ${document.parser_version} · ${document.pages.length} pages · ${document.warnings.length ? document.warnings.join(' ') : 'Text parsed; scientific interpretation remains unverified.'}`
          : 'A navigable scientific model, grounded in original evidence.'}
      </footer>
    </main>
  );
}
