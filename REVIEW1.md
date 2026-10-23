# REVIEW 1: Presentation & Evaluation Material

---

## Slide 1: Title Slide
- **Project Title:** QoS Traffic Management System
- **Domain:** Computer Networks / Software-Defined Networking (SDN)
- **Sub-topics:** OpenFlow 1.3, Open vSwitch, Mininet, Ryu SDN Controller, Custom UDP Socket Programming
- **Presenter:** [Your Name / Roll Number]
- **Supervisor/Department:** Department of Computer Science & Engineering

---

## Slide 2: Problem Statement
- **Context:** Heterogeneous applications (voice, video streaming, bulk downloads) share limited-bandwidth bottleneck links.
- **Problem:** In standard best-effort networks, bandwidth-heavy bulk traffic causes buffer exhaustion, leading to packet loss and high latency for interactive real-time flows.
- **Statement:** *"Develop a UDP-based application that generates different classes of traffic and uses SDN to dynamically prioritize selected flows during network congestion."*

---

## Slide 3: Objectives
1. Build custom Python UDP socket applications (rate pacing, sequence numbering, timestamps).
2. Emulate an SDN topology with an explicit 5 Mbps bottleneck link using Mininet and Open vSwitch.
3. Induce controlled network congestion by injecting 11 Mbps aggregate offered traffic ($11 > 5\text{ Mbps}$).
4. Develop an OpenFlow 1.3 Ryu SDN controller for Layer-4 traffic classification.
5. Implement multi-tier OVS HTB QoS queues to protect high-priority packets.
6. Support dynamic runtime policy reconfiguration via REST API without restarting active flows.
7. Quantify performance using Throughput, Loss, Latency, Jitter, and Jain's Fairness Index.

---

## Slide 4: Proposed System
- **Traffic Generation:** 3 distinct UDP classes:
  - **Voice:** Port 5001, Rate = 1.0 Mbps (High Priority)
  - **Video:** Port 5002, Rate = 4.0 Mbps (Medium Priority)
  - **Bulk:** Port 5003, Rate = 6.0 Mbps (Low Priority)
- **Centralized SDN Controller:** Ryu controller inspects Layer-4 destination ports and installs OpenFlow 1.3 `SetQueue` rules.
- **Data Plane Enforcement:** Open vSwitch assigns flows to hardware-level Linux Hierarchical Token Bucket (HTB) queues.
- **Dynamic Controller Interface:** REST API enables programmatic policy re-prioritization on the fly.

---

## Slide 5: System Architecture Diagram
```
[ Application Layer: Python Sockets ]
   h1 (Voice: 10.0.0.1:5001)  -- (1.0 Mbps) --\
   h2 (Video: 10.0.0.2:5002)  -- (4.0 Mbps) --- [ Switch s1 ] === [ 5 Mbps Bottleneck ] === [ Switch s2 ] --- h4 (Server)
   h3 (Bulk : 10.0.0.3:5003)  -- (6.0 Mbps) --/       |                                            |
                                                      |               OpenFlow 1.3                 |
                                                      +---------------------+----------------------+
                                                                            |
                                                             [ Ryu SDN Controller (Brain) ]
                                                             - Flow Classifier (UDP Ports)
                                                             - REST API (/qos/policy)
```

---

## Slide 6: Technologies & Custom Socket Programming
- **Technologies:**
  - **Mininet:** Network emulation and namespace isolation
  - **Open vSwitch (OVS):** Virtual OpenFlow 1.3 switch with HTB queuing
  - **Ryu Controller:** OpenFlow 1.3 control plane framework
  - **Linux TC:** Kernel-level traffic shaping
  - **Python 3:** Application logic and socket programming
- **Custom Socket Programming:**
  - Standard `AF_INET`, `SOCK_DGRAM` raw sockets
  - Binary header format: `!Q d 8s` (Sequence Number, Timestamp, Class Tag)
  - Inter-packet interval pacing for rate control: $\text{Interval} = (\text{Size} \times 8) / \text{Rate}$

---

## Slide 7: Implementation Methodology
- **Phase 1: Environment & Topology Setup:** Mininet 4-host, 2-switch bottleneck topology.
- **Phase 2: Baseline Congestion:** Simultaneous 11 Mbps traffic transmission without QoS.
- **Phase 3: Controller & Queue Configuration:**
  - Configure OVS HTB queues (Queue 0: 2.5–5 Mbps, Queue 1: 1.5–4 Mbps, Queue 2: 0.5–1.5 Mbps).
  - OpenFlow 1.3 rules with `OFPActionSetQueue`.
- **Phase 4: Static QoS Evaluation:** Run identical traffic under QoS enforcement.
- **Phase 5: Dynamic QoS Event:** Reconfigure flow priorities mid-stream via REST API.
- **Phase 6: Analysis & Graphing:** Automated extraction of CSV metrics, fairness calculation, and Matplotlib plots.

---

## Slide 8: Experimental Metrics & Comparative Results
**Empirical Results Summary:**

| Metric | Traffic Class | Baseline (No QoS) | Static QoS | Dynamic QoS |
| :--- | :--- | :---: | :---: | :---: |
| **Packet Loss (%)** | **Voice** | **59.14%** | **0.00%** | 28.19% |
| | Video | 60.60% | 13.16% | **3.63%** |
| | Bulk | 59.34% | 0.00% | 0.00% |
| **Throughput (Mbps)**| **Voice** | 0.40 Mbps | **1.00 Mbps** | 0.67 Mbps |
| | Video | 1.54 Mbps | 2.74 Mbps | **2.93 Mbps** |
| | Bulk | 2.39 Mbps | 0.75 Mbps | 0.58 Mbps |
| **Average Latency** | **Voice** | 168.53 ms | **6.98 ms** | 1082.01 ms |
| **Jain's Fairness** | All Classes | **0.7581** | **0.7409** | **0.6216** |

- **Key Result:** Voice packet loss drops from **59.14% to 0.00%** and latency drops by **95.8% (from 168.5 ms to 6.98 ms)** under Static QoS.

---

## Slide 9: Conclusion & Expected Review Outcome
- **Conclusion:**
  - Successfully demonstrated SDN-driven Quality of Service in a controlled virtual environment.
  - Proved that SDN traffic classification eliminates packet loss on mission-critical flows during network congestion.
  - Successfully demonstrated real-time dynamic policy modification without stopping active UDP flows.
- **Key Takeaway for Examiners:**
  - The project combines custom network socket programming, SDN control plane architecture, OpenFlow 1.3 flow matching, kernel traffic control queues, and quantitative statistical validation.
