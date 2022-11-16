import numpy as np

class host:
    def __init__(self, init_dict):
        self.id = init_dict['id']
        self.pos = {'r': 0, 'a': 0}
        self.devId = init_dict['locations'][0]['elementId']
        self.devPort = init_dict['locations'][0]['port']
        self.dev_pos = self.pos

class device:
    def __init__(self, id):
        self.id = id
        self.pos = {'r': 0, 'a': 0}  # polar coordinate
        self.hostList = []

    def addHost(self, host:host):
        self.hostList.append(host)

    def rmHost(self, host:host):
        self.hostList.remove(host)

class link:
    def __init__(self, init_dict):
        self.src_devId = init_dict['src']['device']
        self.src_port = init_dict['src']['port']
        self.dst_devId = init_dict['dst']['device']
        self.dst_port = init_dict['dst']['port']
        self.type = init_dict['type']
        self.state = init_dict['state']
        self.src_pos = {'r': 0, 'a': 0}
        self.dst_pos = {'r': 0, 'a': 0}

class cluster:
    def __init__(self, init_dict):
        self.id = init_dict['id']
        self.deviceCount = init_dict['deviceCount']
        self.linkCount = init_dict['linkCount']
        self.root = init_dict['root']
        self.deviceList:list[device] = []
        self.linkList:list[link] = []


    def addDevice(self, device:device):
        self.deviceList.append(device)

    def addLink(self, link:link):
        if not self.linkExist(link):
            self.linkList.append(link)

    def setDevPos(self, evenR, centerR=0.0,centerA=0.0):
        # distribute the angle of each device
        angles = []
        if len(self.deviceList) == 0:
                return
        d_angle = 2 * np.pi / len(self.deviceList)
        for i in range(len(self.deviceList)):
            if i == 0:
                angles.append(0)
            else:
                angles.append(angles[i - 1] + d_angle)
        for i in range(len(self.deviceList)):
            beta=np.pi+centerA-angles[i]
            tmp=evenR ** 2 + centerR ** 2 - \
                    2 * evenR * centerR * np.cos(beta)
            r = np.sqrt(tmp)
            if centerR ==0.0:
                theta=angles[i]
            else:
                theta = np.arcsin(evenR * np.sin(beta) / centerR) + centerA
            self.deviceList[i].pos['r'] = r
            # evenly scatter at different angels
            self.deviceList[i].pos['a'] = theta

    def setLinkPos(self):
        for li in self.linkList:  # set links' src position & dst position
            src_dev=self.getDevById(li.src_devId)
            if src_dev != None:
                li.src_pos = src_dev.pos 
            dst_dev = self.getDevById(li.dst_devId)
            if dst_dev != None:
                li.dst_pos = dst_dev.pos
            

    def getDevById(self, deviceId):
        for dev in self.deviceList:
            if deviceId == dev.id:
                return dev
        return None

    def linkExist(self, link:link):
        for li in self.linkList:
            if li.src_devId == link.dst_devId and li.dst_devId == link.src_devId and li.src_port == link.dst_port and li.dst_port == link.src_port:
                return True
        return False

class hosts:
    def __init__(self, hostlist=[]):
        self.hostList:list[host] = hostlist

    def addHost(self, host:host):
        self.hostList.append(host)

    def attachTo(self, cluster:cluster):
        for host in self.hostList:
            dev = cluster.getDevById(host.devId)
            if dev != None:
                dev.addHost(host)
                host.dev_pos = dev.pos

    def detachFrom(self, cluster:cluster):
        for host in self.hostList:
            dev = cluster.getDevById(host.devId)
            if dev != None:
                dev.rmHost(host)
                host.dev_pos = host.pos

    def setPosRelateToDev(self, cluster:cluster, evenR):
        for dev in cluster.deviceList:
            angles = []
            if len(dev.hostList) == 0:
                continue
            d_angle = 2 * np.pi / len(dev.hostList)
            for i in range(len(dev.hostList)):
                if i == 0:
                    angles.append(0)
                else:
                    angles.append(angles[i - 1] + d_angle)
            # print(f'debug {len(angles)')
            # evenly scatter around device
            dev_r = dev.pos['r']
            dev_theta = dev.pos['a']
            for i in range(len(dev.hostList)):  # set pos of each host
                beta = np.pi + dev_theta - angles[i]
                tmp = evenR ** 2 + dev_r ** 2 - \
                    2 * evenR * dev_r * np.cos(beta)
                r = np.sqrt(tmp)
                theta = np.arcsin(evenR * np.sin(beta) / dev_r) + dev_theta
                dev.hostList[i].pos['r'] = r
                dev.hostList[i].pos['a'] = theta
            angles.clear()

class topo:
    def __init__(self, clusters:list, hosts:hosts):
        self.clusterList:list[cluster] = clusters
        self.hosts = hosts
        for c in clusters:
            self.hosts.attachTo(c)

    def initAllPos(self, deviceEvenR, hostEvenR,centerR=0.0):
        angles=[]
        if len(self.clusterList) ==0:
            return
        d_angle = 2 * np.pi / len(self.clusterList)
        for i in range(len(self.clusterList)):
            if i == 0:
                angles.append(0)
            else:
                angles.append(angles[i - 1] + d_angle)
        for i in range(len(self.clusterList)):
            c=self.clusterList[i]
            c.setDevPos(evenR=deviceEvenR,centerR=centerR,centerA=angles[i])
            c.setLinkPos()
            self.hosts.setPosRelateToDev(cluster=c, evenR=hostEvenR)
