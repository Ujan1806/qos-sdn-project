# QoS Traffic Management System using Software-Defined Networking (SDN)

> **Computer Networks Mini-Project**  
> **Topic:** Dynamic Flow Prioritization and Quality of Service (QoS) using OpenFlow 1.3, Ryu SDN Controller, Open vSwitch, Mininet, and Custom Python UDP Socket Programming.

---

## 1. Problem Statement
> *"Develop a UDP-based application that generates different classes of traffic and uses SDN to dynamically prioritize selected flows during network congestion."*

Modern networks carry diverse application traffic with conflicting requirements. Time-critical interactive applications like **Voice over IP (VoIP)** and **Video Conferencing** demand minimal delay and near-zero packet loss, whereas **Bulk File Transfers** demand throughput but can tolerate latency. When heterogeneous flows compete over a shared bandwidth-constrained link (a **bottleneck**), unmanaged best-effort forwarding allows bandwidth-greedy traffic to saturate buffers, inducing bufferbloat, high packet drops, and severe latency spikes on sensitive flows.

---

## 2. Objectives
1. **Implement custom UDP socket applications** to generate deterministic, rate-paced traffic classes with embedded sequence numbers and timestamps.
2. **Emulate a reproducible virtual SDN network** featuring an access-layer network with an explicit 5 Mbps inter-switch bottleneck link using Mininet and Open vSwitch.
3. **Induce controlled network congestion** by generating an aggregate offered load of 11 Mbps across the 5 Mbps bottleneck ($11\text{ Mbps} > 5\text{ Mbps}$).
4. **Develop an OpenFlow 1.3 SDN controller (Ryu)** to classify flows dynamically based on Layer-4 UDP destination ports.
5. **Configure multi-tier Hierarchical Token Bucket (HTB) QoS queues** on the bottleneck switch port to guarantee bandwidth and eliminate packet drops for high-priority flows.
6. **Support dynamic runtime QoS policy re-prioritization** via a REST API without stopping active UDP client/server streams.
7. **Empirically evaluate and compare network performance metrics** (Throughput, One-Way Latency, Packet Loss, RFC 3550 Jitter, and Jain's Fairness Index) across **No QoS**, **Static QoS**, and **Dynamic QoS** scenarios.

---

## 3. System Architecture & Topology

### 3.1 Network Topology Diagram
```
                     h1 (10.0.0.1)
                   [VOICE: Port 5001]
                    Rate = 1.0 Mbps
                           | (100 Mbps, 1ms)
                           v
                     +-----------+
                     | Switch s1 |
                     +-----------+
                     ^     |     ^
    (100 Mbps, 1ms) /      |      \ (100 Mbps, 1ms)
                   /       |       \
       h2 (10.0.0.2)       |        h3 (10.0.0.3)
     [VIDEO: Port 5002]    |      [BULK: Port 5003]
      Rate = 4.0 Mbps      |       Rate = 6.0 Mbps
                           v
                [ BOTTLENECK LINK: s1-eth4 <-> s2-eth2 ]
                 Bandwidth = 5.0 Mbps, Delay = 10ms
                 Total Offered Load = 11.0 Mbps
                           |
                           v
                     +-----------+
                     | Switch s2 |
                     +-----------+
                           | (100 Mbps, 1ms)
                           v
                     h4 (10.0.0.4)
                 [QoS Traffic Server]
                 UDP Ports: 5001, 5002, 5003
```

### 3.2 SDN Decoupled Architecture
```
+-------------------------------------------------------------------------------+
|                        CONTROL PLANE (Ryu SDN Controller)                     |
|  - OpenFlow 1.3 Protocol Engine                                               |
|  - Flow Classifier (UDP Ports 5001, 5002, 5003)                               |
|  - Dynamic Policy REST API (Port 8080: /qos/policy)                           |
+-------------------------------------------------------------------------------+
                                      ^ (OpenFlow 1.3 / TCP 6653)
                                      v
+-------------------------------------------------------------------------------+
|                         DATA PLANE (Open vSwitch & Linux TC)                  |
|  - Switch s1: Ingress classification & Queue assignment (OFPActionSetQueue)   |
|  - Switch s2: Direct egress delivery to Server h4                             |
|  - Port s1-eth4: Linux HTB Queues (Queue 0: High, Queue 1: Med, Queue 2: Low) |
+-------------------------------------------------------------------------------+
```

---

## 4. Software Requirements
- **Operating System:** Ubuntu Linux 22.04 LTS / 24.04 LTS / 26.04 LTS
- **Network Emulator:** Mininet 2.3.0+
- **Virtual Switch:** Open vSwitch (OVS) 3.0+
- **SDN Controller Framework:** Ryu SDN Framework 4.34
- **OpenFlow Protocol Version:** OpenFlow 1.3
- **Programming Language:** Python 3 (Tested on Python 3.10 - 3.14)
- **Data Science & Plotting:** Pandas, NumPy, Matplotlib
- **Benchmarking Tools:** iperf3, tcpdump

---

## 5. Installation & Setup

### Step 1: Install System Packages
```bash
sudo apt-get update
sudo apt-get install -y mininet openvswitch-switch python3-pip python3-numpy \
  python3-pandas python3-matplotlib iperf3 tcpdump
```

### Step 2: Install Ryu & Networking Dependencies
```bash
cd ~
pip install ryu eventlet dnspython --break-system-packages
```

### Step 3: Clone/Navigate to Project Directory
```bash
cd ~/qos-sdn-project
chmod +x scripts/*.sh experiments/*.sh experiments/*.py traffic/*.py measurements/*.py qos/*.sh
```

---

## 6. Directory Structure
```
qos-sdn-project/
├── controller/
│   └── qos_controller.py       # Ryu OpenFlow 1.3 Controller with REST API
├── experiments/
│   ├── run_experiment.py       # Master automated test harness
│   ├── baseline.sh             # Unmanaged congestion test (No QoS)
│   ├── congestion.sh           # Demonstrates bottleneck buffer exhaustion
│   ├── qos_experiment.sh       # Static SDN QoS test
│   └── dynamic_qos.sh          # Dynamic runtime QoS policy update test
├── measurements/
│   ├── calculate_fairness.py   # Jain's Fairness Index calculator
│   ├── collect_metrics.py      # Consolidates and tabulates results
│   └── analyze_results.py      # Matplotlib publication graph generator
├── plots/                      # High-resolution experimental graphs (.png)
├── qos/
│   ├── setup_queues.sh         # Configures OVS Linux-HTB queues on s1-eth4
│   └── cleanup_queues.sh       # Clears OVS QoS records
├── results/                    # Empirical CSV measurement logs
├── scripts/
│   ├── start_project.sh        # Starts Controller + Mininet CLI
│   ├── stop_project.sh         # Graceful shutdown script
│   └── cleanup.sh              # Safe network environment cleaner
├── topology/
│   └── qos_topology.py         # Mininet 4-host 2-switch bottleneck topology
├── traffic/
│   ├── traffic_config.py       # Traffic class parameters & rates
│   ├── udp_sender.py           # Custom rate-paced UDP packet transmitter
│   └── udp_receiver.py         # Custom UDP receiver & performance analyzer
├── ARCHITECTURE.md             # Detailed engineering design specification
├── DEMO.md                     # Step-by-step demonstration walkthrough
├── EXPERIMENTS.md              # Empirical analysis & measurement logs
├── REVIEW1.md                  # Review 1 presentation slides (9 slides)
├── VIVA.md                     # Comprehensive Viva Voce Q&A guide
└── requirements.txt            # Python dependencies
```

---

## 7. How Custom Socket Programming Works

Rather than treating traffic generation as an opaque black box with `iperf3`, this project implements raw Python UDP socket programming using `socket.socket(socket.AF_INET, socket.SOCK_DGRAM)`.

### 7.1 Packet Header Structure
Every packet generated by `traffic/udp_sender.py` embeds a 24-byte binary header followed by dummy payload bytes:
```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                 Sequence Number (8 Bytes - uint64)            |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                 Send Timestamp (8 Bytes - double)             |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                 Traffic Class Tag (8 Bytes - char[8])         |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                 Payload (e.g. 226B / 976B / 1376B)            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```
Binary format string: `"!Q d 8s"` (Network byte order: unsigned 64-bit integer, 64-bit float, 8-character string).

### 7.2 Rate Pacing Algorithm
To ensure deterministic transmission without relying on operating system buffer bursts, the inter-packet sleep interval is dynamically computed:
$$\text{Interval} = \frac{\text{Packet Size (Bytes)} \times 8}{\text{Configured Rate (bps)}}$$

### 7.3 Metric Derivations at Receiver
1. **Packet Loss Percentage:**
   $$\text{Loss \%} = \frac{\text{Max(Seq)} - \text{Min(Seq)} + 1 - \text{Packets Received}}{\text{Max(Seq)} - \text{Min(Seq)} + 1} \times 100$$
2. **One-Way Latency:**
   $$\text{Latency} = (T_{\text{receive}} - T_{\text{send}}) \times 1000\text{ ms}$$
3. **RFC 3550 Interarrival Jitter:**
   $$D(i, j) = |(R_j - S_j) - (R_i - S_i)|$$
   $$J_i = J_{i-1} + \frac{|D(i-1, i)| - J_{i-1}}{16}$$

---

## 8. Traffic Classes & Classification

| Traffic Class | UDP Port | Target Rate | Packet Size | Default Priority | Target OVS Queue | Bandwidth Guarantee |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **VOICE** | `5001` | 1.0 Mbps | 250 Bytes | HIGH (200) | Queue 0 | Min 2.5 Mbps, Max 5.0 Mbps |
| **VIDEO** | `5002` | 4.0 Mbps | 1000 Bytes | MEDIUM (150) | Queue 1 | Min 1.5 Mbps, Max 4.0 Mbps |
| **BULK** | `5003` | 6.0 Mbps | 1400 Bytes | LOW (100) | Queue 2 | Min 0.5 Mbps, Max 1.5 Mbps |
| **TOTAL** | — | **11.0 Mbps** | — | — | — | **Bottleneck: 5.0 Mbps** |

---

## 9. OVS QoS Queue Implementation

Queues are established on the bottleneck interface (`s1-eth4`) using Linux Hierarchical Token Bucket (HTB) through `ovs-vsctl`:
```bash
sudo ovs-vsctl -- set port s1-eth4 qos=@newqos \
  -- --id=@newqos create qos type=linux-htb other-config:max-rate=5000000 \
     queues:0=@q0 queues:1=@q1 queues:2=@q2 \
  -- --id=@q0 create queue other-config:min-rate=2500000 other-config:max-rate=5000000 \
  -- --id=@q1 create queue other-config:min-rate=1500000 other-config:max-rate=4000000 \
  -- --id=@q2 create queue other-config:min-rate=500000  other-config:max-rate=1500000
```
- **Queue 0 (Voice):** Guaranteed 2.5 Mbps minimum rate; burstable up to the link ceiling (5.0 Mbps). Packets never starve and experience minimal queuing delay.
- **Queue 1 (Video):** Guaranteed 1.5 Mbps minimum rate; max 4.0 Mbps.
- **Queue 2 (Bulk):** Throttled to a ceiling of 1.5 Mbps, preventing aggressive bulk transfers from monopolizing the link.

To verify active queues on the switch:
```bash
sudo ovs-vsctl list qos
sudo ovs-vsctl list queue
sudo ovs-ofctl -O OpenFlow13 dump-flows s1
```

---

## 10. Empirical Results Comparison

All measurements are obtained from reproducible live network executions in our virtual Mininet environment:

| Scenario | Traffic Class | Offered Load | Throughput | Packet Loss | Avg Latency | Jitter | Jain's Fairness |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline (No QoS)** | VOICE | 1.0 Mbps | **0.40 Mbps** | **59.14%** | **168.53 ms** | 2.92 ms | **0.7581** |
| | VIDEO | 4.0 Mbps | 1.54 Mbps | 60.60% | 168.67 ms | 3.10 ms | |
| | BULK | 6.0 Mbps | 2.39 Mbps | 59.34% | 168.96 ms | 3.04 ms | |
| **Static QoS** | VOICE | 1.0 Mbps | **1.00 Mbps** | **0.00%** | **6.98 ms** | 1.19 ms | **0.7409** |
| | VIDEO | 4.0 Mbps | 2.74 Mbps | 13.16% | 1954.15 ms | 2.32 ms | |
| | BULK | 6.0 Mbps | 0.75 Mbps | 0.00% | 6027.85 ms | 13.51 ms | |
| **Dynamic QoS** | VIDEO (Promoted) | 4.0 Mbps | **2.93 Mbps** | **3.63%** | 1962.83 ms | 848.51 ms | **0.6216** |
| | VOICE (Demoted) | 1.0 Mbps | 0.67 Mbps | 28.19% | 1082.01 ms | 3.42 ms | |
| | BULK | 6.0 Mbps | 0.58 Mbps | 0.00% | 6060.64 ms | 17.84 ms | |

### Key Observations:
1. **Under Baseline (No QoS):** High bulk traffic saturates the link. Voice traffic suffers **59.14% packet loss** and **168.53 ms latency**, rendering real-time voice completely unintelligible.
2. **Under Static QoS:** Voice traffic achieves **100% throughput (1.00 Mbps)**, **0% packet loss**, and latency drops by **95.8% to 6.98 ms**!
3. **Under Dynamic QoS:** Mid-stream promotion of Video from Queue 1 to Queue 0 increases Video throughput to 2.93 Mbps and slashes its packet loss to 3.63% without restarting any sockets.

---

## 11. Jain's Fairness Index Analysis
$$\mathcal{J}(x_1, x_2, \dots, x_n) = \frac{\left( \sum_{i=1}^n x_i \right)^2}{n \cdot \sum_{i=1}^n x_i^2}$$
- **Baseline (No QoS):** $\mathcal{J} = 0.7581$
- **Static QoS:** $\mathcal{J} = 0.7409$
- **Dynamic QoS:** $\mathcal{J} = 0.6216$

> **Critical Note on Fairness:** In traditional best-effort networks, a higher fairness index is seen as optimal. In a **QoS-managed network**, resource allocation is **deliberately unequal**. The lower fairness index under QoS proves that the SDN controller is successfully discriminating between traffic classes according to network policy.

---

## 12. How to Run the Project

### Option A: Run Individual Automated Experiments
```bash
# 1. Baseline Experiment (Without QoS)
./experiments/baseline.sh

# 2. Static QoS Experiment
./experiments/qos_experiment.sh

# 3. Dynamic QoS Experiment
./experiments/dynamic_qos.sh

# 4. Generate Metric Analysis & Graphs
python3 measurements/collect_metrics.py
python3 measurements/analyze_results.py
```

### Option B: Interactive Demonstration
```bash
./scripts/start_project.sh
```

### Option C: Complete Cleanup
```bash
./scripts/cleanup.sh
```

---

## 13. Limitations & Future Scope
- **Limitations:** Focuses on single-bottleneck egress queuing. In multi-switch domains, end-to-end path slicing requires multi-hop flow tagging (e.g. DSCP / MPLS).
- **Future Scope:** Integrating machine learning for automated anomaly detection, reinforcement learning for dynamic queue sizing, and extending the policy engine to P4-programmable data planes.
