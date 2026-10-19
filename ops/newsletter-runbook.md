# Digest runbook — 每日更新 / Daily new tools

**Cadence:** **daily** (align with site content ops and `data/daily.json`).  
**Source of truth:** `daily.html` from `data/daily.json` (+ linked tools in `data/tools.json`).  
**Optional rollup:**「本周新品」/`data/weekly.json` / `weekly.html` — weekend or Monday digest of the week’s daily items; **not** a substitute for daily publishing.  
**Send channel:** **TBD** — domestic ESP (once ICP + domain ready) **or** Beehiiv / similar overseas. Until connected, produce the draft and store waitlist only (`subscribe.html` → localStorage / mailto).

## Daily issue anatomy

1. **Subject** — bilingual option; Chinese primary for CN list, English for intl list  
2. **Intro** — short summary of today’s finds  
3. **Tool / update cards** — official name, one-liner, scenario tags, link to `tool.html?id=…` and vendor URL  
4. **CTA** — browse daily page + subscribe/business links  
5. **Disclosure** — if any sponsored item that day, label clearly

## Optional weekly rollup anatomy

Same as above, but sourced from that week’s daily entries → `weekly.json` highlights. Use for newsletter products that readers prefer weekly; still keep daily site feed current.

## Checklist: draft → review → send (daily)

### 0. Preconditions

- [ ] Today’s block exists in `data/daily.json` (run `python3 scripts/scan-daily.py` or edit manually)
- [ ] Linked `tool_ids` resolve in `tools.json`
- [ ] Language preference for this send decided (zh / en / both)

### 1. Draft

- [ ] Open `daily.html` locally (`python3 -m http.server`) and copy structure into ESP draft or markdown
- [ ] Or script: export day JSON → paste into template
- [ ] Subject line ≤ ~40 Chinese chars / ≤ ~60 Latin chars
- [ ] No invented metrics; no fake “#1 AI tool” claims
- [ ] Sponsored items marked

### 2. Review

- [ ] Founder or designated editor skim when first live; thereafter spot-check high-risk days
- [ ] Dead-link spot check on tool URLs
- [ ] Unsubscribe / contact footer present (once ESP is live)

### 3. Send

- [ ] Send channel configured (TBD: domestic ESP vs Beehiiv / etc.)
- [ ] Test send to self (first days / after template change)
- [ ] Send to list (or publish-only on site until ESP ready)
- [ ] Archive: save subject + date in `ops/newsletter-archive/` when first real send happens

### 4. After send

- [ ] Reply to feedback; log X mentions if relevant
- [ ] If sponsor was included: send flight screenshot + dates

## Soft monetization reminder

Do **not** sell digest/newsletter sponsor slots as a product until gates in `ops/monetization-gates.md` are met (or founder override). Practice drafts are encouraged anytime.

## Related

- Live page: `daily.html` (primary), `weekly.html` (optional rollup)  
- Waitlist UI: `subscribe.html`  
- Gates: `ops/monetization-gates.md`  
