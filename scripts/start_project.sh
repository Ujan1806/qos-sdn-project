#!/usr/bin/env bash
# start_project.sh - Launches Ryu OpenFlow 1.3 Controller and Mininet QoS Topology
set -e

PROJECT_DIR="/home/ujan/qos-sdn-project"
export PYTHONPATH="/home/ujan/.local/lib/python3.14/site-packages:$PYTHONPATH"

echo "=========================================================="
echo "    STARTING QoS TRAFFIC MANAGEMENT SYSTEM               "
echo "=========================================================="

# 1. Clean previous state
bash "$PROJECT_DIR/scripts/cleanup.sh"

# 2. Start Ryu Controller
echo "[*] Launching Ryu SDN Controller on port 6653 (REST API on 8080)..."
python3 -m ryu.cmd.manager "$PROJECT_DIR/controller/qos_controller.py" \
  --ofp-tcp-listen-port 6653 --wsapi-host 127.0.0.1 --wsapi-port 8080 > "$PROJECT_DIR/logs/ryu_controller.log" 2>&1 &
CONTROLLER_PID=$!
echo "[+] Controller PID: $CONTROLLER_PID"
sleep 2

# 3. Start Mininet Topology in Interactive CLI Mode
echo "[*] Launching Mininet Topology (4 Hosts, 2 Switches, 5 Mbps Bottleneck)..."
sudo python3 "$PROJECT_DIR/topology/qos_topology.py"

# Stop controller after CLI exit
echo "[*] Mininet CLI closed. Stopping controller..."
kill $CONTROLLER_PID 2>/dev/null || true
bash "$PROJECT_DIR/scripts/cleanup.sh"
