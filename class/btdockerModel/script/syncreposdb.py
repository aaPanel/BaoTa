#!/www/server/panel/pyenv/bin/python3.7
# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------
# docker模型sock 封装库 镜像库
# -------------------------------------------------------------------
import os
import sys
import time

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
import public
import btdockerModel.dk_public as dp

db_file = '{}/class/btdockerModel/config/docker_hub_repos.db'.format(public.get_panel_path())
last_update_pl = "{}/class/btdockerModel/config/docker_hub_last_update.pl".format(public.get_panel_path())


# 2024/3/20 上午 9:47 获取docker hub最新的镜像排行数据
def get_docker_hub_repos():
    '''
        @name 获取docker hub最新的镜像排行数据
        @author wzz <2024/3/20 上午 9:47>
        @param "data":{"参数名":""} <数据类型> 参数描述
        @return dict{"status":True/False,"msg":"提示信息"}
    '''
    try:
        url = "{}/src/docker/docker_hub_repos.db".format(public.get_url())
        dp.download_file(url, db_file)
        if not os.path.exists(db_file):
            return public.returnMsg(False, "info.json下载失败")

        # 写一个最后更新的标记文件，里面有时间戳
        public.writeFile(last_update_pl, str(int(time.time())))

        return
    except Exception as e:
        if os.path.exists('data/debug.pl'):
            print(public.get_error_info())
            public.print_log(public.get_error_info())


# 2024/3/20 上午 9:34 如果当前时间减去这个时间戳大于30天，就执行 get_docker_hub_repos
def check_last_update():
    '''
        @name 如果当前时间减去这个时间戳大于30天，就执行 get_docker_hub_repos
        @author wzz <2024/3/20 上午 9:46>
        @param "data":{"参数名":""} <数据类型> 参数描述
        @return dict{"status":True/False,"msg":"提示信息"}
    '''
    try:
        if os.path.exists(last_update_pl):
            last_update_time = int(public.readFile(last_update_pl))
            if int(time.time()) - last_update_time > 2592000:
                public.ExecShell("rm -f {}".format(db_file))
                public.ExecShell("rm -f {}".format(last_update_pl))
                get_docker_hub_repos()

            if os.path.exists(db_file) and (os.path.getsize(db_file) == 0 or os.path.getsize(db_file) < 80):
                public.ExecShell("rm -f {}".format(db_file))
                public.ExecShell("rm -f {}".format(last_update_pl))
                get_docker_hub_repos()

            if not os.path.exists(db_file):
                public.ExecShell("rm -f {}".format(last_update_pl))
                get_docker_hub_repos()
        else:
            if not os.path.exists(db_file):
                get_docker_hub_repos()

            if os.path.exists(db_file) and (os.path.getsize(db_file) == 0 or os.path.getsize(db_file) < 80):
                public.ExecShell("rm -f {}".format(db_file))
                public.ExecShell("rm -f {}".format(last_update_pl))
                get_docker_hub_repos()
    except Exception as e:
        public.ExecShell("rm -f {}".format(db_file))
        public.ExecShell("rm -f {}".format(last_update_pl))
        if os.path.exists('data/debug.pl'):
            print(public.get_error_info())
            public.print_log(public.get_error_info())


check_last_update()
