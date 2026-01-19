(function () {
  const STORAGE_KEY = "theme"; // "dark" | "light"
  const root = document.documentElement;
  const btn = document.getElementById("themeToggle");
  const icon = document.getElementById("themeIcon");

  function apply(theme) {
    if (theme === "light") {
      root.setAttribute("data-theme", "light");
      // When in light mode, show moon icon (tap to switch to dark)
      if (icon) icon.textContent = "🌙";
    } else {
      root.removeAttribute("data-theme");
      // When in dark mode, show sun icon (tap to switch to light)
      if (icon) icon.textContent = "☀️";
    }
  }

  // Default to dark
  const saved = localStorage.getItem(STORAGE_KEY);
  const initial = (saved === "light" || saved === "dark") ? saved : "dark";
  apply(initial);

  if (btn) {
    btn.addEventListener("click", function () {
      const isLight = root.getAttribute("data-theme") === "light";
      const next = isLight ? "dark" : "light";
      localStorage.setItem(STORAGE_KEY, next);
      apply(next);
    });
  }
})();
