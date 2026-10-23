#!/usr/bin/env bash
# setup_queues.sh - Configure Linux HTB QoS Queues on Open vSwitch bottleneck port (s1-eth4)
set -e

SW_PORT="s1-eth4"

echo "=========================================================="
echo "    CONFIGURING OVS QoS QUEUES ON $SW_PORT                "
echo "    Total Link Bandwidth: 5.0 Mbps                        "
echo "=========================================================="

# 1. Clean up existing QoS records
sudo ovs-vsctl --all destroy qos 2>/dev/null || true
sudo ovs-vsctl --all destroy queue 2>/dev/null || true
sudo ovs-vsctl clear port "$SW_PORT" qos 2>/dev/null || true

# 2. Create HTB QoS with 3 priority queues
# Queue 0 (VOICE): Min 2.5 Mbps, Max 5.0 Mbps (High Priority, guaranteed bandwidth)
# Queue 1 (VIDEO): Min 1.5 Mbps, Max 4.0 Mbps (Medium Priority)
# Queue 2 (BULK) : Min 0.5 Mbps, Max 1.5 Mbps (Low Priority, throttled background)
sudo ovs-vsctl -- set port "$SW_PORT" qos=@newqos \
  -- --id=@newqos create qos type=linux-htb other-config:max-rate=5000000 \
     queues:0=@q0 queues:1=@q1 queues:2=@q2 \
  -- --id=@q0 create queue other-config:min-rate=2500000 other-config:max-rate=5000000 \
  -- --id=@q1 create queue other-config:min-rate=1500000 other-config:max-rate=4000000 \
  -- --id=@q2 create queue other-config:min-rate=500000  other-config:max-rate=1500000

echo "[+] Successfully configured 3 QoS queues on $SW_PORT:"
sudo ovs-vsctl list qos
echo ""
sudo ovs-vsctl list queue
echo "=========================================================="
