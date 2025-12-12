import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = '确保bootloader未禁用AppArmor'
_version = 1.0
_ps = '检查bootloader配置是否包含禁用AppArmor的配置'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_apparmor_bootloader_not_disabled.pl")
_tips = [
    "编辑`/etc/default/grub`并从GRUB_CMDLINE_LINUX、GRUB_CMDLINE_LINUX_DEFAULT参数中删除apparmor = 0",
    "执行`update-grub` 更新配置"
]
_help = ''
_remind = '将AppArmor配置为在引导时启用，并验证它是否未被引导加载程序引导参数覆盖。必须在引导加载程序配置中的引导时启用AppArmor，以确保不会覆盖它提供的控件。'


def check_run():
    try:
        # 只检测ubuntu系统
        if not isUbuntu():
            return True, '无风险'

        files = [
            '/etc/default/grub',
            '/boot/grub2/grub.cfg',
            '/etc/grub2.cfg',
            '/boot/grub/grub.cfg',
            '/boot/grub/grub.conf'
        ]
        for fp in files:
            if not os.path.exists(fp):
                continue
            body = public.readFile(fp) or ''
            if 'apparmor=0' in body:
                return False, '引导配置文件{}包含禁用AppArmor参数：{}'.format(fp, 'apparmor=0')
        return True, '无风险'
    except:
        return True, '无风险'

def isUbuntu(self):
    try:
        if os.path.exists('/etc/lsb-release'):
            body = public.readFile('/etc/lsb-release') or ''
            if 'DISTRIB_ID=Ubuntu' in body:
                return True
        return False
    except:
        return False