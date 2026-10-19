# Daily scan item kind (going forward)

`data/daily.json` remains the automated scan feed. Editorial news lives in `data/news.json`.

New scan rows should include:

- `kind`: `"scan"` (default)
- `type`: optional hint — `product` | `research` | `other`

Do not set `status: published` on daily rows. To promote one into the news archive, rewrite it in `data/news.json` (or park it in `data/editorial_queue.json` with `kind: "news"` and `status: "pending"`). See `ops/EDITORIAL-QUEUE.md`.
