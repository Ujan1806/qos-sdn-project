#!/usr/bin/env python3
"""
udp_receiver.py - Robust UDP Receiver with Latency, Jitter, Packet Loss & Throughput Calculation
"""
import socket
import struct
import time
import argparse
import csv
import os
import sys
import signal

HEADER_FORMAT = "!Q d 8s"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

def save_and_print_metrics(received_seqs, latencies_ms, jitter_samples, total_bytes, start_time, last_receive_time, traffic_class, port, output_csv):
    rx_count = len(received_seqs)
    if rx_count > 0:
        min_seq = min(received_seqs)
        max_seq = max(received_seqs)
        expected_packets = max_seq - min_seq + 1
        lost_packets = max(0, expected_packets - rx_count)
        loss_pct = (lost_packets / expected_packets) * 100.0 if expected_packets > 0 else 0.0

        duration = (last_receive_time - start_time) if (last_receive_time and start_time and last_receive_time > start_time) else 1.0
        throughput_mbps = (total_bytes * 8.0) / (duration * 1_000_000.0)
        avg_latency = sum(latencies_ms) / len(latencies_ms)
        min_latency = min(latencies_ms)
        max_latency = max(latencies_ms)
        avg_jitter = (sum(jitter_samples) / len(jitter_samples)) if jitter_samples else 0.0
    else:
        rx_count = 0
        lost_packets = 0
        loss_pct = 100.0
        throughput_mbps = 0.0
        avg_latency = 0.0
        min_latency = 0.0
        max_latency = 0.0
        avg_jitter = 0.0

    print(f"\n================ Metrics for {traffic_class} (Port {port}) ================")
    print(f"  Packets Received  : {rx_count}")
    print(f"  Packets Lost      : {lost_packets} ({loss_pct:.2f}%)")
    print(f"  Throughput        : {throughput_mbps:.2f} Mbps")
    print(f"  Avg Latency       : {avg_latency:.2f} ms (min: {min_latency:.2f} ms, max: {max_latency:.2f} ms)")
    print(f"  Avg Jitter        : {avg_jitter:.2f} ms")
    print("========================================================================\n", flush=True)

    if output_csv:
        dir_name = os.path.dirname(os.path.abspath(output_csv))
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        file_exists = os.path.isfile(output_csv)
        with open(output_csv, 'a', newline='', buffering=1) as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow([
                    'timestamp', 'traffic_class', 'port', 'packets_received',
                    'packets_lost', 'loss_percent', 'throughput_mbps',
                    'avg_latency_ms', 'min_latency_ms', 'max_latency_ms', 'jitter_ms'
                ])
            writer.writerow([
                time.strftime("%Y-%m-%d %H:%M:%S"), traffic_class, port, rx_count,
                lost_packets, f"{loss_pct:.2f}", f"{throughput_mbps:.2f}",
                f"{avg_latency:.2f}", f"{min_latency:.2f}", f"{max_latency:.2f}", f"{avg_jitter:.2f}"
            ])
            f.flush()

def run_receiver(port, duration_sec, output_csv, traffic_class):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))
    sock.settimeout(1.0)

    print(f"[*] UDP Receiver listening on port {port} for class {traffic_class} (Duration: {duration_sec}s)...", flush=True)

    received_seqs = []
    latencies_ms = []
    jitter_samples = []
    total_bytes = 0
    start_time = None
    last_receive_time = None
    prev_transit = None

    running = [True]

    def handle_signal(sig, frame):
        running[0] = False

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    deadline = time.time() + duration_sec + 2.0

    while running[0] and time.time() < deadline:
        try:
            data, addr = sock.recvfrom(65535)
            recv_time = time.time()
            if start_time is None:
                start_time = recv_time

            total_bytes += len(data)
            last_receive_time = recv_time

            if len(data) >= HEADER_SIZE:
                seq, send_timestamp, tag = struct.unpack(HEADER_FORMAT, data[:HEADER_SIZE])
                received_seqs.append(seq)
                
                latency = max(0.0, (recv_time - send_timestamp) * 1000.0)
                latencies_ms.append(latency)

                transit = recv_time - send_timestamp
                if prev_transit is not None:
                    d = abs(transit - prev_transit)
                    jitter_samples.append(d * 1000.0)
                prev_transit = transit

        except socket.timeout:
            if start_time and (time.time() - start_time >= duration_sec) and (time.time() - last_receive_time >= 1.5):
                break
            continue

    sock.close()

    save_and_print_metrics(
        received_seqs, latencies_ms, jitter_samples, total_bytes,
        start_time, last_receive_time, traffic_class, port, output_csv
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UDP Receiver")
    parser.add_argument("--port", type=int, required=True, help="UDP Listening Port")
    parser.add_argument("--duration", type=float, default=10.0, help="Duration to listen")
    parser.add_argument("--output", default="results/measurements.csv", help="CSV Output Path")
    parser.add_argument("--traffic-class", default="VOICE", help="Traffic Class Name")
    args = parser.parse_args()

    run_receiver(args.port, args.duration, args.output, args.traffic_class)
