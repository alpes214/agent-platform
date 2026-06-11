import { NextRequest, NextResponse } from 'next/server';

const DEMO_KEY = process.env.DEMO_KEY!;
const FASTAPI_INTERNAL_URL = process.env.FASTAPI_INTERNAL_URL!;
const INTERNAL_SECRET = process.env.INTERNAL_SECRET!;
const COOKIE_NAME = 'demo_token';
const COOKIE_MAX_AGE = 60 * 60 * 24 * 30;
const NOINDEX = 'noindex, nofollow, noarchive';

type Gate = 'magic-link' | 'cookie' | 'denied' | 'landing';

function logAccess(req: NextRequest, gate: Gate): void {
  // Fire-and-forget POST to FastAPI /access-log. keepalive lets the request
  // outlive this proxy invocation; .catch swallows errors so log-write
  // failures never break the user-facing flow.
  const body = {
    ip: req.headers.get('x-real-ip') ?? req.headers.get('x-forwarded-for'),
    country: req.headers.get('x-vercel-ip-country'),
    region: req.headers.get('x-vercel-ip-country-region'),
    city: decodeURIComponent(req.headers.get('x-vercel-ip-city') ?? '') || null,
    lat: req.headers.get('x-vercel-ip-latitude'),
    lon: req.headers.get('x-vercel-ip-longitude'),
    user_agent: req.headers.get('user-agent'),
    path: req.nextUrl.pathname,
    referer: req.headers.get('referer'),
    gate,
  };
  void fetch(`${FASTAPI_INTERNAL_URL}/access-log`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-internal-secret': INTERNAL_SECRET,
    },
    body: JSON.stringify(body),
    keepalive: true,
  }).catch(() => {});
}

export function proxy(req: NextRequest): NextResponse {
  const pathname = req.nextUrl.pathname;

  // Magic-link flow: ?k=<key> on any path sets the cookie and redirects to
  // /app (not the source path), so visitors land on the actual app entry
  // rather than the landing.
  const k = req.nextUrl.searchParams.get('k');
  if (k === DEMO_KEY) {
    const url = req.nextUrl.clone();
    url.pathname = '/app';
    url.searchParams.delete('k');
    const res = NextResponse.redirect(url);
    res.cookies.set(COOKIE_NAME, DEMO_KEY, {
      httpOnly: true,
      sameSite: 'lax',
      secure: true,
      maxAge: COOKIE_MAX_AGE,
    });
    logAccess(req, 'magic-link');
    return res;
  }

  // Landing at `/` is public — indexable, no demo cookie required.
  if (pathname === '/') {
    logAccess(req, 'landing');
    return NextResponse.next();
  }

  // Everything else (/app/*, /api/*) is gated.
  if (req.cookies.get(COOKIE_NAME)?.value === DEMO_KEY) {
    logAccess(req, 'cookie');
    const res = NextResponse.next();
    res.headers.set('X-Robots-Tag', NOINDEX);
    return res;
  }

  logAccess(req, 'denied');
  return new NextResponse('Demo access required. Use the shared link.', {
    status: 401,
    headers: { 'X-Robots-Tag': NOINDEX },
  });
}

export const config = {
  matcher: ['/((?!_next|favicon|robots|sitemap).*)'],
};
