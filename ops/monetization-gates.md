# Monetization gates (DRAFT)

**Status:** DRAFT — needs founder approval before hard-enforcing.  
**Scope:** AI Tool Map paid spots, affiliate CTAs as a growth channel, and newsletter / daily digest sponsors.  
**Content cadence:** **daily** (`data/daily.json` / `daily.html`) — aligned with site「每日更新」. `weekly.json` /「本周新品」is an optional rollup, not the primary gate.  
**Rule until gates are met OR founder overrides in writing:** keep monetization **soft** — no hard paywall on core browse (home, scenarios, tool detail, daily, weekly). Waitlist and “coming soon” payment UI are fine.

## Soft vs hard

| Soft (allowed anytime) | Hard (only after gates / override) |
|------------------------|------------------------------------|
| Demo `sponsored` badges on seed tools | Selling live paid placement inventory |
| Waitlist / business inquiry forms | Turning on WeChat / Alipay / Stripe checkout |
| Empty payment links in `data/monetization.json` | Publishing affiliate links as a primary CTA for most tools |
| Media kit / rate card as PDF draft | Digest/newsletter sponsor slots with paid deliverables |

## Proposed gates (concrete)

All of the following should be true **before** turning on paid spots / affiliates / sponsors as default ops — unless the founder overrides.

### A. Catalog readiness

- [ ] **≥ 50 curated tools** in `data/tools.json` (today ~38 — below gate)
- [ ] Each tool has bilingual one-liner + use/avoid + at least one scenario
- [ ] No more than a small share of entries are stubs / “TODO feed” only

### B. Editorial cadence (daily)

- [ ] **≥ 14 consecutive calendar days** of published「每日更新」in `data/daily.json` (or equivalent on the live site)
- [ ] Daily scanner has run successfully on a majority of those days (or manual daily outlines filled)
- [ ] Optional:「本周新品」rollup exists for the same period, but **does not replace** the daily gate

### C. Audience / engagement (pick one equivalent)

Meet **at least one**:

- [ ] **≥ 100 digest/newsletter waitlist** emails (aggregate: localStorage export + ESP list once connected), **or**
- [ ] **≥ 100** unique weekly visitors / UV on the public site (when analytics exists — do not invent numbers), **or**
- [ ] Founder-documented equivalent (e.g. 50 qualified biz inquiries, partner LOI)

### D. Ops readiness

- [ ] Legal entity + payment path decided (domestic ICP + WeChat/Alipay **or** overseas Paddle/Payoneer path)
- [ ] `ops/newsletter-runbook.md` followed for at least **5 practice daily drafts**
- [ ] Sponsor fulfillment checklist exists (screenshot, flight dates, disclosure)

## Override

Founder may green-light a **single** pilot sponsor or affiliate before all gates, by recording:

- date, who approved, what is sold, disclosure text, refund/cancel rule  
Store that note under `ops/overrides/` or append to this file under “Override log”.

## Override log

_(empty)_

## Related files

- `data/monetization.json` — payment flags and plan copy  
- `ops/newsletter-runbook.md` — daily digest process (+ optional weekly rollup)  
- `ops/STANDING-OPS.md` — maps the 9 standing requirements  
