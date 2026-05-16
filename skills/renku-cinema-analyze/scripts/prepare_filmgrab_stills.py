#!/usr/bin/env python3
"""Extract FilmGrab stills and download analysis-sized copies."""

from __future__ import annotations

import argparse
import dataclasses
import html.parser
import json
import mimetypes
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path


IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
USER_AGENT = "Mozilla/5.0 (compatible; FilmGrabVisualLanguage/1.0)"
IGNORED_EMPTY_DIR_FILES = {".DS_Store", "Thumbs.db"}
DEFAULT_ANALYSIS_MAX_EDGE = 1280


@dataclasses.dataclass(frozen=True)
class ImageVariant:
    url: str
    width: int | None = None


class FilmGrabImageParser(html.parser.HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self.candidates: list[ImageVariant] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {k.lower(): v for k, v in attrs if v}
        for key in ("data-orig-file", "data-large-file", "data-full-url", "data-src", "src", "href"):
            if key in attrs_dict:
                self._add(attrs_dict[key])
        for key in ("srcset", "data-srcset"):
            if key in attrs_dict:
                self._add_srcset(attrs_dict[key])

    def _add_srcset(self, value: str) -> None:
        for part in value.split(","):
            bits = part.strip().split()
            if not bits:
                continue
            url = bits[0]
            width = None
            if len(bits) > 1 and bits[1].endswith("w"):
                try:
                    width = int(bits[1][:-1])
                except ValueError:
                    width = None
            self._add(url, width)

    def _add(self, value: str, width: int | None = None) -> None:
        url = urllib.parse.urljoin(self.base_url, value)
        if is_image_url(url):
            self.candidates.append(ImageVariant(url, width or infer_width_from_url(url)))


def is_image_url(url: str) -> bool:
    path = urllib.parse.urlparse(url).path.lower()
    return path.endswith(IMAGE_EXTENSIONS)


def encode_url_for_request(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    path = urllib.parse.quote(urllib.parse.unquote(parsed.path), safe="/%")
    query = urllib.parse.quote(urllib.parse.unquote(parsed.query), safe="=&?/:+,%")
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, path, query, parsed.fragment))


def canonical_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def full_size_url(url: str) -> str:
    parsed = urllib.parse.urlparse(canonical_url(url))
    path = parsed.path
    if "/wp-content/uploads/" in path:
        path = path.replace("/photo-gallery/thumb/", "/photo-gallery/")
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))


def infer_width_from_url(url: str) -> int | None:
    match = re.search(r"-(\d{2,5})x\d{2,5}(?=\.(?:jpe?g|png|webp)$)", urllib.parse.urlparse(url).path, re.I)
    return int(match.group(1)) if match else None


def still_group_key(url: str) -> str:
    parsed = urllib.parse.urlparse(full_size_url(url))
    path = re.sub(r"-\d{2,5}x\d{2,5}(?=\.(?:jpe?g|png|webp)$)", "", parsed.path, flags=re.I)
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))


def request_url(url: str) -> bytes:
    req = urllib.request.Request(encode_url_for_request(url), headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read()


def is_filmgrab_still_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    if "film-grab.com" not in parsed.netloc.lower():
        return False
    path = parsed.path.lower()
    return "/wp-content/uploads/photo-gallery/" in path


def extract_image_variants(page_url: str) -> list[ImageVariant]:
    html = request_url(page_url).decode("utf-8", errors="replace")
    parser = FilmGrabImageParser(page_url)
    parser.feed(html)

    for match in re.findall(r"https?://[^'\"\\s<>]+?\\.(?:jpe?g|png|webp)(?:\\?[^'\"\\s<>]*)?", html, re.I):
        parser._add(match)

    seen: set[str] = set()
    variants: list[ImageVariant] = []
    for candidate in parser.candidates:
        clean = canonical_url(candidate.url)
        if not is_filmgrab_still_url(clean):
            continue
        if clean not in seen:
            seen.add(clean)
            variants.append(ImageVariant(clean, candidate.width or infer_width_from_url(clean)))
    return variants


def choose_full_variant(variants: list[ImageVariant]) -> ImageVariant:
    originals = [
        ImageVariant(full_size_url(variant.url), variant.width)
        for variant in variants
        if infer_width_from_url(variant.url) is None
    ]
    if originals:
        return originals[-1]
    largest = max(variants, key=lambda variant: variant.width or 0)
    return ImageVariant(full_size_url(largest.url), largest.width)


def choose_analysis_variant(variants: list[ImageVariant], max_edge: int) -> ImageVariant:
    sized = [variant for variant in variants if variant.width]
    if not sized:
        thumbnails = [
            variant
            for variant in variants
            if "/wp-content/uploads/photo-gallery/thumb/" in urllib.parse.urlparse(variant.url).path.lower()
        ]
        if thumbnails:
            return thumbnails[-1]
        return choose_full_variant(variants)
    within_limit = [variant for variant in sized if variant.width and variant.width <= max_edge]
    if within_limit:
        return max(within_limit, key=lambda variant: variant.width or 0)
    return min(sized, key=lambda variant: variant.width or 0)


def extract_image_sets(page_url: str, analysis_max_edge: int) -> list[dict]:
    groups: dict[str, list[ImageVariant]] = {}
    for variant in extract_image_variants(page_url):
        groups.setdefault(still_group_key(variant.url), []).append(variant)

    image_sets = []
    for variants in groups.values():
        full = choose_full_variant(variants)
        analysis = choose_analysis_variant(variants, analysis_max_edge)
        image_sets.append(
            {
                "full_url": full.url,
                "analysis_url": analysis.url,
                "analysis_width": analysis.width,
                "variant_count": len(variants),
            }
        )
    return image_sets


def sample_evenly(items: list, max_items: int) -> list:
    if len(items) <= max_items:
        return items
    if max_items <= 1:
        return items[:max_items]
    selected = []
    last_index = len(items) - 1
    for i in range(max_items):
        index = round(i * last_index / (max_items - 1))
        selected.append(items[index])
    return selected


def extension_for(url: str, data: bytes) -> str:
    ext = Path(urllib.parse.urlparse(url).path).suffix.lower()
    if ext in IMAGE_EXTENSIONS:
        return ".jpg" if ext == ".jpeg" else ext
    guessed = mimetypes.guess_extension(mimetypes.guess_type(url)[0] or "")
    return guessed or ".jpg"


def infer_title(page_url: str) -> str:
    slug = urllib.parse.urlparse(page_url).path.strip("/").split("/")[-1]
    return slug.replace("-", " ").title() if slug else "Untitled Film"


def infer_slug(page_url: str) -> str:
    slug = urllib.parse.urlparse(page_url).path.strip("/").split("/")[-1]
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", slug).strip("-").lower()
    return slug or "untitled-film"


def is_effectively_empty_dir(path: Path) -> bool:
    if not path.is_dir():
        return False
    return not any(
        child.is_file() and child.name not in IGNORED_EMPTY_DIR_FILES
        for child in path.rglob("*")
    )


def default_output_dir(page_url: str) -> Path:
    base = Path.cwd() / infer_slug(page_url)
    if not base.exists() or is_effectively_empty_dir(base):
        return base
    for index in range(2, 1000):
        candidate = Path.cwd() / f"{base.name}-{index}"
        if not candidate.exists() or is_effectively_empty_dir(candidate):
            return candidate
    raise RuntimeError(f"Could not find an available output folder for {base.name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="FilmGrab movie page URL")
    parser.add_argument(
        "--output",
        help="Output directory. Defaults to ./<movie-slug>, with a numeric suffix if needed.",
    )
    parser.add_argument("--max-images", type=int, default=30, help="Maximum stills to keep")
    parser.add_argument(
        "--max-edge",
        type=int,
        default=DEFAULT_ANALYSIS_MAX_EDGE,
        help="Preferred longest edge for FilmGrab analysis copies",
    )
    args = parser.parse_args()

    if "film-grab.com" not in urllib.parse.urlparse(args.url).netloc.lower():
        print("Expected a film-grab.com URL.", file=sys.stderr)
        return 2

    image_sets = sample_evenly(extract_image_sets(args.url, args.max_edge), args.max_images)
    if not image_sets:
        print("No FilmGrab still URLs found.", file=sys.stderr)
        return 1

    out_dir = Path(args.output) if args.output else default_output_dir(args.url)
    analysis_dir = out_dir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    stills = []
    for index, image_set in enumerate(image_sets, start=1):
        still_id = f"still-{index:03d}"
        full_url = image_set["full_url"]
        analysis_url = image_set["analysis_url"]
        if analysis_url == full_url:
            print(f"Skipping {full_url}: no smaller FilmGrab analysis variant found.", file=sys.stderr)
            continue
        analysis_data = request_url(analysis_url)
        analysis_ext = extension_for(analysis_url, analysis_data)
        analysis_path = analysis_dir / f"{still_id}{analysis_ext}"
        analysis_path.write_bytes(analysis_data)

        record = {
            "id": still_id,
            "fullUrl": full_url,
            "analysisUrl": analysis_url,
            "analysisPath": os.path.relpath(analysis_path, out_dir),
            "analysisBytes": len(analysis_data),
            "analysisWidthGuess": image_set["analysis_width"],
            "filmGrabVariantCount": image_set["variant_count"],
        }
        stills.append(record)
        print(f"{still_id}: {analysis_url}")

    if not stills:
        print("No smaller FilmGrab analysis variants found.", file=sys.stderr)
        return 1

    manifest = {
        "filmGrabUrl": args.url,
        "titleGuess": infer_title(args.url),
        "maxImages": args.max_images,
        "analysisMaxEdge": args.max_edge,
        "analysisSource": "filmgrab-small-variants-only",
        "count": len(stills),
        "stills": stills,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Output folder: {out_dir}")
    print(f"Wrote {out_dir / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
