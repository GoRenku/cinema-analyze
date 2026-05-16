#!/usr/bin/env python3
"""Create a browser report folder from analysis.json and the stable viewer template."""

from __future__ import annotations

import argparse
import json
import shutil
import urllib.parse
from pathlib import Path


PREVIEW_PORT = 8765


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("analysis_json")
    parser.add_argument("--output", help="Report output directory. Defaults to <analysis-json-folder>/report")
    args = parser.parse_args()

    skill_dir = Path(__file__).resolve().parents[1]
    viewer = skill_dir / "assets" / "viewer.html"
    analysis_path = Path(args.analysis_json)
    output = Path(args.output) if args.output else analysis_path.parent / "report"
    output.mkdir(parents=True, exist_ok=True)
    server_script = skill_dir / "bin" / "server"

    data = json.loads(analysis_path.read_text(encoding="utf-8"))
    (output / "analysis.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    shutil.copyfile(viewer, output / "index.html")

    print(f"Wrote {output / 'index.html'}")
    print(f"Wrote {output / 'analysis.json'}")
    print("Stable preview server:")
    print(f"  {server_script} start")
    print("Preview URL:")
    print(f"  http://127.0.0.1:{PREVIEW_PORT}/?dir={urllib.parse.quote(str(analysis_path.parent.resolve()))}")
    print("Shutdown:")
    print(f"  {server_script} stop")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
