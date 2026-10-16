#!/usr/bin/env python3
"""Run the JavaScript presentation builder with the managed Artifact Tool runtime."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--finalize", action="store_true")
    args = parser.parse_args()

    workspace = Path(__file__).resolve().parents[2]
    build_dir = workspace / ".build" / "phase3-presentation"
    build_dir.mkdir(parents=True, exist_ok=True)

    runtime = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies"
    node = runtime / "node/bin/node"
    modules = runtime / "node/node_modules"
    copied_builder = build_dir / "build_presentation.mjs"
    shutil.copy2(Path(__file__).with_suffix(".mjs"), copied_builder)

    module_link = build_dir / "node_modules"
    if module_link.is_symlink() and module_link.resolve() != modules.resolve():
        module_link.unlink()
    if not module_link.exists():
        module_link.symlink_to(modules, target_is_directory=True)

    command = [str(node), str(copied_builder), "--workspace", str(workspace)]
    if args.finalize:
        command.append("--finalize")
    environment = os.environ.copy()
    environment["RUNTIME_NODE_MODULES"] = str(modules)
    environment["CODEX_PRIMARY_RUNTIME_NODE_MODULES"] = str(modules)
    return subprocess.run(command, cwd=workspace, env=environment, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
