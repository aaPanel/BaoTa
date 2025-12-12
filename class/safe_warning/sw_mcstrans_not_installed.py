import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = '确保MCS Translation未安装'
_version = 1.0
_ps = '检查是否卸载mcstrans组件'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_mcstrans_not_installed.pl")
_tips = [
    "卸载：`yum remove mcstrans`"
]
_help = ''
_remind = 'mcstransd守护程序向请求信息的客户端进程提供类别标签信息。 标签翻译在/etc/selinux/targeted/setrans.conf中定义。\n由于此服务不经常使用，因此请删除它以减少系统上运行的潜在易受攻击代码的数量。'


def check_run():
    try:
        paths = [
            '/usr/sbin/mcstransd',
            '/usr/lib/systemd/system/mcstrans.service'
        ]
        for p in paths:
            if os.path.exists(p):
                return False, '检测到mcstrans组件：{}'.format(p)
        return True, '无风险'
    except:
        return True, '无风险'