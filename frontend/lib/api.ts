import type {
  DocumentOut,
  SearchResponse,
  TranscribeResponse,
  UploadResponse,
} from '@/lib/types';

// Phase 7: BFF routes live at /api/* (same origin as the Next.js app), so
// no CORS, no credentials handshake. Browser never sees the FastAPI URL.
// Server-side, the Next.js route handlers add INTERNAL_SECRET + (in prod)
// the CF Access service-token headers before calling FastAPI.
const BASE = '/api';

async function expect<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const detail = await res.text().catch(() => '');
    throw new Error(`HTTP ${res.status}: ${detail || res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export async function listDocs(): Promise<DocumentOut[]> {
  return expect(await fetch(`${BASE}/docs`));
}

export async function getDoc(id: string): Promise<DocumentOut> {
  return expect(await fetch(`${BASE}/docs/${id}`));
}

export async function uploadDoc(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append('file', file);
  return expect(
    await fetch(`${BASE}/docs`, { method: 'POST', body: form }),
  );
}

export async function deleteDoc(id: string): Promise<void> {
  const res = await fetch(`${BASE}/docs/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
}

export function pdfUrl(id: string, page?: number | null): string {
  const fragment = page ? `#page=${page}` : '';
  return `${BASE}/docs/${id}/pdf${fragment}`;
}

export async function transcribe(blob: Blob): Promise<TranscribeResponse> {
  const form = new FormData();
  form.append('file', blob, 'audio.webm');
  return expect(
    await fetch(`${BASE}/transcribe`, { method: 'POST', body: form }),
  );
}

export async function search(
  query: string,
  k = 10,
  docIds?: string[],
): Promise<SearchResponse> {
  const params = new URLSearchParams({ q: query, k: String(k) });
  for (const id of docIds ?? []) params.append('doc_id', id);
  return expect(await fetch(`${BASE}/search?${params.toString()}`));
}

export const apiBase = BASE;
