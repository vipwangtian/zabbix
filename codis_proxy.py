#!/usr/bin/python
#encoding=UTF8

import sys
import os
import re
import json
import requests
import subprocess

from optparse import OptionParser
from kazoo.client import KazooClient
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class Codis(object):        
    def __init__(self, port=6379):
        self._port = port if port else 6379

    def get_redis_port_list(self):
        cmdstr = "ifconfig -a|grep inet|grep -v 127.0.0.1|grep -v inet6|awk '{print $2}'|tr -d \"addr:\""
        c2 = cmds(cmdstr, timeout=3)
        stdo = c2.stdo()
        stde = c2.stde()
        retcode = c2.code()
        
        (stdo_list, stde_list) = (re.split("\n", stdo), re.split("\n", stde))
        ip_last = stdo_list[1].split(".")[3]

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
            
    def get_item(self,  key, port=None, force=False):
        ret = False
        if key == "all":
            url = "http://192.168.111.156:{}/proxy/stats".format(port)
            zabbix_sender = "/usr/bin/zabbix_sender"
            zabbix_conf = "/etc/zabbix/zabbix_agentd.conf"
            r = requests.get(url, verify=False)
            if r.status_code == 200 :
                data = r.json()
                if data["online"] :
                    ret = True
                    FNULL = open(os.devnull, 'w')
                    subprocess.call([zabbix_sender, "-c", zabbix_conf, "-k", "custom.codisproxy.item[{},qps]".format(port), "-o", str(data["ops"]["qps"])], stdout = FNULL, stderr = FNULL, shell = False)
                    subprocess.call([zabbix_sender, "-c", zabbix_conf, "-k", "custom.codisproxy.item[{},session_total]".format(port), "-o", str(data["sessions"]["total"])], stdout = FNULL, stderr = FNULL, shell = False)
                    subprocess.call([zabbix_sender, "-c", zabbix_conf, "-k", "custom.codisproxy.item[{},session_alive]".format(port), "-o", str(data["sessions"]["alive"])], stdout = FNULL, stderr = FNULL, shell = False)
                    subprocess.call([zabbix_sender, "-c", zabbix_conf, "-k", "custom.codisproxy.item[{},cmd_total]".format(port), "-o", str(data["ops"]["total"])], stdout = FNULL, stderr = FNULL, shell = False)
                    subprocess.call([zabbix_sender, "-c", zabbix_conf, "-k", "custom.codisproxy.item[{},cmd_fails]".format(port), "-o", str(data["ops"]["fails"])], stdout = FNULL, stderr = FNULL, shell = False)
                    subprocess.call([zabbix_sender, "-c", zabbix_conf, "-k", "custom.codisproxy.item[{},rsp_errs]".format(port), "-o", str(data["ops"]["redis"]["errors"])], stdout = FNULL, stderr = FNULL, shell = False)
                    FNULL.close()
        return ret

def main():
    try:
        usage = "usage: %prog [options]\ngGet Codis Proxy Stat"
        parser = OptionParser(usage)
        
        parser.add_option("-l", "--list",  
                          action="store_true", dest="is_list", default=False,  help="if list all codis proxy stat port")
        
        parser.add_option("-k", "--key", 
                          action="store", dest="key", type="string", 
                          default='blocked_clients', help="call codis proxy stat API to see more infomation")
        
        parser.add_option("-p", "--port", 
                          action="store", dest="port", type="int", 
                          default=11100, help="the port for codis-proxy stat, for example: 11100")
        
        parser.add_option("-d", "--debug",  
                          action="store_true", dest="debug", default=False,  
                          help="if output all")
        parser.add_option("-f", "--force",  
                          action="store_true", dest="force", default=False,  
                          help="if force to parse command oupout")
        
        (options, args) = parser.parse_args()
        if 1 >= len(sys.argv):
            parser.print_help()
            return
        
        codis_ins = Codis(port=options.port)
        if options.is_list == True:
            print codis_ins.get_redis_port_list()
            return

        print codis_ins.get_item(options.key, port=options.port, force=options.force)

    except Exception as expt:
        import traceback
        tb = traceback.format_exc()
        print tb

if __name__ == '__main__':
    main()
