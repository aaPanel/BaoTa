#coding: utf-8

#------------------------------
# ip多点切换
#------------------------------
import os,sys
os.chdir('/www/server/panel')
# sys.path.insert(1,'BTPanel/')
sys.path.insert(0,'class/')
import public

try:
    from mailModel import multipleipModel
    print("======================开始执行========================")
    multipleipModel.main().ip_rotate()
    print("======================执行结束========================")
except:
    print(public.get_error_info())