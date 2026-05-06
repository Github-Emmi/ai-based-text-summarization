import { NextRequest, NextResponse } from "next/server";

export async function POST(_req: NextRequest) {
  const response = NextResponse.json({ ok: true });
  response.cookies.delete("refresh_token");
  return response;
}
