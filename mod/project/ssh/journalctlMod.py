import os
import sys
from datetime import datetime
if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

os.chdir("/www/server/panel")
import public

from mod.project.ssh.base import SSHbase


class JournalctlManage(SSHbase):
    def __init__(self):
        super(JournalctlManage, self).__init__()

    def get_journalctl_logs(self, file_positions):
        '''
        获取 systemd journalctl 的 SSH 登录日志
        return  日志,游标位置
        '''
        new_logins = []
        current_positions = ""

        command_list = [
                "journalctl -u ssh --no-pager --show-cursor --grep='Accepted|Failed password for|Accepted publickey'",  # 全量获取
                "journalctl -u ssh --since '30 days ago' --no-pager --show-cursor --grep='Accepted|Failed password for|Accepted publickey'",  # 30天
                "journalctl -u ssh --no-pager --show-cursor --grep='Accepted|Failed password for|Accepted publickey' --cursor='{}'".format(file_positions)  # 从记录的游标开始读取
            ]

        if not file_positions:
            # 获取systemd日志所占用的空间
            res, err = public.ExecShell("journalctl --disk-usage")
            total_bytes = public.parse_journal_disk_usage(res)
            limit_bytes = 5 * 1024 * 1024 * 1024
            # 大于5G 取30天的数据量
            command = command_list[1] if total_bytes > limit_bytes else command_list[0]
            content = public.ExecShell(command)[0].strip()
        else:
            content = public.ExecShell(command_list[2])[0].strip()

        lines = content.split('\n')
        if lines:
             # 处理去除多余游标字符
            current_positions = lines[-1].replace("-- cursor: ", "")

        for line in lines[:-1]:
            if "No entries" in line:break

            if any(keyword in line for keyword in ["Accepted password", "Failed password", "Accepted publickey"]):
                parts = line.split()
                year = datetime.now().year
                entry = self.parse_login_entry(parts, year)
                if entry:
                    entry["log_file"] = "journalctl"
                    new_logins.append(entry)
        return new_logins, current_positions
