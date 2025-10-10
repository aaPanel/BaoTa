# -*- coding: utf-8 -*-
"""
MySQL 主从复制从库管理模块
负责从库配置、同步监控等操作
"""

import json
import re
from urllib.parse import urlparse
from typing import Dict, Any, List, Union
import public
try:
    from .bt_api import BtApi
    from .config_manager import ConfigManager
except:
    from bt_api import BtApi
    from config_manager import ConfigManager


class SlaveManager:
    """从库管理器"""
    
    def __init__(self):
        self.config_manager = ConfigManager()

    def check_slave(self, panel_addr: str, panel_key: str, master_ip: str, slave_ip: str) -> Dict[str, Any]:
        """检查从库连接和配置"""
        # 验证面板地址格式
        parsed_url = urlparse(panel_addr.strip())
        if parsed_url.scheme not in ('http', 'https') or not parsed_url.netloc :
            return public.returnMsg(False, "请输入正确的面板地址！ 如：http://1.1.1.1:8888/ http://www.bt.cn:8888/")

        panel_addr = "{}://{}/".format(parsed_url.scheme, parsed_url.netloc)

        bt_api_obj = BtApi(panel_addr, panel_key)
        result = bt_api_obj.get_config()

        if result.get("status") is False:
            return public.returnMsg(False, "主库请求从库错误：{msg}".format(msg=result.get("msg")))
        
        if "windows" in result.get("distribution").lower():
            return public.returnMsg(False, "Mysql 主从复制暂不支持 Windows 系统！")

        if not result.get("mysql"):
            return public.returnMsg(False, "请检查从库是否安装有Mysql")
        
        if result.get("mysql").get("setup") is False:
            return public.returnMsg(False, "请检查从库mysql是否有正常安装！")
        
        if result.get("mysql").get("status") is False:
            return public.returnMsg(False, "从库Mysql服务未启动,请检查是否正常启动！")

        slave_mysql_version = result.get("mysql").get("version")
        allowed_versions = {'5.7', '8.0', '8.4', '9.0', '10.3', '10.4', '10.5', '10.6', '10.7', '10.8', '10.9', '10.11'}

        if slave_mysql_version:
            for version in allowed_versions:
                if version in slave_mysql_version:
                    break
            else:
                return public.returnMsg(False, "从库Mysql版本不支持，请使用mysql-5.7以上版本")
        
        return public.returnMsg(True, "ok")

    def config_slave(self, slave_ip: str) -> Dict[str, Any]:
        """配置从库"""
        info = self.config_manager.get_slave_config(slave_ip)
        if not info:
            return public.returnMsg(False, "未找到从库配置信息")
        
        bt_api_obj = BtApi(info.get("panel_addr"), info.get("panel_key"))

        # 获取从库MySQL配置文件
        slave_my_cnf_result = bt_api_obj.get_slave_file("/etc/my.cnf")
        if slave_my_cnf_result.get("status") is False:
            return public.returnMsg(False, f"获取从库配置文件失败: {slave_my_cnf_result.get('msg')}")
        
        slave_my_cnf = slave_my_cnf_result["data"]
        
        # 获取从库的server-id
        server_id = info.get("server_id", ConfigManager.get_server_id_from_ip(slave_ip))

        # 删除原有的server-id配置
        slave_my_cnf = re.sub(r'server-id\s*=\s*[0-9]+\s*\n', '', slave_my_cnf)
        # 删除原有的replicate-do-db配置
        slave_my_cnf = re.sub(r'replicate-do-db\s*=\s*[^\n]*\s*\n', '', slave_my_cnf)
        
        # 替换或添加必要的配置
        required_configs = [
            f"server-id={server_id}",
            "gtid_mode=ON",
            "enforce_gtid_consistency=ON",
            "log_slave_updates=ON",
        ]

        err_code = info.get("err_code")
        if err_code and err_code != "0":
            slave_skip_errors = "slave_skip_errors={err_code}".format(err_code=err_code)
            required_configs.append(slave_skip_errors)

        # 检查并添加每个配置项
        for config in required_configs:
            config_name = config.split('=')[0]
            if f"{config_name}=" not in slave_my_cnf:
                slave_my_cnf = slave_my_cnf.replace("[mysqld]", f"[mysqld]\n{config}")
        
        # 根据db_name配置需要同步的库
        db_name_list = info.get("db_name").split(",")
        for db_name in db_name_list:
            replicate_config = "replicate-do-db={db_name}".format(db_name=db_name)
            if replicate_config not in slave_my_cnf:
                slave_my_cnf = slave_my_cnf.replace("[mysqld]", f"[mysqld]\n{replicate_config}")

        # 保存新的配置到从库
        save_result = bt_api_obj.save_slave_conf(slave_my_cnf)
        if not save_result.get('status'):
            return public.returnMsg(False, f"保存从库配置文件失败: {save_result.get('msg')}")
        
        # 重启从库MySQL服务
        restart_result = bt_api_obj.control_mysqld_service('restart')
        if not restart_result:
            return public.returnMsg(False, "重启从库MySQL服务失败")

        # 配置从库连接信息
        set_slave_sql = "change master to master_host='{master_host}',master_user='{master_user}',master_password='{master_password}',MASTER_AUTO_POSITION = 1;".format(
            master_host=info.get("master_ip"),
            master_user=info.get("master_user"),
            master_password=info.get("master_password")
        )
        
        self.exec_shell_sql(slave_ip, set_slave_sql)
        return public.returnMsg(True, "从库配置成功")

    def exec_shell_sql(self, slave_ip: str, sql: str, is_resp: bool = False) -> Union[Dict[str, Any], str]:
        """从库执行SQL语句"""
        info = self.config_manager.get_slave_config(slave_ip)
        if not info:
            return public.returnMsg(False, "未找到从库配置信息")

        bt_api_obj = BtApi(info.get("panel_addr"), info.get("panel_key"))
        if bt_api_obj is None:
            return public.returnMsg(False, "连接从库错误！")
        
        root_password = bt_api_obj.get_root_passowrd()
        
        sql = sql.replace("'", '"')
        shell = "export MYSQL_PWD={root_password} && /usr/bin/mysql --user=root --default-character-set=utf8 --execute 'SET sql_notes = 0;{sql}' && unset MYSQL_PWD".format(
            root_password=root_password, sql=sql)
        resp = bt_api_obj.slave_execute_command(shell, "/tmp")

        if is_resp is True:
            return resp
        if resp["status"] is False:
            return resp["msg"]
        return resp["msg"]

    def get_slave_info(self, slave_ip: str) -> Union[str, Dict[str, Any]]:
        """获取从库状态信息"""
        info = self.config_manager.get_slave_config(slave_ip)
        if not info:
            return public.returnMsg(False, "未找到从库配置信息")
        
        status_sql = "show slave status\\G"
        slave_status = self.exec_shell_sql(slave_ip, status_sql)
        lines = slave_status.strip().split("\n")
        slave_status_dict = {}
        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                slave_status_dict[key.strip()] = value.strip()

        # 将字典转换为JSON格式
        slave_status_json = json.dumps(slave_status_dict, ensure_ascii=False, indent=4)
        return slave_status_json

    def get_slave_info_dict(self, slave_ip: str) -> Dict[str, Any]:
        """获取从库状态信息（字典格式）"""
        info = self.config_manager.get_slave_config(slave_ip)
        if not info:
            return {}
        
        status_sql = "show slave status\\G"
        slave_status = self.exec_shell_sql(slave_ip, status_sql)
        lines = slave_status.strip().split("\n")
        slave_status_dict = {}
        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                slave_status_dict[key.strip()] = value.strip()

        return slave_status_dict

    def set_slave_status(self, slave_ip: str, status: str) -> Dict[str, Any]:
        """设置从库状态"""
        info = self.config_manager.get_slave_config(slave_ip)
        if not info:
            return public.returnMsg(False, "未找到从库配置信息")

        info["run_status"] = status
        self.config_manager.save_slave_config(slave_ip, info)
        
        if status == "stop":
            mysql_sql = "stop slave"
        else:
            mysql_sql = "start slave"
        
        self.exec_shell_sql(slave_ip, mysql_sql)
        return public.returnMsg(True, "设置成功!")

    def get_slave_mysql_status(self, slave_ip: str) -> Dict[str, Any]:
        """获取从库MySQL状态"""
        info = self.config_manager.get_slave_config(slave_ip)
        if not info:
            return public.returnMsg(False, "未找到从库配置信息")
        
        panel_addr = info.get("panel_addr") if str(info.get("panel_addr")).endswith("/") else info.get("panel_addr") + "/"
        panel_key = info.get("panel_key")
        bt_api_obj = BtApi(panel_addr, panel_key)
        slave_panel_info = bt_api_obj.get_config()
        
        result = {}
        if slave_panel_info.get("status") is False:
            result['status'] = False
            result['msg'] = slave_panel_info.get("msg")
        else:
            result['status'] = True
            result['msg'] = "ok"
        
        return result 