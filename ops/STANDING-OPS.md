# Standing operations — AI Tool Map

User-adopted **9 standing requirements** (2026-10-16). This file maps each to routines and repo files.

**Site root:** `/workspace/ai-tool-map`  
**Public placeholder host:** https://goofugoofu.github.io/ (custom domain TBD)  
**Content cadence:** **daily**「每日更新」— site + digest ops stay in sync.「本周新品」is an optional weekly rollup.

## The 9 requirements

| # | Requirement | Status | How we cover it |
|---|-------------|--------|-----------------|
| 1 | **Monetizing when appropriate** | Soft until gates | `ops/monetization-gates.md` + `data/monetization.json`; no hard paywall on core browse |
| 2 | **Optimizing SEO** | NOW active | Unique titles/meta/OG on HTML; `sitemap.xml`; `robots.txt`; bilingual fields; **daily** content cadence |
| 3 | **Optimizing for chat bots (GEO)** | NOW active | `llms.txt`; JSON-LD on home + tool pages; structured `data/tools.json` |
| 4 | **Newsletter / digest** | Process NOW; send TBD | `ops/newsletter-runbook.md`; primary source `data/daily.json` / `daily.html`; optional `weekly.json` rollup; ESP TBD |
| 5 | **Watching feedback on X** | Ongoing | Ingest `data/x_hits.json`; scanner + Friday routine; report only when useful |
| 6 | **Continuously testing & improving** | Ongoing | Biweekly UX/copy/perf checklist; ship small fixes; no redesign-for-its-own-sake |
| 7 | **Watching for bugs** | Ongoing | Wednesday health check; dead-link / console / empty-state; user screenshots prioritized |
| 8 | **Updating you on progress** | Ongoing | Monday weekly brief (summarizes **daily** content ops + blockers) — numbers only when real analytics exist |
| 9 | **Keeping sponsors happy** | After first sponsor | Flight screenshots, dates, disclosure, renewal remind; see gates before selling inventory |

## Key files

| Path | Role |
|------|------|
| `llms.txt` | Agent/chatbot site map + citation rules |
| `robots.txt` | Allow crawlers; points at sitemap |
| `sitemap.xml` | Main pages + scenario/tool query URLs (base = GH Pages placeholder) |
| `ops/monetization-gates.md` | DRAFT thresholds before paid spots / affiliates / sponsors |
| `ops/newsletter-runbook.md` | Daily digest draft → review → send (+ optional weekly rollup) |
| `data/tools.json` / `scenarios.json` / `daily.json` / `weekly.json` | Content + feeds |
| `scripts/scan-daily.py` | Daily discovery pipeline |
| `README.md` | Deploy, monetization config, layout |

## Routines (Asia/Shanghai)

| Routine | When | Notes |
|---------|------|--------|
| AI Tool Map 周进度简报 | Mon ~09:00 | Progress; covers daily content ops |
| AI Tool Map 可用性巡检 | Wed ~11:00 | Bugs only when found |
| AI Tool Map X反馈巡视 | Fri ~10:00 | Feedback only when useful |

## NOW vs blocked

**Can run without entity/ICP:** SEO, llms.txt, bug watch, X watch, progress briefs, **daily** digest *drafts*, soft monetization UI.  

**Blocked or yellow until founder path chosen:** live WeChat/Alipay, hard sponsor inventory, ESP production sends, inventing analytics.

## Changelog

- 2026-10-16 — Adopted 9 requirements; added llms.txt, robots.txt, sitemap.xml, gates + newsletter runbook, JSON-LD helpers.
- 2026-10-16 — Content ops: all former「周更」gates/runbooks switched to **日更**, synced with site「每日更新」; weekly kept as optional rollup.
