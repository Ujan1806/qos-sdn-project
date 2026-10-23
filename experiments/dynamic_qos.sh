#!/usr/bin/env bash
# dynamic_qos.sh - Runs the Dynamic SDN QoS re-prioritization experiment
set -e
echo "=========================================================="
echo "    RUNNING DYNAMIC SDN QoS RE-PRIORITIZATION EXPERIMENT "
echo "=========================================================="
sudo python3 /home/ujan/qos-sdn-project/experiments/run_experiment.py --mode dynamic --duration 15
