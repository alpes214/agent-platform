// Server-only — never imported by client components. The env vars referenced
// here have no NEXT_PUBLIC_ prefix, so they're not inlined into the browser
// bundle even if accidentally imported from a client component.

const BASE = process.env.FASTAPI_INTERNAL_URL;
const SECRET = process.env.INTERNAL_SECRET;

if (!BASE) {
  throw new Error('FASTAPI_INTERNAL_URL is required (set in .env.local or Vercel env)');
}
if (!SECRET) {
  throw new Error('INTERNAL_SECRET is required (set in .env.local or Vercel env)');
}

export interface FastApiFetchInit extends RequestInit {
  // Incoming traceparent from the browser request — propagated to FastAPI for
  // distributed-trace continuity. The route handler grabs it from
  // request.headers and passes it through.
  traceparent?: string | null;
  // Incoming X-Request-Id — propagated so the same id ties together browser
  // log → BFF log → FastAPI log. If not provided, FastAPI generates one and
  // returns it via its response X-Request-Id header.
  requestId?: string | null;
}

export async function fetchFastAPI(
  path: string,
  init: FastApiFetchInit = {},
): Promise<Response> {
  const { traceparent, requestId, ...rest } = init;
  const headers = new Headers(rest.headers);
  headers.set('x-internal-secret', SECRET!);
  if (traceparent) {
    headers.set('traceparent', traceparent);
  }
  if (requestId) {
    headers.set('x-request-id', requestId);
  }
  return fetch(`${BASE}${path}`, { ...rest, headers });
}
