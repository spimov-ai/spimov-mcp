#!/usr/bin/env python3
"""Build & publish the `spimov-mcp` PyPI package.

Bumps the version (in pyproject.toml + __init__.py, kept in lock-step),
rebuilds the wheel/sdist, and uploads to PyPI with twine.

Usage:
    # Auto bump the patch version (0.1.0 -> 0.1.1), build, upload:
    python services/mcp/build_and_publish.py

    # Bump minor / major instead:
    python services/mcp/build_and_publish.py --part minor   # 0.1.0 -> 0.2.0
    python services/mcp/build_and_publish.py --part major   # 0.1.0 -> 1.0.0

    # Set an exact version:
    python services/mcp/build_and_publish.py --version 0.3.0

    # Build only, don't upload (inspect dist/ first):
    python services/mcp/build_and_publish.py --no-upload

    # Bump the version files only (no build/upload):
    python services/mcp/build_and_publish.py --no-build

Required for upload (any one):
    TWINE_USERNAME=__token__ TWINE_PASSWORD=pypi-...   (env), or
    ~/.pypirc with a [pypi] token.

Run from the repo root with the project venv active (build + twine live there).
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

MCP_DIR = Path(__file__).resolve().parent
PYPROJECT = MCP_DIR / "pyproject.toml"
INIT_PY = MCP_DIR / "src" / "spimov_mcp" / "__init__.py"
DIST = MCP_DIR / "dist"

VERSION_RE = re.compile(r'(?m)^(version\s*=\s*")(\d+)\.(\d+)\.(\d+)(")')
INIT_RE = re.compile(r'(?m)^(__version__\s*=\s*")(\d+)\.(\d+)\.(\d+)(")')


def log(msg: str, level: str = "info") -> None:
    prefix = {"info": "==>", "warn": "!!!", "ok": "[OK]", "step": "###"}[level]
    print(f"{prefix} {msg}", flush=True)


def run(cmd: list[str], *, cwd: Path | None = None) -> None:
    log(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def require_binaries(*names: str) -> None:
    missing = [n for n in names if not shutil.which(n)]
    if missing:
        log(f"missing on PATH: {', '.join(missing)} — activate the project venv", "warn")
        sys.exit(2)


def current_version() -> tuple[int, int, int]:
    m = VERSION_RE.search(PYPROJECT.read_text())
    if not m:
        log(f"could not find version in {PYPROJECT}", "warn")
        sys.exit(3)
    return int(m.group(2)), int(m.group(3)), int(m.group(4))


def bump(ver: tuple[int, int, int], part: str) -> tuple[int, int, int]:
    major, minor, patch = ver
    if part == "major":
        return major + 1, 0, 0
    if part == "minor":
        return major, minor + 1, 0
    return major, minor, patch + 1


def write_version(new: str) -> None:
    # Keep pyproject.toml and __init__.py in lock-step so PyPI metadata and the
    # importable __version__ never drift.
    pp = PYPROJECT.read_text()
    pp2 = VERSION_RE.sub(rf'\g<1>{new}\g<5>', pp, count=1)
    PYPROJECT.write_text(pp2)

    init = INIT_PY.read_text()
    init2 = INIT_RE.sub(rf'\g<1>{new}\g<5>', init, count=1)
    INIT_PY.write_text(init2)
    log(f"version set to {new} (pyproject.toml + __init__.py)", "ok")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--version", default=None, help="exact version, e.g. 0.3.0")
    parser.add_argument("--part", choices=["major", "minor", "patch"], default="patch",
                        help="which part to bump when --version is not given (default: patch)")
    parser.add_argument("--no-build", action="store_true", help="only bump version files")
    parser.add_argument("--no-upload", action="store_true", help="build but don't upload to PyPI")
    args = parser.parse_args()

    log("=== spimov-mcp build & publish ===", "step")

    if args.version:
        if not re.fullmatch(r"\d+\.\d+\.\d+", args.version):
            log("--version must be X.Y.Z", "warn")
            return 2
        new = args.version
    else:
        new = ".".join(map(str, bump(current_version(), args.part)))

    cur = ".".join(map(str, current_version()))
    log(f"version: {cur} -> {new}", "step")
    write_version(new)

    if args.no_build:
        log("--no-build: stopping after version bump", "ok")
        return 0

    require_binaries("python", "python3")

    log("cleaning dist/", "step")
    if DIST.exists():
        shutil.rmtree(DIST)

    log("building wheel + sdist", "step")
    run([sys.executable, "-m", "build"], cwd=MCP_DIR)

    artifacts = sorted(p.name for p in DIST.glob("*"))
    log(f"built: {', '.join(artifacts)}", "ok")

    if args.no_upload:
        log("--no-upload: skipping PyPI upload (inspect dist/ then run twine yourself)", "ok")
        return 0

    log("uploading to PyPI", "step")
    # Pass explicit paths — subprocess has no shell to expand a "*" glob.
    run([sys.executable, "-m", "twine", "upload", *[str(p) for p in DIST.glob("*")]], cwd=MCP_DIR)
    log(f"published spimov-mcp {new} to PyPI", "ok")
    log("bump done — commit the version change when you're happy.", "ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
