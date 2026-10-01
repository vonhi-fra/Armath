import json
import re
import shutil
from pathlib import Path

import pytest
from build_site import (
    PYODIDE_FILES,
    WEB,
    build_id,
    offline_files,
    pyodide_url,
    stamp_service_worker,
)


@pytest.fixture
def site(tmp_path: Path) -> Path:
    """A copy of web/ with a fake wheel, as build_site.main() lays it out."""
    site = tmp_path / "site"
    shutil.copytree(WEB, site)
    wheel = site / "wheels" / "abc123" / "armath-0.1.0-py3-none-any.whl"
    wheel.parent.mkdir(parents=True)
    wheel.write_bytes(b"wheel")
    (site / "wheel.json").write_text('{"wheel": "wheels/abc123/armath-0.1.0-py3-none-any.whl"}')
    (site / ".nojekyll").touch()
    return site


def stamped_build(site: Path) -> dict[str, object]:
    stamp_service_worker(site)
    source = (site / "sw.js").read_text(encoding="utf-8")
    match = re.search(r"^const BUILD = (.+);$", source, re.MULTILINE)
    assert match is not None
    build: dict[str, object] = json.loads(match.group(1))
    return build


def test_pyodide_url_is_read_from_main_js() -> None:
    main_js = (WEB / "main.js").read_text(encoding="utf-8")

    assert re.fullmatch(r"https://cdn\.jsdelivr\.net/pyodide/v[\d.]+/full/", pyodide_url(main_js))


def test_pyodide_url_missing_is_an_error() -> None:
    with pytest.raises(ValueError, match="PYODIDE_URL"):
        pyodide_url("const somethingElse = 1;")


def test_offline_files_cover_what_the_app_loads(site: Path) -> None:
    files = offline_files(site)

    for path in (
        "./",
        "main.js",
        "styles.css",
        "manifest.webmanifest",
        "icons/icon-192.png",
        "fonts/inter-latin.woff2",
        "wheel.json",
        "wheels/abc123/armath-0.1.0-py3-none-any.whl",
    ):
        assert path in files
    assert "index.html" not in files  # cached as "./", the URL the app is opened at
    assert "sw.js" not in files
    assert ".nojekyll" not in files
    assert not [path for path in files if path.endswith(".txt")]  # font licences


def test_stamp_fills_in_the_build(site: Path) -> None:
    expected_id = build_id(site)

    build = stamped_build(site)

    assert build["id"] == expected_id
    assert build["files"] == offline_files(site)
    assert build["pyodideFiles"] == list(PYODIDE_FILES)
    assert str(build["pyodideUrl"]).startswith("https://cdn.jsdelivr.net/pyodide/")
    assert "__BUILD__" not in (site / "sw.js").read_text(encoding="utf-8")


@pytest.mark.parametrize("changed", ["styles.css", "sw.js"])
def test_build_id_changes_with_any_file(site: Path, changed: str) -> None:
    before = build_id(site)
    with (site / changed).open("a", encoding="utf-8") as file:
        file.write("/* changed */")

    assert build_id(site) != before


def test_stamping_twice_is_an_error(site: Path) -> None:
    stamp_service_worker(site)

    with pytest.raises(ValueError, match="placeholder"):
        stamp_service_worker(site)
