#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_LINE="0 */2 * * * set -a && . $SCRIPT_DIR/.env && set +a && python3 $SCRIPT_DIR/aggregator.py >> $SCRIPT_DIR/aggregator.log 2>&1"

if crontab -l 2>/dev/null | grep -qF "$SCRIPT_DIR/aggregator.py"; then
    echo "Cron job already installed."
else
    (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
    echo "Cron job installed — runs every 2 hours."
fi
