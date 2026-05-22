const TUNNEL = process.env.STOCKPULSE_TUNNEL_URL || "https://prior-managers-winners-cups.trycloudflare.com";

const ALLOWED = new Set([
  "/api/all",
  "/api/health",
  "/api/portfolio",
  "/api/trades",
  "/api/predictions",
  "/api/performance",
  "/api/mind",
  "/api/market",
  "/api/lessons",
  "/api/journal",
  "/api/journal/tags",
  "/api/tokens",
  "/api/inbox",
]);

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on("data", (chunk) => chunks.push(chunk));
    req.on("end", () => resolve(Buffer.concat(chunks)));
    req.on("error", reject);
  });
}

export async function proxyTo(req, res, upstreamPath) {
  if (!ALLOWED.has(upstreamPath)) {
    res.status(404).json({ error: "unknown_endpoint" });
    return;
  }

  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, HEAD, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  res.setHeader("Cache-Control", "no-store");

  if (req.method === "OPTIONS") {
    res.status(204).end();
    return;
  }

  const qs = Object.entries(req.query || {})
    .filter(([k]) => k !== "_path")
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
    .join("&");

  const url = `${TUNNEL}${upstreamPath}${qs ? `?${qs}` : ""}`;
  const headers = {};
  let body;

  if (req.method !== "GET" && req.method !== "HEAD") {
    body = await readBody(req);
    if (req.headers["content-type"]) {
      headers["content-type"] = req.headers["content-type"];
    }
  }

  try {
    const response = await fetch(url, {
      method: req.method,
      headers,
      body,
      signal: AbortSignal.timeout(25000),
    });
    const text = await response.text();
    res.status(response.status);
    res.setHeader("Content-Type", response.headers.get("content-type") || "application/json; charset=utf-8");
    res.send(text);
  } catch (error) {
    res.status(502).json({ error: "agent_offline", message: "Stockpulse Pi is unreachable" });
  }
}
