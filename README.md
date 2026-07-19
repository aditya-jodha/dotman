<div align="center">

# **Dotman**

```
      _       _                       
   __| | ___ | |_ _ __ ___   __ _ _ __
  / _` |/ _ \| __| '_ ` _ \ / _` | '_ \

 | (_| | (_) | |_| | | | | | (_| | | | |
  \__,_|\___/ \__|_| |_| |_|\__,_|_| |_|
```

[![CI](https://github.com/aditya-jodha/dotman/actions/workflows/ci.yml/badge.svg)](https://github.com/aditya-jodha/dotman/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/aditya-jodha/dotman/branch/main/graph/badge.svg)](https://codecov.io/gh/aditya-jodha/dotman)
[![LICENSE](https://img.shields.io/badge/license-MIT-green)](./LICENSE)
![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)

<!-- uv badge is shown here becaue this tool uses uv as its installation method -->

![CLI](https://img.shields.io/badge/CLI-yellow?logo=bilibili&logoColor=white)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

[![Discord](https://img.shields.io/badge/Discord-blue?logo=Discord&logoColor=white)](https://discord.gg/aditya_jodha)
[![Static Badge](https://img.shields.io/badge/Reddit-red?style=plastic&logo=reddit&logoColor=white)](https://www.reddit.com/user/Dry_Developer)
[![Static Badge](https://img.shields.io/badge/GitHub-black?logo=github&logoColor=white)](https://github.com/aditya-jodha)

</div>

```
     -----------------
    |                 |
    |                 |
    |                 |
    |                 |
    |                 |
 ___|             ____|___
|_________________________|
    |    _       _    |
    |   (-)     (-)   |
    \                 /
     |       ^^      |   ¨Right, let's sort your environment!¨
     \    \______/   /
      \___        __/
          \______/
```

<div align="center">

**A modern, lightweight dotfile manager written in Python.**

*Manage, organize, sync, and switch configurations seamlessly.*

</div>



https://github.com/user-attachments/assets/e07f0579-8d2d-42e5-bc16-0a537472da9c


## Why Dotman

Managing dotfiles across multiple machines quickly becomes messy.

Dotman provides a predictable workflow for organizing configuration
files, previewing changes before they happen, synchronizing symlinks,
and switching between multiple profiles safely.

______________________________________________________________________

## ✨ Features

- **Multiple Profiles**: Manage separate configurations seamlessly.
- **Automatic Symlink Management**: Handles path linking without manual intervention.
- **Safe Rollback**: Revert changes safely if things go wrong.
- **Package Organization**: Keep everything structured and neat.
- **Doctor Diagnostics**: Instantly troubleshoot environmental errors.
- **Rich CLI Output**: Beautiful, readable terminal interfaces.
- **JSON Output for Automation**: Parse and pipe data into other scripts effortlessly.
- **Strongly Typed Configuration**: Validated out-of-the-box via Pydantic models.

---

🧪 **190+ Tests Passing**

---

# Installation

## Using `uv` (Recommended)

Install `uv` (if you don't already have it):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Run Dotman instantly without installing:

```bash
uvx --from git+https://github.com/aditya-jodha/dotman.git dotman --help
```

Or install it globally:

```bash
uv tool install git+https://github.com/aditya-jodha/dotman.git
```

Verify the installation:

```bash
dotman --help
```

## From Source

```bash
git clone https://github.com/aditya-jodha/dotman.git
cd dotman
uv sync
uv run dotman --help
```

______________________________________________________________________

### Safe File Addition

Add existing configuration files into Dotman's managed storage.

Dotman:

- Preserves directory structure
- Creates packages automatically
- Shows a preview before committing
- Allows rollback before finalizing changes

______________________________________________________________________

### Sync Command

Sync managed dotfiles back into your home directory.

```bash
dotman sync
```

Dotman automatically creates symlinks from your managed files to their correct locations.

______________________________________________________________________

### Doctor Command

Diagnose broken or incorrect symlinks.

Checks include:

- Missing targets
- Broken symlinks
- Incorrect symlink destinations
- Non-symlink files where symlinks are expected

______________________________________________________________________

### Automatic Backups

> When conflicts occur, Dotman can safely move existing files into a backup location before linking. (This still needs to make it more robust)

______________________________________________________________________

### Tested

Current test suite includes:

- Add command tests
- Doctor tests
- Linker tests
- Unlinker tests
- Profile management tests

```bash
uv run pytest
```

Current status:

```text
191 passed in 1.49s
```

______________________________________________________________________

## Quick Start

### Initialize Dotman

```bash
dotman init
```

### Add a Configuration

```bash
dotman add ~/.bash_profile --package bash
```

### Sync Files

```bash
dotman sync
```

### Run Diagnostics

```bash
dotman doctor
```

______________________________________________________________________

## How dotman Works

Read the [Architecture.md](ARCHITECTURE.md) for a detailed explanation of the internal workings of Dotman.

______________________________________________________________________

## Example Workflow

Create a profile:

```bash
dotman profile create work
```

Switch to it:

```bash
dotman profile use work
```

Add files:

```bash
dotman add ~/.bash_profile --package bash
dotman add ~/.config/.tmux --package tmux
```

Sync:

```bash
dotman sync
```

Verify:

```bash
dotman doctor
```

______________________________________________________________________

## Commands

| Command                 | Description             |
| ----------------------- | ----------------------- |
| `dotman init`           | Initialize Dotman       |
| `dotman add`            | Add a file or directory |
| `dotman sync`           | Create symlinks         |
| `dotman doctor`         | Verify symlink health   |
| `dotman profile create` | Create profile          |
| `dotman profile use`    | Switch profile          |
| `dotman profile delete` | Delete profile          |
| `dotman profile list`   | List profiles           |

______________________________________________________________________

## Architecture

For better understanding of the architecture, please refer to [Architecture.md](https://github.com/aditya-jodha/dotman/blob/main/ARCHITECTURE.md)

## How to change the dotfiles folder name

______________________________________________________________________

User can change the dotfiles folder name by editing the `config.py` file or leave this task to dotman by using the `dotman config` command.

When a user updates the configuration via the dotman config command, dotman automatically validates the input keys and data.
- Valid input: dotman updates the configuration file with the new data.
- Invalid input: dotman rejects the changes, aborts the update, and displays a detailed error message.

> [!CAUTION] 
> If user modifies the configuration file manually, dotman will  validate the changes at runtime and may lead to unexpected behavior in some commands.

## Roadmap

### Completed

- [x] Dotfile management
- [x] Sync command
- [x] Doctor command
- [x] Profile management
- [x] Profile switching
- [x] Automated testing
- [x] Package removal command
- [x] Configuration file support

### Planned

- [ ] Package management
- [ ] Plugin system
- [ ] Profile export/import
- [ ] Dry-run mode improvements
- [ ] Windows support

______________________________________________________________________

<div>
    <div align="Right">
    𝕯𝖔𝖙𝖒𝖆𝖓
    </div>
    <div align="center">
    <img src="https://img.shields.io/badge/_MADE_BY_-ADITYA-blue.svg" alt="Made by Aditya">
    </div>
</div>