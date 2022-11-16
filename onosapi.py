import requests
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