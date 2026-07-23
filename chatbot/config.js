// Battle of the Minds — live chatbot config (public).
// No secret committed here. The bot works two ways:
//  1) A one-click free key is injected at deploy time via config.local.js (git-ignored), or
//  2) Any visitor can paste their own free OpenRouter key (openrouter.ai) in the key bar.
window.OPENROUTER_MODELS = [
  "openai/gpt-oss-20b:free",
  "nvidia/nemotron-3-super-120b-a12b:free",
  "google/gemma-4-31b-it:free"
];
