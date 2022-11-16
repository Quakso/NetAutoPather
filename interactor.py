from onosapi import get_cluster_devices,get_cluster_links,get_clusters,get_hosts
from topobase import host,hosts,topo,cluster,device,link
import json
import numpy as np
from matplotlib.backend_bases import MouseButton,FigureCanvasBase
from graph import Graph,Point
from matplotlib import axes

ip = "192.168.10.145"

class TopoInteractor:
    """
    a topo interactor

    draw interactive topo

    you can drag the device or host point

    """

    def __init__(self,topo,devLinkColor='gray', hostLinkColor='#e0e0e0', deviceEvenR=4.0, hostEvenR=2.0):
        self.topo = topo
        self.g=Graph(topo)
        self.hosts:hosts = topo.hosts
        fig,ax= plt.subplots(figsize=(10, 10),subplot_kw={'projection':'polar'})
        canvas = fig.canvas
        self.ax:axes = ax
        self.canvas:FigureCanvasBase = canvas
        self.devLinkColor = devLinkColor
        self.hostLinkColor = hostLinkColor
        self.devMarkerSize = 200
        self.hostMarkerSize = 100
        self.devEvenR = float(deviceEvenR)
        self.hostEvenR = float(hostEvenR)
        if len(self.topo.clusterList) == 1:
             self.centerR=0
        else:
            self.centerR=self.devEvenR*2.5
        self.devR = []
        self.devA = []
        self.hostR = []
        self.hostA = []
        self.linkLines = []
        self.hostLines = []
        self.drag_point = None
        self.drag_radius_dev = 0.5  # max pixel distance to count as a drag hit
        self.drag_radius_host = 0.3
        self.host_visible=True
        self.id_text_visible=False
        self.choose_point=False
        self.task_2_point:list[Point]=[]
        self.draw_topo(self.devEvenR, self.hostEvenR,self.centerR)
        self.canvas.mpl_connect('button_press_event', self.on_button_press)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.canvas.mpl_connect('button_release_event', self.on_button_release)
        self.canvas.mpl_connect('key_press_event', self.on_key_press)
        
        

    def on_key_press(self, event):
        if event.key == 'r':
            self.draw_topo(self.devEvenR, self.hostEvenR,self.centerR)
        if event.key == 'h':
            self.host_visible= bool(1-self.host_visible)
            self.redraw_dev()
        if event.key == 't':
            self.id_text_visible= bool(1-self.id_text_visible)
            self.redraw_dev()
        if event.key == 'c':
            self.choose_point=bool(1-self.choose_point)
            self.redraw_dev()
        if event.key == 'enter':
            if self.choose_point:
                if len(self.task_2_point) ==2:
                    pre=self.g.dijistra(self.task_2_point[0])
    
    def draw_path(self,pre:dict,p_end:Point):
        if not pre.__contains__(p_end):
            return
        



    def init_ax(self):
        self.ax.set_ylim(0, 18)
        self.ax.set_xlim(0, 2 * np.pi)
        self.ax.grid(False)
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        # self.ax.axis('off')# set axis invisible
        self.redraw_text()

    def redraw_text(self):
        keyText=("H: Host visible/invisible\n"
              "T: Show basic info on/off\n"
              "C: Choose two host on/off\n"
              "R: Refresh\n")
        plt.text(np.pi*5/4,30,keyText,wrap=True)

        pointText="Choosen Points: "
        if self.choose_point:  
            pointText+="On\n"
            for p in self.task_2_point:
                pointText+=f"Point: id:{p.deviceId} port:{p.devicePort}\n"
        else:
            pointText+="Off\n"
        plt.text(np.pi*3/4,27,pointText,wrap=True)

    def clear_list(self):
        self.devR.clear()
        self.devA.clear()
        self.hostR.clear()
        self.hostA.clear()
        self.linkLines.clear()
        self.hostLines.clear()

    def on_mouse_move(self, event):
        if event.inaxes is None:
            return
        if event.button != MouseButton.LEFT:
            return
        if self.drag_point is None:
            return
        self.drag_point.pos['a'] = event.xdata
        self.drag_point.pos['r'] = event.ydata
        if self.drag_point.__class__.__name__ == 'device':
            self.redraw_dev()
        elif self.drag_point.__class__.__name__ == 'host':
            self.redraw_host()

    def on_button_release(self, event):
        if event.button != MouseButton.LEFT:
            return
        self.drag_point = None

    def on_button_press(self, event):
        if event.inaxes is None:
            return
        if event.button != MouseButton.LEFT:
            return
        # print(f'pressed at {event.xdata} {event.ydata}')
        self.drag_point = self.get_drag_point(event)

    def get_drag_point(self, event):
        d_dev = np.array(self.devR)**2 + event.ydata**2-2*event.ydata*np.array(self.devR)*np.cos(np.array(self.devA)-event.xdata)
        d_host =np.array(self.hostR)**2 + event.ydata**2-2*event.ydata*np.array(self.hostR)*np.cos(np.array(self.hostA)-event.xdata)
        if d_dev.size != 0:
            d_dev_min = d_dev.min()
        else:
            d_dev_min = None
        if d_host.size != 0:
            d_host_min = d_host.min()
        else:
            d_host_min = None
        path = 0
        if d_dev_min != None and d_host_min != None:
            if d_dev.min() < d_host.min():
                path=1
            else:
                path=2
        if d_dev_min != None and d_host_min == None:
            path=1
        if d_dev_min == None and d_host_min != None:
            path=2
        if path == 1:
            indseq, = np.nonzero(d_dev == d_dev.min())
            ind = indseq[0]
            if d_dev[ind] > self.drag_radius_dev:
                return None

            dev=None
            for c in self.topo.clusterList:
                if ind >= len(c.deviceList):
                    ind-=len(c.deviceList)
                    continue
                else:
                    dev=c.deviceList[ind]
                    break

            if dev !=None :
                print(f'hit a device {ind} id {dev.id}')
            return dev
        elif path == 2:
            indseq, = np.nonzero(d_host == d_host.min())
            ind = indseq[0]
            if d_host[ind] > self.drag_radius_host:
                return None
            host = self.hosts.hostList[ind]
            print(f'hit a host {ind} id {host.id}')
            if self.choose_point:
                if len(self.task_2_point)<2:
                    self.task_2_point.append(Point(host.devId,host.devPort))
                else:
                    self.task_2_point.clear()
                    self.task_2_point.append(Point(host.devId,host.devPort))
                self.redraw_dev()
            return host
        else:
            return None
        

    def redraw_dev(self):
        self.ax.clear()
        self.init_ax()
        self.clear_list()
        for c in self.topo.clusterList:
            c.setLinkPos()
        self.get_devices_radius_angles()
        self.get_hosts_radius_angles()
        self.get_link_src_dst()
        self.get_host_src_dst()
        self.draw_links()
        self.draw_devices()
        self.draw_hosts()
        self.canvas.draw_idle()

    def redraw_host(self):
        self.ax.clear()
        self.init_ax()
        self.hostR.clear()
        self.hostA.clear()
        self.hostLines.clear()
        self.get_hosts_radius_angles()
        self.get_host_src_dst()
        self.draw_links()
        self.draw_devices()
        self.draw_hosts()
        self.canvas.draw_idle()

    def draw_topo(self, deviceEvenR, hostEvenR,centerR):
        self.ax.clear()
        self.init_ax()
        self.clear_list()
        self.topo.initAllPos(deviceEvenR, hostEvenR,centerR)
        self.get_devices_radius_angles()
        self.get_hosts_radius_angles()
        self.get_link_src_dst()
        self.get_host_src_dst()
        self.draw_links()
        self.draw_devices()
        self.draw_hosts()
        self.canvas.draw_idle()

    def get_devices_radius_angles(self):
        for c in self.topo.clusterList:
            for dev in c.deviceList:
                self.devR.append(dev.pos['r'])
                self.devA.append(dev.pos['a'])

    def get_hosts_radius_angles(self):
        for h in self.hosts.hostList:
            self.hostR.append(h.pos['r'])
            self.hostA.append(h.pos['a'])

    def get_host_src_dst(self):
        for h in self.hosts.hostList:
            theta = [h.pos['a'],
                     h.dev_pos['a']]
            r = [h.pos['r'],
                 h.dev_pos['r']]
            self.hostLines.append({'theta': theta, 'r': r})

    def get_link_src_dst(self):
        for c in self.topo.clusterList:
            for li in c.linkList:
                theta = [li.src_pos['a'],
                     li.dst_pos['a']]
                r = [li.src_pos['r'],
                    li.dst_pos['r']]
                self.linkLines.append({'theta': theta, 'r': r})

    def draw_devices(self):
        self.ax.scatter(self.devA, self.devR, marker='s', s=self.devMarkerSize)
        if self.id_text_visible:
            for c in self.topo.clusterList:
                for dev in c.deviceList:
                    self.ax.text(dev.pos['a'],dev.pos['r'],dev.id,fontfamily='monospace',color='#454545')
        

    def draw_links(self):
        for li in self.linkLines:
            self.ax.plot(li['theta'], li['r'], color=self.devLinkColor)
        # print(len(self.linkLines))

    def draw_hosts(self):
        if not self.host_visible:
            return
        self.ax.scatter(self.hostA, self.hostR,
                        marker='o', s=self.hostMarkerSize)
        for li in self.hostLines:
            self.ax.plot(li['theta'], li['r'], color=self.hostLinkColor)
        # print(len(self.hostLines))
        if self.id_text_visible:
            for h in self.hosts.hostList:
                self.ax.text(h.pos['a'],h.pos['r'],f'{h.id} {h.devPort}',fontfamily='sans-serif',color='#4169e1')


def main():
    cluster_set = []
    host_set = hosts()
    status_code, resp = get_clusters(ip)
    if status_code == 200:
        # print(status_code)
        # get clusters which is a list
        clusters = (json.loads(resp))['clusters']
        for i in range(len(clusters)):
            clus = cluster(clusters[i])  # init an instance of cluster
            # get devices of cluster
            status_code, resp = get_cluster_devices(ip, clus.id)
            if status_code == 200:
                # get devices which is a list
                devices = (json.loads(resp))['devices']
                for deviceId in devices:
                    dev = device(deviceId)
                    # init a device and add it to cluster
                    clus.addDevice(dev)
            else:
                print('get devices:{}'.format(status_code))

            status_code, resp = get_cluster_links(
                ip, clus.id)  # get links of cluster
            if status_code == 200:
                links = (json.loads(resp))['links']
                for li in links:
                    li = link(li)
                    clus.addLink(li)
            else:
                print('get links:{}'.format(status_code))
            cluster_set.append(clus)
    else:
        print('get clusters:{}'.format(status_code))

    status_code, resp = get_hosts(ip)
    if status_code == 200:
        hosts_get = (json.loads(resp))['hosts']
        for h in hosts_get:
            h = host(h)
            host_set.addHost(h)
    else:
        print('get hosts:{}'.format(status_code))
    
    mpl.use("qt5agg")
    
    appTopo = topo(cluster_set, host_set)
    ti = TopoInteractor(appTopo,deviceEvenR=10, hostEvenR=3)
    
    plt.show()

if __name__ == '__main__':
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    main()