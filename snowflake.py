from mininet.topo import Topo

class MyTopo(Topo):
    "Custom topology with sequential MAC addresses."

    def build(self):
        # Add switches
        switches = []
        for i in range(7):
            switches.append(self.addSwitch(f's{i}'))

        # Add hosts with custom MAC addresses
        hosts = []
        for i in range(12):
            mac = f"00:00:00:00:00:{i+1:02d}"  # Sequential MAC: 00:00:00:00:00:01, 02, ..., 12
            host = self.addHost(f'h{i+1}', mac=mac)
            hosts.append(host)

        # Connect central switch to other switches
        self.addLink(switches[0], switches[1])
        self.addLink(switches[0], switches[2])
        self.addLink(switches[0], switches[3])
        self.addLink(switches[0], switches[4])
        self.addLink(switches[0], switches[5])
        self.addLink(switches[0], switches[6])

        # Connect switches to hosts
        self.addLink(switches[1], hosts[0])  # h1
        self.addLink(switches[1], hosts[1])  # h2

        self.addLink(switches[2], hosts[2])  # h3
        self.addLink(switches[2], hosts[3])  # h4

        self.addLink(switches[3], hosts[4])  # h5
        self.addLink(switches[3], hosts[5])  # h6

        self.addLink(switches[4], hosts[6])  # h7
        self.addLink(switches[4], hosts[7])  # h8

        self.addLink(switches[5], hosts[8])  # h9
        self.addLink(switches[5], hosts[9])  # h10

        self.addLink(switches[6], hosts[10]) # h11
        self.addLink(switches[6], hosts[11]) # h12


topos = {'mytopo': (lambda: MyTopo())}
