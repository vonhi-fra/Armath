// Applies the saved theme before first paint (loaded synchronously in <head>) and wires the picker.
(function () {
  const KEY = "armath.theme";
  const THEMES = ["system", "light", "dark", "midnight", "paper", "terminal"];
  const darkQuery = window.matchMedia("(prefers-color-scheme: dark)");

  function saved() {
    try {
      const value = localStorage.getItem(KEY);
      return THEMES.includes(value) ? value : "system";
    } catch {
      return "system";
    }
  }

  function apply(choice) {
    const resolved = choice === "system" ? (darkQuery.matches ? "dark" : "light") : choice;
    document.documentElement.dataset.theme = resolved;
  }

  apply(saved());
  darkQuery.addEventListener("change", () => {
    if (saved() === "system") apply("system");
  });

  document.addEventListener("DOMContentLoaded", () => {
    const picker = document.getElementById("theme");
    picker.value = saved();
    picker.addEventListener("change", () => {
      try {
        localStorage.setItem(KEY, picker.value);
      } catch {
        // Storage unavailable: the theme still applies for this visit.
      }
      apply(picker.value);
    });
  });
})();
