
 ## Installation
 * Copy userparameter_mssql.conf to your Zabbix Agent folder, e.g. D:\zabbix\conf.d
 * Copy PowerShell scripts to the scripts folder, e.g. C:\zabbix\scripts folder. IMPORTANT: if you use another folder for agent scripts, then update userparameter file in the previous step!
 * Import XML template file(Template App MSSQL 2008-2016 New.xml) into Zabbix via Web GUI (Configuration -> Templates -> Import).
 * Configure regular expression in "Administration -> General -> Regular Expressions (dropdown on the right)":

``` text
Name: MS SQL Databases for discovery
Expression: ^(master|model|msdb|ReportServer|ReportServerTempDB|tempdb)$
Type: Result is FALSE
```

* Assign the imported template to a host.
* Restart Zabbix Agent and enjoy... or, actually, good luck in tuning MS SQL ;)