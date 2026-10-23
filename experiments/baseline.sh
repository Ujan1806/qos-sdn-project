#!/usr/bin/env bash
# baseline.sh - Runs the baseline experiment (Without QoS)
set -e
sudo python3 /home/ujan/qos-sdn-project/experiments/run_experiment.py --mode baseline --duration 12
