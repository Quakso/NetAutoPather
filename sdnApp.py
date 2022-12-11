import sys
from sdnAppInterface import Ui_MainWindow
from interactor import TopoInteractor
from topobase import Host, Hosts, Cluster, Device, Link, Topo
import onosapi, json
from matplotlib.backends.qt_compat import QtWidgets

ip = '192.168.10.145'


class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self, interctorCanvas):
        super().__init__()
        self._main = QtWidgets.QWidget()
        self.setCentralWidget(self._main)
        layout = QtWidgets.QVBoxLayout(self._main)
        layout.addWidget(interctorCanvas)


def main():
    cluster_set = []
    host_set = Hosts()
    status_code, resp = onosapi.get_clusters(ip)
    if status_code == 200:
        # print(status_code)
        # get clusters list
        clusters = (json.loads(resp))['clusters']
        for i in range(len(clusters)):
            clus = Cluster(clusters[i])  # init an instance of cluster
            # get devices of cluster
            status_code, resp = onosapi.get_cluster_devices(ip, clus.id)
            if status_code == 200:
                # get devices list
                devices = (json.loads(resp))['devices']
                for deviceId in devices:
                    dev = Device(deviceId)
                    # init a device and add it to cluster
                    clus.addDevice(dev)
            else:
                print('get devices:{}'.format(status_code))

            status_code, resp = onosapi.get_cluster_links(
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

    status_code, resp = onosapi.get_hosts(ip)
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
    qapp = QtWidgets.QApplication.instance()
    if not qapp:
        qapp = QtWidgets.QApplication(sys.argv)

    app = ApplicationWindow(ti.canvas)
    app.show()
    app.activateWindow()
    app.raise_()
    qapp.exec()


if __name__ == '__main__':
    import matplotlib as mpl
    main()
