# REPRODUCIBILITY GUIDE: QoS Traffic Management System

This document provides the complete specification required to independently reproduce every result, graph, and metric of the **QoS Traffic Management System** project.

---

## 1. Network Topology Specification

### 1.1 Structural Topology
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
                 Queue Limit = 100 packets
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

### 1.2 Node & Link Parameters
| Node / Link | Type / Protocol | IP / Subnet | MAC Address | Bandwidth | Delay | Max Queue |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| **`h1`** | Voice Client | `10.0.0.1/24` | `00:00:00:00:00:01` | — | — | — |
| **`h2`** | Video Client | `10.0.0.2/24` | `00:00:00:00:00:02` | — | — | — |
| **`h3`** | Bulk Client | `10.0.0.3/24` | `00:00:00:00:00:03` | — | — | — |
| **`h4`** | Traffic Server | `10.0.0.4/24` | `00:00:00:00:00:04` | — | — | — |
| **`s1`** | Ingress Switch | OpenFlow 1.3 | — | — | — | — |
| **`s2`** | Egress Switch | OpenFlow 1.3 | — | — | — | — |
| **`h1 - s1`** | Access Link | — | — | 100 Mbps | 1 ms | Default |
| **`h2 - s1`** | Access Link | — | — | 100 Mbps | 1 ms | Default |
| **`h3 - s1`** | Access Link | — | — | 100 Mbps | 1 ms | Default |
| **`s1 - s2`** | **Bottleneck Link** | — | — | **5.0 Mbps** | **10 ms** | **100 pkts** |
| **`s2 - h4`** | Access Link | — | — | 100 Mbps | 1 ms | Default |

* **Topology File:** `topology/qos_topology.py`

---

## 2. Source Code Architecture

| Component | File Path | Function / Responsibility |
| :--- | :--- | :--- |
| **Network Topology** | `topology/qos_topology.py` | Mininet dual-switch topology with 5 Mbps bottleneck via `TCLink`. |
| **SDN Controller** | `controller/qos_controller.py` | Ryu OpenFlow 1.3 controller with UDP port classification & REST API. |
| **UDP Sender** | `traffic/udp_sender.py` | Custom socket traffic generator with sequence numbering, timestamps, and rate pacing. |
| **UDP Receiver** | `traffic/udp_receiver.py` | Custom socket receiver measuring loss %, throughput, one-way delay, and RFC 3550 jitter. |
| **Experiment Runner**| `experiments/run_experiment.py` | Automated orchestrator for Baseline, Static QoS, and Dynamic QoS runs. |
| **Metrics Collector**| `measurements/collect_metrics.py`| Merges CSV results and tabulates Jain's Fairness Index. |
| **Fairness Engine** | `measurements/calculate_fairness.py` | Calculates Jain's Fairness Index $\mathcal{J} = (\sum x_i)^2 / (n \sum x_i^2)$. |
| **Graph Generator** | `measurements/analyze_results.py` | Generates 6 comparative Matplotlib plots in `plots/`. |

---

## 3. Configuration

### 3.1 Traffic Class Configuration (`traffic/traffic_config.py`)
```python
TRAFFIC_CLASSES = {
    'VOICE': {
        'name': 'VOICE',
        'port': 5001,
        'rate_mbps': 1.0,
        'priority': 'HIGH',
        'queue_id': 0,
        'packet_size': 250   # Small VoIP packets
    },
    'VIDEO': {
        'name': 'VIDEO',
        'port': 5002,
        'rate_mbps': 4.0,
        'priority': 'MEDIUM',
        'queue_id': 1,
        'packet_size': 1000  # Medium video frames
    },
    'BULK': {
        'name': 'BULK',
        'port': 5003,
        'rate_mbps': 6.0,
        'priority': 'LOW',
        'queue_id': 2,
        'packet_size': 1400  # Large file transfer chunks
    }
}
BOTTLENECK_BW_MBPS = 5.0
SERVER_IP = "10.0.0.4"
```

### 3.2 OVS Hierarchical Token Bucket (HTB) Queues (`qos/setup_queues.sh`)
```bash
sudo ovs-vsctl -- set port s1-eth4 qos=@newqos \
  -- --id=@newqos create qos type=linux-htb other-config:max-rate=5000000 \
     queues:0=@q0 queues:1=@q1 queues:2=@q2 \
  -- --id=@q0 create queue other-config:min-rate=2500000 other-config:max-rate=5000000 \
  -- --id=@q1 create queue other-config:min-rate=1500000 other-config:max-rate=4000000 \
  -- --id=@q2 create queue other-config:min-rate=500000  other-config:max-rate=1500000
```

---

## 4. Test Cases

| Test Case ID | Test Case Name | Traffic Injected | Active Mechanism | Pass Criteria |
| :---: | :--- | :--- | :--- | :--- |
| **TC-01** | Basic L3 Reachability | ICMP Ping (h1..h4) | Default Switching | `0% dropped (12/12 received)` on `pingall`. |
| **TC-02** | Unmanaged Congestion (Baseline) | 11.0 Mbps Aggregate Load (Voice 1M + Video 4M + Bulk 6M) | FIFO Bottleneck Queuing (No QoS) | Bottleneck saturates; Voice loses >50% packets; Voice latency >150 ms. |
| **TC-03** | Static SDN QoS Prioritization | 11.0 Mbps Aggregate Load | OpenFlow 1.3 `SetQueue` + OVS HTB | Voice achieves 100% throughput (1.0 Mbps), **0.00% packet loss**, and latency <10 ms. |
| **TC-04** | Dynamic Runtime Policy Modification | 11.0 Mbps Aggregate Load | REST API call at $T=6\text{s}$ to swap queues | Video is promoted to Queue 0; Video throughput increases to >2.8 Mbps without stopping applications. |
| **TC-05** | Fairness & Metrics Validation | Processed CSV Logs | Jain's Fairness Formula | Jain's Index calculated and 6 graphical plots generated in `plots/`. |

---

## 5. Step-by-Step Instructions to Reproduce the Results

### Step 5.1: Prepare Environment
```bash
cd ~/qos-sdn-project
./scripts/cleanup.sh
```

### Step 5.2: Execute Test Case 1 (Topology Reachability)
```bash
sudo python3 topology/qos_topology.py --standalone
# Inside Mininet CLI:
mininet> pingall
mininet> net
mininet> exit
./scripts/cleanup.sh
```

### Step 5.3: Execute Test Case 2 (Baseline Congestion)
```bash
sudo ./experiments/baseline.sh
```
*Expected Result:* `results/baseline_results.csv` generated. Voice suffers ~59% loss, ~168 ms latency.

### Step 5.4: Execute Test Case 3 (Static SDN QoS)
```bash
sudo ./experiments/qos_experiment.sh
```
*Expected Result:* `results/qos_results.csv` generated. Voice drops to **0.00% loss**, throughput hits 1.00 Mbps, latency plummets to ~6 ms.

### Step 5.5: Execute Test Case 4 (Dynamic QoS Re-prioritization)
```bash
sudo ./experiments/dynamic_qos.sh
```
*Expected Result:* `results/dynamic_results.csv` generated. Video promoted mid-stream at $T=6.0\text{s}$; Video throughput surges to ~2.9 Mbps.

### Step 5.6: Compile Consolidated Table & Generate Graphs
```bash
python3 measurements/collect_metrics.py
python3 measurements/analyze_results.py
```
*Expected Result:*
1. Full comparative terminal table printed with Jain's Fairness Index.
2. `plots/` populated with 6 publication-ready PNG graphs:
   - `throughput_comparison.png`
   - `packet_loss_comparison.png`
   - `latency_comparison.png`
   - `jitter_comparison.png`
   - `fairness_index.png`
   - `qos_comprehensive_overview.png`

### Step 5.7: Clean Up Environment
```bash
./scripts/cleanup.sh
```
The environment is reset back to pristine condition.
