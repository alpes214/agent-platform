// Pass-through helpers for non-JSON responses (SSE streams + binary).
// Both preserve the upstream response body without buffering, and forward
// the client's AbortSignal so disconnects propagate to FastAPI.

const PRESERVED_HEADERS = [
  'content-type',
  'content-length',
  'content-disposition',
  'cache-control',
  'last-modified',
  'etag',
  'x-request-id',
] as const;

export function passThrough(upstream: Response): Response {
  const headers = new Headers();
  for (const name of PRESERVED_HEADERS) {
    const value = upstream.headers.get(name);
    if (value !== null) {
      headers.set(name, value);
    }
  }
  // Belt-and-suspenders for SSE: explicit no-transform so any proxy in front
  // of the BFF doesn't try to gzip the stream and accidentally buffer.
  if ((headers.get('content-type') ?? '').includes('event-stream')) {
    headers.set('cache-control', 'no-cache, no-transform');
    headers.set('x-accel-buffering', 'no');
  }
  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers,
  });
}
