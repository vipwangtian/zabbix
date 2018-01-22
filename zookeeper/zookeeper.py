#!/usr/bin/python
 
import sys
import socket
import re
import subprocess
import os

from StringIO import StringIO
 
class ZooKeeper(object):
 
    def __init__(self, host='localhost', port='2181', timeout=1):
        self.zabbix_sender = '/usr/bin/zabbix_sender'
        self.zabbix_conf = '/etc/zabbix/zabbix_agentd.conf'
        self._address = (host, int(port))
        self._timeout = timeout
        self._result  = {}
 
    def _send_cmd(self, cmd):
        """ Send a 4letter word command to the server """
        s = socket.socket()
        s.settimeout(self._timeout)
 
        s.connect(self._address)
        s.send(cmd)
 
        data = s.recv(2048)
        s.close()
 
        return data
 
    def get_stats(self):
        pid = self._get_pid()
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
                key, value = self._parse_line(line)
                result[key] = value
            except ValueError:
                pass # ignore broken lines
 
        return result
 
    def _parse_ruok(self, data):
        """ Parse the output from the 'ruok' 4letter word command """
        
        h = StringIO(data)
        
        result = {}
        
        ruok = h.readline()
        if ruok:
           result['zk_server_ruok'] = ruok
  
        return result
   
    def _parse_line(self, line):
        try:
            key, value = map(str.strip, line.split('\t'))
        except ValueError:
            raise ValueError('Found invalid line: %s' % line)
 
        if not key:
            raise ValueError('The key is mandatory and should not be empty')
        try:
            value = int(value)
        except (TypeError, ValueError):
            pass
        return key, value
 
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
        FNULL = open(os.devnull, 'w')
        for key in self._result:
            try:
                subprocess.call([self.zabbix_sender, "-c", self.zabbix_conf, "-k", "zookeeper.status[{0}]".format(key), "-o", str(self._result[key]) ], stdout=FNULL, stderr=FNULL, shell=False)
            except OSError, detail:
                print "Something went wrong while exectuting zabbix_sender : ", detail
        FNULL.close() 
 
def main():
    zk = ZooKeeper()
    print(zk.get_stats()) 

if __name__ == '__main__':
    main()
