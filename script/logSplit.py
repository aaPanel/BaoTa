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
import public,json


data = {}
path = '{}/data/cutting_log.json'.format(public.get_panel_path())
if os.path.exists(path):
    try:
        data = json.loads(public.readFile(path))
    except:pass

print ('==================================================================')
print( '★['+time.strftime("%Y/%m/%d %H:%M:%S")+']，切割日志')
print ('==================================================================')


#获取文件扩展名
def get_file_ext(filename):
    """
    @name 获取文件扩展名
    @param filename
    """
    ss_exts = ['.tar.gz','.tar.bz2','.tar.bz']
    for s in ss_exts:
        e_len = len(s)
        f_len = len(filename)
        if f_len < e_len: continue
        if filename[-e_len:] == s:
            return filename[:-e_len] ,s
    if filename.find('.') == -1: return ''
    return os.path.splitext(filename)


def split_log():
    """
    @name 拆分日志
    """
    for key in data:
        print('|-正在处理文件: {}'.format(key))
        if not os.path.exists(key):
            print('|---文件不存在，跳过!')
            continue

        num = 1024  #切割限制，如按大小切割
        limit = 180  #默认保留多少份
        stype = 'day'

        info = data[key]
        s_msg = '|---切割方式: 每天切割1份'
        try:
            limit = int(info['limit'])
            stype = info['type']
            if stype in ['size']:
                num = info[stype]
                s_msg = '|---切割方式: 按文件大小切割，每个文件大小为{}'.format(public.to_size(num))
        except:
            print ('|---配置文件错误,跳过!')
            continue

        print(s_msg)
        print ('|---当前保留最新的[{}]份'.format(limit))

        fname,fpath = os.path.basename(key),os.path.dirname(key)
        log_path = os.path.join(fpath,'history_backups')
        if not os.path.exists(log_path): os.makedirs(log_path,384)

        sfile = '{}/{}'.format(log_path,fname)
        spath,ext = get_file_ext(sfile)

        #判断切割方式，按天切割或者按大小切割
        dfile = '{}_{}{}'.format(spath,time.strftime("%Y-%m-%d"),ext)
        if stype == 'size':
            dfile = '{}_{}{}'.format(spath,time.strftime("%Y-%m-%d_%H%M%S"),ext)

            #判断是否需要切割
            if os.path.getsize(key) < num:
                print ('|---文件大小未超过[{}]，跳过!'.format(num))
                continue

        if os.path.exists(dfile):
            print('|---文件已存在，跳过!')
            continue

        logs = sorted(glob.glob(spath + "_*"))
        old_logs = sorted(glob.glob(spath+ "_*" + ext))

        count = len(logs)
        remove_num=count - info['limit']
        old_list = old_logs[:remove_num]
        for i in old_list:
            try:
                if os.path.exists(i):
                    os.remove(i)
                    print('|---多余日志['+i+']已删除!')
            except:pass

        shutil.copyfile(key,dfile)
        try:
            os.remove(key)
        except:pass
        print('|---已切割日志到:'+dfile)
        if 'callback' in info and info['callback']:
            public.ExecShell(info['callback'])
            print('|---执行回调函数')

if __name__ == '__main__':

    split_log()