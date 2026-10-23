#!/usr/bin/env python3
"""
collect_metrics.py - Consolidates metrics from Baseline, Static QoS, and Dynamic QoS
===================================================================================
Produces a unified comparison table showing:
- Throughput (Mbps)
- Packet Loss (%)
- Average Latency (ms)
- Jitter (ms)
- Jain's Fairness Index
"""

import os
import sys
import pandas as pd

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RESULTS_DIR = os.path.join(PROJECT_DIR, 'results')

def compute_jains(throughputs):
    n = len(throughputs)
    if n == 0 or sum(throughputs) == 0:
        return 0.0
    return (sum(throughputs) ** 2) / (n * sum(x ** 2 for x in throughputs))

def load_and_summarize():
    experiments = {
        'Baseline (No QoS)': os.path.join(RESULTS_DIR, 'baseline_results.csv'),
        'Static QoS': os.path.join(RESULTS_DIR, 'qos_results.csv'),
        'Dynamic QoS': os.path.join(RESULTS_DIR, 'dynamic_results.csv')
    }

    summary_rows = []

    for exp_name, file_path in experiments.items():
        if not os.path.exists(file_path):
            continue
        df = pd.read_csv(file_path)
        j_index = compute_jains(df['throughput_mbps'].tolist())

        for _, row in df.iterrows():
            summary_rows.append({
                'Experiment': exp_name,
                'Traffic Class': row['traffic_class'],
                'Port': int(row['port']),
                'Throughput (Mbps)': float(row['throughput_mbps']),
                'Loss (%)': float(row['loss_percent']),
                'Avg Latency (ms)': float(row['avg_latency_ms']),
                'Jitter (ms)': float(row['jitter_ms']),
                'Jains Fairness': round(j_index, 4)
            })

    if not summary_rows:
        print("[-] No experiment results found in results/ directory.")
        return None

    summary_df = pd.DataFrame(summary_rows)
    print("\n==========================================================================================================")
    print("                              CONSOLIDATED EXPERIMENT METRICS COMPARISON                                  ")
    print("==========================================================================================================")
    print(summary_df.to_string(index=False))
    print("==========================================================================================================\n")

    summary_csv = os.path.join(RESULTS_DIR, 'consolidated_summary.csv')
    summary_df.to_csv(summary_csv, index=False)
    print(f"[+] Consolidated summary saved to: {summary_csv}")
    return summary_df

if __name__ == '__main__':
    load_and_summarize()
