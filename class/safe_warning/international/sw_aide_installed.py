import sys, os, shutil
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = '确保AIDE安装'
_version = 1.0
_ps = '检查AIDE是否安装'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_aide_installed.pl")
_tips = [
    'Debian/Ubuntu安装：apt-get install aide && aideinit',
    'RHEL/CentOS安装：yum install aide && aide --init && mv /var/lib/aide/aide.db.new.gz /var/lib/aide/aide.db.gz'
]
_help = ''
_remind = '未部署AIDE无法发现关键系统文件被篡改；安装并初始化后可提供文件完整性审计与告警，降低入侵与误改风险'


def check_run():
    try:
        if shutil.which('aide'):
            return True, '无风险'
        bins = [
            '/usr/bin/aide',
            '/usr/sbin/aide',
            '/usr/local/bin/aide',
            '/usr/local/sbin/aide'
        ]
        found_exec = None
        for p in bins:
            try:
                if os.path.exists(p) and os.access(p, os.X_OK):
                    found_exec = p
                    break
            except:
                pass
        if found_exec:
            return True, '无风险'
        rpm_ok = False
        dpkg_ok = False
        try:
            out, err = public.ExecShell('rpm -q aide')
            if out and ('aide' in out) and ('not installed' not in out.lower()):
                rpm_ok = True
        except:
            pass
        try:
            out, err = public.ExecShell('dpkg -s aide | grep Status')
            if out and ('install ok installed' in out):
                dpkg_ok = True
        except:
            pass
        if rpm_ok or dpkg_ok:
            return True, '无风险'
        return False, '未检测到AIDE：未找到可执行文件(/usr/bin/aide,/usr/sbin/aide,/usr/local/bin/aide,/usr/local/sbin/aide)，且rpm/dpkg查询未安装'
    except:
        return True, '无风险'