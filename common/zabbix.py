#!/usr/bin/env python
#-*- coding:utf-8 -*-

import os
import subprocess

class Zabbix(object):
    def __init__(self, zabbix_sender, zabbix_conf, port):
        self.zabbix_sender = zabbix_sender
        self.zabbix_conf = zabbix_conf
        self.port = port

    def send2zabbix(self, key_type, data):
        FNULL = open(os.devnull, 'w')
        for key in data.keys():
            subprocess.call([self.zabbix_sender, "-c", self.zabbix_conf, "-k", "{0}[{1},{2}]".format(key_type, self.port, key), "-o", str(data[key])], stdout = FNULL, stderr = FNULL, shell = False)
        FNULL.close()