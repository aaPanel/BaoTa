#coding: utf-8
import sys,os
os.chdir('/www/server/panel/')
sys.path.insert(0,"class/")
import PluginLoader
cid = sys.argv[-1]
PluginLoader.get_soft_list(cid)