import { HttpServer } from "./server/httpServer.ts";
import { MCPServer } from "./server/mcpServer.ts";

async function main() {
  const args = process.argv.slice(2);
  const isHttp = args.includes("--http") || process.env.MCP_TRANSPORT === "http";
  const apiKey = process.env.SENTINEL_API_KEY || "sentinel-local-dev-key";
  const port = parseInt(process.env.PORT || "8000", 10);

  if (isHttp) {
    const server = new HttpServer(apiKey);
    await server.start(port);
  } else {
    // stdio transport
    const mcp = new MCPServer();
    process.stdin.setEncoding("utf-8");

    let buffer = "";
    process.stdin.on("data", async (chunk) => {
      buffer += chunk;
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (!line.trim()) continue;
        try {
          const req = JSON.parse(line);
          const res = await mcp.handleRequest(req);
          if (res) {
            process.stdout.write(JSON.stringify(res) + "\n");
          }
        } catch (e) {
          process.stdout.write(JSON.stringify({ jsonrpc: "2.0", id: null, error: { code: -32700, message: "Parse error" } }) + "\n");
        }
      }
    });
  }
}

main().catch(console.error);
