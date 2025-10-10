# coding: utf-8
#  + -------------------------------------------------------------------
# | 宝塔Linux面板
#  + -------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http:#bt.cn) All rights reserved.
#  + -------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
#  + -------------------------------------------------------------------
import json
import time
import traceback
from datetime import datetime

import public, db, re, os, firewalls, sys
import subprocess
import ipaddress

try:
    from BTPanel import session
except:
    pass
os.chdir('/www/server/panel')
sys.path.insert(0, 'class/')
import crontab
panel_path = '/www/server/panel'

class ftp:
    __runPath = None
    config_path = '/www/server/panel/data/ftp_push_config.json'


    def __init__(self):
        self.__runPath = '/www/server/pure-ftpd/bin'
        self.migrate_file(panel_path)
        self.filepath="{}/data/ftp_types.json".format(panel_path)

    # 兼容旧的分类文件   
    def migrate_file(self,panel_path):
        import shutil
        old_filepath = "{}/class/ftp_types.json".format(panel_path)
        new_filepath = "{}/data/ftp_types.json".format(panel_path)

        # 检查旧文件是否存在
        if os.path.exists(old_filepath) and not os.path.exists(new_filepath):
            # 创建目标目录（如果不存在）
            os.makedirs(os.path.dirname(new_filepath), exist_ok=True)
            # 复制旧文件内容到新文件
            shutil.copyfile(old_filepath, new_filepath)
            # 删除旧文件
            os.remove(old_filepath)
        else:
            pass

    def AddUser(self, get):
        """
        @name 添加FTP用户
        @param path 保存路径
        @param ftp_username FTP用户名
        @param ftp_password FTP密码
        @param ps 备注
        """
        try:
            if not os.path.exists('/www/server/pure-ftpd/sbin/pure-ftpd'):
                return public.returnMsg(False, '请先到软件商店安装Pure-FTPd服务')
            import files, time
            fileObj = files.files()

            get['ftp_username'] = get['ftp_username'].replace(' ', '')
            if re.search("\W+", get['ftp_username']):
                return {
                    'status': False,
                    'code': 501,
                    'msg': public.getMsg('FTP_USERNAME_ERR_T')
                }
            if len(get['ftp_username']) < 3:
                return {
                    'status': False,
                    'code': 501,
                    'msg': public.getMsg('FTP_USERNAME_ERR_LEN')
                }
            if not fileObj.CheckDir(get['path']):
                return {
                    'status': False,
                    'code': 501,
                    'msg': public.getMsg('FTP_USERNAME_ERR_DIR')
                }
            if public.M('ftps').where('name=?',
                                      (get.ftp_username.strip(),)).count():
                return public.returnMsg(False, 'FTP_USERNAME_ERR_EXISTS',
                                        (get.ftp_username,))
            username = get['ftp_username'].strip()
            password = get['ftp_password'].strip()

            if len(password) < 6:
                return public.returnMsg(False, 'FTP密码长度不能少于6位!')
            get.path = get['path'].strip()
            get.path = get.path.replace("\\", "/")
            fileObj.CreateDir(get)
            public.ExecShell('chown www.www ' + get.path)
            command = 'echo -e "{}\n{}\n" | {}/pure-pw useradd "{}" -u www -d {}'.format(password,password,self.__runPath,username,get["path"])
            result = subprocess.run(command, shell=True, text=True, capture_output=True)
            if result.returncode != 0:
                return public.returnMsg(False, '执行命令添加用户失败: {}'.format(result.stderr))
            self.FtpReload()
            ps = public.xssencode2(get['ps'])
            if get['ps'] == '': ps = public.getMsg('INPUT_PS')
            addtime = time.strftime('%Y-%m-%d %X', time.localtime())

            pid = 0
            if hasattr(get, 'pid'): pid = get.pid
            public.M('ftps').add(
                'pid,name,password,path,status,ps,addtime',
                (pid, username, password, get.path, 1, ps, addtime))
            public.WriteLog('TYPE_FTP', 'FTP_ADD_SUCCESS', (username,))
            return public.returnMsg(True, 'ADD_SUCCESS')
        except Exception as ex:
            public.WriteLog('TYPE_FTP', 'FTP_ADD_ERR', (username, str(ex)))
            return public.returnMsg(False, 'ADD_ERROR')

    def get_quota_list(self):
        quota_dict = {}
        try:
            quota_conf = os.path.join(public.get_panel_path(), "config/quota_list.json")
            quota_dict = json.loads(public.readFile(quota_conf))
        except:
            pass
        return quota_dict

    def removeFTPAlerts(self, path):
        # 从配置文件获取所有路径的配额信息
        quota_dict = self.get_quota_list()
        if path in quota_dict:
            quota_id = quota_dict[path].get('quota_push', {}).get('id', None)
            
            if quota_id:
                # 更新 push.json
                self.update_push_json(quota_id)
                # 删除 quota_list.json 中的相关配额信息
                del quota_dict[path]
                self.update_quota_list(quota_dict)
                print("更新了 quota_list.json 和 push.json 文件。")
            else:
                print("该路径未配置 quota_push，未作更改。")
        else:
            print("无有效配额信息，未作更改。")

    def update_push_json(self, quota_id):
        json_file_path = '/www/server/panel/class/push/push.json'
        try:
            with open(json_file_path, 'r') as file:
                data = json.load(file)
            
            # 检查并删除 quota_push 部分
            keys_to_remove = [key for key, value in data['quota_push'].items() if value.get('id') == quota_id]
            for key in keys_to_remove:
                del data['quota_push'][key]

            # 将修改后的数据写回 JSON 文件
            with open(json_file_path, 'w') as file:
                json.dump(data, file, indent=4)
        except Exception as e:
            pass

    def update_quota_list(self, quota_dict):
        quota_conf = os.path.join(public.get_panel_path(), "config/quota_list.json")
        try:
            with open(quota_conf, 'w') as file:
                json.dump(quota_dict, file, indent=4)
        except Exception as e:
            pass


    # 删除用户
    def DeleteUser(self, get):
        try:
            username = get['username']
            id = get['id']
            query=public.M('ftps').where("id=? and name=?", (id, username,))
            path=query.getField('path')
            self.removeFTPAlerts(path)

            if query.count() == 0:
                return public.returnMsg(False, 'DEL_ERROR')
            public.ExecShell(self.__runPath + '/pure-pw userdel "' + username +
                             '"')
            self.FtpReload()
            public.M('ftps').where("id=?", (id,)).delete()
            public.WriteLog('TYPE_FTP', 'FTP_DEL_SUCCESS', (username,))
            return public.returnMsg(True, "DEL_SUCCESS")
        except Exception as ex:
            public.WriteLog('TYPE_FTP', 'FTP_DEL_ERR', (username, str(ex)))
            return public.returnMsg(False, 'DEL_ERROR')

    # 修改用户密码
    def SetUserPassword(self, get):
        try:
            id = get['id']
            username = get['ftp_username'].strip()
            password = get['new_password'].strip()
            if public.M('ftps').where("id=? and name=?", (id, username,)).count() == 0:
                return public.returnMsg(False, 'DEL_ERROR')
            if len(password) < 6:
                return public.returnMsg(False, 'FTP密码长度不能少于6位!')
            public.ExecShell(self.__runPath + '/pure-pw passwd "' + username +
                             '"<<EOF \n' + password + '\n' + password +
                             '\nEOF')
            self.FtpReload()
            public.M('ftps').where("id=?",
                                   (id,)).setField('password', password)
            public.WriteLog('TYPE_FTP', 'FTP_PASS_SUCCESS', (username,))
            return public.returnMsg(True, 'EDIT_SUCCESS')
        except Exception as ex:
            public.WriteLog('TYPE_FTP', 'FTP_PASS_ERR', (username, str(ex)))
            return public.returnMsg(False, 'EDIT_ERROR')
        
    def SetUser(self, get):
        try:
            id = get['id']
            username = get['ftp_username'].strip()
            password = get['new_password'].strip()
            path = get['path'].strip().replace("\\", "/")
            
            if public.M('ftps').where("id=? and name=?", (id, username)).count() == 0:
                return public.returnMsg(False, 'DEL_ERROR')
            
            if len(password) < 6:
                return public.returnMsg(False, 'FTP密码长度不能少于6位!')

            # 修改用户密码
            command = 'echo -e "{}\n{}\n" | {}/pure-pw passwd "{}"'.format(password,password,self.__runPath,username)
            result = subprocess.run(command, shell=True, text=True, capture_output=True)
            if result.returncode != 0:
                return public.returnMsg(False, '执行命令修改密码失败: {}'.format(result.stderr))

            public.M('ftps').where("id=?", (id,)).setField('password', password)
            public.WriteLog('TYPE_FTP', 'FTP_PASS_SUCCESS', (username,))
            
            # 修改用户目录
            subprocess.run('chown www.www {}'.format(path), shell=True, check=True)
            command = '{}/pure-pw usermod "{}" -d {}'.format(self.__runPath,username,path)
            result = subprocess.run(command, shell=True, text=True, capture_output=True)
            if result.returncode != 0:
                return public.returnMsg(False, '执行命令修改目录失败: {}'.format(result.stderr))

            public.M('ftps').where("id=?", (id,)).setField('path', path)

            self.FtpReload()
            return public.returnMsg(True, 'EDIT_SUCCESS')
        except Exception as ex:
            public.WriteLog('TYPE_FTP', 'FTP_PASS_ERR', (username, str(ex)))
            return public.returnMsg(False, 'EDIT_ERROR'+str(ex))
    def BatchSetUserPassword(self, get):
        try:
            if not hasattr(get, 'data') or not get.data:
                return public.returnMsg(False, '参数错误！')
            result = []
            data = json.loads(get.data)
            for i in data:
                try:
                    id = i['id']
                    username = i['ftp_username'].strip()
                    password = i['new_password'].strip()
                    if public.M('ftps').where("id=? and name=?", (id, username,)).count() == 0:
                        return public.returnMsg(False, 'DEL_ERROR')
                    if len(password) < 6:
                        return public.returnMsg(False, 'FTP密码长度不能少于6位!')
                    public.ExecShell(self.__runPath + '/pure-pw passwd "' + username +
                                     '"<<EOF \n' + password + '\n' + password +
                                     '\nEOF')
                    public.M('ftps').where("id=?", (id,)).setField('password', password)
                    public.WriteLog('TYPE_FTP', 'FTP_PASS_SUCCESS', (username,))
                    result.append({'ftp_username': i['ftp_username'], 'status': True})
                except:
                    result.append({'ftp_username': i['ftp_username'], 'status': False})
            self.FtpReload()
            return result
        except:
            return public.returnMsg(False, '批量修改失败！')

    # 设置用户状态
    def SetStatus(self, get):
        msg = public.getMsg('OFF')
        if get.status != '0': msg = public.getMsg('ON')
        try:
            id = get['id']
            username = get['username']
            status = get['status']
            if public.M('ftps').where("id=? and name=?", (id, username,)).count() == 0:
                return public.returnMsg(False, 'DEL_ERROR')
            if int(status) == 0:
                public.ExecShell(self.__runPath + '/pure-pw usermod "' +
                                 username + '" -r 127.0.0.1')
            else:
                public.ExecShell(self.__runPath + '/pure-pw usermod "' +
                                 username + "\" -r ''")
            self.FtpReload()
            public.M('ftps').where("id=?", (id,)).setField('status', status)
            public.WriteLog('TYPE_FTP', 'FTP_STATUS', (msg, username))
            return public.returnMsg(True, 'SUCCESS')
        except Exception as ex:
            public.WriteLog('TYPE_FTP', 'FTP_STATUS_ERR',
                            (msg, username, str(ex)))
            return public.returnMsg(False, 'FTP_STATUS_ERR', (msg,))

    '''
     * 设置FTP端口
     * @param Int _GET['port'] 端口号
     * @return bool
     '''

    def setPort(self, get):
        try:
            port = get['port'].strip()
            if not port: return public.returnMsg(False, 'FTP端口不能为空')
            if int(port) < 1 or int(port) > 65535:
                return public.returnMsg(False, 'PORT_CHECK_RANGE')
            data = public.ExecShell("ss -nultp|grep -w '%s '" % port)[0]
            if data: return public.returnMsg(False, "PORT_CHECK_EXISTS", [port])
            file = '/www/server/pure-ftpd/etc/pure-ftpd.conf'
            conf = public.readFile(file)
            rep = u"\n#?\s*Bind\s+[0-9]+\.[0-9]+\.[0-9]+\.+[0-9]+,([0-9]+)"
            # preg_match(rep,conf,tmp)
            conf = re.sub(rep, "\nBind        0.0.0.0," + port, conf)
            public.writeFile(file, conf)
            public.ExecShell('/etc/init.d/pure-ftpd restart')
            public.WriteLog('TYPE_FTP', "FTP_PORT", (port,))
            # 添加防火墙
            # data = ftpinfo(port=port,ps = 'FTP端口')
            get.port = port
            get.ps = public.getMsg('FTP_PORT_PS')
            firewalls.firewalls().AddAcceptPort(get)
            session['port'] = port
            return public.returnMsg(True, 'EDIT_SUCCESS')
        except Exception as ex:
            public.WriteLog('TYPE_FTP', 'FTP_PORT_ERR', (str(ex),))
            return public.returnMsg(False, 'EDIT_ERROR')

    # 重载配置
    def FtpReload(self):
        public.ExecShell(
            self.__runPath +
            '/pure-pw mkdb /www/server/pure-ftpd/etc/pureftpd.pdb')

    def get_login_logs(self, get):
        import ftplog
        ftpobj = ftplog.ftplog()
        return ftpobj.get_login_log(get)

    def get_action_logs(self, get):
        import ftplog
        ftpobj = ftplog.ftplog()
        return ftpobj.get_action_log(get)

    def set_ftp_logs(self, get):
        import ftplog
        ftpobj = ftplog.ftplog()
        result = ftpobj.set_ftp_log(get)
        return result

    def get_cron_config(self, get):
        try:
            if not hasattr(get, 'id') and get['id']:
                return public.returnMsg(False, '请传入ftp的id！')
            if not os.path.exists(self.config_path):
                public.writeFile(self.config_path,
                                 json.dumps({'0': [], '1': [], '2': [], '3': [], 'channel': ''}))
            data = json.loads(public.readFile(self.config_path))
            id_data = {}
            for i, j in data.items():
                if i == 'channel':
                    continue
                for k in j:
                    if int(get.id) == k['id']:
                        k['push_action'] = i
                        id_data = k
                        break
            if not id_data:
                return {'id': get.id, 'push_action': '0', 'end_time': '0', 'channel': data['channel']}
            id_data['channel'] = data['channel']
            return id_data
        except:
            return {'id': get.id, 'push_action': '0', 'end_time': '0', 'channel': data.get('channel', '')}

    def set_cron_config(self, get):
        try:
            if os.path.exists(self.config_path):
                config = json.loads(public.readFile(self.config_path))
            else:
                config = {'0': [], '1': [], '2': [], '3': [], 'channel': ''}
            if not hasattr(get, 'id') and get['id']:
                return public.returnMsg(False, '参数错误！')
            for id in json.loads(get.id):
                data = {}
                for i, j in config.items():
                    if i == 'channel':
                        continue
                    for k in j:
                        print(i, j)
                        if k['id'] == int(id):
                            j.remove(k)
                data['id'] = int(id)
                if hasattr(get, 'end_time') and get['end_time'] != '':
                    data['end_time'] = get['end_time']
                if hasattr(get, 'show') and get['show'] != '':
                    data["show"] = get["show"] == "true"
                data['is_push'] = False
                if len(data) < 3:
                    return public.returnMsg(False, '参数不足！')
                config.setdefault(get.push_action, []).append(data)
                config['channel'] = get.channel
            # self.create_task()
            if len(config.get("1", [])) + len(config.get("2", [])) + len(config.get("3", [])) > 0:
                if "/www/server/panel" not in sys.path:
                    sys.path.insert(0, "/www/server/panel")

                from mod.base.push_mod.manager import PushManager
                push_manager = PushManager()
                res = push_manager.set_task_conf_data({
                    "template_id": "102",
                    "task_data": {
                        "status": True,
                        "sender": config["channel"].split(","),
                        "task_data": {},
                        "number_rule": {
                            "day_num": 1
                        }
                    }
                })

            public.writeFile(self.config_path, json.dumps(config))
            return public.returnMsg(True, '设置成功！')
        except:
            public.print_error()
            return public.returnMsg(False, '设置失败！')

    def send_notification(self, title, msg, channel):
        data = public.get_push_info(title, msg)
        for channel in channel.split(','):
            obj = public.init_msg(channel)
            obj.send_msg(data['msg'])

    # 创建计划任务
    def create_task(self):
        id = public.M('crontab').where("name=?", "【勿删】ftp定时检测密码有效期任务").getField('id')
        if id:
            return
        pypath = '/www/server/panel/class/ftp.py'
        p = crontab.crontab()
        args = {
            "name": "【勿删】ftp定时检测密码有效期任务",
            "type": "day",
            "where1": '',
            "hour": 1,
            "minute": 30,
            "week": "",
            "sType": "toShell",
            "sName": "",
            "backupTo": "localhost",
            "save": '',
            "sBody": "btpython {}".format(pypath),
            "urladdress": "undefined"
        }
        p.AddCrontab(args)

    # 删除计划任务
    def remove_task(self):
        p = crontab.crontab()
        id = public.M('crontab').where("name=?", "【勿删】ftp定时检测密码有效期任务").getField('id')
        args = {"id": id}
        p.DelCrontab(args)

    def run(self):
        if not os.path.exists(self.config_path):
            print('配置文件不存在,关闭警告！')
            self.remove_task()
            return
        config = json.loads(public.readFile(self.config_path))
        if not config:
            print('无任务，关闭任务！')
            self.remove_task()
            return
        try:
            for push_achion, data in config.items():
                msg = []
                title = ''
                if push_achion == '0' or push_achion == 'channel':
                    continue
                for i in data:
                    uname = public.M('ftps').where("id=?", (i['id'],)).getField('name')
                    pwd = public.M('ftps').where("id=?", (i['id'],)).getField('password')
                    print(uname, pwd)
                    if not (uname and pwd):
                        continue
                    now = time.time()
                    end_time = int(i['end_time'])
                    if int(end_time) < int(now):
                        if not i['is_push']:
                            if push_achion == '1':
                                i['is_push'] = True
                                title = 'FTP密码修改提醒'
                                msg.append('【{}】账号请及时【修改】FTP密码！'.format(uname))
                            if push_achion == '2':
                                i['is_push'] = True
                                title = 'FTP服务停止提醒'
                                if self.SetStatus(public.to_dict_obj({'id': i['id'], 'username': uname, 'status': 0}))['status']:
                                    msg.append('【{}】账号【已停止】请及时处理！'.format(uname))
                                else:
                                    msg.append('【{}】账号【停止失败】请及时处理！'.format(uname))
                            if push_achion == '3':
                                new_pwd = public.GetRandomString(12)
                                res = self.SetUserPassword(public.to_dict_obj({'id': i['id'], 'ftp_username': uname, 'new_password': new_pwd}))
                                i['is_push'] = True
                                title = 'FTP服务自动改密提醒'
                                if res['status']:
                                    msg.append('【{}】账号已将密码改为【{}】！'.format(uname, new_pwd))
                                else:
                                    msg.append('【{}】账号密码修改失败！'.format(uname))
                if title:
                    self.send_notification(title, msg, config['channel'])
            public.writeFile(self.config_path, json.dumps(config))
        except:
            print(traceback.format_exc())
            public.writeFile(self.config_path, json.dumps(config))
    def kb_to_mb_or_gb(self, size_kb):
        """
        将大小从KB转换为更适合的单位，保持输出格式简单。
        """
        if not size_kb.isdigit():
            return "{}KB".format(size_kb)  # 如果不是数字，返回原始值并附加"KB"
        
        size_kb = int(size_kb)
        if size_kb < 1024:
            return "{}KB".format(size_kb)
        elif size_kb < 1048576:  # 小于1GB的KB数
            size_mb = size_kb / 1024
            return "{}MB".format(int(size_mb))  # 只保留整数部分并返回
        else:
            size_gb = size_kb / 1048576
            return "{}GB".format(int(size_gb))  # 只保留整数部分并返回
        
    def GetFtpUserAccess(self, get):
        try:
            username = get['username']
            cmd = self.__runPath + '/pure-pw show "' + username + '"'
            try:
                result = subprocess.check_output(cmd, shell=True, text=True)
            except Exception as e:
                if "returned non-zero exit status 16" in str(e):
                    user_info = public.M('ftps').where('name=?', (username,)).field('password, path').find()
                    if not user_info:
                        return public.returnMsg(False, '用户信息不存在，请重新创建用户')
                    password = user_info['password']
                    user_path = user_info[' path'].strip()  # 修正键名并去掉空格
                    # 重新创建用户
                    command = 'echo -e "{}\n{}\n" | {}/pure-pw useradd "{}" -u www -d {}'.format(password, password, self.__runPath, username, user_path)
                    result = subprocess.run(command, shell=True, text=True, capture_output=True)
                    # if result.returncode != 0:
                    #     return public.returnMsg(False, '执行命令添加用户命令失败: {result.stderr}')
                    self.FtpReload()
            # 对结果进行处理
            result_lines = result.split('\n')
            result_dict = {}  # 创建一个空字典来存储结果
            for line in result_lines:
                if line:
                    key, value = line.split(':', 1)
                    key = key.lower().strip()  # 将键转换为小写
                    key = '_'.join(key.split())  # 使用一个下划线替换所有空格
                    # 如果键在指定的列表中，就只保留数字，并添加单位
                    if key in ["download_bandwidth", "upload_bandwidth", "max_size"]:
                        numeric_value = ''.join(filter(str.isdigit, value.strip()))
                        if "Mb" in value:
                            value = numeric_value+"MB"
                        else:
                            value = self.kb_to_mb_or_gb(numeric_value)  # 调用辅助函数进行转换

                    elif key in ["ratio","time_restrictions","max_files","max_sim_sessions"]:
                        value = value.split()[0]  
                        # 如果值只包含数字 "0"，则将其设置为空
                        if all(char == "0" for char in value.replace("-", "")):
                            value = ""
                        # 如果 "ratio" 的值为 "0:0"，则将其设置为空
                        if key == "ratio" and value == "0:0":
                            value = ""
                    else:
                        value = value.strip()  # 去掉值前后的空格
                    # 如果值为 "0MB" 或 "0KB"，则将其设置为空
                    if value in ["0MB", "0KB"]:
                        value = ""
                    result_dict[key] = value  # 添加到字典中
            return {"status": True, "msg": "获取ftp用户权限成功","data":result_dict}
        except Exception as e:
            public.WriteLog('TYPE_FTP', '获取ftp用户权限失败', (username, str(e)))
            return {"status": False, "msg": '获取ftp用户权限失败'+str(e)}


    def ModifyFtpUserAccess(self, get):
        
        try:
            username = get['username']
            # 构建修改用户权限的命令
            cmd = self.__runPath + f'/pure-pw usermod "{username}"'           
            # 解析用户提交的权限参数
            download_bandwidth = get.get('download_bandwidth', '0KB')
            upload_bandwidth = get.get('upload_bandwidth', '0KB')
            max_size = get.get('max_size', '0MB')

            if download_bandwidth[-2:].lower() == 'mb':
                download_bandwidth = str(int(download_bandwidth[:-2]) * 1024) + 'KB'
            elif download_bandwidth[-2:].lower() == 'gb':
                download_bandwidth = str(int(download_bandwidth[:-2]) * 1024 * 1024) + 'KB'

            if  upload_bandwidth[-2:].lower() == 'mb':
                upload_bandwidth = str(int(upload_bandwidth[:-2]) * 1024) + 'KB'
            elif  upload_bandwidth[-2:].lower() == 'gb':
                upload_bandwidth = str(int(upload_bandwidth[:-2]) * 1024 * 1024) + 'KB'

            if max_size[-2:].lower() == 'gb':
                max_size = str(int(upload_bandwidth[:-2]) * 1024 * 1024) + 'MB'

            max_files = get.get('max_files', 0)
            ratio = get.get('ratio')
            if ratio:
                upload_ratio, download_ratio = ratio.split(':')
                if int(upload_ratio)==0 or int (download_ratio)==0 :
                   return public.returnMsg(False,'上传和下载比率设置不正确')
                cmd += f' -q {upload_ratio} -Q {download_ratio}'
            else:
                pass
            allowed_local_ips = get.get('allowed_local_ips', '')
            denied_local_ips = get.get('denied_local_ips', '')
            allowed_client_ips = get.get('allowed_client_ips', '')
            denied_client_ips = get.get('denied_client_ips', '')
            # print(get.get('time_restrictions'))
            time_restrictions = get.get('time_restrictions', '0000-2359')
            if  time_restrictions=="0000-0000":
                return public.returnMsg(False, "不能将时间限制设置为0000-0000")
            max_sim_sessions = get.get('max_sim_sessions', '0')
            # 验证 IP 地址的格式
            for ip in [allowed_local_ips, denied_local_ips, allowed_client_ips, denied_client_ips]:
                if ip:
                    try:
                        ipaddress.ip_address(ip)
                    except ValueError:
                        return public.returnMsg(False, 'IP 地址格式不正确')

            # 只有当值不为默认值时，才添加到命令字符串中
            if download_bandwidth and download_bandwidth != '0':
                cmd += f' -t {download_bandwidth[:-2]}'
            if upload_bandwidth and upload_bandwidth != '0':
                cmd += f' -T {upload_bandwidth[:-2]}'
            if max_files:
                cmd += f' -n {max_files}'
            if max_size and max_size != '0':
                cmd += f' -N {max_size[:-2]}'             
            # 时间限制
            if time_restrictions :
                cmd += f' -z {time_restrictions}'
            if max_sim_sessions:
                cmd += f' -y {max_sim_sessions}'
            
            # 处理允许和禁止的IP地址
            if allowed_local_ips:
                cmd += f' -i {allowed_local_ips}'
            else:
                cmd += f' -i ""'
            

            if denied_local_ips:
                cmd += f' -I {denied_local_ips}'
            else:
                cmd += f' -I ""'

            if allowed_client_ips:
                cmd += f' -r {allowed_client_ips}'
            else:
                cmd += f' -r ""'

            if denied_client_ips:
                cmd += f' -R {denied_client_ips}'
            else:
                cmd += f' -R ""'
            # 执行命令
            subprocess.check_call(cmd, shell=True)
            
            # 重载ftp
            public.ExecShell("/www/server/pure-ftpd/bin/pure-pw mkdb /www/server/pure-ftpd/etc/pureftpd.pdb")

            # 返回成功消息
            return public.returnMsg(True, 'EDIT_SUCCESS')
        except Exception as e:
            # public.WriteLog('TYPE_FTP', 'FTP_ACCESS_MODIFY_ERR', (username, str(e)))
            return public.returnMsg(False, 'EDIT_ERROR'+str(e))



    def check_and_create_json(self,default_data={"types": []}):
        """检查JSON文件是否存在，如果不存在则创建并初始化它"""
        if not os.path.exists(self.filepath):
            self.save_json_file(default_data)
            return default_data  # 返回初始化数据以供使用

    def load_json_file(self):
        """加载JSON文件"""
        return self.check_and_create_json()


    def check_and_create_json(self, default_data={"types": []}):
        """检查JSON文件是否存在，如果不存在则创建并初始化它"""
        import os
        import json
        if not os.path.exists(self.filepath):
            self.save_json_file(default_data)
            return default_data  # 返回初始化数据以供使用
        else:
            # 文件已存在，加载并返回内容
            with open(self.filepath, 'r', encoding='utf-8') as file:
                return json.load(file)

    def save_json_file(self,data):
        """保存数据到JSON文件"""
        with open(self.filepath, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    def check_and_add_type_id_column(self):
        # 尝试查询ftps表中的type_id字段，以检查它是否存在
        query_result = public.M('ftps').field('type_id').select()
        if "no such column: type_id" in query_result:
            try:
                public.M('ftps').execute("ALTER TABLE 'ftps' ADD 'type_id' INTEGER", ())
            except Exception as e:
                print(e)

    def view_ftp_types(self, get):

        try:
            self.check_and_add_type_id_column()
            data = self.load_json_file()
            return public.returnMsg(True, data['types'])
        except Exception as e:
            return public.returnMsg(False, str(e))


    def is_name_exists(self, name):
        data = self.load_json_file()  # 加载现有数据
        for t in data.get('types', []):
            if t.get('ps') == name:
                return True  # 名字已存在
        return False  # 名字不存在

    def add_ftp_types(self, get):
        ps = get.ps
        if self.is_name_exists(ps):
            return public.returnMsg(False, "指定分类名称已存在!")
        data = self.load_json_file()  # 加载现有数据
        if not data:  # 如果文件为空或不存在，则初始化数据
            data = {"types": []}
            max_id = 0
        else:
            # 查找当前最大的id值
            max_id = max([t.get('id', 0) for t in data['types']], default=0)
        
        # 新分类的id为当前最大id值加1
        new_type = {"id": max_id + 1, "ps": ps}
        data['types'].append(new_type)  # 添加新的分类信息
        self.save_json_file(data)  # 保存更新后的数据到文件
        return public.returnMsg(True, "分类添加成功。")

    def delete_ftp_types(self, get):
        data = self.load_json_file()  # 加载现有数据
        if not data:  # 检查数据是否成功加载
            return public.returnMsg(False, "分类删除失败，数据加载失败。")
        
        # 查找并删除指定ID的分类
        found = False  # 标记是否找到并准备删除的分类
        for i, t in enumerate(data['types']):
            print(t.get('id'))
            if t.get('id') == int(get.id):
                del data['types'][i]  # 删除找到的分类
                found = True
                break  # 找到后即退出循环

        if found:
            self.save_json_file(data)  # 如果成功找到并删除，保存更改
            return public.returnMsg(True, "分类删除成功。")
        else:
            return public.returnMsg(False, "分类删除失败，未找到指定的分类。")

    def update_ftp_types(self, get):
        ps = get.ps
        if self.is_name_exists(ps):
            return public.returnMsg(False, "指定分类名称已存在!")
        data = self.load_json_file()  # 加载现有数据
        if data:
            for i, t in enumerate(data['types']):
                if t.get('id') == int(get.id):
                    # 更新分类信息
                    t['ps'] = ps
                    self.save_json_file(data)  # 保存更新后的数据
                    return public.returnMsg(True, "分类修改成功。")
            return public.returnMsg(False, "分类修改失败，未找到指定的分类。")
        else:
            return public.returnMsg(False, "分类修改失败，数据加载失败。")

    def set_ftp_type_by_id(self, get):
        try:
            # 尝试分割传入的字符串以处理多个数据库名
            ftp_names = get.ftp_names.split(',')
            
            # 准备数据库操作对象
            database_sql = public.M("ftps")
            
            
            # 遍历所有提供的数据库名
            for name in ftp_names:
                # 去除可能的前后空格
                name =name.strip()
                if name:  # 确保数据库名不为空
                    # 更新指定数据库名的type_id
                    result = database_sql.where("name=?", (name,)).setField("type_id", int(get.id))
            return public.returnMsg(True, "设置成功！")
        except Exception as e:
            # 通用异常处理
            return public.returnMsg(False, "设置失败！"+str(e))



    def find_ftp(self, get):
        try:
            id=get.id

            # 先从类型数据中找到name对应的id
            data = self.load_json_file()
            type_id = next((item['id'] for item in data['types'] if item['id'] == int(id)), None)
            # # 执行查询
            result=public.M("ftps").where("type_id=?", (type_id)).select()
            if result:
                return public.returnMsg(True, result)
            else:
                return public.returnMsg(True, [])
            return public.returnMsg(True, result)
        except Exception as e:
            return public.returnMsg(False, str(e))


if __name__ == "__main__":
    f = ftp()
    f.run()
