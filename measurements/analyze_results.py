#!/usr/bin/env python3
"""
analyze_results.py - Generates Publication-Quality Graphs for QoS Evaluation
===========================================================================
Generates:
1. plots/throughput_comparison.png (Throughput vs Traffic Class across No QoS, Static QoS, Dynamic QoS)
2. plots/latency_comparison.png    (Latency vs Traffic Class across No QoS, Static QoS, Dynamic QoS)
3. plots/packet_loss_comparison.png(Packet Loss % vs Traffic Class)
4. plots/jitter_comparison.png     (Jitter vs Traffic Class)
5. plots/fairness_index.png        (Jain's Fairness Index across Experiments)
6. plots/priority_satisfaction.png (Offered Load vs Actual Received Throughput)
7. plots/qos_comprehensive_overview.png (Multi-panel dashboard summarizing the entire system)
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg') # Headless rendering for Linux terminal environments
import matplotlib.pyplot as plt

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RESULTS_DIR = os.path.join(PROJECT_DIR, 'results')
PLOTS_DIR = os.path.join(PROJECT_DIR, 'plots')
os.makedirs(PLOTS_DIR, exist_ok=True)

def load_data():
    files = {
        'No QoS': os.path.join(RESULTS_DIR, 'baseline_results.csv'),
        'Static QoS': os.path.join(RESULTS_DIR, 'qos_results.csv'),
        'Dynamic QoS': os.path.join(RESULTS_DIR, 'dynamic_results.csv')
    }
    data = {}
    for label, path in files.items():
        if os.path.exists(path):
            df = pd.read_csv(path)
            # Ensure consistent order of classes
            df['traffic_class'] = pd.Categorical(df['traffic_class'], categories=['VOICE', 'VIDEO', 'BULK'], ordered=True)
            df = df.sort_values('traffic_class')
            data[label] = df
        else:
            print(f"[-] Warning: {path} not found. Run the corresponding experiment first.")
    return data

def plot_grouped_bar(data, metric_col, title, ylabel, filename, y_max=None, is_log=False):
    plt.figure(figsize=(9, 5.5))
    classes = ['VOICE', 'VIDEO', 'BULK']
    x = np.arange(len(classes))
    width = 0.25

    colors = {'No QoS': '#e74c3c', 'Static QoS': '#2ecc71', 'Dynamic QoS': '#3498db'}

    i = 0
    for label, df in data.items():
        vals = [df[df['traffic_class'] == c][metric_col].values[0] if len(df[df['traffic_class'] == c]) > 0 else 0 for c in classes]
        offset = (i - 1) * width
        rects = plt.bar(x + offset, vals, width, label=label, color=colors.get(label, '#95a5a6'), edgecolor='black', linewidth=0.8)
        
        # Add data labels
        for rect in rects:
            height = rect.get_height()
            if height > 0:
                plt.annotate(f'{height:.2f}',
                             xy=(rect.get_x() + rect.get_width() / 2, height),
                             xytext=(0, 3), textcoords="offset points",
                             ha='center', va='bottom', fontsize=9, fontweight='bold')
        i += 1

    plt.xlabel('Traffic Class (Priority Tier)', fontsize=12, fontweight='bold')
    plt.ylabel(ylabel, fontsize=12, fontweight='bold')
    plt.title(title, fontsize=14, fontweight='bold', pad=15)
    plt.xticks(x, ['VOICE\n(Port 5001 - High)', 'VIDEO\n(Port 5002 - Med)', 'BULK\n(Port 5003 - Low)'], fontsize=11)
    plt.legend(frameon=True, fontsize=11)
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    if is_log:
        plt.yscale('log')
    elif y_max:
        plt.ylim(0, y_max)
    plt.tight_layout()
    out_path = os.path.join(PLOTS_DIR, filename)
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"[+] Saved: {out_path}")

def plot_fairness(data):
    plt.figure(figsize=(7, 5))
    names = []
    fairness_vals = []

    for label, df in data.items():
        th = df['throughput_mbps'].tolist()
        n = len(th)
        j = (sum(th) ** 2) / (n * sum(x ** 2 for x in th)) if n > 0 and sum(th) > 0 else 0
        names.append(label)
        fairness_vals.append(j)

    bars = plt.bar(names, fairness_vals, color=['#e74c3c', '#2ecc71', '#3498db'], width=0.5, edgecolor='black', linewidth=0.8)
    for bar in bars:
        h = bar.get_height()
        plt.annotate(f'{h:.4f}',
                     xy=(bar.get_x() + bar.get_width() / 2, h),
                     xytext=(0, 4), textcoords="offset points",
                     ha='center', va='bottom', fontsize=11, fontweight='bold')

    plt.title("Jain's Fairness Index Across Experiment Scenarios", fontsize=13, fontweight='bold')
    plt.ylabel("Jain's Fairness Index (0 to 1)", fontsize=11, fontweight='bold')
    plt.ylim(0, 1.15)
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    
    # Explanatory note on QoS vs Fairness
    plt.figtext(0.5, -0.05,
                 "Note: Lower fairness under QoS reflects deliberate prioritization of critical Voice/Video\nover background Bulk data, fulfilling the QoS policy objective.",
                 ha="center", fontsize=9, style='italic', bbox={"facecolor":"orange", "alpha":0.1, "pad":5})

    out_path = os.path.join(PLOTS_DIR, 'fairness_index.png')
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[+] Saved: {out_path}")

def plot_dashboard(data):
    """Generates a 4-panel comprehensive comparison dashboard."""
    fig, axs = plt.subplots(2, 2, figsize=(14, 10))
    classes = ['VOICE', 'VIDEO', 'BULK']
    x = np.arange(len(classes))
    width = 0.25
    colors = {'No QoS': '#e74c3c', 'Static QoS': '#2ecc71', 'Dynamic QoS': '#3498db'}

    # 1. Throughput
    i = 0
    for label, df in data.items():
        vals = [df[df['traffic_class'] == c]['throughput_mbps'].values[0] if len(df[df['traffic_class'] == c]) > 0 else 0 for c in classes]
        axs[0, 0].bar(x + (i - 1) * width, vals, width, label=label, color=colors.get(label))
        i += 1
    axs[0, 0].set_title("Throughput (Mbps) - Bottleneck = 5 Mbps", fontweight='bold')
    axs[0, 0].set_ylabel("Mbps", fontweight='bold')
    axs[0, 0].set_xticks(x)
    axs[0, 0].set_xticklabels(classes)
    axs[0, 0].grid(axis='y', linestyle='--', alpha=0.5)
    axs[0, 0].legend()

    # 2. Packet Loss %
    i = 0
    for label, df in data.items():
        vals = [df[df['traffic_class'] == c]['loss_percent'].values[0] if len(df[df['traffic_class'] == c]) > 0 else 0 for c in classes]
        axs[0, 1].bar(x + (i - 1) * width, vals, width, label=label, color=colors.get(label))
        i += 1
    axs[0, 1].set_title("Packet Loss Percentage (%)", fontweight='bold')
    axs[0, 1].set_ylabel("Loss %", fontweight='bold')
    axs[0, 1].set_xticks(x)
    axs[0, 1].set_xticklabels(classes)
    axs[0, 1].grid(axis='y', linestyle='--', alpha=0.5)

    # 3. Latency (Log scale)
    i = 0
    for label, df in data.items():
        vals = [df[df['traffic_class'] == c]['avg_latency_ms'].values[0] if len(df[df['traffic_class'] == c]) > 0 else 0 for c in classes]
        axs[1, 0].bar(x + (i - 1) * width, vals, width, label=label, color=colors.get(label))
        i += 1
    axs[1, 0].set_title("Average Latency (ms, Log Scale)", fontweight='bold')
    axs[1, 0].set_ylabel("Latency (ms)", fontweight='bold')
    axs[1, 0].set_yscale('log')
    axs[1, 0].set_xticks(x)
    axs[1, 0].set_xticklabels(classes)
    axs[1, 0].grid(axis='y', linestyle='--', alpha=0.5)

    # 4. Jitter (ms)
    i = 0
    for label, df in data.items():
        vals = [df[df['traffic_class'] == c]['jitter_ms'].values[0] if len(df[df['traffic_class'] == c]) > 0 else 0 for c in classes]
        axs[1, 1].bar(x + (i - 1) * width, vals, width, label=label, color=colors.get(label))
        i += 1
    axs[1, 1].set_title("Jitter (ms)", fontweight='bold')
    axs[1, 1].set_ylabel("Jitter (ms)", fontweight='bold')
    axs[1, 1].set_xticks(x)
    axs[1, 1].set_xticklabels(classes)
    axs[1, 1].grid(axis='y', linestyle='--', alpha=0.5)

    plt.suptitle("QoS Traffic Management System - Complete Experimental Evaluation", fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    out_path = os.path.join(PLOTS_DIR, 'qos_comprehensive_overview.png')
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"[+] Saved: {out_path}")

def generate_all():
    data = load_data()
    if not data:
        print("[-] No data found to plot.")
        return

    print("[*] Generating Analytical Plots...")
    plot_grouped_bar(data, 'throughput_mbps', "Throughput Comparison: No QoS vs Static QoS vs Dynamic QoS", "Throughput (Mbps)", "throughput_comparison.png", y_max=5.0)
    plot_grouped_bar(data, 'loss_percent', "Packet Loss Percentage Comparison", "Packet Loss (%)", "packet_loss_comparison.png", y_max=100.0)
    plot_grouped_bar(data, 'avg_latency_ms', "Average Latency Comparison (Log Scale)", "Average Latency (ms)", "latency_comparison.png", is_log=True)
    plot_grouped_bar(data, 'jitter_ms', "Jitter Comparison across Traffic Classes", "Jitter (ms)", "jitter_comparison.png")
    plot_fairness(data)
    plot_dashboard(data)
    print(f"[+] All 6 plots successfully created in: {PLOTS_DIR}")

if __name__ == '__main__':
    generate_all()
