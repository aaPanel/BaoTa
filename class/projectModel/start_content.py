#!/usr/bin/python
# coding: utf-8
# Date 2022/10/25

import sys,os
sys.path.append('/www/server/panel/class')
os.chdir('/www/server/panel')
import public
import PluginLoader


if __name__ == '__main__':
    import sys


    if len(sys.argv) == 1:
        print("请输入参数")
        print("python3 main.py 1")
        exit(0)
    if len(sys.argv) == 2:
        id = sys.argv[1]
        paths="/dev/shm/"+public.Md5(id)+".txt"
        args = public.dict_obj()
        args.id = id
        args.path = paths
        main = PluginLoader.module_run("content", "start", args)