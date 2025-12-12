#!/www/server/panel/pyenv/bin/python3
# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------
# ------------------------------
# 面板后台任务
# ------------------------------
import heapq
import sys
import os
import psutil
import json
import time
import shutil
import hashlib
import sqlite3
import threading
import traceback
import subprocess
import pickle
from multiprocessing import Process
from datetime import datetime, timezone, timedelta
from collections import namedtuple
from typing import Optional, Dict, List, Any, Tuple

os.environ['BT_TASK'] = '1'
SETUP_PATH = '/www/server'
PANEL_PATH = '{}/panel'.format(SETUP_PATH)
PY_BIN = os.path.realpath(sys.executable)
TASK_LOG_FILE = '{}/logs/task.log'.format(PANEL_PATH)
EXEC_LOG_PATH = '/tmp/panelExec.log'


def write_file(path: str, content: str, mode='w'):
    try:
        fp = open(path, mode)
        fp.write(content)
        fp.close()
        return True
    except:
        try:
            fp = open(path, mode, encoding="utf-8")
            fp.write(content)
            fp.close()
            return True
        except:
            return False


def read_file(filename: str):
    fp = None
    try:
        fp = open(filename, "rb")
        f_body_bytes: bytes = fp.read()
        f_body = f_body_bytes.decode("utf-8", errors='ignore')
        fp.close()
        return f_body
    except Exception as ex:
        return False
    finally:
        if fp and not fp.closed:
            fp.close()


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

    write_file(TASK_LOG_FILE, ''.join(_log) + '\n', mode='a+')


def exec_shell(cmd_string, cwd=None, shell=True):
    """
        @name 执行shell命令
        @param cmdstring: str  要执行的shell命令
        @param cwd: str  执行命令的路径
        return int  返回命令执行结果
    """
    try:
        real_cmd = "{} > {} 2>&1".format(cmd_string, EXEC_LOG_PATH)
        sub = subprocess.Popen(real_cmd, cwd=cwd,stdin=subprocess.PIPE, shell=shell, bufsize=4096)
        while sub.poll() is None:
            time.sleep(0.1)

        return sub.returncode
    except:
        return None


# sys.path.insert(0, PANEL_PATH + '/class')
# import public
# import db
# import panelTask
# import process_task
# import PluginLoader
#
#
# class Task:
#     task_obj = None
#     pre = 0
#     timeout_count = 0
#     log_path = '/tmp/panelExec.log'
#     is_task = '/tmp/panelTask.pl'
#     __api_root_url = 'https://api.bt.cn'
#     _check_url = __api_root_url + '/panel/get_soft_list_status'
#     end_time = None
#     is_check = 0
#     python_bin = None
#     thread_dict = {}
#     setup_path = None
#     panel_path = None
#     old_edate = None
#     log_file = None
#     __path_error = None
#     __error_html = None
#
#     # 系统监控相关属性
#     diskio_1 = None
#     diskio_2 = None
#     networkInfo = None
#     cpuInfo = None
#     diskInfo = None
#     network_up = {}
#     network_down = {}
#     cycle = 60
#     last_delete_time = 0
#     # 实例化进程监控对象
#     proc_task_obj = None
#
#     def __init__(self) -> None:
#         if not self.task_obj: self.task_obj = panelTask.bt_task()
#         if not self.python_bin: self.python_bin = public.get_python_bin()
#         if not self.setup_path: self.setup_path = public.get_setup_path()
#         if not self.panel_path: self.panel_path = public.get_panel_path()
#         if not self.log_file: self.log_file = self.panel_path + '/logs/task.log'
#         if not self.__path_error: self.__path_error = self.panel_path + '/data/error_pl.pl'
#         if not self.__error_html: self.__error_html = self.panel_path + '/BTPanel/templates/default/block_error.html'
#         if not self.proc_task_obj: self.proc_task_obj = process_task.process_task()
#
#     def write_log(self, *args, _level='INFO', color="debug"):
#         '''
#             @name 写入日志
#             @author hwliang<2021-08-12>
#             @param *args <any> 要写入到日志文件的信息可以是多个，任意类型
#             @param _level<string> 日志级别
#             @param color<string> 日志颜色，可选值：red,green,yellow,blue,purple,cyan,white,gray,black,info,success,warning,warn,err,error,debug,trace,critical,fatal
#             @return void
#         '''
#
#         color_start = ''
#         color_end = ''
#         color_dict = {
#             'red': '\033[31m',
#             'green': '\033[32m',
#             'yellow': '\033[33m',
#             'blue': '\033[34m',
#             'purple': '\033[35m',
#             'cyan': '\033[36m',
#             'white': '\033[37m',
#             'gray': '\033[90m',
#             'black': '\033[30m',
#             'info': '\033[0m',
#             'success': '\033[32m',
#             'warning': '\033[33m',
#             'warn': '\033[33m',
#             'err': '\033[31m',
#             'error': '\033[31m',
#             'debug': '\033[36m',
#             'trace': '\033[35m',
#             'critical': '\033[31m',
#             'fatal': '\033[31m'
#         }
#         if color:
#             color = color.strip().lower()
#             if color in color_dict:
#                 color_start = color_dict[color]
#                 color_end = '\033[0m'
#
#         log_body = "{}[{}][{}]".format(color_start, public.format_date(), _level.upper())
#         for _info in args:
#             try:
#                 if type(_info) == dict:
#                     _info = json.dumps(_info, indent=4, ensure_ascii=False)
#                 elif type(_info) == list:
#                     _info = json.dumps(_info, ensure_ascii=False)
#                 elif type(_info) == tuple:
#                     _info = json.dumps(_info, ensure_ascii=False)
#             except:
#                 _info = str(_info)
#
#             log_body += " {}".format(_info)
#
#         log_body += "{}\n".format(color_end)
#         # print(log_body.strip())
#         public.WriteFile(self.log_file, log_body, 'a+')
#
#     def exec_shell(self, cmdstring, cwd=None, timeout=None, shell=True):
#         '''
#             @name 执行shell命令
#             @param cmdstring: str  要执行的shell命令
#             @param cwd: str  执行命令的路径
#             @param timeout: int  超时时间
#             @param shell: bool  是否使用shell
#             return int  返回命令执行结果
#         '''
#         try:
#             import subprocess
#             import time
#             sub = subprocess.Popen(cmdstring + ' > ' + self.log_path + ' 2>&1', cwd=cwd,
#                                    stdin=subprocess.PIPE, shell=shell, bufsize=4096)
#
#             while sub.poll() is None:
#                 time.sleep(0.1)
#
#             return sub.returncode
#         except:
#             return None
#
#     def get_soft_name_of_version(self, name):
#         '''
#             @name 获取软件名称和版本
#             @param name<string> 软件名称
#             @return tuple(string, string) 返回软件名称和版本
#         '''
#         if name.find('Docker') != -1:
#             return ('docker', '1.0')
#         return_default = ('', '')
#         arr1 = name.split('[')
#         if len(arr1) < 2:
#             return return_default
#         arr2 = arr1[1].split(']')
#         if len(arr2) < 2:
#             return return_default
#         arr3 = arr2[0].split('-')
#         if len(arr3) < 2:
#             return return_default
#
#         soft_name = arr3[0]
#         soft_version = arr3[1]
#         if soft_name == 'php':
#             soft_version = soft_version.replace('.', '')
#         return (soft_name, soft_version)
#
#     def check_install_status(self, name):
#         '''
#             @name 检查软件是否安装成功
#             @param name<string> 软件名称
#             @return tuple(bool, string) 返回是否安装成功和安装信息
#         '''
#         return_default = (1, '安装成功')
#         try:
#             # 获取软件名称和版本
#             soft_name, soft_version = self.get_soft_name_of_version(name)
#             if not soft_name or not soft_version:
#                 return return_default
#
#             # 获取安装检查配置
#             install_config = public.read_config('install_check')
#             if not install_config:
#                 return return_default
#
#             if soft_name not in install_config:
#                 return return_default
#
#             if os.path.exists("/www/server/panel/install/{}_not_support.pl".format(soft_name)):
#                 return (0, '不兼容此系统！请点详情说明！')
#
#             if os.path.exists("/www/server/panel/install/{}_mem_kill.pl".format(soft_name)):
#                 return (0, '内存不足安装异常！请点详情说明！')
#
#             soft_config = install_config[soft_name]
#
#             def replace_all(data):
#                 '''
#                     @name 替换所有变量
#                     @param data<string> 需要替换的字符串
#                     @return string 替换后的字符串
#                 '''
#                 if not data:
#                     return data
#                 if data.find('{') == -1:
#                     return data
#                 # 替换安装路径
#                 data = data.replace('{SetupPath}', self.setup_path)
#                 # 替换版本号
#                 data = data.replace('{Version}', soft_version)
#                 # 替换主机名
#                 if data.find("{Host") != -1:
#                     host_name = public.get_hostname()
#                     host = host_name.split('.')[0]
#                     data = data.replace("{Hostname}", host_name)
#                     data = data.replace("{Host}", host)
#                 return data
#
#             # 检查文件是否存在
#             if 'files_exists' in soft_config:
#                 for fname in soft_config['files_exists']:
#                     filename = replace_all(fname)
#                     if not os.path.exists(filename):
#                         return (0, '安装失败,文件不存在:{}'.format(filename))
#
#             # 检查pid文件是否有效
#             if 'pid' in soft_config and soft_config['pid']:
#                 pid_file = replace_all(soft_config['pid'])
#                 if not os.path.exists(pid_file):
#                     return (0, '启动失败,pid文件不存在:{}'.format(pid_file))
#                 pid = public.readFile(pid_file)
#                 if not pid:
#                     return (0, '启动失败,pid文件为空:{}'.format(pid_file))
#                 proc_file = '/proc/{}/cmdline'.format(pid.strip())
#                 if not os.path.exists(proc_file):
#                     return (0, '启动失败,指定PID: {}({}) 进程不存在'.format(pid_file, pid))
#
#             # 执行命令检查
#             if 'cmd' in soft_config:
#                 for cmd in soft_config['cmd']:
#                     res = '\n'.join(public.ExecShell(replace_all(cmd['exec'])))
#                     if res.find(replace_all(cmd['success'])) == -1:
#                         return (0, '{}服务启动状态异常'.format(soft_name))
#         except:
#             pass
#
#         return return_default
#
#     def task_table_rep(self):
#         '''
#             @name 修复任务表
#             @param None
#         '''
#         task_obj = public.M('tasks')
#         res = task_obj.query("SELECT count(*) FROM sqlite_master where type='table' and name='tasks' and sql like '%msg%'")
#         if res and res[0][0] == 0:
#             task_obj.execute("ALTER TABLE tasks ADD COLUMN msg TEXT DEFAULT '安装成功'", ())
#         res = task_obj.query("SELECT count(*) FROM sqlite_master where type='table' and name='tasks' and sql like '%install_status%'")
#         if res and res[0][0] == 0:
#             task_obj.execute("ALTER TABLE tasks ADD COLUMN install_status INTEGER DEFAULT 1", ())
#         task_obj.close()
#
#     def save_installed_msg(self, task_id):
#         '''
#             @name 保存安装脚本执行日志
#             @param task_id<int> 任务ID
#             @return None
#         '''
#         try:
#             from panel_msg.msg_file import message_mgr
#
#             msg = message_mgr.get_by_task_id(task_id)
#             if msg is None:
#                 return None
#             else:
#                 msg.title = "正在" + msg.title[2:]
#                 msg.sub["file_name"] = "/tmp/panelExec.log"
#                 msg.sub["install_status"] = "正在" + msg.sub["install_status"][2:]
#                 msg.sub["status"] = 1
#                 msg.read = False
#                 msg.read_time = 0
#
#                 res = msg.save_to_file()
#                 return msg
#         except:
#             return public.get_error_info()
#
#     def update_installed_msg(self, msg):
#         '''
#             @name 更新安装脚本执行日志
#             @param msg<Message> 消息对象
#             @return None
#         '''
#         try:
#             import shutil
#             logs_dir = public.get_panel_path() + "/logs/installed"
#             if not os.path.exists(logs_dir):
#                 os.makedirs(logs_dir, 0o600)
#
#             filename = logs_dir + "/{}_{}.log".format(msg.sub["soft_name"], int(time.time()))
#             if os.path.exists(self.log_path):
#                 shutil.copyfile(self.log_path, filename)
#                 msg.sub["file_name"] = filename
#                 msg.sub["install_status"] = msg.sub["install_status"][2:] + "结束"
#                 msg.sub["status"] = 2
#                 msg.read = False
#                 msg.title = msg.title[2:] + "已结束"
#                 msg.read_time = 0
#
#             msg.save_to_file()
#         except:
#             public.writeFile("{}/logs/task.error".format(self.panel_path), public.get_error_info())
#
#     def task_end(self, value):
#         '''
#             @name 任务结束处理
#             @param value<dict> 任务信息
#             @return None
#         '''
#         # 安装PHP后需要重新加载PHP环境
#         if value['execstr'].find('install php') != -1:
#             os.system("{} {}/tools.py phpenv".format(self.python_bin, self.panel_path))
#         elif value['execstr'].find('install nginx') != -1:
#             # 修复nginx配置文件到支持当前安装的nginx版本
#             os.system("{} {}/script/nginx_conf_rep.py".format(self.python_bin, self.panel_path))
#
#     # 任务队列
#     def startTask(self):
#         '''
#             @name 开始任务队列
#             @param None
#         '''
#         tip_file = '/dev/shm/.panelTask.pl'
#         self.task_table_rep()
#         n = 0
#         tasks_obj = None
#         while 1:
#             try:
#                 if os.path.exists(self.is_task):
#                     tasks_obj = public.M('tasks')
#                     # 重置所有任务状态
#                     tasks_obj.where("status=?", ('-1',)).setField('status', '0')
#
#                     # 获取所有未执行的任务
#                     taskArr = tasks_obj.where("status=?", ('0',)).field('id,name,type,execstr').order("id asc").select()
#
#                     # 逐个执行任务
#                     for value in taskArr:
#
#                         # 检查关键目录是否可写
#                         public.check_sys_write()
#
#                         # 检查任务类型是否为shell执行
#                         if value['type'] != 'execshell': continue
#
#                         # 检查任务是否存在
#                         if not tasks_obj.where("id=?", (value['id'],)).count():
#                             public.writeFile(tip_file, str(int(time.time())))
#                             continue
#
#                         # 写入状态和任务开始时间
#                         start = int(time.time())
#                         tasks_obj.where("id=?", (value['id'],)).save('status,start', ('-1', start))
#
#                         # 保存安装日志
#                         msg = self.save_installed_msg(value["id"])
#
#                         # 执行任务
#                         self.write_log("正在执行任务: {}".format(value['name']))
#
#                         self.exec_shell(value['execstr'])
#
#                         # 处理任务结束事件
#                         self.task_end(value)
#
#                         # 检查软件是否安装成功
#                         end = int(time.time())
#                         install_status, install_msg = self.check_install_status(value['name'])
#
#                         self.write_log("任务执行结果: {},".format(install_msg), "耗时: {}秒".format(end - start))
#
#                         # 写入任务结束状态到数据库
#                         status_code = 1
#
#                         tasks_obj.where("id=?", (value['id'],)).save('status,end,msg,install_status', (status_code, end, install_msg, install_status))
#
#                         # 更新安装日志
#                         self.update_installed_msg(msg)
#
#                         # 移除任务标记文件
#                         if (tasks_obj.where("status=?", ('0')).count() < 1):
#                             if os.path.exists(self.is_task):
#                                 os.remove(self.is_task)
#
#                         # 重置系统加固状态
#                         public.start_syssafe()
#
#                 # 写入任务循环标记
#                 public.writeFile(tip_file, str(int(time.time())))
#
#                 # 线程检查
#                 n += 1
#                 if n > 60:
#                     self.run_thread()
#                     n = 0
#             except:
#                 pass
#             finally:
#                 if tasks_obj:
#                     tasks_obj.close()
#                     tasks_obj = None
#
#             time.sleep(2)
#
#     # 定时任务去检测邮件信息
#     def send_mail_time(self):
#         self.write_log("启动邮件发送定时任务")
#         time.sleep(60)
#         while True:
#             try:
#                 os.system("nohup {} {}/script/mail_task.py > /dev/null 2>&1 &".format(self.python_bin, self.panel_path))
#                 time.sleep(59)
#             except:
#                 time.sleep(59)
#                 self.send_mail_time()
#
#     def get_mac_address(self):
#         '''
#             @name 获取MAC地址
#             @return string
#         '''
#         import uuid
#         mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
#         return ":".join([mac[e:e + 2] for e in range(0, 11, 2)])
#
#     def get_user_info(self):
#         user_file = '{}/data/userInfo.json'.format(self.panel_path)
#         if not os.path.exists(user_file): return {}
#         userInfo = {}
#         try:
#             userTmp = json.loads(public.readFile(user_file))
#             if not 'serverid' in userTmp or len(userTmp['serverid']) != 64:
#                 return userInfo
#             userInfo['uid'] = userTmp['uid']
#             userInfo['address'] = userTmp['address']
#             userInfo['access_key'] = userTmp['access_key']
#             userInfo['username'] = userTmp['username']
#             userInfo['serverid'] = userTmp['serverid']
#             userInfo['oem'] = public.get_oem_name()
#             userInfo['o'] = userInfo['oem']
#             userInfo['mac'] = self.get_mac_address()
#         except:
#             pass
#         return userInfo
#
#     # 获取云端帐户状态
#     def get_cloud_list_status(self):
#         '''
#             @name 获取云端软件列表状态
#             @return str or bool
#         '''
#         try:
#             pdata = public.get_user_info()
#             if not pdata: return False
#             if pdata['uid'] == -1: return False
#             pdata['mac'] = self.get_mac_address()
#             list_body = self.HttpPost(self._check_url, pdata)
#             if not list_body: return False
#
#             list_body = json.loads(list_body)
#             if not list_body['status']:
#                 public.writeFile(self.__path_error, "error")
#                 msg = '''{% extends "layout.html" %}
# {% block content %}
# <div class="main-content pb55" style="min-height: 525px;">
#     <div class="container-fluid">
#         <div class="site_table_view bgw mtb15 pd15 text-center">
#             <div style="padding:50px">
#                 <h1 class="h3"></h1>
#                 '''
#                 msg += list_body['title'] + list_body['body']
#                 msg += '''
#             </div>
#         </div>
#     </div>
# </div>
# {% endblock %}
# {% block scripts %}
# {% endblock %}'''
#                 public.writeFile(self.__error_html, msg)
#                 return '3'
#             else:
#                 if os.path.exists(self.__path_error):
#                     os.remove(self.__path_error)
#                 if os.path.exists(self.__error_html):
#                     os.remove(self.__error_html)
#                 return '2'
#         except Exception as ex:
#             self.write_log(ex)
#             if os.path.exists(self.__path_error): os.remove(self.__path_error)
#             if os.path.exists(self.__error_html): os.remove(self.__error_html)
#             return '1'
#
#     # 5个小时更新一次更新软件列表
#     def update_software_list(self):
#         '''
#             @name 更新软件列表
#             @return void
#         '''
#         self.write_log("启动软件列表定时更新")
#         time.sleep(120)
#         while True:
#             try:
#                 self.get_cloud_list_status()
#                 time.sleep(18000)
#             except Exception as ex:
#                 self.write_log(ex)
#                 time.sleep(1800)
#                 self.update_software_list()
#
#     # 面板消息提醒
#     def check_panel_msg(self):
#         '''
#             @name 面板消息提醒
#             @return None
#         '''
#         self.write_log("启动面板消息提醒")
#         time.sleep(120)
#         while True:
#             #统计ssh的错误次数
#             PluginLoader.module_run("syslog", "task_ssh_error_count", public.dict_obj())
#             os.system('nohup {} {}/script/check_msg.py > /dev/null 2>&1 &'.format(self.python_bin, self.panel_path))
#             time.sleep(3000)
#
#     # 面板推送消息
#     def push_msg(self):
#         '''
#             @name 面板推送消息
#             @return None
#         '''
#         self.write_log("启动面板推送消息")
#         time.sleep(120)
#         while True:
#             time.sleep(60)
#             os.system('nohup {} {}/script/push_msg.py > /dev/null 2>&1 &'.format(self.python_bin, self.panel_path))
#
#
#     def total_load_msg(self):
#         '''
#             @name 面板负载均衡统计任务
#             @return None
#         '''
#         self.write_log("面板负载均衡统计任务")
#         time.sleep(120)
#         while True:
#             time.sleep(60*5)
#             os.system('nohup {} {}/script/total_load_msg.py > /dev/null 2>&1 &'.format(self.python_bin, self.panel_path))
#
#     def node_monitor(self):
#         self.write_log("启动 <节点监控任务>")
#         time.sleep(10)
#         while  True:
#             time.sleep(120)
#             os.system('nohup {} {}/script/node_monitor.py > /dev/null 2>&1 &'.format(self.python_bin, self.panel_path))
#
#     def ProLog(self):
#         '''
#             @name 项目日志清理
#             @return None
#         '''
#         path_list = ["{}/go_project/vhost/logs".format(self.setup_path), "/var/tmp/springboot/vhost/logs/"]
#         try:
#             for i2 in path_list:
#                 if os.path.exists(i2):
#                     for dir in os.listdir(i2):
#                         dir = os.path.join(i2, dir)
#                         # 判断当前目录是否为文件夹
#                         if os.path.isfile(dir):
#                             if dir.endswith(".log"):
#                                 # 文件大于500M的时候则清空文件
#                                 if os.stat(dir).st_size > 200000000:
#                                     public.ExecShell("echo ''>{}".format(dir))
#         except:
#             pass
#
#     def ProDadmons(self):
#         '''
#             @name 项目守护进程
#             @author
#         '''
#         n = 30
#         self.write_log("启动项目守护进程")
#         while 1:
#             n += 1
#             if n >= 30:
#                 n = 1
#                 self.ProLog()
#             self.wait_daemon_time()
#             os.system("nohup {} {}/script/project_daemon.py > /dev/null 2>&1 &".format(self.python_bin, self.panel_path))
#
#     def wait_daemon_time(self):
#         '''
#             @name 等待守护进程时间
#             @return None
#         '''
#         last_time_out = self.get_daemon_time()
#         use_time = 0
#         while use_time < last_time_out:
#             time.sleep(5)
#             use_time += 5
#             new_time_out = self.get_daemon_time()
#             if new_time_out != last_time_out:
#                 if use_time > new_time_out:
#                     break
#                 else:
#                     last_time_out = new_time_out
#
#     def get_daemon_time(self):
#         '''
#             @name 获取守护进程时间
#             @return int
#         '''
#         daemon_time_file = os.path.join(self.panel_path, 'data/daemon_time.pl')
#         if os.path.exists(daemon_time_file):
#             time_out = int(public.readFile(daemon_time_file))
#             if time_out < 10:
#                 time_out = 10
#             if time_out > 30 * 60:
#                 time_out = 30 * 60
#         else:
#             time_out = 120
#         return time_out
#
#     def process_task_thread(self):
#         '''
#             @name 进程监控
#             @auther hwliang
#         '''
#         time.sleep(60)
#         # 进程流量监控，如果文件：/www/server/panel/data/is_net_task.pl 或 /www/server/panel/data/control.conf不存在，则不监控进程流量
#         is_net_task = self.panel_path + '/data/is_net_task.pl'
#         control_file = self.panel_path + '/data/control.conf'
#         if not os.path.exists(is_net_task) or not os.path.exists(control_file):
#             return
#         self.write_log("启动进程流量监控")
#         net_task_obj = process_task.process_network_total()
#         net_task_obj.start()
#
#     def check_database_quota(self):
#         '''
#             @name 数据库配额检查
#             @return None
#         '''
#         get = public.dict_obj()
#         get.model_index = "project"
#         self.write_log("启动数据库配额检查")
#         while True:
#             num = PluginLoader.module_run("quota", "database_quota_check", get)
#             if num == 0:
#                 break
#             time.sleep(60)
#
#     # 取内存使用率
#     def GetMemUsed(self):
#         '''
#             @name 获取内存使用率
#             @return float
#         '''
#         try:
#             mem = psutil.virtual_memory()
#             memInfo = {'memTotal': mem.total / 1024 / 1024, 'memFree': mem.free / 1024 / 1024,
#                        'memBuffers': mem.buffers / 1024 / 1024, 'memCached': mem.cached / 1024 / 1024}
#             tmp = memInfo['memTotal'] - memInfo['memFree'] - \
#                   memInfo['memBuffers'] - memInfo['memCached']
#             tmp1 = memInfo['memTotal'] / 100
#             return (tmp / tmp1)
#         except:
#             return 1
#
#     # 检查502错误
#     def check502(self):
#         '''
#             @name 检查PHP导致的502错误
#             @return None
#         '''
#         try:
#             phpversions = public.get_php_versions()
#             for version in phpversions:
#                 if version in ['52', '5.2']: continue
#                 php_path = self.setup_path + '/php/' + version + '/sbin/php-fpm'
#                 if not os.path.exists(php_path):
#                     continue
#                 if self.checkPHPVersion(version):
#                     continue
#                 if self.startPHPVersion(version):
#                     public.WriteLog('PHP守护程序', '检测到PHP-' + version + '处理异常,已自动修复!', not_web=True)
#                     self.write_log('PHP守护程序', '检测到PHP-' + version + '处理异常,已自动修复!', 'ERROR', 'red')
#         except Exception as ex:
#             self.write_log(ex)
#
#     # 处理指定PHP版本
#     def startPHPVersion(self, version):
#         '''
#             @name 修复指定PHP版本服务状态
#             @param version<string> PHP版本
#             @return bool
#         '''
#         try:
#             fpm = '/etc/init.d/php-fpm-' + version
#             php_path = self.setup_path + '/php/' + version + '/sbin/php-fpm'
#             if not os.path.exists(php_path):
#                 if os.path.exists(fpm):
#                     os.remove(fpm)
#                 return False
#
#             # 尝试重载服务
#             os.system(fpm + ' start')
#             os.system(fpm + ' reload')
#             if self.checkPHPVersion(version):
#                 return True
#
#             # 尝试重启服务
#             cgi = '/tmp/php-cgi-' + version + '.sock'
#             pid = self.setup_path + '/php/' + version + '/var/run/php-fpm.pid'
#             os.system('pkill -9 php-fpm-' + version)
#             time.sleep(0.5)
#             if os.path.exists(cgi):
#                 os.remove(cgi)
#             if os.path.exists(pid):
#                 os.remove(pid)
#             os.system(fpm + ' start')
#             if self.checkPHPVersion(version):
#                 return True
#             # 检查是否正确启动
#             if os.path.exists(cgi):
#                 return True
#             return False
#         except Exception as ex:
#             self.write_log(ex)
#             return True
#
#     # 检查指定PHP版本
#     def checkPHPVersion(self, version):
#         '''
#             @name 检查指定PHP版本服务状态
#             @param version<string> PHP版本
#             @return bool
#         '''
#         try:
#             cgi_file = '/tmp/php-cgi-{}.sock'.format(version)
#             if os.path.exists(cgi_file):
#                 init_file = '/etc/init.d/php-fpm-{}'.format(version)
#                 if os.path.exists(init_file):
#                     init_body = public.ReadFile(init_file)
#                     if not init_body: return True
#                 uri = "http://127.0.0.1/phpfpm_" + version + "_status?json"
#                 result = self.HttpGet(uri)
#                 json.loads(result)
#             return True
#         except:
#             self.write_log("检测到PHP-{}无法访问".format(version))
#             return False
#
#     """
#     @name 检查当前节点是否可用
#     """
#
#     def check_node_status(self):
#         try:
#             node_path = '{}/data/node_url.pl'.format(self.panel_path)
#             if not os.path.exists(node_path):
#                 return False
#
#             mtime = os.path.getmtime(node_path)
#             if time.time() - mtime < 86400:
#                 return False
#             self.write_log("更新节点状态")
#             os.system("nohup {} {}/script/reload_check.py auth_day > /dev/null 2>&1 &".format(self.python_bin, self.panel_path))
#         except:
#             pass
#
#     # 2024/5/21 下午5:32 更新 GeoLite2-Country.json
#     def flush_geoip(self):
#
#         '''
#             @name 检测如果大小小于3M或大于1个月则更新
#             @author wzz <2024/5/21 下午5:33>
#             @param "data":{"参数名":""} <数据类型> 参数描述
#             @return dict{"status":True/False,"msg":"提示信息"}
#         '''
#         _ips_path = "/www/server/panel/data/firewall/GeoLite2-Country.json"
#         m_time_file = "/www/server/panel/data/firewall/geoip_mtime.pl"
#
#         if not os.path.exists(_ips_path):
#             os.system("mkdir -p /www/server/panel/data/firewall")
#             os.system("touch {}".format(_ips_path))
#
#         try:
#             if not os.path.exists(_ips_path):
#                 public.downloadFile('{}/install/lib/{}'.format(public.get_url(), os.path.basename(_ips_path)), _ips_path)
#                 public.writeFile(m_time_file, str(int(time.time())))
#                 return
#
#             _ips_size = os.path.getsize(_ips_path)
#             if os.path.exists(m_time_file):
#                 _ips_mtime = int(public.readFile(m_time_file))
#             else:
#                 _ips_mtime = 0
#
#             if _ips_size < 3145728 or time.time() - _ips_mtime > 2592000:
#                 os.system("rm -f {}".format(_ips_path))
#                 os.system("rm -f {}".format(m_time_file))
#                 public.downloadFile('{}/install/lib/{}'.format(public.get_url(), os.path.basename(_ips_path)), _ips_path)
#                 public.writeFile(m_time_file, str(int(time.time())))
#
#                 if os.path.exists(_ips_path):
#                     try:
#                         import json
#                         from xml.etree.ElementTree import ElementTree, Element
#                         from safeModel.firewallModel import main as firewall
#
#                         firewallobj = firewall()
#                         ips_list = json.loads(public.readFile(_ips_path))
#                         if ips_list:
#                             for ip_dict in ips_list:
#                                 if os.path.exists('/usr/bin/apt-get') and not os.path.exists("/etc/redhat-release"):
#                                     btsh_path = "/etc/ufw/btsh"
#                                     if not os.path.exists(btsh_path):
#                                         os.makedirs(btsh_path)
#                                     tmp_path = '{}/{}.sh'.format(btsh_path, ip_dict['brief'])
#                                     if os.path.exists(tmp_path):
#                                         public.writeFile(tmp_path, "")
#
#                                     _string = "#!/bin/bash\n"
#                                     for ip in ip_dict['ips']:
#                                         if firewallobj.verify_ip(ip):
#                                             _string = _string + 'ipset add ' + ip_dict['brief'] + ' ' + ip + '\n'
#                                     public.writeFile(tmp_path, _string)
#                                 else:
#                                     xml_path = "/etc/firewalld/ipsets/{}.xml.old".format(ip_dict['brief'])
#                                     xml_body = """<?xml version="1.0" encoding="utf-8"?>
# <ipset type="hash:net">
#   <option name="maxelem" value="1000000"/>
# </ipset>
# """
#                                     if os.path.exists(xml_path):
#                                         public.writeFile(xml_path, xml_body)
#                                     else:
#                                         os.makedirs(os.path.dirname(xml_path), exist_ok=True)
#                                         public.writeFile(xml_path, xml_body)
#
#                                     tree = ElementTree()
#                                     tree.parse(xml_path)
#                                     root = tree.getroot()
#                                     for ip in ip_dict['ips']:
#                                         if firewallobj.verify_ip(ip):
#                                             entry = Element("entry")
#                                             entry.text = ip
#                                             root.append(entry)
#
#                                     firewallobj.format(root)
#                                     tree.write(xml_path, 'utf-8', xml_declaration=True)
#                     except:
#                         pass
#         except:
#             try:
#                 public.downloadFile('{}/install/lib/{}'.format(public.get_url(), os.path.basename(_ips_path)), _ips_path)
#                 public.writeFile(m_time_file, str(int(time.time())))
#             except:
#                 pass
#
#     # 2024/3/20 上午 11:09 更新docker_hub镜像排行数据
#     def flush_docker_hub_repos(self):
#         '''
#             @name 更新docker_hub镜像排行数据
#             @author wzz <2024/3/20 上午 11:09>
#             @param "data":{"参数名":""} <数据类型> 参数描述
#             @return dict{"status":True/False,"msg":"提示信息"}
#         '''
#         public.ExecShell("/www/server/panel/pyenv/bin/python3.7 /www/server/panel/class/btdockerModel/script/syncreposdb.py")
#
#     def upload_send_num(self):
#         try:
#             pl_path = public.get_plugin_path() + '/mail_sys/upload_send_num.pl'
#             if not os.path.exists(pl_path):
#                 return False
#             last_time = public.readFile(pl_path)
#             if not last_time:
#                 return False
#             if int(time.time()) - int(last_time) < 3600:
#                 return False
#
#             from mailModel import manageModel
#             res = manageModel.main().upload_send_num()
#         except:
#             pass
#
#     def auto_deploy_ssl(self):
#         # public.print_log("启动SSL证书自动部署")
#         try:
#             from sslModel import autodeployModel
#             res = autodeployModel.main().get_task_list()
#             # public.print_log(res)
#         except:
#             pass
#
#     # 502错误检查线程
#     def check502Task(self):
#         try:
#             while True:
#                 self.check_node_status()
#                 public.auto_backup_panel()
#                 # public.auto_backup_defalt_db()
#                 # self.check502()
#                 self.sess_expire()
#                 # self.mysql_quota_check()
#                 self.siteEdate()
#                 self.upload_send_num()
#                 self.auto_deploy_ssl()
#                 time.sleep(600)
#                 PluginLoader.daemon_panel()
#                 self.flush_docker_hub_repos()
#                 self.flush_geoip()
#
#         except Exception as ex:
#             self.write_log(ex)
#             time.sleep(600)
#             PluginLoader.daemon_panel()
#             self.check502Task()
#
#     # MySQL配额检查
#     def mysql_quota_check(self):
#         os.system("nohup {} {}/script/mysql_quota.py > /dev/null 2>&1 &".format(self.python_bin, self.panel_path))
#
#     # session过期处理
#     def sess_expire(self):
#         self.sess_expire_sql()
#         try:
#             sess_path = os.path.join(self.panel_path, 'data/session')
#             if not os.path.exists(sess_path):
#                 return
#             s_time = time.time()
#             f_list = os.listdir(sess_path)
#             f_num = len(f_list)
#             sess_out_path = '{}/data/session_timeout.pl'.format(self.panel_path)
#             session_timeout = 86400
#             if os.path.exists(sess_out_path):
#                 try:
#                     session_timeout = int(public.readFile(sess_out_path))
#                 except:
#                     pass
#             for fname in f_list:
#                 filename = os.path.join(sess_path, fname)
#                 fstat = os.stat(filename)
#                 f_time = s_time - fstat.st_mtime
#                 if f_time > session_timeout:
#                     os.remove(filename)
#                     continue
#                 if fstat.st_size < 256 and len(fname) == 32:
#                     if f_time > 60 or f_num > 30:
#                         os.remove(filename)
#                         continue
#             del (f_list)
#         except Exception as ex:
#             self.write_log(str(ex))
#
#     def sess_expire_sql(self):
#         try:
#             import sqlite3
#             self.write_log("启动session过期处理")
#             db_file = os.path.join(self.panel_path, "data/db/session.db")
#             size = os.path.getsize(db_file)
#             if size < 1024 * 1024 * 25: # 不足 10M 不用清理
#                 return
#             elif size > 1024 * 1024 * 100: # 大于 100M 删除所有数据
#                 public.clear_sql_session()
#                 return
#             conn = sqlite3.connect(db_file)
#             cur = conn.cursor()
#             expiry_time = (datetime.now(tz=timezone.utc)- timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S.%f")
#             res = cur.execute("DELETE FROM sessions WHERE expiry < ?", (expiry_time,))
#             self.write_log("session过期处理: 删除了{}条数据".format(res.rowcount))
#             res = cur.execute("DELETE FROM sessions WHERE  LENGTH(`data`) < ?", (200,))
#             self.write_log("session过期处理: 删除了{}条空值数据".format(res.rowcount))
#             cur.close()
#             conn.commit()
#             conn.close()
#         except Exception as e:
#             self.write_log(str(e))
#
#     # 检查面板证书是否有更新
#     def check_panel_ssl(self):
#         time.sleep(60)
#         try:
#             self.write_log("启动面板SSL证书监控")
#             while True:
#                 lets_info = public.ReadFile(os.path.join(self.panel_path, "ssl/lets.info"))
#                 if not lets_info:
#                     time.sleep(3600)
#                     continue
#                 os.system("nohup {} {}/script/panel_ssl_task.py > /dev/null 2>&1 &".format(self.python_bin, self.panel_path))
#                 time.sleep(3600)
#         except Exception as e:
#             public.writeFile("/tmp/panelSSL.pl", str(e), "a+")
#
#     # 面板进程守护
#     def daemon_panel(self):
#         cycle = 10
#         panel_pid_file = "{}/logs/panel.pid".format(self.panel_path)
#         self.write_log("启动面板进程守护")
#         while 1:
#             time.sleep(cycle)
#
#             # 检查pid文件是否存在
#             if not os.path.exists(panel_pid_file):
#                 continue
#
#             # 读取pid文件
#             panel_pid = public.readFile(panel_pid_file)
#             if not panel_pid:
#                 self.service_panel('start')
#                 continue
#
#             # 检查进程是否存在
#             comm_file = "/proc/{}/comm".format(panel_pid)
#             if not os.path.exists(comm_file):
#                 self.service_panel('start')
#                 continue
#
#             # 是否为面板进程
#             comm = public.readFile(comm_file)
#             if comm.find('BT-Panel') == -1:
#                 self.service_panel('start')
#                 continue
#
#     def update_panel(self):
#         os.system("curl -k https://download.bt.cn/install/update6.sh|bash &")
#
#     def service_panel(self, action='reload'):
#         init_file = os.path.join(self.panel_path, 'init.sh')
#         if not os.path.exists(init_file):
#             self.update_panel()
#         else:
#             os.system("nohup bash {} {} > /dev/null 2>&1 &".format(init_file, action))
#         self.write_log("面板服务: {}".format(action))
#
#     # 重启面板服务
#     def restart_panel_service(self):
#         rtips = os.path.join(self.panel_path, 'data/restart.pl')
#         reload_tips = os.path.join(self.panel_path, 'data/reload.pl')
#         self.write_log("启动面板服务监控")
#         while True:
#             if os.path.exists(rtips):
#                 os.remove(rtips)
#                 self.service_panel('restart')
#             if os.path.exists(reload_tips):
#                 os.remove(reload_tips)
#                 self.service_panel('reload')
#             time.sleep(1)
#
#     # 取面板pid
#     def get_panel_pid(self):
#         try:
#             panel_pid_file = os.path.join(self.panel_path, 'logs/panel.pid')
#             pid = public.ReadFile(panel_pid_file)
#             if pid:
#                 return int(pid)
#             for pid in psutil.pids():
#                 try:
#                     p = psutil.Process(pid)
#                     n = p.cmdline()[-1]
#                     if n.find('runserver') != -1 or n.find('BT-Panel') != -1:
#                         return pid
#                 except:
#                     pass
#         except:
#             pass
#         return None
#
#     def HttpGet(self, url, timeout=6, UserAgent='BT-Panel'):
#         try:
#             curl_cmd = "curl -sS --connect-timeout {} --max-time {} --user-agent '{}' '{}'".format(timeout, timeout, UserAgent, url)
#             result = public.ExecShell(curl_cmd)
#             if result[1]:
#                 self.write_log("httpGet:", result[1])
#             return result[0]
#         except Exception as ex:
#             self.write_log("URL: {}  => {}".format(url, ex))
#             return str(ex)
#
#     def HttpPost(self, url, data, timeout=6, UserAgent='BT-Panel'):
#         try:
#             pdata = ""
#             if type(data) == dict:
#                 for key in data:
#                     pdata += "{}={}&".format(key, data[key])
#                 pdata = pdata.strip('&')
#             else:
#                 pdata = data
#             curl_cmd = "curl -sS --connect-timeout {} --max-time {} --user-agent '{}' -d '{}' '{}'".format(timeout, timeout, UserAgent, pdata, url)
#
#             result = public.ExecShell(curl_cmd)
#             if result[1]:
#                 self.write_log("httpPost:", result[1])
#             return result[0]
#         except Exception as ex:
#             self.write_log("URL: {}  => {}".format(url, ex))
#             return str(ex)
#
#     # 网站到期处理
#     def siteEdate(self):
#         try:
#             import psutil
#             pids = psutil.pids()
#             for pid in pids:
#                 try:
#                     p = psutil.Process(pid)
#                     if "python3" in p.name() and p.cmdline()[1].find('site_task.py') != -1:
#                         p.kill()
#                 except:
#                     pass
#
#             if not self.old_edate:
#                 end_tip_file = os.path.join(self.panel_path, 'data/edate.pl')
#                 self.old_edate = public.ReadFile(end_tip_file)
#             if not self.old_edate:
#                 self.old_edate = '0000-00-00'
#
#             import time
#             mEdate = time.strftime('%Y-%m-%d', time.localtime())
#             if self.old_edate == mEdate:
#                 return False
#             self.old_edate = mEdate
#
#             import time,random
#
#             time.sleep(random.uniform(90, 1800))
#             os.system("nohup {} {}/script/site_task.py > /dev/null 2>&1 &".format(self.python_bin, self.panel_path))
#         except Exception as ex:
#             self.write_log(ex)
#             pass
#
#     def GetLoadAverage(self):
#         c = os.getloadavg()
#         data = {}
#         data['one'] = float(c[0])
#         data['five'] = float(c[1])
#         data['fifteen'] = float(c[2])
#         data['max'] = psutil.cpu_count() * 2
#         data['limit'] = data['max']
#         data['safe'] = data['max'] * 0.75
#         return data
#
#     def system_task_save_day(self):
#         '''
#             @name 保存系统监控天数
#             @return int 0=未开启，>0=天数
#         '''
#         filename = os.path.join(self.panel_path, 'data/control.conf')
#         if not os.path.exists(filename): return 0
#         day = public.ReadFile(filename)
#         if not day: return 0
#         try:
#             day = int(day)
#         except ValueError:
#             day = 30
#         if day < 1: day = 30
#         return day
#
#     def system_task_get_cpuio(self, now_time) -> dict:
#         '''
#             @name 获取CPU Io
#             @param now_time<int> 当前时间
#             @return dict
#         '''
#         try:
#             if not self.cpuInfo: self.cpuInfo = {}
#             self.cpuInfo['used'] = self.proc_task_obj.get_monitor_list(now_time)
#             self.cpuInfo['mem'] = self.GetMemUsed()
#             return self.cpuInfo
#         except:
#             self.write_log(public.get_error_info())
#             return {'used': 0, 'mem': 0}
#
#     def system_task_get_networkio(self, now_time) -> dict:
#         '''
#             @name 获取网络Io
#             @param now_time<int> 当前时间
#             @return dict
#         '''
#
#         tmp = {}
#         tmp['upTotal'] = 0
#         tmp['downTotal'] = 0
#         tmp['up'] = 0
#         tmp['down'] = 0
#         tmp['downPackets'] = {}
#         tmp['upPackets'] = {}
#         try:
#             # 取当前网络Io
#             networkIo_list = psutil.net_io_counters(pernic=True)
#             for k in networkIo_list.keys():
#                 networkIo = networkIo_list[k][:4]
#                 if not k in self.network_up.keys():
#                     self.network_up[k] = networkIo[0]
#                     self.network_down[k] = networkIo[1]
#
#                 tmp['upTotal'] += networkIo[0]
#                 tmp['downTotal'] += networkIo[1]
#                 tmp['downPackets'][k] = round(
#                     float((networkIo[1] - self.network_down[k]) / 1024) / self.cycle, 2)
#                 tmp['upPackets'][k] = round(
#                     float((networkIo[0] - self.network_up[k]) / 1024) / self.cycle, 2)
#                 tmp['up'] += tmp['upPackets'][k]
#                 tmp['down'] += tmp['downPackets'][k]
#
#                 self.network_up[k] = networkIo[0]
#                 self.network_down[k] = networkIo[1]
#         except:
#             self.write_log(public.get_error_info())
#
#         self.networkInfo = tmp
#         return self.networkInfo
#
#     def system_task_get_diskio(self, now_time) -> dict:
#         '''
#             @name 获取磁盘Io
#             @param now_time<int> 当前时间
#             @return dict
#         '''
#
#         if os.path.exists('/proc/diskstats'):
#             self.diskio_2 = psutil.disk_io_counters()
#
#             if not self.diskio_1:
#                 self.diskio_1 = self.diskio_2
#             tmp = {}
#             tmp['read_count'] = int((self.diskio_2.read_count - self.diskio_1.read_count) / self.cycle)
#             tmp['write_count'] = int((self.diskio_2.write_count - self.diskio_1.write_count) / self.cycle)
#             tmp['read_bytes'] = int((self.diskio_2.read_bytes - self.diskio_1.read_bytes) / self.cycle)
#             tmp['write_bytes'] = int((self.diskio_2.write_bytes - self.diskio_1.write_bytes) / self.cycle)
#             tmp['read_time'] = int((self.diskio_2.read_time - self.diskio_1.read_time) / self.cycle)
#             tmp['write_time'] = int((self.diskio_2.write_time - self.diskio_1.write_time) / self.cycle)
#
#             if not self.diskInfo:
#                 self.diskInfo = tmp
#
#             # if (tmp['read_bytes'] + tmp['write_bytes']) > (diskInfo['read_bytes'] + diskInfo['write_bytes']):
#             self.diskInfo['read_count'] = tmp['read_count']
#             self.diskInfo['write_count'] = tmp['write_count']
#             self.diskInfo['read_bytes'] = tmp['read_bytes']
#             self.diskInfo['write_bytes'] = tmp['write_bytes']
#             self.diskInfo['read_time'] = tmp['read_time']
#             self.diskInfo['write_time'] = tmp['write_time']
#
#             # self.write_log(['read: ',tmp['read_bytes'] / 1024 / 1024,'write: ',tmp['write_bytes'] / 1024 / 1024])
#             self.diskio_1 = self.diskio_2
#             return self.diskio_1
#
#     def system_task_init_db(self):
#         '''
#             @name 初始化系统监控数据库
#             @return None
#         '''
#         with db.Sql() as sql:
#             sql = sql.dbfile('system')
#             csql = '''CREATE TABLE IF NOT EXISTS `load_average` (
#     `id` INTEGER PRIMARY KEY AUTOINCREMENT,
#     `pro` REAL,
#     `one` REAL,
#     `five` REAL,
#     `fifteen` REAL,
#     `addtime` INTEGER
#     )'''
#             sql.execute(csql, ())
#             sql.close()
#
#     # 系统监控任务
#     def systemTask(self):
#         time.sleep(60)
#         cycle = 60
#         try:
#             filename = os.path.join(self.panel_path, 'data/control.conf')
#             with db.Sql() as sql:
#                 sql = sql.dbfile('system')
#                 csql = '''CREATE TABLE IF NOT EXISTS `load_average` (
#     `id` INTEGER PRIMARY KEY AUTOINCREMENT,
#     `pro` REAL,
#     `one` REAL,
#     `five` REAL,
#     `fifteen` REAL,
#     `addtime` INTEGER
#     )'''
#                 sql.execute(csql, ())
#                 sql.close()
#
#             diskio_1 = diskio_2 = networkInfo = cpuInfo = diskInfo = None
#             network_up = {}
#             network_down = {}
#             last_delete_time = 0
#             # 实例化进程监控对象
#             proc_task_obj = process_task.process_task()
#
#             self.write_log("启动系统监控任务")
#             while True:
#                 if not os.path.exists(filename):
#                     time.sleep(10)
#                     continue
#
#                 day = 30
#                 try:
#                     day = int(public.ReadFile(filename))
#                     if day < 1:
#                         time.sleep(10)
#                         continue
#                 except:
#                     day = 30
#
#                 addtime = int(time.time())
#                 deltime = addtime - (day * 86400)
#                 # 取当前CPU Io
#                 cpuInfo = {
#                     # 通过进程监控获取CPU使用率，不得使用psutil.cpu_percent代替，这会导致没有进程监控数据
#                     'used': proc_task_obj.get_monitor_list(addtime),
#                     'mem': self.GetMemUsed()
#                 }
#
#                 # 取当前网络Io
#                 networkIo_list = psutil.net_io_counters(pernic=True)
#                 tmp = {
#                     'upTotal': 0,
#                     'downTotal': 0,
#                     'up': 0,
#                     'down': 0,
#                     'downPackets': {},
#                     'upPackets': {}
#                 }
#
#                 for k in networkIo_list.keys():
#                     networkIo = networkIo_list[k][:4]
#                     if not k in network_up.keys():
#                         network_up[k] = networkIo[0]
#                         network_down[k] = networkIo[1]
#
#                     tmp['upTotal'] += networkIo[0]
#                     tmp['downTotal'] += networkIo[1]
#                     tmp['downPackets'][k] = round(
#                         float((networkIo[1] - network_down[k]) / 1024) / cycle, 2)
#                     tmp['upPackets'][k] = round(
#                         float((networkIo[0] - network_up[k]) / 1024) / cycle, 2)
#                     tmp['up'] += tmp['upPackets'][k]
#                     tmp['down'] += tmp['downPackets'][k]
#
#                     network_up[k] = networkIo[0]
#                     network_down[k] = networkIo[1]
#
#                 # if not networkInfo:
#                 #     networkInfo = tmp
#                 # if (tmp['up'] + tmp['down']) > (networkInfo['up'] + networkInfo['down']):
#                 networkInfo = tmp
#
#                 # 取磁盘Io
#                 disk_ios = True
#                 try:
#                     if os.path.exists('/proc/diskstats'):
#                         diskio_2 = psutil.disk_io_counters()
#
#                         if not diskio_1:
#                             diskio_1 = diskio_2
#                         tmp = {}
#                         tmp['read_count'] = int((diskio_2.read_count - diskio_1.read_count) / cycle)
#                         tmp['write_count'] = int((diskio_2.write_count - diskio_1.write_count) / cycle)
#                         tmp['read_bytes'] = int((diskio_2.read_bytes - diskio_1.read_bytes) / cycle)
#                         tmp['write_bytes'] = int((diskio_2.write_bytes - diskio_1.write_bytes) / cycle)
#                         tmp['read_time'] = int((diskio_2.read_time - diskio_1.read_time) / cycle)
#                         tmp['write_time'] = int((diskio_2.write_time - diskio_1.write_time) / cycle)
#
#                         if not diskInfo:
#                             diskInfo = tmp
#
#                         # if (tmp['read_bytes'] + tmp['write_bytes']) > (diskInfo['read_bytes'] + diskInfo['write_bytes']):
#                         diskInfo['read_count'] = tmp['read_count']
#                         diskInfo['write_count'] = tmp['write_count']
#                         diskInfo['read_bytes'] = tmp['read_bytes']
#                         diskInfo['write_bytes'] = tmp['write_bytes']
#                         diskInfo['read_time'] = tmp['read_time']
#                         diskInfo['write_time'] = tmp['write_time']
#
#                         # self.write_log(['read: ',tmp['read_bytes'] / 1024 / 1024,'write: ',tmp['write_bytes'] / 1024 / 1024])
#                         diskio_1 = diskio_2
#                 except:
#                     self.write_log(public.get_error_info())
#                     disk_ios = False
#
#                 try:
#                     sql = db.Sql().dbfile('system')
#                     # 插入CPU监控数据
#                     data = (round(cpuInfo['used'], 2), round(cpuInfo['mem'], 2), addtime)
#                     sql.table('cpuio').add('pro,mem,addtime', data)
#
#                     # 插入网络监控数据
#                     data = (networkInfo['up'], networkInfo['down'], networkInfo['upTotal'], networkInfo['downTotal'], json.dumps(networkInfo['downPackets']), json.dumps(networkInfo['upPackets']), addtime)
#                     sql.table('network').add('up,down,total_up,total_down,down_packets,up_packets,addtime', data)
#
#                     # 插入磁盘监控数据
#                     if os.path.exists('/proc/diskstats') and disk_ios:
#                         data = (diskInfo['read_count'], diskInfo['write_count'], diskInfo['read_bytes'], diskInfo['write_bytes'], diskInfo['read_time'], diskInfo['write_time'], addtime)
#                         sql.table('diskio').add('read_count,write_count,read_bytes,write_bytes,read_time,write_time,addtime', data)
#
#                     # 插入负载监控数据
#                     load_average = self.GetLoadAverage()
#                     lpro = round(
#                         (load_average['one'] / load_average['max']) * 100, 2)
#                     if lpro > 100:
#                         lpro = 100
#                     sql.table('load_average').add('pro,one,five,fifteen,addtime', (lpro, load_average['one'], load_average['five'], load_average['fifteen'], addtime))
#
#                     # 每隔1小时清理一次过期数据
#                     if addtime - last_delete_time > 3600:
#                         sql.table('diskio').where("addtime<?", (deltime,)).delete()
#                         sql.table('cpuio').where("addtime<?", (deltime,)).delete()
#                         sql.table('network').where("addtime<?", (deltime,)).delete()
#                         sql.table('load_average').where("addtime<?", (deltime,)).delete()
#                         last_delete_time = addtime
#
#                     sql.close()
#
#                     lpro = None
#                     load_average = None
#                     cpuInfo = None
#                     networkInfo = None
#                     diskInfo = None
#                     data = None
#
#                 except Exception as ex:
#                     self.write_log(str(ex))
#                 del (tmp)
#                 time.sleep(cycle)
#         except Exception as ex:
#             self.write_log(ex)
#             time.sleep(cycle)
#             self.systemTask()
#
#     def start_daily(self):
#         '''
#             @name 日报统计
#             @return None
#         '''
#         while True:
#             try:
#                 time.sleep(7200)
#                 os.system("nohup {} {}/script/daily.py > /dev/null 2>&1 &".format(self.python_bin, self.panel_path))
#             except:
#                 time.sleep(7200)
#
#     # 2024/11/19 11:00 Docker网站项目-网站到期处理
#     def deal_with_docker_expired_site(self):
#         '''
#             @name Docker网站项目-网站到期处理
#         '''
#         try:
#             # 2024/11/19 11:13 1天只检查1次
#             pl_file = '{}/data/check_deal_with_docker_expired_site.pl'.format(self.panel_path)
#             if os.path.exists(pl_file):
#                 mtime = os.path.getmtime(pl_file)
#                 if time.time() - mtime < 86400: return
#
#             from btdockerModel import dk_public as dp
#             sresult = dp.sql("docker_sites").field("id,name,edate").select()
#             if not sresult: return
#
#             from mod.project.docker.sites.sitesManage import SitesManage
#             site_manage = SitesManage()
#
#             for site in sresult:
#                 if not site: continue
#                 if site['edate'] == '0000-00-00': continue
#                 if site['edate'] == time.strftime('%Y-%m-%d', time.localtime()): continue
#                 if site['edate'] < time.strftime('%Y-%m-%d', time.localtime()):
#                     args = public.dict_obj()
#                     args.id = site['id']
#                     args.status = 0
#                     args.site_name = site['name']
#                     site_manage.set_site_status(args)
#                     public.WriteLog("Docker网站项目-网站到期处理", "网站{}已到期".format(site['name']))
#
#             if not os.path.exists(pl_file): public.writeFile(pl_file, 'True')
#         except:
#             pass
#     # 定时进行云安全扫描
#     def check_safecloud_task(self):
#         '''
#             @description 云安全扫描任务 /script/safecloud_list.py
#                         【恶意文件检测 已移植到task_ssh_error_count执行 每6小时执行一次】
#                         【首页风险任务 每24小时执行一次】
#                         【漏洞扫描任务 已移植到warning_list.py执行】
#             @author date
#             @return void
#         '''
#         self.write_log("启动云安全扫描任务")
#         time.sleep(120)  # 启动时延迟2分钟，避免与其他服务同时启动
#
#         while True:
#             try:
#                 # 检查上一次执行是否还在运行
#                 ps_result = public.ExecShell("ps aux |grep 'warning_list.py'|grep -v grep|wc -l")[0]
#                 if int(ps_result) > 0:
#                     self.write_log("首页风险任务正在执行中，跳过本次执行", _level='WARNING')
#                     time.sleep(3600)  # 如果上一个任务还在运行，等待1小时后重试
#                     continue
#
#                 # 执行扫描任务
#                 self.write_log("开始执行首页风险任务")
#                 os.system("nohup {} {}/script/warning_list.py > /dev/null 2>&1 &".format(self.python_bin, self.panel_path))
#
#                 # 24小时执行一次
#                 time.sleep(86400)  # 24 小时 24 * 60 * 60 = 3600 * 24 = 86400
#
#             except Exception as e:
#                 time.sleep(3600)  # 发生异常时等待1小时后重试
#
#     def refresh_domain_cache(self):
#         '''
#             @name 刷新域名缓存
#             @return None
#         '''
#         try:
#             self.write_log("开始刷新域名缓存")
#             from mod.project.domain import domainMod
#             domainMod.main().refresh_domain_cache()
#             self.write_log("域名缓存刷新完成")
#             # 24小时执行一次
#             time.sleep(86400)
#         except:
#             self.write_log("刷新域名缓存失败")
#             public.print_log(public.get_error_info())
#             time.sleep(3600)
#
#     def run_thread(self):
#         '''
#             @name 运行线程集合
#             @return None
#         '''
#         from mailModel.power_mta.maillog_stat import maillog_event
#         tkeys = self.thread_dict.keys()
#
#         thread_list = {
#             "start_task": self.task_obj.start_task,
#             "systemTask": self.systemTask,
#             "check502Task": self.check502Task,
#             "daemon_panel": self.daemon_panel,
#             "restart_panel_service": self.restart_panel_service,
#             "check_panel_ssl": self.check_panel_ssl,
#             "update_software_list": self.update_software_list,
#             "send_mail_time": self.send_mail_time,
#             "check_panel_msg": self.check_panel_msg,
#             "push_msg": self.push_msg,
#             "total_load_msg": self.total_load_msg,
#             "node_monitor": self.node_monitor,
#             "ProDadmons": self.ProDadmons,
#             "process_task_thread": self.process_task_thread,
#             'run_tasks_list': self.run_tasks_list,
#             # "check_database_quota": self.check_database_quota,
#             "start_daily": self.start_daily,
#             "deal_with_docker_expired_site": self.deal_with_docker_expired_site,
#             "check_safecloud_task": self.check_safecloud_task,
#             "maillog_event": maillog_event,
#             "refresh_domain_cache": self.refresh_domain_cache,
#         }
#
#         for skey in thread_list.keys():
#             if not skey in tkeys or not self.thread_dict[skey].is_alive():
#                 self.thread_dict[skey] = threading.Thread(target=thread_list[skey])
#                 self.thread_dict[skey].setDaemon(True)
#                 self.thread_dict[skey].start()


class _BTTaskService:
    def __init__(self):
        self.db_file = '{}/data/db/task.db'.format(PANEL_PATH)
    
    @staticmethod
    def proc_execute_task(task_dict_str: str):
        def proc_worker(data:str):
            task_info = json.loads(data)
            os.chdir(PANEL_PATH)
            sys.path.insert(0, PANEL_PATH)
            sys.path.insert(0, "{}/class".format(PANEL_PATH))
            from panelTask import bt_task
            bt_task().execute_task(task_info['id'], task_info['type'], task_info['shell'], task_info['other'])

        p = Process(target=proc_worker, args=(task_dict_str,), daemon=True)
        p.start()
        p.join()
        write_log("执行任务" + task_dict_str + ">>>>", p.exitcode)
        return

    def do_once(self):
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        # 重置所有任务状态
        cur.execute("UPDATE `task_list` SET `status`='0' WHERE `status`=?", ('-1',))
        conn.commit()
        
        ret = cur.execute(
            "SELECT `id`,`name`,`type`,`shell`,`other`,`status`,`exectime`,`endtime`,`addtime` "
            "FROM task_list WHERE `status`=? ORDER BY id ASC", ('0',)
        )
        
        task_arr = list(map(
            lambda x: dict(zip(('id','name','type','shell','other','status','exectime','endtime','addtime'), x)),
            ret.fetchall()
        ))
        cur.close()
        conn.close()

        for task in task_arr:
            task_dict_str = json.dumps(task)
            self.proc_execute_task(task_dict_str)
            write_log("执行任务：{}".format(task['name']))

    def start(self):
        tip_file = '/dev/shm/.start_task.pl'
        start_file = '/dev/shm/bt_task_now.pl'
        n = 0
        # 每60秒主动执行一次，当存在开始文件时，被动执行一次
        while True:
            try:
                time.sleep(1)
                write_file(tip_file, str(int(time.time())))
                n += 1
                if not os.path.exists(start_file) and  n < 60:
                    continue
                if os.path.exists(start_file):
                    os.remove(tip_file)
                n = 0
                self.do_once()
            except:
                err = traceback.format_exc()
                write_log("bt_task任务执行失败:", err,_level='ERROR', color='red')


class _TaskListService:
    def __init__(self):
        self.task_path='{}/data/tasks'.format(PANEL_PATH)

    def start(self):
        """
        @name 延时启动任务
        """

        write_log("启动延时任务")
        while True:
            if os.path.exists(self.task_path):
                self.do_once()
            time.sleep(60)

    def do_once(self):
        task_file_list = os.listdir(self.task_path)
        for file in task_file_list:
            try:
                filename = '{}/{}'.format(self.task_path, file)
                file_data = read_file(filename)
                if not file_data:
                    os.remove(filename)
                    continue
                data = json.loads(file_data)
                # 超过执行时间
                if time.time() > int(data['time']):
                    self.proc_run_tasks_list(filename)
            except:
                err = traceback.format_exc()
                write_log("延时任务执行失败", err, _level='ERROR', color='red')

    @staticmethod
    def proc_run_tasks_list(filename: str ):

        def proc_worker(task_filename:str):
            try:
                task_data_str = read_file(task_filename)
            except:
                return "任务文件不存在"
            task_dict = json.loads(task_data_str)
            os.chdir(PANEL_PATH)
            sys.path.insert(0, PANEL_PATH)
            sys.path.insert(0, "{}/class".format(PANEL_PATH))
            try:
                import PluginLoader
                import public
            except:
                write_log("PluginLoader 模块不存在")
            try:
                if task_dict['type'] in [2, '2']:
                    res = PluginLoader.plugin_run(task_dict['name'], task_dict['fun'], public.to_dict_obj(task_dict['args']))
                    if not res['status']:
                        return "插件执行失败: " + res.get('msg', '')
                    os.remove(task_filename)
                    write_log(task_dict['title'], res['msg'])
                elif task_dict['type'] in [1, '1']:
                    # 面板
                    args = public.to_dict_obj(task_dict['args'])
                    args.model_index = task_dict['model_index']
                    res = PluginLoader.module_run(task_dict['name'], task_dict['fun'], args)
                    os.remove(task_filename)
                    write_log(task_dict['title'], res['msg'])
            except:
                err = traceback.format_exc()
                write_log("模块执行失败: ", err)
                os.remove(task_filename)

        p = Process(target=proc_worker, args=(filename,), daemon=True)
        p.start()
        p.join()
        return


class _BTPanelDaemonService:

    def __init__(self):
        self.pid_file = "{}/logs/panel.pid".format(PANEL_PATH)
        self.restart_tip_file ='{}/data/restart.pl'.format(PANEL_PATH)
        self.reload_tip_file ='{}/data/reload.pl'.format(PANEL_PATH)
        self._num = 0


    def do_one(self):
        if self._num % 10 == 0:
            self._num = 0
            self.daemon_panel()
        self.restart_panel_service()
        self._num += 1

    def start(self):
        while True:
            try:
                self.do_one()
                time.sleep(1)
            except:
                err = traceback.format_exc()
                write_log("面板进程守护异常", err)
                time.sleep(1)

    # 面板进程守护
    def daemon_panel(self):
        # write_log("面板进程守护检查")

        # 检查pid文件是否存在
        if not os.path.exists(self.pid_file):
            return

        # 读取pid文件
        panel_pid = read_file(self.pid_file)
        if not panel_pid:
            self.service_panel('start')
            return

        # 检查进程是否存在
        comm_file = "/proc/{}/comm".format(panel_pid)
        if not os.path.exists(comm_file):
            self.service_panel('start')
            return

        # 是否为面板进程
        comm = read_file(comm_file)
        if comm.find('BT-Panel') == -1:
            self.service_panel('start')

    @staticmethod
    def update_panel():
        os.system("curl -k https://download.bt.cn/install/update6.sh|bash &")

    def service_panel(self, action='reload'):
        init_file = os.path.join(PANEL_PATH, 'init.sh')
        if not os.path.exists(init_file):
            self.update_panel()
        else:
            os.system("nohup bash {} {} > /dev/null 2>&1 &".format(init_file, action))
        write_log("面板服务: {}".format(action))

    # 重启面板服务
    def restart_panel_service(self):
        if os.path.exists(self.restart_tip_file):
            os.remove(self.restart_tip_file)
            self.service_panel('restart')
        if os.path.exists(self.reload_tip_file):
            os.remove(self.reload_tip_file)
            self.service_panel('reload')

    # 取面板pid
    @staticmethod
    def get_panel_pid():
        try:
            panel_pid_file = os.path.join(PANEL_PATH, 'logs/panel.pid')
            pid = read_file(panel_pid_file)
            if pid:
                return int(pid)
            for pid in psutil.pids():
                try:
                    p = psutil.Process(pid)
                    cmdline = p.cmdline()
                    py_proc = any(('python' in i for i in cmdline))
                    if not py_proc:
                        continue
                    n = p.cmdline()[-1]
                    if n.find('runserver') != -1 or n.find('BT-Panel') != -1:
                        return pid
                except:
                    pass
        except:
            pass
        return None


class _SoftService:
    tip_file = '/dev/shm/.panelTask.pl'
    is_task = '/tmp/panelTask.pl'
    db_file = '{}/data/db/task.db'.format(PANEL_PATH)

    @staticmethod
    def can_write_file():
        test_file = '/etc/init.d/bt_10000100.pl'
        write_file(test_file, 'True')
        if os.path.exists(test_file):
            if read_file(test_file) == 'True':
                os.remove(test_file)
                return True
            os.remove(test_file)
        return False

    def stop_syssafe(self):
        ret = self.can_write_file()
        is_stop_syssafe_file = '{}/data/is_stop_syssafe.pl'.format(PANEL_PATH)
        # 如果不可写，则尝试停用系统加固
        if not ret:
            syssafe_path = "{}/plugin/{}".format(PANEL_PATH, 'syssafe')
            if os.path.exists(syssafe_path):
                write_file(is_stop_syssafe_file, 'True')
                init_file = "/etc/init.d/bt_syssafe"
                if not os.path.exists(init_file):
                    plugin_init_file = "{}/init.sh".format(syssafe_path)
                    if os.path.exists(plugin_init_file):
                        shutil.copyfile(plugin_init_file, init_file)
                        os.chmod(init_file, 755)

                os.system("/etc/init.d/bt_syssafe stop")
                # 停用系统加固后再检测一次
                ret = self.can_write_file()
                return ret

        return ret

    @staticmethod
    def start_syssafe():
        is_stop_syssafe_file = '{}/data/is_stop_syssafe.pl'.format(PANEL_PATH)
        if os.path.exists(is_stop_syssafe_file):
            os.system("/etc/init.d/bt_syssafe start")
            if os.path.exists(is_stop_syssafe_file):
                os.remove(is_stop_syssafe_file)

    def task_table_rep(self):
        try:
            conn = sqlite3.connect(self.db_file)
            cur = conn.cursor()
            ret = cur.execute("SELECT count(*) FROM sqlite_master where type='table' and name='tasks' and sql like '%msg%'")
            if ret.fetchone()[0] == 0:
                cur.execute("ALTER TABLE tasks ADD COLUMN msg TEXT DEFAULT '安装成功'")
            ret2 = cur.execute("SELECT count(*) FROM sqlite_master where type='table' and name='tasks' and sql like '%install_status%'")
            if ret2.fetchone()[0] == 0:
                cur.execute("ALTER TABLE tasks ADD COLUMN install_status INTEGER DEFAULT 1")
            cur.close()
            conn.commit()
            conn.close()
        except:
            pass

    @staticmethod
    def save_installed_msg(task_data: dict):
        msg_path = "{}/data/msg_box_data".format(PANEL_PATH)
        try:
            msg_list = [i for i in os.listdir(msg_path) if i not in ("not_read.tip", "update.pl")]
            for msg_name in msg_list:
                msg_file = "{}/{}".format(msg_path, msg_name)
                try:
                    with open(msg_file, "r") as f:
                        msg: dict = json.load(f)
                    if msg["sub"]["task_id"] == task_data["id"]:
                        task_data["msg_name"] = msg_name
                    else:
                        continue

                    msg["title"] = "正在" + msg["title"][2:]
                    msg["sub"]["file_name"] = "/tmp/panelExec.log"
                    msg["sub"]["install_status"] = "正在" + msg["sub"]["install_status"][2:]
                    msg["sub"]["status"] = 1
                    msg["read"] = False
                    msg["read_time"] = 0
                    with open(msg_file, "w") as f:
                        json.dump(msg, f)
                except:
                    continue
        except:
            err_log = traceback.format_exc()
            write_log(err_log, _level="error", color="")

    @staticmethod
    def update_installed_msg(task_data: dict):
        msg_path = "{}/data/msg_box_data".format(PANEL_PATH)
        msg_name = task_data.get("msg_name", "")
        if not msg_name:
             return
        msg_file = "{}/{}".format(msg_path, task_data.get("msg_name"))
        if not os.path.isfile(msg_file):
            return
        try:
            logs_dir = "{}/logs/installed".format(PANEL_PATH)
            if not os.path.exists(logs_dir):
                os.makedirs(logs_dir, 0o600)

            with open(msg_file, "r") as f:
                msg = json.load(f)

            filename = logs_dir + "/{}_{}.log".format(msg["sub"]["soft_name"], int(time.time()))
            if os.path.exists(EXEC_LOG_PATH):
                shutil.copyfile(EXEC_LOG_PATH, filename)
                msg["sub"]["file_name"] = filename
                msg["sub"]["install_status"] = msg["sub"]["install_status"][2:] + "结束"
                msg["sub"]["status"] = 2
                msg["read"] = False
                msg["title"] = msg["title"][2:] + "已结束"
                msg["read_time"] = 0

            with open(msg_file, "w") as f:
                json.dump(msg, f)
        except:
            err_log = traceback.format_exc()
            write_log(err_log, _level="error", color="")

    @staticmethod
    def task_end(exec_str: str):
        # 安装PHP后需要重新加载PHP环境
        if exec_str.find('install php') != -1:
            os.system("{} {}/tools.py phpenv".format(PY_BIN, PANEL_PATH))
        elif exec_str.find('install nginx') != -1:
            # 修复nginx配置文件到支持当前安装的nginx版本
            os.system("{} {}/script/nginx_conf_rep.py".format(PY_BIN, PANEL_PATH))

    @staticmethod
    def parse_soft_name_of_version(name):
        """
            @name 获取软件名称和版本
            @param name<string> 软件名称
            @return tuple(string, string) 返回软件名称和版本
        """
        if name.find('Docker') != -1:
            return 'docker', '1.0'
        return_default = ('', '')
        l, r = name.find('['), name.find(']')
        if l == -1 or r == -1 or l > r:
            return return_default
        # 去除括号只保留括号中间的软件名称和版本
        if name[l+1:r].count("-") == 0:
            return return_default
        soft_name, soft_version = name[l+1:r].split('-')[:2]
        if soft_name == 'php':
            soft_version = soft_version.replace('.', '')
        return soft_name, soft_version

    @staticmethod
    def get_hostname() -> str:
        try:
            import socket
            return socket.gethostname()
        except:
            return 'localhost.localdomain'


    def check_install_status(self, name: str):
        """
        @name 检查软件是否安装成功
        @param name<string> 软件名称
        @return tuple(bool, string) 返回是否安装成功和安装信息
        """
        return_default = (1, '安装成功')
        try:
            # 获取安装检查配置
            install_config = json.loads(read_file("{}/config/install_check.json".format(PANEL_PATH)))
        except:
            return return_default
        try:
            # 获取软件名称和版本
            soft_name, soft_version = self.parse_soft_name_of_version(name)
            if not soft_name or not soft_version:
                return return_default

            if soft_name not in install_config:
                return return_default

            if os.path.exists("{}/install/{}_not_support.pl".format(PANEL_PATH, soft_name)):
                return 0, '不兼容此系统！请点详情说明！'

            if os.path.exists("{}/install/{}_mem_kill.pl".format(PANEL_PATH, soft_name)):
                return 0, '内存不足安装异常！请点详情说明！'

            soft_config = install_config[soft_name]

            # 替换soft_config中所有变量
            def replace_all(dat:str):
                if not dat:
                    return dat
                if dat.find('{') == -1:
                    return dat
                # 替换安装路径, 替换版本号
                dat = dat.replace('{SetupPath}', SETUP_PATH).replace('{Version}', soft_version)
                # 替换主机名
                if dat.find("{Host") != -1:
                    host_name = self.get_hostname()
                    host = host_name.split('.')[0]
                    dat = dat.replace("{Hostname}", host_name)
                    dat = dat.replace("{Host}", host)
                return dat

            # 检查文件是否存在
            if 'files_exists' in soft_config:
                for f_name in soft_config['files_exists']:
                    filename = replace_all(f_name)
                    if not os.path.exists(filename):
                        return 0, '安装失败,文件不存在:{}'.format(filename)

            # 检查pid文件是否有效
            if 'pid' in soft_config and soft_config['pid']:
                pid_file = replace_all(soft_config['pid'])
                if not os.path.exists(pid_file):
                    return 0, '启动失败,pid文件不存在:{}'.format(pid_file)
                pid = read_file(pid_file)
                if not pid:
                    return 0, '启动失败,pid文件为空:{}'.format(pid_file)
                proc_file = '/proc/{}/cmdline'.format(pid.strip())
                if not os.path.exists(proc_file):
                    return 0, '启动失败,指定PID: {}({}) 进程不存在'.format(pid_file, pid)

            # 执行命令检查
            if 'cmd' in soft_config:
                for cmd in soft_config['cmd']:
                    p = subprocess.Popen(
                        replace_all(cmd['exec']), shell=True,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                    )
                    p.wait()
                    res = p.stdout.read() + "\n" + p.stderr.read()
                    if res.find(replace_all(cmd['success'])) == -1:
                        return 0, '{}服务启动状态异常'.format(soft_name)
        except:
            pass

        return return_default

    def do_one(self):
        conn = None
        try:
            conn = sqlite3.connect(self.db_file)
            cur = conn.cursor()
            # 重置所有任务状态
            cur.execute("UPDATE `tasks` SET `status`='0' WHERE `status`=?", ('-1',))
            conn.commit()

            ret = cur.execute(
                "SELECT `id`,`name`,`type`,`execstr` FROM tasks WHERE `status`=? ORDER BY id ASC", ('0',)
            )
            task_arr = list(map(lambda x: dict(zip(('id', 'name', 'type', 'execstr'),  x)), ret.fetchall()))
            cur.close()
            # 逐个执行任务
            for t_task in task_arr:
                # 检查关键目录是否可写
                self.stop_syssafe()
                # 检查任务类型是否为shell执行
                if t_task['type'] != 'execshell':
                    continue

                tmp_cur = conn.cursor()
                # 检查任务是否存在
                t_exists = tmp_cur.execute("SELECT count(*) FROM `tasks` WHERE `id`=?", (t_task['id'],))
                if t_exists.fetchone()[0] == 0:
                    tmp_cur.close()
                    continue

                # 写入状态和任务开始时间
                start = int(time.time())
                tmp_cur.execute("UPDATE `tasks` SET `status`=?,`start`=? WHERE `id`=?", ("-1", start, t_task['id']))
                conn.commit()
                tmp_cur.close()

                # 保存安装日志
                self.save_installed_msg(t_task)
                # 执行任务
                write_log("正在执行任务: {}".format(t_task['name']))
                exec_shell(t_task['execstr'])
                write_log("任务执行完成, 开始验证")

                # 处理任务结束事件
                self.task_end(t_task['execstr'])

                # 检查软件是否安装成功
                end = int(time.time())
                install_status, install_msg = self.check_install_status(t_task['name'])
                write_log("任务执行结果: {},".format(install_msg), "耗时: {}秒".format(end - start))

                # 写入任务结束状态到数据库
                status_code = 1
                tmp_cur = conn.cursor()
                tmp_cur.execute("UPDATE `tasks` SET `status`=?,`end`=?,`msg`=?,`install_status`=? WHERE `id`=?",
                                (status_code, end, install_msg, install_status, t_task['id']),)
                conn.commit()

                # 更新安装日志
                self.update_installed_msg(t_task)

                t_has_check = tmp_cur.execute("SELECT count(*) FROM `tasks` WHERE `status`='0'", )
                # 移除任务标记文件
                if t_has_check.fetchone()[0] == 0:
                    if os.path.exists(self.is_task):
                        os.remove(self.is_task)

                tmp_cur.close()
                # 重置系统加固状态
                self.start_syssafe()
                return True
        except Exception as e:
            err_log = traceback.format_exc()
            write_log("任务执行失败: {}".format(str(e)), err_log, _level='error', color='red')
            if conn:
                conn.close()
            return  False

    def start(self):
        self.task_table_rep()
        while True:
            if os.path.exists(self.is_task):
                self.do_one()
            write_file(self.tip_file, str(int(time.time())))
            time.sleep(1)


_Proc = namedtuple(
    '_Proc',
    [
        'pid', 'c_time', 'st_timer', 'cpu_time', 'disk_read', 'disk_write',
        'net_up', 'net_down', 'net_up_packets', 'net_down_packets'
    ]
)
_proc_zero = _Proc(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
_ProcNet = namedtuple(
    '_ProcNet',
    [
        'pid', 'net_down', 'net_up', 'net_down_packets', 'net_up_packets'
    ]
)
_proc_net_zero = _ProcNet(0, 0, 0, 0, 0)


class _SystemService:
    base_service = os.path.join(PANEL_PATH, 'data/control.conf')
    proc_net_service = os.path.join(PANEL_PATH, 'data/is_net_task.pl')
    db_file = '{}/data/system.db'.format(PANEL_PATH)
    cache_file = "{}/data/system_cache.pkl".format(PANEL_PATH)

    def _init_table(self) -> bool:
        tb_sql='''
CREATE TABLE IF NOT EXISTS `network` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `up` INTEGER,
    `down` INTEGER,
    `total_up` INTEGER,
    `total_down` INTEGER,
    `down_packets` INTEGER,
    `up_packets` INTEGER,
    `addtime` INTEGER
);

CREATE TABLE IF NOT EXISTS `cpuio` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `pro` INTEGER,
    `mem` INTEGER,
    `addtime` INTEGER
);

CREATE TABLE IF NOT EXISTS `diskio` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `read_count` INTEGER,
    `write_count` INTEGER,
    `read_bytes` INTEGER,
    `write_bytes` INTEGER,
    `read_time` INTEGER,
    `write_time` INTEGER,
    `addtime` INTEGER
);

CREATE TABLE IF NOT EXISTS `process_top_list` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `cpu_top` REAL,
    `memory_top` REAL,
    `disk_top` REAL,
    `net_top` REAL,
    `all_top` REAL,
    `addtime` INTEGER
);

CREATE TABLE IF NOT EXISTS `load_average` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `pro` REAL,
    `one` REAL,
    `five` REAL,
    `fifteen` REAL,
    `addtime` INTEGER
);

CREATE TABLE IF NOT EXISTS `backup_status` (
    `id` INTEGER,
    `target` TEXT,
    `status` INTEGER,
    `msg` TEXT DEFAULT "",
    `addtime` DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `app_usage` (
    `time_key` INTEGER PRIMARY KEY,
    `app` TEXT,
    `disks` TEXT,
    `addtime` DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `server_status` (
    `status` TEXT,
    `addtime` DATETIME DEFAULT CURRENT_TIMESTAMP
);
    
CREATE TABLE IF NOT EXISTS `daily` (
    `time_key` INTEGER,
    `evaluate` INTEGER,
    `addtime` DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS 'cpu' ON 'cpuio'('addtime');
CREATE INDEX IF NOT EXISTS 'ntwk' ON 'network'('addtime');
CREATE INDEX IF NOT EXISTS 'disk' ON 'diskio'('addtime');
CREATE INDEX IF NOT EXISTS 'load' ON 'load_average'('addtime');
CREATE INDEX IF NOT EXISTS 'proc' ON 'process_top_list'('addtime');
'''
        try:
            if not os.path.isfile(self.db_file):
                os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
                open(self.db_file, 'w').close()
            conn = sqlite3.connect(self.db_file)
            conn.executescript(tb_sql)
            conn.commit()
            conn.close()
            return True
        except sqlite3.DatabaseError as e:
            write_log("数据库链接失败: {}".format(str(e)), traceback.format_exc(), _level='error', color='red')
            return False
        except Exception as e:
            write_log("初始化数据库失败: {}".format(str(e)), traceback.format_exc(), _level='error', color='red')
            return False

    def data_day(self) -> int:
        if not os.path.isfile(self.base_service):
            return 0
        try:
            day = int(read_file(self.base_service))
            return max(0, day)
        except:
            return 30

    # 在用户侧基本不使用，只有官方测试人员需要在手动写入并启用
    def start_process_net_total(self):
        # 进程流量监控，如果文件：/www/server/panel/data/is_net_task.pl 或 /www/server/panel/data/control.conf不存在，则不监控进程流量
        if not (os.path.isfile(self.proc_net_service) and os.path.isfile(self.base_service)):
            return
        def process_net_total():
            class_path = '{}/class'.format(PANEL_PATH)
            if class_path not in sys.path:
                sys.path.insert(0, class_path)

            write_log("启动进程流量监控")
            import process_task
            process_task.process_network_total().start()

        th = threading.Thread(target=process_net_total, daemon=True)
        th.start()

    def __init__(self):
        self._process_net: Optional[Dict[int, _ProcNet]] = None
        self._last_cache: Optional[Dict[int, _Proc]] = None
        self._cache_hash_sum = ""
        self.last_disk_io = None
        self.last_network_io = None
        self.this_pid = os.getpid()
        self.last_clear_time = int(time.time())

    # 加载所有的缓存数据
    def _load_cache(self):
        if not self._cache_hash_sum:
            if os.path.isfile(self.cache_file):
                os.remove(self.cache_file)
        if os.path.isfile(self.cache_file):
            with open(self.cache_file, 'rb') as f:
                f_data = f.read()

            hash_obj = hashlib.md5()
            hash_obj.update(f_data)
            if hash_obj.hexdigest() != self._cache_hash_sum:
                self._last_cache = {}
            else:
                self._last_cache = pickle.loads(f_data)
        else:
            self._last_cache = {}

        self._process_net = self._load_process_net()

    @staticmethod
    def _load_process_net():
        w_file = '/dev/shm/bt_net_process'
        if not os.path.isfile(w_file):
            return {}

        try:
            with open(w_file, 'rb') as f:
                net_process_body = f.read().decode().replace("\u0000", " ").strip()
        except:
            return {}

        if not net_process_body:
            return {}
        ret = {}
        net_process = net_process_body.split('\n')
        for np in net_process:
            if not np:
                continue
            np_list = np.split()
            if len(np_list) < 5:
                continue
            tmp = _ProcNet(*map(int, np_list[:5]))
            ret[tmp.pid] = tmp

    def _save_cache(self):
        try:
            with open(self.cache_file, 'wb') as f:
                f_data = pickle.dumps(self._last_cache)
                hash_obj = hashlib.md5()
                hash_obj.update(f_data)
                self._cache_hash_sum = hash_obj.hexdigest()
                f.write(f_data)
                self._last_cache = None
        except:
            write_log("保存数据失败", traceback.format_exc(), _level='error', color='red')
            pass

    def start(self, interval: int = 60):
        self._init_table() # 初始化数据库
        write_log("开始数据采集")
        while True:
            if self.data_day() > 0:
                try:
                    self.do_once()
                except Exception as e:
                    write_log("数据采集失败: {}".format(str(e)), traceback.format_exc(), _level='error', color='red')
            time.sleep(interval)

    @staticmethod
    def xss_encode(s:str) -> str:
        s = s.replace("&", "&amp;")  # Must be done first!
        s = s.replace("<", "&lt;")
        s = s.replace(">", "&gt;")
        s = s.replace('"', "&quot;")
        s = s.replace('\'', "&#x27;")
        return s

    def do_once(self):
        disk_io = self._get_disk_io()
        network_io = self._get_network_io()
        cpu_percent = self._get_cpu_percent()
        load_average = self._get_load_average()
        mem_usage = self._get_mem_usage()
        time_key = int(time.time())

        process_list = self._get_process_list()
        if process_list:
            all_top_list = self._cut_top_list(process_list, 'cpu_percent', 'disk_total', 'memory', 'net_total', top_num=5)
            cpu_top_list = self._cut_top_list(process_list, 'cpu_percent', top_num=5)
            disk_top_list = self._cut_top_list(process_list, 'disk_total', top_num=5)
            memory_top_list = self._cut_top_list(process_list, 'memory', top_num=5)
            net_top_list = all_top_list
            if os.path.isfile(self.proc_net_service):
                net_top_list = self._cut_top_list(process_list, 'net_total', top_num=5)

            all_top = json.dumps([(
                p['cpu_percent'], p['disk_read'], p['disk_write'], p['memory'],p['up'], p['down'], p['pid'],
                self.xss_encode(p['name']),self.xss_encode(p['cmdline']), self.xss_encode(p['username']),
                p['create_time']
            ) for p in all_top_list])
            cpu_top = json.dumps([(
                p['cpu_percent'],  p['pid'],self.xss_encode(p['name']),self.xss_encode(p['cmdline']),
                self.xss_encode(p['username']), p['create_time']
            ) for p in cpu_top_list])
            disk_top = json.dumps([(
                p['disk_total'], p['disk_read'], p['disk_write'], p['pid'],self.xss_encode(p['name']),
                self.xss_encode(p['cmdline']), self.xss_encode(p['username']), p['create_time']
            ) for p in disk_top_list])
            net_top = json.dumps([(
                p['net_total'], p['up'], p['down'],p['connect_count'], p['up_package'] + p['down_package'], p['pid'],
                self.xss_encode(p['name']),self.xss_encode(p['cmdline']), self.xss_encode(p['username']), p['create_time']
            ) for p in net_top_list])
            memory_top = json.dumps([(
                p['memory'], p['pid'],self.xss_encode(p['name']),self.xss_encode(p['cmdline']),
                self.xss_encode(p['username']), p['create_time']
            ) for p in memory_top_list])

            process_top_data = (all_top, cpu_top, disk_top, net_top, memory_top, time_key)
        else:
            process_top_data = None

        if cpu_percent:
            cpu_data = (cpu_percent, mem_usage, time_key)
        else:
            cpu_data = None
        if disk_io:
            disk_data = (
                disk_io['read_count'], disk_io['write_count'], disk_io['read_bytes'], disk_io['write_bytes'],
                disk_io['read_time'], disk_io['write_time'], time_key)
        else:
            disk_data = None
        if network_io:
            network_data = (
                network_io['up'], network_io['down'], network_io['total_up'], network_io['total_down'],
                json.dumps(network_io['down_packets']), json.dumps(network_io['up_packets']), time_key)
        else:
            network_data = None

        if load_average:
            load_data = (load_average['pro'], load_average['one'], load_average['five'], load_average['fifteen'],
                         time_key)
        else:
            load_data = None

        self.save_to_db(cpu_data, disk_data, network_data, load_data, process_top_data)

    disk_data_key = ('diskio', ('read_count','write_count','read_bytes','write_bytes','read_time','write_time','addtime'))
    network_data_key = ('network', ('up','down','total_up','total_down','down_packets','up_packets','addtime'))
    cpu_data_key = ('cpuio', ('pro','mem','addtime'))
    load_data_key = ('load_average', ('pro', 'one', 'five', 'fifteen', 'addtime'))
    process_top_data_key =('process_top_list', ('all_top','cpu_top','disk_top','net_top','memory_top','addtime'))
    def save_to_db(self, cpu_data, disk_data, network_data, load_data, process_top_data):
        d_list: List[Tuple[str, Tuple[str, ...], Tuple[Any, ...]]] = []
        if cpu_data:
            d_list.append((self.cpu_data_key[0], self.cpu_data_key[1], cpu_data))
        if disk_data:
            d_list.append((self.disk_data_key[0], self.disk_data_key[1], disk_data))
        if network_data:
            d_list.append((self.network_data_key[0], self.network_data_key[1], network_data))
        if load_data:
            d_list.append((self.load_data_key[0], self.load_data_key[1], load_data))
        if process_top_data:
            d_list.append((self.process_top_data_key[0], self.process_top_data_key[1], process_top_data))
        try:
            conn = sqlite3.connect(self.db_file)
            cur = conn.cursor()
            sql_fmt = "INSERT INTO `{}` ({}) VALUES ({})"
            for table_name, table_columns, table_data in d_list:
                tmp_arg = ",".join(["?"] * len(table_columns))
                sql = sql_fmt.format(table_name, ",".join(table_columns), tmp_arg)
                cur.execute(sql, table_data)
            conn.commit()
            cur.close()
            self._clear_db(conn)
            self._rebuild_db(conn)
            conn.close()
        except:
            write_log("数据写入失败", traceback.format_exc(), _level='error', color='red')
            return


    def _clear_db(self, conn: sqlite3.Connection):
        now = int(time.time())
        if now - self.last_clear_time < 3600:
            return

        exp_time = now - self.data_day() * 24 * 3600
        cur = conn.cursor()
        delete_sql_fmt = "DELETE FROM `{}` WHERE `addtime` < ?"
        for table_name in ("diskio", "cpuio", "network", "load_average", "process_top_list"):
            sql = delete_sql_fmt.format(table_name)
            cur.execute(sql, (exp_time,))

        conn.commit()
        cur.close()

    # 每隔 7 天，执行一次VACUUM，重建索引，减小数据库文件大小
    @staticmethod
    def _rebuild_db(conn: sqlite3.Connection):
        system_vacuum_file = "{}/data/system_vacuum.pl".format(PANEL_PATH)
        do_vacuum = False
        if not os.path.exists(system_vacuum_file):
            write_file(system_vacuum_file, str(int(time.time())))
            do_vacuum = True
        elif os.path.getmtime(system_vacuum_file) < time.time() - 86400 * 7:
            write_file(system_vacuum_file, str(int(time.time())))
            do_vacuum = True
        if do_vacuum:
            write_log("开始重建数据库")
            conn.execute('VACUUM', ())

    @staticmethod
    def _cut_top_list(process_list: List[Dict[str, Any]], *sort_key: str, top_num: int=5) -> List[Dict[str, Any]]:
        # 对进程列表(len = M)取top N, N 目前为 5, 先排序的时间复杂度为O(MlogM) , 使用heapq.nlargest进行优化，时间复杂度为O(M)
        if not process_list or not sort_key:
            return []

        try:
            # 如果只有一个排序键，直接使用该键
            if len(sort_key) == 1:
                return heapq.nlargest(top_num, process_list, key=lambda x: x.get(sort_key[0], 0))
            else:
                # 多个排序键，创建复合排序键
                return heapq.nlargest(top_num, process_list, key=lambda x: tuple(x.get(k, 0) for k in sort_key))
        except (TypeError, ValueError):
            err = traceback.format_exc()
            write_log("数据处理异常", err, _level="error", color="red")
            # 如果排序过程中出现异常，返回空列表
            return []

    def _get_disk_io(self) -> Optional[Dict]:
        if not os.path.exists('/proc/diskstats'):
            return None
        try:
            disk_io = psutil.disk_io_counters()
            if not disk_io:
                return None
            ret = {
                'read_count': disk_io.read_count,
                'write_count': disk_io.write_count,
                'read_bytes': disk_io.read_bytes,
                'write_bytes': disk_io.write_bytes,
                'read_time': disk_io.read_time,
                'write_time': disk_io.write_time,
                'timestamp': time.time()
            }
            if not self.last_disk_io:
                self.last_disk_io = ret
                return None

            diff_t = ret["timestamp"] - self.last_disk_io["timestamp"]
            res = {
                'read_count': int((ret["read_count"] - self.last_disk_io["read_count"]) / diff_t),
                'write_count': int((ret["write_count"] - self.last_disk_io["write_count"]) / diff_t),
                'read_bytes': int((ret["read_bytes"] - self.last_disk_io["read_bytes"]) / diff_t),
                'write_bytes': int((ret["write_bytes"] - self.last_disk_io["write_bytes"]) / diff_t),
                'read_time': int((ret["read_time"] - self.last_disk_io["read_time"]) / diff_t),
                'write_time': int((ret["write_time"] - self.last_disk_io["write_time"]) / diff_t),
            }
            self.last_disk_io = ret
            return res
        except Exception as e:
            write_log("获取磁盘IO失败: {}".format(str(e)), traceback.format_exc(), _level='error', color='red')
            return None

    def _get_network_io(self) -> Optional[Dict]:
        try:
            network_io = psutil.net_io_counters(pernic=True)
            ret = {
                'total_up': sum(v.bytes_sent for v in network_io.values()),
                'total_down': sum(v.bytes_recv for v in network_io.values()),
                'timestamp': time.time(),
                'down_packets': {
                    k:  v.bytes_recv for k, v in network_io.items()
                },
                'up_packets': {
                    k:  v.bytes_sent for k, v in network_io.items()
                }
            }
            if not self.last_network_io:
                self.last_network_io = ret
                return None
            diff_t = (ret["timestamp"] - self.last_network_io["timestamp"]) * 1024  # * 1024 转化为KB
            res = {
                'up': round((ret['total_up'] - self.last_network_io['total_up']) / diff_t, 2),
                'down': round((ret['total_down'] - self.last_network_io['total_down']) / diff_t, 2),
                'total_up': ret['total_up'],
                'total_down': ret['total_down'],
                'down_packets': {
                    k: round((v - self.last_network_io['down_packets'].get(k, 0)) / diff_t, 2)
                    for k, v in ret['down_packets'].items()
                },
                'up_packets': {
                    k: round((v - self.last_network_io['up_packets'].get(k, 0)) / diff_t, 2)
                    for k, v in ret['up_packets'].items()
                }
            }
            self.last_network_io = ret
            return res
        except Exception as e:
            write_log("获取网络IO失败: {}".format(str(e)), traceback.format_exc(), _level='error', color='red')
            return None

    def _get_process_list(self) -> List[Dict]:
        self._load_cache()
        pids = psutil.pids()
        timer = getattr(time, "monotonic", time.time)
        ret_dict = {}
        process_list = []
        cpu_num = psutil.cpu_count() or 1
        for pid in pids:
            if pid == self.this_pid:
                continue
            try:
                p = psutil.Process(pid)
                with p.oneshot():
                    last_cache = self._last_cache.get(pid, None)
                    if last_cache and last_cache.c_time != p.create_time():
                        last_cache = None

                    p_cpu_time = p.cpu_times()
                    cpu_time = p_cpu_time.system + p_cpu_time.user
                    io_counters = p.io_counters()
                    memory_info = p.memory_info()
                    net_works = _proc_net_zero
                    if pid and self._process_net and pid in self._process_net:
                        net_works: _ProcNet = self._process_net[pid]
                    ret = _Proc(pid, p.create_time(), timer(), cpu_time, io_counters.read_bytes, io_counters.write_bytes, *(net_works[1:]))
                    ret_dict[ret.pid] =  ret
                    if not last_cache:
                        # 初次处理的进程，不计算后续的资源使用率
                        continue
                    diff_t = ret.st_timer - last_cache.st_timer
                    if diff_t <= 0:
                        continue

                    process_info = {
                        # cpu_percent 计算综合资源占用，而不是类似于top的单核资源暂用
                        'cpu_percent':max(round((ret.cpu_time - last_cache.cpu_time) * 100 / diff_t/ cpu_num, 2), 0),
                        'memory': memory_info.rss,
                        'disk_read': max(0, int((ret.disk_read - last_cache.disk_read)/diff_t)),
                        'disk_write': max(0, int((ret.disk_write - last_cache.disk_write)/diff_t)),
                        'up': max(0, int((ret.net_up - last_cache.net_up)/diff_t)),
                        'down': max(0, int((ret.net_down - last_cache.net_down)/diff_t)),
                        'up_package': max(0, int((ret.net_up_packets - last_cache.net_up_packets) / diff_t)),
                        'down_package': max(0, int((ret.net_down_packets - last_cache.net_down_packets) / diff_t)),
                        'pid': ret.pid,
                        'name': p.name(),
                        'cmdline': ' '.join(filter(lambda x: x, p.cmdline())),
                        'username': p.username(),
                        'create_time': ret.c_time,
                        'connect_count': len(p.net_connections() if hasattr(p, "net_connections") else  p.connections())
                    }
                    process_info["net_total"] = process_info["up"] + process_info["down"]
                    process_info["disk_total"] = process_info["disk_read"] + process_info["disk_write"]
                    if not process_info["net_total"] and not process_info["disk_total"] and not process_info["cpu_percent"]:
                        continue
                    process_list.append(process_info)
            except psutil.NoSuchProcess:  # 进程不存在
                continue
            except Exception as e:
                write_log("获取进程信息失败: {}".format(str(e)), traceback.format_exc(), _level='error', color='red')
                continue
        self._last_cache = ret_dict
        self._save_cache()
        return process_list

    @staticmethod
    def _get_cpu_percent() -> float:
        return psutil.cpu_percent()

    @staticmethod
    def _get_load_average() -> Dict:
        c = os.getloadavg()
        limit = psutil.cpu_count() * 2
        return {
            'one': float(c[0]),
            'five': float(c[1]),
            'fifteen': float(c[2]),
            'max': limit,
            'limit': limit,
            'safe': limit * 0.75,
            'pro': round(min(float(c[0]) / limit * 100, 100), 2)
        }

    # 获取内存使用率
    @staticmethod
    def _get_mem_usage() -> float:
        try:
            mem = psutil.virtual_memory()
            total = mem.total
            used = mem.total - mem.free - mem.cached - mem.buffers
            return round(used / total * 100, 2)
        except:
            write_log("获取内存使用率失败", traceback.format_exc(), _level='error', color='red')
            return 1


class _Script:
    __slots__ = ('name', 'cmd', 'interval', '_is_first', '_ident')

    def __init__(self, name: str, cmd: str, interval: int):
        self.name = name
        self.cmd = cmd
        self.interval = interval
        self._is_first = True
        self._ident = 0

    def first(self) -> int:
        if self._is_first:
            self._is_first = False
            return int(time.time())
        else:
            return 0

    def get_next_time(self) -> int:
        """
        获取下一次执行时间
        """
        return int(time.time() + self.interval)

    def get_ident(self) -> int:
        """
        获取任务标识
        """
        return self._ident

    def set_ident(self, ident: int):
        """
        设置任务标识
        """
        self._ident = ident

    def run(self):
        """
        运行任务
        """
        write_log("执行任务: {}".format(self.name))
        try:
            # write_log("cmd:", self.cmd, _level='debug')
            os.system(self.cmd)
        except Exception as e:
            write_log("执行{}任务失败: {}".format(self.name, str(e)), traceback.format_exc(), _level='error', color='red')


class _ScriptService:

    def __init__(self):
        self.heap: List[Tuple[int, int, _Script]] = []
        self.lock = threading.Lock()
        self._tasks: List[_Script] = []

    def register(self, name: str, cmd: str, interval: int):
        """注册任务"""
        task = _Script(name, cmd, interval)
        self._tasks.append(task)
        return task

    def register_scripts(self, *scripts: _Script):
        """注册任务"""
        for script in scripts:
            if script in self._tasks:
                continue
            self._tasks.append(script)

    def init_tasks(self):
        """添加任务到队列"""
        with self.lock:
            for idx, task in enumerate(self._tasks):
                next_execution_time = task.first() + idx*3
                heapq.heappush(self.heap, (next_execution_time, task.get_ident(), task))
        self._tasks = None

    def start(self):
        """运行任务队列"""
        self.init_tasks()
        while True:
            if not self.heap:
                time.sleep(1)
                continue

            with self.lock:
                # 取出最近任务
                next_time, _, task = heapq.heappop(self.heap)

            # 计算等待时间
            current_time = int(time.time())
            wait_time = max(0, next_time - current_time)

            # 等待执行
            if wait_time > 0:
                time.sleep(wait_time)

            # 执行任务
            task.run()

            # 获取下一次执行时间重新入队
            try:
                next_execution_time = task.get_next_time()
                with self.lock:
                    heapq.heappush(self.heap, (next_execution_time, task.get_ident(), task))
            except Exception as e:
                # 如果无法获取下一次执行时间，任务不再重新入队
                write_log("获取{}任务下次执行时间失败: {}".format(task.name, str(e)), traceback.format_exc(), _level='error', color='red')
                pass


def start_scripts_service():
    check_panel_ssl = _Script(
        name="面板SSL证书监控",
        cmd='lets_info="{}/ssl/lets.info";[ -f "${{lets_info}}" ] && '
            'nohup {} {}/script/panel_ssl_task.py > /dev/null 2>&1 &'.format(PANEL_PATH, PY_BIN, PANEL_PATH),
        interval=3600)

    send_mail_time = _Script(
        name="邮件发送任务",
        cmd='nohup {} {}/script/mail_task.py > /dev/null 2>&1 &'.format(
            PY_BIN, PANEL_PATH
        ),
        interval=3600)

    class ProjectDemons(_Script):
        def __init__(self, ):
            super().__init__("项目守护进程", '', 120)
            self.cmd = 'nohup {} {}/script/project_daemon.py > /dev/null 2>&1 &'.format(
                PY_BIN, PANEL_PATH
            )

        def get_next_time(self) -> int:
            daemon_time_file ='{}/data/daemon_time.pl'.format(PANEL_PATH)
            if os.path.exists(daemon_time_file):
                time_out = int(read_file(daemon_time_file))
                if time_out < 10:
                    time_out = 10
                if time_out > 30 * 60:
                    time_out = 30 * 60
            else:
                time_out = 120

            return int(time.time() + time_out)

    project_demons = ProjectDemons()

    ssh_error_count_code = (
        'import sys; sys.path.insert(0, "{}/class"); import PluginLoader, public;'
        'PluginLoader.module_run("syslog", "task_ssh_error_count", public.dict_obj())'
    ).format(PANEL_PATH)

    task_ssh_error_count=_Script(
        name="SSH错误次数",
        cmd='nohup {} -c \'{}\' > /dev/null 2>&1 &'.format(
            PY_BIN, ssh_error_count_code
        ),
        interval=3600)

    check_panel_msg = _Script(
        name="面板消息提醒",
        cmd='nohup {py_bin} {panel_path}/script/check_msg.py > /dev/null 2>&1 &'.format(
            py_bin=PY_BIN, panel_path=PANEL_PATH
        ),
        interval=3600)

    push_msg = _Script(
        name="消息推送",
        cmd='nohup {py_bin} {panel_path}/script/push_msg.py > /dev/null 2>&1 &'.format(
            py_bin=PY_BIN, panel_path=PANEL_PATH
        ),
        interval=60)

    total_load_msg=_Script(
        name="面板负载均衡统计",
        cmd='nohup {py_bin} {panel_path}/script/total_load_msg.py > /dev/null 2>&1 &'.format(
            py_bin=PY_BIN, panel_path=PANEL_PATH
        ),
        interval=60)

    node_monitor=_Script(
        name="节点监控",
        cmd='nohup {py_bin} {panel_path}/script/node_monitor.py > /dev/null 2>&1 &'.format(
            py_bin=PY_BIN, panel_path=PANEL_PATH
        ),
        interval=60)

    check_safecloud_task = _Script(
        name="云安全扫描",
        cmd='nohup {py_bin} {panel_path}/script/warning_list.py > /dev/null 2>&1 &'.format(
            py_bin=PY_BIN, panel_path=PANEL_PATH
        ),
        interval=3600)

    start_daily = _Script(
        name="日报统计",
        cmd='nohup {py_bin} {panel_path}/script/daily.py > /dev/null 2>&1 &'.format(
            py_bin=PY_BIN, panel_path=PANEL_PATH
        ),
        interval=7200)

    flush_docker_hub_repos = _Script(
        name="同步Docker Hub镜像排行数据",
        cmd='nohup {} {}/class/btdockerModel/script/syncreposdb.py > /dev/null 2>&1 &'.format(
            PY_BIN, PANEL_PATH
        ),
        interval=86400)

    # 站点任务
    # 网站到期检查 （docker网站到期检查也在内）
    site_task = _Script(
        name="站点任务",
        cmd='nohup {} {}/script/site_task.py > /dev/null 2>&1 &'.format(
            PY_BIN, PANEL_PATH
        ),
        interval=900)

    # 原check502Task
    # 包含
    # 检查下载节点状态 -> node_url.pl
    # 自动备份面板数据 -> auto_backup_panel
    # Session过期处理
    # SSL证书自动部署
    # 邮件发送数量上传
    check_502_task = _Script(
        name="检查502任务",
        cmd='nohup {} {}/script/task_script_extension.py {} > /dev/null 2>&1 &'.format(
            PY_BIN, PANEL_PATH, 'check502Task'
        ),
        interval=900)

    refresh_domain_cache = _Script(
        name="刷新域名缓存",
        cmd='nohup {} {}/script/task_script_extension.py {} > /dev/null 2>&1 &'.format(
            PY_BIN, PANEL_PATH, 'refresh_domain_cache'
        ),
        interval=3610)

    update_software_list = _Script(
        name="更新软件列表",
        cmd='nohup {} {}/script/task_script_extension.py {} > /dev/null 2>&1 &'.format(
            PY_BIN, PANEL_PATH, "update_software_list"
        ),
        interval=1810)

    # 邮件日志事件是一个后台运行的服务，此处仅做守护
    maillog_event = _Script(
        name="邮件日志事件",
        cmd='nohup {} {}/script/task_script_extension.py {} > /dev/null 2>&1 &'.format(
            PY_BIN, PANEL_PATH, "maillog_event"
        ),
        interval=600)

    _scripts = (
        check_panel_ssl,
        send_mail_time,
        project_demons,
        task_ssh_error_count,
        check_panel_msg,
        push_msg,
        total_load_msg,
        node_monitor,
        check_safecloud_task,
        start_daily,
        flush_docker_hub_repos,
        site_task,
        check_502_task,
        refresh_domain_cache,
        update_software_list,
        maillog_event,
    )

    while True:
        try:
            for idx, _script in enumerate(_scripts):
                _script._is_first = True
                _script.set_ident(idx)

            s = _ScriptService()
            s.register_scripts(*_scripts)
            s.start()
            del s
        except Exception as e:
            err = traceback.format_exc()
            write_log("任务调度服务异常: {}".format(e), err, _level="ERROR", color='red')
            time.sleep(5)


def panel_daemon_start():
    _BTPanelDaemonService().start()

def sys_start():
    write_log("监控数据采集服务已启动")
    _SystemService().start(interval=60)

def run_tasks_list_start():
    write_log("延迟任务列表服务已启动")
    _TaskListService().start()

def bt_task_start():
    write_log("BT任务服务已启动")
    _BTTaskService().start()


def main():
    main_pid = os.path.join(PANEL_PATH, 'logs/task.pid')
    if os.path.exists(main_pid):
        os.system("kill -9 $(cat {}) &> /dev/null".format(main_pid))
    pid = os.fork()
    if pid:
        sys.exit(0)

    os.setsid()

    _pid = os.fork()
    if _pid:
        write_file(main_pid, str(_pid))
        sys.exit(0)

    sys.stdout.flush()
    sys.stderr.flush()

    # 重定向标准输出和错误到日志文件
    try:
        so = open(TASK_LOG_FILE, 'a+')
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(so.fileno(), sys.stderr.fileno())
    except Exception as e:
        print(f"重定向输出失败: {e}")

    write_log('BT-Task服务已启动')
    time.sleep(2)
    sys_start_th = threading.Thread(target=sys_start, daemon=True)
    sys_start_th.start()
    threading.Thread(target=start_scripts_service, daemon=True).start()
    threading.Thread(target=panel_daemon_start, daemon=True).start()
    threading.Thread(target=run_tasks_list_start, daemon=True).start()
    threading.Thread(target=bt_task_start, daemon=True).start()
    _SoftService().start()





if __name__ == "__main__":
    main()
