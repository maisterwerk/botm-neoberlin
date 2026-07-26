// Battle of the Minds — chatbot config (public, NO secret).
// The LLM API key is held server-side by a Cloudflare Worker proxy (/llm); the client never sees it.
window.OPENROUTER_MODELS = [
  "openai/gpt-oss-20b:free",
  "nvidia/nemotron-3-super-120b-a12b:free",
  "google/gemma-4-31b-it:free"
];
