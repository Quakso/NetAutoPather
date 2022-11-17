import requests,json
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

def post_flow(controller_ip,appId,priority,targetDeviceId,outputPort,inputPort,srcMac,dstMac):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    params = {
        "appId": appId
    }
    data={
        "priority":priority,
        "timeout":0,
        "isPermanent":True,
        "deviceId":targetDeviceId,
        "selector": {
            "criteria":[
                {
                    "type":"ETH_TYPE",
                    "ethType":"0x0800"
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
        "treatment":{
            "instructions":[
                {
                    "type":"OUTPUT",
                    "port":outputPort
                }
            ]
        }
    }
    post_url='http://{}:8181/onos/v1/flows/{}'.format(controller_ip, targetDeviceId)
    resp = requests.post(url=post_url, params=params,
                         headers=headers, auth=auth, data=json.dumps(data))
    return resp.status_code, resp.text

def del_flows_by_appId(controller_ip,appId):
    headers={
        'Accept':'application/json'
    }
    get_device_url='http://{}:8181/onos/v1/flows/application/{}'.format(controller_ip,appId)
    resp=requests.delete(url=get_device_url,headers=headers,auth=auth)
    return resp.status_code, resp.text
