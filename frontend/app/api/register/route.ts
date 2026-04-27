import { NextResponse } from "next/server";

import { fetchThreatvisionApi } from "@/lib/threatvisionServerFetch";

/** Public pass-through to FastAPI ``POST /auth/register`` (no internal JWT). */
export async function POST(request: Request) {
  const body = await request.text();
  const res = await fetchThreatvisionApi("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body || "{}",
  });
  const text = await res.text();
  return new NextResponse(text, {
    status: res.status,
    headers: {
      "Content-Type": res.headers.get("content-type") ?? "application/json",
    },
  });
}
