#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: zouhw <zhw@bt.cn>
#-------------------------------------------------------------------

#------------------------------
# Docker模型
#------------------------------

import db

def sql(table):
    with db.Sql() as sql:
        sql.dbfile("docker")
        return sql.table(table)

# 实例化docker
def docker_client(url):
    import docker
    """
    目前仅支持本地服务器
    :param url: unix:///var/run/docker.sock
    :return:
    """
    try:
        client = docker.DockerClient(base_url=url)
        return client
    except docker.errors.DockerException:
        return False