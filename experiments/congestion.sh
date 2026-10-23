#!/usr/bin/env bash
# congestion.sh - Demonstrates unmanaged bottleneck congestion without QoS
set -e
echo "=========================================================="
echo "    RUNNING CONGESTED BASELINE TRAFFIC EXPERIMENT        "
echo "=========================================================="
sudo python3 /home/ujan/qos-sdn-project/experiments/run_experiment.py --mode baseline --duration 12
