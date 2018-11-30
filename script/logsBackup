#!/usr/bin/python
#coding: utf-8
#-----------------------------
#宝塔Linux面板网站日志切割脚本
#-----------------------------
import sys
import os
import shutil
import time
import glob
os.chdir("/www/server/panel")
sys.path.append('class/')
import public
print ('==================================================================')
print( '★['+time.strftime("%Y/%m/%d %H:%M:%S")+']，切割日志')
print ('==================================================================')
print ('|--当前保留最新的['+sys.argv[2]+']份')
logsPath = '/www/wwwlogs/'
is_nginx = False
if os.path.exists('/www/server/nginx/logs/nginx.pid'): is_nginx = True
px = '.log'
if not is_nginx: px = '-access_log'

def split_logs(oldFileName,num):
    global logsPath
    if not os.path.exists(oldFileName):
        print('|---'+oldFileName+'文件不存在!')
        return

    logs=sorted(glob.glob(oldFileName+"_*"))
    count=len(logs)
    num=count - num

    for i in range(count):
        if i>num: break;
        os.remove(logs[i])
        print('|---多余日志['+logs[i]+']已删除!')

    newFileName=oldFileName+'_'+time.strftime("%Y-%m-%d_%H%M%S")+'.log'
    shutil.move(oldFileName,newFileName)
    print('|---已切割日志到:'+newFileName)

def split_all(save):
    sites = public.M('sites').field('name').select()
    for site in sites:
        oldFileName = logsPath + site['name'] + px
        split_logs(oldFileName,save)

if __name__ == '__main__':
    num = int(sys.argv[2])
    if sys.argv[1].find('ALL') == 0:
        split_all(num)
    else:
        siteName = sys.argv[1]
        if siteName[-4:] == '.log': 
            siteName = siteName[:-4]
        else:
            siteName = siteName.replace("-access_log")
        oldFileName = logsPath+sys.argv[1]
        split_logs(oldFileName,num)

    if is_nginx:
        os.system("kill -USR1 `cat /www/server/nginx/logs/nginx.pid`");
    else:
        os.system('/etc/init.d/httpd reload');