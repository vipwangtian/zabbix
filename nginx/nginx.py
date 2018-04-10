#!/usr/bin/env python
#-*- coding:utf-8 -*-

import sys
import os
import requests
import re
import subprocess
from common.zabbix import Zabbix
from common.cmds import cmds
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class Nginx(object):
	def __init__(self):
		self.nginx_url = "http://127.0.0.1/nginx_status"
		self.cmdstr = "ps ax|grep -v \"grep\" | grep -c \"nginx:\""

	def send2zabbix(self, data):
		send_data = {}
		for key in data.keys():
			send_key = "nginx.status[{0}]".format(key)
			send_data[send_key] = data[key]
		zabbix = Zabbix()
		zabbix.send2zabbix(send_data)
		print(data["process"])

	def get_status(self):
		ret = {}
		c2 = cmds(self.cmdstr, timeout = 3)
		stdo = c2.stdo()
		stde = c2.stde()
		retcode = c2.code()
        ret = { 
            "process" : stdo, 
            "active" : 0, 
            "accepts" : 0, 
            "handled" : 0, 
            "requests" : 0, 
            "reading" : 0, 
            "writing" : 0, 
            "waiting" : 0 
        }

		try:
			r = requests.get(self.nginx_url, verify=False, timeout = 1)
			if r.status_code == 200:
				lines = r.text.split("\n")
				ret["active"] = lines[0].split(":")[1].strip()
				p = re.compile(r"\d+")
				line3Arr = p.findall(lines[2])
				ret["accepts"] = line3Arr[0].strip()
				ret["handled"] = line3Arr[1].strip()
				ret["requests"] = line3Arr[2].strip()
				p = re.compile(r"\d+")
				line4Arr = p.findall(lines[3])
				ret["reading"] = line4Arr[0]
				ret["writing"] = line4Arr[1]
				ret["waiting"] = line4Arr[2]
		except:
			pass
		return ret, True
def main():
	try:
		nginx_ins = Nginx()
		data, stat = nginx_ins.get_status()
		if stat:
			nginx_ins.send2zabbix(data)
	except Exception as expt:
		import traceback
		tb = traceback.format_exc()
		print(tb)
		

if __name__ == "__main__":
	main()
