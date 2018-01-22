## zabbinx监控codis
### 使用方法 
将codis.py复制到/etc/zabbix/scripts/下，将userparameter_codis.conf复制到/etc/zabbix/zabbix_agent.d/下<br/>
因为脚本用到了kazoo和requests库，要先安装这两个python库<br/>
```shell
pip install requests
pip install kazoo
```
重启zabbix-agent<br/>
在web端导入监控模板。
```shell
service zabbix-agent restart
```
### 实现原理
模板中包含自动发现，自动发现会调用客户端codis.py --listserver发现codis-server，codis.py --listproxy发现codis-proxy。<br/>
发现方式为从zookeeper中读取集群配置。
