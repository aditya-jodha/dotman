from pathlib import Path

import typer

from dotman.core.config import load_config

app = typer.Typer(help="A CLI tool to manage your dotfiles.", no_args_is_help=True)


@app.command(
    help="Creates dotfile folder and if previous folder exists then makes it as backup then creates new dotfile folder."
)
def init():
    from dotman.cli.app.init import init  # noqa: PLC0415

    init()


@app.command(help="Sync dotfiles package links to the home directory.")
def sync(
    package_name: str | None = typer.Option(
        None, "--package", help="Sync only this package. Syncs all packages by default."
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be linked without changing files."),
):
    from dotman.cli.app.sync import sync  # noqa: PLC0415

    sync(package_name=package_name, dry_run=dry_run)


@app.command(help="Give a full diagnostic report.")
def doctor(detail: bool = typer.Option(False, "-a", "--all", help="Show detailed information.")):
    from dotman.cli.app.doctor import doctor  # noqa: PLC0415

    doctor(detail=detail)


@app.command(help="Add a file to a package.")
def add(
    file: Path,
    package_name: str | None = typer.Option(None, "--package", help="The package name to which the file belongs."),
):
    from dotman.cli.app.add import add  # noqa: PLC0415

    add(file=file, package_name=package_name)


# ================================================================
# Sandbox command
# ================================================================


@app.command(hidden=True)
def sandbox():
    """This command creates a fresh testing setup."""
    cgf = load_config()
    home_dir = cgf.home_dir
    dotfiles_dir = cgf.dotfiles_dir

    print(cgf.as_dict())

    items = list(home_dir.rglob("*"))
    if items:
        print("home directory is not empty")
        return

    def make_home():
        home_dir.mkdir(exist_ok=True)

        (home_dir / ".bashrc").touch()
        (home_dir / ".bash_profile").touch()
        (home_dir / ".zshrc").touch()
        (home_dir / ".gitconfig").touch()
        (home_dir / ".gitignore").touch()

        (home_dir / ".config").mkdir(exist_ok=False)
        (home_dir / ".config" / "nvim").mkdir(exist_ok=False)
        (home_dir / ".config" / "nvim" / "init.vim").touch()

        (home_dir / ".config" / ".tmux").mkdir(exist_ok=False)
        (home_dir / ".config" / ".tmux" / "tmux.conf").touch()

    def make_dotfile():
        (dotfiles_dir / "zsh").mkdir(exist_ok=True)
        (dotfiles_dir / "zsh" / ".zshrc").touch()

        (dotfiles_dir / "bash").mkdir(exist_ok=False)
        (dotfiles_dir / "bash" / ".bashrc").touch()
        (dotfiles_dir / "bash" / ".bash_profile").touch()

        (dotfiles_dir / "git").mkdir(exist_ok=False)
        (dotfiles_dir / "git" / ".gitconfig").touch()
        (dotfiles_dir / "git" / ".gitignore").touch()

        (dotfiles_dir / "nvim").mkdir(exist_ok=False)
        (dotfiles_dir / "nvim" / ".config").mkdir(exist_ok=False)
        (dotfiles_dir / "nvim" / ".config" / "nvim").mkdir(exist_ok=False)
        (dotfiles_dir / "nvim" / ".config" / "nvim" / "init.vim").touch()

        (dotfiles_dir / "tmux").mkdir(exist_ok=False)
        (dotfiles_dir / "tmux" / ".config").mkdir(exist_ok=False)
        (dotfiles_dir / "tmux" / ".config" / "tmux").mkdir(exist_ok=False)
        (dotfiles_dir / "tmux" / ".config" / "tmux" / ".tmux.conf").touch()

    # Testing structure:
    choice = input("Press 1 for creating dotfiles_dir, 2 for home_dir & 3 for both: ")
    if choice == "1":
        make_dotfile()
    elif choice == "2":
        make_home()
    else:
        make_dotfile()
        make_home()
