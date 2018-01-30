## zabbix监控[mysql](https://www.mysql.com/)
### 使用方法
* 将checkmysql.py复制到/etc/zabbix/scripts/下，修改脚本中连接mysql的配置。<br/>
* 将userparameter_mysql.conf复制到/etc/zabbix/zabbix_agent.d/下<br/>
* [安装mysql-connector-python](https://github.com/vipwangtian/zabbix/blob/master/doc/install_libs.md)
* 重启zabbix-agent<br/>
```shell
service zabbix-agent restart
```
* 在web端导入Template App mysql.xml模板<br/>
### 实现方式
与官方提供的MySQL Workbench提供的Dashboard实现方式相同，数据来自show global status命令
