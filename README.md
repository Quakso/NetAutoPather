## 如何实现可交互拖动的拓扑UI

因为在之前的实验中主要通过Python实现下发流表，Python中常用的画图库**matplotlib**，考虑使用matplotlib画出拓扑。

考虑到了交互性，于是查阅matplotlib官方文档寻找实现交互的拓扑可能性(**详见参考资料第二项**)。之后又了解到可以在Qt中加入matplotlib画出的图（**详见参考资料第三项**），于是决定使用PyQt实现简单的交互界面。具体实现可见**作品实现与测试展示**章节的**`TopoInteractor`**中相关描述。

交互拓扑的接口设计可见**`Cluster`**、**`Hosts`**中相关描述。

# 作品实现与测试展示

应用层软件框架如下图所示。

![img](https://uestc.feishu.cn/space/api/box/stream/download/asynccode/?code=MDc1Nzg4OGM5ZjZkYjNhNjkyZTljNTc2OTNjOGZkMmJfalE0WWs1WDJpSDFhQnNBMk9lb3dJNTM3dEJLWXVqUzlfVG9rZW46Ym94Y25yaXRmb2dWSzRkc0Q1cmlSWnpCVXIyXzE2ODA0MzU4NjY6MTY4MDQzOTQ2Nl9WNA)

应用层软件框架图

应用层主要由接口层、组件层和交互层构成。各源代码文件的层级分布如下图所示。

![img](https://uestc.feishu.cn/space/api/box/stream/download/asynccode/?code=NzNiZTU3MWRkM2Q5YjM2NTU0MjJkOWIzYTQ3MjNhMTdfMzFscTRjaUtRcENuczJmS0dESmF6TXdKYTRkM3l3MFhfVG9rZW46Ym94Y25FenNYQVA3ZWxPang0RmtRNXVFZXlmXzE2ODA0MzU4NjY6MTY4MDQzOTQ2Nl9WNA)

应用层软件分层结构

下面开始从接口层开始自下而上详细阐释设计与实现。

## 接口层详细设计与实现

### onosapi.py

主要包含需要使用到的 HTTP API 封装的函数。

| **函数名**          | **参数**                                                     | **含义**                                                     | **HTTP API**                                                 |
| ------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| get_cluster         | controller_ip                                                | 获取当前拓扑中簇的信息                                       | http://{controller_ip}:8181/onos/v1/topology/clusters        |
| get_cluster_devices | controller_ip, clusterId                                     | 获取某簇下的所有交换机的信息                                 | http://{controller_ip}:8181/onos/v1/topology/clusters/{clusterId}/devices |
| get_cluster_links   | controller_ip, clusterId                                     | 获取某簇下的所有连接信息                                     | http://{controller_ip}:8181/onos/v1/topology/clusters/{clusterId}/links |
| get_hosts           | controller_ip                                                | 获取当前拓扑中所有主机信息                                   | http://{controller_ip}:8181/onos/v1/hosts                    |
| post_flow           | controller_ip, appId, priority, targetDeviceId, outputPort, inputPort, srcMac, dstMac | 下发流表，指定appId，优先级，目标交换机id，匹配对应端口与源Mac地址和目的Mac地址，往目的端口转发 | http://{controller_ip}:8181/onos/v1/flows/{targetDeviceId}   |
| del_flows_by_appId  | controller_ip，appId                                         | 删除所有包含对应appId的流表                                  | http://{controller_ip}:8181/onos/v1/flows/application/{appId} |
| post_flow_drop      | controller_ip, appId,  targetDeviceId, priority              | 下发drop流表，指定优先级与目标交换机Id                       | http://{controller_ip}:8181/onos/v1/flows/{appId}            |
| get_change_id       | controller_ip                                                | 获取链路改变的信息                                           | http://{controller_ip}:8181/onos/sdn-app/quakso/checkLinkChange |
| start_delay_detect  | controller_ip                                                | 开始时延检测                                                 | http://{controller_ip}:8181/onos/sdn-app/quakso/delay/start  |
| stop_delay_detect   | controller_ip                                                | 停止时延检测                                                 | http://{controller_ip}:8181/onos/sdn-app/quakso/delay/stop   |
| get_delay_map       | controller_ip                                                | 获取时延的Map                                                | http://{controller_ip}:8181/onos/sdn-app/quakso/delay/getMap |
| get_udp_service_msg | controller_ip                                                | 获取捕获到的udp包的信息                                      | http://{controller_ip}:8181/onos/sdn-app/quakso/udpMsg       |

上述封装好的api供interactor.py中的TopoInteractor调用。

## 组件层的详细设计与实现

### topobase.py

此文件主要包含构建拓扑所需要的基础类，包括主机（Host）、主机列（Hosts）、拓扑（Topo）、交换机（Device）、连接（Link）、簇（Cluster）。

#### Host

表示主机的类，其各成员变量如下表所示。这里只考虑了Host只连接一个交换机，只有一个ip地址。

| 名称    | 类型 | 含义                                                         |
| ------- | ---- | ------------------------------------------------------------ |
| id      | str  | 表示主机的Id，初始值默认为`''`                               |
| ip      | str  | 表示主机的ip，初始值默认为`''`                               |
| pos     | dict | 表示主机在构建的极坐标图中的位置，有两个键：'r' (极径) 和'a' (极角)，初始化为`{'r': 0, 'a': 0}` |
| devId   | str  | 表示Host所连接的交换机的Id                                   |
| devPort | str  | 表示Host所连接的交换机的端口号                               |
| devPos  | dict | 表示Host所连接的交换机的位置，有两个键：'r' (极径) 和'a' (极角)，初始化为`{'r': 0, 'a': 0}` |

Host的构造方法（ __init__ ）需传入dict，其与onos提供的api中返回的json结果的结构对应，如下所示。

```JSON
{'id': '', 'ipAddresses': [''], 'locations': [{'elementId': '', 'port': ''}]}
```

Host类所含方法及其解释如下表。

| 方法名      | 参数 | 返回值类型 | 含义                                                         |
| ----------- | ---- | ---------- | ------------------------------------------------------------ |
| getSimpleId | -    | str        | 获取Host Id的简单表示，例如`00:00:00:00:00:01/None`即可表示为`h1``00:00:00:00:00:0A/None`即可表示为`h10` |

#### Device

表示交换机的类，其各成员变量如下表。

| 名称     | 类型       | 含义                                                         |
| -------- | ---------- | ------------------------------------------------------------ |
| id       | str        | 表示交换机的Id，初始值默认为`''`                             |
| pos      | dict       | 表示交换机在构建的极坐标图中的位置，有两个键：`'r'` (极径) 和`'a' `(极角)，初始化为`{'r': 0, 'a': 0}` |
| hostList | list[Host] | 表示交换机下所连接的主机列表，每个list元素类应当为`Host`     |

Device类的构造方法需要传入交换机的Id。其所含成员方法及其解释如下表。

| 方法名      | 参数      | 返回值类型 | 含义                                                         |
| ----------- | --------- | ---------- | ------------------------------------------------------------ |
| addHost     | host:Host | -          | 将主机添加到交换机的`hostList`中                             |
| rmHost      | host:Host | -          | 将主机从交换机的`hostList`中移除                             |
| getSimpleId | -         | str        | 获取交换机Id的简单表示，例如:`of:0000000000000001`即可表示为`s1``of:000000000000000A`即可表示为`s10` |

#### Link

表示连接的类，其各成员变量如下表所示。

| 名称       | 类型 | 含义                                               |
| ---------- | ---- | -------------------------------------------------- |
| srcDevId   | str  | 连接的源交换机id                                   |
| srcDevPort | str  | 连接的源交换机端口号                               |
| dstDevId   | str  | 连接的目的交换机id                                 |
| dstDevPort | str  | 连接的目的交换机的端口号                           |
| type       | str  | 连接的类型                                         |
| srcPos     | dict | 连接的源交换机的位置，初始化为`{'r': 0, 'a': 0}`   |
| dstPos     | dict | 连接的目的交换机的位置，初始化为`{'r': 0, 'a': 0}` |

Link的构造方法（ __init__ ）需传入dict，其与onos提供的api中返回的json结果的结构对应，如下所示。

```Python
{
      "src": {
        "port": "4",
        "device": "of:0000000000000002"
      },
      "dst": {
        "port": "1",
        "device": "of:0000000000000006"
      },
      "type": "DIRECT",
      "state": "ACTIVE"
}
```

#### Cluster

表示簇的类，一个簇即一个连通图。其成员变量如下表所示。

| 名称        | 类型         | 含义                           |
| ----------- | ------------ | ------------------------------ |
| id          | str          | 簇的id                         |
| deviceCount | str          | 簇中交换机的数目               |
| linkCouont  | str          | 簇中连接的数目                 |
| root        | str          | 簇中根交换机的id，例如         |
| deviceList  | list[Device] | 簇中交换机的列表，初始化为`[]` |
| linkList    | list[Link]   | 簇中连接的列表，初始化为`[]`   |

Cluster的构造方法（ __init__ ）需传入dict，其与onos提供的api中返回的json结果的结构对应，如下所示。

```Python
{
      "id": 0,
      "deviceCount": 6,
      "linkCount": 20,
      "root": "of:0000000000000001"
}
```

Cluster类所含成员方法及其解释如下表。

| 方法名     | 参数                            | 返回值类型 | 含义                                                         |
| ---------- | ------------------------------- | ---------- | ------------------------------------------------------------ |
| addDevice  | device:Device                   | -          | 将交换机添加到簇的交换机列表中                               |
| addLink    | link:Link                       | -          | 将连接添加到簇的连接列表中                                   |
| setDevPos  | evenR，centerR=0.0，centerA=0.0 | -          | 设定簇下交换机列表中交换机的初始位置，`evenR`指的是各交换机分布所在圆的半径，`centerR`指的是该簇中心的分布所在圆的半径，`centerA`指的是该簇中心分布所在圆的角度。具体解析见下文。 |
| setLinkPos | -                               | -          | 设定簇下连接列表中连接的`srcPos`和`dstPos`，即源交换机和目的交换机的位置 |
| getDevById | devId:str                       | -          | 获取簇下对应devId的交换机，有则返回，无则返回None            |
| linkExist  | link:Link                       | bool       | 判断连接在簇中是否存在，因为onos api返回的连接存在重复，即源和目的以及目的和源算作两种连接。此方法判断是否存在这种重复，主要根据参数link的srcDevId与已有的link的dstDevId是否相同参数link的dstDevId与已有的link的srcDevId是否相同参数link的srcPort与已有的link的dstPort是否相同参数link的dstPort与已有的link的srcPort是否相同这四点来判断是否重复，对应关键代码：`for li in self.linkList:    if li.srcDevId == link.dstDevId and li.dstDevId == link.srcDevId and li.srcPort == link.dstPort and li.dstPort == link.srcPort:        return True return False` |

`setDevPos`的具体解析：

- 因为需要尽可能分布得平均，所以考虑使用极坐标表示位置，让同一簇的交换机均匀地分布在半径为`evenR`圆上，形如下图。

![img](https://uestc.feishu.cn/space/api/box/stream/download/asynccode/?code=NDk3MTU2N2Q4YWFkMTA0NDNmYmVmMjE4MmM0YTM1NmNfNklLRUJlRG5sdHZ5WFdxV3FwdEY3M1R0V3pHVkk2SkdfVG9rZW46Ym94Y25oNTd1ZUl6RDdRQzg2WmtRQkl0Y2JIXzE2ODA0MzU4NjY6MTY4MDQzOTQ2Nl9WNA)

同簇交换机分布图

有公式：

$$$$\begin{cases}r=evenR\\ \theta=theta \end{cases} $$$$

此时，交换机有`pos`值为`{'r':evenR,'a':theta}`，其中`theta`为交换机被分配到的极角。例如，上图交换机的极角列表为`[0,np.pi/3,2*np.pi/3,np.pi,4*np.pi/3,5*np.pi/3]`

- 对于有多个簇的的拓扑，采取让簇的中心分布在半径为`centerR`圆上的方案，形如下图。

![img](https://uestc.feishu.cn/space/api/box/stream/download/asynccode/?code=NjExYTFjMWRiZTBjNjU4OTg5OTQ1YTVkNDI0YWRhZDZfUnZxemlqanBjVmcxRjNDS01VYkZDTDV5RnROMUlnRFNfVG9rZW46Ym94Y25mVjBKREhZMTZnbzNmT2tBWUtxWmhCXzE2ODA0MzU4NjY6MTY4MDQzOTQ2Nl9WNA)

多簇交换机分布图

于是，交换机的位置需要经过一定的公式变换：

$$\begin{cases} r'=\sqrt{evenR^2+centerR^2-2*evenR*centerR*\cos(\pi+centerA-theta)} \\ \theta'=\arcsin(\frac{evenR*\sin(\pi+centerA-theta)}{centerR} )+centerA \end{cases} $$

其中*`centerA`*对应该簇分配到的极角。例如，上图簇的极角列表为`[0,2*np.pi/3,4*np.pi/3]`

*`theta`*即为前面所求得的交换机分配到的极角（相对于簇中心）。

#### Hosts

表示拓扑中的主机列，其主要成员变量如下表所示。

| 名称     | 类型       | 含义             |
| -------- | ---------- | ---------------- |
| hostList | list[Host] | 拓扑中的主机列表 |
|          |            |                  |

其主要成员方法的列表如下所示。

| 方法名            | 参数                  | 返回值类型 | 含义                                                         |
| ----------------- | --------------------- | ---------- | ------------------------------------------------------------ |
| addHost           | host:Host             | -          | 向主机列中添加主机                                           |
| attachTo          | cluster:Cluster       | -          | 将主机列依附到簇上。根据host的交换机Id找到cluster的交换机列表中的交换机，将host加入交换机的主机列表，并设置其`devPos`变量为对应交换机的位置。 |
| detachFrom        | cluster:Cluster       | -          | 将主机列从簇上分离。根据host的交换机Id找到cluster的交换机列表中的交换机，将host移出交换机的主机列表。 |
| setPosRelateToDev | cluster:Cluster,evenR | -          | 设定主机列中各主机的位置，`evenR`指的是各主机分布所在圆的半径。具体解析见下文。 |
| clear             | -                     | -          | 清除主机列中的所有主机                                       |

setPosRelateToDev解析：

类似于前面所述的多个簇的情况，一个簇中可能有多个交换机，一个交换机可能连接多个主机，将主机平均的放在以交换机为中心的圆上，形如下图。

![img](https://uestc.feishu.cn/space/api/box/stream/download/asynccode/?code=YTVmMDQ2MDMyOGQ4ODc2YzllYTkwMzYyYTAxZGZhMzFfeE16WXpvbHlsWGFuYm5JbjBNVDczZnBIZGZ3aFBWSEhfVG9rZW46Ym94Y255c09WMTlOMHFJUmNqMmhZZFFrdjRkXzE2ODA0MzU4Njc6MTY4MDQzOTQ2N19WNA)

单簇交换机主机分布图

根据前文所述的公式算法，我们已知各交换机的位置，各主机的位置计算有如下公式：

$$\begin{cases} r_{host}=\sqrt{evenR_{host}^2+r_{dev}^2-2*evenR_{host}*r_{dev}*\cos(\pi+\theta_{dev}-theta)}\\ \theta_{host}=\arcsin(\frac {evenR_{host}*\sin(\pi+\theta_{dev}-theta)} {r_{dev}})+\theta_{dev} \end{cases} $$

*其中**`r_dev`*指的是主机所连交换机的极径，*`θ_dev`*指的是主机所连交换机的极角，*`evenR_host`*指的是设置的主机围绕交换机的圆的半径，*`theta`*指的是该主机被分配到的极角（以交换机为中心）。例如上图中右上角有主机极角列表`[0,2*np.pi/3,4*np.pi/3]`。

#### Topo

表示拓扑的类，其成员变量如下表所示。

| 名称        | 类型          | 含义                 |
| ----------- | ------------- | -------------------- |
| clusterList | list[Cluster] | 表示该拓扑下的簇列表 |
| hosts       | Hosts         | 表示该拓扑下的主机列 |

Topo的构造方法（__init__）中会调用Hosts的attachTo方法，将拓扑中的主机依附到各个簇上。

其各成员方法如下表所示。

| 方法名     | 参数                                | 返回值类型 | 含义                                                         |
| ---------- | ----------------------------------- | ---------- | ------------------------------------------------------------ |
| initAllPos | deviceEvenR，hostEvenR，centerR=0.0 | -          | 初始化拓扑下所有交换机和主机的位置，同时确定Link的src和dst的位置。针对各个簇调用`setDevPos`，`setLinkPos`；针对主机列调用`setPosRelateToDev`；如此将所有的主机和交换机以及连接的位置进行初始化。`deviceEvenR`为设定的同簇交换机分布所在圆的半径，`hostEvenR`为设定的同交换机的主机分布所在圆的半径，`centerR`为多簇情况下各簇中心分布所在圆的半径。 |
|            |                                     |            |                                                              |

### graphy.py

#### Point

表示算法图中的一个点，对应拓扑中交换机id和端口号构成的连接节点。其成员变量如下表。

| 名称       | 类型 | 含义                     |
| ---------- | ---- | ------------------------ |
| deviceId   | str  | 表示该连接节点的交换机id |
| devicePort | -    | 表示该连接节点的端口号   |

为了能让Point类作为键值，需要重写__eq__和__hash__方法，如下代码所示

```Python
def __eq__(self, __o: object) -> bool:
    if not isinstance(__o, Point):
        raise TypeError('need a point')
    return (self.deviceId, self.devicePort) == (__o.deviceId, __o.devicePort)

def __hash__(self) -> int:
    return hash((self.deviceId, self.devicePort))
```

其余成员方法见下表。

| 方法名   | 参数 | 返回值类型 | 含义                                                         |
| -------- | ---- | ---------- | ------------------------------------------------------------ |
| toString | -    | str        | 获取该连接节点的字符串表示。例如，交换机Id为`of:0000000000000001`，端口号为`1`其字符串表示即为`of:0000000000000001/1` |

#### Graph

用于构建算法图，实现选路算法的类，其各成员变量如下表所示。

| 名称         | 类型        | 含义                                                         |
| ------------ | ----------- | ------------------------------------------------------------ |
| weightMatrix | dict        | 权重矩阵，用来存放图中各`Point`之间的权重，主要是使用测得的延迟作为权重。处于不同交换机端口之间的`Point`之间的权重缺省值为1（用常量`__DEFAULT_WEIGHT`表示），不可达的两个`Point`之间权重缺省值为999（用常量`__MAX_WEIGHT`表示） |
| pointList    | list[Point] | 图中所有连接节点的列表，初始化为`[]`                         |

![img](https://uestc.feishu.cn/space/api/box/stream/download/asynccode/?code=ZTYzZTlmOWVkZGNkNDI4MjNlZTZlZjBmNjM3YmZmY2FfejBhN2dqYTdlWUl5NThjSVRtZE9WMUxUeFR1WE9uajFfVG9rZW46Ym94Y25zQlFReUkxT3ZKeXJQVm5nZ2FneEliXzE2ODA0MzU4Njc6MTY4MDQzOTQ2N19WNA)

交换机连接点示意图

例如，上图中`weightMatrix`的结构大致如下所示。

```Python
{
    Point1:{
        Point2:0,
        Point3:1,
        Point4:999
    }, 
    Point2:{
        Point1:0,
        Point3:999,
        Point4:999
    },
    Point3:{
        Point1:1,
        Point2:999,
        Point4:999
    },
    Point4:{
        Point1:999,
        Point2:999,
        Point3:999
    }
}
```

Graph类各成员方法如下表。

| 方法名                 | 参数          | 返回值类型 | 含义                                                         |
| ---------------------- | ------------- | ---------- | ------------------------------------------------------------ |
| readTopo               | topo:Topo     | -          | 读取`Topo`，根据拓扑结构，构建出其所包含的所有连接节点`Point`，同时初始化`weightMatrix`的结构。构建的`Point`主要来源于拓扑的主机列表。主机会连接到某交换机的某端口，因此每个主机可以看作一个`Point`。拓扑的连接列表。每个连接会有源和目的节点，指明了源交换机id、源端口号、目的交换机id、目的端口号，因此每个连接会得到两个`Point`。 |
| printMap               | -             | -          | 在终端打印出`weightMatrix`中的值，如下图。![img](https://uestc.feishu.cn/space/api/box/stream/download/asynccode/?code=N2M0NDI3MmZjMWY5MWNkNTBmN2MxMjFiY2RhNjViYmNfWjJBNjN4Rm9HemxIdUkxMG5tRU5JQUFwS0hsRHRtMVpfVG9rZW46Ym94Y25tM2c1bHpYUmRqSEFhTmlPaXdxOGtjXzE2ODA0MzU4Njc6MTY4MDQzOTQ2N19WNA) |
| getSameDevicePointList | point:Point   | -          | 获取和指定`Point`在相同交换机上的`Point`列表                 |
| dijistra               | point:Point   | dict       | 执行一次dijistra算法，指定起始Point，返回一个字典，该字典中记录：键为目的Point值为从起始Point按最短路径到目的Point的前一个Point因此通过该字典即可得出一个最小生成路径树。 |
| getMinWeightPoint      | dict:dict     | Point      | 获取dict中最低权重的Point，即根据最小的键值获取键            |
| putDelayMap            | delayMap:dict | -          | 将接口获取到的时延检测结果放入`weightMatrix`中，对于获取到的空值就默认置为1。 |

### interactor.py

#### TopoInteractor

表示交互拓扑的类，主要使用`matplotlib`库构建这个可交互的拓扑。其各成员变量如下表

| 名称                   | 类型             | 含义                                                         |
| ---------------------- | ---------------- | ------------------------------------------------------------ |
| topo                   | Topo             | 表示当前拓扑交互图中所承载的拓扑                             |
| graph                  | Graph            | 表示拓扑对应的算法图                                         |
| hosts                  | Hosts            | 表示当前拓扑中的所有主机                                     |
| ax                     | axes             | 表示拓扑图所在的极坐标系                                     |
| canvas                 | FigureCanvasBase | 表示绘制图形的画布                                           |
| devLinkColor           | str              | 表示交换机之间连接线的颜色                                   |
| hostLinkColor          | str              | 表示主机与交换机连接的颜色                                   |
| devMarkerSize          | int              | 交换机的图像大小                                             |
| hostMarkSize           | int              | 主机的图像大小                                               |
| devEvenR               | float            | 交换机所在簇的圆半径                                         |
| hostEvenR              | float            | 连接同交换机的主机所在圆的半径                               |
| centerR                | float            | 不同簇到坐标系中心的距离，默认为0                            |
| devR                   | list             | 暂存的所有交换机极径列表                                     |
| devA                   | list             | 暂存的所有交换机极角列表                                     |
| hostR                  | list             | 暂存的所有主机极径列表                                       |
| hostA                  | list             | 暂存的所有主机极角列表                                       |
| linkLines              | list             | 所有交换机之间的link暂存的始末点信息                         |
| hostLines              | list             | 所有主机与交换机之间link暂存的始末点信息                     |
| pick_point             | int              | 表示当前选中的设备类型，有三种常量：`__PICK_NOTHING`未选中任何设备`__PICK_HOST`选中了主机`__PICK_DEVICE`选中了交换机会需要根据选中的设备类型，在合适位置显示选中设备的简要信息。 |
| pick_host              | Host             | 表示选中的主机                                               |
| pick_device            | Device           | 表示选中的交换机                                             |
| drag_point             | -                | 表示当前鼠标拖动选中的设备，有两种类型，Host和Device         |
| drag_radius_dev        | int              | 判断拖动选中交换机的命中距离，默认为0.5。命中后即处于可拖动状态。![img](https://uestc.feishu.cn/space/api/box/stream/download/asynccode/?code=NmFlMDE2ZDAwYjNlOTI2M2JmMGFhNWM0YWZhMGI5YjVfYnVlY2Y4Vng3TlM5d0c4a3REYTduS2trWlVIVlIxckxfVG9rZW46Ym94Y25QYkhhZmw0N05QbUlCdVB6MXJKclpkXzE2ODA0MzU4Njc6MTY4MDQzOTQ2N19WNA) |
| drag_radius_host       | int              | 判断拖动选中主机的命中距离，默认为0.3。命中后即处于可拖动状态。![img](https://uestc.feishu.cn/space/api/box/stream/download/asynccode/?code=MGViZjZkMmRlMzM1MGQ3OTM0ZTdiNzMxMGQ1YjI5MjFfbnRUR20wZHM0TGo5cEFBZWJtRHd3ZXNsdklOeUNSalFfVG9rZW46Ym94Y25YSjQxM1R4UlZ1dGpCeEswMmFYN3NnXzE2ODA0MzU4Njc6MTY4MDQzOTQ2N19WNA) |
| host_visible           | bool             | 主机是否可见，默认为True                                     |
| id_text_visible        | bool             | 主机和交换机的id是否可见，默认为False                        |
| delay_visible          | bool             | 时延信息是否可见，默认为False                                |
| show_simple_id         | bool             | 是否简单显示主机和交换机的id，默认为True                     |
| show_simple_delay      | bool             | 是否简单显示时延信息，默认为True                             |
| choose_point           | bool             | 是否进入直接点击主机选路模式                                 |
| task_2_host            | list             | 表示选中的两个主机                                           |
| pathColorList          | list             | 表示为两个主机选路后的显示路径的颜色列表`['#FFFFCC', '#00EC00', '#2894FF', '#4A4AFF', '#FFB5B5']` |
| colorWheel             | int              | 颜色轮盘。每选中一个颜色，轮盘的值就加一并且对pathColorList长度取余`self.colorWheel = (self.colorWheel + 1) % len(self.pathColorList)` |
| appId                  | str              | 下发流表的appId                                              |
| changeId               | str              | 记录链路改变状态的Id，可从`onosapi`中的`get_change_id`接口获取 |
| linkListen             | bool             | 监听链路改变的标志，用于判断线程停止为`True`表示正在进行链路改变监听为`False`表示停止链路改变监听 |
| linkListenThread       | threading.Thread | 链路改变监听线程常量`__CHECK_LINK_INTERVAL`表示检查链路改变的时间间隔，为3s |
| udpServiceId           | str              | 记录未能转发UDP包的id，可从`onosapi`中的`get_udp_service_msg`接口获取 |
| udpServiceListen       | bool             | 监听未能转发UDP包的标志，用于判断线程停止为`True`表示正在进行监听为`False`表示停止监听 |
| udpServiceListenThread | threading.Thread | 监听未能转发UDP包线程常量`__CHECK_UDP_INTERVAL`表示检查未能转发UDP包的时间间隔，为3s |
| delayListen            | bool             | 持续获取时延Map的标志，用于判断线程停止为`True`表示正在持续获取为`False`表示停止持续获取 |
| getDelayThread         | threading.Thread | 获取时延Map的线程常量`__CHECK_DELAY_INTERVAL`表示获取时延Map的时间间隔，为3s |
| controller_ip          | str              | 表示控制器的IP地址                                           |

其各成员方法如下表

| 方法名                    | 参数                                                         | 返回值类型 | 含义                                                         |
| ------------------------- | ------------------------------------------------------------ | ---------- | ------------------------------------------------------------ |
| change_show_simple_delay  | -                                                            | -          | 改变是否显示时延                                             |
| setCenterR                | -                                                            | -          | 设定各个簇所在圆的半径，一个簇时不需要设置，多个簇时为交换机所在圆的半径的2.5倍 |
| change_show_simple_id     | -                                                            | -          | 改变是否简单显示交换机和主机的id                             |
| confirm_choose_path       | -                                                            | -          | 对于选中的两个主机确认进行选路，会调用pathBetween2Hosts      |
| change_choose_hose        | -                                                            | -          | 改变是否进行点击选路                                         |
| change_delay_visible      | -                                                            | -          | 确定是否在链路上显示时延                                     |
| chage_host_visible        | -                                                            | -          | 改变是否显示主机                                             |
| change_id_visible         | -                                                            | -          | 确定是否显示交换机和主机的id                                 |
| draw_path                 | pre:dict dijistra选路选出的路径节点数组p_end:Point路径结尾的节点h_begin:Host路径开始的主机h_end:Host路径结束的主机 | -          | 画出两主机之间的选路                                         |
| init_ax                   | -                                                            | -          | 初始化坐标轴                                                 |
| redraw_text               | -                                                            | -          | 重新画出界面上的文字                                         |
| clear_list                | -                                                            | -          | 清除画线和点的列表                                           |
| on_mouse_move             | -                                                            | -          | 鼠标拖动时调用，如果鼠标左键按下且drag_point非空，那么需要重新画图 |
| on_button_release         | -                                                            | -          | 鼠标按键弹开时调用，设置drag_point为None                     |
| on_button_press           | -                                                            | -          | 鼠标按键按下时调用，当按下为鼠标左键时，找到最近的主机或交换机的位置，设置drag_point为该主机或交换机 |
| get_drag_point            | -                                                            | -          | 通过计算获取最近的主机或交换机点，返回drag_point             |
| redraw_dev                | -                                                            | -          | 重新画出交换机                                               |
| redraw_host               | -                                                            | -          | 重新画出主机以及主机和交换机的连线                           |
| draw_topo                 | -                                                            | -          | 画出整个拓扑                                                 |
| get_devices_radius_angles | -                                                            | -          | 将交换机的所处的极角和极径放入辅助画图数组，便于画出交换机   |
| get_hosts_radius_angles   | -                                                            | -          | 将主机所处的极角和极径放入辅助数组，便于画出主机             |
| get_host_src_dst          | -                                                            | -          | 获取主机和交换机连线的源点和目的点，放入辅助数组，便于画出主机和交换机的连线 |
| get_link_src_dst          | -                                                            | -          | 获取各个连线的源点和目的点，放入辅助数组，便于画出各个交换机间连线 |
| draw_devices              | -                                                            | -          | 画出所有交换机                                               |
| draw_links                | -                                                            | -          | 画出所有连线（主机和交换机，交换机和交换机）                 |
| draw_delay_weight         | -                                                            | -          | 在交换机线路上画出所有的时延权重                             |
| refreshTopo               | -                                                            | -          | 刷新拓扑，获取拓扑信息                                       |
| getDelay2Graph            | -                                                            | -          | 将获取到的时延放入graph类，便于进行选路                      |
| getDelayThreadFunc        | -                                                            | -          | 获取时延线程所执行的函数                                     |
| startGetDelayThread       | -                                                            | -          | 开启时延获取线程                                             |
| stopGetDelayThread        | -                                                            | -          | 停止时延获取线程                                             |
| changeGetDelay            | -                                                            | -          | 改变时延的获取，正在获取时关闭线程，不在获取开启线程         |
| startDelayDetect          | -                                                            | -          | 开启onos插件的时延检测线程，调用接口层的start_delay_detect   |
| stopDelayDetect           | -                                                            | -          | 停止onos插件的时延检测线程，调用接口层的stop_delay_detect    |
| pathBetween2HostsByIp     | beginHostIpendHostIp                                         | -          | 根据host的IP在两host之间执行选路和下发流表                   |
| pathBetween2Hosts         | beginHostendHost                                             | -          | 在两个host之间选路下发流表                                   |
| pathForAllHosts           | -                                                            | -          | 为所有的主机之间进行选路                                     |
| checkLinkChange           | -                                                            | -          | 调用接口层get_change_id根据获得的changeId是否与原来相同来判断链路改变 |
| startLinkListenThread     | -                                                            | -          | 开启链路改变监听线程，会确定当前是否有链路监听，有则不重复开启，无则开启新的线程 |
| stopLinkListenThread      | -                                                            | -          | 停止链路改变监听线程                                         |
| checkUdpService           | -                                                            | -          | 检测udp服务是否正常，调用get_udp_service_msg                 |
| udpServiceThreadFunc      | -                                                            | -          | 检测udp服务线程所执行的函数                                  |
| startUdpServiceThread     | -                                                            | -          | 开启udp服务的线程                                            |
| stopUdpServiceThread      | -                                                            | -          | 停止udp服务的线程                                            |
| deleteAllAddedFlows       | -                                                            | -          | 删除所有添加的流表                                           |
| postDropFlow2AllDev       | -                                                            | -          | 对所有的交换机下发drop流表，调用接口层post_flow_drop         |
|                           |                                                              |            |                                                              |

## 交互层详细设计与实现

### sdnAppInterface.py

使用Qt Designer自动生成，首先在Qt Designer上设计号界面的大致框架如下图所示

![img](https://uestc.feishu.cn/space/api/box/stream/download/asynccode/?code=YzNhNzg3YjM2ODNlYWFjZDIxMmMwZGUzMWRkMGYwY2JfcVR6NU1zbWVUdnRyMk5Ka1ZyeFd5TzRaTGRKdkN4aVlfVG9rZW46Ym94Y25Zc1JuVDlVbVVvT3hZT0lXNW5FUDRiXzE2ODA0MzU4Njc6MTY4MDQzOTQ2N19WNA)

界面框架示意图

主要分为左侧的拓扑图显示栏和右侧的控制栏。之后使用如下命令生成组件界面的py文件。

```Python
pyuic ./sdnAppInterface.ui -o sdnAppInterface.py
```

左侧拓扑图最终显示效果和界面元素的解释如下图：

![img](https://uestc.feishu.cn/space/api/box/stream/download/asynccode/?code=OGQ1ZDI5MmFmNjYwZTMwOTZmNGRiNzc1OTNmNWZiZDRfam1wZkszM1d4bXh2RHFpY1BDQ0dyWFRhbVdYWGZQdVhfVG9rZW46Ym94Y253MFJwQ0JVdzR0VGdSdWFjN3J4bDNiXzE2ODA0MzU4Njc6MTY4MDQzOTQ2N19WNA)

界面元素介绍图（一）

![img](https://uestc.feishu.cn/space/api/box/stream/download/asynccode/?code=Njg5MjBlMGJjNWU1MjYzMTllNGM1MWVmN2Q1NDViYmRfd3ptT0E2ZlRvZTZxa3NzOUU1MktpQXFFN0FxYkdsdjdfVG9rZW46Ym94Y25lSHRGNkpMdnZ3M0pWamg4dlRHOG5nXzE2ODA0MzU4Njc6MTY4MDQzOTQ2N19WNA)

界面元素介绍图（二）

![img](https://uestc.feishu.cn/space/api/box/stream/download/asynccode/?code=YzliMDY5OTZlMTczYjNiNTFhOTliOTA3NGI0ZjM5NjJfdTNodHNZd2R5SHBNZlFpTjRLMnM0TGxLa1BmcWZMR09fVG9rZW46Ym94Y25jYzlnR3VwRXduWmVJQnVKOU91dXZlXzE2ODA0MzU4Njc6MTY4MDQzOTQ2N19WNA)

界面元素介绍图（三）

![img](https://uestc.feishu.cn/space/api/box/stream/download/asynccode/?code=MDQ2NmNkZmYyNjU5ZDk3NDg4NGQ1OTNmMjdjMWUyYjhfWDVpRHliamNZYnc0Uk5vWko0UTduTnhVQWtaQVE1NVdfVG9rZW46Ym94Y25JNGN6cmM0SEhJSDhzd0JxR1lMcWdlXzE2ODA0MzU4Njc6MTY4MDQzOTQ2N19WNA)

界面元素介绍图（四）

右侧控制栏的界面如下图所示

![img](https://uestc.feishu.cn/space/api/box/stream/download/asynccode/?code=NzVkZjhhZmE2NTQ0Zjk3YzlhODA4NTYwODkxNjFkN2FfdGQxWXZFdXdqemViUTNpVVhtOU1VcFpoYzhZNjRZMURfVG9rZW46Ym94Y25mNDFDNHNMTjlTQWxSTXhRcE9WdEhjXzE2ODA0MzU4Njc6MTY4MDQzOTQ2N19WNA)

控制栏界面示意图

### qssLoader.py

#### QSSLoader

加载qss文件，含有静态方法

```Python
@staticmethod
def read_qss_file(qss_file_name):
    with open(qss_file_name,'r',encoding='UTF-8') as file:
        return file.read()
```

### sdnApp.qss

渲染界面的qss文件，主要是对`QPushButton、QLineEdit、QLabel、QCheckBox`的样式自定义，语法与CSS类似

### sdnApp.py

程序的入口文件

#### ApplicationWindow

应用主窗口类，继承`QMainWindow`和生成的`sdnAppInterface.py`中的`Ui_MainWindow`类，

其构造方法中，使用`Ui_MainWindiw::setupUi`直接设置好界面。连接各`QPushBotton`的`clicked`信号与对应的槽；初始化各`QCheckBox`的状态，连接`clicked`信号与对应槽；初始化`QLineEdit`的文字。将`TopoInteractor`中的画布`canvas`以Widget形式放入左侧的布局`TopoLayout`中。信号与槽的连接如下表。

| 信号                           | 槽                                         |
| ------------------------------ | ------------------------------------------ |
| BtnDropFlow::clicked()         | TopoInteractor::postDropFlow2AllDev()      |
| BtnRefreshTopo::clicked()      | ApplicationMainWindow::refreshTopo()       |
| BtnDeleteFlow::clicked()       | TopoInteractor::deleteAllAddedFlows()      |
| BtnStartDelayDetect::clicked() | TopoInteractor::startDelayDetect()         |
| BtnStopDelayDetect::clicked()  | TopoInteractor::stopDelayDetect()          |
| BtnStartLinkListen::clicked()  | TopoInteractor::startLinkListenThread()    |
| BtnStopLinkListen::clicked()   | TopoInteractor::stopLinkListenThread()     |
| BtnPathForAllHost::clicked()   | TopoInteractor::pathForAllHost()           |
| BtnConfirmPath::clicked()      | ApplicationMainWindow::confirm_path()      |
| BtnStartUdpService::clicked()  | TopoInteractor::startUdpServiceThread()    |
| BtnStopUdpService::clicked()   | TopoInteractor::stopUdpServiceThread()     |
| CheckIdVisible::clicked()      | TopoInteractor::change_id_visible()        |
| CheckHostVisible::clicked()    | TopoInteractor::change_host_visible()      |
| CheckDelayVisible::clicked()   | TopoInteractor::change_delay_visible()     |
| CheckSimpleId::clicked()       | TopoInteractor::change_show_simple_id()    |
| CheckSimpleDelay::clicked()    | TopoInteractor::change_show_simple_delay() |
| CheckChooseHost::clicked()     | TopoInteractor::changeGetDelay()           |