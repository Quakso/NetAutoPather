import time
import threading
from onosapi import get_cluster_devices, get_cluster_links, get_clusters, get_hosts
from topobase import Host, Hosts, Topo, Cluster, Device, Link
import json
import numpy as np
from matplotlib.backend_bases import MouseButton, FigureCanvasBase
from graph import Graph, Point
from matplotlib import axes
import onosapi
import matplotlib.pyplot as plt

ip = "192.168.10.145"


class TopoInteractor:
    """
    a topo interactor

    draw interactive topo

    you can drag the device or host point

    """

    def __init__(self, topo: Topo, devLinkColor='gray', hostLinkColor='#e0e0e0', deviceEvenR=4.0, hostEvenR=2.0):
        self.__PICK_NOTHING = 0  # 未选中任何对象的标志
        self.__PICK_HOST = 1  # 选中对象为主机
        self.__PICK_DEVICE = 2  # 选中对象为交换机

        self.topo = topo  # 存放当前平面的拓扑信息
        self.graph = Graph(topo)  # 将当前拓扑转换为图，用于选路计算
        self.hosts: Hosts = topo.hosts  # 当前的主机

        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': 'polar'})  # 坐标系
        canvas = fig.canvas  # 画布
        self.ax: axes = ax
        self.canvas: FigureCanvasBase = canvas

        self.devLinkColor = devLinkColor  # 交换机之间连接的颜色
        self.hostLinkColor = hostLinkColor  # 主机与交换机连接的颜色
        self.devMarkerSize = 200  # 交换机的图像大小
        self.hostMarkerSize = 100  # 主机的图像大小
        self.devEvenR = float(deviceEvenR)  # 交换机离中心的距离
        self.hostEvenR = float(hostEvenR)  # 主机离交换机的距离
        if len(self.topo.clusterList) == 1:
            self.centerR = 0  # 只有一簇不需要考虑
        else:
            self.centerR = self.devEvenR * 2.5  # 不同簇离坐标系中心的距离
        self.devR = []  # 所有交换机暂存的极径列表
        self.devA = []  # 所有交换机暂存的角度列表
        self.hostR = []  # 所有主机暂存的极径列表
        self.hostA = []  # 所有主机暂存的角度列表
        self.linkLines = []  # 所有交换机之间的link暂存的始末点信息
        self.hostLines = []  # 所有主机与交换机之间link暂存的始末点信息
        self.pick_point = self.__PICK_NOTHING  # 未选中任何对象
        self.pick_host: Host = Host()  # 选中的主机
        self.pick_device: Device = Device()  # 选中的交换机
        self.drag_point = None  # 拖动抓住的点
        self.drag_radius_dev = 0.5  # 判断抓住交换机的最大距离
        self.drag_radius_host = 0.3  # 判断抓住主机的最大距离
        self.host_visible = True  # 主机是否可见
        self.id_text_visible = False  # 各设备id是否可见
        self.delay_visible = False  # 时延是否可见

        self.choose_point = False  # 是否进入选中主机模式
        self.task_2_host: list[Host] = []  # 选中的主机列表，至多两个，两个才可以开始选路
        self.pathColorList = ['#FFFFCC', '#00EC00', '#2894FF', '#4A4AFF', '#FFB5B5']  # 路径的颜色，有多种可选方便区分
        self.colorWheel = 0  # 颜色转盘，用于选择颜色

        self.appId = 'myApp'  # 下发流表的AppId

        self.draw_topo(self.devEvenR, self.hostEvenR, self.centerR)  # 画出拓扑
        self.canvas.mpl_connect('button_press_event', self.on_button_press)  # 监听鼠标按下
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)  # 监听鼠标移动
        self.canvas.mpl_connect('button_release_event', self.on_button_release)  # 监听鼠标放开
        self.canvas.mpl_connect('key_press_event', self.on_key_press)  # 监听键盘

        self.changeId = 0  # 记录链路是否改变的id
        self.linkListen = False  # 表示是否继续链路监听循环
        self.linkListenThread: threading.Thread = threading.Thread(target=self.linkChangeThreadFunc)  # 链路监听线程

    def on_key_press(self, event):

        if event.key == 'r':
            self.refreshTopo()
        elif event.key == 'h':
            self.host_visible = bool(1 - self.host_visible)
            self.redraw_dev()
        elif event.key == 't':
            self.id_text_visible = bool(1 - self.id_text_visible)
            self.redraw_dev()
        elif event.key == 'c':
            self.choose_point = bool(1 - self.choose_point)
            self.redraw_dev()
        elif event.key == 'd':
            self.deleteAllAddedFlows()
        elif event.key == 'e':
            self.postDropFlow2AllDev()
        elif event.key == 's':
            self.startDelayDetect()
        elif event.key == 'p':
            self.stopDelayDetect()
        elif event.key == 'm':
            self.getDelay2Graph()
        elif event.key == 'w':
            self.delay_visible = bool(1 - self.delay_visible)
            self.redraw_dev()
        elif event.key == 'a':
            self.pathForAllHosts()
        elif event.key == 'n':
            self.startLinkListenThread()
        elif event.key == 'j':
            self.stopLinkListenThread()
        elif event.key == 'enter':
            if self.choose_point:
                if len(self.task_2_host) == 2:
                    self.pathBetween2Hosts(self.task_2_host[0], self.task_2_host[1])

    def draw_path(self, pre: dict, p_end: Point, h_begin: Host, h_end: Host):
        if not pre.__contains__(p_end):
            return
        pathLines = []
        # host和其所连device的连线
        # host_begin
        theta = [h_begin.pos['a'], h_begin.dev_pos['a']]
        r = [h_begin.pos['r'], h_begin.dev_pos['r']]
        pathLines.append({'theta': theta, 'r': r})

        # host_end
        theta = [h_end.pos['a'], h_end.dev_pos['a']]
        r = [h_end.pos['r'], h_end.dev_pos['r']]
        pathLines.append({'theta': theta, 'r': r})

        # 读取pre链接数组，将相应的连线信息计入pathLines
        # 如果当前Point和之前Point的所属device不同，则需要创建连线
        # p_pre记录前一个Point,p_cur记录当前Point
        p_pre = p_end
        p_cur = p_end
        # 以下一个Point是否是None来判断结束
        while pre[p_cur] is not None:
            if p_cur.deviceId != p_pre.deviceId:
                # 找到两个device的位置
                dev_pre: Device = Device()
                dev_cur: Device = Device()
                for c in self.topo.clusterList:
                    dev_pre = c.getDevById(p_pre.deviceId)
                    dev_cur = c.getDevById(p_cur.deviceId)
                    if dev_pre is not None and dev_cur is not None:
                        break

                # 插入线段的起始点
                if dev_pre is not None and dev_cur is not None:
                    theta = [dev_pre.pos['a'], dev_cur.pos['a']]
                    r = [dev_pre.pos['r'], dev_cur.pos['r']]
                    pathLines.insert(1, {'theta': theta, 'r': r})
            # 迭代
            p_pre = p_cur
            p_cur = pre[p_cur]

        # 画出线段
        for path in pathLines:
            self.ax.plot(path['theta'], path['r'], color=self.pathColorList[self.colorWheel])
        self.canvas.draw_idle()
        self.colorWheel = (self.colorWheel + 1) % len(self.pathColorList) # 切换颜色轮盘

    def init_ax(self):
        self.ax.set_ylim(0, 18)
        self.ax.set_xlim(0, 2 * np.pi)
        self.ax.grid(False)
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        # self.ax.axis('off')# set axis invisible
        self.redraw_text()

    def redraw_text(self):
        keyText = ("H: Host visible/invisible\n"
                   "T: Show basic info on/off\n"
                   "C: Choose two host on/off\n"
                   "D: Delete all added flows\n"
                   "E: Add drop flows to all device\n"
                   "R: Refresh\n"
                   "S: Start delay detection\n"
                   "P: Stop delay detection\n"
                   "M: Get delay map\n"
                   "W: Delay visible/invisible\n"
                   "A: Path and flow for all hosts")
        plt.text(np.pi * 5 / 4, 30, keyText, wrap=True)

        hostText = "Choosen Points: "
        if self.choose_point:
            hostText += "On\n"
            for h in self.task_2_host:
                hostText += f"Host:\nid:{h.id}\nip:{h.ip}\nconnect to:{h.devId} port {h.devPort}\n------\n"
        else:
            hostText += "Off\n"
        plt.text(np.pi * 3 / 4, 23, hostText, wrap=True)

        # 表示选中了一个设备，显示他的信息
        pickText = ""
        if self.pick_point != self.__PICK_NOTHING:
            # 选中host
            if self.pick_point == self.__PICK_DEVICE:
                pickText = (f"Device:\n"
                            f"Id:{self.pick_device.id}\n")
            elif self.pick_point == self.__PICK_HOST:
                pickText = (f"Host:\n"
                            f"Id:{self.pick_host.id}\n"
                            f"Connect to:{self.pick_host.devId} port {self.pick_host.devPort}\n"
                            f"Ip:{self.pick_host.ip}\n"
                            f"Mac:{self.pick_host.id[:-5]}"
                            )
        plt.text(np.pi * 13 / 8, 23, pickText, wrap=True)

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
        if self.drag_point.__class__.__name__ == 'Device':
            self.redraw_dev()
        elif self.drag_point.__class__.__name__ == 'Host':
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
        if self.drag_point.__class__.__name__ == 'Device':
            self.pick_point = self.__PICK_DEVICE
            self.pick_device = self.drag_point
        elif self.drag_point.__class__.__name__ == 'Host':
            self.pick_point = self.__PICK_HOST
            self.pick_host = self.drag_point
        self.redraw_dev()

    def get_drag_point(self, event):
        d_dev = np.array(self.devR) ** 2 + event.ydata ** 2 - 2 * event.ydata * np.array(self.devR) * np.cos(
            np.array(self.devA) - event.xdata)
        d_host = np.array(self.hostR) ** 2 + event.ydata ** 2 - 2 * event.ydata * np.array(self.hostR) * np.cos(
            np.array(self.hostA) - event.xdata)
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
                path = 1
            else:
                path = 2
        if d_dev_min != None and d_host_min == None:
            path = 1
        if d_dev_min == None and d_host_min != None:
            path = 2
        if path == 1:
            indseq, = np.nonzero(d_dev == d_dev.min())
            ind = indseq[0]
            if d_dev[ind] > self.drag_radius_dev:
                return None

            dev = None
            for c in self.topo.clusterList:
                if ind >= len(c.deviceList):
                    ind -= len(c.deviceList)
                    continue
                else:
                    dev = c.deviceList[ind]
                    break

            if dev != None:
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
                if len(self.task_2_host) < 2:
                    self.task_2_host.append(host)
                else:
                    self.task_2_host.clear()
                    self.task_2_host.append(host)
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
        self.draw_delay_weight()
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
        self.draw_delay_weight()
        self.canvas.draw_idle()

    def draw_topo(self, deviceEvenR, hostEvenR, centerR):
        self.ax.clear()
        self.init_ax()
        self.clear_list()
        self.topo.initAllPos(deviceEvenR, hostEvenR, centerR)
        self.get_devices_radius_angles()
        self.get_hosts_radius_angles()
        self.get_link_src_dst()
        self.get_host_src_dst()
        self.draw_links()
        self.draw_devices()
        self.draw_hosts()
        self.draw_delay_weight()
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
                    self.ax.text(dev.pos['a'], dev.pos['r'], dev.id, fontfamily='monospace', color='#454545')

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
                self.ax.text(h.pos['a'], h.pos['r'], f'{h.id} {h.devPort}', fontfamily='sans-serif', color='#4169e1')

    def draw_delay_weight(self):
        if self.delay_visible:
            for c in self.topo.clusterList:
                for li in c.linkList:
                    # 准备Point，获取时延信息
                    p_src = Point(li.src_devId, li.src_port)
                    p_dst = Point(li.dst_devId, li.dst_port)
                    delaySrcDst = self.graph.weightMatrix[p_src][p_dst]
                    delayDstSrc = self.graph.weightMatrix[p_dst][p_src]
                    # 计算时延文字要显现的位置 r3 theta3
                    r1 = li.src_pos['r']
                    r2 = li.dst_pos['r']
                    theta1 = li.src_pos['a']
                    theta2 = li.dst_pos['a']
                    if theta2 < 0:
                        theta2 = theta2 + 2 * np.pi
                    r3 = np.sqrt(np.square(r1) + np.square(r2) + np.cos(theta2 - theta1) * 2 * r1 * r2) / 2
                    if r3 == 0:
                        theta3 = 0
                    else:
                        theta3 = theta1 + np.arcsin(r2 * np.sin(theta2 - theta1) / (2 * r3))
                    self.ax.text(theta3, r3, f'{delaySrcDst}\n'
                                             f'{delayDstSrc}',
                                 fontfamily='sans-serif',
                                 color='#ff5151')

    # 刷新
    def refreshTopo(self):
        # 获取拓扑
        cluster_set = []
        host_set = Hosts([])
        status_code, resp = get_clusters(ip)
        if status_code == 200:
            # print(status_code)
            # get clusters list
            clusters = (json.loads(resp))['clusters']
            for i in range(len(clusters)):
                clus = Cluster(clusters[i])  # init an instance of cluster
                # get devices of cluster
                status_code, resp = get_cluster_devices(ip, clus.id)
                if status_code == 200:
                    # get devices list
                    devices = (json.loads(resp))['devices']
                    for deviceId in devices:
                        dev = Device(deviceId)
                        # init a device and add it to cluster
                        clus.addDevice(dev)
                else:
                    print('get devices:{}'.format(status_code))

                status_code, resp = get_cluster_links(
                    ip, clus.id)  # get links of cluster
                if status_code == 200:
                    links = (json.loads(resp))['links']
                    for li in links:
                        li = Link(li)
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
                h = Host(h)
                host_set.addHost(h)
        else:
            print('get hosts:{}'.format(status_code))

        self.clear_list()
        # 刷新拓扑信息
        self.topo = Topo(cluster_set, host_set)
        # 重建算法图
        self.graph = Graph(self.topo)
        self.hosts: Hosts = self.topo.hosts
        # 重新获取时延信息
        self.getDelay2Graph()
        # 重新画图
        self.draw_topo(self.devEvenR, self.hostEvenR, self.centerR)

    # 获取时延并将其放入Graph中
    def getDelay2Graph(self):
        status_code, resp = onosapi.get_delay_map(ip)
        if status_code == 200:
            delayMap = json.loads(resp)
            self.graph.putDelayMap(delayMap)
            self.redraw_dev()
        else:
            print('get delay graph: {}'.format(status_code))

    def startDelayDetect(self):
        status_code, resp = onosapi.start_delay_detect(ip)
        if status_code != 200:
            print('start delay detection: {}'.format(status_code))
        else:
            msg_map = json.loads(resp)
            print('message: {}'.format(msg_map['msg']))

    def stopDelayDetect(self):
        status_code, resp = onosapi.stop_delay_detect(ip)
        if status_code != 200:
            print('stop delay detection: {}'.format(status_code))
        else:
            msg_map = json.loads(resp)
            print('message: {}'.format(msg_map['msg']))

    # 在两个host之间选路
    def pathBetween2Hosts(self, beginHost: Host, endHost: Host):
        p_begin = Point(beginHost.devId, beginHost.devPort)
        p_end = Point(endHost.devId, endHost.devPort)
        # 调用算法返回结果pre，通过pre了解到最短路径
        pre = self.graph.dijistra(p_begin)
        self.draw_path(pre, p_end, beginHost, endHost)
        p_pre = p_end
        p_cur = pre[p_end]
        while p_cur is not None:
            if p_pre.deviceId == p_cur.deviceId:
                resp, resp_text = onosapi.post_flow(controller_ip=ip, appId=self.appId, priority=7,
                                                    srcMac=beginHost.id[:-5],
                                                    dstMac=endHost.id[:-5],
                                                    inputPort=p_cur.devicePort, outputPort=p_pre.devicePort,
                                                    targetDeviceId=p_cur.deviceId)
                print(
                    f"Post flow controller_ip={ip}, appId={self.appId}, priority=6, srcMac={beginHost.id[:-5]}"
                    f", dstMac={endHost.id[:-5]}, inputPort={p_cur.devicePort}, "
                    f"outputPort={p_pre.devicePort}, targetDeviceId={p_cur.deviceId}"
                    f", Status code:{resp}")
                resp, resp_text = onosapi.post_flow(controller_ip=ip, appId=self.appId, priority=7,
                                                    dstMac=beginHost.id[:-5],
                                                    srcMac=endHost.id[:-5],
                                                    outputPort=p_cur.devicePort, inputPort=p_pre.devicePort,
                                                    targetDeviceId=p_cur.deviceId)
                print(
                    f"Post flow controller_ip={ip}, appId={self.appId}, priority=6, dstMac={beginHost.id[:-5]}"
                    f", srcMac={endHost.id[:-5]}, outputPort={p_cur.devicePort}, "
                    f"inputPort={p_pre.devicePort}, targetDeviceId={p_cur.deviceId}"
                    f", Status code:{resp}")

            p_pre = p_cur
            p_cur = pre[p_cur]

    # 为所有的链路下发最短路径(时延)流表
    def pathForAllHosts(self):
        i = 0
        while i < len(self.hosts.hostList) - 1:
            j = i + 1
            while j < len(self.hosts.hostList):
                self.pathBetween2Hosts(self.hosts.hostList[i], self.hosts.hostList[j])
                j += 1
            i += 1

    # 链路连接检测线程
    def checkLinkChange(self):
        status_code, resp = onosapi.get_change_id(ip)
        if status_code == 200:
            content = json.loads(resp)
            if int(content["changeId"]) != self.changeId:
                self.changeId = int(content["changeId"])
                print(f'changeId:{content["changeId"]} {content["changeMsg"]} \n'
                      f'link event:{content["linkEvent"]}')
                # 检测到链路改变
                print("链路改变，重新选路")
                self.refreshTopo()
                # 删除所有已下发的流表
                self.deleteAllAddedFlows()
                # 为所有交换机下发drop流表
                self.postDropFlow2AllDev()
                # 重新为所有链路选路
                self.pathForAllHosts()
        else:
            print(f'check link change {status_code}')

    def linkChangeThreadFunc(self):
        while self.linkListen:
            try:
                self.checkLinkChange()
                # 每隔3秒进行一此链路改变检测
                time.sleep(3)
            except InterruptedError:
                print("link change listen thread was interrupted")
        print('end of link change listen thread')

    def startLinkListenThread(self):
        if self.linkListen == True:
            print('已有link改变监听线程 ' + self.linkListenThread.name)
        else:
            self.linkListen = True
            try:
                self.linkListenThread = threading.Thread(target=self.linkChangeThreadFunc)
                print('开始link改变监听线程 ' + self.linkListenThread.name)
                self.linkListenThread.start()
            except Exception:
                print('error at start a thread')

    def stopLinkListenThread(self):
        if self.linkListen:
            self.linkListen = False
            print('终止link改变监听线程')

    def deleteAllAddedFlows(self):
        # 删除所有已下发的流表
        resp, resp_text = onosapi.del_flows_by_appId(controller_ip=ip, appId=self.appId)
        print(f'Delete all flows appId={self.appId}, Status code: {resp}')


    def postDropFlow2AllDev(self):
        # 对所有交换机下发优先级为6的drop流表，将原onos提供的流表屏蔽
        for c in self.topo.clusterList:
            for dev in c.deviceList:
                resp_status_code, resp_text = onosapi.post_flow_drop(controller_ip=ip, appId=self.appId,
                                                                     targetDeviceId=dev.id, priority=6)
                print(f'Post drop flow to {dev.id}, AppId={self.appId}, Status code: {resp_status_code}')



def main():
    cluster_set = []
    host_set = Hosts()
    status_code, resp = get_clusters(ip)
    if status_code == 200:
        # print(status_code)
        # get clusters list
        clusters = (json.loads(resp))['clusters']
        for i in range(len(clusters)):
            clus = Cluster(clusters[i])  # init an instance of cluster
            # get devices of cluster
            status_code, resp = get_cluster_devices(ip, clus.id)
            if status_code == 200:
                # get devices list
                devices = (json.loads(resp))['devices']
                for deviceId in devices:
                    dev = Device(deviceId)
                    # init a device and add it to cluster
                    clus.addDevice(dev)
            else:
                print('get devices:{}'.format(status_code))

            status_code, resp = get_cluster_links(
                ip, clus.id)  # get links of cluster
            if status_code == 200:
                links = (json.loads(resp))['links']
                for li in links:
                    li = Link(li)
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
            h = Host(h)
            host_set.addHost(h)
    else:
        print('get hosts:{}'.format(status_code))

    mpl.use("qt5agg")
    appTopo = Topo(cluster_set, host_set)
    ti = TopoInteractor(appTopo, deviceEvenR=10, hostEvenR=3)

    plt.show()

if __name__ == '__main__':
    import matplotlib as mpl

    main()
