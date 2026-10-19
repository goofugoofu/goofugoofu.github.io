---
title: AI Tool Map
emoji: 🗺️
colorFrom: blue
colorTo: indigo
sdk: static
app_file: index.html
pinned: false
license: mit
short_description: "Bilingual AI tool directory: scenarios and weekly feeds"
---

# AI Tool Map (MVP)

Bilingual (ZH / EN) AI tool directory: scenario-based recommendations, daily update outlines, and a “this week’s new tools” feed that doubles as a newsletter source.

## Features

- **Language toggle** — only one language shown at a time; preference saved in `localStorage` (`ai-tool-map-lang`)
- **Home** — scenario entry, today’s update summary, new-this-week tools, search
- **Scenario pages** — tools filtered by Writing / Image·Video / Coding / Agents / Research / Office
- **Tool detail** — use when / avoid when, pricing, sources, sponsored & affiliate
- **Daily Updates** — short outline summaries (filled by scanner + seeds)
- **This Week’s New Tools** — weekly feed usable as newsletter copy
- **Subscribe / Business** — waitlist forms; WeChat/Alipay “coming soon”; optional Stripe
- **About** — mission + contact/business inquiry
- **SEO + ICP footer** — meta/og tags; ICP placeholder for later filing number
- **Daily scanner** — `scripts/scan-daily.py` pulls public sources into `data/daily.json` / `weekly.json`


## Standing ops (`ops/`)

Nine standing requirements are documented in **`ops/STANDING-OPS.md`** (SEO, chatbot/GEO, newsletter, X watch, monetization gates, etc.).

| File | Purpose |
|------|---------|
| `ops/STANDING-OPS.md` | Maps the 9 requirements → routines/files |
| `ops/monetization-gates.md` | **DRAFT** thresholds before paid spots / affiliates / sponsors |
| `ops/newsletter-runbook.md` | Weekly issue from `weekly.json` → draft → review → send (ESP TBD) |
| `llms.txt` | Guidance for AI agents / chatbots citing this site |
| `robots.txt` | Allow crawlers; points to sitemap |
| `sitemap.xml` | Main HTML + scenario/tool URLs — **base URL placeholder** `https://goofugoofu.github.io/` until custom domain |

Until gates are met (or founder overrides), monetization stays soft: no hard paywall on core browse.

## Theme switcher

Use the **Theme** dropdown in the header (persisted as `localStorage` key `ai-tool-map-theme`):

| Value | Effect |
|-------|--------|
| System | Follow OS light/dark (`prefers-color-scheme`) |
| Light | Clean light UI |
| Dark | Soft dark UI |
| Soft blue | Light blue-tinted palette |
| Warm sand | Warm beige palette |
| High contrast | Strong black/white/yellow for readability |

Themes apply via `data-theme` on `<html>` and CSS variables. `js/theme-boot.js` runs in `<head>` to avoid a flash of the wrong theme.



## Live public site (current)

- **GitHub Pages (live):** https://goofugoofu.github.io/
- Source mirror: https://github.com/goofugoofu/ai-tool-map
- Pages repo: https://github.com/goofugoofu/goofugoofu.github.io
- **Hugging Face Space (live):** https://huggingface.co/spaces/TonyGooF/ai-tool-map
- Space app URL: https://tonygoof-ai-tool-map.hf.space

Redeploy the Space with `./scripts/deploy-hf.sh` when the local tree changes. GitHub Pages is a separate push to `goofugoofu/goofugoofu.github.io`.

## Deploy to Hugging Face Space (static)

```bash
# Needs a write-capable HF token in the environment (hf auth login or HF_TOKEN)
export PATH="$HOME/.local/bin:$PATH"
hf auth whoami
./scripts/deploy-hf.sh          # creates TonyGooF/ai-tool-map if needed and uploads
# or:
# hf repos create TonyGooF/ai-tool-map --type space --space-sdk static --public --exist-ok
# hf upload TonyGooF/ai-tool-map . --type space --commit-message "deploy AI Tool Map"
```

Public URLs after deploy:

- https://huggingface.co/spaces/TonyGooF/ai-tool-map
- https://tonygoof-ai-tool-map.hf.space

Do **not** commit `.env`, tokens, or private keys.

## Run locally

Content is loaded via `fetch`, so you need a tiny static server (opening `file://` will block JSON).

From this directory:

```bash
cd /workspace/ai-tool-map
python3 -m http.server 5173
```

Then open: **http://127.0.0.1:5173/**

Or with Node (if available):

```bash
npx --yes serve -l 5173 .
```


## Monetization

Edit `data/monetization.json`:

```json
{
  "stripe_payment_link": "",
  "stripe_sponsored_link": "",
  "waitlist_mailto": "",
  "contact_email": "",
  "wechat_pay_enabled": false,
  "alipay_enabled": false,
  "icp_number": "",
  "plans": [ ... ]
}
```

- **China (primary):** WeChat Pay / Alipay show as **即将开通 / Coming soon** until merchant + ICP are ready. Do **not** invent payment URLs. Flip `wechat_pay_enabled` / `alipay_enabled` only when real checkout exists.
- **Stripe (optional):** If `stripe_payment_link` is non-empty, the international Pay CTA opens that URL; empty = disabled.
- Same rule for `stripe_sponsored_link` on sponsored listing.
- `waitlist_mailto` / `contact_email` enable optional `mailto:` buttons; forms also save to a **localStorage waitlist**.
- `icp_number`: when set, the footer shows the备案号; when empty, shows a placeholder (“待备案通过后填写”).
- After changing config, redeploy Pages / Space.

No fake checkout links — empty means intentionally disabled.

## Daily scanner

Python 3 stdlib only (no pip install required).

```bash
cd /workspace/ai-tool-map
python3 scripts/scan-daily.py            # fetch + write JSON
python3 scripts/scan-daily.py --dry-run  # report only
python3 scripts/scan-daily.py --no-stubs # skip RunningHub / Higgsfield / manual stubs
```

### What it writes

| File | Role |
|------|------|
| `data/daily.json` | Replaces **today’s** entries with scan results; keeps older days |
| `data/weekly.json` | Upserts the current ISO-week block from today’s scan |
| `data/suggested_tools.json` | Optional new `tools.json` candidates (not auto-merged) |
| `data/scan_cache/last_scan_report.json` | Source status + counts |
| `data/manual_scan.json` | Hand-edited / stub items merged when `enabled: true` |

Bilingual titles/summaries use a **template** by default. If `OPENAI_API_KEY` (or `OPENAI_KEY`) is set, the script asks the Chat Completions API instead. Optional HF path: `HF_TOKEN` + `HF_LLM_MODEL`.

### Source status

| Source | Mode | Notes |
|--------|------|--------|
| **Product Hunt** | **Live** | Public Atom feed `https://www.producthunt.com/feed`, AI-keyword filtered |
| **Hugging Face** | **Live** | Public API: trending models + popular Spaces |
| **GitHub** | **Live** | Unauthenticated search API (set `GITHUB_TOKEN` / `GH_TOKEN` for higher limits) |
| **X / Twitter** | **Live via file and/or API** | Always ingests `data/x_hits.json`; optional `X_BEARER_TOKEN` for recent search. Graceful empty fallback if neither has hits. |
| **RunningHub** | **Best-effort / TODO** | Homepage reachability check only — no stable public feed yet |
| **Higgsfield** | **Best-effort / TODO** | Same as above |
| **Manual JSON** | **Stub merge** | `data/manual_scan.json` for X/RH/HF placeholders or editor picks |


### X / Twitter ingest (`data/x_hits.json`)

Drop posts here when you don’t have (or don’t want to use) a bearer token — e.g. from the X MCP / public search. The scanner **always** reads this file.

Format: a JSON **array** of objects:

```json
[
  {
    "id": "2110974928497549580",
    "text": "Tracxn AI Suite Launched With ChatGPT, Claude, Gemini and MCP Integrations",
    "url": "https://x.com/sahyadristartup/status/2110974928497549580",
    "author": "sahyadristartup",
    "created_at": "2026-10-16T06:03:37.000Z"
  }
]
```

| Field | Required | Notes |
|-------|----------|--------|
| `text` | recommended | Post body (used for title/summary) |
| `url` | recommended | Permalink; built from `author`+`id` if omitted |
| `id` | optional | Tweet/post id (dedupe key) |
| `author` | optional | Username without `@` |
| `created_at` | optional | ISO timestamp |

If the file is missing, `scan-daily.py` creates `[]`.

Live API (optional):

```bash
export X_BEARER_TOKEN=...   # or TWITTER_BEARER_TOKEN
# optional override:
# export X_SEARCH_QUERY='("AI tool" OR "AI agent") launch -is:retweet lang:en'
python3 scripts/scan-daily.py
```

Queries default to AI tool/agent launch and Product Hunt AI chatter. File hits are merged with API hits and deduped by post id/URL.

### Cron example (daily ~09:00 Asia/Shanghai)

```bash
# crontab -e
0 9 * * * cd /workspace/ai-tool-map && /usr/bin/python3 scripts/scan-daily.py >> /tmp/ai-tool-map-scan.log 2>&1
```

After a scan, refresh the site (hard refresh if the browser cached JSON). Theme + language UI are unchanged.

## Project layout

```
ai-tool-map/
  index.html
  scenario.html
  tool.html
  daily.html
  weekly.html
  subscribe.html
  about.html
  llms.txt
  robots.txt
  sitemap.xml
  css/styles.css
  js/i18n.js
  js/app.js
  js/theme-boot.js
  scripts/scan-daily.py
  ops/
    STANDING-OPS.md
    monetization-gates.md
    newsletter-runbook.md
  data/
    scenarios.json
    tools.json
    daily.json
    weekly.json
    ui.json
    monetization.json
    manual_scan.json
    x_hits.json          # X posts for scanner ingest
    suggested_tools.json   # created by scanner
    scan_cache/
  README.md
```

## Seed / monetization notes

- Tools include real products with bilingual fields.
- `sponsored: true` + optional `affiliate_url` demonstrate monetization placements.
- Scanner may attach `source` / `source_url` on daily items; the UI ignores unknown fields safely.

## Gaps (still out of MVP)

- Subscribe / business / contact forms are front-end waitlists only
- WeChat/Alipay and Stripe checkout not live until configured
- No auth or CMS
- RunningHub / Higgsfield still need real public feeds; X works via `x_hits.json` and/or bearer token
- Suggested tools are not auto-published into `tools.json`
- Live on GitHub Pages and Hugging Face Space; China cloud + ICP still pending
- `sitemap.xml` / canonical / `llms.txt` still use Pages placeholder host until custom domain

## License

MVP scaffold for internal product exploration.
