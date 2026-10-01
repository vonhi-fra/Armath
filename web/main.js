// Loads Pyodide and the armath wheel, then hands control to Python (armath.web.dom.main).
// scripts/build_site.py reads PYODIDE_URL to cache Pyodide for offline use: keep it one literal.
const PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/";

const status = document.getElementById("loading-status");

async function boot() {
  const [{ loadPyodide }, manifest] = await Promise.all([
    import(`${PYODIDE_URL}pyodide.mjs`),
    // GitHub Pages lets browsers reuse files for 10 minutes; a stale wheel.json would point at a
    // wheel that the last deploy removed. "no-cache" revalidates (cheap: usually a 304).
    fetch("wheel.json", { cache: "no-cache" }).then((response) => {
      if (!response.ok) throw new Error(`wheel.json: HTTP ${response.status}`);
      return response.json();
    }),
  ]);
  const pyodide = await loadPyodide({ indexURL: PYODIDE_URL });
  status.textContent = "Starting Armath…";
  // loadPackage only logs a failed download; fail here instead of at "No module named armath".
  const failures = [];
  await pyodide.loadPackage(new URL(manifest.wheel, window.location.href).href, {
    errorCallback: (message) => failures.push(message),
  });
  if (failures.length > 0) throw new Error(failures.join(" "));
  pyodide.runPython("from armath.web.dom import main\nmain()");
}

// Runs after boot, so the service worker caches files the browser has just downloaded instead
// of downloading them a second time.
async function workOffline() {
  if ("serviceWorker" in navigator) {
    await navigator.serviceWorker.register("sw.js");
  }
  // Without this, Chrome may clear saved sessions when the phone runs low on space.
  if (navigator.storage?.persist && !(await navigator.storage.persisted())) {
    await navigator.storage.persist();
  }
}

boot()
  .then(() => workOffline().catch((error) => console.warn("Offline support unavailable:", error)))
  .catch((error) => {
    console.error(error);
    status.textContent = `Could not start Armath: ${error.message}`;
    document.body.classList.add("failed");
  });
