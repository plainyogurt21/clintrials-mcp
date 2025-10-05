import manifest from "../manifest.json" assert { type: "json" };

interface Env {
  FASTMCP_BASE_URL?: string;
  FASTMCP_URL?: string;
  BACKEND_URL?: string;
}

const JSON_HEADERS: Record<string, string> = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "public, max-age=300",
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET,POST,OPTIONS",
  "access-control-allow-headers": "authorization,content-type",
};

function jsonResponse(body: unknown, init?: ResponseInit): Response {
  const mergedHeaders = new Headers(JSON_HEADERS);
  if (init?.headers) {
    const extra = new Headers(init.headers);
    extra.forEach((value, key) => mergedHeaders.set(key, value));
  }

  const status = init?.status ?? 200;
  const statusText = init?.statusText;

  return new Response(JSON.stringify(body, null, 2), {
    ...init,
    status,
    statusText,
    headers: mergedHeaders,
  });
}

function resolveBackend(env: Env): string | undefined {
  return env.FASTMCP_BASE_URL ?? env.FASTMCP_URL ?? env.BACKEND_URL;
}

function ensureTrailingSlash(url: string): string {
  return url.endsWith("/") ? url : `${url}/`;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: JSON_HEADERS,
      });
    }

    if (url.pathname === "/" || url.pathname === "/manifest.json") {
      return jsonResponse(manifest);
    }

    if (url.pathname === "/health") {
      return jsonResponse({ status: "ok", timestamp: new Date().toISOString() });
    }

    const backendBase = resolveBackend(env);

    if (!backendBase) {
      return jsonResponse(
        {
          error: "Upstream MCP backend is not configured",
          expectedEnvironmentVariables: [
            "FASTMCP_BASE_URL",
            "FASTMCP_URL",
            "BACKEND_URL",
          ],
        },
        { status: 500 }
      );
    }

    const target = new URL(url.pathname + url.search, ensureTrailingSlash(backendBase));
    const upstreamRequest = new Request(target.toString(), request);

    try {
      const upstreamResponse = await fetch(upstreamRequest, {
        cf: { cacheEverything: false },
      });

      const headers = new Headers(upstreamResponse.headers);
      headers.set("access-control-allow-origin", "*");

      return new Response(upstreamResponse.body, {
        status: upstreamResponse.status,
        statusText: upstreamResponse.statusText,
        headers,
      });
    } catch (error) {
      return jsonResponse(
        {
          error: "Failed to reach upstream MCP backend",
          details: error instanceof Error ? error.message : String(error),
        },
        { status: 502 }
      );
    }
  },
};
