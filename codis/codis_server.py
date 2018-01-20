#!/usr/bin/python
import sys
import os
import re
import json
import subprocess

from codis.cmds import cmds
from optparse import OptionParser
from kazoo.client import KazooClient

class Codis(object):        
    def __init__(self, port=6379, debug=False):
        self._port = port if port else 6379
        self._debug = debug
        self.key_map = [
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
            
    def send2zabbix(self, data):
        FNULL = open(os.devnull, 'w')
        for key in self.key_map:
            subprocess.call([self.zabbix_sender, "-c", self.zabbix_conf, "-k", "custom.redis.item[{0},{1}]".format(self._port, key), "-o", str(data[key])], stdout = FNULL, stderr = FNULL, shell = False)
        FNULL.close()

    def get_item(self, key, port=None, force=False):
        port = port if port else self._port
        if key == "check":
            rds_cli_path = "/usr/local/codis/bin/redis-cli"
            cmdstr = "%s -h 127.0.0.1 -p %s info" % (rds_cli_path, port)
            c2 = cmds(cmdstr, timeout=3)
            stdo = c2.stdo()
            stde = c2.stde()
            retcode = c2.code()        
            (stdo_list, stde_list) = (re.split("\n", stdo), re.split("\n", stde))
            resobj = {}
            for line in stdo_list:
                for key in self.key_map:
                    if key + ":" in str(line):
                        resobj[key] = line.split(":")[1].strip()
            if len(resobj) > 0:
                self.send2zabbix(resobj)
                return True
        return False
def main():
    try:
        usage = "usage: %prog [options]\ngGet Redis Stat"
        parser = OptionParser(usage)
        
        parser.add_option("-l", "--list",  
                          action="store_true", dest="is_list", default=False,  help="if list all redis port")
        
        parser.add_option("-k", "--key", 
                          action="store", dest="key", type="string", 
                          default='blocked_clients', help="execute 'redis-cli info' to see more infomation")
        
        parser.add_option("-p", "--port", 
                          action="store", dest="port", type="int", 
                          default=6379, help="the port for redis-server, for example: 6379")
        
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
        
        codis_ins = Codis(port=options.port, debug=options.debug)
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
