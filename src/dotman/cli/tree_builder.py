import pathlib

from rich.tree import Tree


def _add_to_tree(directory: pathlib.Path, tree_node: Tree) -> None:
    """Safely loops through directory contents and adds them to the Rich tree."""
    try:
        # Sort so folders stay on top, followed alphabetically by files
        items = sorted(directory.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    except PermissionError:
        # Silently skip folders that your user account doesn't have access to read
        return

    for item in items:
        if item.is_dir():
            # Create a stylized folder branch
            branch = tree_node.add(f"📂 [bold magenta1]{item.name}[/]")
            # Recursively descend into the subfolder
            _add_to_tree(item, branch)
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


def print_beautiful_directory(target_path: pathlib.Path):
    """Initializes the root tree node and triggers the clean printer."""
    root_path = pathlib.Path(target_path).resolve()

    root_tree = Tree(
        f"✨ [bold black on violet] {root_path.name or root_path} [/]",
        guide_style="bold bright_cyan",
    )

    _add_to_tree(root_path, root_tree)
    return root_tree
