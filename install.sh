#!/usr/bin/env bash

set -euo pipefail

REPO="aditya-jodha/dotman"
INSTALL_DIR="${HOME}/.local/bin"
BINARY_NAME="dotman"

TEMP_FILE=""

# ============================================================
# Utilities
# ============================================================

log() {
    printf '==> %s\n' "$*"
}

error() {
    printf 'error: %s\n' "$*" >&2
    exit 1
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

cleanup() {
    if [[ -n "${TEMP_FILE:-}" ]]; then
        rm -f "$TEMP_FILE"
    fi
}

download() {
    local url="$1"
    local output="$2"

    if command_exists curl; then
        curl \
            --proto '=https' \
            --tlsv1.2 \
            --fail \
            --location \
            --silent \
            --show-error \
            "$url" \
            --output "$output"

    elif command_exists wget; then
        wget \
            --https-only \
            --output-document="$output" \
            "$url"

    else
        error "curl or wget is required to download files"
    fi
}

download_to_stdout() {
    local url="$1"

    if command_exists curl; then
        curl \
            --proto '=https' \
            --tlsv1.2 \
            --fail \
            --location \
            --silent \
            --show-error \
            "$url"

    elif command_exists wget; then
        wget \
            --https-only \
            --quiet \
            --output-document=- \
            "$url"

    else
        error "curl or wget is required to download files"
    fi
}

ask_yes_no() {
    local question="$1"
    local response

    if [[ "${ASSUME_YES:-}" == "1" ]]; then
        return 0
    fi

    while true; do
        printf '%s (y/n): ' "$question"
        read -r response

        case "$response" in
            [Yy]|[Yy][Ee][Ss])
                return 0
                ;;

            [Nn]|[Nn][Oo])
                return 1
                ;;

            *)
                printf "Please answer 'y' or 'n'.\n"
                ;;
        esac
    done
}

# ============================================================
# Platform detection
# ============================================================

detect_binary() {
    local os
    local arch

    os="$(uname -s)"
    arch="$(uname -m)"

    case "$os-$arch" in
        Darwin-arm64)
            BINARY="${BINARY_NAME}-darwin-arm64"
            ;;

        Darwin-x86_64)
            BINARY="${BINARY_NAME}-darwin-x86_64"
            ;;

        Linux-aarch64|Linux-arm64)
            BINARY="${BINARY_NAME}-linux-arm64"
            ;;

        Linux-x86_64|Linux-amd64)
            BINARY="${BINARY_NAME}-linux-x86_64"
            ;;

        *)
            error "unsupported platform: $os $arch"
            ;;
    esac

    log "Detected platform: $os $arch"
    log "Binary: $BINARY"
}

# ============================================================
# Checksum verification
# ============================================================

verify_checksum() {
    local file="$1"
    local checksum_url="$2"

    local expected
    local actual

    if command_exists sha256sum; then
        actual="$(sha256sum "$file" | awk '{print $1}')"

    elif command_exists shasum; then
        actual="$(shasum -a 256 "$file" | awk '{print $1}')"

    else
        log "No SHA-256 utility found; skipping checksum verification."
        return 0
    fi

    log "Verifying checksum..."

    expected="$(
        download_to_stdout "$checksum_url" |
            awk -v binary="$BINARY" '$2 == binary { print $1 }'
    )"

    if [[ -z "$expected" ]]; then
        error "Failed to retrieve checksum for ${BINARY}"
    fi

    if [[ "$expected" != "$actual" ]]; then
        error "Checksum verification failed"
    fi

    log "Checksum OK."
}

# ============================================================
# PATH configuration
# ============================================================

path_contains_install_dir() {
    case ":${PATH}:" in
        *":${INSTALL_DIR}:"*)
            return 0
            ;;

        *)
            return 1
            ;;
    esac
}

add_path_to_file() {
    local file="$1"
    local path_line="export PATH=\"${INSTALL_DIR}:\$PATH\""

    touch "$file"

    if ! grep -Fqx "$path_line" "$file"; then
        printf '\n%s\n' "$path_line" >> "$file"
        log "Added ${INSTALL_DIR} to PATH in ${file}"
    fi
}

configure_path() {
    local shell_name

    shell_name="$(basename "${SHELL:-}")"

    case "$shell_name" in
        bash)
            add_path_to_file "$HOME/.bashrc"
            ;;

        zsh)
            add_path_to_file "$HOME/.zshrc"
            ;;

        *)
            log "Could not automatically configure PATH for ${shell_name:-unknown}."
            log "Add ${INSTALL_DIR} to your PATH manually."
            ;;
    esac
}

check_path() {
    if path_contains_install_dir; then
        return
    fi

    log "${INSTALL_DIR} is not currently in your PATH."

    if ask_yes_no "Would you like to add it to your PATH?"; then
        configure_path
    fi
}

# ============================================================
# Installation
# ============================================================

install_binary() {
    local download_url
    local checksum_url

    mkdir -p "$INSTALL_DIR"

    if [[ ! -w "$INSTALL_DIR" ]]; then
        error "Cannot write to ${INSTALL_DIR}. Check its permissions."
    fi

    download_url="https://github.com/${REPO}/releases/latest/download/${BINARY}"
    checksum_url="https://github.com/${REPO}/releases/latest/download/checksums.sha256"

    TEMP_FILE="$(mktemp)"

    log "Downloading ${BINARY}..."

    download "$download_url" "$TEMP_FILE"

    verify_checksum "$TEMP_FILE" "$checksum_url"

    if [[ -e "${INSTALL_DIR}/${BINARY_NAME}" ]]; then
        if ! ask_yes_no "dotman is already installed. Overwrite it?"; then
            log "Keeping existing installation."
            exit 0
        fi

        log "Replacing existing installation..."
    fi

    mv "$TEMP_FILE" "${INSTALL_DIR}/${BINARY_NAME}"

    # The temporary file has been moved successfully.
    TEMP_FILE=""

    chmod +x "${INSTALL_DIR}/${BINARY_NAME}"
}

# ============================================================
# Main
# ============================================================

main() {
    detect_binary
    install_binary
    check_path

    echo
    log "dotman installed successfully!"
    echo
    echo "Run:"
    echo "  dotman --help"
}

trap cleanup EXIT

main "$@"