import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保使用了时间同步'
_version = 1.0
_ps = '检查是否启用时间同步（ntp/chrony/timesyncd）'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_time_sync_used.pl")
_tips = [
    '在未启用主机时间同步的系统上安装并配置ntp或chrony',
    'ntp示例：yum install ntp 或 apt-get install ntp；在/etc/ntp.conf配置server行',
    'chrony示例：yum install chrony 或 apt-get install chrony；在/etc/chrony.conf配置server行'
]
_help = ''
_remind = '系统时间应在环境中的所有系统之间同步。 这通常通过建立权威时间服务器或服务器集并让所有系统将它们的时钟同步到它们来完成。\n时间同步对于支持时间敏感的安全机制（如Kerberos）很重要，并且还确保日志文件在整个企业中具有一致的时间记录， 帮助进行取证调查。'


def check_run():
    try:
        used = False
        if os.path.exists('/etc/ntp.conf'):
            conf = public.readFile('/etc/ntp.conf') or ''
            if re.findall(r'^\s*(?!#)\s*server\s+\S+', conf, re.M):
                used = True
        for f in ['/etc/chrony.conf', '/etc/chrony/chrony.conf']:
            if os.path.exists(f):
                conf = public.readFile(f) or ''
                if re.findall(r'^\s*(?!#)\s*server\s+\S+', conf, re.M):
                    used = True
                    break
        tsf = '/etc/systemd/timesyncd.conf'
        if os.path.exists(tsf):
            conf = public.readFile(tsf) or ''
            if re.search(r'^\s*(?!#)\s*NTP\s*=\s*\S+', conf, re.M):
                used = True
        if not used:
            return False, '未配置时间同步'
        return True, '无风险'
    except:
        return True, '无风险'