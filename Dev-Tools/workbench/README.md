# Resource Workbench

A terminal-based workbench (TUI) for discovering, documenting, and running the scripts and tools in this repository.

## Features

- **Auto-Discovery** — Finds `.py`, `.sh`, and `.html` files across the repository and extracts metadata (docstrings, HTML titles).
- **Integrated Documentation** — Displays script docstrings and directory `README.md` files inline.
- **Live Execution** — Runs scripts with real-time output streaming; the UI stays responsive.
- **Image Previews** — Renders PNG/JPG/GIF assets directly in the terminal using Unicode half-blocks.
- **HTML Serving** — Automatically starts a local HTTP server for interactive HTML tools.
- **Pinned Favorites** — Mark tools with `# @runner:pinned` or via `runner.toml` to keep them at the top.

## Usage

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Launch:**
   ```bash
   python3 workbench.py
   ```

## Controls

| Key | Action |
|-----|--------|
| Arrows / Enter | Navigate and select tools |
| `/` | Search tools by name or category |
| `r` | Run the selected tool |
| `k` | Kill a running process |
| `e` | Open source in editor |
| `v` | Toggle the Visuals & Metadata pane |
| `f` | Fullscreen image preview |
| `s` | Open Settings |
| `h` or `?` | Show Help |
| `q` | Quit |

## Architecture

- **`workbench.py`** — Main entry point and UI (Textual app, modal screens, async execution).
- **`discovery.py`** — Stateless discovery engine that scans the repo and returns `RunnableUnit` dataclasses.
- **`runner.toml`** — Configuration: hide tools, override names/descriptions, pin favorites, set UI preferences.

## Configuration (`runner.toml`)

```toml
hide = ["path/to/script.py"]         # Hide specific tools from the library

[settings]
editor_command = "code"              # Editor for the 'e' keybinding
theme = "viridis"                    # viridis | contrast | sunset
auto_clear_logs = true               # Clear terminal output before each run
persist_args = true                  # Remember arguments per tool

[tools."Mathematics/TSP/TSP-code.py"]
name = "TSP Solver"                  # Override display name
description = "Custom description."  # Override description
pinned = true                        # Pin to ★ Favorites
```

## Auto-Discovery Rules

The discovery engine identifies runnable units by these patterns:

- **Python** (`.py`, excluding `__init__.py`) — name from filename, description from module docstring (via `ast`).
- **Shell** (`.sh`) — treated as bash scripts.
- **HTML** (`.html`) — served via local HTTP server; name from `<title>` tag.
- **Directory-based** — a directory containing `main.py`, `run.sh`, or `run-servers.sh` is treated as a single tool.
