import Anthropic from "@anthropic-ai/sdk";
import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: path.resolve(__dirname, "../../../.env") });

let client;

export function getAnthropicClient() {
  if (!process.env.ANTHROPIC_API_KEY?.trim()) {
    throw new Error(
      "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key from https://console.anthropic.com/",
    );
  }
  if (!client) {
    client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY.trim() });
  }
  return client;
}

export function getModel() {
  return process.env.ANTHROPIC_MODEL?.trim() || "claude-sonnet-4-20250514";
}

/**
 * @param {Anthropic.MessageCreateParams} params
 */
export async function createMessage(params) {
  const anthropic = getAnthropicClient();
  return anthropic.messages.create({
    model: getModel(),
    max_tokens: 4096,
    ...params,
  });
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
