# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: zouhw <zhw@bt.cn>
# -------------------------------------------------------------------

# ------------------------------
# Docker模型
# ------------------------------

import db
import public
import json
import os

def check_db():
    db_path = "/www/server/panel/data/docker.db"
    if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
        execstr = "wget -O {} {}/install/src/docker.db".format(db_path, public.get_url())
        public.ExecShell(execstr)

def sql(table):
    check_db()
    with db.Sql() as sql:
        sql.dbfile("docker")
        return sql.table(table)

# 实例化docker
def docker_client(url="unix:///var/run/docker.sock"):
    import docker
    """
    目前仅支持本地服务器
    :param url: unix:///var/run/docker.sock
    :return:
    """
    try:
        client = docker.DockerClient(base_url=url)
        client.networks.list()
        return client
    except:
        return False

def docker_client_low(url="unix:///var/run/docker.sock"):
    """
    docker 低级接口
    :param url:
    :return:
    """
    import docker
    try:
        client = docker.APIClient(base_url=url)
        return client
    except docker.errors.DockerException:
        return False

#取CPU类型
def get_cpu_count():
    import re
    cpuinfo = open('/proc/cpuinfo','r').read()
    rep = "processor\s*:"
    tmp = re.findall(rep,cpuinfo)
    if not tmp:
        return 0
    return len(tmp)

def set_kv(kv_str):
    """
    将键值字符串转为对象
    :param data:
    :return:
    """
    if not kv_str:
        return None
    res = kv_str.split('\n')
    data = dict()
    for i in res:
        i = i.strip()
        if not i:
            continue
        k,v = i.split('=')
        data[k]= v
    return data

def get_mem_info():
    #取内存信息
    import psutil
    mem = psutil.virtual_memory()
    memInfo = int(mem.total)
    return memInfo

def byte_conversion(data):
    if "b" in data:
        return int(data.replace('b',''))
    elif "KB" in data:
        return int(data.replace('KB','')) * 1024
    elif "MB" in data:
        return int(data.replace('MB','')) * 1024 * 1024
    elif "GB" in data:
        return int(data.replace('GB','')) * 1024 * 1024 * 1024
    else:
        return False

def log_docker(generator, task_name):
    __log_path = '/tmp/dockertmp.log'
    while True:
        try:
            output = generator.__next__()
            try:
                output = json.loads(output)
                if 'status' in output:
                    output_str = "{}\n".format(output['status'])
                    public.writeFile(__log_path, output_str, 'a+')
            except:
                public.writeFile(__log_path, public.get_error_info(), 'a+')
            if 'stream' in output:
                output_str = output['stream']
                public.writeFile(__log_path,output_str,'a+')
        except StopIteration:
            public.writeFile(__log_path,f'{task_name} complete.','a+')
            break
        except ValueError:
            public.writeFile(log_path,f'Error parsing output from {task_name}: {output}','a+')

def docker_conf():
    """
    解析docker配置文件
    KEY=VAULE
    KEY1=VALUE1
    :return:
    """
    docker_conf = public.readFile("{}/data/docker.conf".format(public.get_panel_path()))
    if not docker_conf:
        return {"SAVE":30}
    data = dict()
    for i in docker_conf.split("\n"):
        if not i:
            continue
        k,v = i.split("=")
        if k == "SAVE":
            v = int(v)
        data[k] = v
    return data

def get_process_id(pname,cmd_line):
    import psutil
    pids = psutil.pids()
    for pid in pids:
        try:
            p = psutil.Process(pid)
            if p.name() == pname and cmd_line in p.cmdline():
                return pid
        except:
            pass
    return False

def write_log(log_data):
    public.WriteLog("Docker", log_data)

def check_socket(port):
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    location = ("127.0.0.1", int(port))
    result_of_check = s.connect_ex(location)
    s.close()
    if result_of_check == 0:
        return True
    else:
        return False

def download_file(url, filename):
    '''
    下载方法
    @param url:
    @param filename:
    @return:
    '''
    return public.ExecShell(f"wget -O {filename} {url} --no-check-certificate")

