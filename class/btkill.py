#coding: utf-8
# +-------------------------------------------------------------------
# | Linux异常进程专杀
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2019 宝塔软件(https://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------

#使用示例： 
#    1、将此文件重命名为btkill.py , 然后上传到服务器/root目录
#    2、执行 python /root/btkill.py

import psutil,time,os

class btkill:
    __limit = 10;   #Cpu使用率触发上限
    __vmsize = 1048576/4;  #虚拟内存触发上限(字节)

    def checkMain(self):
        pids = psutil.pids()
        num = 0;
        for pid in pids:
            try:
                p = psutil.Process(pid);
                if p.exe() == "": continue;
                name = p.name()
                if self.whiteList(name): continue;
                cputimes = p.cpu_times()
                if cputimes.user < 0.1: continue;
                percent = p.cpu_percent(interval = 0.1);
                vm = p.memory_info().vms
                if percent > self.__limit or vm > self.__vmsize:
                    log = time.strftime('%Y-%m-%d %X',time.localtime()) + "  (PID=" + str(pid) + ", NAME=" + name + ", VMS=" + str(vm) + ", PERCENT=" + str(percent) + "%)";
                    p.kill();
                    num += 1
                    print log + " >> killed\n";
            except Exception as ex:print str(ex)
        return num

    #检查白名单
    def whiteList(self,name):
        wlist = ['yum','apt-get','apt','redis-cli','memcached','sshd','vm','vim','htop','top','sh','bash','zip','gzip','rsync',
                 'tar','unzip','php','composer','pkill','mongo','mongod','php-fpm','nginx','httpd','lsof','ps','redis-server',
                 'mysqld','mysqld_safe','mysql','pure-ftpd','sparse_dd','stunnel','squeezed','vncterm','awk','ruby','postgres',
                 'mpathalert','vncterm','multipathd','fe','elasticsyslog','syslogd','v6d','xapi','screen','runsvdir','svlogd',
                 'java','udevd','ntpd','irqbalance','qmgr','wpa_supplicant','mysqld_safe','sftp-server','lvmetad','gitlab-web',
                 'pure-ftpd','auditd','master','dbus-daemon','tapdisk','sshd','init','ksoftirqd','kworker','kmpathd',
                 'kmpath_handlerd','python','kdmflush','bioset','crond','kthreadd','migration','rcu_sched','kjournald',
                 'gcc','gcc++','nginx','mysqld','php-cgi','login','firewalld','iptables','systemd','network','dhclient',
                 'systemd-journald','NetworkManager','systemd-logind','systemd-udevd','polkitd','tuned','rsyslogd','AliYunDunUpdate','AliYunDun','sendmail']
        wslist = ['vif','qemu','scsi_eh','xcp','xen','docker','yunsuo','aliyun','PM2']

        for key in wlist:
            if key == name: return True

        for key in wslist:
            if name.find(key) != -1: return True

        return False


    #开始处理
    def start(self):
        num = 0;
        while True:
            num += self.checkMain();
            time.sleep(3);
        print '======================================='
        print "查杀完成, 共查杀["+str(num)+"]个异常进程!"
        print "官网: https://www.bt.cn/bbs"



if __name__ == "__main__":
    print "正在检测异常进程..."
    print '======================================='
    c = btkill();
    c.start();
