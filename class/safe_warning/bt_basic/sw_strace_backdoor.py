#!/usr/bin/python
#coding: utf-8

import os, psutil

_title = 'strace获取登录凭证后门检测'
_version = 1.0  # 版本
_ps = "检测进程中是否有通过strace命令获取其他用户账号信息"  # 描述
_level = 3  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-09'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_strace_backdoor.pl")
_tips = [
    "使用kill -9 【pid】命令杀死恶意进程",
    "对服务器进行全方面的安全检查，排查其余后门"
]
_help = ''
_remind = '检测到服务器存在黑客入侵行为，通过方案命令可以及时中断黑客行为，防止服务器被进一步入侵控制。'


def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    # 获取所有进程的信息
    all_processes = psutil.process_iter()
    ssh_pid = ""
    strace_cmdline = []
    strace_pid = ""
    for process in all_processes:
        if "strace" == process.name():
            strace_cmdline = process.cmdline()
            strace_pid = str(process.pid)
            break
    if len(strace_cmdline) == 0 or not strace_pid:
        return True, '无风险'

    for process in all_processes:
        # 获取sshd的pid
        if "sshd" == process.name() and "/usr/sbin/sshd" in process.cmdline():
            ssh_pid = str(process.pid)
            break

    if not ssh_pid:
        return True, '无风险'

    if (ssh_pid in strace_cmdline and "trace=read,write,connect" in strace_cmdline) or (ssh_pid in strace_cmdline and "trace=read,write" in strace_cmdline):
        return False, '发现利用strace命令窃取sshd信息的恶意进程：<br>进程命令：{}<br>pid：{}'.format(' '.join(strace_cmdline), strace_pid)

    return True, '无风险'
    #
    # s_time = time.time()
    # sshd_pid = public.ExecShell('ps ax|grep "sshd -D"|grep -v grep|awk {\'print$2\'}')[0].strip()
    # public.print_log("一：{}".format(time.time()-s_time))
    # s_time = time.time()
    # result = public.ExecShell('ps aux')[0].strip()
    # public.print_log("二：{}".format(time.time()-s_time))
    # rep = 'strace.*' + sshd_pid + '.*trace=read,write'
    # tmp = re.search(rep, result)
    # if tmp:
    #     return False, '存在通过strace窃取sshd登录信息的恶意进程'
    # else:
    #     return True, '无风险'
