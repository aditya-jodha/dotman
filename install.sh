#!/usr/bin/env bash

set -euo pipefail


# Getting the Architecture
OS="$(uname -s)"
ARCH="$(uname -m)"

case "$OS-$ARCH" in
    Darwin-arm64)
        BINARY="dotman-darwin-arm64"
        ;;
    Darwin-x86_64)
        BINARY="dotman-darwin-x86_64"
        ;;
    Linux-aarch64|Linux-arm64)
        BINARY="dotman-linux-arm64"
        ;;
    Linux-x86_64|Linux-amd64)
        BINARY="dotman-linux-x86_64"
        ;;
    *)
        echo "Unsupported platform: $OS $ARCH"
        exit 1
        ;;
esac

echo "Detected platform: $OS $ARCH"
echo "Binary: $BINARY"


INSTALL_DIR="$HOME/.local/bin"

mkdir -p "$INSTALL_DIR"

echo "Installing to: $INSTALL_DIR"

# Create install directory
mkdir -p "$INSTALL_DIR"

# Download binary
curl -fsSL \
    "https://github.com/aditya-jodha/dotman/releases/download/$VERSION/$BINARY" \
    -o "$INSTALL_DIR/dotman"

# Make executable
chmod +x "$INSTALL_DIR/dotman"

echo "dotman installed successfully!"
