import { NextRequest } from 'next/server';

import { fetchFastAPI } from '@/app/api/_lib/fastapi-client';
import { passThrough } from '@/app/api/_lib/stream';

export const runtime = 'nodejs';

export async function GET(request: NextRequest): Promise<Response> {
  const upstream = await fetchFastAPI(
    `/search?${request.nextUrl.searchParams.toString()}`,
    {
      traceparent: request.headers.get('traceparent'),
      requestId: request.headers.get('x-request-id'),
    },
  );
  return passThrough(upstream);
}
