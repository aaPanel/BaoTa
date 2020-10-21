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
is_gzip = not os.path.exists('/www/server/panel/data/log_not_gzip.pl')

def split_log(siteName,num):
    global logsPath,is_gzip

    print('|-正在处理网站: {}'.format(siteName))
    log_path = os.path.join(logsPath,'history_backups',siteName)
    if not os.path.exists(log_path): os.makedirs(log_path,384)

    logs=sorted(glob.glob(log_path + '/' + siteName+"_access_*"))
    old_logs = sorted(glob.glob(logsPath + '/' + siteName + "*log_*.log"))
    count=len(logs)
    remove_num=count - num
    # print('|-当前日志数量: {}, 删除：{}'.format(count,remove_num))
    old_list = old_logs[:remove_num]
    for i in old_list:
        if os.path.exists(i):
            os.remove(old_logs[i])
            print('|---多余日志['+i+']已删除!')
        
    remove_num = remove_num - len(old_list)
    for i in logs[:remove_num]:
        if os.path.exists(i):
            os.remove(i)
            print('|---多余日志['+i+']已删除!')
        err_file = i.replace('access','error')
        if os.path.exists(err_file):
            os.remove(err_file)
            print('|---多余日志['+err_file+']已删除!')
        
    

    his_date = time.strftime("%Y-%m-%d_%H%M%S")
    ngx_access_log = os.path.join(logsPath,siteName + '.log')
    ngx_error_log =  os.path.join(logsPath,siteName + '.error.log')
    if os.path.exists(ngx_access_log):
        history_log_file = log_path + '/' + siteName +'_access_'+his_date+'.log'
        shutil.move(ngx_access_log,history_log_file)
        if is_gzip:
            os.system('gzip {}'.format(history_log_file))
            print('|---已切割日志到:'+history_log_file+'.gz')
        else:
            print('|---已切割日志到:'+history_log_file+'.gz')
    if os.path.exists(ngx_error_log):
        history_log_file = log_path + '/' + siteName +'_error_'+his_date+'.log'
        shutil.move(ngx_error_log,history_log_file)
        if is_gzip:
            os.system('gzip {}'.format(history_log_file))
            print('|---已切割日志到:'+history_log_file+'.gz')
        else:
            print('|---已切割日志到:'+history_log_file+'.gz')

    httpd_access_log = os.path.join(logsPath,siteName + '-access_log')
    httpd_error_log = os.path.join(logsPath,siteName + '-error_log')
    if os.path.exists(httpd_access_log):
        history_log_file = log_path + '/' + siteName +'_access_'+his_date+'.log'
        if not os.path.exists(history_log_file):
            shutil.move(httpd_access_log,history_log_file)
            if is_gzip:
                os.system('gzip {}'.format(history_log_file))
                print('|---已切割日志到:'+history_log_file+'.gz')
            else:
                print('|---已切割日志到:'+history_log_file+'.gz')
    if os.path.exists(httpd_error_log):
        history_log_file = log_path + '/' + siteName +'_error_'+his_date+'.log'
        if not os.path.exists(history_log_file):
            shutil.move(httpd_error_log,history_log_file)
            if is_gzip:
                os.system('gzip {}'.format(history_log_file))
                print('|---已切割日志到:'+history_log_file+'.gz')
            else:
                print('|---已切割日志到:'+history_log_file+'.gz')


def split_all(save):
    sites = public.M('sites').field('name').select()
    for site in sites:
        split_log(site['name'],save)

if __name__ == '__main__':
    num = int(sys.argv[2])
    if sys.argv[1].find('ALL') == 0:
        split_all(num)
    else:
        siteName = sys.argv[1]
        split_log(sys.argv[1],num)

    public.serviceReload()