"""Serve ``site/`` locally with correct MIME types.

``python -m http.server`` takes types from the Windows registry, which often maps ``.js`` to
``text/plain``; browsers then refuse to run module scripts. Usage:
``uv run python scripts/serve.py [port]``.
"""

import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"


class SiteHandler(SimpleHTTPRequestHandler):
    extensions_map = {  # noqa: RUF012 - overrides the base class attribute of the same shape
        **SimpleHTTPRequestHandler.extensions_map,
        ".js": "text/javascript",
        ".mjs": "text/javascript",
        ".json": "application/json",
        ".svg": "image/svg+xml",
        ".wasm": "application/wasm",
        ".whl": "application/zip",
        ".woff2": "font/woff2",
    }

    def end_headers(self) -> None:
        # Always revalidate, so a rebuilt site is picked up on reload.
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    if not SITE.is_dir():
        sys.exit("site/ not found; run scripts/build_site.py first")
    handler = partial(SiteHandler, directory=str(SITE))
    with ThreadingHTTPServer(("127.0.0.1", port), handler) as server:
        print(f"Serving {SITE} at http://localhost:{port}")
        server.serve_forever()


if __name__ == "__main__":
    main()
