#!/usr/bin/env python3
"""
calculate_fairness.py - Computes Jain's Fairness Index across Traffic Classes
=============================================================================
Formula:
    J = (sum(x_i))^2 / (n * sum(x_i^2))
where:
    x_i = throughput of class i
    n   = total number of active traffic classes (3)

CRITICAL NETWORKING / QoS NOTE:
In a Best-Effort network, high fairness (~1.0) is often considered desirable.
In a QoS Prioritized network, resource allocation is INTENTIONALLY UNEQUAL!
High priority traffic (Voice) receives guaranteed low latency and zero loss,
while low priority bulk data is intentionally throttled. Therefore, a lower
Jain's Fairness Index under QoS reflects purposeful policy differentiation.
"""

import sys
import os
import pandas as pd
import argparse

def compute_jains_index(throughputs):
    """Calculates Jain's Fairness Index from a list or array of throughputs."""
    if not throughputs or len(throughputs) == 0:
        return 0.0
    n = len(throughputs)
    sum_x = sum(throughputs)
    sum_x_sq = sum(x ** 2 for x in throughputs)
    if sum_x_sq == 0:
        return 0.0
    return (sum_x ** 2) / (n * sum_x_sq)

def analyze_csv_fairness(csv_path):
    if not os.path.exists(csv_path):
        print(f"[-] File not found: {csv_path}", file=sys.stderr)
        return None

    df = pd.read_csv(csv_path)
    if 'throughput_mbps' not in df.columns:
        print(f"[-] 'throughput_mbps' column missing in {csv_path}", file=sys.stderr)
        return None

    throughputs = df['throughput_mbps'].tolist()
    j_index = compute_jains_index(throughputs)

    print(f"\n=======================================================")
    print(f"     JAIN'S FAIRNESS INDEX ANALYSIS: {os.path.basename(csv_path)}")
    print(f"=======================================================")
    for _, row in df.iterrows():
        print(f"  Class: {row['traffic_class']:<8} | Port: {row['port']} | Throughput: {row['throughput_mbps']:>6.2f} Mbps | Loss: {row['loss_percent']:>5.2f}% | Latency: {row['avg_latency_ms']:>7.2f} ms")
    print(f"-------------------------------------------------------")
    print(f"  Calculated Jain's Fairness Index (J) : {j_index:.4f}")
    print(f"=======================================================\n")
    return j_index

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Calculate Jain's Fairness Index")
    parser.add_argument("csv_file", nargs="?", default="results/baseline_results.csv", help="Path to experiment results CSV")
    args = parser.parse_args()

    analyze_csv_fairness(args.csv_file)
