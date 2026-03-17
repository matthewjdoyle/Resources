# Dev-Tools

Terminal utilities for exploring and maintaining this repository.

## Tools

### `repo-dashboard.py`

Scans every repository in the parent directory and prints a colour-coded breakdown of languages, line counts, and file types.

```bash
python3 Dev-Tools/repo-dashboard.py
```

### `readme-coverage.py`

Walks the repo tree and reports which directories have a `README.md` and which don't, with a coverage score.

```bash
python3 Dev-Tools/readme-coverage.py              # scan repo root
python3 Dev-Tools/readme-coverage.py --missing    # show only gaps
python3 Dev-Tools/readme-coverage.py --depth 2    # top 2 levels only
python3 Dev-Tools/readme-coverage.py /other/path  # custom root
```

### `workbench/`

A full terminal UI (TUI) for discovering, documenting, and running scripts across the repository. See [`workbench/README.md`](workbench/README.md) for details.
