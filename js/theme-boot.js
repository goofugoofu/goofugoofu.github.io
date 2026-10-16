(function () {
  var key = "ai-tool-map-theme";
  var allowed = ["system", "light", "dark", "soft-blue", "warm-sand", "high-contrast"];
  var t = localStorage.getItem(key) || "system";
  if (allowed.indexOf(t) === -1) t = "system";
  document.documentElement.setAttribute("data-theme", t);
})();
