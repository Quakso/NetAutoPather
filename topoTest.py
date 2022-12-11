from mininet.topo import Topo


class MyTopo(Topo):
    def __init__(self):
        super().__init__(self)
        host1 = self.addHost('h1', ip="10.0.0.1")
        host2 = self.addHost('h2', ip="10.0.0.2")
        host3 = self.addHost('h3', ip="10.0.0.3")
        host4 = self.addHost('h4', ip="10.0.0.4")

        switch1 = self.addSwitch('s1')
        switch2 = self.addSwitch('s2')
        switch3 = self.addSwitch('s3')
        switch4 = self.addSwitch('s4')
        switch5 = self.addSwitch('s5')
        switch6 = self.addSwitch('s6')

        self.addLink(switch1, switch2)
        self.addLink(switch1, switch5)
        self.addLink(switch1, switch4)

        self.addLink(switch2, switch3)
        self.addLink(switch2, switch5)
        self.addLink(switch2, switch6)

        self.addLink(switch3, switch5)
        self.addLink(switch3, switch6)

        self.addLink(switch4, switch5)

        self.addLink(switch5, switch6)

        self.addLink(switch1, host1)
        self.addLink(switch4, host3)
        self.addLink(switch3, host2)
        self.addLink(switch3, host2)
        self.addLink(switch6, host4)

topos = {'mytopo': (lambda: MyTopo())}
