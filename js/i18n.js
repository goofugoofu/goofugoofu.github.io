/**
 * Language + theme preferences.
 * Lang: ai-tool-map-lang (zh|en) — only one language shown at a time.
 * Theme: ai-tool-map-theme — system|light|dark|soft-blue|warm-sand|high-contrast
 */
const LANG_KEY = "ai-tool-map-lang";
const THEME_KEY = "ai-tool-map-theme";
const THEME_OPTIONS = [
  { id: "system", labelKey: "theme_system" },
  { id: "light", labelKey: "theme_light" },
  { id: "dark", labelKey: "theme_dark" },
  { id: "soft-blue", labelKey: "theme_soft_blue" },
  { id: "warm-sand", labelKey: "theme_warm_sand" },
  { id: "high-contrast", labelKey: "theme_high_contrast" },
];

let _siteConfig = null;

async function loadSiteConfig() {
  if (_siteConfig) return _siteConfig;
  try {
    _siteConfig = await fetch("data/monetization.json").then((r) => {
      if (!r.ok) throw new Error("monetization");
      return r.json();
    });
  } catch (_) {
    _siteConfig = {
      icp_number: "",
      contact_email: "",
      waitlist_mailto: "",
      wechat_pay_enabled: false,
      alipay_enabled: false,
    };
  }
  return _siteConfig;
}

function getLang() {
  const stored = localStorage.getItem(LANG_KEY);
  if (stored === "zh" || stored === "en") return stored;
  return "zh";
}

function setLang(lang) {
  localStorage.setItem(LANG_KEY, lang);
  document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";
}

function getTheme() {
  const t = localStorage.getItem(THEME_KEY) || "system";
  return THEME_OPTIONS.some((o) => o.id === t) ? t : "system";
}

function applyTheme(theme) {
  const t = THEME_OPTIONS.some((o) => o.id === theme) ? theme : "system";
  localStorage.setItem(THEME_KEY, t);
  document.documentElement.setAttribute("data-theme", t);
}

function tField(obj, base) {
  const lang = getLang();
  return obj[`${base}_${lang}`] ?? obj[`${base}_en`] ?? obj[`${base}_zh`] ?? "";
}

function pricingLabel(tier, ui) {
  if (tier === "free") return ui.pricing_free;
  if (tier === "subscription") return ui.pricing_subscription;
  if (tier === "usage") return ui.pricing_usage;
  return tier;
}

async function loadUI() {
  const res = await fetch("data/ui.json");
  const all = await res.json();
  return all[getLang()];
}

function applyStaticUI(ui) {
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (ui[key] != null) el.textContent = ui[key];
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    const key = el.getAttribute("data-i18n-placeholder");
    if (ui[key] != null) el.setAttribute("placeholder", ui[key]);
  });
  document.querySelectorAll("[data-i18n-title]").forEach((el) => {
    const key = el.getAttribute("data-i18n-title");
    if (ui[key] != null) el.setAttribute("title", ui[key]);
  });
  const btn = document.getElementById("lang-toggle");
  if (btn) {
    btn.textContent = ui.lang_btn;
    btn.title = ui.lang_btn_title;
  }
  const select = document.getElementById("theme-select");
  if (select) {
    THEME_OPTIONS.forEach((opt) => {
      const optionEl = select.querySelector(`option[value="${opt.id}"]`);
      if (optionEl && ui[opt.labelKey]) optionEl.textContent = ui[opt.labelKey];
    });
    select.value = getTheme();
  }
  const icpEl = document.getElementById("footer-icp");
  if (icpEl && ui) {
    const cfg = _siteConfig || {};
    const num = (cfg.icp_number || "").trim();
    icpEl.textContent = num
      ? `${ui.footer_icp_prefix || ""}${num}`
      : (ui.footer_icp_empty || "");
  }
}

function wireLangToggle(onChange) {
  const btn = document.getElementById("lang-toggle");
  if (!btn) return;
  btn.addEventListener("click", () => {
    const next = getLang() === "zh" ? "en" : "zh";
    setLang(next);
    if (typeof onChange === "function") onChange();
    else location.reload();
  });
}

function wireThemeSelect() {
  const select = document.getElementById("theme-select");
  if (!select) return;
  select.value = getTheme();
  select.addEventListener("change", () => {
    applyTheme(select.value);
  });
}

function headerHTML(active) {
  const themeOpts = THEME_OPTIONS.map(
    (o) => `<option value="${o.id}" data-i18n="${o.labelKey}">${o.id}</option>`
  ).join("");
  return `
    <header class="site-header">
      <div class="container header-inner">
        <a class="brand" href="index.html">
          <span class="brand-mark">🗺️</span>
          <span data-i18n="site_name">AI Tool Map</span>
        </a>
        <div class="header-controls">
          <nav class="nav" aria-label="Main">
            <a href="index.html" class="${active === "home" ? "active" : ""}" data-i18n="nav_home">Home</a>
            <a href="models.html" class="${active === "models" ? "active" : ""}" data-i18n="nav_models">Models</a>
            <a href="index.html#scenarios" class="${active === "tools" || active === "scenarios" ? "active" : ""}" data-i18n="nav_tools">Tools</a>
            <a href="news.html" class="${active === "news" ? "active" : ""}" data-i18n="nav_news">News</a>
            <a href="compare.html" class="${active === "compare" ? "active" : ""}" data-i18n="nav_compare">Compare</a>
            <a href="daily.html" class="${active === "daily" ? "active" : ""}" data-i18n="nav_daily">Daily</a>
            <a href="subscribe.html" class="${active === "subscribe" ? "active" : ""}" data-i18n="nav_subscribe">Subscribe</a>
            <a href="about.html" class="${active === "about" ? "active" : ""}" data-i18n="nav_about">About</a>
            <a href="search.html" class="nav-search ${active === "search" ? "active" : ""}" data-i18n="nav_search" aria-label="Search">Search</a>
          </nav>
          <div class="theme-wrap">
            <span class="theme-label" data-i18n="theme_label">Theme</span>
            <select id="theme-select" class="theme-select" aria-label="Theme">${themeOpts}</select>
          </div>
          <button type="button" id="lang-toggle" class="lang-toggle" data-i18n-title="lang_btn_title">EN</button>
        </div>
      </div>
    </header>
  `;
}

function footerHTML() {
  return `
    <footer class="site-footer">
      <div class="container">
        <p class="footer-tagline" data-i18n="footer">AI Tool Map · portal</p>
        <nav class="footer-nav" aria-label="Footer">
          <a href="models.html" data-i18n="nav_models">Models</a>
          <a href="news.html" data-i18n="nav_news">News</a>
          <a href="compare.html" data-i18n="nav_compare">Compare</a>
          <a href="search.html" data-i18n="nav_search">Search</a>
          <a href="daily.html" data-i18n="nav_daily">Daily</a>
          <a href="about.html" data-i18n="footer_about">About</a>
          <a href="subscribe.html" data-i18n="footer_subscribe">Subscribe</a>
        </nav>
        <p class="footer-icp" id="footer-icp" data-i18n="footer_icp_empty">ICP备案号：待备案通过后填写</p>
      </div>
    </footer>
  `;
}

applyTheme(getTheme());
setLang(getLang());
