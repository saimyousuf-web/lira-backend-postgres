import {
  BedrockRuntimeClient,
  InvokeModelWithResponseStreamCommand,
} from "@aws-sdk/client-bedrock-runtime";
import { PollyClient, SynthesizeSpeechCommand } from "@aws-sdk/client-polly";
import express from "express";

const PYTHON_RAG_URL  = process.env.PYTHON_RAG_URL  || "http://localhost:8000/rag";
const PYTHON_SAVE_URL = process.env.PYTHON_SAVE_URL || "http://localhost:8000/rag/save";
const POLLY_VOICE     = process.env.POLLY_VOICE     || "Stephen";
const AWS_REGION      = process.env.AWS_REGION      || "us-east-1";

/* ---------------- AWS CLIENTS ---------------- */
const bedrock = new BedrockRuntimeClient({ region: AWS_REGION });
const polly   = new PollyClient({ region: AWS_REGION });

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
  "Access-Control-Allow-Methods":  "POST, GET, OPTIONS",
  "Access-Control-Allow-Headers":  "Content-Type, Authorization",
  "Access-Control-Expose-Headers": "X-Chat-Id",
};

/* ---------------- POLLY HELPERS ---------------- */

const SPEAK_SENTENCE_ENDS = /[.?!]$/;
const SPEAK_MAX_CHARS     = 100;

function shouldSpeak(buffer) {
  if (SPEAK_SENTENCE_ENDS.test(buffer.trimEnd())) return true;
  if (buffer.length >= SPEAK_MAX_CHARS && /\s/.test(buffer)) return true;
  return false;
}

async function synthesize(text) {
  const command = new SynthesizeSpeechCommand({
    Text:         text,
    Engine:       "generative",
    OutputFormat: "mp3",
    VoiceId:      POLLY_VOICE,
  });
  const response = await polly.send(command);
  const chunks   = [];
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
    const ragRes = await fetch(PYTHON_RAG_URL, {
      method:  "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization:  req.headers?.authorization || "",
      },
      body: JSON.stringify(req.body),
    });

    if (!ragRes.ok) {
      const errorText = await ragRes.text();
      console.error("RAG STATUS:", ragRes.status, errorText);
      throw new Error("RAG API failed");
    }

    const data             = await ragRes.json();
    console.log(data);
    const prompt           = data?.streaming_metadata?.prompt;
    let voice_mode       = data?.streaming_metadata?.voice_mode;
    const storage_metadata = data?.storage_metadata;

    console.log("RAG response received. Voice mode:", voice_mode);

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
      "Connection":    "keep-alive",
      "X-Chat-Id":     storage_metadata?.chat_id || "",
    });

    /* ---------- 3. Bedrock request (same for both modes) ---------- */
    const command = new InvokeModelWithResponseStreamCommand({
      modelId:     "us.anthropic.claude-haiku-4-5-20251001-v1:0",
      contentType: "application/json",
      accept:      "application/json",
      body: JSON.stringify({
        anthropic_version: "bedrock-2023-05-31",
        max_tokens:        4096,
        temperature:       0.4,
        messages: [{ role: "user", content: [{ type: "text", text: prompt }] }],
      }),
    });

    const response = await bedrock.send(command);
    const decoder  = new TextDecoder();
    let fullResponse = "";

    if (voice_mode) {
      /* ── VOICE MODE ────────────────────────────────────────────────────────
         Mirrors Python WebSocket pipeline: text tokens + Polly audio chunks  */

      writeLine(res, {
        type:       "message_start",
        message_id: storage_metadata?.message_id,
      });

      let textBuffer = "";

      for await (const streamEvent of response.body) {
        const chunk = streamEvent.chunk;
        if (!chunk) continue;

        const parsed = JSON.parse(decoder.decode(chunk.bytes, { stream: true }));

        if (
          parsed.type === "content_block_delta" &&
          parsed.delta?.type === "text_delta"
        ) {
          const token  = parsed.delta.text;
          textBuffer   += token;
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
      /* ── TEXT MODE — original logic, untouched ─────────────────────────── */

      res.write(
        JSON.stringify({
          type:       "message_start",
          message_id: storage_metadata?.message_id,
        }) + "\n",
      );

      let buffer = "";

      for await (const streamEvent of response.body) {
        const chunk = streamEvent.chunk;
        if (!chunk) continue;

        const parsed = JSON.parse(decoder.decode(chunk.bytes, { stream: true }));

        if (
          parsed.type === "content_block_delta" &&
          parsed.delta?.type === "text_delta"
        ) {
          const text = parsed.delta?.text;
          buffer       += text;
          fullResponse += text;

          if (buffer.length > 10 || /[\s.,!?]$/.test(buffer)) {
            res.write(buffer);
            buffer = "";
          }
        }
      }

      if (buffer) res.write(buffer);
    }

    /* ---------- 4. Save (same for both modes) ---------- */
    fetch(PYTHON_SAVE_URL, {
      method:  "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization:  req.headers?.authorization || "",
      },
      body: JSON.stringify({ ...storage_metadata, full_response: fullResponse }),
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