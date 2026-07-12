from dotman.core.config.config import DotmanConfig, InternalFileSystemObject


def complete_profiles(incomplete: str) -> list[str]:
    cfg = DotmanConfig.load()
    profiles_dir = cfg.dotfiles_dir / InternalFileSystemObject.PROFILES.value

    if not profiles_dir.exists():
        return []

    return [p.name for p in profiles_dir.iterdir() if p.is_dir() and p.name.startswith(incomplete)]
