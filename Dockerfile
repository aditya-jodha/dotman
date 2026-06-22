FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    eza \
    file \
    git \
    zsh \
    && rm -rf /var/lib/apt/lists/*

# Install Starship as root
RUN curl -sS https://starship.rs/install.sh | sh -s -- -y

# Create test user
RUN useradd -m -s /bin/zsh tester

USER tester
WORKDIR /home/tester

ENV PATH="/home/tester/.local/bin:${PATH}"

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Prevent zsh first-run wizard and enable starship
RUN echo 'eval "$(starship init zsh)"' > ~/.zshrc

# Add convenient development alias
RUN echo "alias tree='eza --tree --icons -I \"__pycache__|*.pyc|*.pyo|*pytest_cache*|.git|node_modules|env|.pytest_cache|.cache|.local|dotman\"'" >> ~/.zshrc

# Sanity checks
RUN starship --version
RUN uv --version

CMD ["/bin/zsh", "-l"]
