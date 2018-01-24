#!/usr/bin/env python
#-*- coding:utf-8 -*-

import os
import subprocess

class Zabbix(object):
    def __init__(self):
        self.zabbix_sender = '/usr/bin/zabbix_sender'
        self.zabbix_conf = '/etc/zabbix/zabbix_agentd.conf'

    def send2zabbix(self, data):
        FNULL = open(os.devnull, 'w')
        for key in data.keys():
            subprocess.call([self.zabbix_sender, "-c", self.zabbix_conf, "-k", key, "-o", str(data[key])], stdout = FNULL, stderr = FNULL, shell = False)
        FNULL.close()