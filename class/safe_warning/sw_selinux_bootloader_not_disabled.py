import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保bootloader配置中SELinux未禁用'
_version = 1.0
_ps = '检查是否移除SELinux防护'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_selinux_bootloader_not_disabled.pl")
_tips = [
    "编辑`/etc/default/grub`从`GRUB_CMDLINE_LINUX*`中移除`selinux=0`、`enforcing=0`",
    "CentOS/RHEL：`grub2-mkconfig > /boot/grub2/grub.cfg`",
    "Debian/Ubuntu：`update-grub`",
    "旧版：编辑`/boot/grub/grub.conf`移除`selinux=0`与`enforcement=0`"
]
_help = ''
_remind = '将SELINUX配置为在引导时启用，并验证它是否未被grub引导参数覆盖。\n必须在grub配置中启动时启用SELinux，以确保不会覆盖它提供的控件。'


def check_run():
    try:
        files = [
            '/etc/default/grub',
            '/boot/grub2/grub.cfg',
            '/etc/grub2.cfg',
            '/boot/grub/grub.cfg',
            '/boot/grub/grub.conf'
        ]
        bad_tokens = ('selinux=0', 'enforcing=0', 'enforcement=0')
        hits = []
        for fp in files:
            if not os.path.exists(fp):
                continue
            body = public.readFile(fp) or ''
            for t in bad_tokens:
                if t in body:
                    hits.append(fp + ':' + t)
        if hits:
            return False, '引导配置含禁用SELinux参数：{}'.format(','.join(hits))
        return True, '无风险'
    except:
        return True, '无风险'