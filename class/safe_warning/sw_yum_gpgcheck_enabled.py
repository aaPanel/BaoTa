import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保全局激活gpgcheck'
_version = 1.0
_ps = '检查是否启用YUM包签名校验'
_level = 2
_date = '2025-11-22'
_ignore = os.path.exists("data/warning/ignore/sw_yum_gpgcheck_enabled.pl")
_tips = [
    '在`/etc/yum.conf`的`[main]`设置：gpgcheck=1',
    '在`/etc/yum.repos.d/*.repo`将所有`gpgcheck`实例设置为1：sed -ri "s/^[[:space:]]*gpgcheck[[:space:]]*=.*/gpgcheck=1/" /etc/yum.repos.d/*.repo'
]
_help = ''
_remind = '在/etc/yum.conf的主要部分和单个/etc/yum/repos.d/*文件中找到的gpgcheck选项确定在安装之前是否检查了RPM软件包的签名。\n确保 始终在安装之前检查RPM的程序包签名，以确保从受信任的来源获取软件。'


def check_run():
    try:
        # 仅centos系统检测
        if not os.path.exists('/etc/centos-release'):
            return True, '无风险'
        issues = []
        yum_conf = '/etc/yum.conf'
        conf = public.readFile(yum_conf) or ''
        main_g = None
        if conf:
            for m in re.findall(r'^\s*(?!#)\s*gpgcheck\s*=\s*(\S+)\s*$', conf, re.M):
                main_g = m.strip()
                break
            if main_g != '1':
                issues.append('/etc/yum.conf [main] 未启用gpgcheck=1')
        repos_dir = '/etc/yum.repos.d'
        if os.path.isdir(repos_dir):
            for name in os.listdir(repos_dir):
                if not name.endswith('.repo'):
                    continue
                fp = os.path.join(repos_dir, name)
                body = public.readFile(fp) or ''
                for m in re.findall(r'^\s*(?!#)\s*gpgcheck\s*=\s*(\S+)\s*$', body, re.M):
                    if m.strip() != '1':
                        issues.append('{} 未启用gpgcheck=1'.format(fp))
        if issues:
            return False, 'gpgcheck未全局启用：{}'.format('、'.join(issues))
        return True, '无风险'
    except:
        return True, '无风险'