#!/usr/bin/env python
#-*- coding:utf-8 -*-

class Config(object):
    #是否使用命令行自动获取的第一个ip作为codis监听的ip
    #如果机器存在多块网卡，多个ip的情况，并且集群部署比较复杂的情况下，建议手动指定ip
    auto_discovery_node_ip = True
    codis_dashboard_ip = 'your dashboard ip address'
    codis_proxy_ip = 'your proxy ip address'
    codis_server_ip = 'your server ip address'
    #you needn't specify the port of every node, it will be found in zookeeper automatic.
    zookeeper_host = '127.0.0.1:2181'
    zabbix_sender = '/usr/bin/zabbix_sender'
    zabbix_conf = '/etc/zabbix/zabbix_agentd.conf'

    server_key_map = [
        "lru_clock",
        "total_commands_processed",
        "used_memory",
        "mem_fragmentation_ratio",
        "used_memory_peak",
        "blocked_clients",
        "connected_clients",
        "rejected_connections",
        "total_connections_received",
        "keyspace_misses",
        "used_memory_rss"
    ]

class NodeType(object):
    Dashboard = 1
    Proxy = 2
    Server = 3
