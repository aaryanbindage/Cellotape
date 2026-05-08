#!/bin/bash
# EasyPush installer for macOS
set -e

CYAN='\033[36m'
GREEN='\033[32m'
YELLOW='\033[33m'
RED='\033[31m'
BOLD='\033[1m'
R='\033[0m'

echo ""
echo -e "${CYAN}${BOLD}  EasyPush Installer — macOS${R}"
echo -e "${CYAN}  ──────────────────────────────${R}"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}✗ Python 3 not found.${R}"
    echo "  Install from: https://python.org"
    exit 1
fi
PYTHON=$(command -v python3)
echo -e "  ${GREEN}✓${R} Python: $($PYTHON --version)"

# Check Git
if ! command -v git &>/dev/null; then
    echo -e "${YELLOW}⚠ Git not found. Install with: xcode-select --install${R}"
fi

# Install dependencies
echo ""
echo -e "  Installing dependencies…"
$PYTHON -m pip install --upgrade pip --quiet
$PYTHON -m pip install customtkinter --quiet
echo -e "  ${GREEN}✓${R} customtkinter installed"

# Install CLI globally
INSTALL_DIR="$HOME/.local/bin"
mkdir -p "$INSTALL_DIR"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create launcher script
cat > "$INSTALL_DIR/easypush" << EOF
#!/bin/bash
$PYTHON "$SCRIPT_DIR/easypush_cli.py" "\$@"
EOF
chmod +x "$INSTALL_DIR/easypush"

# Create GUI launcher
cat > "$INSTALL_DIR/easypush-gui" << EOF
#!/bin/bash
$PYTHON "$SCRIPT_DIR/easypush.py" &
EOF
chmod +x "$INSTALL_DIR/easypush-gui"

echo -e "  ${GREEN}✓${R} CLI installed to $INSTALL_DIR/easypush"

# Add to PATH if needed
SHELL_RC=""
if [[ "$SHELL" == *"zsh"* ]]; then
    SHELL_RC="$HOME/.zshrc"
elif [[ "$SHELL" == *"bash"* ]]; then
    SHELL_RC="$HOME/.bashrc"
fi

if [[ -n "$SHELL_RC" ]] && ! grep -q "$INSTALL_DIR" "$SHELL_RC" 2>/dev/null; then
    echo "" >> "$SHELL_RC"
    echo "export PATH=\"$INSTALL_DIR:\$PATH\"" >> "$SHELL_RC"
    echo -e "  ${GREEN}✓${R} Added to PATH in $SHELL_RC"
fi

# Create macOS .app wrapper
APP_DIR="$HOME/Applications/EasyPush.app/Contents/MacOS"
mkdir -p "$APP_DIR"
cat > "$APP_DIR/EasyPush" << EOF
#!/bin/bash
$PYTHON "$SCRIPT_DIR/easypush.py"
EOF
chmod +x "$APP_DIR/EasyPush"

PLIST="$HOME/Applications/EasyPush.app/Contents/Info.plist"
cat > "$PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key><string>EasyPush</string>
    <key>CFBundleExecutable</key><string>EasyPush</string>
    <key>CFBundleIdentifier</key><string>com.easypush.app</string>
    <key>CFBundleVersion</key><string>1.0</string>
    <key>CFBundlePackageType</key><string>APPL</string>
</dict>
</plist>
EOF

echo -e "  ${GREEN}✓${R} App created at ~/Applications/EasyPush.app"

echo ""
echo -e "${GREEN}${BOLD}  ✓ Installation complete!${R}"
echo ""
echo -e "  ${BOLD}Launch GUI:${R}  open ~/Applications/EasyPush.app"
echo -e "  ${BOLD}CLI usage:${R}   restart your terminal, then type: easypush"
echo -e "  ${BOLD}First run:${R}   easypush config"
echo ""
