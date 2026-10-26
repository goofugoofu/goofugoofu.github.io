# Daily scan hardening notes (2026-10-26)

## What went wrong around 2026-10-24

### Calendar fact check
In **Asia/Shanghai**, **2026-10-24 was Saturday**, not Friday.
- Fri 10-23 — daily scan **did run** (`963a21b`, 27 items, commit ~08:06 +0800)
- Sat 10-24 / Sun 10-25 — no commits (weekend skip by standing ops)
- Mon 10-26 — scan resumed (`f9f9715`)

The Monday weekly brief labeled “10/24 周五缺一天” — that weekday label was **wrong**. The real Friday (10-23) succeeded. The visible “hole” on the live site for 10-24 was expected under weekend policy; we still **backfilled 10-24** on request for continuity.

### Silent data loss (more serious)
`merge_daily(..., keep=50)` previously capped `daily.json` at **50** rows. With ~27 items/day, keeping only two days meant **10-20 / 10-21 / 10-22 disappeared** from the live file even though git history still has those commits. Homepage / daily page therefore looked thinner than the commit log.

### Other reliability gaps
- Default date used `date.today()` (box TZ) instead of explicit **Asia/Shanghai**.
- No `--date` flag → weekday backfills were awkward.
- Consecutive weekdays often looked copy-pasted (PH/HF/GitHub + stale `x_hits.json`) with no cross-day title dedupe.
- No post-write assert that the target date count > 0.
- X API skipped without `X_BEARER_TOKEN` (file fallback only).

## Code changes shipped
In `scripts/scan-daily.py`:
1. `--date YYYY-MM-DD` (default = today **Asia/Shanghai**)
2. `--keep` (default **100**) + sort merged rows **newest date first** (stable within day) so backfills do not jump ahead of later days
3. Cross-day dedupe vs **previous calendar day** (`source|scan_name` or near-identical title, stripping `(via …)`)
4. Refuse to write / exit 1 if target day would be empty; re-load assert after write

## Recommended routine prompt patches (parent → UpdateRoutine)

Use Asia/Shanghai weekday gate explicitly:

```text
【AI Tool Map 日更】Asia/Shanghai 工作日 08:00（周一至周五；周末跳过并安静退出）。
1) cd /workspace/ai-tool-map && python3 scripts/scan-daily.py
   （需要回填某日时：python3 scripts/scan-daily.py --date YYYY-MM-DD）
2) 若 exit≠0 或 last_scan_report 里 counts.daily_written==0 → 大声报错，不要假装成功。
3) 自检：python3 -c "import json;from datetime import datetime;from zoneinfo import ZoneInfo;d=json.load(open('data/daily.json'));t=datetime.now(ZoneInfo('Asia/Shanghai')).date().isoformat();n=sum(1 for x in d if x.get('date')==t);assert n>0, f'no entries for {t}';print(t,n)"
4) 同步到 /workspace/goofugoofu.github.io（daily.json / weekly.json / suggested_tools.json / scan_cache/last_scan_report.json）
5) 用 GitHub MCP push_files 推 goofugoofu/goofugoofu.github.io main（每批≤4 文件，$file: 路径）；确认 raw.githubusercontent 含今日 date。
6) 可选：写 ops/newsletter-archive/YYYY-MM-DD-daily-draft.md，不发信（发送通道仍空）。
不要编造产品；来源失败就在报告里标明并继续其他源。
```

Also update the Monday brief so it counts **Mon–Fri Asia/Shanghai**, not mislabeled weekend dates.

## After each push — self-check
```bash
python3 - <<'PY'
import json, urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo
today = datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()
url = "https://raw.githubusercontent.com/goofugoofu/goofugoofu.github.io/main/data/daily.json"
data = json.load(urllib.request.urlopen(url, timeout=30))
n = sum(1 for x in data if x.get("date") == today)
print("raw", today, n)
assert n > 0, f"FAIL: raw has 0 entries for {today}"
PY
```

## Backfill record
- 2026-10-26 ops run: `python3 scripts/scan-daily.py --date 2026-10-24` → **14** items after cross-day dedupe vs 10-23 (skipped 13 duplicates).
