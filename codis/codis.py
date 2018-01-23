#!/usr/bin/python
#encoding=UTF8

import sys
import os
import re
import json
import requests
import subprocess

from common.cmds import cmds
from optparse import OptionParser
from kazoo.client import KazooClient
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class Codis(object):        
    def __init__(self, port=6379):
        self._port = port if port else 6379
        self.server_key_map = [
        "lru_clock",
        "total_commands_processed",
        "used_memory",
        "mem_fragmentation_ratio",
        "used_memory_peak",
        "blocked_clients",
        "connected_clients",
        "rejected_connections",
        "total_connections_received",
        "keyspace_misses",
        "used_memory_rss"
        ]
        self.zabbix_sender = "/usr/bin/zabbix_sender"
        self.zabbix_conf = "/etc/zabbix/zabbix_agentd.conf"

    def get_ip(self):
        cmdstr = "ifconfig -a|grep inet|grep -v 127.0.0.1|grep -v inet6|awk '{print $2}'|tr -d \"addr:\""
        c2 = cmds(cmdstr, timeout=3)
        stdo = c2.stdo()
        stde = c2.stde()
        retcode = c2.code()
        
        (stdo_list, stde_list) = (re.split("\n", stdo), re.split("\n", stde))
        return stdo_list[1]

    def get_proxy_port_list(self):
        ip_last = self.get_ip().split(".")[3]

        zk = KazooClient(hosts='127.0.0.1:2181')
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
        ip_last = self.get_ip().split(".")[3]

        zk = KazooClient(hosts='127.0.0.1:2181')
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
            
    def get_item_proxy(self, port=None):
        ret = False
        url = "http://{0}:{1}/proxy/stats".format(self.get_ip(), port)
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

    def get_item_server(self, port = None):
        port = port if port else self._port
        rds_cli_path = "/usr/local/codis/bin/redis-cli"
        cmdstr = "%s -h 127.0.0.1 -p %s info" % (rds_cli_path, port)
        c2 = cmds(cmdstr, timeout=3)
        stdo = c2.stdo()
        stde = c2.stde()
        retcode = c2.code()        
        (stdo_list, stde_list) = (re.split("\n", stdo), re.split("\n", stde))
        resobj = {}
        for line in stdo_list:
            for key in self.server_key_map:
                if key + ":" in str(line):
                    resobj[key] = line.split(":")[1].strip()
        if len(resobj) > 0:
            self.send2zabbix("custom.codisserver.item", resobj)
            return True
        return False        

    def send2zabbix(self,key_type,data):
        FNULL = open(os.devnull, 'w')
        for key in data.keys():
            subprocess.call([self.zabbix_sender, "-c", self.zabbix_conf, "-k", "{0}[{1},{2}]".format(key_type, self._port, key), "-o", str(data[key])], stdout = FNULL, stderr = FNULL, shell = False)
        FNULL.close()

def main():
    try:
        usage = "usage: %prog [options]\ngGet Codis Proxy Stat"
        parser = OptionParser(usage)
        
        parser.add_option("-P", "--listproxy",  
                          action="store_true", dest="is_list_proxy", default=False,  help="if list all codis proxy stat port")

        parser.add_option("-R", "--listserver",  
                          action="store_true", dest="is_list_server", default=False,  help="if list all codis server stat port")
        
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
        elif options.key == "get_item_proxy":
            print codis_ins.get_item_proxy(port=options.port)
            return
        elif options.key == "get_item_server":
            print codis_ins.get_item_server(port=options.port)

    except Exception as expt:
        import traceback
        tb = traceback.format_exc()
        print tb

if __name__ == '__main__':
    main()
