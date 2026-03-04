# Resource Workbench Design: A Universal Runner for Scientific Tools

**Date:** 2026-03-04  
**Status:** Approved  
**Author:** Gemini CLI  

## 1. Overview
The **Resource Workbench** is a terminal-based workbench (TUI) designed to unify the disparate Python simulations, LaTeX templates, and numerical experiments in the `Resources` repository into a single, interactive application. It provides a full-screen interface for discovering, documenting, and executing scientific tools without leaving the terminal.

## 2. Core Features
### 2.1 Hybrid Discovery Engine
The system will automatically identify "Runnable Units" by scanning the repository:
- **Patterns:** Looks for `main.py`, `run.sh`, `run-servers.sh`, or any `.py` file containing a specific docstring or `# @runner` tag.
- **Categorization:** Uses the folder structure (e.g., `Mathematics/Numerical-Methods`) as the primary organizational hierarchy.
- **`runner.toml` Override:** Allows the user to:
    - Pin favorite tools to the top.
    - Hide noise (like `repo-dashboard.py`).
    - Provide custom display names and descriptions.
    - Define default arguments for specific scripts.

### 2.2 Interactive TUI (Textual)
A full-screen dashboard built with the **Textual** library, featuring:
- **Navigation Sidebar:** A searchable tree-view of categories and scripts.
- **The "Main Stage":**
    - **Documentation View:** Renders the script's `README.md` or its top-level docstring using `Rich` for beautiful Markdown formatting.
    - **Execution Log:** A live-scrolling terminal window that captures output from running processes in real-time.
- **Optional Info Panels (Collapsible):**
    - **Asset Preview:** Displays details of the most recently generated `.png` or `.pdf` in the script's directory.
    - **Parameter Config:** A form to input command-line arguments (e.g., `--iterations 5000`) before running.
    - **Health & Metadata:** File size, last-run timestamp, and exit status of the previous run.

### 2.3 Integrated Execution Lifecycle
- **Real-time Streaming:** Uses `asyncio.create_subprocess_exec` to run scripts asynchronously, ensuring the TUI remains responsive while heavy math simulations are processing.
- **Input Handling:** Provides a "Kill" button to safely terminate runaway or long-running processes.
- **Post-Run Hook:** After execution, the Workbench rescans the script's directory for new output files (plots/data) to update the preview pane.

## 3. Technical Architecture
### 3.1 Stack
- **Language:** Python 3.x
- **UI Framework:** [Textual](https://textual.textualize.io/) (modern async TUI framework).
- **Rendering:** [Rich](https://github.com/Textualize/rich) (for Markdown, tables, and colorized terminal output).
- **Configuration:** `toml` (built-in Python library for the discovery config).

### 3.2 Data Flow
1. **Startup:** Discovery Engine scans the disk → Builds an internal map of Runnable Units.
2. **User Input:** Selection in Sidebar → Fetches documentation and metadata for the unit.
3. **Execution:** User clicks "Run" → Subprocess launches → Output streams to the Execution Log.
4. **Completion:** Process exits → Workbench scans for new assets → Updates UI state.

## 4. Maintenance & "Indefinite" Reliability
- **Dependency Management:** All UI logic is decoupled from the scripts it runs. If a script's dependencies break, the Workbench still functions and can report the error.
- **Standard Tooling:** Relies on standard Python subprocess and signal handling, which are stable across OS updates (macOS/Linux).
- **Self-Documenting:** New scripts added to the repo are automatically included if they follow the standard naming patterns, requiring zero manual configuration for basic usage.
