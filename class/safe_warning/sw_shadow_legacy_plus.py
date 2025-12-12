import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保/etc/shadow中没有遗留的＂+＂条目'
_version = 1.0
_ps = '检查/etc/shadow是否遗留“+”条目'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_shadow_legacy_plus.pl")
_tips = [
    "备份：`cp -a /etc/shadow /etc/shadow.bak.$(date +%F)`",
    "清理：`sed -i '/^\\s*\\+/d' /etc/shadow`"
]
_help = ''
_remind = '各种文件中的字符+曾经是系统的标记，用于在系统配置文件中的某个点插入来自NIS映射的数据。 大多数系统不再需要这些条目，但可能存在于从其他平台导入的文件中。\n这些条目可以为攻击者提供获得系统特权访问的途径。'


def check_run():
    try:
        sf = '/etc/shadow'
        body = public.readFile(sf)
        if not body:
            return True, '无风险'
        hits = re.findall(r'^\s*\+.*$', body, re.M)
        if hits:
            return False, '存在遗留"+"条目：{}条'.format(len(hits))
        return True, '无风险'
    except:
        return True, '无风险'