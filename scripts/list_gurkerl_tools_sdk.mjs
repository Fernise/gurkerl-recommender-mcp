import fs from "node:fs";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

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

function withTimeout(promise, label, timeoutMs = 30000) {
  return Promise.race([
    promise,
    new Promise((_, reject) => {
      setTimeout(() => reject(new Error(`${label} timed out after ${timeoutMs}ms`)), timeoutMs);
    }),
  ]);
}

const client = new Client(
  { name: "gurkerl-recommender", version: "0.1.0" },
  { capabilities: {} },
);

const transport = new StreamableHTTPClientTransport(
  new URL("https://mcp.gurkerl.at/mcp/"),
  {
    requestInit: {
      headers: {
        "rhl-email": email,
        "rhl-pass": password,
      },
    },
  },
);

try {
  console.error("SDK connect...");
  await withTimeout(client.connect(transport), "connect");
  console.error("SDK listTools...");
  const tools = await withTimeout(client.listTools(), "listTools");
  console.log(JSON.stringify(tools, null, 2));
} finally {
  await client.close();
}
