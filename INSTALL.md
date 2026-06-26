## Installation

### Install from **`uv`** package manager (Recommended):

- Install `uv` from [Astral Shell](https://astral.sh/uv)

  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

- Run Dotman instantly with **uvx** (no local install required):

  ```bash
  uvx --from git+https://github.com/aditya-jodha/dotman.git dotman --help
  ```

- If you prefer to install it globally to your environment:

  ```bash
  uv tool install git+https://github.com/aditya-jodha/dotman.git
  dotman --help
  ```

### Install from source (Traditional):

```bash
git clone https://github.com/your-username/dotman.git
cd dotman
```

Install dependencies:

```bash
uv sync
```

Run:

```bash
uv run dotman --help
```