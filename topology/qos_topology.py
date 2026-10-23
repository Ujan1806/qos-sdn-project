#!/usr/bin/env python3
"""
qos_topology.py - 2-Switch Bottleneck Topology with QoS Support
"""
import sys
import time
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel, info

class QoSTopo(Topo):
    def build(self):
        # 1. Add Switches (OpenFlow 1.3)
        s1 = self.addSwitch('s1', protocols='OpenFlow13')
        s2 = self.addSwitch('s2', protocols='OpenFlow13')

        # 2. Add Hosts with static IP and MAC addresses
        h1 = self.addHost('h1', ip='10.0.0.1/24', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', ip='10.0.0.2/24', mac='00:00:00:00:00:02')
        h3 = self.addHost('h3', ip='10.0.0.3/24', mac='00:00:00:00:00:03')
        h4 = self.addHost('h4', ip='10.0.0.4/24', mac='00:00:00:00:00:04')

        # 3. Add Fast Access Links (100 Mbps, 1ms delay)
        self.addLink(h1, s1, bw=100, delay='1ms', cls=TCLink)
        self.addLink(h2, s1, bw=100, delay='1ms', cls=TCLink)
        self.addLink(h3, s1, bw=100, delay='1ms', cls=TCLink)
        self.addLink(h4, s2, bw=100, delay='1ms', cls=TCLink)

        # 4. Add Bottleneck Link between s1 and s2 (5 Mbps, 10ms delay)
        self.addLink(s1, s2, bw=5, delay='10ms', max_queue_size=100, cls=TCLink)

def run(standalone=False, no_cli=False):
    topo = QoSTopo()
    if standalone:
        info("*** Starting Mininet in STANDALONE mode (Default Controller) ***\n")
        net = Mininet(topo=topo, link=TCLink, switch=OVSSwitch)
    else:
        info("*** Starting Mininet in SDN mode (Connecting to Remote Controller 127.0.0.1:6653) ***\n")
        c0 = RemoteController('c0', ip='127.0.0.1', port=6653)
        net = Mininet(topo=topo, link=TCLink, switch=OVSSwitch, controller=c0)

    net.start()
    info("*** Topology started! Testing initial pingAll ***\n")
    net.pingAll()
    
    if no_cli:
        info("*** Running in daemon mode without CLI. Keeping network alive... ***\n")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    else:
        CLI(net)
        
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    standalone_mode = '--standalone' in sys.argv
    no_cli_mode = '--no-cli' in sys.argv
    run(standalone=standalone_mode, no_cli=no_cli_mode)
