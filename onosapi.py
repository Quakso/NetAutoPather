import requests, json
from requests.auth import HTTPBasicAuth

auth = HTTPBasicAuth("karaf", "karaf")


def get_clusters(controller_ip):
    headers = {
        'Accept': 'application/json'
    }
    get_cluster_url = 'http://{}:8181/onos/v1/topology/clusters'.format(
        controller_ip)
    resp = requests.get(url=get_cluster_url, headers=headers, auth=auth)
    return resp.status_code, resp.text


def get_cluster_devices(controller_ip, clusterId):
    headers = {
        'Accept': 'application/json'
    }
    get_device_url = 'http://{}:8181/onos/v1/topology/clusters/{}/devices'.format(
        controller_ip, clusterId)
    resp = requests.get(url=get_device_url, headers=headers, auth=auth)
    return resp.status_code, resp.text


def get_cluster_links(controller_ip, clusterId):
    headers = {
        'Accept': 'application/json'
    }
    get_link_url = 'http://{}:8181/onos/v1/topology/clusters/{}/links'.format(
        controller_ip, clusterId)
    resp = requests.get(url=get_link_url, headers=headers, auth=auth)
    return resp.status_code, resp.text


def get_hosts(controller_ip):
    headers = {
        'Accept': 'application/json'
    }
    get_host_url = 'http://{}:8181/onos/v1/hosts'.format(controller_ip)
    resp = requests.get(url=get_host_url, headers=headers, auth=auth)
    return resp.status_code, resp.text


def post_flow(controller_ip, appId, priority, targetDeviceId, outputPort, inputPort, srcMac, dstMac):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    params = {
        "appId": appId
    }
    data = {
        "priority": priority,
        "timeout": 0,
        "isPermanent": True,
        "deviceId": targetDeviceId,
        "selector": {
            "criteria": [
                {
                    "type": "ETH_TYPE",
                    "ethType": "0x0800"
                },
                {
                    "type": "ETH_DST",
                    "mac": dstMac
                },
                {
                    "type": "ETH_SRC",
                    "mac": srcMac
                },
                {
                    "type": "IN_PORT",
                    "port": inputPort
                }
            ]
        },
        "treatment": {
            "instructions": [
                {
                    "type": "OUTPUT",
                    "port": outputPort
                }
            ]
        }
    }
    post_url = 'http://{}:8181/onos/v1/flows/{}'.format(controller_ip, targetDeviceId)
    resp = requests.post(url=post_url, params=params,
                         headers=headers, auth=auth, data=json.dumps(data))
    return resp.status_code, resp.text


# 删除指定appId的所有流表
def del_flows_by_appId(controller_ip, appId):
    headers = {
        'Accept': 'application/json'
    }
    get_device_url = 'http://{}:8181/onos/v1/flows/application/{}'.format(controller_ip, appId)
    resp = requests.delete(url=get_device_url, headers=headers, auth=auth)
    return resp.status_code, resp.text


# 指定targetDeviceId下发drop流表
def post_flow_drop(controller_ip, appId, targetDeviceId, priority):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    params = {
        "appId": appId
    }
    data = {
        "priority": priority,
        "timeout": 0,
        "isPermanent": True,
        "deviceId": targetDeviceId,
        "selector": {
            "criteria": [
                {
                    "type": "ETH_TYPE",
                    "ethType": "0x0800"
                }
            ]
        },
        "treatment": {
            "instructions": [
                # 没有instruction视作drop
            ]
        }
    }
    post_url = 'http://{}:8181/onos/v1/flows/{}'.format(controller_ip, targetDeviceId)
    resp = requests.post(url=post_url, params=params,
                         headers=headers, auth=auth, data=json.dumps(data))
    return resp.status_code, resp.text


# 获取链路编号，来确定链路是否改变
def get_change_id(controller_ip):
    headers = {
        'Accept': 'application/json'
    }
    get_url = 'http://{}:8181/onos/device-and-host/quakso/checkLinkChange'.format(controller_ip)
    resp = requests.get(get_url, headers=headers, auth=auth)
    return resp.status_code, resp.text


# 开始链路时延监听
def start_delay_detect(controller_ip):
    headers = {
        'Accept': 'application/json'
    }
    get_url = 'http://{}:8181/onos/device-and-host/quakso/delay/start'.format(controller_ip)
    resp = requests.get(get_url, headers=headers, auth=auth)
    return resp.status_code, resp.text


# 停止链路时延监听
def stop_delay_detect(controller_ip):
    headers = {
        'Accept': 'application/json'
    }
    get_url = 'http://{}:8181/onos/device-and-host/quakso/delay/stop'.format(controller_ip)
    resp = requests.get(get_url, headers=headers, auth=auth)
    return resp.status_code, resp.text


# 获取链路时延的Map
def get_delay_map(controller_ip):
    headers = {
        'Accept': 'application/json'
    }
    get_url = 'http://{}:8181/onos/device-and-host/quakso/delay/getMap'.format(controller_ip)
    resp = requests.get(get_url, headers=headers, auth=auth)
    return resp.status_code, resp.text

def get_udp_service_msg(controller_ip):
    headers = {
        'Accept': 'application/json'
    }
    get_url = 'http://{}:8181/onos/device-and-host/quakso/udpMsg'.format(controller_ip)
    resp = requests.get(get_url, headers=headers, auth=auth)
    return resp.status_code, resp.text
