import { NextRequest, NextResponse } from "next/server";

const PUBLIC_PATHS = ["/login", "/register", "/api/"];

export function proxy(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // Allow public paths through
  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  // Check for refresh token cookie as proxy for "logged in"
  // (access token lives in memory; cookie persists across page reloads)
  const hasRefreshToken = req.cookies.has("refresh_token");

  if (!hasRefreshToken) {
    const loginUrl = req.nextUrl.clone();
    loginUrl.pathname = "/login";
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
