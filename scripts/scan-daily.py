#!/usr/bin/env python3
"""
AI Tool Map — daily source scanner.

Fetches public Product Hunt / Hugging Face / GitHub feeds,
X (API and/or data/x_hits.json), merges optional stubs (RunningHub, Higgsfield)
and manual JSON,
dedupes, writes data/daily.json + updates data/weekly.json,
and optionally suggests new tools.json entries.

Usage:
  python3 scripts/scan-daily.py
  python3 scripts/scan-daily.py --dry-run
  python3 scripts/scan-daily.py --date 2026-10-24
  X_BEARER_TOKEN=... OPENAI_API_KEY=... python3 scripts/scan-daily.py

Default date is today in Asia/Shanghai. --date enables honest backfills
(same live sources, stamped with the given day). Cross-day dedupe skips
titles/scan_name already present on the previous calendar day.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DAILY_PATH = DATA / "daily.json"
WEEKLY_PATH = DATA / "weekly.json"
TOOLS_PATH = DATA / "tools.json"
MANUAL_PATH = DATA / "manual_scan.json"
X_HITS_PATH = DATA / "x_hits.json"
SUGGEST_PATH = DATA / "suggested_tools.json"
REPORT_PATH = DATA / "scan_cache" / "last_scan_report.json"

SHANGHAI = ZoneInfo("Asia/Shanghai")

UA = "AI-Tool-Map-Scanner/1.0 (+https://github.com/local/ai-tool-map; research bot)"
ATOM_NS = {"a": "http://www.w3.org/2005/Atom"}
AI_RE = re.compile(
    r"\b(ai|a\.i\.|llm|gpt|claude|gemini|agent|agents|ml|machine learning|"
    r"openai|anthropic|hugging\s?face|diffusion|transformer|copilot|"
    r"vibe.?coding|rag|model|chatbot|generative)\b",
    re.I,
)
TAG_HINTS = [
    (re.compile(r"\b(video|image|diffusion|comic|visual|runway|comfy)\b", re.I), "image-video"),
    (re.compile(r"\b(code|coding|devtools|github|ide|copilot|review)\b", re.I), "coding"),
    (re.compile(r"\b(agent|workflow|orchestr|mcp|autonom)\b", re.I), "agents"),
    (re.compile(r"\b(search|research|rag|retrieval|paper)\b", re.I), "research"),
    (re.compile(r"\b(office|meeting|slides?|ppt|docs?|email|productivity)\b", re.I), "office"),
    (re.compile(r"\b(writ|copy|blog|content|marketing)\b", re.I), "writing"),
]


def log(msg: str) -> None:
    print(msg, flush=True)


def http_get(url: str, timeout: int = 25, headers: dict | None = None) -> bytes:
    h = {"User-Agent": UA, "Accept": "*/*"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def http_get_json(url: str, **kwargs: Any) -> Any:
    raw = http_get(url, **kwargs)
    return json.loads(raw.decode("utf-8"))


def slugify(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower()).strip("-")
    return s[:48] or "item"


def guess_tags(text: str) -> list[str]:
    tags: list[str] = []
    for rx, tag in TAG_HINTS:
        if rx.search(text) and tag not in tags:
            tags.append(tag)
    return tags[:3] or ["research"]


def strip_html(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_key(name: str, url: str) -> str:
    host = ""
    try:
        host = urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        pass
    return f"{slugify(name)}|{host}"


# ---------- bilingual outlines ----------

def template_bilingual(name: str, blurb: str, source: str, tags: list[str]) -> dict[str, str]:
    blurb = (blurb or "").strip()
    short = blurb[:160] + ("…" if len(blurb) > 160 else "")
    tag_zh = {
        "writing": "写文案",
        "image-video": "做图/视频",
        "coding": "写代码",
        "agents": "智能体",
        "research": "研究检索",
        "office": "办公效率",
    }
    tags_zh = "、".join(tag_zh.get(t, t) for t in tags) or "通用"
    tags_en = ", ".join(tags) or "general"
    return {
        "title_zh": f"{name}（来自 {source}）",
        "title_en": f"{name} (via {source})",
        "summary_zh": f"扫描来源：{source}。{short or '今日扫描到的新条目。'} 相关场景：{tags_zh}。",
        "summary_en": f"Source: {source}. {short or 'Picked up in today’s scan.'} Scenarios: {tags_en}.",
    }


def maybe_llm_bilingual(name: str, blurb: str, source: str, tags: list[str]) -> dict[str, str] | None:
    """Optional: OPENAI_API_KEY or HF_TOKEN + HF inference. Falls back to None → template."""
    openai_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_KEY")
    prompt = (
        "Write bilingual short outline JSON with keys title_zh,title_en,summary_zh,summary_en "
        f"for an AI tool directory daily update. Tool={name!r} source={source!r} "
        f"blurb={blurb!r} tags={tags!r}. Keep each summary under 220 chars. JSON only."
    )
    if openai_key:
        try:
            body = json.dumps(
                {
                    "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                    "messages": [
                        {"role": "system", "content": "You write concise bilingual product blurbs. JSON only."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.4,
                }
            ).encode()
            req = urllib.request.Request(
                os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1/chat/completions"),
                data=body,
                headers={
                    "Authorization": f"Bearer {openai_key}",
                    "Content-Type": "application/json",
                    "User-Agent": UA,
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=40) as resp:
                data = json.loads(resp.read().decode())
            content = data["choices"][0]["message"]["content"]
            content = re.sub(r"^```json\s*|\s*```$", "", content.strip())
            parsed = json.loads(content)
            if all(k in parsed for k in ("title_zh", "title_en", "summary_zh", "summary_en")):
                return parsed
        except Exception as e:
            log(f"  [llm] OpenAI failed ({e}); using template")

    hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")
    if hf_token and os.environ.get("HF_LLM_MODEL"):
        try:
            model = os.environ["HF_LLM_MODEL"]
            body = json.dumps({"inputs": prompt, "parameters": {"max_new_tokens": 280}}).encode()
            req = urllib.request.Request(
                f"https://api-inference.huggingface.co/models/{model}",
                data=body,
                headers={
                    "Authorization": f"Bearer {hf_token}",
                    "Content-Type": "application/json",
                    "User-Agent": UA,
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode())
            text = data[0]["generated_text"] if isinstance(data, list) else str(data)
            m = re.search(r"\{[\s\S]*\}", text)
            if m:
                parsed = json.loads(m.group(0))
                if all(k in parsed for k in ("title_zh", "title_en", "summary_zh", "summary_en")):
                    return parsed
        except Exception as e:
            log(f"  [llm] HF inference failed ({e}); using template")
    return None


def bilingual_for(item: dict) -> dict[str, str]:
    llm = maybe_llm_bilingual(item["name"], item.get("blurb", ""), item["source"], item.get("tags", []))
    return llm or template_bilingual(item["name"], item.get("blurb", ""), item["source"], item.get("tags", []))


# ---------- sources ----------

def fetch_product_hunt(limit: int = 8) -> tuple[list[dict], str]:
    url = "https://www.producthunt.com/feed"
    try:
        raw = http_get(url)
        root = ET.fromstring(raw)
        out: list[dict] = []
        for entry in root.findall("a:entry", ATOM_NS):
            title = (entry.findtext("a:title", default="", namespaces=ATOM_NS) or "").strip()
            link_el = entry.find("a:link[@rel='alternate']", ATOM_NS)
            if link_el is None:
                link_el = entry.find("a:link", ATOM_NS)
            href = link_el.get("href") if link_el is not None else ""
            content = strip_html(entry.findtext("a:content", default="", namespaces=ATOM_NS) or "")
            # drop trailing Discussion | Link noise
            content = re.sub(r"\s*Discussion\s*\|\s*Link\s*$", "", content).strip()
            blob = f"{title} {content}"
            if not AI_RE.search(blob):
                continue
            out.append(
                {
                    "source": "Product Hunt",
                    "name": title,
                    "url": href.split("?")[0],
                    "blurb": content,
                    "tags": guess_tags(blob),
                    "live": True,
                }
            )
            if len(out) >= limit:
                break
        return out, "live"
    except Exception as e:
        return [], f"error: {e}"


def fetch_huggingface(limit: int = 6) -> tuple[list[dict], str]:
    items: list[dict] = []
    status_parts: list[str] = []
    try:
        models = http_get_json(
            "https://huggingface.co/api/models?sort=trendingScore&direction=-1&limit=12"
        )
        for m in models:
            mid = m.get("modelId") or m.get("id") or ""
            if not mid:
                continue
            pipe = m.get("pipeline_tag") or "model"
            likes = m.get("likes") or 0
            items.append(
                {
                    "source": "Hugging Face",
                    "name": mid.split("/")[-1][:60],
                    "url": f"https://huggingface.co/{mid}",
                    "blurb": f"Trending HF model ({pipe}), likes≈{likes}. Full id: {mid}",
                    "tags": guess_tags(f"{mid} {pipe} model"),
                    "live": True,
                }
            )
            if len(items) >= limit // 2 + 1:
                break
        status_parts.append("models:live")
    except Exception as e:
        status_parts.append(f"models:error:{e}")

    try:
        spaces = http_get_json(
            "https://huggingface.co/api/spaces?sort=likes&direction=-1&limit=8"
        )
        for s in spaces:
            sid = s.get("id") or ""
            if not sid:
                continue
            # skip ultra-generic test spaces with 0 likes already filtered by sort=likes
            likes = s.get("likes") or 0
            if likes < 50:
                continue
            sdk = s.get("sdk") or "space"
            items.append(
                {
                    "source": "Hugging Face Spaces",
                    "name": sid.split("/")[-1][:60],
                    "url": f"https://huggingface.co/spaces/{sid}",
                    "blurb": f"Popular HF Space ({sdk}), likes≈{likes}. id={sid}",
                    "tags": guess_tags(f"{sid} space demo {sdk}"),
                    "live": True,
                }
            )
            if len([i for i in items if "Spaces" in i["source"]]) >= max(2, limit // 3):
                break
        status_parts.append("spaces:live")
    except Exception as e:
        status_parts.append(f"spaces:error:{e}")

    return items[:limit], "; ".join(status_parts) if status_parts else "empty"


def fetch_github(limit: int = 6) -> tuple[list[dict], str]:
    # Prefer recently created AI-tagged repos with some stars to reduce noise
    since = (date.today() - timedelta(days=21)).isoformat()
    q = f"topic:artificial-intelligence created:>{since} stars:>5"
    url = (
        "https://api.github.com/search/repositories?"
        + urllib.parse.urlencode({"q": q, "sort": "stars", "order": "desc", "per_page": str(limit)})
    )
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": UA,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        data = http_get_json(url, headers=headers)
        out = []
        for repo in data.get("items") or []:
            name = repo.get("full_name") or repo.get("name") or "repo"
            desc = repo.get("description") or "AI-related GitHub repository"
            out.append(
                {
                    "source": "GitHub",
                    "name": name,
                    "url": repo.get("html_url") or f"https://github.com/{name}",
                    "blurb": f"{desc} ★{repo.get('stargazers_count', 0)}",
                    "tags": guess_tags(f"{name} {desc} code"),
                    "live": True,
                }
            )
        return out, "live"
    except Exception as e:
        # fallback query without date constraint
        try:
            q2 = "topic:llm stars:>100"
            url2 = (
                "https://api.github.com/search/repositories?"
                + urllib.parse.urlencode({"q": q2, "sort": "updated", "order": "desc", "per_page": str(limit)})
            )
            data = http_get_json(url2, headers=headers)
            out = []
            for repo in (data.get("items") or [])[:limit]:
                name = repo.get("full_name") or "repo"
                desc = repo.get("description") or "LLM-related repository"
                out.append(
                    {
                        "source": "GitHub",
                        "name": name,
                        "url": repo.get("html_url") or f"https://github.com/{name}",
                        "blurb": f"{desc} ★{repo.get('stargazers_count', 0)}",
                        "tags": guess_tags(f"{name} {desc} code"),
                        "live": True,
                    }
                )
            return out, f"live-fallback (primary error: {e})"
        except Exception as e2:
            return [], f"error: {e2}"


def ensure_x_hits_file() -> None:
    """Create empty data/x_hits.json if missing (MCP/public search drop target)."""
    if not X_HITS_PATH.exists():
        X_HITS_PATH.write_text("[]\n", encoding="utf-8")


def _x_item_from_hit(hit: dict, *, from_file: bool) -> dict | None:
    text = (hit.get("text") or hit.get("blurb") or "").replace("\n", " ").strip()
    tid = str(hit.get("id") or "").strip()
    url = (hit.get("url") or "").strip()
    if not url and tid:
        author = (hit.get("author") or "").lstrip("@")
        url = (
            f"https://x.com/{author}/status/{tid}"
            if author
            else f"https://x.com/i/web/status/{tid}"
        )
    if not text and not url:
        return None
    author = (hit.get("author") or "").lstrip("@")
    # Prefer a short product-ish name from the first clause of the tweet
    name_src = re.split(r"[.!:\n]", text)[0].strip() if text else ""
    name = name_src[:72] if name_src else (f"@{author}" if author else f"X post {tid or 'unknown'}")
    blurb = text[:220]
    if author:
        blurb = f"@{author}: {blurb}" if not blurb.startswith("@") else blurb
    return {
        "source": "X",
        "name": name,
        "url": url or f"https://x.com/search?q={urllib.parse.quote(name[:40])}",
        "blurb": blurb,
        "tags": guess_tags(text),
        "live": True,
        "x_id": tid or None,
        "x_from_file": from_file,
        "x_created_at": hit.get("created_at"),
    }


def load_x_hits_file(limit: int = 20) -> tuple[list[dict], str]:
    ensure_x_hits_file()
    try:
        raw = json.loads(X_HITS_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        return [], f"x_hits.json error: {e}"
    if not isinstance(raw, list):
        return [], "x_hits.json must be a JSON array"
    out: list[dict] = []
    for hit in raw:
        if not isinstance(hit, dict):
            continue
        item = _x_item_from_hit(hit, from_file=True)
        if item:
            out.append(item)
        if len(out) >= limit:
            break
    return out, f"file:{len(out)} from x_hits.json"


def fetch_x_api(limit: int = 8) -> tuple[list[dict], str]:
    token = os.environ.get("X_BEARER_TOKEN") or os.environ.get("TWITTER_BEARER_TOKEN")
    if not token:
        return [], "api:skipped (no X_BEARER_TOKEN)"

    # Multiple launch-oriented queries; X recent search allows one query per call.
    default_queries = [
        '("AI tool" OR "AI tools") (launch OR launched OR launches) -is:retweet lang:en',
        '("new AI agent" OR "AI agent launch" OR "AI agents") -is:retweet lang:en',
        '("Product Hunt" AI) (tool OR agent OR launch) -is:retweet lang:en',
        '(LLM OR "open model") (release OR launched OR launch) -is:retweet lang:en',
    ]
    env_q = os.environ.get("X_SEARCH_QUERY")
    queries = [env_q] if env_q else default_queries

    headers = {"Authorization": f"Bearer {token}", "User-Agent": UA}
    collected: list[dict] = []
    errors: list[str] = []
    per = max(10, min(limit * 2, 20))

    for q in queries:
        if len(collected) >= limit:
            break
        url = "https://api.twitter.com/2/tweets/search/recent?" + urllib.parse.urlencode(
            {
                "query": q,
                "max_results": per,
                "tweet.fields": "created_at,lang,author_id",
                "expansions": "author_id",
                "user.fields": "username",
            }
        )
        try:
            data = http_get_json(url, headers=headers)
            users = {
                u["id"]: u.get("username")
                for u in (data.get("includes") or {}).get("users") or []
                if u.get("id")
            }
            for tw in data.get("data") or []:
                tid = tw.get("id")
                text = (tw.get("text") or "").replace("\n", " ")
                author = users.get(tw.get("author_id") or "", "")
                hit = {
                    "id": tid,
                    "text": text,
                    "author": author,
                    "created_at": tw.get("created_at"),
                    "url": (
                        f"https://x.com/{author}/status/{tid}"
                        if author and tid
                        else f"https://x.com/i/web/status/{tid}"
                    ),
                }
                item = _x_item_from_hit(hit, from_file=False)
                if item:
                    collected.append(item)
                if len(collected) >= limit * 3:
                    break
        except Exception as e:
            errors.append(str(e))

    # Dedupe by x_id / url inside API batch
    seen: set[str] = set()
    out: list[dict] = []
    for it in collected:
        key = (it.get("x_id") or it.get("url") or it.get("name") or "").lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(it)
        if len(out) >= limit:
            break

    if out:
        status = f"api:live ({len(out)})"
        if errors:
            status += f"; partial errors: {errors[0][:80]}"
        return out, status
    if errors:
        return [], f"api:error ({errors[0][:120]})"
    return [], "api:live empty"


def fetch_x_twitter(limit: int = 8) -> tuple[list[dict], str]:
    """First-class X source: bearer API (optional) + always ingest data/x_hits.json."""
    ensure_x_hits_file()
    file_items, file_status = load_x_hits_file(limit=max(limit, 20))
    api_items, api_status = fetch_x_api(limit=limit)

    merged: list[dict] = []
    seen: set[str] = set()
    # Prefer file hits first (parent/MCP curated), then API
    for it in file_items + api_items:
        key = (it.get("x_id") or "").lower() or normalize_key(it.get("name", ""), it.get("url", ""))
        if key in seen:
            continue
        seen.add(key)
        merged.append(it)

    parts = [file_status, api_status]
    if merged:
        status = f"live ({len(merged)} hits; {'; '.join(parts)})"
    else:
        status = (
            "fallback empty — set X_BEARER_TOKEN and/or drop posts into data/x_hits.json "
            f"({'; '.join(parts)})"
        )
    return merged[: max(limit, len(file_items))], status


def fetch_runninghub() -> tuple[list[dict], str]:
    # Best-effort homepage fetch — no stable public JSON feed documented.
    url = "https://www.runninghub.ai"
    try:
        raw = http_get(url, timeout=15).decode("utf-8", errors="ignore")
        title = re.search(r"<title[^>]*>([^<]+)</title>", raw, re.I)
        name = strip_html(title.group(1)) if title else "RunningHub"
        # Only emit if page looks alive; still marked best-effort
        return (
            [
                {
                    "source": "RunningHub",
                    "name": name.split("|")[0].strip() or "RunningHub",
                    "url": url,
                    "blurb": "Best-effort homepage check OK. TODO: wire a real changelog/API when available.",
                    "tags": ["image-video"],
                    "live": False,
                }
            ],
            "best-effort homepage (no public feed API; TODO)",
        )
    except Exception as e:
        return [], f"stub/error: {e}"


def fetch_higgsfield() -> tuple[list[dict], str]:
    url = "https://higgsfield.ai"
    try:
        raw = http_get(url, timeout=15).decode("utf-8", errors="ignore")
        title = re.search(r"<title[^>]*>([^<]+)</title>", raw, re.I)
        name = strip_html(title.group(1)) if title else "Higgsfield"
        return (
            [
                {
                    "source": "Higgsfield",
                    "name": name.split("|")[0].strip() or "Higgsfield",
                    "url": url,
                    "blurb": "Best-effort homepage check OK. TODO: public changelog/API not wired.",
                    "tags": ["image-video"],
                    "live": False,
                }
            ],
            "best-effort homepage (no public feed API; TODO)",
        )
    except Exception as e:
        return [], f"stub/error: {e}"


def load_manual() -> tuple[list[dict], str]:
    if not MANUAL_PATH.exists():
        return [], "no manual_scan.json"
    try:
        data = json.loads(MANUAL_PATH.read_text(encoding="utf-8"))
        out = []
        for it in data.get("items") or []:
            if not it.get("enabled", True):
                continue
            out.append(
                {
                    "source": it.get("source") or "manual",
                    "name": it.get("name") or "manual item",
                    "url": it.get("url") or "",
                    "blurb": it.get("blurb_en") or it.get("blurb") or "",
                    "tags": it.get("tags") or ["research"],
                    "live": False,
                }
            )
        return out, f"merged {len(out)} enabled manual/stub items"
    except Exception as e:
        return [], f"error: {e}"


# ---------- persistence ----------

def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def match_tool_ids(name: str, url: str, tools: list[dict]) -> list[str]:
    name_l = name.lower()
    host = urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")
    hits = []
    for t in tools:
        tid = t.get("id", "")
        names = f"{t.get('name_en','')} {t.get('name_zh','')} {tid}".lower()
        turl = (t.get("url") or "").lower()
        if tid and tid in name_l.replace(" ", "-"):
            hits.append(tid)
            continue
        if t.get("name_en") and t["name_en"].lower() in name_l:
            hits.append(tid)
            continue
        if host and host in turl:
            # weak host match only for distinctive hosts
            if host not in ("github.com", "huggingface.co", "producthunt.com", "x.com", "twitter.com"):
                hits.append(tid)
    # unique preserve order
    seen = set()
    out = []
    for h in hits:
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out[:3]


def iso_week_meta(d: date) -> tuple[str, str, str, str]:
    iso = d.isocalendar()
    week = iso.week
    year = iso.year
    # Monday-Sunday of that ISO week
    start = d - timedelta(days=d.weekday())
    end = start + timedelta(days=6)
    wid = f"week-{year}-w{week:02d}-scan"
    label_zh = f"{year} 年第 {week} 周"
    label_en = f"Week {week}, {year}"
    dr = f"{start.isoformat()} — {end.isoformat()}"
    return wid, label_zh, label_en, dr


def title_norm(title: str) -> str:
    t = (title or "").lower().strip()
    t = re.sub(r"\s*\(via [^)]+\)\s*$", "", t).strip()
    t = re.sub(r"\s+", " ", t)
    return t


def filter_vs_previous_day(new_entries: list[dict], existing: list[dict], today: str) -> list[dict]:
    """Drop items that already appeared on the previous calendar day (same source+scan_name or near-identical title)."""
    today_d = date.fromisoformat(today)
    prev = (today_d - timedelta(days=1)).isoformat()
    prev_entries = [e for e in existing if e.get("date") == prev]
    prev_keys: set[str] = set()
    prev_titles: set[str] = set()
    for e in prev_entries:
        name = (e.get("scan_name") or "").lower().strip()
        src = (e.get("source") or "").lower().strip()
        if name:
            prev_keys.add(f"{src}|{name}")
        tn = title_norm(e.get("title_en") or e.get("title_zh") or "")
        if tn:
            prev_titles.add(tn)
    if not prev_keys and not prev_titles:
        return new_entries
    out: list[dict] = []
    skipped = 0
    for e in new_entries:
        name = (e.get("scan_name") or "").lower().strip()
        src = (e.get("source") or "").lower().strip()
        key = f"{src}|{name}"
        tn = title_norm(e.get("title_en") or e.get("title_zh") or "")
        if (name and key in prev_keys) or (tn and tn in prev_titles):
            skipped += 1
            continue
        out.append(e)
    if skipped:
        log(f"Cross-day dedupe vs {prev}: skipped {skipped}, kept {len(out)}")
    # Re-number ids so indices stay contiguous after filtering
    renumbered: list[dict] = []
    for i, e in enumerate(out, start=1):
        slug = slugify(e.get("scan_name") or e.get("title_en") or "item")[:24]
        ne = dict(e)
        ne["id"] = f"daily-{today}-{i}-{slug}"
        renumbered.append(ne)
    return renumbered


def build_daily_entries(items: list[dict], tools: list[dict], today: str) -> list[dict]:
    entries = []
    for i, it in enumerate(items, start=1):
        bi = bilingual_for(it)
        entry = {
            "id": f"daily-{today}-{i}-{slugify(it['name'])[:24]}",
            "date": today,
            "title_zh": bi["title_zh"],
            "title_en": bi["title_en"],
            "summary_zh": bi["summary_zh"],
            "summary_en": bi["summary_en"],
            "related_tool_ids": match_tool_ids(it["name"], it.get("url", ""), tools),
            "tags": it.get("tags") or ["research"],
            "source": it["source"],
            "source_url": it.get("url") or "",
            "scan_name": it["name"],
        }
        entries.append(entry)
    return entries


def merge_daily(existing: list[dict], new_entries: list[dict], today: str, keep: int = 100) -> list[dict]:
    # Replace all entries for the target date, keep other days, then sort newest-first
    # (stable within a date so backfills with --date do not jump ahead of later days).
    kept = [e for e in existing if e.get("date") != today]
    merged = new_entries + kept
    merged.sort(key=lambda e: e.get("date") or "", reverse=True)
    return merged[:keep]


def update_weekly(weekly: list[dict], new_entries: list[dict], today_d: date) -> list[dict]:
    wid, label_zh, label_en, dr = iso_week_meta(today_d)
    highlights_zh = []
    highlights_en = []
    tool_ids: list[str] = []
    by_source: dict[str, int] = {}
    for e in new_entries:
        by_source[e.get("source", "?")] = by_source.get(e.get("source", "?"), 0) + 1
        for tid in e.get("related_tool_ids") or []:
            if tid not in tool_ids:
                tool_ids.append(tid)
        highlights_zh.append(e["title_zh"][:80])
        highlights_en.append(e["title_en"][:80])

    src_list = "、".join(f"{k}×{v}" for k, v in by_source.items()) or "无"
    src_list_en = ", ".join(f"{k}×{v}" for k, v in by_source.items()) or "none"

    block = {
        "id": wid,
        "week_label_zh": label_zh,
        "week_label_en": label_en,
        "date_range": dr,
        "title_zh": f"本周扫描更新（{today_d.isoformat()}）",
        "title_en": f"Weekly scan update ({today_d.isoformat()})",
        "intro_zh": f"自动扫描写入。今日来源统计：{src_list}。可作通讯草稿。",
        "intro_en": f"Auto-scan write-up. Today's source counts: {src_list_en}. Reuse as newsletter draft.",
        "tool_ids": tool_ids[:12],
        "highlights_zh": highlights_zh[:8],
        "highlights_en": highlights_en[:8],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    # Replace same week id if present, else prepend
    others = [w for w in weekly if w.get("id") != wid]
    return [block] + others


def suggest_tools(items: list[dict], tools: list[dict]) -> list[dict]:
    existing_urls = {(t.get("url") or "").rstrip("/").lower() for t in tools}
    existing_names = {t.get("name_en", "").lower() for t in tools} | {t.get("id", "").lower() for t in tools}
    suggestions = []
    for it in items:
        if not it.get("live"):
            continue
        url = (it.get("url") or "").rstrip("/").lower()
        name = it["name"]
        if url in existing_urls or name.lower() in existing_names:
            continue
        if "github.com" in url or "huggingface.co" in url or "producthunt.com" in url:
            sid = slugify(name.split("/")[-1] if "/" in name else name)
            suggestions.append(
                {
                    "id": sid,
                    "name_zh": name,
                    "name_en": name,
                    "url": it.get("url"),
                    "scenarios": it.get("tags") or ["research"],
                    "one_liner_zh": (it.get("blurb") or "")[:120],
                    "one_liner_en": (it.get("blurb") or "")[:120],
                    "use_when_zh": "（待编辑）适合该工具定位的场景。",
                    "use_when_en": "(todo) When this tool’s positioning fits.",
                    "avoid_when_zh": "（待编辑）明确不适合的情况。",
                    "avoid_when_en": "(todo) When it is a poor fit.",
                    "pricing": "free",
                    "sources": [it["source"]],
                    "launched_or_updated_at": date.today().isoformat(),
                    "is_new_this_week": True,
                    "sponsored": False,
                    "affiliate_url": None,
                    "_suggested_by_scan": True,
                }
            )
    return suggestions[:15]


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan AI sources into daily/weekly JSON")
    parser.add_argument("--dry-run", action="store_true", help="Print report only; do not write JSON")
    parser.add_argument("--limit-per-source", type=int, default=6)
    parser.add_argument("--include-stubs", action="store_true", default=True)
    parser.add_argument("--no-stubs", action="store_true", help="Skip RunningHub/Higgsfield/manual stubs")
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="YYYY-MM-DD stamp for this run (default: today Asia/Shanghai). Use for weekday backfills.",
    )
    parser.add_argument(
        "--keep",
        type=int,
        default=100,
        help="Max daily.json entries to retain after merge (default 100).",
    )
    args = parser.parse_args()
    include_stubs = not args.no_stubs

    ensure_x_hits_file()
    if args.date:
        today_d = date.fromisoformat(args.date)
    else:
        today_d = datetime.now(SHANGHAI).date()
    today = today_d.isoformat()
    report: dict[str, Any] = {"date": today, "sources": {}, "counts": {}}

    log(f"AI Tool Map scanner — {today}")
    all_items: list[dict] = []

    fetchers = [
        ("product_hunt", lambda: fetch_product_hunt(args.limit_per_source)),
        ("huggingface", lambda: fetch_huggingface(args.limit_per_source)),
        ("github", lambda: fetch_github(args.limit_per_source)),
        ("x_twitter", lambda: fetch_x_twitter(max(8, args.limit_per_source))),
    ]
    if include_stubs:
        fetchers.extend(
            [
                ("runninghub", fetch_runninghub),
                ("higgsfield", fetch_higgsfield),
                ("manual", load_manual),
            ]
        )

    for key, fn in fetchers:
        log(f"→ {key} …")
        try:
            items, status = fn()
        except Exception as e:
            items, status = [], f"error: {e}"
        report["sources"][key] = {"status": status, "count": len(items)}
        log(f"  {status} ({len(items)} items)")
        all_items.extend(items)

    # Deduplicate by URL (preferred) then name|host
    seen: set[str] = set()
    seen_urls: set[str] = set()
    deduped: list[dict] = []
    for it in all_items:
        url = (it.get("url") or "").split("?")[0].rstrip("/").lower()
        if url:
            if url in seen_urls:
                continue
            seen_urls.add(url)
        key = normalize_key(it.get("name", ""), it.get("url", ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(it)
    report["counts"]["raw"] = len(all_items)
    report["counts"]["deduped"] = len(deduped)
    log(f"Deduped {len(all_items)} → {len(deduped)}")

    tools = load_json(TOOLS_PATH, [])
    daily_new = build_daily_entries(deduped, tools, today)
    existing_daily = load_json(DAILY_PATH, [])
    daily_new = filter_vs_previous_day(daily_new, existing_daily, today)
    merged_daily = merge_daily(existing_daily, daily_new, today, keep=args.keep)

    existing_weekly = load_json(WEEKLY_PATH, [])
    merged_weekly = update_weekly(existing_weekly, daily_new, today_d)

    suggestions = suggest_tools(deduped, tools)
    report["counts"]["daily_written"] = len(daily_new)
    report["counts"]["suggestions"] = len(suggestions)
    report["sample_titles"] = [e["title_en"] for e in daily_new[:5]]

    if args.dry_run:
        log("Dry run — not writing files.")
        log(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    if len(daily_new) == 0:
        log(f"ERROR: zero daily entries for {today} after dedupe — refusing to write empty day.")
        save_json(REPORT_PATH, report)
        return 1

    save_json(DAILY_PATH, merged_daily)
    save_json(WEEKLY_PATH, merged_weekly)
    save_json(SUGGEST_PATH, suggestions)
    save_json(REPORT_PATH, report)
    # Self-check: target date must be present after write
    verify = load_json(DAILY_PATH, [])
    wrote_n = sum(1 for e in verify if e.get("date") == today)
    if wrote_n == 0:
        log(f"ERROR: post-write assert failed — no entries with date={today}")
        return 1
    log(f"Wrote {DAILY_PATH} ({len(merged_daily)} total entries, {wrote_n} for {today})")
    log(f"Wrote {WEEKLY_PATH} (updated current week block)")
    log(f"Wrote {SUGGEST_PATH} ({len(suggestions)} suggestions)")
    log(f"Report → {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
