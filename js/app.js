async function fetchJSON(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Failed to load ${path}`);
  return res.json();
}

function qs(name) {
  return new URLSearchParams(location.search).get(name);
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

function emptyState(ui, kind) {
  const msg = kind === "search" ? ui.no_search : ui.no_tools;
  return `<div class="empty"><strong>${escapeHTML(msg)}</strong></div>`;
}

async function bootPage({ active, render }) {
  applyTheme(getTheme());
  setLang(getLang());
  const shell = document.getElementById("app");
  shell.innerHTML = headerHTML(active) + `<main id="main" class="container"></main>` + footerHTML();
  const ui = await loadUI();
  applyStaticUI(ui);
  wireThemeSelect();
  wireLangToggle(async () => {
    const nextUI = await loadUI();
    applyStaticUI(nextUI);
    await render(nextUI);
  });
  await render(ui);
}
