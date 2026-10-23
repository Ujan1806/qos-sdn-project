#!/usr/bin/env bash
# qos_experiment.sh - Runs static SDN QoS prioritization experiment
set -e
echo "=========================================================="
echo "    RUNNING STATIC SDN QoS PRIORITIZATION EXPERIMENT     "
echo "=========================================================="
sudo python3 /home/ujan/qos-sdn-project/experiments/run_experiment.py --mode qos --duration 12
