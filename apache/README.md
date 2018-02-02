## zabbix监控apache
### apache配置文件中增加location
```xml
<location /server-status>  
	SetHandler server-status  
	Order allow,deny
	Allow from localhost 
</location> 
```
