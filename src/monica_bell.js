/* Public job URL notification counter. Browser-scoped; no CV or user data sent. */
(function () {
  function start() {
    const area = document.getElementById("monica-inline");
    const bell = document.getElementById("monica-bell");
    const count = document.getElementById("monica-new-count");
    const hint = document.getElementById("monica-bell-hint");
    if (!area || !bell || !count) return;
    const urls = Array.from(new Set(Array.from(area.querySelectorAll('article a[href]'))
      .map(a => a.href).filter(u => u.startsWith("https://"))));
    const key = "ai-job-hunter:monica-seen:v1";
    let seen = [];
    try {
      const stored = localStorage.getItem(key);
      if (stored === null) {
        localStorage.setItem(key, JSON.stringify(urls));
        seen = urls.slice();
      } else {
        const saved = JSON.parse(stored);
        seen = Array.isArray(saved) ? saved : [];
      }
    } catch (_) {
      seen = urls.slice();
      if (hint) hint.textContent = "Histórico indisponível neste navegador";
    }
    const fresh = urls.filter(u => !seen.includes(u));
    count.textContent = String(fresh.length);
    bell.setAttribute("aria-label", fresh.length + " novas vagas desde a última visita");
    bell.addEventListener("click", () => {
      try {
        localStorage.setItem(key, JSON.stringify(Array.from(new Set([...seen, ...urls]))));
        count.textContent = "0";
        bell.setAttribute("aria-label", "Nenhuma vaga nova não vista");
        if (hint) hint.textContent = "Vagas atuais marcadas como vistas";
      } catch (_) {
        if (hint) hint.textContent = "Não foi possível salvar o histórico";
      }
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
