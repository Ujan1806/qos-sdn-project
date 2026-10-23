#!/usr/bin/env python3
"""
run_experiment.py - Automated Mininet Experiment Runner for Baseline, Static QoS, and Dynamic QoS
================================================================================================
"""
import sys
import os
import time
import argparse
import subprocess
import urllib.request
import json

# Add parent directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from topology.qos_topology import QoSTopo
from traffic.traffic_config import TRAFFIC_CLASSES, SERVER_IP

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RESULTS_DIR = os.path.join(PROJECT_DIR, 'results')
LOGS_DIR = os.path.join(PROJECT_DIR, 'logs')

os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

def cleanup_environment():
    info("[*] Cleaning up environment (Mininet, OVS, Ryu)...\n")
    subprocess.run(["pkill", "-9", "-f", "ryu.cmd.manager"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    subprocess.run(["pkill", "-9", "-f", "ryu-manager"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    subprocess.run(["mn", "-c"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    subprocess.run(["ovs-vsctl", "--all", "destroy", "qos"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    subprocess.run(["ovs-vsctl", "--all", "destroy", "queue"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    time.sleep(1.0)

def start_ryu_controller():
    controller_script = os.path.join(PROJECT_DIR, 'controller', 'qos_controller.py')
    log_file = open(os.path.join(LOGS_DIR, 'ryu_controller.log'), 'w')
    info("[*] Starting Ryu OpenFlow 1.3 QoS Controller (Port 6653, REST: 8080)...\n")
    
    env = os.environ.copy()
    user_site = "/home/ujan/.local/lib/python3.14/site-packages"
    env["PYTHONPATH"] = f"{user_site}:{env.get('PYTHONPATH', '')}"

    proc = subprocess.Popen(
        [
            sys.executable, "-m", "ryu.cmd.manager",
            controller_script,
            "--ofp-tcp-listen-port", "6653",
            "--wsapi-host", "127.0.0.1",
            "--wsapi-port", "8080"
        ],
        stdout=log_file,
        stderr=subprocess.STDOUT,
        env=env
    )
    time.sleep(3.0)
    return proc, log_file

def update_controller_policy_rest(policy_dict):
    """Sends a REST request to the Ryu controller to dynamically update QoS policy."""
    url = "http://127.0.0.1:8080/qos/policy"
    data = json.dumps(policy_dict).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            info(f"[+] Dynamic QoS REST Response: {resp.read().decode('utf-8')}\n")
    except Exception as e:
        info(f"[-] Warning: Failed to send REST policy update: {e}\n")

def run_test(mode="baseline", duration=12):
    cleanup_environment()

    output_csv = os.path.join(RESULTS_DIR, f"{mode}_results.csv")
    if os.path.exists(output_csv):
        os.remove(output_csv)

    info(f"\n=======================================================\n")
    info(f"   STARTING EXPERIMENT: {mode.upper()}\n")
    info(f"   Duration: {duration}s | Output: {output_csv}\n")
    info(f"=======================================================\n")

    ryu_proc = None
    ryu_log = None

    if mode in ["qos", "dynamic"]:
        ryu_proc, ryu_log = start_ryu_controller()

    topo = QoSTopo()
    if mode == "baseline":
        net = Mininet(topo=topo, link=TCLink, switch=OVSSwitch)
    else:
        c0 = RemoteController('c0', ip='127.0.0.1', port=6653)
        net = Mininet(topo=topo, link=TCLink, switch=OVSSwitch, controller=c0)

    net.start()
    info("[*] Testing initial connectivity with pingAll...\n")
    time.sleep(1.0)
    net.pingAll()

    # If QoS mode, configure OVS queues on bottleneck port s1-eth4
    if mode in ["qos", "dynamic"]:
        info("[*] Setting up OVS QoS Queues on bottleneck port s1-eth4...\n")
        subprocess.run(["bash", os.path.join(PROJECT_DIR, 'qos', 'setup_queues.sh')],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.0)

    h1 = net.get('h1')
    h2 = net.get('h2')
    h3 = net.get('h3')
    h4 = net.get('h4')

    # 1. Start UDP Receivers on Server h4
    info(f"[*] Starting UDP Receivers on Server h4 (Ports 5001, 5002, 5003 for {duration}s)...\n")
    for name, cfg in TRAFFIC_CLASSES.items():
        cmd = (f"python3 {PROJECT_DIR}/traffic/udp_receiver.py "
               f"--port {cfg['port']} --duration {duration} "
               f"--traffic-class {name} --output {output_csv} "
               f"> {LOGS_DIR}/rx_{name.lower()}_{mode}.log 2>&1 &")
        h4.cmd(cmd)

    time.sleep(1.0)

    # 2. Start Traffic Senders simultaneously
    info(f"[*] Generating 11 Mbps Traffic (VOICE=1M, VIDEO=4M, BULK=6M for {duration}s)...\n")
    senders = [
        (h1, 'VOICE'),
        (h2, 'VIDEO'),
        (h3, 'BULK')
    ]
    for host, name in senders:
        cfg = TRAFFIC_CLASSES[name]
        cmd = (f"python3 {PROJECT_DIR}/traffic/udp_sender.py "
               f"-i {SERVER_IP} -p {cfg['port']} -r {cfg['rate_mbps']} "
               f"-d {duration} -s {cfg['packet_size']} -c {name} "
               f"> {LOGS_DIR}/tx_{name.lower()}_{mode}.log 2>&1 &")
        host.cmd(cmd)

    if mode == "dynamic":
        # Mid-stream dynamic policy trigger at T = 6s
        dynamic_trigger_time = 6.0
        info(f"[*] Traffic running... Dynamic policy will trigger at T={dynamic_trigger_time}s...\n")
        time.sleep(dynamic_trigger_time)

        info("\n[!] >>> DYNAMIC EVENT TRIGGERED: Promoting VIDEO (5002) to Queue 0 & Demoting VOICE (5001) to Queue 1 <<<\n")
        new_policy = {
            5002: {'name': 'VIDEO', 'queue_id': 0, 'priority': 250},
            5001: {'name': 'VOICE', 'queue_id': 1, 'priority': 200},
            5003: {'name': 'BULK',  'queue_id': 2, 'priority': 100}
        }
        update_controller_policy_rest(new_policy)
        remaining = max(1.0, duration - dynamic_trigger_time + 3.0)
        info(f"[*] Continuing traffic under new dynamic policy for {remaining:.1f}s...\n")
        time.sleep(remaining)
    else:
        info(f"[*] Traffic running... Waiting {duration + 3} seconds for completion...\n")
        time.sleep(duration + 3)

    net.stop()

    if ryu_proc:
        ryu_proc.terminate()
        try:
            ryu_proc.wait(timeout=2.0)
        except Exception:
            ryu_proc.kill()
        if ryu_log:
            ryu_log.close()

    cleanup_environment()

    # Display results
    info("\n=======================================================\n")
    info(f"             {mode.upper()} MEASURED RESULTS            \n")
    info("=======================================================\n")
    if os.path.exists(output_csv):
        with open(output_csv, 'r') as f:
            print(f.read())
    else:
        print("[-] No results generated.")

if __name__ == '__main__':
    setLogLevel('info')
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="baseline", choices=["baseline", "qos", "dynamic"])
    parser.add_argument("--duration", type=int, default=12)
    args = parser.parse_args()

    run_test(mode=args.mode, duration=args.duration)
