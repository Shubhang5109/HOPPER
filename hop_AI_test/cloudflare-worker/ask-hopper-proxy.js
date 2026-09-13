/**
 * HOPPER — Ask HOPPER AI proxy (optional)
 * ----------------------------------------
 * This is a Cloudflare Worker, not part of the static site itself. It exists
 * for exactly one reason: a public GitHub Pages site cannot hold a secret
 * API key, so if you want "Ask HOPPER" to be answered by a real model
 * (Claude) instead of the built-in local keyword parser, the API key has to
 * live somewhere with a server — this Worker is the smallest version of
 * that "somewhere."
 *
 * It does NOT give the model free rein: the frontend does its own local
 * retrieval first (the same rule-based matching used in the no-proxy mode)
 * and sends only that already-filtered set of HOPPER records as context.
 * The system prompt instructs the model to answer only from those records.
 * This Worker does not query any other database or the open internet.
 *
 * Setup: see docs/ai-proxy-setup.md in the main repo for a full, no-CLI-
 * required walkthrough. Short version:
 *   1. Cloudflare dashboard -> Workers & Pages -> Create -> "Hello World" -> Deploy
 *   2. Edit code -> paste this whole file -> Deploy
 *   3. Settings -> Variables and Secrets -> Add -> type "Secret" ->
 *      name ANTHROPIC_API_KEY -> paste your key -> Deploy
 *   4. Copy the Worker's *.workers.dev URL into js/config.js
 *
 * Required secret:
 *   ANTHROPIC_API_KEY   — from https://console.anthropic.com
 */

// Tighten this to your exact GitHub Pages origin (e.g.
// "https://yourname.github.io") once you've confirmed it works — "*" is
// the easiest way to get started but allows any site to call this Worker.
const ALLOWED_ORIGIN = "*";

const MODEL = "claude-haiku-4-5-20251001"; // fast + inexpensive; see README for alternatives
const MAX_TOKENS = 400;
const MAX_QUESTION_LENGTH = 500;
const MAX_RECORDS = 25;

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };
}

function jsonResponse(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders(), "Content-Type": "application/json" },
  });
}

function buildSystemPrompt(records) {
  return [
    'You are "Ask HOPPER", answering questions about a small plant-disease',
    "prototype database called HOPPER (Harmonized Ontology & Plant Pathology",
    "Exploration Repository).",
    "",
    "Answer ONLY using the JSON records listed below, which HOPPER's own",
    "local search already retrieved for this question. Do not use outside",
    "knowledge, and do not invent databases, genes, relationships, or facts",
    "that are not present in these records.",
    "",
    "If the records don't contain enough to answer the question, say that",
    "plainly instead of guessing.",
    "",
    "When you reference a record, name it and give its HOPPER_ID so the",
    "person can find it on the site. Keep the answer under 120 words, plain",
    "prose, no markdown headers or bullet lists.",
    "",
    "INDEXED RECORDS (JSON):",
    JSON.stringify(records),
  ].join("\n");
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders() });
    }

    if (request.method !== "POST") {
      return jsonResponse({ error: "This endpoint only accepts POST." }, 405);
    }

    if (!env.ANTHROPIC_API_KEY) {
      return jsonResponse(
        { error: "Server misconfigured: ANTHROPIC_API_KEY secret is not set on this Worker." },
        500
      );
    }

    let body;
    try {
      body = await request.json();
    } catch {
      return jsonResponse({ error: "Request body must be JSON." }, 400);
    }

    const question = String(body.question || "").trim().slice(0, MAX_QUESTION_LENGTH);
    const records = Array.isArray(body.records) ? body.records.slice(0, MAX_RECORDS) : [];

    if (!question) {
      return jsonResponse({ error: "Missing 'question'." }, 400);
    }

    let upstream;
    try {
      upstream = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: {
          "x-api-key": env.ANTHROPIC_API_KEY,
          "anthropic-version": "2023-06-01",
          "content-type": "application/json",
        },
        body: JSON.stringify({
          model: MODEL,
          max_tokens: MAX_TOKENS,
          system: buildSystemPrompt(records),
          messages: [{ role: "user", content: question }],
        }),
      });
    } catch (err) {
      return jsonResponse({ error: `Could not reach Anthropic API: ${err.message}` }, 502);
    }

    if (!upstream.ok) {
      const detail = await upstream.text().catch(() => "");
      return jsonResponse(
        { error: `Anthropic API returned ${upstream.status}.`, detail: detail.slice(0, 300) },
        502
      );
    }

    const data = await upstream.json();
    const answer = (data.content || [])
      .filter((block) => block.type === "text")
      .map((block) => block.text)
      .join("\n")
      .trim();

    return jsonResponse({ answer: answer || "The model returned no text." });
  },
};
