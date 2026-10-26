# X feedback Friday routine — paste into UpdateRoutine

Last failure mode: generic **“Activity task failed”** with no useful summary. Prefer a short, resilient standing intent that uses **Grok Bot public X reads** (free `x` / built-in reads), never crashes the whole activity on empty or auth errors.

## Standing intent (copy/paste)

```text
【AI Tool Map · X 反馈巡视】每周五 Asia/Shanghai ~10:00。

目标：只汇报「针对本站/品牌」的有用反馈；没有就安静退出；工具/鉴权失败只报一次然后安静，不要让整个 Activity 崩溃。

品牌与站：
- AI Tool Map / 大模型情报
- goofugoofu / https://goofugoofu.github.io/

步骤：
1) 用 Grok Bot 公共 X 读取（search_posts_all 或等价只读搜索），不要估算积分、不要叫用户买 credits。
2) 依次搜索（每条 max_results≤20，最近 14 天即可）：
   - "AI Tool Map" OR goofugoofu OR goofugoofu.github.io
   - "大模型情报" (goofugoofu OR github.io OR "tool map")
   - goofugoofu
3) 过滤：丢掉泛泛的 “AI tool / map your workflow” 鸡汤；只保留明确提到本站、域名、品牌，或指向 goofugoofu.github.io 的帖。
4) 若有有用帖：用中文给站长 3–8 条要点（谁、链、在说什么、是否需跟进）。
5) 若无有用帖：回复一句「本周无针对本站的有效 X 反馈」即可（或按渠道习惯保持安静）。
6) 若工具缺失 / needsAuth / 鉴权错误 / 限流：用一两句话报告「X 读取失败：原因」，然后停止；不要重试死循环，不要改用未授权的登录绕过。

禁止：发帖、私信、点赞、关注；不要把无关 SEO 鸡汤当反馈。
```

## Suggested queries
```
("AI Tool Map" OR goofugoofu OR goofugoofu.github.io) -is:retweet
"大模型情报" (工具 OR 门户 OR 目录 OR github)
goofugoofu
url:goofugoofu.github.io
```

## Spot-check (2026-10-26)
- Broad “AI Tool Map” query mostly matched unrelated “map your workflow before buying AI tools” posts.
- One `@ImLateToAI` reply used the phrase “Our AI Tool Map” with a link — treat as possible brand-adjacent promo; verify the destination before counting as site feedback.
- Query `goofugoofu OR goofugoofu.github.io OR "大模型情报"` → no clear mentions of this site; one hit was the generic phrase「AI 大模型情报」in a model-rumor thread (`@NeoZineMind`), **not** our brand.
- Conclusion for parent: **no actionable site-specific X feedback** this check; routine should stay quiet unless a post clearly names us or our URL.
