import typer

from core.config import DOTFILES_DIR

from .backup import Backup

app = typer.Typer(help="A CLI tool to manage your dotfiles.", no_args_is_help=True)


@app.command(
    help="""Creates dotfile folder and if previous folder exists then makes it as backup then 
    creates new dotfile folder."""
)
def backup():
    backup = Backup(home_dir=DOTFILES_DIR.parent, dotfiles_dir=DOTFILES_DIR)
    if backup.old_dotfiles_exist:
        typer.echo("Existing dotfiles directory found. Creating backup...")
        backup.convert_to_backup()
        typer.echo("Backup created successfully.")
    else:
        typer.echo("No existing dotfiles directory found. Creating new one...")
        backup.make_dir()
        typer.echo("New dotfiles directory created successfully.")


@app.command(help="Restores the backup of dotfiles if it exists.")
def main():
    pass


if __name__ == "__main__":
    app()
