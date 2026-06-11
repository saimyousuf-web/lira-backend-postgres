import {
  BedrockRuntimeClient,
  InvokeModelWithResponseStreamCommand,
} from "@aws-sdk/client-bedrock-runtime";

/* ---------------- ENV ---------------- */
const PYTHON_RAG_URL  = "https://ziewv6e9h7.execute-api.us-east-1.amazonaws.com/rag";
const PYTHON_SAVE_URL = "https://ziewv6e9h7.execute-api.us-east-1.amazonaws.com/rag/save";
const AWS_REGION      = "us-east-1";

/* ---------------- AWS CLIENT ---------------- */
const bedrockClient = new BedrockRuntimeClient({ region: AWS_REGION });

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

      /* 3. Bedrock */
      const command = new InvokeModelWithResponseStreamCommand({
        modelId:     "us.anthropic.claude-haiku-4-5-20251001-v1:0",
        contentType: "application/json",
        accept:      "application/json",
        body: JSON.stringify({
          anthropic_version: "bedrock-2023-05-31",
          max_tokens:        4096,
          temperature:       0.4,
          messages: [
            { role: "user", content: [{ type: "text", text: prompt }] },
          ],
        }),
      });

      const response   = await bedrockClient.send(command);
      const decoder    = new TextDecoder();
      let fullResponse = "";
      let textBuffer   = "";

      writeLine(responseStream, {
        type:       "message_start",
        message_id: storage_metadata?.message_id,
      });

      for await (const streamEvent of response.body) {
        const chunk = streamEvent.chunk;
        if (!chunk) continue;

        const parsed = JSON.parse(decoder.decode(chunk.bytes, { stream: true }));

        if (
          parsed.type === "content_block_delta" &&
          parsed.delta?.type === "text_delta"
        ) {
          const token   = parsed.delta.text;
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