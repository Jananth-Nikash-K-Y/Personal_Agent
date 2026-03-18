#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# Lee — launchd Service Installer
# Usage:
#   bash scripts/install_service.sh            # Install & start the service
#   bash scripts/install_service.sh --uninstall # Remove the service
# ─────────────────────────────────────────────────────────────────────────────

set -e

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_PYTHON="$PROJECT_DIR/agentEnv/bin/python"
SERVICE_LABEL="com.Lee.assistant"
PLIST_NAME="$SERVICE_LABEL.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/$PLIST_NAME"
LOG_DIR="$PROJECT_DIR/data"

# ── Ensure directories ───────────────────────────────────────────────────────
mkdir -p "$LOG_DIR"
mkdir -p "$HOME/Library/LaunchAgents"

# ── Functions ─────────────────────────────────────────────────────────────────
print_header() {
    echo -e "${CYAN}${BOLD}"
    echo "  ╔════════════════════════════════════╗"
    echo "  ║   🤖 Lee Service Installer        ║"
    echo "  ╚════════════════════════════════════╝"
    echo -e "${NC}"
}

do_install() {
    print_header

    # Pre-flight checks
    if [ ! -f "$VENV_PYTHON" ]; then
        echo -e "  ${RED}✗ Python venv not found at: $VENV_PYTHON${NC}"
        echo -e "  ${YELLOW}  Please set up the environment first:${NC}"
        echo -e "  ${YELLOW}  python3 -m venv agentEnv && source agentEnv/bin/activate && pip install -r requirements.txt${NC}"
        exit 1
    fi

    if [ ! -f "$PROJECT_DIR/main.py" ]; then
        echo -e "  ${RED}✗ main.py not found in $PROJECT_DIR${NC}"
        exit 1
    fi

    # Stop any existing manual process
    if pgrep -f "uvicorn.*main:app" > /dev/null 2>&1; then
        echo -e "  ${YELLOW}⚠  Found a running Lee process. Stopping it...${NC}"
        pkill -f "uvicorn.*main:app" 2>/dev/null || true
        sleep 2
        echo -e "  ${GREEN}✓ Existing process stopped${NC}"
    fi

    # Unload existing service if present
    if launchctl list "$SERVICE_LABEL" > /dev/null 2>&1; then
        echo -e "  ${YELLOW}⚠  Existing service found. Unloading...${NC}"
        launchctl unload "$PLIST_DEST" 2>/dev/null || true
        sleep 1
    fi

    # Generate the plist file
    echo -e "  ${CYAN}Generating launchd configuration...${NC}"
    cat > "$PLIST_DEST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${SERVICE_LABEL}</string>

    <key>ProgramArguments</key>
    <array>
        <string>${VENV_PYTHON}</string>
        <string>${PROJECT_DIR}/main.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>${PROJECT_DIR}</string>

    <key>EnvironmentVLeebles</key>
    <dict>
        <key>PATH</key>
        <string>${PROJECT_DIR}/agentEnv/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>

    <key>ThrottleInterval</key>
    <integer>10</integer>

    <key>StandardOutPath</key>
    <string>${LOG_DIR}/Lee_stdout.log</string>

    <key>StandardErrorPath</key>
    <string>${LOG_DIR}/Lee_stderr.log</string>

    <key>ProcessType</key>
    <string>Background</string>
</dict>
</plist>
EOF

    echo -e "  ${GREEN}✓ Plist created at: $PLIST_DEST${NC}"

    # Load the service
    echo -e "  ${CYAN}Loading service...${NC}"
    launchctl load "$PLIST_DEST"
    sleep 3

    # Verify
    if launchctl list "$SERVICE_LABEL" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓ Service loaded successfully!${NC}"
    else
        echo -e "  ${RED}✗ Service failed to load${NC}"
        exit 1
    fi

    # Check if Lee is actually running
    sleep 2
    if pgrep -f "uvicorn.*main:app" > /dev/null 2>&1 || curl -s http://localhost:8000 > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓ Lee is running!${NC}"
    else
        echo -e "  ${YELLOW}⚠  Service loaded but Lee may still be starting up...${NC}"
        echo -e "  ${YELLOW}   Check logs: tail -f $LOG_DIR/Lee_stderr.log${NC}"
    fi

    echo ""
    echo -e "  ${BOLD}${GREEN}═══════════════════════════════════════${NC}"
    echo -e "  ${BOLD}  ✅ Lee is now a 24/7 service!${NC}"
    echo -e "  ${BOLD}${GREEN}═══════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${CYAN}Dashboard:${NC}    http://localhost:8000"
    echo -e "  ${CYAN}Auto-start:${NC}   Enabled (runs on login)"
    echo -e "  ${CYAN}Auto-restart:${NC} Enabled (restarts on crash)"
    echo -e "  ${CYAN}Logs:${NC}         $LOG_DIR/Lee_stdout.log"
    echo -e "  ${CYAN}Manage:${NC}       bash scripts/Lee.sh {start|stop|restart|status|logs}"
    echo -e "  ${CYAN}Uninstall:${NC}    bash scripts/install_service.sh --uninstall"
    echo ""
}

do_uninstall() {
    print_header
    echo -e "  ${CYAN}Uninstalling Lee service...${NC}"

    # Unload service
    if launchctl list "$SERVICE_LABEL" > /dev/null 2>&1; then
        launchctl unload "$PLIST_DEST" 2>/dev/null || true
        echo -e "  ${GREEN}✓ Service unloaded${NC}"
    else
        echo -e "  ${YELLOW}⚠  Service was not loaded${NC}"
    fi

    # Remove plist file
    if [ -f "$PLIST_DEST" ]; then
        rm -f "$PLIST_DEST"
        echo -e "  ${GREEN}✓ Plist removed from $PLIST_DEST${NC}"
    fi

    # Stop any running processes
    if pgrep -f "uvicorn.*main:app" > /dev/null 2>&1; then
        pkill -f "uvicorn.*main:app" 2>/dev/null || true
        echo -e "  ${GREEN}✓ Lee process stopped${NC}"
    fi

    echo ""
    echo -e "  ${GREEN}✓ Lee service uninstalled.${NC}"
    echo -e "  ${CYAN}  You can still run Lee manually with: python main.py${NC}"
    echo ""
}

# ── Main ──────────────────────────────────────────────────────────────────────
case "${1:-}" in
    --uninstall|-u)
        do_uninstall
        ;;
    *)
        do_install
        ;;
esac
