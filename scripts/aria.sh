#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# Lee — Management Script
# Usage: bash scripts/Lee.sh {start|stop|restart|status|logs}
# ─────────────────────────────────────────────────────────────────────────────

set -e

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ── Resolve project directory ─────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_DIR/agentEnv"
PYTHON="$VENV_DIR/bin/python"
PIDFILE="$PROJECT_DIR/data/Lee.pid"
LOG_DIR="$PROJECT_DIR/data"
SERVICE_LABEL="com.Lee.assistant"

# ── Ensure data directory exists ──────────────────────────────────────────────
mkdir -p "$LOG_DIR"

# ── Helper functions ──────────────────────────────────────────────────────────
print_header() {
    echo -e "${CYAN}${BOLD}"
    echo "  ╔════════════════════════════════════╗"
    echo "  ║     🤖 Lee Service Manager        ║"
    echo "  ╚════════════════════════════════════╝"
    echo -e "${NC}"
}

is_running() {
    if [ -f "$PIDFILE" ]; then
        local pid
        pid=$(cat "$PIDFILE" 2>/dev/null)
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            return 0
        fi
    fi
    # Also check via process name
    if pgrep -f "uvicorn.*main:app" > /dev/null 2>&1; then
        return 0
    fi
    return 1
}

get_pid() {
    if [ -f "$PIDFILE" ]; then
        local pid
        pid=$(cat "$PIDFILE" 2>/dev/null)
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo "$pid"
            return
        fi
    fi
    pgrep -f "uvicorn.*main:app" 2>/dev/null | head -1
}

# ── Commands ──────────────────────────────────────────────────────────────────
do_start() {
    print_header
    if is_running; then
        echo -e "  ${YELLOW}⚠  Lee is already running (PID: $(get_pid))${NC}"
        echo -e "  ${CYAN}   Dashboard: http://localhost:8000${NC}"
        return 0
    fi

    echo -e "  ${CYAN}Starting Lee...${NC}"

    if [ ! -f "$PYTHON" ]; then
        echo -e "  ${RED}✗ Python venv not found at: $VENV_DIR${NC}"
        echo -e "  ${YELLOW}  Run: python3 -m venv agentEnv && source agentEnv/bin/activate && pip install -r requirements.txt${NC}"
        exit 1
    fi

    # Start Lee in background
    cd "$PROJECT_DIR"
    nohup "$PYTHON" main.py > "$LOG_DIR/Lee_stdout.log" 2> "$LOG_DIR/Lee_stderr.log" &
    local pid=$!
    echo "$pid" > "$PIDFILE"

    # Wait a moment and verify
    sleep 2
    if kill -0 "$pid" 2>/dev/null; then
        echo -e "  ${GREEN}✓ Lee started successfully (PID: $pid)${NC}"
        echo -e "  ${CYAN}  Dashboard: http://localhost:8000${NC}"
        echo -e "  ${CYAN}  Logs:      $LOG_DIR/Lee_stdout.log${NC}"
    else
        echo -e "  ${RED}✗ Lee failed to start. Check logs:${NC}"
        echo -e "  ${YELLOW}  $LOG_DIR/Lee_stderr.log${NC}"
        rm -f "$PIDFILE"
        exit 1
    fi
}

do_stop() {
    print_header
    if ! is_running; then
        echo -e "  ${YELLOW}⚠  Lee is not running${NC}"
        rm -f "$PIDFILE"
        return 0
    fi

    local pid
    pid=$(get_pid)
    echo -e "  ${CYAN}Stopping Lee (PID: $pid)...${NC}"

    kill "$pid" 2>/dev/null
    sleep 2

    # Force kill if still running
    if kill -0 "$pid" 2>/dev/null; then
        kill -9 "$pid" 2>/dev/null
        sleep 1
    fi

    rm -f "$PIDFILE"
    echo -e "  ${GREEN}✓ Lee stopped${NC}"
}

do_restart() {
    do_stop
    echo ""
    do_start
}

do_status() {
    print_header
    if is_running; then
        local pid
        pid=$(get_pid)
        echo -e "  ${GREEN}● Lee is RUNNING${NC}"
        echo -e "    PID:       $pid"
        echo -e "    Dashboard: ${CYAN}http://localhost:8000${NC}"

        # Show uptime if possible
        if [ -n "$pid" ]; then
            local start_time
            start_time=$(ps -p "$pid" -o lstart= 2>/dev/null)
            if [ -n "$start_time" ]; then
                echo -e "    Started:   $start_time"
            fi
        fi

        # Show resource usage
        if [ -n "$pid" ]; then
            local mem cpu
            mem=$(ps -p "$pid" -o rss= 2>/dev/null | awk '{printf "%.1f MB", $1/1024}')
            cpu=$(ps -p "$pid" -o %cpu= 2>/dev/null)
            echo -e "    Memory:    $mem"
            echo -e "    CPU:       ${cpu}%"
        fi

        # Check launchd status
        if launchctl list "$SERVICE_LABEL" > /dev/null 2>&1; then
            echo -e "    Service:   ${GREEN}launchd managed (auto-start enabled)${NC}"
        else
            echo -e "    Service:   ${YELLOW}manual mode (no auto-start)${NC}"
        fi
    else
        echo -e "  ${RED}● Lee is STOPPED${NC}"
        if launchctl list "$SERVICE_LABEL" > /dev/null 2>&1; then
            echo -e "    Service:   ${YELLOW}launchd loaded but process not running${NC}"
        fi
    fi
    echo ""
}

do_logs() {
    print_header
    echo -e "  ${CYAN}Showing last 50 lines of logs (Ctrl+C to exit):${NC}"
    echo ""
    if [ -f "$LOG_DIR/Lee_stdout.log" ]; then
        tail -50f "$LOG_DIR/Lee_stdout.log"
    else
        echo -e "  ${YELLOW}No logs found. Has Lee been started yet?${NC}"
    fi
}

# ── Main ──────────────────────────────────────────────────────────────────────
case "${1:-}" in
    start)    do_start ;;
    stop)     do_stop ;;
    restart)  do_restart ;;
    status)   do_status ;;
    logs)     do_logs ;;
    *)
        echo -e "${BOLD}Lee — Service Manager${NC}"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "  start    — Start Lee in background"
        echo "  stop     — Stop Lee"
        echo "  restart  — Restart Lee"
        echo "  status   — Show current status and resource usage"
        echo "  logs     — Tail the log file"
        exit 1
        ;;
esac
