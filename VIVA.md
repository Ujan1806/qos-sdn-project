# VIVA.md - Comprehensive Viva Voce Questions & Answers

This document prepares you for technical viva questions on Computer Networks, SDN, OpenFlow, Mininet, OVS, and Socket Programming.

---

### Q1: Why did you choose UDP instead of TCP for traffic generation in this project?
**Answer:**  
TCP has built-in congestion control mechanisms (such as additive increase/multiplicative decrease, flow control, and slow start) that automatically reduce the sending rate upon packet loss, as well as automatic retransmissions. UDP is an unmanaged, connectionless transport protocol that transmits data at whatever rate the application dictates without backoff. Real-time media (VoIP, live video streaming, gaming) relies on UDP because retransmitted stale packets are useless. Using UDP allows us to create deliberate, steady-state network congestion over the bottleneck link and evaluate how the network infrastructure itself (SDN + OVS) prioritizes packets.

---

### Q2: What is Quality of Service (QoS)?
**Answer:**  
Quality of Service (QoS) refers to a suite of networking mechanisms and traffic management techniques designed to provide differentiated guarantees for data flows based on their specific performance requirements. QoS controls packet delay, jitter, bandwidth allocation, and packet loss rate by prioritizing latency-sensitive packets over delay-tolerant background data.

---

### Q3: What is Software-Defined Networking (SDN), and how is it different from traditional networking?
**Answer:**  
In traditional networks, the control plane (the routing and decision logic) and the data plane (the forwarding hardware) are tightly coupled inside each physical router or switch. Each box runs distributed protocols and makes local forwarding decisions.  
In SDN, the control plane is decoupled from the data plane and centralized in a software controller (such as Ryu). The physical or virtual switches become simple forwarding elements that execute flow rules pushed down by the controller via an open standard protocol like OpenFlow.

---

### Q4: What is OpenFlow, and which version did you use?
**Answer:**  
OpenFlow is a standardized Southbound communications interface that defines how an SDN controller communicates with and programs the flow tables of network switches. In this project, we used **OpenFlow 1.3**. OpenFlow 1.3 includes key capabilities required for QoS: multiple flow tables, group tables, meter tables, and the `OFPActionSetQueue` action, which instructs the switch port to enqueue a matched packet into a specific hardware queue.

---

### Q5: Why did you use the Ryu controller framework?
**Answer:**  
Ryu is an open-source, component-based SDN controller framework written in Python. It natively supports OpenFlow versions 1.0 through 1.5, provides an asynchronous event-driven architecture, and includes a built-in WSGI HTTP server, which allowed us to create a REST API endpoint for dynamic runtime policy updates.

---

### Q6: What is Mininet, and what role does it play in this project?
**Answer:**  
Mininet is a network emulator that creates realistic virtual networks on a single Linux kernel. It utilizes Linux network namespaces (`netns`) to isolate virtual hosts, virtual Ethernet pairs (`veth`) to create links, and Open vSwitch as the switching fabric. Mininet allows us to create links with defined bandwidth, propagation delay, and queue sizes via Linux Traffic Control (`tc-netem`).

---

### Q7: What is Open vSwitch (OVS)?
**Answer:**  
Open vSwitch is a production-quality, multi-layer virtual switch designed for hypervisors and Linux virtualization. It implements standard management and control interfaces including OpenFlow and the OVSDB management protocol. In our project, OVS acts as switches `s1` and `s2`, forwarding packets according to OpenFlow 1.3 rules and executing queue-based rate shaping.

---

### Q8: What is a bottleneck link, and why did you intentionally create congestion?
**Answer:**  
A bottleneck is a link in a network path that has the lowest bandwidth or capacity, restricting the overall throughput. In our topology, the inter-switch link connecting `s1` and `s2` is constrained to 5 Mbps, while client access links are 100 Mbps. We intentionally generated 11 Mbps of offered traffic (Voice: 1 Mbps, Video: 4 Mbps, Bulk: 6 Mbps) to overload the 5 Mbps capacity ($11 > 5$). Congestion creates bufferbloat and packet drops, which is necessary to observe and prove the effectiveness of QoS prioritization compared to unmanaged best-effort forwarding.

---

### Q9: How are flows classified by the SDN controller?
**Answer:**  
Traffic classification is performed at Layer-4 based on the UDP destination port:
- UDP Port `5001` $\to$ **VOICE** (High Priority)
- UDP Port `5002` $\to$ **VIDEO** (Medium Priority)
- UDP Port `5003` $\to$ **BULK** (Low Priority)  
The controller installs flow entries matching `ip_proto=17` (UDP) and `udp_dst=<port>`.

---

### Q10: How are QoS queues implemented in Open vSwitch and Linux?
**Answer:**  
Queues are implemented using the Linux kernel's **Hierarchical Token Bucket (HTB)** queuing discipline (`sch_htb`) configured via `ovs-vsctl`:
1. A root QoS record is attached to the bottleneck egress port (`s1-eth4`) with `max-rate=5000000` (5 Mbps).
2. Three sub-queues are created with distinct minimum guaranteed rates (`min-rate`) and burst ceilings (`max-rate`):
   - Queue 0 (Voice): Min 2.5 Mbps, Max 5.0 Mbps.
   - Queue 1 (Video): Min 1.5 Mbps, Max 4.0 Mbps.
   - Queue 2 (Bulk): Min 0.5 Mbps, Max 1.5 Mbps.
3. When OpenFlow applies `OFPActionSetQueue(queue_id)`, the kernel sets the packet's `skb->priority` to direct the packet into that specific HTB class.

---

### Q11: How is packet loss measured in your Python socket program?
**Answer:**  
Each transmitted packet contains an 8-byte unsigned integer sequence number ($0, 1, 2, \dots$) packed into the packet header. The receiver tracks all received sequence numbers. By computing:
$$\text{Expected Packets} = \text{Max(Seq)} - \text{Min(Seq)} + 1$$
$$\text{Packets Lost} = \text{Expected Packets} - \text{Packets Received}$$
$$\text{Packet Loss \%} = \frac{\text{Packets Lost}}{\text{Expected Packets}} \times 100$$
This accurately detects missing and dropped packets even under heavy packet loss.

---

### Q12: How is latency and jitter measured?
**Answer:**  
- **Latency (One-Way Delay):** The sender timestamps the packet at the instant of `sendto()` using `time.time()`. Upon receiving the packet with `recvfrom()`, the receiver records the arrival timestamp:
  $$\text{Latency} = (T_{\text{recv}} - T_{\text{send}}) \times 1000\text{ ms}$$
- **Jitter:** Jitter represents the statistical variance in packet transit times. It is calculated using the RFC 3550 standard exponential moving average formula:
  $$\Delta = |(R_j - S_j) - (R_{i} - S_{i})|$$
  $$J = J + \frac{\Delta - J}{16}$$

---

### Q13: What is Jain's Fairness Index, and why is a lower fairness index acceptable under QoS?
**Answer:**  
Jain's Fairness Index ($\mathcal{J}$) is a metric defined by Raj Jain in 1984 to measure the equality of resource sharing among $n$ flows:
$$\mathcal{J}(x_1, \dots, x_n) = \frac{(\sum_{i=1}^n x_i)^2}{n \sum_{i=1}^n x_i^2}$$
Values range from $1/n$ (worst-case unfairness) to $1.0$ (complete equality).  
In best-effort networks, $\mathcal{J} \to 1.0$ is desired. **However, in a QoS system, flows have deliberately unequal priorities.** Voice traffic must receive its full rate with 0% loss, while Bulk data must be restricted. The drop in Jain's index from 0.7581 (No QoS) to 0.7409 (Static QoS) and 0.6216 (Dynamic QoS) quantitatively proves that the SDN controller is intentionally enforcing policy discrimination.

---

### Q14: What is dynamically changing in your Dynamic QoS experiment?
**Answer:**  
While all UDP senders and receivers are actively running, an external REST call `POST /qos/policy` is issued to the controller. The controller immediately sends an OpenFlow `OFPFlowMod` command to Switch `s1` to modify the flow table in real time:
- The rule for Video (Port 5002) is promoted from Queue 1 to Queue 0.
- The rule for Voice (Port 5001) is demoted from Queue 0 to Queue 1.  
This policy modification occurs in the switch data plane without restarting the applications or tearing down network connections.

---

### Q15: What is the difference between the Control Plane and the Data Plane?
**Answer:**  
- **Control Plane:** The decision-making layer that computes routes, classifies flows, enforces security, and dictates policy (e.g., Ryu SDN controller).
- **Data Plane (Forwarding Plane):** The high-speed packet-forwarding layer that inspects packet headers and applies flow actions (forwarding, queueing, dropping, header rewrite) specified by the control plane (e.g., Open vSwitch and Linux kernel).

---

### Q16: What happens if the SDN controller crashes?
**Answer:**  
In Open vSwitch, the `fail-mode` can be set to either `secure` or `standalone`:
- In **standalone mode**, if the controller disconnects, OVS falls back to behaving like a standard legacy Layer-2 learning switch.
- In **secure mode**, OVS continues to execute existing flows until their idle/hard timeouts expire, and drops any new unmatched packets until the controller reconnects.
