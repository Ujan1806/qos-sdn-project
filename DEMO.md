# DEMO.md - Step-by-Step Live Demonstration Guide

This guide provides an exact, command-by-command procedure for presenting the **QoS Traffic Management System** in a live lab demonstration or examiner review.

---

## Prerequisites Check
Ensure the terminal is open in the project root:
```bash
cd ~/qos-sdn-project
```

Ensure no previous virtual network instances are active:
```bash
./scripts/cleanup.sh
```

---

## Demonstration Workflow Overview
1. **Demo Part 1:** Show clean environment and inspect topology.
2. **Demo Part 2:** Run **Baseline Experiment** (Unmanaged Congestion). Show high packet loss and latency on Voice traffic.
3. **Demo Part 3:** Run **Static QoS Experiment**. Show 0% loss on Voice and guaranteed bandwidth.
4. **Demo Part 4:** Run **Dynamic QoS Experiment**. Show real-time policy switching mid-stream via REST API.
5. **Demo Part 5:** Calculate Jain's Fairness Index and generate analytical plots.
6. **Demo Part 6:** Inspect OpenFlow flow tables and OVS queues.

---

## Step-by-Step Demonstration Script

### Step 1: Demonstrate Baseline (No QoS) Congestion
Explain to the evaluator:
> *"First, we will demonstrate what happens in a standard best-effort network without QoS. 3 hosts generate 11 Mbps total traffic into a 5 Mbps bottleneck link."*

Run:
```bash
./experiments/baseline.sh
```

**What to look for in the output:**
```
=======================================================
             BASELINE MEASURED RESULTS            
=======================================================
timestamp,traffic_class,port,packets_received,packets_lost,loss_percent,throughput_mbps,avg_latency_ms
... VOICE, 5001, ..., loss_percent: ~59%, throughput: 0.40 Mbps, latency: ~168 ms
... VIDEO, 5002, ..., loss_percent: ~60%, throughput: 1.54 Mbps, latency: ~168 ms
... BULK,  5003, ..., loss_percent: ~59%, throughput: 2.39 Mbps, latency: ~168 ms
```

**Key Takeaway to Explain:**
- Voice traffic was supposed to get 1.0 Mbps, but only received **0.40 Mbps**.
- Packet loss is **~59%**, which makes real-time audio completely glitchy and unusable.
- Bulk traffic took away the majority of bandwidth (2.39 Mbps).

---

### Step 2: Demonstrate Static SDN QoS Prioritization
Explain to the evaluator:
> *"Now we activate our Ryu OpenFlow 1.3 controller and configure 3-tier HTB QoS queues on the bottleneck switch port. Voice is mapped to Queue 0 (High Priority)."*

Run:
```bash
./experiments/qos_experiment.sh
```

**What to look for in the output:**
```
=======================================================
             QOS MEASURED RESULTS            
=======================================================
timestamp,traffic_class,port,packets_received,packets_lost,loss_percent,throughput_mbps,avg_latency_ms
... VOICE, 5001, packets_received: 6000, loss_percent: 0.00%, throughput: 1.00 Mbps, latency: 6.98 ms
... VIDEO, 5002, ..., loss_percent: 13.16%, throughput: 2.74 Mbps, latency: ~1950 ms
... BULK,  5003, ..., loss_percent: 0.00%, throughput: 0.75 Mbps, latency: ~6000 ms
```

**Key Takeaways to Highlight:**
1. **Voice Packet Loss dropped from 59.14% down to 0.00%!**
2. **Voice Throughput achieved full target rate (1.00 Mbps).**
3. **Voice Latency decreased from 168.53 ms to 6.98 ms (a 95.8% reduction in latency!).**
4. Bulk traffic is strictly throttled to 0.75 Mbps, preventing starvation of interactive traffic.

---

### Step 3: Demonstrate Dynamic QoS Modification (Mid-Flow)
Explain to the evaluator:
> *"In this stage, traffic starts running with the standard QoS policy. At T = 6 seconds, while traffic is actively streaming, an external event triggers a dynamic REST call to the controller. The controller reconfigures switch flow rules in real-time to promote Video to Queue 0 and demote Voice to Queue 1, without stopping the sender or receiver applications."*

Run:
```bash
./experiments/dynamic_qos.sh
```

**What to look for in the live logs:**
```
[*] Generating 11 Mbps Traffic (VOICE=1M, VIDEO=4M, BULK=6M for 14s)...
[*] Traffic running... Dynamic policy will trigger at T=6.0s...

[!] >>> DYNAMIC EVENT TRIGGERED: Promoting VIDEO (5002) to Queue 0 & Demoting VOICE (5001) to Queue 1 <<<
[+] Dynamic QoS REST Response: {"status": "SUCCESS", "message": "QoS policy updated."}
[*] Continuing traffic under new dynamic policy for 11.0s...
```

**What to look for in the results:**
- Video packet loss dropped from 13.16% down to **3.63%**, and its throughput increased to **2.93 Mbps**.
- Voice packet loss increased to 28.19% as it yielded bandwidth to the newly prioritized Video stream.

---

### Step 4: Inspect Active OpenFlow Rules and Hardware Queues
To prove to the examiner that this is genuine SDN and hardware-level queuing (not simulated numbers), show the OpenFlow and OVS tables:

#### 1. Show OVS QoS Queues on the Bottleneck Switch (`s1`):
```bash
sudo ovs-vsctl list qos
sudo ovs-vsctl list queue
```

#### 2. Show Active OpenFlow 1.3 Flow Entries:
```bash
sudo ovs-ofctl -O OpenFlow13 dump-flows s1
```
Point out the flow entries showing `actions=set_queue:0,output:4` for `udp_dst=5001`, `actions=set_queue:1,output:4` for `udp_dst=5002`, etc.

---

### Step 5: Generate and Show Analytical Graphs
Run the analysis scripts:
```bash
python3 measurements/collect_metrics.py
python3 measurements/analyze_results.py
```

Display the generated plots:
```bash
ls -lh plots/
```
You can view the plots using any image viewer:
- `plots/qos_comprehensive_overview.png` — 4-panel dashboard of Throughput, Loss, Latency, and Jitter.
- `plots/throughput_comparison.png` — Grouped bar chart comparing rates across all 3 scenarios.
- `plots/packet_loss_comparison.png` — Zero loss visualization for Voice under QoS.
- `plots/fairness_index.png` — Jain's Fairness Index across experiments.

---

### Step 6: Clean Up After Demo
```bash
./scripts/cleanup.sh
```
The environment is immediately returned to a clean, pristine state.
