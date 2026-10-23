#!/usr/bin/env bash
# cleanup_queues.sh - Clear all OVS QoS and Queues
set -e

SW_PORT="s1-eth4"

echo "[*] Cleaning up OVS QoS and Queues on $SW_PORT..."
sudo ovs-vsctl --all destroy qos 2>/dev/null || true
sudo ovs-vsctl --all destroy queue 2>/dev/null || true
sudo ovs-vsctl clear port "$SW_PORT" qos 2>/dev/null || true
echo "[+] QoS cleanup complete."
