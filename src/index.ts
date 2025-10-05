import manifest from "../manifest.json" assert { type: "json" };

const JSON_HEADERS: Record<string, string> = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "public, max-age=300",
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

export default {
  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);

    if (request.method !== "GET") {
      return jsonResponse(
        { error: "Method not allowed", allowedMethods: ["GET"] },
        { status: 405 }
      );
    }

    if (url.pathname === "/" || url.pathname === "/manifest.json") {
      return jsonResponse(manifest);
    }

    if (url.pathname === "/health") {
      return jsonResponse({ status: "ok", timestamp: new Date().toISOString() });
    }

    return jsonResponse(
      {
        error: "Not found",
        message:
          "Available endpoints are '/' (or '/manifest.json') for the MCP manifest and '/health' for a simple status check.",
      },
      { status: 404 }
    );
  },
};
