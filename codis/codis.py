#!/usr/bin/env python
#-*- coding:utf-8 -*-

import sys
import os
import re
import json
import requests

from codis_config import Config
from codis_config import NodeType
from common.zabbix import Zabbix
from common.cmds import cmds
from optparse import OptionParser
from kazoo.client import KazooClient
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class Codis(object):        
    def __init__(self, port=None):
        self.port = port

    def get_ip(self,node_type=None):
        if Config.auto_discovery_node_ip:
            cmdstr = "ifconfig -a|grep inet|grep -v 127.0.0.1|grep -v inet6|awk '{print $2}'|tr -d \"addr:\""
            c2 = cmds(cmdstr, timeout=3)
            stdo = c2.stdo()
            stde = c2.stde()
            retcode = c2.code()
            
            (stdo_list, stde_list) = (re.split("\n", stdo), re.split("\n", stde))
            return stdo_list[1]
        else:
            if node_type == NodeType.Dashboard:
                return Config.codis_dashboard_ip
            elif node_type == NodeType.Proxy:
                return Config.codis_proxy_ip
            elif node_type == NodeType.Server:
                return Config.codis_server_ip
            else:
                return None
            

    def get_proxy_port_list(self):
        ip_last = self.get_ip(NodeType.Proxy).split(".")[3]

        zk = KazooClient(hosts=Config.zookeeper_host)
        zk.start()
        port_arr = []
        cluster_children = zk.get_children("/codis3")
        for cluster_child in cluster_children:
            proxy_children = zk.get_children("/codis3/" + cluster_child + "/proxy")
            for proxy_child in proxy_children:
                node_str,stat = zk.get("/codis3/" + cluster_child + "/proxy/" + proxy_child)
                data = json.loads(node_str)
                arr = data["admin_addr"].split(":")
                if ip_last in arr[0]:
                    port_arr.append(arr[1])
        zk.stop()
        ret = list()
        port_arr.sort()
        for port in port_arr:
            ret.append({"{#REDIS_PORT}": port})
        return json.dumps({'data': ret}, sort_keys=True, indent=7, separators=(",",":"))

    def get_server_port_list(self):
        ip_last = self.get_ip(NodeType.Server).split(".")[3]

        zk = KazooClient(hosts=Config.zookeeper_host)
        zk.start()
        port_arr = []
        children = zk.get_children("/codis3")
        for child in children:
            node_str,stat = zk.get("/codis3/" + child + "/group/group-0001")
            data = json.loads(node_str)
            for server in data["servers"]:
                arr = server["server"].split(":")
                if ip_last in arr[0]:
                    port_arr.append(arr[1])
        zk.stop()
        ret = list()
        port_arr.sort()
        for port in port_arr:
            ret.append({"{#REDIS_PORT}": port})
        return json.dumps({'data': ret}, sort_keys=True, indent=7, separators=(",",":"))

    def get_dashboard_port_list(self):
        ip_last = self.get_ip(NodeType.Dashboard).split(".")[3]

        zk = KazooClient(hosts=Config.zookeeper_host)
        zk.start()
        port_arr = []
        children = zk.get_children("/codis3")
        for child in children:
            node_str, stat = zk.get("/codis3/" + child + "/topom")
            data = json.loads(node_str)
            arr = data["admin_addr"].split(":")
            if ip_last in arr[0]:
                port_arr.append(arr[1])
        zk.stop()
        ret = list()
        port_arr.sort()
        for port in port_arr:
            ret.append({"{#REDIS_PORT}":port})
        return json.dumps({'data': ret}, sort_keys=True, indent=7, separators=(",",":"))
            
    def get_item_proxy(self):
        ret = False
        url = "http://127.0.0.1:{0}/proxy/stats".format(self.port)
        r = requests.get(url, verify=False)
        if r.status_code == 200 :
            data = r.json()
            if data["online"] :
                ret = True
                resobj = {}
                resobj["qps"] = data["ops"]["qps"]
                resobj["session_total"] = data["sessions"]["total"]
                resobj["session_alive"] = data["sessions"]["alive"]
                resobj["cmd_total"] = data["ops"]["total"]
                resobj["cmd_fails"] = data["ops"]["fails"]
                resobj["rsp_errs"] = data["ops"]["redis"]["errors"]
                self.send2zabbix("custom.codisproxy.item", resobj)
        return ret

    def get_item_server(self):
        rds_cli_path = "/usr/local/codis/bin/redis-cli"
        cmdstr = "%s -h 127.0.0.1 -p %s info" % (rds_cli_path, self.port)
        c2 = cmds(cmdstr, timeout=3)
        stdo = c2.stdo()
        stde = c2.stde()
        retcode = c2.code()        
        (stdo_list, stde_list) = (re.split("\n", stdo), re.split("\n", stde))
        resobj = {}
        for line in stdo_list:
            for key in Config.server_key_map:
                if key + ":" in str(line):
                    resobj[key] = line.split(":")[1].strip()
        if len(resobj) > 0:
            self.send2zabbix("custom.codisserver.item", resobj)
            return True
        return False        

    def get_item_dashboard(self):
        ret = False
        url = "http://127.0.0.1:{0}/topom".format(self.port)
        r = requests.get(url, verify=False)
        if r.status_code == 200:
            ret = True
            data = r.json()
            resobj = {}
            resobj["pid"] = data["model"]["pid"]
            resobj["product_name"] = data["config"]["product_name"]
            resobj["pwd"] = data["model"]["pwd"]
            resobj["start_time"] = data["model"]["start_time"]
            self.send2zabbix("custom.codisdashboard.item", resobj)
        return ret

    def send2zabbix(self,key_type,data):
        zabbix = Zabbix(Config.zabbix_sender, Config.zabbix_conf, self.port)
        zabbix.send2zabbix(key_type, data)

def main():
    try:
        usage = "usage: %prog [options]\ngGet Codis Proxy Stat"
        parser = OptionParser(usage)
        
        parser.add_option("-P", "--listproxy",  
                          action="store_true", dest="is_list_proxy", default=False,  help="if list all codis proxy stat port")

        parser.add_option("-R", "--listserver",  
                          action="store_true", dest="is_list_server", default=False,  help="if list all codis server stat port")
        
        parser.add_option("-D", "--listdashboard",  
                          action="store_true", dest="is_list_dashboard", default=False,  help="if list all codis dashboard stat port")

        parser.add_option("-k", "--key", 
                          action="store", dest="key", type="string", 
                          default='', help="call codis proxy stat API to see more infomation")
        
        parser.add_option("-p", "--port", 
                          action="store", dest="port", type="int", 
                          default=11100, help="the port for codis-proxy stat, for example: 11100")
        
        (options, args) = parser.parse_args()
        if 1 >= len(sys.argv):
            parser.print_help()
            return

        codis_ins = Codis(port=options.port)
        if options.is_list_proxy == True:
            print codis_ins.get_proxy_port_list()
            return
        elif options.is_list_server == True:
            print codis_ins.get_server_port_list()
            return
        elif options.is_list_dashboard == True:
            print codis_ins.get_dashboard_port_list()
            return
        elif options.key == "get_item_proxy":
            print codis_ins.get_item_proxy()
            return
        elif options.key == "get_item_server":
            print codis_ins.get_item_server()
            return
        elif options.key == "get_item_dashboard":
            print codis_ins.get_item_dashboard()

    except Exception as expt:
        import traceback
        tb = traceback.format_exc()
        print tb

if __name__ == '__main__':
    main()
