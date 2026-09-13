# Setting up real AI answers for Ask HOPPER (optional)

By default, **Ask HOPPER** works with zero configuration: it's a local,
rule-based keyword interpreter (see `docs/interoperability.md` and
`js/ask.js`). That's a deliberate, legitimate way to run this prototype —
you can stop reading here and it will work fine.

**Easiest real-AI option — no setup below required:** open the Ask HOPPER
page on your deployed site and expand "Set up real AI answers." Paste an
Anthropic API key there and Claude answers directly from your browser —
nothing to deploy, nothing in this guide required. This is the fastest way
to get genuine AI answers working, but it means whoever wants AI answers
(you, or any visitor) needs to paste their own key into that box each time
they use a new browser (or check "remember on this device" to skip that).

This guide covers the alternative: a small shared proxy so **every**
visitor gets AI answers without any of them needing their own key. Only
bother with this if that matters to you — for trying things out yourself,
the box above is simpler.

**Why this needs a separate step at all:** GitHub Pages only serves static
files. If you put a real API key directly in the site's JavaScript, anyone
who opens their browser's dev tools could read it and run up charges on
your account. So the key has to live on a small server you control instead
— this guide uses [Cloudflare Workers](https://workers.cloudflare.com),
because its free tier is generous and, importantly, **you don't need to
install anything on your computer** — everything below happens in your
browser.

Budget about 15 minutes.

## What you'll end up with

- A tiny piece of server code (a "Worker") hosted on Cloudflare, holding
  your Anthropic API key as a secret
- Your HOPPER site's `js/config.js` pointing at that Worker's URL
- Ask HOPPER answering with Claude, still grounded only in indexed records,
  with automatic fallback to the local rule-based mode if the Worker is
  ever unreachable

## Step 1 — Get an Anthropic API key

1. Go to [console.anthropic.com](https://console.anthropic.com) and sign in
   or create an account.
2. Add a small amount of credit (the Console will prompt you — this is a
   pay-as-you-go API, a few dollars goes a very long way for a demo like
   this).
3. In the left sidebar, go to **API Keys → Create Key**. Copy the key
   somewhere safe — you won't be able to see it again after this screen.
4. **Before you do anything else:** in the Console, find **Limits** (or
   your workspace's **Spend limits** settings) and set a modest monthly
   cap — a few dollars is plenty for a demo. This protects you if the key
   ever leaks or gets called more than expected.

## Step 2 — Create the Cloudflare Worker

1. Go to [dash.cloudflare.com](https://dash.cloudflare.com) and sign in or
   create a free account.
2. In the left sidebar, select **Workers & Pages**.
3. Select **Create**, then choose the **"Hello World" Worker** template,
   and select **Deploy**. (This deploys a placeholder — you'll replace its
   code next.)
4. Once it's deployed, select **Edit code** — this opens an in-browser code
   editor, no install required.
5. Select all the placeholder code and delete it.
6. Open `cloudflare-worker/ask-hopper-proxy.js` from this repository, copy
   its entire contents, and paste it into the editor.
7. Select **Deploy** (sometimes shown as a small arrow next to Deploy →
   **Save and deploy**).
8. Note the Worker's URL shown at the top of the page — it looks like
   `https://ask-hopper-proxy.<your-subdomain>.workers.dev`.

## Step 3 — Add your API key as a secret

Do **not** paste your API key into the code itself.

1. On your Worker's page, go to **Settings**.
2. Under **Variables and Secrets**, select **Add**.
3. Choose type **Secret**, set the variable name to exactly
   `ANTHROPIC_API_KEY`, and paste your key as the value.
4. Select **Deploy** to apply it.

The key is now encrypted and only readable by your Worker's code — not
visible again in the dashboard, not visible to anyone visiting your site.

## Step 4 — Point HOPPER at your Worker

In your local copy of the repository, open `js/config.js` and set:

```js
export const ASK_HOPPER_PROXY_URL = "https://ask-hopper-proxy.<your-subdomain>.workers.dev";
```

Commit and push — GitHub Pages will redeploy automatically. Open your live
site's **Ask HOPPER** page and try one of the example questions; you should
see "AI-assisted answer" instead of "Demo semantic search mode."

## Step 5 (recommended) — Restrict who can call your Worker

Two optional hardening steps, in increasing order of effort:

**a) Lock CORS to your own site.** In `cloudflare-worker/ask-hopper-proxy.js`,
change:
```js
const ALLOWED_ORIGIN = "*";
```
to your exact GitHub Pages origin, e.g.:
```js
const ALLOWED_ORIGIN = "https://yourname.github.io";
```
Re-paste the updated file into **Edit code** and deploy again. This stops
other websites from calling your Worker directly from a browser (it does
not stop server-to-server calls, which is what the next step is for).

**b) Add a Cloudflare rate-limiting rule.** In the Cloudflare dashboard,
go to your account's **Security → WAF → Rate limiting rules** (or your
Worker's **Triggers/Routes** settings, depending on your plan) and add a
rule capping requests per IP address per minute to your Worker's route.
This is the real backstop against someone hammering your endpoint and
running up API costs — the spend limit from Step 1 is your last line of
defense either way.

## Testing it directly (optional)

You can confirm the Worker itself works before touching the frontend, using
your browser's address bar is not enough (it's a POST endpoint), but this
`curl` command works from any terminal, or from Cloudflare's own **Edit
code → Preview** panel:

```bash
curl -X POST https://ask-hopper-proxy.<your-subdomain>.workers.dev \
  -H "Content-Type: application/json" \
  -d '{"question":"What pathogens cause rice blast?","records":[{"HOPPER_ID":"HOPPER:DIS:0001","Name":"Rice blast","Entity_Type":"Disease","Host":"Rice","Pathogen":"Magnaporthe oryzae"}]}'
```

You should get back `{"answer": "..."}`.

## Cost expectations

This uses Claude Haiku by default (`claude-haiku-4-5-20251001` in the
Worker code) — a fast, inexpensive model well suited to a small grounded
Q&A feature like this. Each question sends a short prompt plus up to 25
compact records (a few hundred to low thousands of tokens) and returns a
capped ~400-token answer. Real-world cost per question is a small fraction
of a cent at today's pricing; check
[anthropic.com/pricing](https://www.anthropic.com/pricing) for current
rates, and rely on the Console spend limit from Step 1 as your safety net
regardless.

## Turning it back off

Set `ASK_HOPPER_PROXY_URL` back to `""` in `js/config.js`, commit, and
push. Ask HOPPER immediately goes back to fully local, rule-based mode —
nothing else about the site depends on the proxy.
