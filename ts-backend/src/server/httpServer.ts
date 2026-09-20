import * as http from "http";
import { MCPServer } from "./mcpServer.ts";

export class HttpServer {
  private mcpServer: MCPServer;
  private apiKey: string;
  private server: http.Server | null = null;

  constructor(apiKey: string = "sentinel-local-dev-key", mcpServer?: MCPServer) {
    this.apiKey = apiKey;
    this.mcpServer = mcpServer || new MCPServer();
  }

  private authenticate(req: http.IncomingMessage): boolean {
    if (!this.apiKey) return true;

    const authHeader = req.headers["authorization"] || "";
    if (authHeader.startsWith("Bearer ") && authHeader.slice(7).trim() === this.apiKey) {
      return true;
    }

    const sentinelKey = req.headers["x-sentinel-api-key"] || req.headers["x-api-key"];
    if (typeof sentinelKey === "string" && sentinelKey.trim() === this.apiKey) {
      return true;
    }

    return false;
  }

  public start(port: number = 8000, host: string = "127.0.0.1"): Promise<void> {
    return new Promise((resolve) => {
      this.server = http.createServer(async (req, res) => {
        const url = req.url?.split("?")[0] || "/";

        // GET /health
        if (req.method === "GET" && url === "/health") {
          res.writeHead(200, { "Content-Type": "application/json; charset=utf-8" });
          res.end(JSON.stringify({
            status: "ok",
            service: "nasiko-sentinel-ts",
            version: "0.1.0",
            runtime: "typescript",
            environment: "development",
            dependencies: {
              kubernetes: { status: "simulated" },
              autoscaler: { provider: "simulated_ts" },
              reasoner: { provider: "deterministic_fallback" }
            }
          }));
          return;
        }

        // POST /mcp
        if (req.method === "POST" && (url === "/mcp" || url === "/")) {
          if (!this.authenticate(req)) {
            res.writeHead(401, { "Content-Type": "application/json; charset=utf-8" });
            res.end(JSON.stringify({
              jsonrpc: "2.0",
              id: null,
              error: { code: -32001, message: "Unauthorized: Invalid or missing API key" }
            }));
            return;
          }

          let body = "";
          req.on("data", (chunk) => { body += chunk; });
          req.on("end", async () => {
            try {
              const payload = JSON.parse(body);
              const response = await this.mcpServer.handleRequest(payload);
              if (response === null) {
                res.writeHead(204);
                res.end();
                return;
              }
              res.writeHead(200, { "Content-Type": "application/json; charset=utf-8" });
              res.end(JSON.stringify(response));
            } catch (e: any) {
              res.writeHead(200, { "Content-Type": "application/json; charset=utf-8" });
              res.end(JSON.stringify({
                jsonrpc: "2.0",
                id: null,
                error: { code: -32700, message: "Parse error: Invalid JSON payload" }
              }));
            }
          });
          return;
        }

        // Default 404
        res.writeHead(404, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ jsonrpc: "2.0", error: { code: -32601, message: "Not Found" } }));
      });

      this.server.listen(port, host, () => {
        console.log(`[nasiko-sentinel-ts] TypeScript HTTP MCP Server listening on http://${host}:${port}`);
        resolve();
      });
    });
  }

  public stop(): Promise<void> {
    return new Promise((resolve) => {
      if (this.server) {
        this.server.close(() => resolve());
      } else {
        resolve();
      }
    });
  }
}
