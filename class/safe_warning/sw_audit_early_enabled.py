import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保启用对auditd之前启动的进程的审计'
_version = 1.0
_ps = '检查是否启用auditd进程日志审计'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_audit_early_enabled.pl")
_tips = [
    "编辑`/etc/default/grub`在`GRUB_CMDLINE_LINUX`添加`audit=1`",
    "CentOS/RHEL：`grub2-mkconfig -o /boot/grub2/grub.cfg`",
    "Debian/Ubuntu：`update-grub`",
    "旧版Grub：编辑`/boot/grub/grub.conf`将所有`kernel`行追加`audit=1`"
]
_help = ''
_remind = '未启用audit=1会导致auditd启动前的进程未被审计；启用后可覆盖系统引导阶段事件，提升合规与溯源能力'


def check_run():
    try:
        hits = []
        df = '/etc/default/grub'
        if os.path.exists(df):
            body = public.readFile(df) or ''
            ok1 = re.search(r'^\s*(?!#)\s*GRUB_CMDLINE_LINUX[^\n]*\baudit=1\b', body, re.M)
            ok2 = re.search(r'^\s*(?!#)\s*GRUB_CMDLINE_LINUX_DEFAULT[^\n]*\baudit=1\b', body, re.M)
            if ok1 or ok2:
                hits.append(df)
        cfgs = [
            '/boot/grub2/grub.cfg',
            '/etc/grub2.cfg',
            '/boot/grub/grub.cfg',
            '/boot/grub/grub.conf'
        ]
        checked_cfgs = []
        for fp in cfgs:
            if not os.path.exists(fp):
                continue
            body = public.readFile(fp) or ''
            if re.search(r'^\s*(linux|kernel)\b[^\n]*\baudit=1\b', body, re.M):
                hits.append(fp)
            checked_cfgs.append(fp)
        if hits:
            return True, '无风险'
        parts = []
        if os.path.exists(df):
            parts.append('/etc/default/grub未在GRUB_CMDLINE_LINUX/GRUB_CMDLINE_LINUX_DEFAULT设置audit=1\n')
        if checked_cfgs:
            parts.append('grub配置(kernel/linux行)未启用audit=1: ' + ','.join(checked_cfgs))
        msg = '未在引导配置中启用audit=1' if not parts else '；'.join(parts)
        return False, msg
    except:
        return True, '无风险'