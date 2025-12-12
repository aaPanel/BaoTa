#!/www/server/panel/pyenv/bin/python3
# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: baozi <包子@bt.cn>
# +-------------------------------------------------------------------
# ------------------------------
# 面板后台任务-脚本扩展
#   使用脚本的方式执行BT-Task的部分扩展任务，降低整体资源消耗
# ------------------------------
import json
import sys
import os
import psutil

SETUP_PATH = '/www/server'
PANEL_PATH = '{}/panel'.format(SETUP_PATH)
TASK_LOG_FILE = '{}/logs/task.log'.format(PANEL_PATH)
PY_BIN = os.path.realpath(sys.executable)
os.chdir(PANEL_PATH)
sys.path.insert(0, PANEL_PATH + '/class')
if PANEL_PATH not in sys.path:
    sys.path.insert(0, PANEL_PATH)
import time
from datetime import datetime, timezone, timedelta
import public
import PluginLoader


class Task:
    __api_root_url = 'https://api.bt.cn'
    _check_url = __api_root_url + '/panel/get_soft_list_status'
    __path_error = '{}/data/error.pl'.format(PANEL_PATH)
    __error_html = '{}/BTPanel/templates/default/block_error.html'.format(PANEL_PATH)

    @staticmethod
    def write_log(*args, _level='INFO', color="debug"):
        """
            @name 写入日志
            @author hwliang<2021-08-12>
            @param *args <any> 要写入到日志文件的信息可以是多个，任意类型
            @param _level<string> 日志级别
            @param color<string> 日志颜色，可选值：red,green,yellow,blue,purple,cyan,white,gray,black,info,success,warning,warn,err,error,debug,trace,critical,fatal
            @return void
        """

        color_dict = {
            'red': '\033[31m',
            'green': '\033[32m',
            'yellow': '\033[33m',
            'blue': '\033[34m',
            'purple': '\033[35m',
            'cyan': '\033[36m',
            'white': '\033[37m',
            'gray': '\033[90m',
            'black': '\033[30m',
            'info': '\033[0m',
            'success': '\033[32m',
            'warning': '\033[33m',
            'warn': '\033[33m',
            'err': '\033[31m',
            'error': '\033[31m',
            'debug': '\033[36m',
            'trace': '\033[35m',
            'critical': '\033[31m',
            'fatal': '\033[31m'
        }

        _log = []
        if color:
            color_start = color_dict.get(color.strip().lower(), "")
            if color_start:
                _log.append(color_start)

        _log.append("[{}][{}]".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), _level.upper()))
        for _info in args:
            try:
                if isinstance(_info, (list, tuple)):
                    _log.append(json.dumps(_info, ensure_ascii=False))
                elif isinstance(_info, dict):
                    _log.append(json.dumps(_info, indent=4, ensure_ascii=False))
                else:
                    _log.append(str(_info))
            except:
                _log.append(str(_info))
            _log.append(" ")

        if _log[0].startswith('\033'):
            _log.append('\033[0m')

        public.WriteFile(TASK_LOG_FILE, ''.join(_log) + '\n', mode='a+')

    def check_node_status(self):
        try:
            node_path = '{}/data/node_url.pl'.format(PANEL_PATH)
            if not os.path.exists(node_path):
                return False

            mtime = os.path.getmtime(node_path)
            if time.time() - mtime < 86400:
                return False
            self.write_log("更新节点状态")
            os.system("nohup {} {}/script/reload_check.py auth_day > /dev/null 2>&1 &".format(PY_BIN, PANEL_PATH))
        except:
            pass

    def check502Task(self):
        try:
            self.check_node_status()
            public.auto_backup_panel()
            self.sess_expire()
            self.upload_send_num()
            self.auto_deploy_ssl()
            PluginLoader.daemon_panel()
            self.flush_geoip()
        except:
            PluginLoader.daemon_panel()

    @staticmethod
    def upload_send_num():
        try:
            pl_path = public.get_plugin_path() + '/mail_sys/upload_send_num.pl'
            if not os.path.exists(pl_path):
                return False
            last_time = public.readFile(pl_path)
            if not last_time:
                return False
            if int(time.time()) - int(last_time) < 3600:
                return False

            from mailModel import manageModel
            res = manageModel.main().upload_send_num()
        except:
            pass

    @staticmethod
    def auto_deploy_ssl():
        try:
            from sslModel import autodeployModel
            res = autodeployModel.main().get_task_list()
        except:
            pass

    # 2024/5/21 下午5:32 更新 GeoLite2-Country.json
    @staticmethod
    def flush_geoip():

        '''
            @name 检测如果大小小于3M或大于1个月则更新
            @author wzz <2024/5/21 下午5:33>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        _ips_path = "/www/server/panel/data/firewall/GeoLite2-Country.json"
        m_time_file = "/www/server/panel/data/firewall/geoip_mtime.pl"

        if not os.path.exists(_ips_path):
            os.system("mkdir -p /www/server/panel/data/firewall")
            os.system("touch {}".format(_ips_path))

        try:
            if not os.path.exists(_ips_path):
                public.downloadFile('{}/install/lib/{}'.format(public.get_url(), os.path.basename(_ips_path)),
                                    _ips_path)
                public.writeFile(m_time_file, str(int(time.time())))
                return

            _ips_size = os.path.getsize(_ips_path)
            if os.path.exists(m_time_file):
                _ips_mtime = int(public.readFile(m_time_file))
            else:
                _ips_mtime = 0

            if _ips_size < 3145728 or time.time() - _ips_mtime > 2592000:
                os.system("rm -f {}".format(_ips_path))
                os.system("rm -f {}".format(m_time_file))
                public.downloadFile('{}/install/lib/{}'.format(public.get_url(), os.path.basename(_ips_path)),
                                    _ips_path)
                public.writeFile(m_time_file, str(int(time.time())))

                if os.path.exists(_ips_path):
                    try:
                        import json
                        from xml.etree.ElementTree import ElementTree, Element
                        from safeModel.firewallModel import main as firewall

                        firewallobj = firewall()
                        ips_list = json.loads(public.readFile(_ips_path))
                        if ips_list:
                            for ip_dict in ips_list:
                                if os.path.exists('/usr/bin/apt-get') and not os.path.exists("/etc/redhat-release"):
                                    btsh_path = "/etc/ufw/btsh"
                                    if not os.path.exists(btsh_path):
                                        os.makedirs(btsh_path)
                                    tmp_path = '{}/{}.sh'.format(btsh_path, ip_dict['brief'])
                                    if os.path.exists(tmp_path):
                                        public.writeFile(tmp_path, "")

                                    _string = "#!/bin/bash\n"
                                    for ip in ip_dict['ips']:
                                        if firewallobj.verify_ip(ip):
                                            _string = _string + 'ipset add ' + ip_dict['brief'] + ' ' + ip + '\n'
                                    public.writeFile(tmp_path, _string)
                                else:
                                    xml_path = "/etc/firewalld/ipsets/{}.xml.old".format(ip_dict['brief'])
                                    xml_body = """<?xml version="1.0" encoding="utf-8"?>
<ipset type="hash:net">
<option name="maxelem" value="1000000"/>
</ipset>
"""
                                    if os.path.exists(xml_path):
                                        public.writeFile(xml_path, xml_body)
                                    else:
                                        os.makedirs(os.path.dirname(xml_path), exist_ok=True)
                                        public.writeFile(xml_path, xml_body)

                                    tree = ElementTree()
                                    tree.parse(xml_path)
                                    root = tree.getroot()
                                    for ip in ip_dict['ips']:
                                        if firewallobj.verify_ip(ip):
                                            entry = Element("entry")
                                            entry.text = ip
                                            root.append(entry)

                                    firewallobj.format(root)
                                    tree.write(xml_path, 'utf-8', xml_declaration=True)
                    except:
                        pass
        except:
            try:
                public.downloadFile('{}/install/lib/{}'.format(public.get_url(), os.path.basename(_ips_path)),
                                    _ips_path)
                public.writeFile(m_time_file, str(int(time.time())))
            except:
                pass

    # session过期处理
    def sess_expire(self):
        self.sess_expire_sql()
        try:
            sess_path = os.path.join(PANEL_PATH, 'data/session')
            if not os.path.exists(sess_path):
                return
            s_time = time.time()
            f_list = os.listdir(sess_path)
            f_num = len(f_list)
            sess_out_path = '{}/data/session_timeout.pl'.format(PANEL_PATH)
            session_timeout = 86400
            if os.path.exists(sess_out_path):
                try:
                    session_timeout = int(public.readFile(sess_out_path))
                except:
                    pass
            for fname in f_list:
                filename = os.path.join(sess_path, fname)
                fstat = os.stat(filename)
                f_time = s_time - fstat.st_mtime
                if f_time > session_timeout:
                    os.remove(filename)
                    continue
                if fstat.st_size < 256 and len(fname) == 32:
                    if f_time > 60 or f_num > 30:
                        os.remove(filename)
                        continue
            del f_list
        except Exception as ex:
            self.write_log(str(ex))

    def sess_expire_sql(self):
        try:
            import sqlite3
            self.write_log("启动session过期处理")
            db_file = os.path.join(PANEL_PATH, "data/db/session.db")
            if not os.path.exists(db_file):
                return
            size = os.path.getsize(db_file)
            if size < 1024 * 1024 * 25: # 不足 10M 不用清理
                return
            elif size > 1024 * 1024 * 100: # 大于 100M 删除所有数据
                public.clear_sql_session()
                return
            conn = sqlite3.connect(db_file)
            cur = conn.cursor()
            expiry_time = (datetime.now(tz=timezone.utc)- timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S.%f")
            res = cur.execute("DELETE FROM sessions WHERE expiry < ?", (expiry_time,))
            self.write_log("session过期处理: 删除了{}条数据".format(res.rowcount))
            res = cur.execute("DELETE FROM sessions WHERE  LENGTH(`data`) < ?", (200,))
            self.write_log("session过期处理: 删除了{}条空值数据".format(res.rowcount))
            cur.close()
            conn.commit()
            conn.close()
        except Exception as e:
            self.write_log(str(e))

    def refresh_domain_cache(self):
        '''
            @name 刷新域名缓存
            @return None
        '''
        next_refresh_tip = "{}/data/refresh_domain_cache.pl".format(PANEL_PATH)
        if os.path.exists(next_refresh_tip):
            next_time = int(public.readFile(next_refresh_tip))
            if time.time() < next_time:
                return
        try:
            self.write_log("开始刷新域名缓存")
            from mod.project.domain import domainMod
            domainMod.main().refresh_domain_cache()
            self.write_log("域名缓存刷新完成")
            # 24小时执行一次
            public.writeFile(next_refresh_tip, str(int(time.time()) + 86400))
        except:
            self.write_log("刷新域名缓存失败")
            public.print_log(public.get_error_info())
            public.writeFile(next_refresh_tip, str(int(time.time()) + 3600))

    # 5个小时更新一次更新软件列表
    def update_software_list(self):
        '''
            @name 更新软件列表
            @return void
        '''
        self.write_log("启动软件列表定时更新")
        next_update_tip = "{}/data/update_software_list.pl".format(PANEL_PATH)
        if os.path.exists(next_update_tip):
            next_time = int(public.readFile(next_update_tip))
            if time.time() < next_time:
                return

        try:
            self.get_cloud_list_status()
            public.writeFile(next_update_tip, str(int(time.time()) + 18000))
        except Exception as ex:
            self.write_log(ex)
            public.writeFile(next_update_tip, str(int(time.time()) + 1800))


    # 获取云端帐户状态
    def get_cloud_list_status(self):
        '''
            @name 获取云端软件列表状态
            @return str or bool
        '''
        try:
            pdata = public.get_user_info()
            if not pdata: return False
            if pdata['uid'] == -1: return False
            pdata['mac'] = self.get_mac_address()
            list_body = self.HttpPost(self._check_url, pdata)
            if not list_body: return False

            list_body = json.loads(list_body)
            if not list_body['status']:
                public.writeFile(self.__path_error, "error")
                msg = '''{% extends "layout.html" %}
{% block content %}
<div class="main-content pb55" style="min-height: 525px;">
    <div class="container-fluid">
        <div class="site_table_view bgw mtb15 pd15 text-center">
            <div style="padding:50px">
                <h1 class="h3"></h1>
                '''
                msg += list_body['title'] + list_body['body']
                msg += '''
            </div>
        </div>
    </div>
</div>
{% endblock %}
{% block scripts %}
{% endblock %}'''
                public.writeFile(self.__error_html, msg)
                return '3'
            else:
                if os.path.exists(self.__path_error):
                    os.remove(self.__path_error)
                if os.path.exists(self.__error_html):
                    os.remove(self.__error_html)
                return '2'
        except Exception as ex:
            self.write_log(ex)
            if os.path.exists(self.__path_error): os.remove(self.__path_error)
            if os.path.exists(self.__error_html): os.remove(self.__error_html)
            return '1'

    @staticmethod
    def get_mac_address():
        '''
            @name 获取MAC地址
            @return string
        '''
        import uuid
        mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
        return ":".join([mac[e:e + 2] for e in range(0, 11, 2)])

    def HttpPost(self, url, data, timeout=6, UserAgent='BT-Panel'):
        try:
            pdata = ""
            if type(data) == dict:
                for key in data:
                    pdata += "{}={}&".format(key, data[key])
                pdata = pdata.strip('&')
            else:
                pdata = data
            curl_cmd = "curl -sS --connect-timeout {} --max-time {} --user-agent '{}' -d '{}' '{}'".format(timeout, timeout, UserAgent, pdata, url)

            result = public.ExecShell(curl_cmd)
            if result[1]:
                self.write_log("httpPost:", result[1])
            return result[0]
        except Exception as ex:
            self.write_log("URL: {}  => {}".format(url, ex))
            return str(ex)

    def maillog_event_service(self):
        # 判断是否已安装企业版邮局
        from mailModel import manageModel
        install_data = manageModel.main().install_status(None)
        if not install_data:
            print("未安装企业版邮局，邮件日志事件服务退出")
            return None
        if not install_data['status']:
            print("未安装企业版邮局，邮件日志事件服务退出")
            return None

        mail_log_event_pid = "{}/data/mail_log_event.pid"
        pid = self.get_mail_log_event_pid()
        if pid:
            try:
                p = psutil.Process(pid)
                # 运行7天后重启一次该服务
                if p.create_time() > (time.time() - 7* 24 * 60 * 60):
                    print("邮件日志事件服务已启动")
                    return pid
                else:
                    p.kill()
            except:
                pass

        public.writeFile(mail_log_event_pid, str(os.getpid()))
        from mailModel.power_mta.maillog_stat import maillog_event
        maillog_event()

    @staticmethod
    def get_mail_log_event_pid():
        mail_log_event_pid = "{}/data/mail_log_event.pid"
        if os.path.exists(mail_log_event_pid):
            try:
                pid = int(public.readFile(mail_log_event_pid))
                if psutil.pid_exists(pid):
                    return pid
            except:
                pass
        self_filename = os.path.basename(__file__)
        for pid in psutil.pids():
            if pid == os.getpid():
                continue
            try:
                p = psutil.Process(pid)
                cmdline = p.cmdline()
                is_python_proc = any(x for x in cmdline if x.find("python") > -1)
                is_self_filename = any(x for x in cmdline if x.find(self_filename) > -1)
                if len(cmdline) > 2:
                    is_args = cmdline[2] == 'maillog_event'
                else:
                    is_args = False
                if is_python_proc and is_self_filename and is_args:
                    return pid
            except:
                continue


def main(action: str):
    if action == "check502Task":
        Task().check502Task()
    elif action == "refresh_domain_cache":
        Task().refresh_domain_cache()
    elif action == "update_software_list":
        Task().update_software_list()
    elif action == "maillog_event":
        Task().maillog_event_service()
    else:
        print("Unknown action: {}".format(action))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 task_script_extension.py <action>")
        exit(1)
    main(sys.argv[1])