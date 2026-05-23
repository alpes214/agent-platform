import { NextRequest } from 'next/server';

import { fetchFastAPI } from '@/app/api/_lib/fastapi-client';
import { passThrough } from '@/app/api/_lib/stream';

export const runtime = 'nodejs';
// Stream stays open as long as the LLM is generating. Vercel function timeout
// defaults to 10s on Hobby — we need substantially more for CPU-bound LLM.
// 300s (5 min) is the max on Hobby; Pro allows up to 800s.
export const maxDuration = 300;

export async function POST(request: NextRequest): Promise<Response> {
  // Re-serialize the JSON body so we don't need duplex streaming for a tiny
  // request. The response is what needs to stream, not the request.
  const body = await request.text();

  const upstream = await fetchFastAPI('/ask', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body,
    traceparent: request.headers.get('traceparent'),
    requestId: request.headers.get('x-request-id'),
    // When the browser disconnects, Next.js aborts request.signal; passing
    // it to fetch closes the upstream TCP connection, which cascades into
    // FastAPI's `request.is_disconnected()` returning True so the agent
    // loop bails out instead of running to completion uselessly.
    signal: request.signal,
  });

  return passThrough(upstream);
}
