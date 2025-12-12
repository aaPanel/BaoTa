import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = '确保/tmp分区设置了nosuid选项'
_version = 1.0
_ps = '检查nosuid是否禁止/tmp中创建具有setuid位的文件'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_tmp_nosuid.pl")
_tips = [
    '第一种Debian/Ubuntu：编辑文件`/etc/fstab`添加 nosuid 选项，添加如下信息',
    '`tmpfs /tmp tmpfs defaults,nodev,nosuid,noexec 0 0`',
    '执行以下命令重新挂载 /tmp：mount -o remount,nosuid /tmp',
    '第二种CentOS系统：',
    '编辑 /etc/systemd/system/local-fs.target.wants/tmp.mount 文件添加 nosuid 选项：',
    'Options=mode=1777,strictatime,noexec,nodev,nosuid',
    '执行以下命令重新挂载 /tmp：mount -o remount,nosuid /tmp'
]
_help = ''
_remind = '由于/tmp文件系统只用于临时文件存储，因此请设置此选项以确保用户无法在/tmp中创建setuid文件。'


def check_run():
    try:
        mounts = public.ReadFile('/proc/mounts')
        if mounts:
            for line in mounts.splitlines():
                parts = line.split()
                if len(parts) < 4:
                    continue
                if parts[1] == '/tmp':
                    opts = parts[3].split(',')
                    if 'nosuid' in opts:
                        return True, '无风险'
                    return False, '未设置/tmp的nosuid挂载选项'
        unit = '/etc/systemd/system/local-fs.target.wants/tmp.mount'
        if os.path.exists(unit):
            body = public.ReadFile(unit) or ''
            if 'Options=' in body and 'nosuid' in body:
                return True, '无风险'
        return False, '未设置/tmp的nosuid挂载选项'
    except:
        return True, '无风险'