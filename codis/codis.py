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
        key_pre = "custom.codisproxy.item"
        r = requests.get(url, verify=False)
        if r.status_code == 200 :
            data = r.json()
            if data["online"] :
                ret = True
                resobj = {}
                resobj[self.make_zabbix_key(key_pre, "qps")] = data["ops"]["qps"]
                resobj[self.make_zabbix_key(key_pre, "session_total")] = data["sessions"]["total"]
                resobj[self.make_zabbix_key(key_pre, "session_alive")] = data["sessions"]["alive"]
                resobj[self.make_zabbix_key(key_pre, "cmd_total")] = data["ops"]["total"]
                resobj[self.make_zabbix_key(key_pre, "cmd_fails")] = data["ops"]["fails"]
                resobj[self.make_zabbix_key(key_pre, "rsp_errs")] = data["ops"]["redis"]["errors"]
                self.send2zabbix(resobj)
        return ret

    def get_item_server(self):
        key_pre = "custom.codisserver.item"
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
                    resobj[self.make_zabbix_key(key_pre, key)] = line.split(":")[1].strip()
        if len(resobj) > 0:
            self.send2zabbix(resobj)
            return True
        return False        

    def get_item_dashboard(self):
        ret = False
        url = "http://127.0.0.1:{0}/topom".format(self.port)
        key_pre = "custom.codisdashboard.item"
        r = requests.get(url, verify=False)
        if r.status_code == 200:
            data = r.json()
            overview = "{0}\n".format(data["config"]["product_name"])
            overview += "coordinator_name:{0}\n".format(data["config"]["coordinator_name"])
            overview += "coordinator_addr:{0}\n".format(data["config"]["coordinator_addr"])
            overview += "admin_addr:{0}\n".format(data["config"]["admin_addr"])
            for proxy in data["stats"]["proxy"]["models"]:
                overview += "proxy:{0} admin_addr:{1}\n".format(proxy["proxy_addr"], proxy["admin_addr"])
            for server in data["stats"]["group"]["models"][0]["servers"]:
                overview += "server:{0} role:{1}\n".format(server["server"], data["stats"]["group"]["stats"][server["server"]]["stats"]["role"])

            resobj = {}
            resobj[self.make_zabbix_key(key_pre, "pid")] = data["model"]["pid"]
            resobj[self.make_zabbix_key(key_pre, "overview")] = "\"{0}\"".format(overview)
            resobj[self.make_zabbix_key(key_pre, "product_name")] = data["config"]["product_name"]
            resobj[self.make_zabbix_key(key_pre, "pwd")] = data["model"]["pwd"]
            resobj[self.make_zabbix_key(key_pre, "start_time")] = data["model"]["start_time"]
            self.send2zabbix(resobj)
            ret = True
        return ret

    def make_zabbix_key(self, key_pre, key):
        return "{0}[{1},{2}]".format(key_pre, self.port, key)

    def send2zabbix(self,data):
        zabbix = Zabbix()
        zabbix.send2zabbix(data)

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
