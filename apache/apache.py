#!/usr/bin/env python
#-*- coding:utf-8 -*-

import sys
import os
import requests
from common.zabbix import Zabbix
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class Apache(object):
    def __init__(self):
        self.apache_url = "http://127.0.0.1/server-status?auto"
        self.keys_map = [
            "ServerVersion",
            "CurrentTime",
            "RestartTime",
            "ServerUptime",
            "Total Accesses",
            "Total kBytes",
            "BusyWorkers",
            "IdleWorkers",
            "ConnsTotal",
            "ConnsAsyncWriting",
            "ConnsAsyncKeepAlive",
            "ConnsAsyncClosing",
            "ReqPerSec",
            "BytesPerSec",
            "BytesPerReq"
        ]

    def send2zabbix(self, data):
        key_pre = "custom.apache.item"
        send_data = {}

        for key in self.keys_map:
            send_key = "{0}[{1}]".format(key_pre, key)
            send_data[send_key] = data[key]
        zabbix = Zabbix()
        zabbix.send2zabbix(send_data)

    def get_status(self):
        r = requests.get(self.apache_url, verify=False)
        ret = False
        data = {}
        if r.status_code == 200:
            for line in r.text.splitlines():
                if ":" in line:
                    arr = line.split(":")
                    for item in arr:
                        item = item.strip()
                    data[arr[0]] = arr[1]
            if data:
                self.send2zabbix(data)
                ret = True
        return ret

def main():
    try:
        apache = Apache()
        print(apache.get_status())
    except:
        import traceback
        tb = traceback.format_exc()
        print tb

if __name__ == "__main__":
    main()