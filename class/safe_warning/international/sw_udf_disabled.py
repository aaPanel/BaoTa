import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保udf文件系统挂载禁用'
_version = 1.0
_ps = '检查是否禁用UDF文件系统模块'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_udf_disabled.pl")
_tips = [
    '创建或编辑/etc/modprobe.d/CIS.conf添加：install udf /bin/true'
]
_help = ''
_remind = 'udf文件系统类型是用于实现ISO / IEC 13346和ECMA-167规范的通用磁盘格式。 这是一种开放的供应商文件系统类型，用于在各种媒体上进行数据存储。 此文件系统类型是支持写入DVD和更新光盘格式所必需的。删除对不需要的文件系统类型的支持可减少系统的本地攻击面。 \n如果不需要此文件系统类型，请将其禁用。'


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
            if re.search(r'^\s*(?!#)\s*install\s+udf\s+/bin/true\s*$', body, re.M):
                return True, '无风险'
        return False, '未在/etc/modprobe.d/*.conf配置禁用规则：install udf /bin/true'
    except:
        return True, '无风险'