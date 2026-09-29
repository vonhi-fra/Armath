"""Assemble the static site in ``site/``: the files from ``web/`` plus a freshly built wheel.

Usage: ``uv run python scripts/build_site.py``, then serve ``site/`` with any static server.
"""

import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
SITE = ROOT / "site"


def build_wheel(out_dir: Path) -> Path:
    subprocess.run(["uv", "build", "--wheel", "--out-dir", str(out_dir)], cwd=ROOT, check=True)
    (wheel,) = out_dir.glob("armath-*.whl")
    return wheel


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
    print(f"Built {SITE} with {manifest['wheel']}")


if __name__ == "__main__":
    main()
