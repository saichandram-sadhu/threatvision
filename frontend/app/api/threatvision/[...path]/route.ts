import { getServerSession } from "next-auth";
import { NextRequest, NextResponse } from "next/server";

import { authOptions } from "@/lib/auth";
import {
  exchangeInternalJwt,
  getBackendUrl,
  isBackendLinkedUserId,
} from "@/lib/backend";

async function proxy(request: NextRequest, pathSegments: string[]) {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  if (!isBackendLinkedUserId(session.user.id)) {
    return NextResponse.json(
      {
        error: "oauth_not_linked",
        message:
          "Sign in with email and password to use API-backed features. OAuth sessions cannot exchange an internal JWT yet.",
      },
      { status: 403 },
    );
  }

  let internalJwt: string;
  try {
    internalJwt = await exchangeInternalJwt(session.user.id, session.user.role);
  } catch (e) {
    const msg = e instanceof Error ? e.message : "exchange failed";
    return NextResponse.json({ error: "bff_exchange_failed", message: msg }, { status: 502 });
  }

  const subpath = pathSegments.length ? pathSegments.join("/") : "";
  if (!subpath) {
    return NextResponse.json({ error: "Missing path" }, { status: 404 });
  }

  const incoming = new URL(request.url);
  const target = `${getBackendUrl()}/${subpath}${incoming.search}`;

  const headers = new Headers();
  const ct = request.headers.get("content-type");
  if (ct) headers.set("content-type", ct);
  const accept = request.headers.get("accept");
  if (accept) headers.set("accept", accept);
  headers.set("authorization", `Bearer ${internalJwt}`);

  const method = request.method.toUpperCase();
  const hasBody = !["GET", "HEAD"].includes(method);
  let bodyBuf: ArrayBuffer | undefined;
  if (hasBody) {
    bodyBuf = await request.arrayBuffer();
  }
  const backendRes = await fetch(target, {
    method,
    headers,
    body: bodyBuf && bodyBuf.byteLength > 0 ? bodyBuf : undefined,
  });

  const outHeaders = new Headers();
  const pass = [
    "content-type",
    "cache-control",
    "content-disposition",
    "x-request-id",
  ] as const;
  for (const k of pass) {
    const v = backendRes.headers.get(k);
    if (v) outHeaders.set(k, v);
  }

  if (backendRes.headers.get("content-type")?.includes("text/event-stream")) {
    outHeaders.set("cache-control", "no-cache");
    outHeaders.set("connection", "keep-alive");
  }

  return new NextResponse(backendRes.body, {
    status: backendRes.status,
    headers: outHeaders,
  });
}

type Ctx = { params: { path?: string[] } };

export async function GET(request: NextRequest, ctx: Ctx) {
  return proxy(request, ctx.params.path ?? []);
}

export async function POST(request: NextRequest, ctx: Ctx) {
  return proxy(request, ctx.params.path ?? []);
}

export async function PUT(request: NextRequest, ctx: Ctx) {
  return proxy(request, ctx.params.path ?? []);
}

export async function PATCH(request: NextRequest, ctx: Ctx) {
  return proxy(request, ctx.params.path ?? []);
}

export async function DELETE(request: NextRequest, ctx: Ctx) {
  return proxy(request, ctx.params.path ?? []);
}
