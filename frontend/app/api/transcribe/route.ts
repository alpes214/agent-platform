import { NextRequest } from 'next/server';

import { fetchFastAPI } from '@/app/api/_lib/fastapi-client';
import { passThrough } from '@/app/api/_lib/stream';

export const runtime = 'nodejs';

// Audio clips are small; cap at 4 MB like the doc upload to stay under the
// Vercel Hobby body limit and reject oversized recordings up-front.
const MAX_UPLOAD_BYTES = 4 * 1024 * 1024;

export async function POST(request: NextRequest): Promise<Response> {
  const contentLengthHeader = request.headers.get('content-length');
  if (contentLengthHeader) {
    const contentLength = Number(contentLengthHeader);
    if (Number.isFinite(contentLength) && contentLength > MAX_UPLOAD_BYTES) {
      return Response.json(
        {
          detail: `audio too large (${contentLength} bytes); max is ${MAX_UPLOAD_BYTES} bytes (~4 MB)`,
        },
        { status: 413 },
      );
    }
  }

  const contentType = request.headers.get('content-type');
  if (!contentType?.startsWith('multipart/form-data')) {
    return Response.json(
      { detail: 'content-type must be multipart/form-data' },
      { status: 415 },
    );
  }

  const upstream = await fetchFastAPI('/transcribe', {
    method: 'POST',
    headers: {
      'content-type': contentType,
      ...(contentLengthHeader ? { 'content-length': contentLengthHeader } : {}),
    },
    body: request.body,
    duplex: 'half',
    traceparent: request.headers.get('traceparent'),
    requestId: request.headers.get('x-request-id'),
    signal: request.signal,
  } as RequestInit & { duplex: 'half' });

  return passThrough(upstream);
}
