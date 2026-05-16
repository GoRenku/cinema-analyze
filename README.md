# Renku Cinema Analyze

Renku Cinema Analyze is an agent skill/plugin for turning a FilmGrab movie page into a cinematographer-focused visual-language study.

It downloads a capped set of FilmGrab stills, uses FilmGrab's own smaller image variants for vision analysis, guides the agent through a structured visual reading, validates cited stills against the downloaded manifest, and renders a browser report with switchable visual styles.

## Quick Start

There are two clear paths:

1. Install the plugin for the agent you use: Codex or Claude Code.
2. After it is installed, create a base analysis folder, invoke the skill with a FilmGrab URL, preview the report, and ask the agent to stop the preview server when you are done.

## Install

Choose one install path.

### If You Use Codex

This plugin is not listed in Codex's default curated Plugin Directory. OpenAI has not launched self-serve submission for public Codex Plugin Directory listings yet.

For now, add this GitHub repository as a Codex plugin marketplace:

```bash
codex plugin marketplace add GoRenku/cinema-analyze --ref main
```

Then install the plugin from that added marketplace:

1. Open Codex.
2. Open the plugin directory.
   - In the Codex CLI, type `/plugins`.
   - In the Codex app, open Plugins.
3. Choose the `Renku Cinema Analyze Plugins` marketplace. It appears only after you add the marketplace above.
4. Install `cinema-analyze`.
5. Start a new Codex thread.

In Codex, `cinema-analyze` is the plugin package. The callable skill is named `renku-cinema-analyze`, so you invoke it with:

```text
$renku-cinema-analyze
```

### If You Use Claude Code

Add this GitHub repository as a Claude Code plugin marketplace from inside Claude Code:

```text
/plugin marketplace add GoRenku/cinema-analyze
```

Then install the plugin from that marketplace:

```text
/plugin install cinema-analyze@cinema-analyze
```

Run `/reload-plugins` after installation, or restart Claude Code if Claude Code asks you to reload plugins.

Then ask Claude Code to use the Renku Cinema Analyze skill with a FilmGrab movie URL. Claude Code plugin usage is prompt-driven, so you can say:

```text
Use the Renku Cinema Analyze skill to analyze this FilmGrab movie page:
https://film-grab.com/2021/05/07/promising-young-woman/
```

## After Install

These steps are the same whether you installed the plugin in Codex or Claude Code.

### 1. Create A Base Analysis Folder

Create one folder where all generated movie studies will go:

```bash
mkdir -p ~/cinema-analyses
```

Open that folder as the workspace folder in Codex or Claude Code when you are creating analyses.

This matters because each movie gets its own generated folder inside the current workspace, for example:

```text
~/cinema-analyses/
  promising-young-woman/
  the-substance/
  in-the-mood-for-love/
```

Keeping all studies in one base folder makes the report viewer's movie picker useful: it lists sibling folders that contain `analysis.json`.

### 2. Analyze A FilmGrab Movie Page

Use a direct [FilmGrab](https://film-grab.com/) movie URL:

For Codex:

```text
$renku-cinema-analyze analyze this FilmGrab movie page:
https://film-grab.com/2021/05/07/promising-young-woman/
```

For Claude Code:

```text
Use the Renku Cinema Analyze skill to analyze this FilmGrab movie page:
https://film-grab.com/2021/05/07/promising-young-woman/
```

The skill intentionally uses a direct FilmGrab page link instead of automatically searching the web. That keeps the user in control of the source page and helps FilmGrab continue to receive the visit, ad impression, and link credit for the still images they provide.

### 3. Preview The Report

The skill renders a static report into each movie folder. Ask the agent to open or preview the generated report, and it will use the shared local preview server on one stable port: `127.0.0.1:8765`.

For manual control, the deterministic server script is:

```bash
skills/renku-cinema-analyze/bin/server start
```

Then open a generated movie folder through the `dir` query parameter:

```text
http://127.0.0.1:8765/?dir=/Users/you/cinema-analyses/promising-young-woman
```

You can also choose a style with the `style` query parameter:

```text
http://127.0.0.1:8765/?dir=/Users/you/cinema-analyses/promising-young-woman&style=cinema
http://127.0.0.1:8765/?dir=/Users/you/cinema-analyses/promising-young-woman&style=gallery
http://127.0.0.1:8765/?dir=/Users/you/cinema-analyses/promising-young-woman&style=dossier
```

### 4. Stop The Preview Server

When you are finished looking at reports, ask the agent to stop the shared preview server:

```text
Stop the Renku Cinema Analyze preview server.
```

For manual control:

```bash
skills/renku-cinema-analyze/bin/server stop
```

This prevents a leftover local server from continuing to run in the background.

## What It Produces

Given a FilmGrab URL, the skill creates a temporary movie analysis folder containing:

- `manifest.json` with the downloaded still metadata
- `analysis.json` with the structured visual-language study
- `full/` with full-size downloaded stills
- `analysis/` with smaller FilmGrab-provided still variants for model analysis
- `report/` with a static rendered copy of the report

The generated movie folders are scratch output. They are intentionally ignored by Git.

## Included Skill

The main skill lives at:

```text
skills/renku-cinema-analyze/SKILL.md
```

It covers:

- FilmGrab still extraction
- capped still sampling
- smaller analysis images from FilmGrab `srcset` variants
- visual-language JSON authoring
- citation validation against `manifest.json`
- browser report rendering
- a shared local preview server
- a sibling-movie analysis picker
- style variants for the report viewer

## Requirements

- Network access when downloading FilmGrab pages and stills
- An agent environment that supports local skills/plugins, such as Codex or Claude Code

There are no package dependencies to install.

## Report Styles

The browser report supports style variants through the `style` query parameter:

```text
http://127.0.0.1:8765/?dir=/path/to/report&style=cinema
http://127.0.0.1:8765/?dir=/path/to/report&style=gallery
http://127.0.0.1:8765/?dir=/path/to/report&style=dossier
```

The top bar also includes a style switcher.

## Preview Server Script

Most users should let Codex or Claude Code run the workflow. If you want to manage the preview server yourself, use the smart lifecycle script:

```bash
skills/renku-cinema-analyze/bin/server start
skills/renku-cinema-analyze/bin/server status
skills/renku-cinema-analyze/bin/server restart
skills/renku-cinema-analyze/bin/server stop
```

The script checks whether the server is already healthy, removes stale PID state, and refuses to start if another process owns the port. The preview server uses the stable local address: `http://127.0.0.1:8765/`.

## Thanks And Attribution

Many thanks to [FilmGrab](https://film-grab.com/) for maintaining a deep visual archive of film stills. This skill depends on FilmGrab pages as the source for still images and keeps the original FilmGrab image URLs in the generated JSON so viewers can inspect the source stills.

Please use direct FilmGrab movie-page links when running this skill. The workflow is designed around explicit links rather than automatic search so FilmGrab can keep receiving traffic, ad views, and link credit for the work of collecting and presenting the stills.

## Plugin Files

The Codex plugin files are:

```text
.agents/plugins/marketplace.json
.codex-plugin/plugin.json
```

The Claude Code plugin files are:

```text
.claude-plugin/marketplace.json
.claude-plugin/plugin.json
```

The skill itself is:

```text
skills/renku-cinema-analyze/SKILL.md
```

Codex uses the skill name from `SKILL.md`, which is why the Codex invocation is `$renku-cinema-analyze`. Claude Code plugin skills are installed from the `cinema-analyze` marketplace and then used through normal prompting.

## Public Codex Plugin Directory

This plugin does not appear in Codex's default curated Plugin Directory unless OpenAI adds it there.

As of the current Codex plugin documentation, OpenAI says official public plugin publishing and self-serve plugin management are coming soon. Until that exists, distribution works through explicit marketplace installation:

```bash
codex plugin marketplace add GoRenku/cinema-analyze --ref main
```

After the marketplace is added, Codex can show `Renku Cinema Analyze Plugins` as a selectable marketplace source, and users can install `cinema-analyze` from there.

## Local Plugin Development

If you are editing the plugin locally, cloning the repo is only a development step. It does not install the plugin by itself.

Clone the source code:

```bash
git clone https://github.com/GoRenku/cinema-analyze.git
```

Then add that local folder as a marketplace root:

```bash
codex plugin marketplace add /absolute/path/to/cinema-analyze
```

After adding the marketplace, restart Codex, open the plugin directory, choose `Renku Cinema Analyze Plugins`, and install `cinema-analyze`.

The marketplace files tell Codex and Claude Code where the plugin lives. The plugin manifests tell the agent that the plugin contains skills under:

```text
./skills/
```

## Repository Layout

```text
.
├── .codex-plugin/
│   └── plugin.json
├── .claude-plugin/
│   ├── marketplace.json
│   └── plugin.json
├── skills/
│   └── renku-cinema-analyze/
│       ├── SKILL.md
│       ├── assets/
│       │   └── viewer.html
│       ├── bin/
│       │   ├── server
│       │   ├── preview-server
│       │   └── stop-preview-server
│       └── scripts/
│           └── internal workflow scripts
└── README.md
```

## Notes

- Generated movie folders are temporary scratch output. Keep them in your base analysis folder rather than in this plugin repository.
- The preview server uses one well-known local port: `127.0.0.1:8765`.
- The movie picker in the report lists sibling folders that contain `analysis.json`.
- The skill avoids inventing credits. If director, cinematographer, or year cannot be found, the report should use `null`.
- The `Inspired by` section is visual lineage, not confirmed production history unless a source explicitly confirms it.
