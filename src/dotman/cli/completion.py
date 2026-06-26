from dotman.core.config import InternalFileSystemObject, load_config


def complete_profiles(incomplete: str) -> list[str]:
    cfg = load_config()
    profiles_dir = cfg.dotfiles_dir / InternalFileSystemObject.PROFILES.value

    if not profiles_dir.exists():
        return []

    return [
        p.name
        for p in profiles_dir.iterdir()
        if p.is_dir() and p.name.startswith(incomplete)
    ]
