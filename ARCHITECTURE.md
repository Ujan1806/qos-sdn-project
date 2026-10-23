# ARCHITECTURE.md - System Design & Engineering Architecture

## 1. System Overview
The **QoS Traffic Management System** implements an end-to-end Software-Defined Network (SDN) solution to resolve flow contention and buffer exhaustion on resource-constrained bottleneck links. The system decouples network intelligence (the SDN Control Plane) from packet forwarding hardware (the SDN Data Plane), enabling granular traffic classification and real-time policy adjustments.

---

## 2. Decoupled SDN Architecture

```
+===================================================================================+
|                               MANAGEMENT PLANE                                    |
|   - Network Administrator Policy Definition (traffic_config.py)                   |
|   - Dynamic QoS Reconfiguration REST Client (urllib HTTP POST)                     |
+===================================================================================+
                                         |
                                  REST / HTTP (Port 8080)
                                         v
+===================================================================================+
|                          CONTROL PLANE (Ryu Framework)                            |
|                                                                                   |
|   +--------------------------+          +-------------------------------------+   |
|   |   QoSRestController      | <------> |          QoSController (Core)       |   |
|   |  - Handles /qos/policy   |          |  - OpenFlow 1.3 Handshake Engine    |   |
|   |  - Parses JSON requests  |          |  - L2 MAC Learning & Forwarding     |   |
|   +--------------------------+          |  - Flow Classifier (UDP Dst Port)   |   |
|                                         |  - Proactive QoS Rule Dispatcher    |   |
|                                         +-------------------------------------+   |
+===================================================================================+
                                         |
                               OpenFlow 1.3 (TCP 6653)
                                         v
+===================================================================================+
|                           DATA PLANE (Open vSwitch & Linux TC)                    |
|                                                                                   |
|      [Switch s1 (DPID 1)]                               [Switch s2 (DPID 2)]      |
|  +--------------------------+                      +--------------------------+   |
|  | - Table 0 Flow Entries:  |                      | - Table 0 Flow Entries:  |   |
|  |   * Port 5001 -> SetQ(0) |                      |   * Forward to h4 (Port 1|   |
|  |   * Port 5002 -> SetQ(1) |                      |   * Table-miss -> Ryu    |   |
|  |   * Port 5003 -> SetQ(2) |                      +--------------------------+   |
|  |   * Table-miss -> Ryu    |                                    ^                |
|  +--------------------------+                                    |                |
|               |                                                  |                |
|               v                                                  |                |
|     [ Port s1-eth4 Egress ] -------------------------------------+                |
|     Linux HTB root qdisc: max-rate = 5 Mbps                                       |
|       * Queue 0: Min 2.5 Mbps, Max 5.0 Mbps (Voice)                               |
|       * Queue 1: Min 1.5 Mbps, Max 4.0 Mbps (Video)                               |
|       * Queue 2: Min 0.5 Mbps, Max 1.5 Mbps (Bulk)                                |
+===================================================================================+
                                         ^
                                         |
+===================================================================================+
|                         APPLICATION LAYER (Python Sockets)                        |
|   - h1: UDP Sender (VOICE: 1.0 Mbps, Port 5001, 250B)                             |
|   - h2: UDP Sender (VIDEO: 4.0 Mbps, Port 5002, 1000B)                            |
|   - h3: UDP Sender (BULK:  6.0 Mbps, Port 5003, 1400B)                            |
|   - h4: UDP Multi-Port Receiver (Ports 5001, 5002, 5003)                          |
+===================================================================================+
```

---

## 3. Data Plane Pipeline & Flow Classification

### 3.1 Flow Match and Action Specification
Classification is performed at Layer-4 based on the UDP destination port:

#### Switch `s1` (Ingress & Classification Switch, DPID 1):
1. **VOICE Flow Entry:**
   - **Match:** `eth_type=0x0800` (IPv4), `ip_proto=17` (UDP), `ipv4_dst=10.0.0.4`, `udp_dst=5001`
   - **Priority:** `200`
   - **Instructions:** `APPLY_ACTIONS: [SetQueue(0), Output(port 4)]`
2. **VIDEO Flow Entry:**
   - **Match:** `eth_type=0x0800`, `ip_proto=17`, `ipv4_dst=10.0.0.4`, `udp_dst=5002`
   - **Priority:** `150`
   - **Instructions:** `APPLY_ACTIONS: [SetQueue(1), Output(port 4)]`
3. **BULK Flow Entry:**
   - **Match:** `eth_type=0x0800`, `ip_proto=17`, `ipv4_dst=10.0.0.4`, `udp_dst=5003`
   - **Priority:** `100`
   - **Instructions:** `APPLY_ACTIONS: [SetQueue(2), Output(port 4)]`
4. **Table-Miss Rule:**
   - **Match:** `*` (Any packet)
   - **Priority:** `0`
   - **Instructions:** `APPLY_ACTIONS: [Output(OFPP_CONTROLLER)]`

#### Switch `s2` (Egress Switch, DPID 2):
- Proactively forwards all classified UDP streams matching `ipv4_dst=10.0.0.4` directly out port 1 (`s2-eth1` -> `h4`) with zero packet-in latency.

---

## 4. OVS Hierarchical Token Bucket (HTB) Queuing Architecture

When an OpenFlow flow assigns `SetQueue(id)`, OVS tags the Linux socket buffer (`sk_buff`) with a `priority` corresponding to the queue ID. The Linux kernel's `sch_htb` traffic control module maps this priority to a specific HTB class:

```
                      +---------------------------------------+
                      |     Root HTB Qdisc on s1-eth4         |
                      |        Rate Limit = 5.0 Mbps          |
                      +---------------------------------------+
                                          |
                +-------------------------+-------------------------+
                |                                                   |
                v                                                   v
+-------------------------------+                   +-------------------------------+
|     HTB Class 1:1 (Queue 0)   |                   |     HTB Class 1:3 (Queue 2)   |
|   Guaranteed: 2.5 Mbps        |                   |   Guaranteed: 0.5 Mbps        |
|   Ceiling   : 5.0 Mbps        |                   |   Ceiling   : 1.5 Mbps        |
|   Traffic   : VOICE           |                   |   Traffic   : BULK            |
+-------------------------------+                   +-------------------------------+
                |                                                   |
                v                                                   v
+-------------------------------+                   +-------------------------------+
|     HTB Class 1:2 (Queue 1)   |                   |   Restricted Bandwidth        |
|   Guaranteed: 1.5 Mbps        |                   |   Excess packets dropped      |
|   Ceiling   : 4.0 Mbps        |                   |   or buffered to avoid        |
|   Traffic   : VIDEO           |                   |   starving Voice/Video        |
+-------------------------------+                   +-------------------------------+
```

---

## 5. Socket Programming Architecture

### 5.1 Binary Protocol Framing
`udp_sender.py` formats packets using Python's `struct` module:
- `struct.pack("!Q d 8s", seq, send_time, class_tag) + payload`
  - `!Q`: 64-bit Big-Endian unsigned integer sequence number.
  - `d`: 64-bit IEEE 754 double-precision floating-point epoch timestamp.
  - `8s`: 8-byte ASCII string identifying the traffic class (`VOICE\x00\x00\x00`).
  - Total Header Size = 24 Bytes.

### 5.2 Mathematical Latency and Jitter Models
- **One-Way Delay ($D_i$):**
  $$D_i = T_{\text{recv}}(i) - T_{\text{send}}(i)$$
- **RFC 3550 Interarrival Jitter ($J$):**
  For packet $i$ arriving at $R_i$ with send time $S_i$:
  $$\Delta_i = |(R_i - S_i) - (R_{i-1} - S_{i-1})|$$
  $$J_i = J_{i-1} + \frac{\Delta_i - J_{i-1}}{16}$$

---

## 6. Dynamic Policy Update State Machine

```
                      +-----------------------------+
                      |    Normal QoS Operation     |
                      |  Voice -> Q0 (High)         |
                      |  Video -> Q1 (Med)          |
                      |  Bulk  -> Q2 (Low)          |
                      +-----------------------------+
                                     |
                                     | Event: Emergency Video Streaming
                                     | REST POST to /qos/policy
                                     v
                      +-----------------------------+
                      | Controller Receives REST    |
                      | JSON: {5002: Q0, 5001: Q1}  |
                      +-----------------------------+
                                     |
                                     | Dispatches OpenFlow 1.3 OFPFlowMod
                                     v
                      +-----------------------------+
                      | Switch s1 Flow Table Update |
                      | Port 5002 -> SetQueue(0)    |
                      | Port 5001 -> SetQueue(1)    |
                      +-----------------------------+
                                     |
                                     v
                      +-----------------------------+
                      | Real-Time Prioritization    |
                      | Video loss drops to 3.6%    |
                      | Zero Application Restarts   |
                      +-----------------------------+
```
