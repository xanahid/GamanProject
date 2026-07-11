// Tiny toast helper shared by every server-rendered page.
// React widgets call window.gamanToast(...) too, so there's one consistent
// notification style across the Django-rendered shell and mounted widgets.
window.gamanToast = function (message, durationMs = 3200) {
  const el = document.getElementById("toast");
  if (!el) return;
  el.textContent = message;
  el.classList.remove("opacity-0", "translate-y-2", "pointer-events-none");
  el.classList.add("opacity-100", "translate-y-0");
  clearTimeout(window.__gamanToastTimer);
  window.__gamanToastTimer = setTimeout(() => {
    el.classList.add("opacity-0", "translate-y-2", "pointer-events-none");
    el.classList.remove("opacity-100", "translate-y-0");
  }, durationMs);
};

// Reads Django's CSRF cookie so fetch() calls from inline page scripts
// (login/signup forms) can include it without a template-rendered token.
window.getCsrfToken = function () {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? match[1] : "";
};
