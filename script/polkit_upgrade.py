#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------

#--------------------------------
# 修复polkit提权漏洞(CVE-2021-4034)
#--------------------------------

import os,sys
os.chdir("/www/server/panel")
sys.path.insert(0,'class/')
import public
upgrade_log_file = '/www/server/panel/logs/upgrade_polkit.log'
log_msg = "检测到您的系统中存在polkit(CVE-2021-4034)提权漏洞,已为您修复!"


def write_log(msg):
    global upgrade_log_file
    public.writeFile(upgrade_log_file,"[{}] - {}".format(public.format_date(),msg),'a+')

def is_yum():
    if os.path.exists('/usr/bin/yum'):
        return True
    return False

def is_dnf():
    if os.path.exists('/usr/bin/dnf'):
        return True
    return False

def is_apt():
    if os.path.exists('/usr/bin/apt'):
        return True
    return False

def upgrade_by_yum():
    global upgrade_log_file,log_msg
    res = public.ExecShell("rpm -q polkit")[0]
    if res.startswith('polkit-'):
        os.system("yum -y update polkit &> {}".format(upgrade_log_file))
        res2 = public.ExecShell("rpm -q polkit")[0]
        if res == res2:
            write_log("修复失败,请手动执行命令: yum -y update polkit")
            return False
        public.WriteLog('漏洞修复',log_msg)
        return True
    return False

def upgrade_by_dnf():
    global upgrade_log_file,log_msg
    res = public.ExecShell("rpm -q polkit")[0]
    if res.startswith('polkit-'):
        os.system("dnf -y update polkit &> {}".format(upgrade_log_file))
        res2 = public.ExecShell("rpm -q polkit")[0]
        if res == res2:
            write_log("修复失败,请手动执行命令: dnf -y update polkit")
            return False
        public.WriteLog('漏洞修复',log_msg)
        return True
    return False


def upgrade_by_apt():
    global upgrade_log_file,log_msg
    res = public.ExecShell("dpkg -l policykit-1|grep policykit-1|awk '{print $3}'")[0]
    if res.startswith('0.105'):
        os.system("apt-get -y install policykit-1 &> {}".format(upgrade_log_file))
        res2 = public.ExecShell("dpkg -l policykit-1|grep policykit-1|awk '{print $3}'")[0]
        if res == res2:
            write_log("修复失败,请手动执行命令: apt-get -y install policykit-1")
            return False
        public.WriteLog('漏洞修复',log_msg)
        return True
    return False

def check():
    tip_file = '/www/server/panel/data/upgrade_polkit.pl'
    if os.path.exists(tip_file):
        return
    write_log("正在修复polkit(CVE-2021-4034)提权漏洞...")
    if is_yum():
        upgrade_by_yum()
    elif is_dnf():
        upgrade_by_dnf()
    elif is_apt():
        upgrade_by_apt()
    else:
        return

    public.writeFile(tip_file,'True')


if __name__ == "__main__":
    tip_file = '/www/server/panel/data/upgrade_polkit_run.pl'
    if os.path.exists(tip_file):
        print("程序正在运行中,退出!")
        sys.exit(1)

    public.writeFile(tip_file,'True')
    try:
        check()
    except:
        pass
    finally:
        if os.path.exists(tip_file): os.remove(tip_file)


