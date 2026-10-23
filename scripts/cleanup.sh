#!/usr/bin/env bash
# cleanup.sh - Clean up all Mininet namespaces, OVS bridges, QoS queues, and background processes
set -e

echo "=========================================================="
echo "    CLEANING UP QoS SDN PROJECT ENVIRONMENT              "
echo "=========================================================="

echo "[*] Terminating Ryu Controller and Mininet processes..."
sudo pkill -9 -f "ryu.cmd.manager" 2>/dev/null || true
sudo pkill -9 -f "ryu-manager" 2>/dev/null || true
sudo pkill -9 -f "udp_sender.py" 2>/dev/null || true
sudo pkill -9 -f "udp_receiver.py" 2>/dev/null || true
sudo pkill -9 -f "qos_topology.py" 2>/dev/null || true
sudo pkill -9 -f "run_experiment.py" 2>/dev/null || true

echo "[*] Cleaning Mininet residual interfaces and namespaces..."
sudo mn -c 2>/dev/null || true

echo "[*] Removing OVS QoS records and queues..."
sudo ovs-vsctl --all destroy qos 2>/dev/null || true
sudo ovs-vsctl --all destroy queue 2>/dev/null || true

echo "[+] Cleanup complete. Virtual networking environment is pristine."
echo "=========================================================="
