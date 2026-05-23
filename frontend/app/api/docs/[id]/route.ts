import { NextRequest } from 'next/server';

import { fetchFastAPI } from '@/app/api/_lib/fastapi-client';
import { passThrough } from '@/app/api/_lib/stream';

export const runtime = 'nodejs';

interface RouteContext {
  params: Promise<{ id: string }>;
}

export async function GET(
  request: NextRequest,
  context: RouteContext,
): Promise<Response> {
  const { id } = await context.params;
  const upstream = await fetchFastAPI(`/docs/${encodeURIComponent(id)}`, {
    traceparent: request.headers.get('traceparent'),
    requestId: request.headers.get('x-request-id'),
  });
  return passThrough(upstream);
}

export async function DELETE(
  request: NextRequest,
  context: RouteContext,
): Promise<Response> {
  const { id } = await context.params;
  const upstream = await fetchFastAPI(`/docs/${encodeURIComponent(id)}`, {
    method: 'DELETE',
    traceparent: request.headers.get('traceparent'),
    requestId: request.headers.get('x-request-id'),
  });
  return passThrough(upstream);
}
