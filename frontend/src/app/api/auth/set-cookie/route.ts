import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  const body = (await req.json()) as { refresh_token?: string };
  const token = body?.refresh_token;

  if (!token || typeof token !== "string") {
    return NextResponse.json({ error: "Missing refresh_token" }, { status: 400 });
  }

  const response = NextResponse.json({ ok: true });
  response.cookies.set("refresh_token", token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 30, // 30 days
  });
  return response;
}
