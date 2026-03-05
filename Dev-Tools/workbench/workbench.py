"""Resource Workbench — a TUI for discovering, documenting, and running repository tools."""

from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Tree, RichLog, Markdown, Input, Label, Button, Switch, Select
from textual.binding import Binding
from textual.screen import ModalScreen
from discovery import DiscoveryEngine, RunnableUnit
from rich.color import Color
from rich.style import Style
from rich.text import Text
from PIL import Image
import asyncio
import datetime
import webbrowser
import subprocess
import platform

class HelpScreen(ModalScreen[None]):
    """A modal screen showing help and documentation."""
    HELP_TEXT = """
# Resource Workbench Help

The Resource Workbench is your central hub for repository tools.

## Keyboard Shortcuts
- **`Arrows / Enter`**: Navigate and select tools in the library.
- **`/`**: Focus the search bar to find tools by name or category.
- **`r`**: **Run** the selected tool.
- **`k`**: **Kill** a currently running process.
- **`e`**: **Edit** the source code of the selected tool in your configured editor.
- **`v`**: Toggle the **Visuals & Metadata** side pane.
- **`f`**: **Fullscreen** preview of the current image.
- **`s`**: Open the **Settings** menu.
- **`h` or `?`**: Show this **Help** screen.
- **`q`**: **Quit** the Workbench.

## Features
- **Auto-Discovery**: Automatically finds `.py`, `.sh`, and `.html` files.
- **Smart Metadata**: Extracts tool names and descriptions from Python docstrings.
- **Live Previews**: Renders image assets (PNG, JPG, GIF) directly in your terminal.
- **HTML Serving**: Automatically starts a local server to view interactive HTML tools.
- **Pinned Tools**: Tools marked with `# @runner:pinned` appear in your **★ Favorites**.

## Configuration
Settings are saved to `runner.toml`. You can manually hide tools or override their names and descriptions there.
"""

    def compose(self) -> ComposeResult:
        with Vertical(id="help-container"):
            yield Label("WORKBENCH GUIDE", id="help-title")
            yield Markdown(self.HELP_TEXT, id="help-content")
            yield Button("Close Help", id="help-close-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "help-close-button":
            self.dismiss()

class ImagePreviewScreen(ModalScreen[None]):
    """A modal screen showing a fullscreen image preview."""
    BINDINGS = [
        Binding("escape", "dismiss", "Close", show=False),
        Binding("f", "dismiss", "Close", show=False),
        Binding("left", "prev_image", "Previous", show=False),
        Binding("right", "next_image", "Next", show=False),
    ]

    def __init__(self, images: list, index: int, render_fn):
        super().__init__()
        self._images = images
        self._index = index
        self._render_fn = render_fn

    def compose(self) -> ComposeResult:
        with Vertical(id="preview-container"):
            yield Label("IMAGE PREVIEW", id="preview-title")
            yield Label("", id="preview-filename")
            yield Static(id="preview-image")
            with Horizontal(id="preview-nav-bar"):
                yield Button("← Prev", id="preview-prev-button", classes="nav-button")
                yield Label("", id="preview-counter")
                yield Button("Next →", id="preview-next-button", classes="nav-button")
            yield Button("Close  (f)", id="preview-close-button")

    def on_mount(self) -> None:
        self._refresh_preview()

    def _refresh_preview(self) -> None:
        if not self._images:
            return
        image_path = self._images[self._index]
        self.query_one("#preview-filename", Label).update(f"[bold]{image_path.name}[/bold]")
        self.query_one("#preview-counter", Label).update(
            f"{self._index + 1}/{len(self._images)}"
        )
        self.query_one("#preview-nav-bar").display = len(self._images) > 1
        # Render at large width to fill the modal
        preview_text = self._render_fn(image_path, width=90)
        self.query_one("#preview-image", Static).update(preview_text)

    def action_prev_image(self) -> None:
        if self._images:
            self._index = (self._index - 1) % len(self._images)
            self._refresh_preview()

    def action_next_image(self) -> None:
        if self._images:
            self._index = (self._index + 1) % len(self._images)
            self._refresh_preview()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "preview-close-button":
            self.dismiss()
        elif event.button.id == "preview-prev-button":
            self.action_prev_image()
        elif event.button.id == "preview-next-button":
            self.action_next_image()

class SettingsScreen(ModalScreen[None]):
    """A modal screen for application settings."""
    def __init__(self, engine: DiscoveryEngine):
        super().__init__()
        self.engine = engine
        self.settings = self.engine.config.get("settings", {})

    def compose(self) -> ComposeResult:
        with Vertical(id="settings-container"):
            yield Label("WORKBENCH SETTINGS", id="settings-title")
            
            with Horizontal(classes="setting-row"):
                yield Label("Auto-Clear Logs", classes="setting-label")
                yield Switch(value=self.settings.get("auto_clear_logs", True), id="auto_clear_logs")
            
            with Horizontal(classes="setting-row"):
                yield Label("Persist Arguments", classes="setting-label")
                yield Switch(value=self.settings.get("persist_args", True), id="persist_args")
            
            with Horizontal(classes="setting-row"):
                yield Label("Full Path Copy", classes="setting-label")
                yield Switch(value=self.settings.get("full_path_copy", False), id="full_path_copy")
            
            with Horizontal(classes="setting-row"):
                yield Label("UI Theme", classes="setting-label")
                yield Select(
                    [("Viridis Dark", "viridis"), ("High Contrast", "contrast"), ("Sunset", "sunset")],
                    value=self.settings.get("theme", "viridis"),
                    id="theme-select"
                )
            
            with Horizontal(classes="setting-row"):
                yield Label("Editor Command", classes="setting-label")
                yield Input(value=self.settings.get("editor_command", "code"), id="editor_command", classes="setting-input")
            
            with Horizontal(classes="setting-row"):
                yield Label("Extra Paths", classes="setting-label")
                yield Input(
                    value=self.settings.get("extra_paths", ""), 
                    id="extra_paths", 
                    placeholder="Comma-separated relative/absolute paths",
                    classes="setting-input"
                )
                
            yield Button("Save & Close", id="close-button")

    def on_switch_changed(self, event: Switch.Changed) -> None:
        self._update_setting(event.switch.id, event.value)

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.value is Select.NULL:
            return
        theme = str(event.value)
        if self.app.has_class(f"theme-{theme}"):
            return
        self._update_setting("theme", theme)
        self.app.apply_theme(theme)

    def on_input_changed(self, event: Input.Changed) -> None:
        self._update_setting(event.input.id, event.value)

    def _update_setting(self, key: str, value: any) -> None:
        if "settings" not in self.engine.config:
            self.engine.config["settings"] = {}
        self.engine.config["settings"][key] = value
        self.engine.save_config()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close-button":
            self.app.refresh_tools()
            self.dismiss()

class WorkbenchApp(App):
    TITLE = "Resource Workbench"

    CSS = """
    /* --- CONSTANT STRUCTURAL LAYOUT --- */
    #sidebar { width: 32; }
    #search-box { margin: 1; }
    #main-content { width: 1fr; }
    #docs-pane { height: 1.3fr; padding: 1 2; overflow-y: auto; }
    #docs-header, #docs-body { height: auto; background: transparent; }
    #command-bar { height: 3; margin: 1 0; padding: 0 1; align: left middle; }
    #command-text { padding: 0 1; width: 1fr; text-style: italic; }
    #run-now-button { height: 1; min-width: 12; text-style: bold; border: none; margin-left: 1; }
    #copy-command-button { height: 1; min-width: 15; text-style: bold; border: none; }
    #execution-header { height: 1; padding: 0 1; text-style: bold; }
    #execution-pane { height: 1fr; padding: 1; background: black; overflow-y: auto; }
    #controls-pane { height: auto; padding: 1; layout: horizontal; }
    #visuals-pane { width: 44; padding: 1; overflow-y: auto; }
    #image-preview-static { width: 100%; height: auto; text-wrap: nowrap; content-align: center middle; }
    .nav-button { min-width: 8; margin: 0 1; border: none; }
    #open-image-button { width: 1fr; text-style: bold; border: none; margin-top: 1; }
    #image-button-separator { width: 1fr; height: 1; text-align: center; text-style: dim; margin: 0; padding: 0; }
    #fullscreen-image-button { width: 1fr; text-style: bold; border: none; margin-top: 0; }
    #image-counter, #preview-counter { width: 1fr; text-align: center; text-style: italic; }
    Tree { background: transparent; padding: 0 1; height: 1fr; }
    .config-label { width: 12; padding-top: 1; text-style: bold; }
    #arg-input { width: 1fr; }
    Markdown H1 { text-style: bold; background: transparent; margin-bottom: 1; }
    Markdown H2 { text-style: bold; }
    HelpScreen, SettingsScreen, ImagePreviewScreen { align: center middle; background: rgba(0, 0, 0, 0.5); }
    #help-container, #settings-container { width: 70; height: auto; max-height: 90%; padding: 1 2; }
    #preview-container { width: 100; height: auto; max-height: 95%; padding: 1 2; overflow-y: auto; }
    #preview-title { width: 1fr; text-align: center; text-style: bold; margin-bottom: 1; }
    #preview-filename { width: 1fr; text-align: center; text-style: italic; margin-bottom: 1; }
    #preview-image { width: 100%; height: auto; text-wrap: nowrap; content-align: center middle; }
    #preview-nav-bar { height: 3; align: center middle; }
    #preview-close-button { margin-top: 1; width: 1fr; text-style: bold; }
    #help-title, #settings-title { width: 1fr; text-align: center; text-style: bold; margin-bottom: 1; }
    .setting-row { height: 3; align: left middle; }
    .setting-label { width: 25; text-style: bold; }
    .setting-input { width: 1fr; }
    #close-button, #help-close-button { margin-top: 1; width: 1fr; text-style: bold; }

    /* --- THEME: VIRIDIS (DEFAULT) --- */
    .theme-viridis Screen { background: #000f0d; color: #d1d5db; }
    .theme-viridis Header { background: #2c728e; color: #fde725; }
    .theme-viridis Footer { background: #000f0d; color: #21918c; }
    .theme-viridis #sidebar { background: #001a17; border-right: solid #21918c; }
    .theme-viridis #search-box { background: #002622; color: #fde725; border: tall #21918c; }
    .theme-viridis #docs-pane { background: #000f0d; border-bottom: double #21918c; }
    .theme-viridis #command-bar { background: #001a17; border: solid #21918c; }
    .theme-viridis #command-text { color: #fcfdbf; }
    .theme-viridis #run-now-button { background: #05e68c; color: #000f0d; }
    .theme-viridis #copy-command-button { background: #3b528b; color: #fde725; }
    .theme-viridis #execution-header { background: #3b528b; color: #fde725; border-bottom: solid #05e68c; }
    .theme-viridis #execution-pane { border-bottom: solid #21918c; }
    .theme-viridis #controls-pane { background: #001a17; }
    .theme-viridis #visuals-pane { background: #001a17; border-left: solid #21918c; }
    .theme-viridis .nav-button { background: #3b528b; color: #fde725; }
    .theme-viridis #open-image-button, .theme-viridis #fullscreen-image-button { background: #21918c; color: #fde725; }
    .theme-viridis Tree { color: #2c728e; }
    .theme-viridis Tree > .tree--guides { color: #21918c; }
    .theme-viridis .config-label { color: #21918c; }
    .theme-viridis #arg-input { background: #002622; color: #f0f8ff; border: tall #21918c; }
    .theme-viridis Markdown H1 { color: #fde725; border-bottom: solid #05e68c; }
    .theme-viridis Markdown H2 { color: #05e68c; }
    .theme-viridis #help-container, .theme-viridis #settings-container, .theme-viridis #preview-container { background: #001a17; border: thick #21918c; }
    .theme-viridis #help-title, .theme-viridis #settings-title, .theme-viridis #preview-title { color: #fde725; border-bottom: solid #21918c; }
    .theme-viridis .setting-label { color: #05e68c; }
    .theme-viridis .setting-input { background: #002622; color: #fde725; border: tall #21918c; }
    .theme-viridis #close-button, .theme-viridis #help-close-button, .theme-viridis #preview-close-button { background: #3b528b; color: #fde725; }

    /* --- THEME: HIGH CONTRAST --- */
    .theme-contrast Screen { background: black; color: white; }
    .theme-contrast Header { background: white; color: black; }
    .theme-contrast Footer { background: black; color: white; }
    .theme-contrast #sidebar { background: #111; border-right: solid white; }
    .theme-contrast #search-box { background: black; color: white; border: tall white; }
    .theme-contrast #docs-pane { background: black; border-bottom: double white; }
    .theme-contrast #command-bar { background: #111; border: solid white; }
    .theme-contrast #run-now-button { background: white; color: black; }
    .theme-contrast #copy-command-button { background: #333; color: white; }
    .theme-contrast #execution-header { background: #222; color: white; border-bottom: solid white; }
    .theme-contrast #execution-pane { border-bottom: solid white; }
    .theme-contrast #controls-pane { background: black; }
    .theme-contrast #visuals-pane { background: black; border-left: solid white; }
    .theme-contrast Tree { color: white; }
    .theme-contrast .config-label { color: white; }
    .theme-contrast #arg-input { background: black; color: white; border: tall white; }
    .theme-contrast Markdown H1, .theme-contrast Markdown H2 { color: white; border-bottom: solid white; }
    .theme-contrast #help-container, .theme-contrast #settings-container, .theme-contrast #preview-container { background: #111; border: thick white; }
    .theme-contrast #help-title, .theme-contrast #settings-title, .theme-contrast #preview-title { color: white; border-bottom: solid white; }
    .theme-contrast .setting-label { color: white; }
    .theme-contrast .setting-input { background: black; color: white; border: tall white; }
    .theme-contrast #close-button, .theme-contrast #help-close-button, .theme-contrast #preview-close-button { background: #333; color: white; }

    /* --- THEME: SUNSET --- */
    .theme-sunset Screen { background: #2d142c; color: #f8b400; }
    .theme-sunset Header { background: #801336; color: #f8b400; }
    .theme-sunset Footer { background: #2d142c; color: #c72c41; }
    .theme-sunset #sidebar { background: #510a32; border-right: solid #c72c41; }
    .theme-sunset #search-box { background: #510a32; color: #f8b400; border: tall #ee4540; }
    .theme-sunset #docs-pane { background: #2d142c; border-bottom: double #c72c41; }
    .theme-sunset #command-bar { background: #510a32; border: solid #c72c41; }
    .theme-sunset #run-now-button { background: #ee4540; color: white; }
    .theme-sunset #copy-command-button { background: #801336; color: #f8b400; }
    .theme-sunset #execution-header { background: #c72c41; color: #f8b400; border-bottom: solid #ee4540; }
    .theme-sunset #execution-pane { border-bottom: solid #c72c41; }
    .theme-sunset #controls-pane { background: #510a32; }
    .theme-sunset #visuals-pane { background: #510a32; border-left: solid #c72c41; }
    .theme-sunset Tree { color: #f8b400; }
    .theme-sunset .config-label { color: #ee4540; }
    .theme-sunset #arg-input { background: #2d142c; color: #f8b400; border: tall #ee4540; }
    .theme-sunset Markdown H1 { color: #ee4540; border-bottom: solid #ee4540; }
    .theme-sunset Markdown H2 { color: #f8b400; }
    .theme-sunset #help-container, .theme-sunset #settings-container, .theme-sunset #preview-container { background: #510a32; border: thick #c72c41; }
    .theme-sunset #help-title, .theme-sunset #settings-title, .theme-sunset #preview-title { color: #f8b400; border-bottom: solid #c72c41; }
    .theme-sunset .setting-label { color: #ee4540; }
    .theme-sunset .setting-input { background: #2d142c; color: #f8b400; border: tall #ee4540; }
    .theme-sunset #close-button, .theme-sunset #help-close-button, .theme-sunset #preview-close-button { background: #c72c41; color: white; }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "run_script", "Run Script"),
        Binding("k", "kill_script", "Kill Script"),
        Binding("v", "toggle_visuals", "Toggle Info"),
        Binding("f", "fullscreen_image", "Fullscreen"),
        Binding("s", "toggle_settings", "Settings"),
        Binding("e", "open_in_editor", "Edit"),
        Binding("h", "toggle_help", "Help"),
        Binding("?", "toggle_help", "Help", show=False),
        Binding("/", "focus_search", "Search"),
    ]

    def __init__(self):
        super().__init__()
        self.engine = DiscoveryEngine(Path(__file__).parent.parent.parent)
        self.units = self.engine.discover()
        self.current_unit = None
        self.running_process = None
        self.current_images = []
        self.current_image_index = 0

    def apply_theme(self, theme_name: str) -> None:
        for t in ["viridis", "contrast", "sunset"]:
            self.remove_class(f"theme-{t}")
        self.add_class(f"theme-{theme_name}")
        # Theme CSS targets Screen which also matches modal screens,
        # overriding their semi-transparent background to opaque.
        # Textual skips re-styling screens behind opaque modals, so
        # the main screen never gets the new theme. Force-update all.
        for screen in self.screen_stack:
            self.stylesheet.update_nodes(screen.walk_children(with_self=True))

    def refresh_tools(self) -> None:
        self.units = self.engine.discover()
        self._populate_tree(self.query_one("#search-box", Input).value)

    def action_toggle_help(self) -> None:
        self.push_screen(HelpScreen())

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Input(placeholder="Search tools...", id="search-box")
                yield Tree("Library", id="unit-tree")
            with Vertical(id="main-content"):
                with Vertical(id="docs-pane"):
                    yield Markdown(id="docs-header")
                    with Horizontal(id="command-bar"):
                        yield Label("[bold teal]Command:[/bold teal]", classes="config-label", id="command-label")
                        yield Static("Select a tool...", id="command-text")
                        yield Button("Copy Command", id="copy-command-button")
                        yield Button("Run Now", id="run-now-button", variant="success")
                    yield Markdown(id="docs-body")
                yield Label(" TERMINAL OUTPUT", id="execution-header")
                yield RichLog(id="execution-pane", highlight=True, markup=True)
                with Horizontal(id="controls-pane"):
                    yield Label("Arguments:", classes="config-label")
                    yield Input(placeholder="e.g. --steps 1000", id="arg-input")
            with Vertical(id="visuals-pane"):
                yield Label("[bold white]Visuals & Assets[/bold white]")
                yield Markdown(id="visuals-content")
                yield Static(id="image-preview-static")
                with Horizontal(id="image-nav-bar"):
                    yield Button("← Prev", id="prev-image-button", classes="nav-button")
                    yield Label("0/0", id="image-counter")
                    yield Button("Next →", id="next-image-button", classes="nav-button")
                yield Button("Open Image", id="open-image-button")
                yield Static("─" * 40, id="image-button-separator")
                yield Button("Fullscreen Preview", id="fullscreen-image-button")
                yield Label("\n[bold white]Metadata[/bold white]")
                yield Markdown(id="metadata-content")
        yield Footer()

    def on_mount(self) -> None:
        theme = self.engine.config.get("settings", {}).get("theme", "viridis")
        self.apply_theme(theme)
        self._populate_tree()
        self.query_one("#docs-header", Markdown).update("# Resource Workbench")
        self.query_one("#docs-body", Markdown).update("Select a tool from the library or press `/` to search.")
        self.query_one("#command-bar").display = False
        self.query_one("#image-nav-bar").display = False
        self.query_one("#open-image-button").display = False
        self.query_one("#image-button-separator").display = False
        self.query_one("#fullscreen-image-button").display = False

    def _populate_tree(self, filter_text: str = "") -> None:
        tree = self.query_one("#unit-tree", Tree)
        tree.clear()
        tree.root.expand()
        
        categories = {}
        # Pinned items at top
        pinned_node = None
        
        for unit in self.units:
            if filter_text.lower() and filter_text.lower() not in unit.name.lower() and filter_text.lower() not in unit.category.lower():
                continue

            if unit.is_pinned:
                if not pinned_node:
                    pinned_node = tree.root.add("[bold yellow]★ Favorites[/bold yellow]", expand=True)
                pinned_node.add_leaf(f"[yellow]{unit.name}[/yellow]", data=unit)
            else:
                if unit.category not in categories:
                    categories[unit.category] = tree.root.add(unit.category, expand=True)
                categories[unit.category].add_leaf(unit.name, data=unit)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search-box":
            self._populate_tree(event.value)
        elif event.input.id == "arg-input":
            if self.current_unit and self.engine.config.get("settings", {}).get("persist_args", True):
                try:
                    rel_path = str(self.current_unit.path.relative_to(self.engine.root_dir))
                except ValueError:
                    rel_path = str(self.current_unit.path)
                if "tools" not in self.engine.config:
                    self.engine.config["tools"] = {}
                if rel_path not in self.engine.config["tools"]:
                    self.engine.config["tools"][rel_path] = {}
                self.engine.config["tools"][rel_path]["last_args"] = event.value
                self.engine.save_config()

    def action_focus_search(self) -> None:
        self.query_one("#search-box").focus()

    def action_toggle_settings(self) -> None:
        self.push_screen(SettingsScreen(self.engine))

    def action_open_in_editor(self) -> None:
        if self.current_unit:
            editor = self.engine.config.get("settings", {}).get("editor_command", "code")
            try:
                subprocess.Popen([editor, str(self.current_unit.path)])
                self.query_one("#execution-pane", RichLog).write(f"[bold green]>>> OPENING IN EDITOR:[/bold green] [dim]{self.current_unit.name}[/dim]")
            except Exception as e:
                self.query_one("#execution-pane", RichLog).write(f"[bold red]Editor error: {str(e)}[/bold red]")

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        if event.node.data:
            unit: RunnableUnit = event.node.data
            self.current_unit = unit
            
            # Load persisted args
            if self.engine.config.get("settings", {}).get("persist_args", True):
                try:
                    rel_path = str(unit.path.relative_to(self.engine.root_dir))
                except ValueError:
                    rel_path = str(unit.path)
                last_args = self.engine.config.get("tools", {}).get(rel_path, {}).get("last_args", "")
                self.query_one("#arg-input", Input).value = last_args

            # Header Info
            header_md = [f"# {unit.name}"]
            if unit.is_pinned:
                header_md.append("> ★ **Favorite Tool**")
            header_md.append(f"**Category:** {unit.category}")
            try:
                rel_path = unit.path.relative_to(self.engine.root_dir)
            except ValueError:
                rel_path = unit.path
            header_md.append(f"**Path:** `{rel_path}`")
            
            self.query_one("#docs-header", Markdown).update("\n".join(header_md))
            
            # Command Bar
            self.query_one("#command-bar").display = True
            self.query_one("#command-text", Static).update(unit.command)
            
            # Change button label for HTML
            btn = self.query_one("#run-now-button", Button)
            if unit.path.suffix == ".html":
                btn.label = "View Page"
            else:
                btn.label = "Run Now"
            
            # Body Info
            body_md = [unit.description or "*No description provided.*"]
            readme_path = unit.path.parent / "README.md"
            if readme_path.exists():
                body_md.append("\n---\n")
                body_md.append(readme_path.read_text())
                
            self.query_one("#docs-body", Markdown).update("\n".join(body_md))
            self._update_visuals_and_metadata()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run-now-button":
            self.run_worker(self.action_run_script())
        elif event.button.id == "copy-command-button":
            self.action_copy_command()
        elif event.button.id == "prev-image-button":
            self.action_prev_image()
        elif event.button.id == "next-image-button":
            self.action_next_image()
        elif event.button.id == "open-image-button":
            self.action_open_image()
        elif event.button.id == "fullscreen-image-button":
            self.action_fullscreen_image()

    def action_copy_command(self) -> None:
        if not self.current_unit:
            return
        
        args = self.query_one("#arg-input", Input).value
        
        # Determine command base
        if self.engine.config.get("settings", {}).get("full_path_copy", False):
            # Use absolute path
            if "python3 " in self.current_unit.command:
                base_cmd = f"python3 {self.current_unit.path.absolute()}"
            elif "bash " in self.current_unit.command:
                base_cmd = f"bash {self.current_unit.path.absolute()}"
            else:
                base_cmd = f"{self.current_unit.command.split()[0]} {self.current_unit.path.absolute()}"
        else:
            base_cmd = self.current_unit.command
            
        full_cmd = f"{base_cmd} {args}".strip()
        
        if self._copy_to_clipboard(full_cmd):
            log = self.query_one("#execution-pane", RichLog)
            log.write(f"[bold green]>>> COPIED TO CLIPBOARD:[/bold green] [dim]{full_cmd}[/dim]")

    def _copy_to_clipboard(self, text: str) -> bool:
        try:
            if platform.system() == "Darwin":
                process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
                process.communicate(text.encode('utf-8'))
            elif platform.system() == "Windows":
                subprocess.run(['clip'], input=text.encode('utf-16'), check=True)
            else:
                # Try xclip or xsel on Linux
                try:
                    subprocess.run(['xclip', '-selection', 'clipboard'], input=text.encode('utf-8'), check=True)
                except FileNotFoundError:
                    subprocess.run(['xsel', '--clipboard', '--input'], input=text.encode('utf-8'), check=True)
            return True
        except Exception as e:
            self.query_one("#execution-pane", RichLog).write(f"[bold red]Clipboard error: {str(e)}[/bold red]")
            return False

    def action_prev_image(self) -> None:
        if self.current_images:
            self.current_image_index = (self.current_image_index - 1) % len(self.current_images)
            self._show_current_image()

    def action_next_image(self) -> None:
        if self.current_images:
            self.current_image_index = (self.current_image_index + 1) % len(self.current_images)
            self._show_current_image()

    def action_open_image(self) -> None:
        if self.current_images and 0 <= self.current_image_index < len(self.current_images):
            image_path = self.current_images[self.current_image_index]
            try:
                if platform.system() == "Darwin":
                    subprocess.run(["open", str(image_path)])
                elif platform.system() == "Windows":
                    os.startfile(image_path)
                else:
                    subprocess.run(["xdg-open", str(image_path)])
            except Exception as e:
                self.query_one("#execution-pane", RichLog).write(f"[red]Failed to open image: {str(e)}[/red]")

    def action_fullscreen_image(self) -> None:
        if self.current_images:
            self.push_screen(ImagePreviewScreen(
                images=self.current_images,
                index=self.current_image_index,
                render_fn=self._render_image_preview,
            ))

    def _show_current_image(self) -> None:
        if self.current_images:
            image_path = self.current_images[self.current_image_index]
            self.query_one("#image-nav-bar").display = len(self.current_images) > 1
            self.query_one("#open-image-button").display = True
            self.query_one("#image-button-separator").display = True
            self.query_one("#fullscreen-image-button").display = True
            self.query_one("#image-counter", Label).update(f"{self.current_image_index + 1}/{len(self.current_images)}")
            
            # Update Preview
            preview_text = self._render_image_preview(image_path)
            self.query_one("#visuals-content", Markdown).update(f"**Preview:** `{image_path.name}`\n\n")
            self.query_one("#image-preview-static", Static).update(preview_text)
        else:
            self.query_one("#image-nav-bar").display = False
            self.query_one("#open-image-button").display = False
            self.query_one("#image-button-separator").display = False
            self.query_one("#fullscreen-image-button").display = False
            self.query_one("#visuals-content", Markdown).update("*No visual assets found.*")
            self.query_one("#image-preview-static", Static).update(Text(""))

    def _update_visuals_and_metadata(self) -> None:
        if not self.current_unit:
            return
            
        unit_dir = self.current_unit.path.parent
        unit_path = self.current_unit.path
        
        # Metadata
        stats = unit_path.stat()
        size_kb = stats.st_size / 1024
        mtime = datetime.datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M')
        
        metadata_md = (
            f"- **File Size:** {size_kb:.1f} KB\n"
            f"- **Modified:** {mtime}\n"
            f"- **Type:** {unit_path.suffix.upper()[1:]}\n"
            f"- **Dir:** `{unit_dir.name}/`"
        )
        self.query_one("#metadata-content", Markdown).update(metadata_md)

        # Update Image List
        self.current_images = []
        for ext in (".png", ".jpg", ".jpeg", ".gif"):
            self.current_images.extend(list(unit_dir.glob(f"*{ext}")))
        
        self.current_images.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        self.current_image_index = 0
        self._show_current_image()

    def _render_image_preview(self, image_path: Path, width: int = 38) -> Text:
        """Render an image to a Rich Text object using Unicode half-blocks."""
        try:
            with Image.open(image_path) as img:
                img = img.convert("RGB")
                # Calculate height: each char is 2 vertical pixels
                aspect_ratio = img.height / img.width
                height = int(width * aspect_ratio)
                if height > 40: # Cap height
                    height = 40
                    width = int(height / aspect_ratio)
                
                # Each character represents 2 vertical pixels (top/bottom)
                img = img.resize((width, height * 2), Image.Resampling.LANCZOS)
                
                result = Text()
                for y in range(0, height * 2, 2):
                    for x in range(width):
                        r1, g1, b1 = img.getpixel((x, y))
                        r2, g2, b2 = img.getpixel((x, y + 1))
                        
                        # Use Unicode Lower Half Block '▄' (U+2584)
                        # Top pixel is background color, Bottom pixel is foreground
                        style = Style(
                            color=Color.from_rgb(r2, g2, b2),
                            bgcolor=Color.from_rgb(r1, g1, b1)
                        )
                        result.append("▄", style=style)
                    result.append("\n")
                return result
        except Exception as e:
            return Text(f"Preview Failed: {str(e)}", style="red")

    async def action_run_script(self) -> None:
        if not self.current_unit:
            return
        
        log = self.query_one("#execution-pane", RichLog)
        args = self.query_one("#arg-input", Input).value
        
        if self.engine.config.get("settings", {}).get("auto_clear_logs", True):
            log.clear()

        # Handle HTML Serving
        if self.current_unit.command.startswith("serve "):
            await self._serve_html(log)
            return

        log.write(f"[bold green]>>> RUNNING:[/bold green] [white]{self.current_unit.name}[/white]")
        if args:
            log.write(f"[dim]Args: {args}[/dim]")
        log.write("=" * 40 + "\n")
        
        if self.running_process:
            log.write("[bold red]ERROR: A script is already running. Press 'k' to kill it first.[/bold red]")
            return

        try:
            cwd = self.current_unit.path.parent
            cmd = f"{self.current_unit.command} {args}"
            
            self.running_process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            async def stream_output(stream, is_stderr=False):
                while True:
                    line = await stream.readline()
                    if line:
                        text = line.decode().strip()
                        if is_stderr:
                            log.write(f"[red]{text}[/red]")
                        else:
                            log.write(text)
                    else:
                        break

            await asyncio.gather(
                stream_output(self.running_process.stdout),
                stream_output(self.running_process.stderr, is_stderr=True)
            )
            
            await self.running_process.wait()
            log.write("\n" + "=" * 40)
            if self.running_process.returncode == 0:
                log.write("[bold green]>>> FINISHED SUCCESSFULLY[/bold green]")
            else:
                log.write(f"[bold red]>>> FAILED (Exit Code: {self.running_process.returncode})[/bold red]")
            
            self._update_visuals_and_metadata()
            
        except Exception as e:
            log.write(f"[bold red]CRITICAL ERROR: {str(e)}[/bold red]")
        finally:
            self.running_process = None

    async def _serve_html(self, log: RichLog) -> None:
        filename = self.current_unit.path.name
        cwd = self.current_unit.path.parent
        
        # Find an open port
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', 0))
        port = sock.getsockname()[1]
        sock.close()

        log.write(f"[bold cyan]>>> STARTING SERVER FOR:[/bold cyan] [white]{filename}[/white]")
        log.write(f"[dim]Directory: {cwd}[/dim]")
        log.write(f"[bold yellow]Access via: http://localhost:{port}/{filename}[/bold yellow]")
        log.write("\n" + "=" * 40)
        
        if self.running_process:
            log.write("[bold red]ERROR: A script/server is already running. Press 'k' to kill it first.[/bold red]")
            return

        try:
            # We use subprocess for the server so it's easy to kill
            cmd = f"python3 -m http.server {port}"
            self.running_process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            # Open browser after a short delay
            async def delayed_open():
                await asyncio.sleep(0.5)
                webbrowser.open(f"http://localhost:{port}/{filename}")
                log.write("[green]>>> Web browser opened successfully.[/green]")

            asyncio.create_task(delayed_open())

            async def stream_output(stream, is_stderr=False):
                while True:
                    line = await stream.readline()
                    if line:
                        text = line.decode().strip()
                        if is_stderr:
                            log.write(f"[dim red]{text}[/dim red]")
                        else:
                            log.write(f"[dim]{text}[/dim]")
                    else:
                        break

            await asyncio.gather(
                stream_output(self.running_process.stdout),
                stream_output(self.running_process.stderr, is_stderr=True)
            )
            
        except Exception as e:
            log.write(f"[bold red]CRITICAL ERROR: {str(e)}[/bold red]")
        finally:
            self.running_process = None

    def action_kill_script(self) -> None:
        if self.running_process:
            self.running_process.kill()
            self.query_one("#execution-pane", RichLog).write("\n[bold yellow]>>> PROCESS TERMINATED BY USER[/bold yellow]")
            self.running_process = None

    def action_toggle_visuals(self) -> None:
        visuals = self.query_one("#visuals-pane")
        visuals.display = not visuals.display

if __name__ == "__main__":
    app = WorkbenchApp()
    app.run()
