---
name: film-grab-visual-language
description: Analyze a film-grab.com movie page into a cinematographer-focused visual language study. Use when a user gives a FilmGrab film URL and wants still extraction, capped full-size and smaller analysis image downloads, structured JSON analysis, or a browser-ready HTML/JavaScript report about a film's color, grading, composition, lighting, texture, and visual principles.
---

# FilmGrab Visual Language

In commands below, `<skill>` is the absolute path to this skill's folder.

## Workflow

Use this skill to turn one FilmGrab movie URL into a reusable visual-language report for cinematographers.

1. Prepare stills:

```bash
python3 <skill>/scripts/prepare_filmgrab_stills.py "<film-grab-url>" --max-images 30
```

This creates one movie-specific folder in the current working directory, then extracts direct still URLs, downloads full-size images, downloads smaller FilmGrab-provided `srcset` variants for analysis, and writes `manifest.json`.

Use the printed output folder as `<work-dir>` for every later step. Keep all files for this movie inside that one folder:

```text
<work-dir>/
  manifest.json
  analysis.json
  full/
  analysis/
  report/
```

Only pass `--output "<work-dir>"` when the user explicitly wants a custom folder name.

2. Analyze only the smaller copies in `<work-dir>/analysis/`, not the full-size downloads. Use up to 30 stills. Study the stills as a system, not as isolated pretty frames.

3. Write `analysis.json` matching the schema below. For every claim that cites images, choose stills that visibly demonstrate that exact point. Never use a random still just to fill a slot.

4. Validate the JSON against the manifest:

```bash
python3 <skill>/scripts/validate_analysis_json.py "<work-dir>/analysis.json" --manifest "<work-dir>/manifest.json"
```

5. Render the report:

```bash
python3 <skill>/scripts/render_report.py "<work-dir>/analysis.json"
```

Preview reports through the shared FilmGrab preview server on the well-known local port `8765`. Start it once:

```bash
<skill>/bin/preview-server
```

Then open the report by passing the analysis folder in the URL:

```text
http://127.0.0.1:8765/?dir=<absolute-work-dir>
```

For example:

```text
http://127.0.0.1:8765/?dir=/Users/example/project/filmgrab-movie-title
```

The renderer prints the exact preview URL after rendering.

The shared preview also exposes a movie picker for sibling analysis folders. Any folder in the same parent directory that contains an `analysis.json` file appears in the modal opened from the top-bar grid icon.

Shut the shared preview server down when it is no longer needed:

```bash
<skill>/bin/stop-preview-server
```

6. Sanity-check the rendered report. Confirm that the page loads the film title, expected sections, stills, and no obvious loading error. If browser access to localhost is blocked, use `curl "http://127.0.0.1:8765/analysis.json?dir=<absolute-work-dir>"` to confirm the preview server is serving the rendered JSON, then report the browser limitation clearly.

## Common Hiccups

- The still extractor can occasionally capture non-film page assets such as site icons, logos, ads, or tiny thumbnails. Exclude those from `sourceStills`, hero stills, observations, and all cited examples. Keep them in `manifest.json` if the script produced them, but do not analyze them as film frames.
- If the manifest mixes `thumb/` URLs and full gallery URLs, still cite only URLs that appear in the manifest. Do not manually "upgrade" a thumbnail URL unless the manifest contains the upgraded URL.
- Network downloads may require approval in sandboxed environments. If fetching FilmGrab fails with DNS, host resolution, or connection errors, retry the same prepare command with the needed network permission instead of changing the workflow. The prepare script should not create the default output folder until after FilmGrab image URLs have been fetched successfully; if an older failed run left an empty default folder behind, the script should reuse it rather than creating a `-2` suffix.
- Use the shared preview server on `127.0.0.1:8765`; do not create a new per-report static server on a random port. Pass the analysis folder through the `dir` query parameter instead.
- If the preview server is already running, reuse it. If it needs to be stopped, run `<skill>/bin/stop-preview-server`.
- Browser preview is useful but not the source of truth. Validation against `manifest.json` and successful rendering of `report/index.html` plus `report/analysis.json` are required even if browser preview fails.

## Analysis Rules

- Write for working cinematographers: concrete, visual, and useful. Prefer phrases that describe repeatable choices a DP could test.
- Create one self-contained folder per movie in the current working directory. Do not scatter images, manifests, JSON, or rendered HTML across separate project locations.
- Ground every section in the actual FilmGrab stills. If an observation says "low frontal fill isolates faces," its cited stills must show that lighting behavior.
- Use the smaller analysis images for AI vision. Use the full URLs in JSON fields so users can inspect the source stills.
- Cap the study at about 30 stills. If the page has more, sample across the whole film rather than taking only the opening run.
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

- `scripts/prepare_filmgrab_stills.py`: extract still URLs, download full images plus smaller FilmGrab `srcset` analysis copies, and write a manifest.
- `scripts/validate_analysis_json.py`: validate schema basics and verify cited still URLs come from the manifest.
- `scripts/render_report.py`: create a report folder from the stable viewer template and `analysis.json`.
- `scripts/preview_report_server.py`: serve the reusable viewer on `127.0.0.1:8765`, load any report with `?dir=<work-dir>`, and stop the server with `--stop`.
- `bin/preview-server` and `bin/stop-preview-server`: friendly wrappers for starting and stopping the shared preview server.
- `assets/viewer.html`: reusable browser renderer. It reads `analysis.json`; do not generate new HTML for every movie.
