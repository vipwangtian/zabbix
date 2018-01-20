#!/usr/bin/python
#encoding=UTF8

import sys
import os
import requests
import re
import subprocess
from cmds import cmds
from optparse import OptionParser
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class Nginx(object):
	def __init__(self):
		self.nginx_url = "http://127.0.0.1/stub_status"
		self.zabbix_sender = "/usr/bin/zabbix_sender"
		self.zabbix_conf = "/etc/zabbix/zabbix_agentd.conf"
		self.cmdstr = "ps ax|grep -v \"grep\" | grep -c \"nginx:\""

	def send2zabbix(self, data):
		FNULL = open(os.devnull, 'w')
		subprocess.call([self.zabbix_sender, "-c", self.zabbix_conf, "-k", "nginx.status[active]", "-o", str(data["active"])], stdout = FNULL, stderr = FNULL, shell = False)
		subprocess.call([self.zabbix_sender, "-c", self.zabbix_conf, "-k", "nginx.status[accepts]", "-o", str(data["accepts"])], stdout = FNULL, stderr = FNULL, shell = False)
		subprocess.call([self.zabbix_sender, "-c", self.zabbix_conf, "-k", "nginx.status[handled]", "-o", str(data["handled"])], stdout = FNULL, stderr = FNULL, shell = False)
		subprocess.call([self.zabbix_sender, "-c", self.zabbix_conf, "-k", "nginx.status[requests]", "-o", str(data["requests"])], stdout = FNULL, stderr = FNULL, shell = False)
		subprocess.call([self.zabbix_sender, "-c", self.zabbix_conf, "-k", "nginx.status[reading]", "-o", str(data["reading"])], stdout = FNULL, stderr = FNULL, shell = False)
		subprocess.call([self.zabbix_sender, "-c", self.zabbix_conf, "-k", "nginx.status[writing]", "-o", str(data["writing"])], stdout = FNULL, stderr = FNULL, shell = False)
		subprocess.call([self.zabbix_sender, "-c", self.zabbix_conf, "-k", "nginx.status[waiting]", "-o", str(data["waiting"])], stdout = FNULL, stderr = FNULL, shell = False)
		FNULL.close()
		print(data["process"])

	def get_status(self):
		ret = {}
		c2 = cmds(self.cmdstr, timeout = 3)
		stdo = c2.stdo()
		stde = c2.stde()
		retcode = c2.code()
		ret["process"] = stdo

		r = requests.get(self.nginx_url, verify=False)
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
			return ret, True
		return NULL, False
def main():
	try:
		nginx_ins = Nginx()
		data, stat = nginx_ins.get_status()
		if stat:
			nginx_ins.send2zabbix(data)
	except Exception as expt:
		import traceback
		tb = traceback.format_exc()
		print tb
		

if __name__ == "__main__":
	main()