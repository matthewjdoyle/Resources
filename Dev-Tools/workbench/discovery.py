"""Discovery engine — scans the repository for runnable scripts and extracts metadata."""

import ast
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
import toml

@dataclass
class RunnableUnit:
    name: str
    path: Path
    category: str
    description: str
    command: str
    is_pinned: bool = False

class DiscoveryEngine:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.skip_dirs = {".git", "__pycache__", ".venv", "venv", "env", "node_modules", "docs", "Dev-Tools", "Templates"}
        self.config = self._load_config()

    def _load_config(self):
        config_path = self.root_dir / "Dev-Tools" / "workbench" / "runner.toml"
        if config_path.exists():
            try:
                return toml.load(config_path)
            except Exception:
                return {}
        return {}

    def save_config(self):
        config_path = self.root_dir / "Dev-Tools" / "workbench" / "runner.toml"
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                toml.dump(self.config, f)
        except Exception:
            pass

    def discover(self) -> List[RunnableUnit]:
        units = []
        # Check for explicit tools in config
        config_tools = self.config.get("tools", {})
        
        # Determine paths to search
        search_paths = [self.root_dir]
        extra_paths = self.config.get("settings", {}).get("extra_paths", "")
        if extra_paths:
            for p in extra_paths.split(","):
                p = p.strip()
                if p:
                    path_obj = Path(p)
                    if not path_obj.is_absolute():
                        path_obj = self.root_dir / path_obj
                    if path_obj.exists():
                        search_paths.append(path_obj)

        for search_root in search_paths:
            for path in search_root.rglob("*"):
                if any(part in self.skip_dirs for part in path.parts):
                    continue
                
                # Check if this path is hidden in config
                try:
                    rel_path = str(path.relative_to(self.root_dir))
                except ValueError:
                    rel_path = str(path) # For paths outside root_dir

                if rel_path in self.config.get("hide", []):
                    continue

                unit = self._identify_unit(path)
                if unit:
                    # Apply overrides from config if they exist
                    if rel_path in config_tools:
                        override = config_tools[rel_path]
                        unit.name = override.get("name", unit.name)
                        unit.description = override.get("description", unit.description)
                        unit.command = override.get("command", unit.command)
                        unit.is_pinned = override.get("pinned", False)
                    
                    units.append(unit)
        
        # Sort: Pinned first, then by Category, then by Name
        return sorted(units, key=lambda x: (not x.is_pinned, x.category, x.name))

    def _identify_unit(self, path: Path) -> Optional[RunnableUnit]:
        if path.is_dir():
            # Check for directory-based tools (e.g. ones with a specific runner script)
            run_scripts = ["run.sh", "run-servers.sh", "main.py"]
            for s in run_scripts:
                script_path = path / s
                if script_path.exists():
                    return self._identify_unit(script_path)
            return None
        
        # Python scripts
        if path.suffix == ".py" and path.name != "__init__.py":
            return self._create_python_unit(path)
        
        # Shell scripts
        if path.suffix == ".sh":
            return self._create_shell_unit(path)

        # HTML files
        if path.suffix == ".html":
            return self._create_html_unit(path)
        
        return None

    def _create_html_unit(self, path: Path) -> RunnableUnit:
        # Extract title from HTML
        title = ""
        try:
            content = path.read_text(encoding="utf-8")
            import re
            match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
            if match:
                title = match.group(1).strip()
        except Exception:
            pass

        return RunnableUnit(
            name=path.stem.replace("_", " ").replace("-", " ").title(),
            path=path,
            category=self._get_category(path),
            description=f"Interactive HTML Visualization: {title or path.name}",
            command=f"serve {path.name}"
        )

    def _get_category(self, path: Path) -> str:
        relative = path.relative_to(self.root_dir)
        if len(relative.parts) > 1:
            return relative.parts[0]
        return "General"

    def _extract_python_metadata(self, path: Path):
        """Extract docstring and look for @runner tags using AST."""
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            docstring = ast.get_docstring(tree) or ""
            
            # Look for @runner tags in comments (AST doesn't keep comments easily, so we use regex or simple scan)
            is_pinned = False
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                if "# @runner:pinned" in content:
                    is_pinned = True
            
            return docstring.strip(), is_pinned
        except Exception:
            return "No description available.", False

    def _create_python_unit(self, path: Path) -> RunnableUnit:
        doc, is_pinned = self._extract_python_metadata(path)
        
        # Format name: "ode_solvers.py" -> "ODE Solvers"
        name = path.stem.replace("_", " ").replace("-", " ")
        # Special case for acronyms
        name = " ".join([word.upper() if word.lower() in ["ode", "tsp", "ui", "api"] else word.capitalize() for word in name.split()])
        
        return RunnableUnit(
            name=name,
            path=path,
            category=self._get_category(path),
            description=doc or "No description available.",
            command=f"python3 {path.name}",
            is_pinned=is_pinned
        )

    def _create_shell_unit(self, path: Path) -> RunnableUnit:
        return RunnableUnit(
            name=path.name,
            path=path,
            category=self._get_category(path),
            description=f"Shell script in {self._get_category(path)}",
            command=f"bash {path.name}"
        )

if __name__ == "__main__":
    engine = DiscoveryEngine(Path(__file__).parent.parent.parent)
    for unit in engine.discover():
        pin_str = "[PINNED] " if unit.is_pinned else ""
        print(f"{pin_str}[{unit.category}] {unit.name}")
        if unit.description:
            print(f"  {unit.description.splitlines()[0]}...")
