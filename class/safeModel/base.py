#coding: utf-8
import public,re,time,sys,os
from datetime import datetime


class safeBase:

    __isUfw = False
    __isFirewalld = False
    _months = {'Jan':'01','Feb':'02','Mar':'03','Apr':'04','May':'05','Jun':'06','Jul':'07','Aug':'08','Sep':'09','Sept':'09','Oct':'10','Nov':'11','Dec':'12'}

    def __init__(self):
        if os.path.exists('/usr/sbin/firewalld'): self.__isFirewalld = True
        if os.path.exists('/usr/sbin/ufw'): self.__isUfw = True

    #转换时间格式
    def to_date(self,date_str):
        tmp = re.split('\s+',date_str)
        if len(tmp) < 3: return date_str
        s_date = str(datetime.now().year) + '-' + self._months.get(tmp[0]) + '-' + tmp[1] + ' ' + tmp[2]
        time_array = time.strptime(s_date, "%Y-%m-%d %H:%M:%S")
        time_stamp = int(time.mktime(time_array))
        return time_stamp


    def to_date2(self,date_str):
        tmp = date_str.split()
        if len(tmp) < 4: return date_str
        s_date = str(tmp[-1]) + '-' + self._months.get(tmp[1],tmp[1]) + '-' + tmp[2] + ' ' + tmp[3]
        return s_date

    def to_date3(self,date_str):
        tmp = date_str.split()
        if len(tmp) < 4: return date_str
        s_date = str(datetime.now().year) + '-' + self._months.get(tmp[1],tmp[1]) + '-' + tmp[2] + ' ' + tmp[3]
        return s_date

    def to_date4(self,date_str):
        tmp = date_str.split()
        if len(tmp) < 3: return date_str
        s_date = str(datetime.now().year) + '-' + self._months.get(tmp[0],tmp[0]) + '-' + tmp[1] + ' ' + tmp[2]
        return s_date


    #取防火墙状态
    def CheckFirewallStatus(self):
        if self.__isUfw:
            res = public.ExecShell('ufw status verbose')[0]
            if res.find('inactive') != -1: return False
            return True

        if self.__isFirewalld:
            res = public.ExecShell("systemctl status firewalld")[0]
            if res.find('active (running)') != -1: return True
            if res.find('disabled') != -1: return False
            if res.find('inactive (dead)') != -1: return False
        else:
            res = public.ExecShell("/etc/init.d/iptables status")[0]
            if res.find('not running') != -1: return False
            return True
        return False


    def get_ssh_log_files(self,get):
        """
        获取ssh日志文件
        """
        s_key = 'secure'
        if not os.path.exists('/var/log/secure'):
            s_key = 'auth.log'
        if os.path.exists('/var/log/secure') and os.path.getsize('/var/log/secure') == 0:
            s_key = 'auth.log'

        res = []
        spath = '/var/log/'
        for fname in os.listdir(spath):
            fpath = '{}{}'.format(spath,fname)
            if fname.find(s_key) == -1 or fname == s_key:
                continue

            #debian解压日志
            if fname[-3:] in ['.gz','.xz']:
                if os.path.exists(fpath[:-3]):
                    continue
                public.ExecShell("gunzip -c " + fpath + " > " + fpath[:-3])
                res.append(fpath[:-3])
            else:
                res.append(fpath)

        res = sorted(res,reverse=True)
        res.insert(0,spath + s_key)
        return res
    
    def get_ssh_log_files_list(self,get):
        """
        获取ssh日志文件
        """
        s_key = 'secure'
        if not os.path.exists('/var/log/secure'):
            s_key = 'auth.log'
        if os.path.exists('/var/log/secure') and os.path.getsize('/var/log/secure') == 0:
            s_key = 'auth.log'

        res = []
        spath = '/var/log/'
        for fname in os.listdir(spath):
            fpath = '{}{}'.format(spath,fname)
            if fname.find(s_key) == -1 or fname == s_key:
                continue
            #debian解压日志
            if fname[-3:] in ['.gz','.xz']:
                continue
            if os.path.getsize(fpath) > 1024 * 1024 * 10:
                continue
            #判断文件数量为15个
            if len(res) > 15:
                break
            res.append(fpath)
        res = sorted(res,reverse=True)
        res.insert(0,spath + s_key)
        return res