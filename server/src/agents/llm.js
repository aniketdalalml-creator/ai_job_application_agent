import Groq from "groq-sdk";
import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: path.resolve(__dirname, "../../../.env") });

let client;

function resolveGroqApiKey() {
  let key = process.env.GROQ_API_KEY?.trim() || "";
  if (!key || key.includes("your_key")) {
    const fallback = process.env.ANTHROPIC_API_KEY?.trim() || "";
    if (fallback.startsWith("gsk_")) {
      key = fallback;
    }
  }
  return key;
}

export function getGroqClient() {
  const apiKey = resolveGroqApiKey();
  if (!apiKey) {
    throw new Error(
      "GROQ_API_KEY is not set. Copy .env.example to .env and add your free key from https://console.groq.com/",
    );
  }
  if (!client) {
    client = new Groq({ apiKey });
  }
  return client;
}

export function getModel() {
  return process.env.GROQ_MODEL?.trim() || "llama-3.3-70b-versatile";
}

/**
 * @param {{
 *   system?: string;
 *   messages: Array<{ role: string; content: string }>;
 *   temperature?: number;
 *   jsonMode?: boolean;
 * }} params
 */
export async function chatCompletion({ system, messages, temperature = 0.4, jsonMode = false }) {
  const groq = getGroqClient();
  /** @type {import("groq-sdk").Groq.Chat.Completions.ChatCompletionMessageParam[]} */
  const payload = system
    ? [{ role: "system", content: system }, ...messages]
    : messages;

  const response = await groq.chat.completions.create({
    model: getModel(),
    messages: payload,
    temperature,
    ...(jsonMode ? { response_format: { type: "json_object" } } : {}),
  });

  return response.choices[0]?.message?.content?.trim() || "";
}

/**
 * @param {string} text
 */
export function extractJson(text) {
  const cleaned = text.trim();
  const fenced = cleaned.match(/```(?:json)?\s*([\s\S]*?)\s*```/);
  const candidate = fenced ? fenced[1].trim() : cleaned;
  try {
    const parsed = JSON.parse(candidate);
    if (parsed && typeof parsed === "object") return parsed;
  } catch {
    const start = candidate.indexOf("{");
    const end = candidate.lastIndexOf("}");
    if (start !== -1 && end > start) {
      return JSON.parse(candidate.slice(start, end + 1));
    }
  }
  throw new Error(`Could not parse JSON from model response:\n${text.slice(0, 500)}`);
}
