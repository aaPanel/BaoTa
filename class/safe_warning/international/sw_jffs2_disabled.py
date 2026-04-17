import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保jffs2文件系统挂载禁用'
_version = 1.0
_ps = '检查是否禁用jffs2文件系统模块'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_jffs2_disabled.pl")
_tips = [
    '创建或编辑/etc/modprobe.d/CIS.conf添加：install jffs2 /bin/true'
]
_help = ''
_remind = 'jffs2（日志记录闪存文件系统2）文件系统类型是用于闪存设备的日志结构文件系统。\n删除对不需要的文件系统类型的支持减少了系统的本地攻击面。 如果不需要此文件系统类型，请将其禁用。'


def check_run():
    try:
        d = '/etc/modprobe.d'
        if not os.path.isdir(d):
            return True, '无风险'
        for name in os.listdir(d):
            if not name.endswith('.conf'):
                continue
            fp = os.path.join(d, name)
            body = public.readFile(fp) or ''
            if re.search(r'^\s*(?!#)\s*install\s+jffs2\s+/bin/true\s*$', body, re.M):
                return True, '无风险'
        return False, '未在/etc/modprobe.d/*.conf配置禁用规则：install jffs2 /bin/true'
    except:
        return True, '无风险'