## zabbix监控[nginx](http://nginx.org/)
### 使用方法
* 配置nginx
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
* 将nginx.py复制到/etc/zabbix/scripts/下，将userparameter_nginx.conf复制到/etc/zabbix/zabbix_agent.d/下<br/>
* 安装[requests](https://github.com/vipwangtian/zabbix/blob/master/README.md)和[zabbix_sender](https://github.com/vipwangtian/zabbix/blob/master/README.md)  
* 重启zabbix-agent
```shell
service zabbix-agent restart
```
* 在web端导入监控模板。
