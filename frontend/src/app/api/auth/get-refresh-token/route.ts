import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  const token = req.cookies.get("refresh_token")?.value;
  if (!token) {
    return NextResponse.json({ error: "No refresh token" }, { status: 401 });
  }
  return NextResponse.json({ refresh_token: token });
}
