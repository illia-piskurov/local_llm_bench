import assert from "node:assert/strict";
import { createServer, type Server } from "node:http";
import type { AddressInfo } from "node:net";
import test from "node:test";
import { OpenAiCompatibleClient, ProviderError } from "./model-client.js";

function createMockServer(handler: (req: any, res: any) => void): Promise<{ server: Server; url: string }> {
  return new Promise((resolve) => {
    const server = createServer(handler);
    server.listen(0, "127.0.0.1", () => {
      const addr = server.address() as AddressInfo;
      resolve({ server, url: `http://127.0.0.1:${addr.port}/v1` });
    });
  });
}

test("OpenAiCompatibleClient: listModels returns parsed model IDs", async () => {
  const { server, url } = await createMockServer((req, res) => {
    if (req.url === "/v1/models" && req.method === "GET") {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ data: [{ id: "model-1" }, { id: "model-2" }] }));
      return;
    }
    res.writeHead(404).end();
  });

  try {
    const client = new OpenAiCompatibleClient(url);
    const models = await client.listModels();
    assert.deepEqual(models, [{ id: "model-1" }, { id: "model-2" }]);
  } finally {
    server.close();
  }
});

test("OpenAiCompatibleClient: sends Authorization header when apiKey is configured", async () => {
  let authHeader = "";
  const { server, url } = await createMockServer((req, res) => {
    authHeader = req.headers["authorization"] ?? "";
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ data: [{ id: "secret-model" }] }));
  });

  try {
    const client = new OpenAiCompatibleClient(url, { apiKey: "sk-test-token-123" });
    await client.listModels();
    assert.equal(authHeader, "Bearer sk-test-token-123");
  } finally {
    server.close();
  }
});

test("OpenAiCompatibleClient: throws ProviderError on HTTP 500 error", async () => {
  const { server, url } = await createMockServer((req, res) => {
    res.writeHead(500, { "Content-Type": "text/plain" });
    res.end("Internal Server Error");
  });

  try {
    const client = new OpenAiCompatibleClient(url);
    await assert.rejects(
      () => client.listModels(),
      (err: any) => {
        assert.ok(err instanceof ProviderError);
        assert.equal(err.status, 500);
        assert.match(err.message, /HTTP 500/);
        return true;
      }
    );
  } finally {
    server.close();
  }
});

test("OpenAiCompatibleClient: complete() parses response, usage and finish_reason", async () => {
  const { server, url } = await createMockServer((req, res) => {
    if (req.url === "/v1/chat/completions" && req.method === "POST") {
      let body = "";
      req.on("data", (chunk: Buffer) => { body += chunk; });
      req.on("end", () => {
        const parsed = JSON.parse(body);
        assert.equal(parsed.model, "test-model");
        res.writeHead(200, { "Content-Type": "application/json" });
        res.end(JSON.stringify({
          choices: [
            {
              message: { content: "export function solve() { return 42; }" },
              finish_reason: "stop"
            }
          ],
          usage: {
            completion_tokens: 15,
            prompt_tokens: 50,
            total_tokens: 65
          }
        }));
      });
    }
  });

  try {
    const client = new OpenAiCompatibleClient(url);
    const result = await client.complete({
      model: "test-model",
      messages: [{ role: "user", content: "Solve task" }],
      temperature: 0.2,
      max_tokens: 500,
      stream: false
    });

    assert.equal(result.content, "export function solve() { return 42; }");
    assert.equal(result.finishReason, "stop");
    assert.deepEqual(result.usage, { completion_tokens: 15, prompt_tokens: 50, total_tokens: 65 });
    assert.ok(result.durationMs >= 0);
  } finally {
    server.close();
  }
});

test("OpenAiCompatibleClient: throws ProviderError on non-JSON response (e.g. HTML gateway error)", async () => {
  const { server, url } = await createMockServer((req, res) => {
    res.writeHead(502, { "Content-Type": "text/html" });
    res.end("<html><body>502 Bad Gateway</body></html>");
  });

  try {
    const client = new OpenAiCompatibleClient(url);
    await assert.rejects(
      () => client.complete({
        model: "m",
        messages: [{ role: "user", content: "hi" }],
        temperature: 0,
        max_tokens: 10,
        stream: false
      }),
      (err: any) => {
        assert.ok(err instanceof ProviderError);
        assert.equal(err.status, 502);
        return true;
      }
    );
  } finally {
    server.close();
  }
});

test("OpenAiCompatibleClient: throws ProviderError when response choices are missing", async () => {
  const { server, url } = await createMockServer((req, res) => {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: "Something went wrong" }));
  });

  try {
    const client = new OpenAiCompatibleClient(url);
    await assert.rejects(
      () => client.complete({
        model: "m",
        messages: [{ role: "user", content: "hi" }],
        temperature: 0,
        max_tokens: 10,
        stream: false
      }),
      (err: any) => {
        assert.ok(err instanceof ProviderError);
        assert.match(err.message, /Invalid chat completion response/);
        return true;
      }
    );
  } finally {
    server.close();
  }
});

test("OpenAiCompatibleClient: respects timeoutMs option and throws TimeoutError", async () => {
  const { server, url } = await createMockServer((_req, _res) => {
    // Intentionally never respond to trigger client timeout
  });

  try {
    const client = new OpenAiCompatibleClient(url, { timeoutMs: 50 });
    await assert.rejects(
      () => client.complete({
        model: "m",
        messages: [{ role: "user", content: "hi" }],
        temperature: 0,
        max_tokens: 10,
        stream: false
      }),
      (err: any) => {
        assert.ok(err instanceof ProviderError);
        assert.match(err.message, /timed out/);
        return true;
      }
    );
  } finally {
    server.close();
  }
});

test("OpenAiCompatibleClient: aborts immediately on caller AbortSignal", async () => {
  const { server, url } = await createMockServer((_req, _res) => {
    // Server hangs
  });

  try {
    const client = new OpenAiCompatibleClient(url, { timeoutMs: 10000 });
    const controller = new AbortController();
    setTimeout(() => controller.abort(), 20);

    await assert.rejects(
      () => client.complete(
        {
          model: "m",
          messages: [{ role: "user", content: "hi" }],
          temperature: 0,
          max_tokens: 10,
          stream: false
        },
        controller.signal
      ),
      (err: any) => {
        assert.ok(err instanceof ProviderError);
        assert.match(err.message, /aborted/);
        return true;
      }
    );
  } finally {
    server.close();
  }
});
