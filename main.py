from mininet.net import Mininet
from mininet.node import OVSController
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.topo import Topo

class StarTopo(Topo):
    def build(self):
        # Add a central switch
        switch = self.addSwitch('s1')
        
        # Add 6 hosts and connect them to the switch
        for h in range(7):
            host = self.addHost(f'h{h+1}')
            self.addLink(host, switch)

class SnowFlakeTopo(Topo):
    def build(self):

        # Add a switches switch
        switches = []
        for i in range(7):
            switches.append(self.addSwitch(f's{i}'))

        hosts = []
        for i in range(12):
            hosts.append(self.addHost(f'h{i+1}'))

        self.addLink(switches[0], switches[1])
        self.addLink(switches[0], switches[2])
        self.addLink(switches[0], switches[3])
        self.addLink(switches[0], switches[4])
        self.addLink(switches[0], switches[5])
        self.addLink(switches[0], switches[6])

        self.addLink(switches[1], hosts[0])
        self.addLink(switches[1], hosts[1])

        self.addLink(switches[2], hosts[2])
        self.addLink(switches[2], hosts[3])

        self.addLink(switches[3], hosts[4])
        self.addLink(switches[3], hosts[5])

        self.addLink(switches[4], hosts[6])
        self.addLink(switches[4], hosts[7])

        self.addLink(switches[5], hosts[8])
        self.addLink(switches[5], hosts[9])

        self.addLink(switches[6], hosts[10])
        self.addLink(switches[6], hosts[11])



def run():

    print("#########################################")
    print("##                                     ##")
    print("##   Welcome to the IBN Demonstrator!  ##")
    print("##                                     ##")
    print("#########################################")
    print("Created by: Antonio Lopes & Pedro Duarte")

    print("\nPlease input your first intent: ")
    input(">> ")
    print("Generating a network with a Snowflake Topology...")

    # Create the network
    topo = SnowFlakeTopo()
    net = Mininet(topo=topo, controller=OVSController)
    net.start()

    CLI(net)

    print("\nWhat is your next intent: ")
    input(">> ")
    print("\nIsolating branch 1 from the main network...")

    net.configLinkStatus('s1', 's2', 'down')

    CLI(net)

    print("\nWhat is your next intent: ")
    input(">> ")
    print("\nIsolating branch 2 and returning branch 1 to the main network...")
    
    net.configLinkStatus('s1', 's2', 'up')
    net.configLinkStatus('s1', 's3', 'down')

    CLI(net)

    print("\nWhat is your next intent: ")
    input(">> ")
    print("\nRestricting traffic between hosts 10 and 11...")
    
    host10 = net.get('h10')
    host11 = net.get('h11')
    
    host10.cmd(f'iptables -A INPUT -s {host11.IP()} -j ACCEPT')
    host10.cmd(f'iptables -A INPUT -j DROP')

    host11.cmd(f'iptables -A INPUT -s {host10.IP()} -j ACCEPT')
    host11.cmd(f'iptables -A INPUT -j DROP')

    CLI(net)

    print("\nWhat is your next intent: ")
    input(">> ")
    print("\nShutting down the network...")

    # Stop the network
    net.stop()

if __name__ == '__main__':
    # Set the log level to info
    setLogLevel('info')
    run()