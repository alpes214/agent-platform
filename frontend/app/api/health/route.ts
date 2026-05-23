import { fetchFastAPI } from '@/app/api/_lib/fastapi-client';
import { passThrough } from '@/app/api/_lib/stream';

export const runtime = 'nodejs';

export async function GET(): Promise<Response> {
  const upstream = await fetchFastAPI('/health');
  return passThrough(upstream);
}
