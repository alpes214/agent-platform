import { NextRequest } from 'next/server';

import { fetchFastAPI } from '@/app/api/_lib/fastapi-client';
import { passThrough } from '@/app/api/_lib/stream';

export const runtime = 'nodejs';

// Vercel Hobby plan caps request bodies at 4.5 MB. Reject up-front with a
// friendly 413 so users get a clear message instead of an obscure platform
// error. Tightened to 4 MB to give breathing room over the platform limit.
const MAX_UPLOAD_BYTES = 4 * 1024 * 1024;

export async function GET(request: NextRequest): Promise<Response> {
  const upstream = await fetchFastAPI('/docs', {
    traceparent: request.headers.get('traceparent'),
    requestId: request.headers.get('x-request-id'),
  });
  return passThrough(upstream);
}

export async function POST(request: NextRequest): Promise<Response> {
  const contentLengthHeader = request.headers.get('content-length');
  if (contentLengthHeader) {
    const contentLength = Number(contentLengthHeader);
    if (Number.isFinite(contentLength) && contentLength > MAX_UPLOAD_BYTES) {
      return Response.json(
        {
          detail: `upload too large (${contentLength} bytes); max is ${MAX_UPLOAD_BYTES} bytes (~4 MB) due to the Vercel Hobby platform limit`,
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

  const upstream = await fetchFastAPI('/docs', {
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
