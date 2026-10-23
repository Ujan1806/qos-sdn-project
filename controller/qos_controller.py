#!/usr/bin/env python3
"""
qos_controller.py - OpenFlow 1.3 QoS & Dynamic Policy Ryu Controller
===================================================================
Features:
1. OpenFlow 1.3 Switch handshake and Table-Miss rule.
2. Layer-2 Learning for general traffic (ARP, ICMP, replies).
3. Pre-installed proactive QoS Classification on Bottleneck Switch s1:
     - Port 5001 (VOICE): High Priority -> Queue 0 (Min 2.5 Mbps, Max 5.0 Mbps)
     - Port 5002 (VIDEO): Medium Priority -> Queue 1 (Min 1.5 Mbps, Max 4.0 Mbps)
     - Port 5003 (BULK) : Low Priority -> Queue 2 (Min 0.5 Mbps, Max 1.5 Mbps)
4. Pre-installed egress forwarding on Switch s2 to Server h4.
5. REST API for Dynamic QoS Policy Switching on-the-fly.
"""

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, udp, ether_types
from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from webob import Response
import json

QOS_API_INSTANCE_NAME = 'qos_api_app'
URL = '/qos/policy'

# Default QoS Policy: UDP port -> queue_id & priority
DEFAULT_POLICY = {
    5001: {'name': 'VOICE', 'queue_id': 0, 'priority': 200},
    5002: {'name': 'VIDEO', 'queue_id': 1, 'priority': 150},
    5003: {'name': 'BULK',  'queue_id': 2, 'priority': 100}
}

class QoSController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'wsgi': WSGIApplication}

    def __init__(self, *args, **kwargs):
        super(QoSController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.datapaths = {}
        self.policy = dict(DEFAULT_POLICY)
        
        wsgi = kwargs.get('wsgi')
        if wsgi:
            wsgi.register(QoSRestController, {QOS_API_INSTANCE_NAME: self})
        self.logger.info("[*] QoSController initialized with OpenFlow 1.3.")

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid = datapath.id
        self.datapaths[dpid] = datapath

        self.logger.info(f"[*] Switch connected: DPID={dpid}")

        # Install Table-Miss flow entry (send unmatched packets to controller for L2 learning)
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, priority=0, match=match, actions=actions)

        # Proactively install QoS rules on s1 (DPID 1) and egress rules on s2 (DPID 2)
        if dpid == 1:
            self.install_s1_qos_rules(datapath)
        elif dpid == 2:
            self.install_s2_forwarding_rules(datapath)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None, idle_timeout=0, hard_timeout=0):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath, buffer_id=buffer_id if buffer_id is not None else ofproto.OFP_NO_BUFFER,
            priority=priority, match=match,
            idle_timeout=idle_timeout, hard_timeout=hard_timeout,
            instructions=inst
        )
        datapath.send_msg(mod)

    def install_s1_qos_rules(self, datapath):
        """Installs QoS classification flow rules on Switch s1 targeting bottleneck port 4."""
        parser = datapath.ofproto_parser
        out_port = 4  # s1-eth4 connects to s2

        self.logger.info("[*] Installing QoS Classification Flow Rules on Switch s1 (DPID 1)...")
        for port, rule in self.policy.items():
            match = parser.OFPMatch(
                eth_type=ether_types.ETH_TYPE_IP,
                ipv4_dst='10.0.0.4',
                ip_proto=17,  # UDP
                udp_dst=port
            )
            actions = [
                parser.OFPActionSetQueue(rule['queue_id']),
                parser.OFPActionOutput(out_port)
            ]
            self.add_flow(datapath, priority=rule['priority'], match=match, actions=actions)
            self.logger.info(f"    -> UDP Port {port} ({rule['name']}) => Queue {rule['queue_id']} -> Port {out_port} (Priority: {rule['priority']})")

    def install_s2_forwarding_rules(self, datapath):
        """Installs direct egress forwarding on Switch s2 targeting Server h4 (port 1)."""
        parser = datapath.ofproto_parser
        out_port = 1  # s2-eth1 connects to h4

        self.logger.info("[*] Installing UDP Forwarding Rules on Switch s2 (DPID 2) -> Server h4...")
        for port, rule in self.policy.items():
            match = parser.OFPMatch(
                eth_type=ether_types.ETH_TYPE_IP,
                ipv4_dst='10.0.0.4',
                ip_proto=17,
                udp_dst=port
            )
            actions = [parser.OFPActionOutput(out_port)]
            self.add_flow(datapath, priority=rule['priority'], match=match, actions=actions)

    def update_policy(self, new_policy):
        """Dynamically updates the QoS policy and rewires OpenFlow flow rules in real-time."""
        self.logger.info(f"[*] Dynamically modifying QoS policy: {new_policy}")
        self.policy.update(new_policy)
        if 1 in self.datapaths:
            self.install_s1_qos_rules(self.datapaths[1])
            self.logger.info("[+] Dynamic QoS rules successfully updated in Switch s1 data plane!")

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """Standard L2 learning for ARP and non-QoS traffic."""
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        dst = eth.dst
        src = eth.src
        dpid = datapath.id

        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            self.add_flow(datapath, priority=10, match=match, actions=actions, idle_timeout=30)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(
            datapath=datapath, buffer_id=msg.buffer_id,
            in_port=in_port, actions=actions, data=data
        )
        datapath.send_msg(out)


class QoSRestController(ControllerBase):
    """REST API Controller for Dynamic QoS Policy updates."""
    def __init__(self, req, link, data, **config):
        super(QoSRestController, self).__init__(req, link, data, **config)
        self.qos_app = data[QOS_API_INSTANCE_NAME]

    @route('qos', URL, methods=['GET'])
    def get_policy(self, req, **kwargs):
        body = json.dumps(self.qos_app.policy).encode('utf-8')
        return Response(content_type='application/json', body=body)

    @route('qos', URL, methods=['POST'])
    def set_policy(self, req, **kwargs):
        try:
            new_policy = req.json if hasattr(req, 'json') and req.json else json.loads(req.body.decode('utf-8'))
            formatted_policy = {int(k): v for k, v in new_policy.items()}
            self.qos_app.update_policy(formatted_policy)
            res_body = json.dumps({'status': 'SUCCESS', 'message': 'QoS policy updated.'}).encode('utf-8')
            return Response(content_type='application/json', body=res_body)
        except Exception as e:
            self.qos_app.logger.error(f"Error updating policy: {e}")
            err_body = f"Error updating policy: {str(e)}".encode('utf-8')
            return Response(status=400, body=err_body)
