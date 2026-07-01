import { PollyClient, SynthesizeSpeechCommand } from "@aws-sdk/client-polly";
import express from "express";
import http from "node:http";

const PYTHON_RAG_URL = process.env.PYTHON_RAG_URL || 'http://127.0.0.1:8000/rag' || "http://localhost:8000/rag";
const PYTHON_SAVE_URL = process.env.PYTHON_SAVE_URL || 'http://127.0.0.1:8000/rag/save' || "http://localhost:8000/rag/save";
const POLLY_VOICE = process.env.POLLY_VOICE || "Stephen";
const AWS_REGION = process.env.AWS_REGION || "us-east-1";
const OLLAMA_BASE_URL = process.env.OLLAMA_BASE_URL || "http://localhost:11434";
const OLLAMA_MODEL = process.env.OLLAMA_MODEL || "llama3.1:8b";

/* ---------------- AWS CLIENTS ---------------- */
const polly = new PollyClient({ region: AWS_REGION });

/* ---------------- OLLAMA STREAM HELPER ---------------- */
// Uses the built-in http module (not fetch): llama3.1:8b on CPU can take longer to
// evaluate a large prompt than undici's default headers timeout allows, which makes
// fetch abort with UND_ERR_HEADERS_TIMEOUT before the first token.
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
    req.setTimeout(0); // wait as long as needed for the first byte (prompt eval)
    req.write(JSON.stringify(payload));
    req.end();
  });
}

async function* streamOllamaTokens(prompt, userMessage, citation_html) {
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

/* ---------------- EXPRESS ---------------- */
const app = express();
app.use(express.json());
// http://localhost:5173
// 
const allowedOrigins = [
  "http://localhost:5173",
  "http://localhost:8001",
];
const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "http://localhost:5173",
  "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
  "Access-Control-Expose-Headers": "X-Chat-Id",
};

/* ---------------- POLLY HELPERS ---------------- */

const SPEAK_SENTENCE_ENDS = /[.?!]$/;
const SPEAK_MAX_CHARS = 100;

function shouldSpeak(buffer) {
  if (SPEAK_SENTENCE_ENDS.test(buffer.trimEnd())) return true;
  if (buffer.length >= SPEAK_MAX_CHARS && /\s/.test(buffer)) return true;
  return false;
}

async function synthesize(text) {
  const command = new SynthesizeSpeechCommand({
    Text: text,
    Engine: "generative",
    OutputFormat: "mp3",
    VoiceId: POLLY_VOICE,
  });
  const response = await polly.send(command);
  const chunks = [];
  for await (const chunk of response.AudioStream) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  return Buffer.concat(chunks).toString("base64");
}

/* ---------------- WRITER ---------------- */

function writeLine(res, obj) {
  res.write(JSON.stringify(obj) + "\n");
}

/* ---------------- SINGLE ENDPOINT ---------------- */

app.options("/stream", (req, res) => {
  res.writeHead(204, CORS_HEADERS);
  res.end();
});

app.post("/stream", async (req, res) => {
  try {
    /* ---------- 1. RAG ---------- */
    // console.log('req.body', req.body);
    console.log('comes here', PYTHON_RAG_URL);

    const ragRes = await fetch(PYTHON_RAG_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: req.headers?.authorization || "",
      },
      body: JSON.stringify(req.body),
    });

    if (!ragRes.ok) {
      const errorText = await ragRes.text();
      console.error("RAG STATUS:", ragRes.status, errorText);
      throw new Error("RAG API failed");
    }


    let data = await ragRes.json();

    data = Array.isArray(data) ? data[0] : data;

    const prompt = data?.streaming_metadata?.prompt;
    const user_message = data?.streaming_metadata?.user_message;
    let voice_mode = data?.streaming_metadata?.voice_mode;
    const storage_metadata = data?.storage_metadata;
    const citation_html = data?.streaming_metadata?.citation_html;
    console.log('\n--------------citation--------------\n', citation_html);
    // console.log(data);
    // console.log('--------------------- prompt ------', prompt);
    // console.log("RAG response received. Voice mode:", voice_mode);

    if (!prompt) throw new Error("Invalid RAG response: missing prompt");

    /* ---------- 2. Open stream — content type depends on mode ---------- */
    //
    //  voice_mode = true  → application/x-ndjson  (JSON lines: text tokens + audio chunks)
    //  voice_mode = false → text/plain             (raw text, original behaviour)
    //
    res.writeHead(200, {
      ...CORS_HEADERS,
      "Content-Type": voice_mode
        ? "application/x-ndjson; charset=utf-8"
        : "text/plain; charset=utf-8",
      "Cache-Control": "no-cache",
      "Connection": "keep-alive",
      "X-Chat-Id": storage_metadata?.chat_id || "",
    });

    /* ---------- 3. Ollama request (same for both modes) ---------- */
    let fullResponse = "";

    if (voice_mode) {
      /* ── VOICE MODE ────────────────────────────────────────────────────────
         Mirrors Python WebSocket pipeline: text tokens + Polly audio chunks  */

      writeLine(res, {
        type: "message_start",
        message_id: storage_metadata?.message_id,
      });

      let textBuffer = "";

      for await (const token of streamOllamaTokens(prompt, user_message)) {
        textBuffer += token;
        fullResponse += token;

        // Send token immediately for UI text display
        writeLine(res, { type: "text", text: token });

        // Sentence boundary → synthesize → send audio chunk
        if (shouldSpeak(textBuffer)) {
          try {
            const audioB64 = await synthesize(textBuffer);
            writeLine(res, { type: "audio", audio: audioB64, text: textBuffer });
          } catch (pollyErr) {
            console.error("[polly] chunk error:", pollyErr);
            writeLine(res, { type: "audio_error", text: textBuffer });
          }
          textBuffer = "";
        }
      }

      // Flush remaining buffer
      if (textBuffer.trim()) {
        try {
          const audioB64 = await synthesize(textBuffer);
          writeLine(res, { type: "audio", audio: audioB64, text: textBuffer });
        } catch (pollyErr) {
          console.error("[polly] final chunk error:", pollyErr);
          writeLine(res, { type: "audio_error", text: textBuffer });
        }
      }

      writeLine(res, { type: "done" });

    } else {
      /* ── TEXT MODE ─────────────────────────────────────────────────────── */

      res.write(
        JSON.stringify({
          type: "message_start",
          message_id: storage_metadata?.message_id,
        }) + "\n",
      );

      let buffer = "";

      for await (const token of streamOllamaTokens(prompt, user_message)) {
        buffer += token;
        fullResponse += token;

        if (buffer.length > 10 || /[\s.,!?]$/.test(buffer)) {
          res.write(buffer);
          buffer = "";
        }
      }

      if (buffer) res.write(buffer);
      res.write(citation_html || "");  
      fullResponse = fullResponse + "\n" + (citation_html || "");
    }
    
    console.log('-------------full_response-------- ', fullResponse)
    
    /* ---------- 4. Save (same for both modes) ---------- */
    console.log('saved called');
    
    fetch(PYTHON_SAVE_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: req.headers?.authorization || "",
      },
      body: JSON.stringify({
        ...storage_metadata,
        full_response: fullResponse,
        
      }),
    }).catch(console.error);

  } catch (err) {
    console.error("ERROR:", err);
    if (!res.headersSent) {
      res.writeHead(500, { ...CORS_HEADERS, "Content-Type": "text/plain" });
    }
    res.write("\nERROR: " + (err?.message || "Unknown error"));
  }

  res.end();
});

app.listen(3000, () => console.log("Running on http://localhost:3000"));

// test = {
//   'sub': '54e8b4f8-a001-7007-5fa5-ed28f945594f',
//   'iss': 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_3BNCKJ4VT',
//    'client_id': '4flnkmiud6dpkmu1viik3kjrte',
//    'origin_jti': 'f4ee2a85-79d5-4f11-8ab5-caf26d58d2e3',
//    'event_id': '48f7b11d-832f-45d3-87f5-69f8f51fea41',
//    'token_use': 'access',
//    'scope': 'aws.cognito.signin.user.admin',
//    'auth_time': 1781077042,
//     'exp': 1781080642,
//     'iat': 1781077042,
//     'jti': '807bd3ea-06dc-4e57-ab61-9fec64bf7f9a',
//     'username': '54e8b4f8-a001-7007-5fa5-ed28f945594f' }