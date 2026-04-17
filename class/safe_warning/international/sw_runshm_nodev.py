import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = '确保/run/shm分区设置了nodev选项'
_version = 1.0
_ps = '检查是否设置nodev防止创建特殊设备'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_runshm_nodev.pl")
_tips = [
    '示例挂载行：`tmpfs /run/shm tmpfs defaults,nodev,nosuid,noexec 0 0`',
    '编辑/etc/fstab在/run/shm挂载项增加nodev，并执行：`mount -o remount,nodev /run/shm`'
]
_help = ''
_remind = '阻止在共享内存分区创建设备文件'


def check_run():
    try:
        # 只检测ubuntu系统
        if not isUbuntu():
            return True, '无风险'
        mounts = public.ReadFile('/proc/mounts')
        if not mounts:
            return True, '无风险'
        for line in mounts.splitlines():
            parts = line.split()
            if len(parts) < 4:
                continue
            if parts[1] == '/run/shm':
                opts = parts[3].split(',')
                if 'nodev' in opts:
                    return True, '无风险'
                return False, '未设置/run/shm的nodev挂载选项'
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