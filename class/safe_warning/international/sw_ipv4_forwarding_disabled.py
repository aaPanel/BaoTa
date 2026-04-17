import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保IP转发禁用(仅限主机)'
_version = 1.1
_ps = '检查是否禁用IPv4转发'
_level = 2
_date = '2025-01-15'
_ignore = os.path.exists("data/warning/ignore/sw_ipv4_forwarding_disabled.pl")
_tips = [
    "在`/etc/sysctl.conf`设置：net.ipv4.ip_forward = 0",
    "执行：sysctl -w net.ipv4.ip_forward=0",
    "执行：sysctl -w net.ipv4.route.flush=1",
]
_help = ''
_remind = '若服务器作为docker宿主机，请忽略此项，将标志设置为0可确保具有多个接口的系统（例如，硬代理）永远无法转发数据包， 因此，不可作为路由器'


def check_container_env():
    '''检测是否运行容器或虚拟化环境（需要IP转发）'''
    # 检查Docker
    if os.path.exists('/usr/bin/docker') or os.path.exists('/usr/bin/dockerd'):
        try:
            output, err = public.ExecShell('docker ps -q 2>/dev/null')
            if output.strip():
                return True
        except:
            pass
        # 检查Docker服务是否运行
        try:
            output, err = public.ExecShell('systemctl is-active docker 2>/dev/null')
            if 'active' in output or 'running' in output:
                return True
        except:
            pass

    # 检查containerd
    try:
        output, err = public.ExecShell('systemctl is-active containerd 2>/dev/null')
        if 'active' in output:
            return True
    except:
        pass

    # 检查Podman
    if os.path.exists('/usr/bin/podman'):
        try:
            output, err = public.ExecShell('podman ps -q 2>/dev/null')
            if output.strip():
                return True
        except:
            pass

    # 检查KVM/libvirt虚拟机
    if os.path.exists('/usr/bin/virsh'):
        try:
            output, err = public.ExecShell('virsh list 2>/dev/null | grep -c "running"')
            if output.strip() and int(output.strip()) > 0:
                return True
        except:
            pass

    # 检查容器相关内核模块
    try:
        modules, err = public.ExecShell('lsmod | grep -E "bridge|overlay|br_netfilter|nf_conntrack"')
        if modules.strip():
            return True
    except:
        pass

    return False


def check_run():
    try:
        # 检测容器/虚拟化环境，如果存在则跳过检测
        if check_container_env():
            return True, '无风险（检测到容器/虚拟化环境，需要IP转发）'

        # 普通服务器才检测IP转发配置
        conf = public.readFile('/etc/sysctl.conf') or ''
        ok = re.search(r'^\s*(?!#)\s*net\.ipv4\.ip_forward\s*=\s*0\s*$', conf, re.M)
        if ok:
            return True, '无风险'
        return False, '未在/etc/sysctl.conf设置：net.ipv4.ip_forward=0'
    except:
        return True, '无风险'