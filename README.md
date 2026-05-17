# Renku Cinema Analyze

![Renku Cinema Analyze visual language preview](analysis-sample.gif)

Renku Cinema Analyze turns a [FilmGrab](https://film-grab.com/) movie page into a cinematographer-focused visual-language report.

Give the skill a FilmGrab movie page. It downloads a safe working set of stills, asks the agent to analyze the movie's visual language, validates the still references, and creates a browser report you can open locally.

## Quick Start

1. Install the plugin for the agent you use: Codex or Claude Code.
2. Start a new Codex or Claude Code session after installing it.
3. Open or create one folder where your movie reports should live, for example:

   ```bash
   mkdir -p ~/cinema-analyses
   ```

4. Open that folder as your workspace in Codex or Claude Code.
5. Paste a FilmGrab movie page prompt.

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

6. When the agent finishes, open the preview link it gives you.
7. When you are done looking at reports, ask the agent:

   ```text
   Stop the Renku Cinema Analyze preview server.
   ```

## Install

### Codex

This plugin is not listed in Codex's default curated Plugin Directory yet. For now, add this GitHub repository as a Codex plugin marketplace:

```bash
codex plugin marketplace add GoRenku/cinema-analyze --ref main
```

Then install the plugin from that added marketplace:

1. Open Codex.
2. Open the plugin directory.
   - In the Codex CLI, type `/plugins`.
   - In the Codex app, open Plugins.
3. Choose the `Renku Cinema Analyze Plugins` marketplace. It appears after you add the marketplace above.
4. Install `cinema-analyze`.
5. Start a new Codex thread.

In Codex, `cinema-analyze` is the plugin package. The callable skill is named `renku-cinema-analyze`, so you invoke it with:

```text
$renku-cinema-analyze
```

### Claude Code CLI

Claude Code's terminal CLI uses slash commands for plugins.

1. Open a project with `claude` in the terminal.
2. In the chat input, add this GitHub repository as a plugin marketplace:

   ```text
   /plugin marketplace add GoRenku/cinema-analyze
   ```

3. Install the plugin from that marketplace:

   ```text
   /plugin install cinema-analyze@cinema-analyze
   ```

4. Activate the newly installed plugin in the current session:

   ```text
   /reload-plugins
   ```

You can also run `/plugin` on its own to open the interactive plugin manager. From there, use the Discover, Installed, Marketplaces, and Errors tabs to add the marketplace or install the plugin.

If `/plugin` is not recognized in the CLI, your Claude Code is too old. Update it with `brew upgrade claude-code`, `npm install -g @anthropic-ai/claude-code@latest`, or the native installer. Then restart Claude Code and try again.

### Claude Desktop

The Claude Desktop app for macOS and Windows uses a plugin browser instead of the `/plugin marketplace add` slash command.

1. Open the Claude Desktop app.
2. Click the **Cowork** tab in the mode selector at the top of the app.
3. In the left sidebar, click **Customize**.
4. Click **Browse plugins**.
5. Select **Personal**.
6. Click the **+** button and select **Add marketplace from GitHub**.
7. Enter the repository URL:

   ```text
   https://github.com/GoRenku/cinema-analyze
   ```

8. Once the marketplace is added, find `cinema-analyze` in the plugin list and install it.

After installing, switch to the **Code** tab and start a Local session. The plugin's skills become available to the agent. Use **+** -> **Plugins** -> **Manage plugins** in a Code session to enable, disable, or uninstall it later.

Plugins are not available for Desktop **Remote** sessions. Use Local or SSH sessions.

Claude Code plugin usage is prompt-driven. Once the plugin is installed, ask Claude Code to use the Renku Cinema Analyze skill with a FilmGrab movie URL:

```text
Use the Renku Cinema Analyze skill to analyze this FilmGrab movie page:
https://film-grab.com/2021/05/07/promising-young-woman/
```

## Using The Skill

These steps are the same whether you installed the plugin in Codex or Claude Code.

### Choose A Reports Folder

Create one folder where all generated movie studies will go:

```bash
mkdir -p ~/cinema-analyses
```

Open that folder as the workspace folder in Codex or Claude Code when you are creating analyses.

Each movie gets its own generated folder inside the current workspace:

```text
~/cinema-analyses/
  promising-young-woman/
  the-substance/
  in-the-mood-for-love/
```

Keeping all studies in one base folder makes the report viewer's movie picker useful. It can list sibling folders that contain `analysis.json`.

### Analyze A Movie

Use a direct [FilmGrab](https://film-grab.com/) movie URL.

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

The skill intentionally uses direct FilmGrab movie-page links instead of automatically searching the web. This keeps you in control of the source page and helps FilmGrab continue to receive visits, ad views, and link credit for the still images they provide.

### View The Report

The skill renders a static report into each movie folder. It also starts a shared local preview server on one stable address:

```text
http://127.0.0.1:8765/
```

When the agent finishes, it should give you a direct preview link for the generated report. Open that link in your browser.

The server home page also includes a movie picker when the preview server knows your base reports folder.

### Stop The Preview

When you are finished looking at reports, ask the agent to stop the shared preview server:

```text
Stop the Renku Cinema Analyze preview server.
```

This prevents a leftover local server from continuing to run in the background.

## Advanced Usage

Use this section if you want to manage the preview server yourself, bookmark report URLs, or switch report styles manually.

### Manage The Preview Server

The preview server should be managed through the bundled server helper:

```bash
skills/renku-cinema-analyze/bin/server start --base-dir ~/cinema-analyses
```

The same helper supports:

```bash
skills/renku-cinema-analyze/bin/server status
skills/renku-cinema-analyze/bin/server restart --base-dir ~/cinema-analyses
skills/renku-cinema-analyze/bin/server stop
```

The shared preview server uses:

```text
127.0.0.1:8765
```

### Open A Specific Report

Open the server home page to pick from the analyses in your base folder:

```text
http://127.0.0.1:8765/
```

Open a generated movie folder directly through the `dir` query parameter:

```text
http://127.0.0.1:8765/?dir=/Users/you/cinema-analyses/promising-young-woman
```

### Switch Report Styles

The browser report supports style variants through the `style` query parameter:

```text
http://127.0.0.1:8765/?dir=/Users/you/cinema-analyses/promising-young-woman&style=cinema
http://127.0.0.1:8765/?dir=/Users/you/cinema-analyses/promising-young-woman&style=gallery
http://127.0.0.1:8765/?dir=/Users/you/cinema-analyses/promising-young-woman&style=dossier
```

The top bar in the report also includes a style switcher.

## What The Skill Creates

Given a FilmGrab URL, the skill creates one movie analysis folder. That folder contains:

- `manifest.json`: an index of the downloaded stills, their local analysis images, and their original FilmGrab source URLs.
- `analysis.json`: the structured visual-language study used by the report.
- `analysis/`: smaller FilmGrab-provided image variants used by the agent for visual analysis.
- `report/`: browser-ready report files rendered from the reusable viewer.

Generated movie folders are scratch output. They are intentionally ignored by Git, and they should usually live in your reports folder rather than inside this plugin repository.

## How It Works Internally

The main skill lives at:

```text
skills/renku-cinema-analyze/SKILL.md
```

The skill workflow is:

1. Extract still image URLs from a FilmGrab movie page.
2. Download a capped working set of smaller FilmGrab image variants for analysis.
3. Ask the agent to analyze every downloaded still as a visual system.
4. Write a structured `analysis.json` study.
5. Validate cited still URLs against `manifest.json`.
6. Render the reusable browser report.
7. Serve reports through the shared local preview server.

Important implementation files:

- `skills/renku-cinema-analyze/SKILL.md`: the agent-facing workflow, analysis rules, and JSON schema.
- `skills/renku-cinema-analyze/scripts/prepare_filmgrab_stills.py`: extracts still URLs, downloads smaller analysis copies, and writes `manifest.json`.
- `skills/renku-cinema-analyze/scripts/validate_analysis_json.py`: validates schema basics and verifies cited still URLs against the manifest.
- `skills/renku-cinema-analyze/scripts/render_report.py`: creates the report folder from `analysis.json` and the stable viewer template.
- `skills/renku-cinema-analyze/scripts/preview_report_server.py`: serves reports on `127.0.0.1:8765`.
- `skills/renku-cinema-analyze/bin/server`: lifecycle wrapper for the shared preview server.
- `.agents/plugins/marketplace.json` and `.codex-plugin/plugin.json`: Codex plugin marketplace and plugin metadata.
- `.claude-plugin/marketplace.json` and `.claude-plugin/plugin.json`: Claude Code plugin marketplace and plugin metadata.

Codex uses the skill name from `SKILL.md`, which is why the Codex invocation is `$renku-cinema-analyze`. Claude Code plugin skills are installed from the `cinema-analyze` marketplace and then used through normal prompting.

### Local Plugin Development

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

The plugin manifests tell the agent that the plugin contains skills under:

```text
./skills/
```

### Repository Layout

```text
.
├── .agents/
│   └── plugins/
│       └── marketplace.json
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
│           ├── prepare_filmgrab_stills.py
│           ├── preview_report_server.py
│           ├── render_report.py
│           └── validate_analysis_json.py
└── README.md
```

## Thanks And Attribution

Many thanks to [FilmGrab](https://film-grab.com/) for maintaining a deep visual archive of film stills. This skill depends on FilmGrab pages as the source for still images and keeps the original FilmGrab image URLs in the generated JSON so viewers can inspect the source stills.

Please use direct FilmGrab movie-page links when running this skill. The workflow is designed around explicit links rather than automatic search so FilmGrab can keep receiving traffic, ad views, and link credit for the work of collecting and presenting the stills.

## Limitations And Notes

- This plugin does not appear in Codex's default curated Plugin Directory unless OpenAI adds it there. Until then, Codex users install it by explicitly adding the `GoRenku/cinema-analyze` marketplace.
- The preview server uses one well-known local port: `127.0.0.1:8765`.
- The `Inspired by` section is visual lineage, not confirmed production history unless a source explicitly confirms it.
