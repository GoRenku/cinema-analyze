#!/usr/bin/env python3
"""Validate a FilmGrab visual-language analysis JSON file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REQUIRED_TOP_LEVEL = [
    "film",
    "coreVisualLanguage",
    "color",
    "grading",
    "composition",
    "lighting",
    "texture",
    "visualConstitution",
]


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"{path}: invalid JSON: {exc}") from exc


def collect_still_refs(value) -> list[str]:
    refs: list[str] = []
    if isinstance(value, dict):
        for key, inner in value.items():
            if key in {"stills", "exampleStills"} and isinstance(inner, list):
                refs.extend([item for item in inner if isinstance(item, str)])
            else:
                refs.extend(collect_still_refs(inner))
    elif isinstance(value, list):
        for item in value:
            refs.extend(collect_still_refs(item))
    return refs


def is_thumb_url(url: str) -> bool:
    return "/wp-content/uploads/photo-gallery/thumb/" in url


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("analysis_json")
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    errors: list[str] = []
    analysis = load_json(Path(args.analysis_json))
    manifest = load_json(Path(args.manifest))

    for key in REQUIRED_TOP_LEVEL:
        if key not in analysis:
            errors.append(f"Missing top-level key: {key}")

    film = analysis.get("film", {})
    if not isinstance(film, dict) or not film.get("title"):
        errors.append("film.title is required")
    if film.get("filmGrabUrl") != manifest.get("filmGrabUrl"):
        errors.append("film.filmGrabUrl should match manifest.filmGrabUrl")

    source_urls = {item.get("fullUrl") for item in manifest.get("stills", []) if isinstance(item, dict)}
    thumb_source_urls = sorted(url for url in source_urls if isinstance(url, str) and is_thumb_url(url))
    if thumb_source_urls:
        errors.append(
            "Manifest fullUrl values must use full-size FilmGrab URLs, not /thumb/ URLs: "
            + ", ".join(thumb_source_urls[:10])
        )
    cited = collect_still_refs(analysis)
    thumb_cited = sorted({url for url in cited if is_thumb_url(url)})
    if thumb_cited:
        errors.append(
            "Cited still URLs must use full-size FilmGrab URLs, not /thumb/ URLs: "
            + ", ".join(thumb_cited[:10])
        )
    missing = sorted({url for url in cited if url not in source_urls})
    if missing:
        errors.append("Cited still URLs not found in manifest: " + ", ".join(missing[:10]))

    if len(source_urls) > 30:
        errors.append("Manifest contains more than 30 stills; rerun prepare script with --max-images 30")

    palette = analysis.get("color", {}).get("palette", [])
    if not isinstance(palette, list) or not (4 <= len(palette) <= 8):
        errors.append("color.palette should usually contain 4-8 swatches")

    principles = analysis.get("visualConstitution", {}).get("principles", [])
    if not isinstance(principles, list) or not (4 <= len(principles) <= 8):
        errors.append("visualConstitution.principles should usually contain 4-8 items")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"OK: {args.analysis_json} cites {len(set(cited))} stills from the manifest.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
