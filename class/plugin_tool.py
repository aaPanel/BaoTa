#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: baozi <baozi@bt.cn>
#-------------------------------------------------------------------

import os
import json
import shutil
import time
import zipfile
import re
from typing import Optional, Dict, Tuple, Union, List

import public
from pluginAuth import Plugin

_PLUGIN_DIR = "/www/server/panel/plugin"
_BACKUP_DIR = "/www/server/panel/data/plugin_settings"

if not os.path.exists(_BACKUP_DIR):
    os.makedirs(_BACKUP_DIR, 0o600)


class BaseZipOptions:
    _TARGET_PATH_LIST = []

    def _save_options(self, zip_file_name):
        """ 通用保存方法 """
        with zipfile.ZipFile(zip_file_name, "w") as z:
            for t, f, n in self._TARGET_PATH_LIST:
                if t == "f":
                    z.write(f, n)
                if t == "d":
                    base = os.path.dirname(f)
                    for root, dirs, files in os.walk(f):
                        for file in files:
                            file_path = os.path.join(root, file)
                            z.write(file_path, os.path.relpath(file_path, base))

    def _load_options(self, zip_file_name):
        """ 通用还原方法 """
        tmp_path = "/tmp/unzip_plugins_settings_" + str(int(time.time()))
        os.makedirs(tmp_path)
        with zipfile.ZipFile(zip_file_name, "r") as z:
            z.extractall(tmp_path)

        for t, f, n in self._TARGET_PATH_LIST:
            if os.path.exists(tmp_path + "/" + n):
                if t == "f":
                    if os.path.exists(f):
                        os.remove(f)
                    shutil.copyfile(tmp_path + "/" + n, f)
                if t == "d":
                    if os.path.exists(f):
                        shutil.rmtree(f)
                    shutil.copytree(tmp_path + "/" + n, f)

        shutil.rmtree(tmp_path)


class BasePluginSetting(BaseZipOptions):
    _NAME = ''

    def __init__(self, name, *, path=None, **kwargs):
        self.name = name
        if path is None:
            path = '{}/{}'.format(_PLUGIN_DIR, self.name)
        self.path = path

    def call_plugin_save_settings(self) -> Tuple[bool, Dict]:
        return self._call_plugin_func('this_save_settings')

    def call_plugin_load_settings(self, args) -> Tuple[bool, Dict]:
        return self._call_plugin_func('this_load_settings', args)

    def call_plugin_restart(self) -> Tuple[bool, Dict]:
        return self._call_plugin_func('this_restart')

    def _call_plugin_func(self, func_name: str, args=None) -> Tuple[bool, Dict]:
        """
        第一个返回值表示是否有这个函数
        第二个表示这个函数执行的结果
        """
        plugin_object = Plugin(self.name)
        get_obj = public.dict_obj()
        if args is not None:
            get_obj.args = args
        res = plugin_object.exec_fun(get_obj, func_name)
        if not isinstance(res, dict):
            return False, res
        if 'msg' in res and re.compile(r'在\[\w*]插件中找不到\[\w*]方法').search(res['msg']):
            return False, res
        elif 'msg' in res and res['msg'].find("该插件未购买或已到期") != -1:
            return False, res
        else:
            return True, res

    def save_settings(self, zip_file_name) -> Tuple[bool, str]:
        info_data = self._get_info()
        if info_data is None or "config" not in info_data:
            return False, "未找到配置文件"

        # return False, "未找到配置文件"
        # TODO: 实现默认文件保存
        config_list = info_data["config"]
        self._TARGET_PATH_LIST = self.parser_config_list(config_list)
        self._save_options(zip_file_name)
        self.call_plugin_restart()
        return True, "保存成功"

    @staticmethod
    def parser_config_list(config_list: List[str]) -> [Tuple[str, str, str]]:
        test = re.compile(r"[df]\|/([^|/]+/)*[^|/]+\|.*")
        result = []
        for i in config_list:
            if test.match(i) is not None:
                result.append(i.split("|"))

        return result

    def _get_info(self) -> Optional[Dict]:
        if not os.path.exists(self.path):
            return None
        if not os.path.exists(self.path + "/info.json"):
            return None

        data = public.readFile(self.path + "/info.json")
        if not data:
            return None
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return None

    def load_settings(self, zip_file_name: str) -> Tuple[bool, str]:
        info_data = self._get_info()
        if info_data is None or "config" not in info_data:
            return False, "未找到配置文件"
        if not os.path.exists(zip_file_name):
            return False, "配置文件丢失"
        # return False, "无法加载配置文件"
        # TODO: 实现默认文件加载
        config_list = info_data["config"]
        self._TARGET_PATH_LIST = self.parser_config_list(config_list)
        self._load_options(zip_file_name)

        return True, "恢复成功"


def create_plugin_setting(name, *args, **kwargs) -> BasePluginSetting:
    names_map = {getattr(c, "_NAME", ""): c for c in BasePluginSetting.__subclasses__()}
    if name in names_map:
        return names_map[name](name, *args, **kwargs)
    else:
        return BasePluginSetting(name, *args, **kwargs)


class RsyncSetting(BasePluginSetting):
    _NAME = 'rsync'
    _TARGET_PATH_LIST = [
        ("f", '{}/rsync/config.json'.format(_PLUGIN_DIR), "config.json"),
        ("f", '{}/rsync/config4.json'.format(_PLUGIN_DIR), "config4.json"),
        ("d", '{}/rsync/sclient'.format(_PLUGIN_DIR), "sclient"),
        ("d", '{}/rsync/secrets'.format(_PLUGIN_DIR), "secrets"),
    ]

    def save_settings(self, zip_file_name: str) -> Tuple[bool, Union[str, Dict]]:
        for t, f, n in self._TARGET_PATH_LIST:
            if t == "f" and not os.path.isfile(f):
                return False, "未找到配置文件"
            if t == "d" and not os.path.isdir(f):
                return False, "未找到配置文件"

        self._save_options(zip_file_name)

        import public

        reload_shell = "nohup /www/server/panel/pyenv/bin/python3.7 {}/rsync/rsync_cron.py &".format(_PLUGIN_DIR)
        public.ExecShell(reload_shell)

        return True, "保存完成"

    def load_settings(self, zip_file_name: str) -> Tuple[bool, str]:
        if not os.path.exists(zip_file_name):
            return False, "配置文件丢失"
        self._load_options(zip_file_name)
        return True, "配置文件还原成功"


# print(RsyncSetting("rsync").save_settings(_BACKUP_DIR + "/rsync_setting.zip"))
# print(RsyncSetting("rsync").load_settings(_BACKUP_DIR + "/rsync_setting.zip"))
#

class TamperCoreSetting(BasePluginSetting):
    _NAME = 'tamper_core'
    _BASE_PATH = "/www/server/tamper"
    _TARGET_PATH_LIST = [
        ("f", '{}/tamper.conf'.format(_BASE_PATH), "tamper.conf"),
        ("f", '{}/config_ps.json'.format(_BASE_PATH), "config_ps.json"),
    ]
    tips_file = '{}/tips.pl'.format(_BASE_PATH)

    def save_settings(self, zip_file_name: str) -> Tuple[bool, str]:
        for t, f, n in self._TARGET_PATH_LIST:
            if t == "f" and not os.path.isfile(f):
                return False, "未找到配置文件"

        self._save_options(zip_file_name)
        return True, "保存完成"

    def load_settings(self, zip_file_name: str) -> Tuple[bool, str]:
        if not os.path.exists(zip_file_name):
            return False, "配置文件丢失"

        self._load_options(zip_file_name)
        with open(self.tips_file, "w") as t_file:
            t_file.write("1")

        return True, "配置文件还原成功"


class TamperProofSetting(BasePluginSetting):
    _NAME = 'tamper_proof'
    _TARGET_PATH_LIST = [
        ("f", '{}/tamper_proof/sites.json'.format(_PLUGIN_DIR), "sites.json"),
        ("f", '{}/tamper_proof/config.json'.format(_PLUGIN_DIR), "config.json"),
    ]

    def save_settings(self, zip_file_name: str) -> Tuple[bool, str]:
        for t, f, n in self._TARGET_PATH_LIST:
            if t == "f" and not os.path.isfile(f):
                return False, "未找到配置文件"

        self._save_options(zip_file_name)
        return True, "保存完成"

    def load_settings(self, zip_file_name: str) -> Tuple[bool, str]:
        if not os.path.exists(zip_file_name):
            return False, "配置文件丢失"

        self._load_options(zip_file_name)

        import public
        public.ExecShell('/etc/init.d/bt_tamper_proof restart')

        return True, "配置文件还原成功"

class TamperProofRefactoredSetting(BasePluginSetting):
    """
    @description 网站防篡改-重构版 针对防护的站点配置文件和主配置文件进行备份导入，分别为保存->检测->重载
    @author wpl <2024/3/29>
    @return
    """
    _NAME = 'tamper_proof_refactored'
    _TARGET_PATH_LIST = [
        ("f", '{}/tamper_proof_refactored/tamper_proof_refactored/config/sites.json'.format(_PLUGIN_DIR), "sites.json"),
        ("f", '{}/tamper_proof_refactored/tamper_proof_refactored/config/config.json'.format(_PLUGIN_DIR), "config.json"),
    ]

    def save_settings(self, zip_file_name: str) -> Tuple[bool, str]:
        for t, f, n in self._TARGET_PATH_LIST:
            if t == "f" and not os.path.isfile(f):
                return False, "未找到配置文件"

        self._save_options(zip_file_name)
        return True, "保存完成"

    def load_settings(self, zip_file_name: str) -> Tuple[bool, str]:
        if not os.path.exists(zip_file_name):
            return False, "配置文件丢失"

        self._load_options(zip_file_name)

        import public
        public.ExecShell('systemctl restart tamper_proof')

        return True, "配置文件还原成功"


class SySSafeSetting(BasePluginSetting):
    _NAME = 'syssafe'
    _TARGET_PATH_LIST = [
        ("f", '{}/syssafe/config.json'.format(_PLUGIN_DIR), "config.json"),
        ("f", '{}/syssafe/deny.json'.format(_PLUGIN_DIR), "deny.json"),
    ]

    def save_settings(self, zip_file_name: str) -> Tuple[bool, str]:
        for t, f, n in self._TARGET_PATH_LIST:
            if t == "f" and not os.path.isfile(f):
                return False, "未找到配置文件"

        self._save_options(zip_file_name)
        return True, "保存完成"

    def load_settings(self, zip_file_name: str) -> Tuple[bool, str]:
        if not os.path.exists(zip_file_name):
            return False, "配置文件丢失"

        self._load_options(zip_file_name)

        public.ExecShell("{}/syssafe/init.sh restart".format(_PLUGIN_DIR))
        return True, "配置文件还原成功"


class NginxWafSetting(BasePluginSetting):
    _NAME = 'btwaf'

    _TARGET_PATH_LIST = [
    ]


class NginxTotalSetting(BasePluginSetting):
    _NAME = 'total'
    _BASE_PATH = "/www/server/total"
    _TARGET_PATH_LIST = [
        ("f", '{}/total/config.json'.format(_PLUGIN_DIR), "total_config.json"),
        ("f", '{}/config.json'.format(_BASE_PATH), "config.json"),
        ("f", '{}/total_config.lua'.format(_BASE_PATH), "total_config.lua"),
        ("d", '{}/config'.format(_BASE_PATH), "config"),
    ]

    def save_settings(self, zip_file_name: str) -> Tuple[bool, str]:
        for t, f, n in self._TARGET_PATH_LIST:
            if t == "f" and not os.path.isfile(f):
                return False, "未找到配置文件"

        self._save_options(zip_file_name)
        return True, "保存完成"

    def load_settings(self, zip_file_name: str) -> Tuple[bool, str]:
        if not os.path.exists(zip_file_name):
            return False, "配置文件丢失"

        self._load_options(zip_file_name)

        import public
        if public.get_webserver() == "apache":
            public.ExecShell('/etc/init.d/httpd restart')
        else:
            public.ExecShell('/etc/init.d/nginx restart')
        return True, "配置文件还原成功"


class SettingMager:
    """
    结构 :    {
        "rsync":{
            "name": 'rsync',
            "save_path": "/xxxx/",
            "create_time": 1695212434
        }
    }
    """

    def __init__(self):
        self._config = None

    @property
    def config(self) -> Dict:
        if self._config is None:
            self._config = self._read_plugin_settings_conf()
        return self._config

    @staticmethod
    def _read_plugin_settings_conf():
        conf_file = "{}/data/plugin_settings/conf.json".format(public.get_panel_path())
        if not os.path.exists(os.path.dirname(conf_file)):
            os.makedirs(os.path.dirname(conf_file), 0o600)
        if not os.path.exists(conf_file):
            return {}

        data = public.readFile(conf_file)
        if not data:
            return {}

        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return {}

    def save_conf(self):
        conf_file = "{}/data/plugin_settings/conf.json".format(public.get_panel_path())
        public.writeFile(conf_file, json.dumps(self._config))

    def save_plugin_settings(self, name):
        if name in self.config:
            target_path = self.config[name]["save_path"]
            if os.path.exists(target_path):
                os.remove(target_path)

        p = create_plugin_setting(name)
        f, res = p.call_plugin_save_settings()  # 先尝试用插件内部的
        if f:  #
            if res['status'] is True:
                if "args" in res:
                    self.config[name] = res['args']
                else:
                    self.config[name] = {
                        "name": name,
                        "create_time": time.time()
                    }
                self.save_conf()
                return public.returnMsg(True, "保存成功")
            else:
                return res

        target_path = "{}/backup_{}.zip".format(_BACKUP_DIR, name)
        f, m = p.save_settings(target_path)
        if f:
            self.config[name] = {
                "name": name,
                "save_path": target_path,
                "create_time": time.time()
            }
            self.save_conf()

            return public.returnMsg(True, m)
        return public.returnMsg(False, m)

    def load_plugin_settings(self, name):
        if name not in self.config:
            return public.returnMsg(True, "没有这个插件的历史配置信息")

        p = create_plugin_setting(name)
        f, res = p.call_plugin_load_settings(self.config[name])  # 先尝试用插件内部的加载
        if f:
            del self.config[name]
            self.save_conf()
            return res

        target_path = self.config[name]["save_path"]
        if not os.path.exists(target_path):
            del self.config[name]
            return public.returnMsg(True, "配置信息丢失")

        f, m = p.load_settings(target_path)
        if f:
            os.remove(target_path)
            del self.config[name]
            self.save_conf()
            return public.returnMsg(True, m)

        return public.returnMsg(False, m)

    def check_plugin_settings(self, name):
        if name not in self.config:
            return {
                "status": True,
                "on_config": True,
                "msg": "没有这个插件的历史配置信息"
            }
        return self.config[name]

