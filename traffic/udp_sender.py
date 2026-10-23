#!/usr/bin/env python3
"""
udp_sender.py - Rate-controlled UDP Traffic Generator
"""
import socket
import time
import struct
import argparse
import sys

HEADER_FORMAT = "!Q d 8s"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

def send_traffic(dst_ip, dst_port, rate_mbps, duration_sec, packet_size, traffic_class):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    bytes_per_sec = (rate_mbps * 1_000_000) / 8.0
    packets_per_sec = bytes_per_sec / packet_size
    interval = 1.0 / packets_per_sec if packets_per_sec > 0 else 0.01

    payload_size = max(0, packet_size - HEADER_SIZE)
    dummy_payload = b'X' * payload_size
    class_tag = traffic_class.encode('utf-8')[:8].ljust(8, b'\x00')
    
    seq = 0
    start_time = time.time()
    next_send_time = start_time
    total_bytes = 0

    print(f"[*] Starting {traffic_class} sender -> {dst_ip}:{dst_port}")
    print(f"[*] Target Rate: {rate_mbps} Mbps | Packet Size: {packet_size}B | Duration: {duration_sec}s")

    while (time.time() - start_time) < duration_sec:
        now = time.time()
        header = struct.pack(HEADER_FORMAT, seq, now, class_tag)
        packet = header + dummy_payload

        try:
            sock.sendto(packet, (dst_ip, dst_port))
            seq += 1
            total_bytes += len(packet)
        except Exception as e:
            print(f"Send error: {e}", file=sys.stderr)

        next_send_time += interval
        sleep_time = next_send_time - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)

    actual_duration = time.time() - start_time
    actual_rate_mbps = (total_bytes * 8) / (actual_duration * 1_000_000) if actual_duration > 0 else 0.0
    print(f"[+] Finished {traffic_class}: Sent {seq} packets ({total_bytes} bytes) in {actual_duration:.2f}s (~{actual_rate_mbps:.2f} Mbps)")
    sock.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Custom UDP Sender")
    parser.add_argument("--dst-ip", "-i", default="10.0.0.4", help="Target IP")
    parser.add_argument("--port", "-p", type=int, required=True, help="Target UDP Port")
    parser.add_argument("--rate", "-r", type=float, required=True, help="Sending rate in Mbps")
    parser.add_argument("--duration", "-d", type=float, default=5.0, help="Duration in seconds")
    parser.add_argument("--size", "-s", type=int, default=1000, help="Packet size in bytes")
    parser.add_argument("--traffic-class", "-c", "--class", dest="traffic_class", default="VOICE", help="Traffic Class")
    args = parser.parse_args()

    send_traffic(args.dst_ip, args.port, args.rate, args.duration, args.size, args.traffic_class)
