#!/usr/bin/env python
#-*- coding:utf-8 -*-

import mysql.connector
from common.zabbix import Zabbix

class check_mysql(object):
    def __init__(self):
        self.config = {
            'user': 'dbadmin',
            'password': 'AZOffOqYxkqZNH0v',
            'host': '192.168.112.8'
        }

    def get_status(self):
        ret = False
        try:
            cnx = mysql.connector.connect(**self.config)
            cursor = cnx.cursor()
            query_data = {}
            result = cursor.execute("SHOW GLOBAL STATUS")
            for (Variable_name, Value) in cursor:
                query_data[Variable_name] = Value
            cnx.close()
            if query_data:
                data = self.make_monit_data(query_data)
                self.send2zabbix(data)
                ret = True
        except:
            ret = False
        return ret


    def make_monit_data(self, query_data):
        data = {}
        key_pre = "custom.mysql.item"
        data["{0}[Bytes_received]".format(key_pre)] = query_data["Bytes_received"]
        data["{0}[Bytes_sent]".format(key_pre)] = query_data["Bytes_sent"]
        data["{0}[client_connections]".format(key_pre)] = query_data["Threads_connected"]
        data["{0}[Com_select]".format(key_pre)] = query_data["Com_select"]
        data["{0}[Com_insert]".format(key_pre)] = query_data["Com_insert"]
        data["{0}[Com_delete]".format(key_pre)] = query_data["Com_delete"]
        data["{0}[Com_update]".format(key_pre)] = query_data["Com_update"]
        data["{0}[Table_open_cache_hits]".format(key_pre)] = query_data["Table_open_cache_hits"]
        data["{0}[Table_open_cache_misses]".format(key_pre)] = query_data["Table_open_cache_misses"]
        data["{0}[Innodb_buffer_pool_pages_total]".format(key_pre)] = query_data["Innodb_buffer_pool_pages_total"]
        data["{0}[Innodb_buffer_pool_pages_data]".format(key_pre)] = query_data["Innodb_buffer_pool_pages_data"]
        data["{0}[Innodb_buffer_pool_pages_free]".format(key_pre)] = query_data["Innodb_buffer_pool_pages_free"]
        data["{0}[Innodb_buffer_pool_read_requests]".format(key_pre)] = query_data["Innodb_buffer_pool_read_requests"]
        data["{0}[Innodb_buffer_pool_write_requests]".format(key_pre)] = query_data["Innodb_buffer_pool_write_requests"]
        data["{0}[Innodb_buffer_pool_reads]".format(key_pre)] = query_data["Innodb_buffer_pool_reads"]
        data["{0}[Innodb_pages_read]".format(key_pre)] = query_data["Innodb_pages_read"]
        data["{0}[Innodb_os_log_written]".format(key_pre)] = query_data["Innodb_os_log_written"]
        data["{0}[Innodb_log_writes]".format(key_pre)] = query_data["Innodb_log_writes"]
        data["{0}[Innodb_pages_written]".format(key_pre)] = query_data["Innodb_pages_written"]
        data["{0}[Innodb_data_written]".format(key_pre)] = query_data["Innodb_data_written"]
        data["{0}[Innodb_dblwr_writes]".format(key_pre)] = query_data["Innodb_dblwr_writes"]
        data["{0}[Innodb_data_read]".format(key_pre)] = query_data["Innodb_data_read"]

        return data

    def send2zabbix(self, data):
        zabbix = Zabbix()
        zabbix.send2zabbix(data)

def main():
    mysql_ins = check_mysql()
    print(mysql_ins.get_status())

if __name__ == '__main__':
    main()