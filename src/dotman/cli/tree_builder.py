import pathlib

from rich import print
from rich.tree import Tree

from dotman.core.config import InternalFileSystemObject


def _add_to_tree(directory: pathlib.Path, tree_node: Tree, temp_log_file: pathlib.Path) -> None:
    """Safely loops through directory contents and adds them to the Rich tree."""
    try:
        # Sort so folders stay on top, followed alphabetically by files
        items = sorted(directory.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    except PermissionError:
        # Silently skip folders that your user account doesn't have access to read
        return

    for item in items:
        if item.name in InternalFileSystemObject.values() or item.name == temp_log_file.name:
            continue

        if item.is_dir():
            # Create a stylized folder branch
            branch = tree_node.add(f"📂 [bold magenta1]{item.name}[/]")
            # Recursively descend into the subfolder
            _add_to_tree(item, branch, temp_log_file)
        else:
            # Color-code different file extensions beautifully
            if item.suffix == ".py":
                tree_node.add(f"🐍 [spring_green3]{item.name}[/]")
            elif item.suffix in [".json", ".yaml", ".yml", ".toml"]:
                tree_node.add(f"⚙️  [bright_yellow]{item.name}[/]")
            elif item.suffix in [".md", ".txt"]:
                tree_node.add(f"📝 [cornflower_blue]{item.name}[/]")
            else:
                tree_node.add(f"📄 [bright_white]{item.name}[/]")


def print_beautiful_directory(temp_log_file: pathlib.Path, target_path: pathlib.Path):
    """Initializes the root tree node and triggers the clean printer."""
    root_path = pathlib.Path(target_path).resolve()

    # Base layout frame with custom neon cyan connector lines
    root_tree = Tree(
        f"✨ [bold black on violet] {root_path.name or root_path} [/]",
        guide_style="bold bright_cyan",
    )

    _add_to_tree(root_path, root_tree, temp_log_file)
    print(root_tree)
