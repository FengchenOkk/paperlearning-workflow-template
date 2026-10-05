import type {
  Anchor,
  Document,
  EvidenceBundle,
  Graph,
  Job,
  Node,
  Paper,
  SearchHit,
  UploadResult,
  Verification,
} from './contracts';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, init);
  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null);
    const message =
      body && typeof body === 'object' && 'detail' in body && typeof body.detail === 'string'
        ? body.detail
        : `Request failed (${response.status})`;
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export const api = {
  papers: () => request<Paper[]>('/papers'),
  paper: (id: string) => request<Paper>(`/papers/${id}`),
  job: (id: string) => request<Job>(`/jobs/${id}`),
  retry: (id: string) => request<Job>(`/jobs/${id}/retry`, { method: 'POST' }),
  document: (id: string) => request<Document>(`/papers/${id}/document`),
  graph: (id: string, view: string, limit: number) =>
    request<Graph>(`/papers/${id}/graph?view=${view}&limit=${limit}`),
  neighborhood: (id: string, depth: number) =>
    request<Graph>(`/nodes/${id}/neighborhood?depth=${depth}&limit=120`),
  evidence: (id: string) => request<EvidenceBundle>(`/nodes/${id}/evidence`),
  anchor: (id: string) => request<Anchor>(`/anchors/${id}`),
  associated: (id: string) => request<Node[]>(`/anchors/${id}/nodes`),
  search: (id: string, query: string) =>
    request<SearchHit[]>(`/papers/${id}/search?q=${encodeURIComponent(query)}`),
  verify: (id: string, review: Verification) =>
    request<Node>(`/nodes/${id}/verification`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(review),
    }),
  upload: (file: File) => {
    const body = new FormData();
    body.append('file', file);
    return request<UploadResult>('/papers', { method: 'POST', body });
  },
};
