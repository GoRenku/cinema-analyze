---
name: renku-cinema-analyze
description: Analyze a film-grab.com movie page into a cinematographer-focused visual language study. Use when a user gives a FilmGrab film URL and wants still extraction, capped small analysis image downloads, structured JSON analysis, or a browser-ready HTML/JavaScript report about a film's color, grading, composition, lighting, texture, and visual principles.
---

# Renku Cinema Analyze

In commands below, `<skill>` is the absolute path to this skill's folder.

## Workflow

Use this skill to turn one FilmGrab movie URL into a reusable visual-language report for cinematographers.

1. Prepare stills:

```bash
python3 <skill>/scripts/prepare_filmgrab_stills.py "<film-grab-url>" --max-images 30
```

This creates one movie-specific folder in the current working directory, then extracts direct still URLs, downloads only smaller FilmGrab-provided `srcset` variants for analysis, and writes `manifest.json`. The manifest keeps full-size FilmGrab URLs as metadata for citation, but the script must not download full-size images.

Use the printed output folder as `<work-dir>` for every later step. Keep all files for this movie inside that one folder:

```text
<work-dir>/
  manifest.json
  analysis.json
  analysis/
  report/
```

Only pass `--output "<work-dir>"` when the user explicitly wants a custom folder name.

2. Analyze only the smaller copies in `<work-dir>/analysis/`. Analyze every still downloaded into the analysis folder; do not stop after reviewing only a few representative images. Study the complete downloaded set as a system, not as isolated pretty frames.

3. Write a thorough `analysis.json` matching the schema below. Cover the film's visual language in depth across color, grading, composition, lighting, texture, visual lineage, and practical cinematography principles. For every claim that cites images, choose stills that visibly demonstrate that exact point. Never use a random still just to fill a slot.

4. Validate the JSON against the manifest:

```bash
python3 <skill>/scripts/validate_analysis_json.py "<work-dir>/analysis.json" --manifest "<work-dir>/manifest.json"
```

5. Render the report:

```bash
python3 <skill>/scripts/render_report.py "<work-dir>/analysis.json"
```

Preview reports through the shared Renku Cinema Analyze preview server on the well-known local port `8765`. Start it once:

```bash
<skill>/bin/server start --base-dir <analysis-base-folder>
```

Always use the bundled server lifecycle scripts for preview server management: `<skill>/bin/server start`, `<skill>/bin/server status`, `<skill>/bin/server restart`, and `<skill>/bin/server stop` when shutdown is explicitly requested. The compatibility wrappers `<skill>/bin/preview-server` and `<skill>/bin/stop-preview-server` are also allowed. Do not manually run `scripts/preview_report_server.py`, `python -m http.server`, `nohup`, or a custom ad hoc server for normal report preview operations.

Then open the report by passing the analysis folder in the URL:

```text
http://127.0.0.1:8765/?dir=<absolute-work-dir>
```

Opening the server home page shows the movie picker directly when the server was started with a base analysis folder:

```text
http://127.0.0.1:8765/
```

For example:

```text
http://127.0.0.1:8765/?dir=/Users/example/project/movie-title
```

The renderer prints the exact preview URL after rendering. Keep that preview URL and include it in the successful completion response so the user can open the report directly.

The shared preview also exposes a movie picker. On the server home page it lists analysis folders under the explicit server base folder. From a selected report, it lists sibling folders in the same parent directory. Any folder with an `analysis.json` file appears in the modal opened from the top-bar grid icon.

Do not stop the shared preview server at the end of a successful run. Leave it running so the user can view the report after completion. Only stop the server when the user explicitly asks you to stop it, or when you must restart it to clear a stale or unhealthy port state.

6. Sanity-check the rendered report. Confirm that the page loads the film title, expected sections, stills, and no obvious loading error. If browser access to localhost is blocked, use `curl "http://127.0.0.1:8765/analysis.json?dir=<absolute-work-dir>"` to confirm the preview server is serving the rendered JSON, then report the browser limitation clearly. In the final response, include the exact preview URL, the `analysis.json` path, and a brief note that the preview server was left running.

## Common Hiccups

- The still extractor should only keep FilmGrab `/photo-gallery/` movie stills. If non-film page assets such as site icons, logos, ads, or tiny thumbnails appear, fix the extractor rather than analyzing them.
- `fullUrl` values and all cited FilmGrab still URLs must point to the full-size image, never the `/photo-gallery/thumb/` URL. The prepare script canonicalizes thumbnail URLs by removing `/thumb/`; if any thumb URL remains in `analysis.json`, fix it before validation.
- Network downloads may require approval in sandboxed environments. If fetching FilmGrab fails with DNS, host resolution, or connection errors, retry the same prepare command with the needed network permission instead of changing the workflow. The prepare script should not create the default output folder until after FilmGrab image URLs have been fetched successfully; if an older failed run left an empty default folder behind, the script should reuse it rather than creating a `-2` suffix.
- Use the shared preview server on `127.0.0.1:8765`; do not create a new per-report static server on a random port. Pass the analysis folder through the `dir` query parameter instead. Manage this server only through the bundled `bin/server` script or its compatibility wrappers.
- If the preview server is already running, reuse it. Use `<skill>/bin/server status` to check it, `<skill>/bin/server start --base-dir <analysis-base-folder>` to start it, and `<skill>/bin/server restart --base-dir <analysis-base-folder>` if the port state looks stale. Do not run `<skill>/bin/server stop` after a successful report unless the user explicitly asks for shutdown.
- Browser preview is useful but not the source of truth. Validation against `manifest.json` and successful rendering of `report/index.html` plus `report/analysis.json` are required even if browser preview fails.

## Analysis Rules

- Write for working cinematographers: concrete, visual, and useful. Prefer phrases that describe repeatable choices a DP could test.
- Create one self-contained folder per movie in the current working directory. Do not scatter images, manifests, JSON, or rendered HTML across separate project locations.
- Ground every section in the actual FilmGrab stills. Inspect every downloaded analysis image before writing `analysis.json`. If an observation says "low frontal fill isolates faces," its cited stills must show that lighting behavior.
- Use the smaller analysis images for AI vision. Use the full URLs in JSON fields so users can inspect the source stills.
- The downloader may cap the working set, usually around 30 stills. Once the stills are downloaded, analyze all of them. If the FilmGrab page has more stills than the cap, sample across the whole film during download rather than taking only the opening run.
- Do not invent credits. If the FilmGrab page or obvious surrounding text does not provide director/cinematographer/year, set the field to `null`.
- Avoid generic film-school labels unless you explain what they do in this specific movie.
- Treat "Inspired By" as visual lineage, not verified production history. Unless a source explicitly confirms influence, use cautious language such as "potentially echoes," "shares a strategy with," or "sits near." Never state that a filmmaker was inspired by another film, director, or cinematographer as fact without a source.

## JSON Schema

Create this shape exactly enough for the viewer to render. Optional unknown fields are allowed, but these fields are expected:

```json
{
  "film": {
    "title": "Movie title",
    "year": 0000,
    "director": "Director name or null",
    "cinematographer": "Cinematographer name or null",
    "filmGrabUrl": "https://film-grab.com/..."
  },
  "sourceStills": [
    {
      "id": "still-001",
      "fullUrl": "https://film-grab.com/wp-content/uploads/...",
      "analysisPath": "analysis/still-001.jpg"
    }
  ],
  "coreVisualLanguage": {
    "idea": "3-5 sentence thesis of the movie's visual language.",
    "exampleStills": ["https://film-grab.com/wp-content/uploads/..."]
  },
  "color": {
    "description": "How color operates as a strategy.",
    "palette": [
      { "hex": "#RRGGBB", "name": "evocative name", "meaning": "what this color does visually or narratively" }
    ],
    "observations": [
      { "text": "Specific color observation.", "stills": ["https://film-grab.com/wp-content/uploads/..."] }
    ]
  },
  "grading": {
    "tone": "short tonal phrase",
    "mood": "mood words separated by commas or middle dots",
    "description": "How shadows, midtones, highlights, contrast, saturation, and day/night behavior work.",
    "exampleStills": ["https://film-grab.com/wp-content/uploads/..."]
  },
  "composition": {
    "description": "Overall compositional strategy.",
    "patterns": [
      { "name": "Memorable pattern name", "description": "How it works.", "stills": ["https://film-grab.com/wp-content/uploads/..."] }
    ]
  },
  "lighting": {
    "description": "Overall lighting approach.",
    "techniques": [
      { "name": "Memorable technique name", "description": "How it is used.", "stills": ["https://film-grab.com/wp-content/uploads/..."] }
    ]
  },
  "texture": {
    "description": "Surface, grain, tactility, lens/filter feel, production texture.",
    "observations": [
      { "text": "Specific texture observation.", "stills": ["https://film-grab.com/wp-content/uploads/..."] }
    ]
  },
  "inspiredBy": {
    "description": "Visual-lineage note. Explain that these are potential affinities, not confirmed influences unless sourced.",
    "items": [
      {
        "category": "movie | director | cinematographer",
        "name": "Reference name",
        "confidence": "low | medium | high",
        "why": "What specific visual strategy this film shares with the reference.",
        "stills": ["https://film-grab.com/wp-content/uploads/..."]
      }
    ]
  },
  "visualConstitution": {
    "summary": "2-4 sentence synthesis of the film's visual argument.",
    "principles": [
      "Imperative principle another cinematographer could use."
    ]
  }
}
```

## Image Selection

When selecting stills for the report:

- Use `manifest.json` to map smaller analysis files back to full URLs.
- Prefer 2-4 stills per observation. One strong still is better than four weak ones.
- Reuse stills only when they genuinely support multiple ideas.
- Spread examples across the film if the page provides enough variety.
- Check that hero stills together summarize the film's look: one dominant composition, one color/lighting signature, and one texture or tonal signature.

## Inspired By Selection

When filling `inspiredBy`:

- Include a balanced mix of movies, directors, and cinematographers when the film supports it visually. Three to six entries is usually enough.
- Ground each entry in a visible strategy from the stills: color design, framing, lighting, production texture, lens behavior, blocking, genre grammar, or tonal contrast.
- Use `confidence` to separate strong visual resemblance from looser lineage. "High" should be reserved for references with very specific, repeated visual overlap or confirmed sourcing.
- Avoid vague entries such as "Hitchcock" or "De Palma" unless you name the precise shared behavior: voyeuristic framing, split diopter staging, theatrical color, subjective camera, and so on.
- Do not imply intent. Write "The film potentially echoes..." rather than "The film borrows from..." unless you have a source.
- Cite stills that show the resemblance. If a comparison cannot be tied to the FilmGrab stills, leave it out.

## Bundled Resources

- `scripts/prepare_filmgrab_stills.py`: extract still URLs, download only smaller FilmGrab analysis copies, and write a manifest with full-size source URLs as metadata.
- `scripts/validate_analysis_json.py`: validate schema basics and verify cited still URLs come from the manifest.
- `scripts/render_report.py`: create a report folder from the stable viewer template and `analysis.json`.
- `scripts/preview_report_server.py`: serve the reusable viewer on `127.0.0.1:8765`, load any report with `?dir=<work-dir>`, and stop the server with `--stop`.
- `bin/server`: smart lifecycle wrapper for the shared preview server. It supports `start`, `stop`, `restart`, and `status`.
- `bin/preview-server` and `bin/stop-preview-server`: compatibility wrappers around `bin/server`.
- `assets/viewer.html`: reusable browser renderer. It reads `analysis.json`; do not generate new HTML for every movie.
