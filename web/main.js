// Loads Pyodide and the armath wheel, then hands control to Python (armath.web.dom.main).
const PYODIDE_VERSION = "314.0.7";
const PYODIDE_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;

const status = document.getElementById("loading-status");

async function boot() {
  const [{ loadPyodide }, manifest] = await Promise.all([
    import(`${PYODIDE_URL}pyodide.mjs`),
    fetch("wheel.json").then((response) => {
      if (!response.ok) throw new Error(`wheel.json: HTTP ${response.status}`);
      return response.json();
    }),
  ]);
  const pyodide = await loadPyodide({ indexURL: PYODIDE_URL });
  status.textContent = "Starting Armath…";
  await pyodide.loadPackage(new URL(manifest.wheel, window.location.href).href);
  pyodide.runPython("from armath.web.dom import main\nmain()");
}

boot().catch((error) => {
  console.error(error);
  status.textContent = `Could not start Armath: ${error.message}`;
  document.body.classList.add("failed");
});
