import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保收集成功的文件系统挂载'
_version = 1.0
_ps = '检查是否开启监控非特权用户执行mount系统调用，识别异常挂载行为'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_audit_mounts_events.pl")
_tips = [
    "在`/etc/audit/rules.d/audit.rules`和`/etc/audit/audit.rules`添加：",
    "-a always,exit -F arch=b64 -S mount -F auid>=1000 -F auid!=4294967295 -k mounts",
    "-a always,exit -F arch=b32 -S mount -F auid>=1000 -F auid!=4294967295 -k mounts",
    "重启：`service auditd restart`"
]
_help = ''
_remind = '监视mount系统调用的使用。 mount（和umount）系统调用控制文件系统的安装和卸载。以下参数将系统配置为在非特权用户使用装载系统调用时创建审计记录非特权用户将文件系统挂载到系统是非常不寻常的。跟踪挂载命令为系统管理员提供了可能已挂载外部媒体的证据（基于对挂载源的检查并确认它是外部媒体类型），但它并不能最终表明数据已导出到媒体。希望确定数据是否已导出的系统管理员还必须跟踪成功的打开，创建和截断系统调用，这些调用需要对外部媒体文件系统的安装点下的文件进行写访问。这可以给出写入发生的公平指示。真正证明它的唯一方法是跟踪对外部媒体的成功写入。跟踪写入系统调用可能会快速填满审核日志，不建议这样做。有关跟踪数据导出到媒体的配置选项的建议超出了本文档的范围。'


def check_run():
    try:
        # 只检查centos系统
        if not os.path.exists('/etc/centos-release'):
            return True, '无风险'

        files = ['/etc/audit/rules.d/audit.rules', '/etc/audit/audit.rules']
        contents = []
        for f in files:
            if os.path.exists(f):
                contents.append(public.readFile(f) or '')
        if not contents:
            return False, '未检测到audit规则文件'
        body = '\n'.join(contents)
        rules = [
            (r'^\s*-a\s+always,exit\s+-F\s+arch=b64\s+-S\s+mount\s+-F\s+auid>=1000\s+-F\s+auid!=4294967295\s+-k\s+mounts\s*$', '-a always,exit -F arch=b64 -S mount -F auid>=1000 -F auid!=4294967295 -k mounts'),
            (r'^\s*-a\s+always,exit\s+-F\s+arch=b32\s+-S\s+mount\s+-F\s+auid>=1000\s+-F\s+auid!=4294967295\s+-k\s+mounts\s*$', '-a always,exit -F arch=b32 -S mount -F auid>=1000 -F auid!=4294967295 -k mounts')
        ]
        missing = []
        for p, line in rules:
            if not re.search(p, body, re.M):
                missing.append(line)
        if missing:
            return False, '缺少审计规则：' + '；'.join(missing)
        return True, '无风险'
    except:
        return True, '无风险'