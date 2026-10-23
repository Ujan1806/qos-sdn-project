#!/usr/bin/env bash
# stop_project.sh - Gracefully shuts down all running project processes
set -e

PROJECT_DIR="/home/ujan/qos-sdn-project"
bash "$PROJECT_DIR/scripts/cleanup.sh"
echo "[+] Project successfully stopped."
