#!/www/server/panel/pyenv/bin/python
#coding: utf-8
import os,sys
os.chdir("/www/server/panel")
sys.path.insert(0,"class/")
import PluginLoader
import public
args = public.dict_obj()
args.module_get_object = 1
mysql_quota_check = PluginLoader.module_run('quota','mysql_quota_check',args)
mysql_quota_check()

