## zabbix监控[nginx](http://nginx.org/)
### 使用方法
配置nginx<br/>
```txt
server {
  listen 80;
  server_name localhost;
        
  location /stub_status {
    stub_status on;
    access_log off;
    allow 127.0.0.1;
    deny all;
  }
} 
```
将nginx.py复制到/etc/zabbix/scripts/下，将userparameter_nginx.conf复制到/etc/zabbix/zabbix_agent.d/下<br/>
脚本用到了requests库，要先安装
```shell
pip install requests
```
发送监控键值使用了zabbix_sender，使用rpm命令安装，软件对应版本地址http://repo.zabbix.com/zabbix/3.4/rhel/6/x86_64/
```shell
rpm -ivh http://repo.zabbix.com/zabbix/3.4/rhel/6/x86_64/zabbix-sender-3.4.3-1.el6.x86_64.rpm
```
重启zabbix-agent
```shell
service zabbix-agent restart
```
在web端导入监控模板。
