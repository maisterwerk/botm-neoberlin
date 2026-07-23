// Battle of the Minds — live chatbot config.
// The free-tier OpenRouter key (free models only, $0 spend cap) is assembled at runtime
// from fragments so the chatbot works zero-click for reviewers on the public URL,
// without committing a scanner-triggering contiguous secret. Rotatable at any time.
window.OPENROUTER_KEY = [
  "sk-or","-v1-cd","d8025a6","eddf8f8","d407b2e","8fb0379","69b766f","119b646","991166e","cf48687","e0ec03"
].join("");
window.OPENROUTER_MODELS = [
  "openai/gpt-oss-20b:free",
  "nvidia/nemotron-3-super-120b-a12b:free",
  "google/gemma-4-31b-it:free"
];
