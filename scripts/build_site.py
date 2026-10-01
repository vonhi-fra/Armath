"""Assemble the static site in ``site/``: the files from ``web/`` plus a freshly built wheel.

Usage: ``uv run python scripts/build_site.py``, then serve ``site/`` with any static server.
"""

import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
SITE = ROOT / "site"
SERVICE_WORKER = "sw.js"
BUILD_PLACEHOLDER = "__BUILD__"
# What loadPyodide fetches (checked in the browser for v314.0.7). Anything else Pyodide loads
# is cached by the service worker on first use.
PYODIDE_FILES = (
    "pyodide.mjs",
    "pyodide.asm.mjs",
    "pyodide.asm.wasm",
    "python_stdlib.zip",
    "pyodide-lock.json",
)
_PYODIDE_URL = re.compile(r'const PYODIDE_URL = "([^"]+)";')


def build_wheel(out_dir: Path) -> Path:
    subprocess.run(["uv", "build", "--wheel", "--out-dir", str(out_dir)], cwd=ROOT, check=True)
    (wheel,) = out_dir.glob("armath-*.whl")
    return wheel


def pyodide_url(main_js: str) -> str:
    """The Pyodide CDN folder that ``main.js`` loads from (its single source of truth)."""
    match = _PYODIDE_URL.search(main_js)
    if match is None:
        raise ValueError("main.js does not define PYODIDE_URL")
    return match.group(1)


def offline_files(site: Path) -> list[str]:
    """Site paths the service worker caches up front: all the app loads ("./" is the page)."""
    paths = []
    for path in sorted(site.rglob("*")):
        relative = path.relative_to(site).as_posix()
        skipped = relative == SERVICE_WORKER or path.name.startswith(".") or path.suffix == ".txt"
        if path.is_file() and not skipped:
            paths.append("./" if relative == "index.html" else relative)
    return paths


def build_id(site: Path) -> str:
    """A hash of every file (the service worker still unstamped): changes with the site."""
    digest = hashlib.sha256()
    for path in sorted(site.rglob("*")):
        if path.is_file():
            digest.update(path.relative_to(site).as_posix().encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()[:12]


def stamp_service_worker(site: Path) -> str:
    """Write this build's id and file lists into the service worker; return the id.

    A changed service worker is what makes browsers install the new version and drop the old
    cache, so the stamp must change with every build that changes the site.
    """
    worker = site / SERVICE_WORKER
    source = worker.read_text(encoding="utf-8")
    if source.count(BUILD_PLACEHOLDER) != 1:
        raise ValueError(f"{SERVICE_WORKER} needs exactly one {BUILD_PLACEHOLDER} placeholder")
    build = {
        "id": build_id(site),
        "files": offline_files(site),
        "pyodideUrl": pyodide_url((site / "main.js").read_text(encoding="utf-8")),
        "pyodideFiles": list(PYODIDE_FILES),
    }
    worker.write_text(source.replace(BUILD_PLACEHOLDER, json.dumps(build)), encoding="utf-8")
    return str(build["id"])


def main() -> None:
    shutil.rmtree(SITE, ignore_errors=True)
    shutil.copytree(WEB, SITE)
    with tempfile.TemporaryDirectory() as tmp:
        wheel = build_wheel(Path(tmp))
        # A content hash in the path makes browsers fetch the new wheel after every change,
        # while the file name stays a valid wheel name for Pyodide.
        digest = hashlib.sha256(wheel.read_bytes()).hexdigest()[:12]
        target = SITE / "wheels" / digest / wheel.name
        target.parent.mkdir(parents=True)
        shutil.copy2(wheel, target)
    manifest = {"wheel": target.relative_to(SITE).as_posix()}
    (SITE / "wheel.json").write_text(json.dumps(manifest), encoding="utf-8")
    (SITE / ".nojekyll").touch()  # GitHub Pages: serve files as-is
    build = stamp_service_worker(SITE)
    print(f"Built {SITE} with {manifest['wheel']} (offline build {build})")


if __name__ == "__main__":
    main()
