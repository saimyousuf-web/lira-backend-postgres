import http from "node:http";

/* ---------------- ENV ---------------- */
const PYTHON_RAG_URL  = "https://ziewv6e9h7.execute-api.us-east-1.amazonaws.com/rag";
const PYTHON_SAVE_URL = "https://ziewv6e9h7.execute-api.us-east-1.amazonaws.com/rag/save";
const OLLAMA_BASE_URL = process.env.OLLAMA_BASE_URL || "http://localhost:11434";
const OLLAMA_MODEL    = process.env.OLLAMA_MODEL || "llama3.1:8b";

/* ---------------- OLLAMA STREAM HELPER ---------------- */
function postOllamaStream(payload) {
  return new Promise((resolve, reject) => {
    const url = new URL(`${OLLAMA_BASE_URL}/api/chat`);
    const req = http.request(
      {
        hostname: url.hostname,
        port: url.port || 80,
        path: url.pathname,
        method: "POST",
        headers: { "Content-Type": "application/json" },
      },
      (res) => resolve(res),
    );
    req.on("error", reject);
    req.setTimeout(0);
    req.write(JSON.stringify(payload));
    req.end();
  });
}

async function* streamOllamaTokens(prompt, userMessage) {
  const res = await postOllamaStream({
    model: OLLAMA_MODEL,
    stream: true,
    options: { temperature: 0.4, num_predict: 4096 },
    messages: [
      { role: "system", content: prompt },
      { role: "user", content: userMessage || "Please respond per the instructions above." },
    ],
  });

  if (res.statusCode !== 200) {
    let errBody = "";
    for await (const c of res) errBody += c.toString("utf8");
    throw new Error(`Ollama request failed: ${res.statusCode} ${errBody}`);
  }

  let lineBuffer = "";
  for await (const chunk of res) {
    lineBuffer += chunk.toString("utf8");
    const lines = lineBuffer.split("\n");
    lineBuffer = lines.pop() ?? "";
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      let parsed;
      try {
        parsed = JSON.parse(trimmed);
      } catch (e) {
        console.error("[ollama] non-JSON line:", trimmed);
        continue;
      }
      if (parsed.error) throw new Error(`Ollama error: ${parsed.error}`);
      const token = parsed.message?.content || "";
      if (token) yield token;
    }
  }
}

/* ---------------- SENTENCE CHUNKING ---------------- */

const SENTENCE_ENDS = /[.?!]$/;
const MAX_CHARS     = 80;

function shouldFlush(buffer) {
  if (SENTENCE_ENDS.test(buffer.trimEnd())) return true;
  if (buffer.length >= MAX_CHARS && /\s/.test(buffer)) return true;
  return false;
}

/* ---------------- HELPER ---------------- */

function writeLine(stream, obj) {
  stream.write(JSON.stringify(obj) + "\n");
}

/* ================================================================
   LAMBDA HANDLER
   ================================================================ */
export const handler = awslambda.streamifyResponse(
  async (event, responseStream) => {
    let body = {};
    try {
      body =
        typeof event.body === "string"
          ? JSON.parse(event.body)
          : event.body || {};
    } catch {
      body = {};
    }

    try {
      /* 1. RAG */
      const ragRes = await fetch(PYTHON_RAG_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: event.headers?.authorization || "",
        },
        body: JSON.stringify(body),
      });

      if (!ragRes.ok) throw new Error("RAG API failed");

      const data             = await ragRes.json();
      const prompt           = data?.[0]?.streaming_metadata?.prompt;
      const user_message     = data?.[0]?.streaming_metadata?.user_message;
      const voice_mode       = data?.[0]?.streaming_metadata?.voice_mode;
      const storage_metadata = data?.[0]?.storage_metadata;

      if (!prompt) throw new Error("Invalid RAG response: missing prompt");

      /* 2. Open response stream */
      responseStream = awslambda.HttpResponseStream.from(responseStream, {
        statusCode: 200,
        headers: {
          "Content-Type": "application/x-ndjson; charset=utf-8",
          "Cache-Control": "no-cache",
          "Connection":    "keep-alive",
          "X-Chat-Id":     storage_metadata?.chat_id || "",
        },
      });

      /* 3. Ollama (local LLM, streaming) */
      let fullResponse = "";
      let textBuffer   = "";

      writeLine(responseStream, {
        type:       "message_start",
        message_id: storage_metadata?.message_id,
      });

      for await (const token of streamOllamaTokens(prompt, user_message)) {
        textBuffer   += token;
        fullResponse += token;

        // Always stream raw token so FE can render text in real time
        writeLine(responseStream, { type: "text", text: token });

        // In voice mode, also emit a completed sentence for FE TTS
        if (voice_mode && shouldFlush(textBuffer)) {
          writeLine(responseStream, { type: "sentence", text: textBuffer.trim() });
          textBuffer = "";
        }
      }

      // Flush remaining buffer
      if (textBuffer.trim()) {
        if (voice_mode) {
          writeLine(responseStream, { type: "sentence", text: textBuffer.trim() });
        }
      }

      writeLine(responseStream, { type: "done" });

      /* 4. Save */
      fetch(PYTHON_SAVE_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization:  event.headers?.authorization || "",
        },
        body: JSON.stringify({ ...storage_metadata, full_response: fullResponse }),
      }).catch(console.error);

    } catch (err) {
      console.error("ERROR:", err);
      try {
        writeLine(responseStream, {
          type:    "error",
          message: err?.message || "Unknown error",
        });
      } catch {
        responseStream.write("\nERROR: " + (err?.message || "Unknown error"));
      }
    }

    responseStream.end();
  }
);