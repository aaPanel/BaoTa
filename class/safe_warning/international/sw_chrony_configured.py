import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保配置了chrony'
_version = 1.0
_ps = '检查是否配置配置了chrony'
_level = 2
_date = '2025-11-22'
_ignore = os.path.exists("data/warning/ignore/sw_chrony_configured.pl")
_tips = [
    '在`/etc/chrony.conf`添加或编辑服务器行：server <remote-server>',
    '在`/etc/sysconfig/chronyd`设置：OPTIONS="-u chrony"，或在`/usr/lib/systemd/system/chronyd.service`的`ExecStart`包含`-u chrony`',
    '启用并重启：systemctl enable --now chronyd'
]
_help = ''
_remind = 'chrony是一个实现网络时间协议（NTP）的守护进程，用于在各种系统中同步系统时钟，并使用高度准确的源。可以将同步配置为客户端和/或服务器。如果是chrony，则 在系统上使用正确的配置对于确保时间同步正常工作至关重要。\n此建议仅适用于在系统上使用chrony的情况。'


def check_run():
    try:
        # 仅centos系统检测
        if not os.path.exists('/etc/centos-release'):
            return True, '无风险'
        conf_file = '/etc/chrony.conf'
        miss = []
        if os.path.exists(conf_file):
            conf = public.readFile(conf_file) or ''
            has_server = re.findall(r'^\s*(?!#)\s*(server|pool)\s+\S+', conf, re.M)
            if not has_server:
                miss.append('缺少server/pool行（/etc/chrony.conf）')
        syscfg = '/etc/sysconfig/chronyd'
        unitf = '/usr/lib/systemd/system/chronyd.service'
        checked_u = False
        if os.path.exists(syscfg):
            s = public.readFile(syscfg) or ''
            checked_u = True
            if '-u chrony' not in s:
                miss.append('chronyd未以chrony用户运行（缺少 -u chrony）')
        elif os.path.exists(unitf):
            s = public.readFile(unitf) or ''
            checked_u = True
            if '-u chrony' not in s:
                miss.append('chronyd未以chrony用户运行（缺少 -u chrony）')
        if miss:
            return False, 'chrony配置不规范：{}'.format('、'.join(miss))
        return True, '无风险'
    except:
        return True, '无风险'