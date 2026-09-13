// config.js
//
// Optional: point Ask HOPPER at a deployed AI proxy (see
// cloudflare-worker/ask-hopper-proxy.js and docs/ai-proxy-setup.md) so
// questions are answered by a real model instead of the local rule-based
// parser. Leave this empty to keep HOPPER fully static with no external
// calls and no API key required — that is the default and is a completely
// legitimate way to run this prototype.
//
// Example once deployed:
//   export const ASK_HOPPER_PROXY_URL = "https://ask-hopper-proxy.yourname.workers.dev";

export const ASK_HOPPER_PROXY_URL = "";

// How long to wait for the proxy before falling back to the local
// rule-based interpreter (milliseconds).
export const ASK_HOPPER_PROXY_TIMEOUT_MS = 15000;
