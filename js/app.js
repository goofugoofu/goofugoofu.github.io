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
