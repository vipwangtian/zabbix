# [zabbix](https://www.zabbix.com/)监控模板
[zabbix_sender](http://repo.zabbix.com/zabbix/3.4/rhel/6/x86_64/)安装
```shell
rpm -ivh http://repo.zabbix.com/zabbix/3.4/rhel/6/x86_64/zabbix-sender-3.4.3-1.el6.x86_64.rpm
```
[kazoo](http://kazoo.readthedocs.io/en/latest/)安装
```shell
pip install kazoo
```
[requests](http://docs.python-requests.org/en/master/)安装
```shell
pip install requests
```
[mysql-connector-python](https://dev.mysql.com/downloads/connector/python/)安装
下载源码mysql-connector-python-2.1.7-1.el6.src.rpm包，解压
```shell
rpm2cpio mysql-connector-python-2.1.7-1.el6.src.rpm | cpio -div
tar -zxvf mysql-connector-python-2.1.7.tar.gz
cd mysql-connector-python-2.1.7
python setup.py install
```
