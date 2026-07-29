// Battle of the Minds — chatbot config (public, NO secret).
// The LLM API key is held server-side by a Cloudflare Worker proxy (/llm); the client never sees it.
// Primary model: Google Gemini, via a free Google AI Studio key held server-side.
// Fallback: an OpenRouter free model, used only if Gemini is momentarily rate-limited.
window.OPENROUTER_MODELS = [
  "gemini-flash-latest",
  "openai/gpt-oss-20b:free"
];
window.MODEL_LABELS = {
  "gemini-flash-latest": "Google Gemini 2.5 Flash",
  "openai/gpt-oss-20b:free": "GPT-OSS 20B (fallback)"
};
