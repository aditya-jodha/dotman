#!/usr/bin/env bash

set -euo pipefail

REPO="aditya-jodha/dotman"
INSTALL_DIR="${HOME}/.local/bin"
BINARY_NAME="dotman"

TEMP_DIR=""
TEMP_FILE=""
BINARY=""
UI_MODE="native"

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
    if [[ -n "${TEMP_DIR:-}" && -d "$TEMP_DIR" ]]; then
        rm -rf "$TEMP_DIR"
    fi
}

# ============================================================
# Terminal UI & Colors
# ============================================================

setup_terminal() {
    if [[ -t 1 ]]; then
        INTERACTIVE=1
        RESET='\033[0m'
        BOLD='\033[1m'
        DIM='\033[2m'
        GREEN='\033[32m'
        RED='\033[31m'
        CYAN='\033[36m'
        YELLOW='\033[33m'
    else
        INTERACTIVE=0
        RESET=''
        BOLD=''
        DIM=''
        GREEN=''
        RED=''
        CYAN=''
        YELLOW=''
    fi
}

setup_ui() {
    UI_MODE="native"

    if command_exists gum; then
        UI_MODE="gum"
    elif command_exists whiptail; then
        UI_MODE="whiptail"
    elif command_exists dialog; then
        UI_MODE="dialog"
    fi
}

# ============================================================
# UI Rendering
# ============================================================

ui_header() {
    case "$UI_MODE" in
        gum)
            gum style \
                --border double \
                --padding "1 2" \
                --margin "1" \
                "dotman installer"
            ;;
        *)
            printf '\n==================== dotman installer ====================\n\n'
            ;;
    esac
}

ui_log() {
    case "$UI_MODE" in
        gum)
            gum log --level info "$*"
            ;;
        *)
            printf "${CYAN}==>${RESET} %s\n" "$*"
            ;;
    esac
}

ui_success() {
    case "$UI_MODE" in
        gum)
            gum style --foreground 2 "✓ $*"
            ;;
        *)
            printf "${GREEN}✓ %s${RESET}\n" "$*"
            ;;
    esac
}

ui_error() {
    case "$UI_MODE" in
        gum)
            gum style --foreground 1 "✗ $*"
            ;;
        *)
            printf "${RED}✗ %s${RESET}\n" "$*" >&2
            ;;
    esac
}

# ============================================================
# Input
# ============================================================

ask_yes_no_native() {
    local question="$1"
    local response

    while true; do
        printf '%s (y/n): ' "$question"
        read -r response

        case "$response" in
            [Yy]|[Yy][Ee][Ss]) return 0 ;;
            [Nn]|[Nn][Oo])     return 1 ;;
            *) printf "Please answer 'y' or 'n'.\n" ;;
        esac
    done
}

ui_confirm() {
    local question="$1"

    # Crucial Fix: Bypass UI entirely if automated CI flag is set
    if [[ "${ASSUME_YES:-}" == "1" ]]; then
        return 0
    fi

    case "$UI_MODE" in
        gum)
            gum confirm "$question"
            ;;
        whiptail)
            whiptail --title "dotman Installer" --yesno "$question" 10 60
            ;;
        dialog)
            dialog --title "dotman Installer" --yesno "$question" 10 60
            ;;
        *)
            ask_yes_no_native "$question"
            ;;
    esac
}

# ============================================================
# Download
# ============================================================

download() {
    local url="$1"
    local output="$2"

    if command_exists curl; then
        curl --proto '=https' --tlsv1.2 --fail --location --silent --show-error "$url" --output "$output"
    elif command_exists wget; then
        wget --https-only --output-document="$output" "$url"
    else
        error "curl or wget is required to download files"
    fi
}

download_to_stdout() {
    local url="$1"

    if command_exists curl; then
        curl --proto '=https' --tlsv1.2 --fail --location --silent --show-error "$url"
    elif command_exists wget; then
        wget --https-only --quiet --output-document=- "$url"
    else
        error "curl or wget is required to download files"
    fi
}

# ============================================================
# Platform Detection & Checksums
# ============================================================

detect_binary() {
    local os arch
    os="$(uname -s)"
    arch="$(uname -m)"

    case "$os-$arch" in
        Darwin-arm64)              BINARY="${BINARY_NAME}-darwin-arm64" ;;
        Darwin-x86_64)             BINARY="${BINARY_NAME}-darwin-x86_64" ;;
        Linux-aarch64|Linux-arm64) BINARY="${BINARY_NAME}-linux-arm64" ;;
        Linux-x86_64|Linux-amd64)  BINARY="${BINARY_NAME}-linux-x86_64" ;;
        *) error "unsupported platform: $os $arch" ;;
    esac

    ui_log "Detected platform: $os $arch"
    ui_log "Binary: $BINARY"
}

verify_checksum() {
    local file="$1"
    local checksum_url="$2"
    local expected actual

    if command_exists sha256sum; then
        actual="$(sha256sum "$file" | awk '{print $1}')"
    elif command_exists shasum; then
        actual="$(shasum -a 256 "$file" | awk '{print $1}')"
    else
        ui_log "No SHA-256 utility found; skipping checksum verification."
        return 0
    fi

    ui_log "Verifying checksum..."
    expected="$(download_to_stdout "$checksum_url" | awk -v binary="$BINARY" '$2 == binary { print $1 }')"

    if [[ -z "$expected" ]]; then
        error "Failed to retrieve checksum for ${BINARY}"
    fi

    if [[ "$expected" != "$actual" ]]; then
        error "Checksum verification failed"
    fi

    ui_success "Checksum verified"
}

# ============================================================
# PATH Configuration
# ============================================================

path_contains_install_dir() {
    case ":${PATH}:" in
        *":${INSTALL_DIR}:"*) return 0 ;;
        *) return 1 ;;
    esac
}

add_path_to_file() {
    local file="$1"
    local path_line="export PATH=\"${INSTALL_DIR}:\$PATH\""
    touch "$file"
    if ! grep -Fqx "$path_line" "$file"; then
        printf '\n%s\n' "$path_line" >> "$file"
        ui_log "Added ${INSTALL_DIR} to PATH in ${file}"
    fi
}

configure_path() {
    local shell_name
    shell_name="$(basename "${SHELL:-}")"

    case "$shell_name" in
        bash) add_path_to_file "$HOME/.bashrc" ;;
        zsh)  add_path_to_file "$HOME/.zshrc" ;;
        *)
            ui_log "Could not automatically configure PATH for ${shell_name:-unknown}."
            ui_log "Add ${INSTALL_DIR} to your PATH manually."
            ;;
    esac
}

check_path() {
    if path_contains_install_dir; then return; fi

    ui_log "${INSTALL_DIR} is not currently in your PATH."
    if ui_confirm "Would you like to add it to your PATH?"; then
        configure_path
    fi
}

# ============================================================
# Installation
# ============================================================

install_binary() {
    local download_url checksum_url

    mkdir -p "$INSTALL_DIR"
    if [[ ! -w "$INSTALL_DIR" ]]; then
        error "Cannot write to ${INSTALL_DIR}. Check its permissions."
    fi

    download_url="https://github.com/${REPO}/releases/latest/download/${BINARY}"
    checksum_url="https://github.com/${REPO}/releases/latest/download/checksums.sha256"

    TEMP_DIR="$(mktemp -d)"
    TEMP_FILE="${TEMP_DIR}/${BINARY}"

    ui_log "Downloading ${BINARY}..."
    download "$download_url" "$TEMP_FILE"
    ui_success "Download complete"

    verify_checksum "$TEMP_FILE" "$checksum_url"

    if [[ -e "${INSTALL_DIR}/${BINARY_NAME}" ]]; then
        if ! ui_confirm "dotman is already installed. Overwrite it?"; then
            ui_log "Keeping existing installation."
            exit 0
        fi
        ui_log "Replacing existing installation..."
    fi

    mv "$TEMP_FILE" "${INSTALL_DIR}/${BINARY_NAME}"
    TEMP_FILE=""
    chmod +x "${INSTALL_DIR}/${BINARY_NAME}"
    ui_success "Installed ${INSTALL_DIR}/${BINARY_NAME}"
}

# ============================================================
# Main
# ============================================================

main() {
    setup_terminal
    setup_ui
    ui_header

    detect_binary
    install_binary
    check_path

    printf '\n'
    ui_success "dotman installed successfully!"
    printf '\nRun:\n  dotman --help\n\n'
}

trap cleanup EXIT
main "$@"