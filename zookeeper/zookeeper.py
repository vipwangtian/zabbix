#!/usr/bin/python
 
import sys
import socket
import re
import subprocess
import os

from kazoo.client import KazooClient
from common.zabbix import Zabbix
from StringIO import StringIO
 
class ZooKeeper(object):
 
    def __init__(self):
        self._result  = {}
 
    def _send_cmd(self, cmd):
        """ Send a 4letter word command to the server """
        zk = KazooClient(hosts = '127.0.0.1:2181')
        zk.start()
        ret = zk.command(cmd).decode('string_escape') 
        zk.stop()
        return ret
 
    def get_stats(self):
        pid = self._get_pid()
        if pid:
            """ Get ZooKeeper server stats as a map """
            data_mntr = self._send_cmd('mntr')
            data_ruok = self._send_cmd('ruok')
            if data_mntr:
                result_mntr = self._parse(data_mntr)
            if data_ruok:
                result_ruok = self._parse_ruok(data_ruok)
     
            self._result = dict(result_mntr.items() + result_ruok.items())
            
            if not self._result.has_key('zk_followers') and not self._result.has_key('zk_synced_followers') and not self._result.has_key('zk_pending_syncs'):
                ##### the tree metrics only exposed on leader role zookeeper server, we just set the followers' to 0
                leader_only = {'zk_followers':0,'zk_synced_followers':0,'zk_pending_syncs':0}    
                self._result = dict(result_mntr.items() + result_ruok.items() + leader_only.items() )
            self._send2zabbix()
        return pid
 
    def _parse(self, data):
        """ Parse the output from the 'mntr' 4letter word command """
        h = StringIO(data)
        result = {}
        for line in h.readlines():
            try:
                key, value = map(str.strip, line.split('\t'))
                result[key] = int(value)
            except ValueError:
                pass
        return result
 
    def _parse_ruok(self, data):
        """ Parse the output from the 'ruok' 4letter word command """
        h = StringIO(data)
        result = {}
        ruok = h.readline()
        if ruok:
           result['zk_server_ruok'] = ruok
        return result
 
    def _get_pid(self):
        #  ps -ef|grep java|grep zookeeper|awk '{print $2}'
        pidarg = '''ps -ef|grep java|grep zookeeper|grep -v grep|awk '{print $2}' ''' 
        pidout = subprocess.Popen(pidarg, shell = True, stdout = subprocess.PIPE)
        pid = pidout.stdout.readline().strip('\n')
        if pid:
            return pid
        else:
            return 0
  
    def _send2zabbix(self):
        send_data = {}
        data = self._result
        for key in data.keys():
            send_key = "zookeeper.status[{0}]".format(key)
            send_data[send_key] = data[key]
        zabbix = Zabbix()
        zabbix.send2zabbix(send_data)
 
def main():
    zk = ZooKeeper()
    print(zk.get_stats()) 

if __name__ == '__main__':
    main()
