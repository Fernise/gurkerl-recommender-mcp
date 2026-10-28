import fs from "node:fs";

const envPath = new URL("../.env", import.meta.url);
if (fs.existsSync(envPath)) {
  const lines = fs.readFileSync(envPath, "utf8").split(/\r?\n/);
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#") || !trimmed.includes("=")) continue;
    const [key, ...valueParts] = trimmed.split("=");
    if (!process.env[key]) {
      process.env[key] = valueParts.join("=").trim().replace(/^['"]|['"]$/g, "");
    }
  }
}

const email = process.env.RHL_EMAIL;
const password = process.env.RHL_PASS;
if (!email || !password) {
  throw new Error("Missing RHL_EMAIL or RHL_PASS");
}

const url = "https://mcp.gurkerl.at/mcp/";
let nextId = 1;
let sessionId = null;
const protocolVersion = "2024-11-05";

async function post(label, payload) {
  console.error(`MCP ${label}...`);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30000);
  const headers = {
    "content-type": "application/json",
    accept: "application/json, text/event-stream",
    "user-agent": "mcp-remote",
    "mcp-protocol-version": protocolVersion,
    "rhl-email": email,
    "rhl-pass": password,
  };
  if (sessionId) headers["mcp-session-id"] = sessionId;

  try {
    const response = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
    console.error(
      `MCP ${label} response ${response.status} ${response.headers.get("content-type") || ""}`,
    );
    if (!response.ok) {
      const text = await response.text();
      throw new Error(`MCP ${label} failed: HTTP ${response.status}: ${text}`);
    }
    sessionId = response.headers.get("mcp-session-id") || sessionId;
    const parsed = await readResponse(response);
    console.error(`MCP ${label} ok`);
    return parsed;
  } finally {
    clearTimeout(timeout);
  }
}

async function readResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("text/event-stream")) {
    const text = await response.text();
    return parseResponse(text);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) return parseResponse(buffer);
    buffer += decoder.decode(value, { stream: true });
    const eventEnd = buffer.indexOf("\n\n");
    if (eventEnd !== -1) {
      const event = buffer.slice(0, eventEnd);
      const dataLines = event
        .split(/\r?\n/)
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice("data:".length).trim());
      if (dataLines.length) {
        await reader.cancel();
        return JSON.parse(dataLines.join("\n"));
      }
    }
  }
}

function parseResponse(text) {
  const trimmed = text.trim();
  if (!trimmed) return {};
  const dataLines = trimmed
    .split(/\r?\n/)
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice("data:".length).trim());
  return JSON.parse(dataLines.length ? dataLines.join("\n") : trimmed);
}

await post("initialize", {
  jsonrpc: "2.0",
  id: nextId++,
  method: "initialize",
  params: {
    protocolVersion,
    capabilities: {},
    clientInfo: { name: "gurkerl-recommender", version: "0.1.0" },
  },
});

await post("initialized notification", {
  jsonrpc: "2.0",
  method: "notifications/initialized",
  params: {},
});

const tools = await post("tools/list", {
  jsonrpc: "2.0",
  id: nextId++,
  method: "tools/list",
  params: {},
});

console.log(JSON.stringify(tools, null, 2));
