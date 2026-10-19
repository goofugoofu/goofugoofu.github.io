async function fetchJSON(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Failed to load ${path}`);
  return res.json();
}

function qs(name) {
  return new URLSearchParams(location.search).get(name);
}

function ensureMeta(attr, key, value) {
  if (!value) return;
  let el = document.head.querySelector(`meta[${attr}="${key}"]`);
  if (!el) {
    el = document.createElement("meta");
    el.setAttribute(attr, key);
    document.head.appendChild(el);
  }
  el.setAttribute("content", value);
}

/** Set document title + description + basic Open Graph / Twitter tags. */
function setPageMeta({ title, description, type }) {
  if (title) document.title = title;
  if (description) {
    ensureMeta("name", "description", description);
    ensureMeta("property", "og:description", description);
    ensureMeta("name", "twitter:description", description);
  }
  if (title) {
    ensureMeta("property", "og:title", title);
    ensureMeta("name", "twitter:title", title);
  }
  ensureMeta("property", "og:type", type || "website");
  ensureMeta("property", "og:url", location.href.split("#")[0]);
  ensureMeta("property", "og:site_name", "AI Tool Map");
  ensureMeta("property", "og:locale", getLang() === "en" ? "en_US" : "zh_CN");
  ensureMeta("name", "twitter:card", "summary");
  ensureMeta("name", "robots", "index,follow");
}

/** Replace or insert a JSON-LD script by id (safe for SPA-style page boots). */
function injectJsonLd(id, data) {
  if (!data) return;
  let el = document.getElementById(id);
  if (!el) {
    el = document.createElement("script");
    el.type = "application/ld+json";
    el.id = id;
    document.head.appendChild(el);
  }
  el.textContent = JSON.stringify(data);
}

/** SoftwareApplication JSON-LD for a tools.json entry. */
function toolJsonLd(tool) {
  if (!tool) return null;
  const name = tool.name_en || tool.name_zh || tool.id;
  const desc = tool.one_liner_en || tool.one_liner_zh || "";
  const page = new URL(`tool.html?id=${encodeURIComponent(tool.id)}`, location.href).href;
  const obj = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name,
    description: desc,
    url: tool.url || page,
    applicationCategory: "BusinessApplication",
    operatingSystem: "Web",
    inLanguage: ["zh-CN", "en"],
    isAccessibleForFree: tool.pricing === "free" || tool.pricing === "freemium",
  };
  if (tool.launched_or_updated_at) obj.dateModified = tool.launched_or_updated_at;
  return obj;
}

function toolCardHTML(tool, ui) {
  const name = tField(tool, "name");
  const one = tField(tool, "one_liner");
  const badges = [];
  badges.push(`<span class="badge pricing">${pricingLabel(tool.pricing, ui)}</span>`);
  if (tool.is_new_this_week) badges.push(`<span class="badge new">${ui.new_badge}</span>`);
  if (tool.sponsored) badges.push(`<span class="badge sponsored">${ui.sponsored}</span>`);
  return `
    <a class="card tool-list-item" href="tool.html?id=${encodeURIComponent(tool.id)}">
      <h3>${escapeHTML(name)}</h3>
      <p class="one-liner">${escapeHTML(one)}</p>
      <div class="meta-row">${badges.join("")}</div>
    </a>
  `;
}

function escapeHTML(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function scenarioMapFrom(list) {
  const m = {};
  list.forEach((s) => { m[s.id] = s; });
  return m;
}

/**
 * kind: "search" | "tools" | "daily" | "weekly"
 * opt.ctaHref / opt.ctaLabel for a secondary action
 */
function emptyState(ui, kind, opt) {
  const map = {
    search: ui.no_search,
    tools: ui.no_tools,
    daily: ui.empty_daily || ui.no_tools,
    weekly: ui.empty_weekly || ui.no_tools,
    news: ui.no_news || ui.no_tools,
    models: ui.no_models || ui.no_tools,
  };
  const msg = map[kind] || ui.no_tools;
  const ctaHref = (opt && opt.ctaHref) || "index.html";
  const ctaLabel = (opt && opt.ctaLabel) || ui.empty_cta_home || ui.back_home;
  return `
    <div class="empty">
      <strong>${escapeHTML(msg)}</strong>
      <a class="empty-cta" href="${escapeHTML(ctaHref)}">${escapeHTML(ctaLabel)}</a>
    </div>
  `;
}

async function bootPage({ active, render, metaKey }) {
  applyTheme(getTheme());
  setLang(getLang());
  await loadSiteConfig();
  const shell = document.getElementById("app");
  shell.innerHTML = headerHTML(active) + `<main id="main" class="container"></main>` + footerHTML();
  const ui = await loadUI();
  if (metaKey && ui[metaKey]) {
    const pageTitle = active === "home"
      ? `${ui.site_name}`
      : `${ui[metaKey.replace("meta_desc_", "") + "_title"] || ui.site_name} · ${ui.site_name}`;
    // Prefer explicit titles from ui when available
    const titleMap = {
      meta_desc_home: ui.site_name,
      meta_desc_daily: `${ui.daily_title} · ${ui.site_name}`,
      meta_desc_weekly: `${ui.weekly_title} · ${ui.site_name}`,
      meta_desc_subscribe: `${ui.subscribe_title} · ${ui.site_name}`,
      meta_desc_about: `${ui.about_title} · ${ui.site_name}`,
      meta_desc_models: `${ui.models_title} · ${ui.site_name}`,
      meta_desc_news: `${ui.news_title} · ${ui.site_name}`,
      meta_desc_compare: `${ui.compare_title} · ${ui.site_name}`,
      meta_desc_search: `${ui.search_title} · ${ui.site_name}`,
    };
    setPageMeta({
      title: titleMap[metaKey] || pageTitle,
      description: ui[metaKey],
    });
  }
  applyStaticUI(ui);
  wireThemeSelect();
  wireLangToggle(async () => {
    const nextUI = await loadUI();
    applyStaticUI(nextUI);
    if (metaKey && nextUI[metaKey]) {
      const titleMap = {
        meta_desc_home: nextUI.site_name,
        meta_desc_daily: `${nextUI.daily_title} · ${nextUI.site_name}`,
        meta_desc_weekly: `${nextUI.weekly_title} · ${nextUI.site_name}`,
        meta_desc_subscribe: `${nextUI.subscribe_title} · ${nextUI.site_name}`,
        meta_desc_about: `${nextUI.about_title} · ${nextUI.site_name}`,
        meta_desc_models: `${nextUI.models_title} · ${nextUI.site_name}`,
        meta_desc_news: `${nextUI.news_title} · ${nextUI.site_name}`,
        meta_desc_compare: `${nextUI.compare_title} · ${nextUI.site_name}`,
        meta_desc_search: `${nextUI.search_title} · ${nextUI.site_name}`,
      };
      setPageMeta({
        title: titleMap[metaKey] || nextUI.site_name,
        description: nextUI[metaKey],
      });
    }
    await render(nextUI);
  });
  await render(ui);
}

/** Format context window for display. */
function formatContext(n, ui) {
  if (n == null || n === "") return "—";
  const num = Number(n);
  if (!Number.isFinite(num)) return String(n);
  if (num >= 1000000) return `${(num / 1000000).toFixed(num % 1000000 === 0 ? 0 : 1)}M`;
  if (num >= 1000) return `${Math.round(num / 1000)}K`;
  return String(num);
}

function isOpenLicense(license) {
  const L = String(license || "").toLowerCase();
  return L.includes("open") || L.includes("apache") || L.includes("mit") || L.includes("llama") || L === "modified-mit";
}

function licenseLabel(license, ui) {
  return isOpenLicense(license) ? (ui.license_open || "Open") : (ui.license_proprietary || "Proprietary");
}

function newsTypeLabel(type, ui) {
  const map = {
    release: ui.news_type_release,
    pricing: ui.news_type_pricing,
    policy: ui.news_type_policy,
    research: ui.news_type_research,
    product: ui.news_type_product,
  };
  return map[type] || type;
}

function modalityLabel(m, ui) {
  const map = {
    text: ui.modality_text,
    image: ui.modality_image,
    audio: ui.modality_audio,
    video: ui.modality_video,
  };
  return map[m] || m;
}

function modelCardHTML(model, ui) {
  const name = tField(model, "name");
  const card = tField(model, "card");
  const badges = [];
  badges.push(`<span class="badge">${escapeHTML(tField(model, "vendor"))}</span>`);
  badges.push(`<span class="badge">${escapeHTML(licenseLabel(model.license, ui))}</span>`);
  if (model.featured) badges.push(`<span class="badge new">${escapeHTML(ui.featured_badge || "Featured")}</span>`);
  const mods = (model.modalities || []).map((m) => modalityLabel(m, ui)).join(" · ");
  return `
    <a class="card tool-list-item model-card" href="model.html?id=${encodeURIComponent(model.id)}">
      <h3>${escapeHTML(name)}</h3>
      <p class="one-liner">${escapeHTML(card)}</p>
      <div class="meta-row">${badges.join("")}<span class="badge muted-badge">${escapeHTML(formatContext(model.context_window))} ${escapeHTML(ui.tokens_label || "tok")}</span></div>
      <p class="small muted" style="margin:0.4rem 0 0">${escapeHTML(mods)}</p>
    </a>
  `;
}

function modelJsonLd(model) {
  if (!model) return null;
  const name = model.name_en || model.name_zh || model.id;
  const desc = model.card_en || model.card_zh || "";
  const page = new URL(`model.html?id=${encodeURIComponent(model.id)}`, location.href).href;
  return {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name,
    description: desc,
    url: model.official_url || page,
    applicationCategory: "DeveloperApplication",
    operatingSystem: "Web",
    inLanguage: ["zh-CN", "en"],
    creator: {
      "@type": "Organization",
      name: model.vendor_en || model.vendor_zh || "",
    },
  };
}

function newsItemHTML(n, ui) {
  const type = newsTypeLabel(n.type, ui);
  return `
    <article class="feed-item">
      <div class="date">${escapeHTML(n.date)} · <span class="badge">${escapeHTML(type)}</span></div>
      <h3>${escapeHTML(tField(n, "title"))}</h3>
      <p>${escapeHTML(tField(n, "summary"))}</p>
      <div class="feed-links">
        ${n.source_url ? `<a class="pill-link" href="${escapeHTML(n.source_url)}" target="_blank" rel="noopener noreferrer">${escapeHTML(ui.source_label || "Source")}: ${escapeHTML(n.source || "")}</a>` : ""}
      </div>
    </article>
  `;
}

function cellText(cells, colId) {
  if (!cells) return "";
  const lang = getLang();
  const keyed = cells[`${colId}_${lang}`] ?? cells[`${colId}_en`] ?? cells[`${colId}_zh`];
  if (keyed != null && keyed !== "") return keyed;
  return cells[colId] != null ? cells[colId] : "";
}

/**
 * Simple client-side search across models, tools, news (+ optional daily).
 * Rank: name hit (3) > summary/one-liner (2) > other blob (1)
 */
function searchCorpus(q, { models, tools, news, daily }) {
  const query = String(q || "").trim().toLowerCase();
  if (!query) return [];
  const results = [];
  const scoreBlob = (nameParts, summaryParts, otherParts) => {
    const name = nameParts.join(" ").toLowerCase();
    const summary = summaryParts.join(" ").toLowerCase();
    const other = otherParts.join(" ").toLowerCase();
    let score = 0;
    if (name.includes(query)) score += 3;
    if (summary.includes(query)) score += 2;
    if (other.includes(query)) score += 1;
    return score;
  };
  (models || []).forEach((m) => {
    const score = scoreBlob(
      [m.name_zh, m.name_en, m.id],
      [m.card_zh, m.card_en],
      [m.vendor_zh, m.vendor_en, m.family, ...(m.tags || []), ...(m.strengths_zh || []), ...(m.strengths_en || [])]
    );
    if (score > 0) {
      results.push({
        type: "model",
        score,
        id: m.id,
        href: `model.html?id=${encodeURIComponent(m.id)}`,
        title_zh: m.name_zh,
        title_en: m.name_en,
        summary_zh: m.card_zh,
        summary_en: m.card_en,
      });
    }
  });
  (tools || []).forEach((t) => {
    const score = scoreBlob(
      [t.name_zh, t.name_en, t.id],
      [t.one_liner_zh, t.one_liner_en],
      [...(t.scenarios || []), t.pricing]
    );
    if (score > 0) {
      results.push({
        type: "tool",
        score,
        id: t.id,
        href: `tool.html?id=${encodeURIComponent(t.id)}`,
        title_zh: t.name_zh,
        title_en: t.name_en,
        summary_zh: t.one_liner_zh,
        summary_en: t.one_liner_en,
      });
    }
  });
  (news || []).forEach((n) => {
    if (n.status && n.status !== "published") return;
    const score = scoreBlob(
      [n.title_zh, n.title_en, n.id],
      [n.summary_zh, n.summary_en],
      [n.type, n.source, ...(n.related_model_ids || [])]
    );
    if (score > 0) {
      results.push({
        type: "news",
        score,
        id: n.id,
        href: `news.html#${encodeURIComponent(n.id)}`,
        title_zh: n.title_zh,
        title_en: n.title_en,
        summary_zh: n.summary_zh,
        summary_en: n.summary_en,
        date: n.date,
      });
    }
  });
  (daily || []).forEach((d) => {
    const score = scoreBlob(
      [d.title_zh, d.title_en, d.id],
      [d.summary_zh, d.summary_en],
      [d.source, d.scan_name]
    );
    if (score > 0) {
      results.push({
        type: "daily",
        score: score * 0.8,
        id: d.id,
        href: `daily.html`,
        title_zh: d.title_zh,
        title_en: d.title_en,
        summary_zh: d.summary_zh,
        summary_en: d.summary_en,
        date: d.date,
      });
    }
  });
  results.sort((a, b) => b.score - a.score || String(b.date || "").localeCompare(String(a.date || "")));
  return results;
}

function typeBadge(type, ui) {
  const map = {
    model: ui.type_model,
    tool: ui.type_tool,
    news: ui.type_news,
    daily: ui.type_daily,
  };
  return map[type] || type;
}
