import { NextRequest, NextResponse } from 'next/server';

const DEMO_KEY = process.env.DEMO_KEY!;
const COOKIE_NAME = 'demo_token';
const COOKIE_MAX_AGE = 60 * 60 * 24 * 30;

export function proxy(req: NextRequest): NextResponse {
  // Magic-link flow: ?k=<key> sets the cookie then strips the param so the
  // shared URL doesn't keep echoing the key around (browser history, referer).
  const k = req.nextUrl.searchParams.get('k');
  if (k === DEMO_KEY) {
    const url = req.nextUrl.clone();
    url.searchParams.delete('k');
    const res = NextResponse.redirect(url);
    res.cookies.set(COOKIE_NAME, DEMO_KEY, {
      httpOnly: true,
      sameSite: 'lax',
      secure: true,
      maxAge: COOKIE_MAX_AGE,
    });
    return res;
  }
  if (req.cookies.get(COOKIE_NAME)?.value === DEMO_KEY) {
    return NextResponse.next();
  }
  return new NextResponse('Demo access required. Use the shared link.', { status: 401 });
}

export const config = {
  matcher: ['/((?!_next|favicon|robots).*)'],
};
