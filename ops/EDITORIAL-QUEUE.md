# Editorial queue

Light review before anything hits the homepage or model/tool/news catalogs.

## Files

| File | Role |
|------|------|
| `data/editorial_queue.json` | Candidates waiting on a human |
| `data/models.json` | Published model cards |
| `data/tools.json` | Published tools |
| `data/news.json` | Published editorial news (`status: "published"`) |
| `data/daily.json` | Automated scan feed (not the news archive) |
| `data/suggested_tools.json` | Scanner leftovers — source of pending tool candidates |

## Statuses

- `pending` — not public. Do not render on home.
- `approved` — editor accepted; **copy the record into the publish file** and set this item to `approved` (or remove it).
- `rejected` — do not publish. Keep the row so we do not re-queue the same source blindly.

## Flow

1. **Candidate.** Scanner or a person adds an object:

```json
{
  "id": "eq-example",
  "kind": "tool",
  "title_zh": "名称",
  "title_en": "Name",
  "source_url": "https://example.com",
  "submitted_at": "2026-10-19",
  "status": "pending",
  "notes": "why it is here"
}
```

`kind` is `model` | `tool` | `news`.

2. **Review.** Check the official page. Fill bilingual copy, pricing note (“以官网为准” / “check official pricing”), and whether it is a duplicate.

3. **Publish.**
   - `model` → append to `data/models.json` (required fields match existing cards).
   - `tool` → append to `data/tools.json` with real `use_when` / `avoid_when` (not the scan placeholder).
   - `news` → append to `data/news.json` with `status: "published"` and a `type` of `release|pricing|policy|research|product`.

4. **Daily vs news.** `daily.json` stays the raw scan. Promote a scan item to `news.json` only after a rewrite. Optional fields going forward on daily items: `kind: "scan"` and `type` (`product` | `research` | `other`) so the scanner can flag news-like rows. The homepage “今日要闻” reads `news.json`, not the scan.

5. **Do not auto-fill the homepage.** The home page only lists published news and featured models. The queue itself is not rendered on the site.

## Seed

Current pending rows come from the latest Product Hunt scan (`suggested_tools.json`) plus two editorial holds (unconfirmed next GPT flagship, Krea 3 scan blurb).
