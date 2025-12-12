# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
# -------------------------------------------------------------------

# ssh信息
# ------------------------------
import json
import os
import re
import time

import public
from safeModel.base import safeBase
from datetime import datetime


class main(safeBase):

    def __init__(self):
        pass

    # 获取当天登陆失败/登陆成功计数
    def __get_today_stats(self):
        today_err_num1 = int(public.ExecShell(
            "journalctl -u ssh --no-pager -S today |grep -a 'Failed password for' |grep -v 'invalid' |wc -l")[0])
        today_err_num2 = int(public.ExecShell(
            "journalctl -u ssh --no-pager -S today |grep -a 'Connection closed by authenticating user' |grep -a 'preauth' |wc -l")[0])
        today_success = int(public.ExecShell("journalctl -u ssh --no-pager -S today |grep -a 'Accepted' |wc -l")[0])
        return today_err_num1 + today_err_num2, today_success

    # 更新ssh统计记录
    def __update_record_with_today_stats(self, record):
        today_err_num, today_success = self.__get_today_stats()
        if record["today_success"] < today_success: record["success"] += today_success
        if record["today_error"] < today_err_num: record["error"] += today_err_num
        record['today_error'] = today_err_num
        record['today_success'] = today_success

    # 获取终端执行命令记录
    def ssh_cmd_history(self, get):
        try:
            result = []
            file_path = "/root/.bash_history"
            data = public.readFile(file_path) if os.path.exists(file_path) else None

            danger_cmd = ['rm', 'rmi', 'kill', 'stop', 'pause', 'unpause', 'restart', 'update', 'exec', 'init',
                          'shutdown', 'reboot', 'chmod', 'chown', 'dd', 'fdisk', 'killall', 'mkfs', 'mkswap', 'mount',
                          'swapoff', 'swapon', 'umount', 'userdel', 'usermod', 'passwd', 'groupadd', 'groupdel',
                          'groupmod', 'chpasswd', 'chage', 'usermod', 'useradd', 'userdel', 'pkill']

            if data:
                data_list = data.split("\n")
                for i in data_list:
                    if len(result) >= 200: break
                    if not i or i.startswith("#"):
                        continue

                    is_dangerous = any(cmd in i for cmd in danger_cmd)

                    result.append({
                        "command": i,
                        "is_dangerous": is_dangerous
                    })
            else:
                result = []

            return public.returnMsg(True, {
                "data": result,
                "total": len(result)
            })
        except:
            return public.returnMsg(False, {
                "data": [],
                "total": 0
            })

    def get_ssh_intrusion(self, get):
        """
        @获取SSH爆破次数
        @param get:
        """
        result = {'error': 0, 'success': 0, 'today_error': 0, 'today_success': 0}

        # debian系统处理
        if os.path.exists("/etc/debian_version"):
            version = public.readFile('/etc/debian_version').strip()
            if 'bookworm' in version or 'jammy' in version or 'impish' in version:
                version = 12
            else:
                try:
                    version = float(version)
                except:
                    version = 11

            if version >= 12:
                try:
                    # # 优先取缓存
                    pkey = "version_12_ssh_login_counts"
                    if public.cache_get(pkey):
                        return public.cache_get(pkey)

                    # 读取记录文件
                    filepath = "/www/server/panel/data/ssh_login_counts.json"
                    filedata = public.readFile(filepath) if os.path.exists(filepath) else public.writeFile(filepath, "[]")
                    today = datetime.now().strftime('%Y-%m-%d')
                    # 解析记录文件的内容
                    try:
                        data_list = json.loads(filedata)
                    except:
                        data_list = []

                    if data_list:
                        for index, record in enumerate(data_list):
                            # 如果记录中有当天的数据，则直接返回
                            if record['date'] == today:
                                self.__update_record_with_today_stats(record)
                                if index == 0:  # 确保只在首次找到匹配项时返回
                                    data_list[0] = record
                                    # 设置缓存
                                    public.cache_set(pkey, record, 30)
                                    return record
                            else:
                                record = data_list[0]
                                self.__update_record_with_today_stats(record)
                                # 设置缓存
                                public.cache_set(pkey, record, 30)
                                return record

                    # 没有记录文件   按原先的方式获取
                    err_num1 = int(public.ExecShell(
                        "journalctl -u ssh --no-pager |grep -a 'Failed password for' |grep -v 'invalid' |wc -l")[0])
                    err_num2 = int(public.ExecShell(
                        "journalctl -u ssh --no-pager --grep='Connection closed by authenticating user|preauth' |wc -l")[0])
                    result['error'] = err_num1 + err_num2
                    result['success'] = int(public.ExecShell("journalctl -u ssh --no-pager|grep -a 'Accepted' |wc -l")[0])

                    today_err_num, today_success = self.__get_today_stats()
                    result['today_error'] = today_err_num
                    result['today_success'] = today_success
                    # 设置缓存
                    public.cache_set(pkey, result, 30)
                except:
                    pass
                return result

        # 记录文件
        ssh_intrusion_file = '/www/server/panel/config/ssh_intrusion.json'
        today = datetime.now().strftime('%Y-%m-%d')
        wf = True
        # 读取文件
        try:
            ssh_intrusion_data = json.loads(public.readFile(ssh_intrusion_file))
            if "time" in ssh_intrusion_data and ssh_intrusion_data['time'] == today:
                wf = False
                result['error'] = ssh_intrusion_data["data"]["error"]
                result['success'] = ssh_intrusion_data["data"]["success"]
        except:
            ssh_intrusion_data = {'time': '', 'data': result}

        logs_path_info = self.get_ssh_log_files_list(None)
        time_formatted = time.strftime('%b  %d', time.localtime())
        month, day = time_formatted.split()
        day = day.lstrip('0')

        formatted_time = "{}  {}".format(month, day)
        formatted_time1 = "{} {} ".format(month, day)

        for sfile in logs_path_info:
            if not os.path.exists(sfile):
                continue

            for stype in result.keys():
                try:
                    if stype in ["error", "success"] and ssh_intrusion_data and ssh_intrusion_data["time"] == today\
                            and ssh_intrusion_data["data"][stype] != 0:
                        continue

                    if stype == 'error':
                        cmds = [
                            "cat {} | grep -a 'Failed password for' | grep -v 'invalid' | awk '{{print $5}}'".format(sfile),
                            "cat {} | grep -a 'Connection closed by authenticating user' | grep -a 'preauth' | awk '{{print $5}}'".format(sfile),
                            "cat {} | grep -a 'PAM service(sshd) ignoring max retries' | awk '{{print $5}}'".format(sfile)
                        ]
                    elif stype == 'success':
                        cmds = [
                            "cat {} | grep -a 'Accepted' | awk '{{print $5}}'".format(sfile),
                            "cat {} | grep -a 'sshd\\[.*session opened for user' | awk '{{print $5}}'".format(sfile)
                        ]
                    elif stype == 'today_error' and sfile in ["/var/log/secure", "/var/log/auth.log"]:
                        cmds = [
                            "cat {} | grep -a 'Failed password for' | grep -v 'invalid' | grep -aE '{}|{}' | awk '{{print $5}}'".format(sfile, formatted_time, formatted_time1),
                            "cat {} | grep -a 'Connection closed by authenticating user' | grep -a 'preauth' | grep -aE '{}|{}' | awk '{{print $5}}'".format(sfile, formatted_time, formatted_time1),
                            "cat {} | grep -a 'PAM service(sshd) ignoring max retries' | grep -aE '{}|{}' | awk '{{print $5}}'".format(sfile, formatted_time, formatted_time1)
                        ]
                    elif stype == 'today_success' and sfile in ["/var/log/secure", "/var/log/auth.log"]:
                        cmds = [
                            "cat {} | grep -a 'Accepted' | grep -aE '{}|{}' | awk '{{print $5}}'".format(sfile, formatted_time, formatted_time1),
                            "cat {} | grep -a 'sshd\\[.*session opened for user' | grep -aE '{}|{}' | awk '{{print $5}}'".format(sfile, formatted_time, formatted_time1)
                        ]
                    else:
                        continue

                    log_entries = []
                    for cmd in cmds:
                        output = public.ExecShell(cmd)[0].strip()
                        if output:
                            log_entries.extend(output.split('\n'))

                        # 去重处理
                        if stype in ["success", "today_success"]:
                            count = len(set(log_entries))
                        else:
                            count = len(log_entries)

                        result[stype] += count

                except Exception as e:
                    continue

            result['success'] = result['today_success'] if result['today_success'] >= result['success'] else result['success'] + result['today_success']
            result['error'] = result['today_error'] if result['today_error'] >= result['error'] else result['error'] + result['today_error']
            # 写入到文件中
            if wf:
                ssh_intrusion_data = {'time': today, 'data': result}
                public.writeFile(ssh_intrusion_file, json.dumps(ssh_intrusion_data))

        return result

    def get_ssh_cache(self):
        """
        @获取换成ssh记录
        """
        file = '{}/data/ssh_cache.json'.format(public.get_panel_path())
        cache_data = {'success': {}, 'error': {}, 'today_success': {}, 'today_error': {}}
        if not os.path.exists(file):
            public.writeFile(file, json.dumps(cache_data))
            return cache_data

        try:
            data = json.loads(public.readFile(file))
        except:
            public.writeFile(file, json.dumps(cache_data))
            data = cache_data

        return data

    def set_ssh_cache(self, data):
        """
        @设置ssh缓存
        """
        file = '{}/data/ssh_cache.json'.format(public.get_panel_path())
        public.writeFile(file, json.dumps(data))
        return True

    def GetSshInfo(self, get):
        """
        @获取SSH登录信息

        """
        port = public.get_sshd_port()
        status = public.get_sshd_status()
        isPing = True
        try:
            file = '/etc/sysctl.conf'
            conf = public.readFile(file)
            rep = r"#*net\.ipv4\.icmp_echo_ignore_all\s*=\s*([0-9]+)"
            tmp = re.search(rep, conf).groups(0)[0]
            if tmp == '1': isPing = False
        except:
            isPing = True

        data = {}
        data['port'] = port
        data['status'] = status
        data['status_text'] = '运行中' if status else '已停止'
        data['ping'] = isPing
        data['firewall_status'] = self.CheckFirewallStatus()
        # data['error'] = self.get_ssh_intrusion(get)
        data['fail2ban'] = self._get_ssh_fail2ban()
        ban_job = public.M('crontab').where("name='BT-SSH爆破IP封禁[安全-SSH管理-登录日志中添加]'", ()).count()
        data['ban_cron_job'] =  ban_job > 0
        return data

    def get_ssh_login_info(self, get):
        """
        @获取SSH登录信息
        """
        return self.get_ssh_intrusion(get)

    @staticmethod
    def _get_ssh_fail2ban():
        """
        @name 获取fail2ban的服务和SSH防爆破状态
        @return:
        """
        plugin_path = "/www/server/panel/plugin/fail2ban"
        result_data = {"status": 0, "installed": 1}
        if not os.path.exists("{}".format(plugin_path)):
            result_data['installed'] = 0
            return result_data

        sock = "{}/fail2ban.sock".format(plugin_path)
        if not os.path.exists(sock):
            return result_data

        s_file = '{}/plugin/fail2ban/config.json'.format(public.get_panel_path())
        if os.path.exists(s_file):
            try:
                data = json.loads(public.readFile(s_file))
                if 'sshd' in data:
                    if data['sshd']['act'] == 'true':
                        result_data['status'] = 1
                        return result_data
            except:
                pass

        return result_data

    # 改远程端口
    def SetSshPort(self, get):
        port = get.port
        if int(port) < 22 or int(port) > 65535: return public.returnMsg(False, 'FIREWALL_SSH_PORT_ERR')
        ports = ['21', '25', '80', '443', '8080', '888', '8888']
        if port in ports: return public.returnMsg(False, '请不要使用常用程序的默认端口!')
        file = '/etc/ssh/sshd_config'
        conf = public.readFile(file)

        rep = r"#*Port\s+([0-9]+)\s*\n"
        conf = re.sub(rep, "Port " + port + "\n", conf)
        public.writeFile(file, conf)

        if self.__isFirewalld:
            public.ExecShell('firewall-cmd --permanent --zone=public --add-port=' + port + '/tcp')
            public.ExecShell('setenforce 0')
            public.ExecShell('sed -i "s#SELINUX=enforcing#SELINUX=disabled#" /etc/selinux/config')
            # public.ExecShell("systemctl restart sshd.service")
        elif self.__isUfw:
            public.ExecShell('ufw allow ' + port + '/tcp')
            # public.ExecShell("service ssh restart")
        else:
            public.ExecShell('iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport ' + port + ' -j ACCEPT')
            # public.ExecShell("/etc/init.d/sshd restart")

        public.set_sshd_status(status_act="restart")

        self.FirewallReload()
        public.M('firewall').where("ps=? or ps=? or port=?", ('SSH远程管理服务', 'SSH远程服务', port)).delete()
        public.M('firewall').add('port,ps,addtime', (port, 'SSH远程服务', time.strftime('%Y-%m-%d %X', time.localtime())))
        public.WriteLog("TYPE_FIREWALL", "FIREWALL_SSH_PORT", (port,))
        return public.returnMsg(True, 'EDIT_SUCCESS')

    def SetSshStatus(self, get):
        """
        @设置SSH状态
        """
        get.exists(["status"])
        if int(get['status']) == 1:
            msg = public.getMsg('FIREWALL_SSH_STOP')
            act = 'stop'
        else:
            msg = public.getMsg('FIREWALL_SSH_START')
            act = 'start'

        public.set_sshd_status(status_act=act)

        public.WriteLog("TYPE_FIREWALL", msg)
        return public.returnMsg(True, 'SUCCESS')
