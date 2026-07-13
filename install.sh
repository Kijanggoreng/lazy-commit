#!/bin/bash
set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing lazy-commit..."
echo "  Repo: $REPO_DIR"

# find python
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        PYTHON="$cmd"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "ERROR: Python not found. Install python3 first."
    exit 1
fi

echo "  Python: $PYTHON"

# find main script
PY_FILE=""
for f in "$REPO_DIR"/*.py; do
    [ -f "$f" ] && PY_FILE="$f" && break
done

if [ -z "$PY_FILE" ]; then
    echo "ERROR: No *.py file found in $REPO_DIR"
    exit 1
fi

PY_BASENAME="$(basename "$PY_FILE")"
NAME="${PY_BASENAME%.py}"
[ -z "$NAME" ] && NAME="lazy_commit"

SERVICE_NAME="${NAME}.service"
TIMER_NAME="${NAME}.timer"

echo "  Script: $PY_BASENAME"

# ensure runtime dirs exist
mkdir -p "$REPO_DIR/issues/open" "$REPO_DIR/issues/closed"

# check git config
if ! git -C "$REPO_DIR" config user.name &>/dev/null || ! git -C "$REPO_DIR" config user.email &>/dev/null; then
    echo ""
    echo "WARNING: Git user.name or user.email not set in this repo."
    echo "  git config user.name \"Your Name\""
    echo "  git config user.email \"you@example.com\""
fi

# check remote
if ! git -C "$REPO_DIR" remote &>/dev/null || [ -z "$(git -C "$REPO_DIR" remote)" ]; then
    echo ""
    echo "WARNING: No git remote configured."
    echo "  git remote add origin https://github.com/YOURNAME/YOURREPO.git"
fi

# systemd user service (no root needed)
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
mkdir -p "$SYSTEMD_USER_DIR"

cat > "$SYSTEMD_USER_DIR/$SERVICE_NAME" <<EOF
[Unit]
Description=Lazy Commit Activity Tracker
After=network.target

[Service]
Type=oneshot
WorkingDirectory=$REPO_DIR
ExecStart="$PYTHON" "$REPO_DIR/$PY_BASENAME"
StandardOutput=journal
StandardError=journal
EOF

cat > "$SYSTEMD_USER_DIR/$TIMER_NAME" <<EOF
[Unit]
Description=Lazy Commit Timer -- 8x daily with randomized delay
Requires=$SERVICE_NAME

[Timer]
OnCalendar=*-*-* 08,10,12,14,16,18,20,22:00:00
RandomizedDelaySec=45m
Persistent=true

[Install]
WantedBy=timers.target
EOF

# reload & enable
systemctl --user daemon-reload
systemctl --user enable "$TIMER_NAME"
systemctl --user start "$TIMER_NAME"

echo ""
echo "Note: Persistent=true means missed runs fire immediately on boot."
echo "Done. Timer enabled for user $(whoami)."
echo ""
echo "Commands:"
echo "  systemctl --user status $TIMER_NAME     # check timer"
echo "  systemctl --user status $SERVICE_NAME   # check last run"
echo "  journalctl --user -u $SERVICE_NAME -f   # follow logs"
echo "  systemctl --user start $TIMER_NAME      # start now"
echo "  systemctl --user stop $TIMER_NAME       # stop"
echo ""
echo "Preview schedule:"
echo "  $PYTHON $REPO_DIR/$PY_BASENAME --plan"
echo ""
echo "Test dry-run:"
echo "  $PYTHON $REPO_DIR/$PY_BASENAME --dry-run"
echo ""
echo "Force commit:"
echo "  $PYTHON $REPO_DIR/$PY_BASENAME --force"
