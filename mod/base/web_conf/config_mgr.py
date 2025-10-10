import os
import time
from hashlib import md5
from typing import Optional
from .util import service_reload, check_server_config, write_file, read_file


# 支持读取配置文件
# 保存并重启配置文件
# 历史文件记录
class ConfigMgr:
    _vhost_path = "/www/server/panel/vhost"

    def __init__(self, site_name: str, config_prefix: str = ""):
        self.site_name = site_name
        self.config_prefix = config_prefix

    def _read_config(self, web_server: str) -> Optional[str]:
        config_file = "{}/{}/{}{}.conf".format(self._vhost_path, web_server, self.config_prefix, self.site_name)
        res = read_file(config_file)
        if isinstance(res, str):
            return res
        return None

    def nginx_config(self) -> Optional[str]:
        return self._read_config("nginx")

    def apache_config(self) -> Optional[str]:
        return self._read_config("apache")

    def save_config(self, conf_data: str, web_server: str):
        config_file = "{}/{}/{}{}.conf".format(self._vhost_path, web_server, self.config_prefix, self.site_name)
        old_config = self._read_config(web_server)
        write_file(config_file, conf_data)
        errmsg = check_server_config()
        if errmsg:
            write_file(config_file, old_config)
            return errmsg
        self._save_history(web_server)
        service_reload()

    def save_nginx_config(self, conf_data: str) -> Optional[str]:
        return self.save_config(conf_data, "nginx")

    def save_apache_config(self, conf_data: str) -> Optional[str]:
        return self.save_config(conf_data, "apache")

    def history_list(self):
        his_path = '/www/backup/file_history'
        nginx_config_file = "{}/nginx/{}{}.conf".format(self._vhost_path, self.config_prefix, self.site_name)
        ng_save_path = "{}{}".format(his_path, nginx_config_file)
        apache_config_file = "{}/apache/{}{}.conf".format(self._vhost_path, self.config_prefix, self.site_name)
        ap_save_path = "{}{}".format(his_path, apache_config_file)
        return {
            "nginx": [] if not os.path.isdir(ng_save_path) else sorted(os.listdir(ng_save_path), reverse=True),
            "apache": [] if not os.path.isdir(ap_save_path) else sorted(os.listdir(ap_save_path), reverse=True)
        }

    def history_conf(self, history_id: str) -> Optional[str]:
        his_path = '/www/backup/file_history'
        nginx_config_file = "{}/nginx/{}{}.conf".format(self._vhost_path, self.config_prefix, self.site_name)
        ng_save_path = "{}{}".format(his_path, nginx_config_file)
        if os.path.isdir(ng_save_path):
            for i in os.listdir(ng_save_path):
                if i == history_id:
                    return read_file(os.path.join(ng_save_path, i))

        apache_config_file = "{}/apache/{}{}.conf".format(self._vhost_path, self.config_prefix, self.site_name)
        ap_save_path = "{}{}".format(his_path, apache_config_file)
        if os.path.isdir(ap_save_path):
            for i in os.listdir(ap_save_path):
                if i == history_id:
                    return read_file(os.path.join(ap_save_path, i))
        return None

    def remove_history_file(self, history_id: str) -> None:
        his_path = '/www/backup/file_history'
        nginx_config_file = "{}/nginx/{}{}.conf".format(self._vhost_path, self.config_prefix, self.site_name)
        ng_save_path = "{}{}".format(his_path, nginx_config_file)
        if os.path.isdir(ng_save_path):
            for i in os.listdir(ng_save_path):
                if i == history_id:
                    os.remove(os.path.join(ng_save_path, i))

        apache_config_file = "{}/apache/{}{}.conf".format(self._vhost_path, self.config_prefix, self.site_name)
        ap_save_path = "{}{}".format(his_path, apache_config_file)
        if os.path.isdir(ap_save_path):
            for i in os.listdir(ap_save_path):
                if i == history_id:
                    os.remove(os.path.join(ng_save_path, i))

    def clear_history_file(self) -> None:
        """
        清空所有的历史文件
        """
        his_path = '/www/backup/file_history'
        nginx_config_file = "{}/nginx/{}{}.conf".format(self._vhost_path, self.config_prefix, self.site_name)
        ng_save_path = "{}{}".format(his_path, nginx_config_file)
        if os.path.isdir(ng_save_path):
            for i in os.listdir(ng_save_path):
                try:
                    os.unlink(os.path.join(ng_save_path, i))
                except IsADirectoryError:
                    try:
                        os.rmdir(os.path.join(ng_save_path, i))
                    except Exception:
                        pass
                except:
                    pass

        apache_config_file = "{}/apache/{}{}.conf".format(self._vhost_path, self.config_prefix, self.site_name)
        ap_save_path = "{}{}".format(his_path, apache_config_file)
        if os.path.isdir(ap_save_path):
            for i in os.listdir(ap_save_path):
                try:
                    os.unlink(os.path.join(ap_save_path, i))
                except IsADirectoryError:
                    try:
                        os.rmdir(os.path.join(ap_save_path, i))
                    except Exception:
                        pass
                except:
                    pass

    @staticmethod
    def _file_md5(filename):
        if not os.path.isfile(filename):
            return False
        md5_obj = md5()
        with open(filename, mode="rb") as f:
            while True:
                b = f.read(8096)
                if not b:
                    break
                md5_obj.update(b)

        return md5_obj.hexdigest()

    def _save_history(self, web_server: str):
        if os.path.exists('/www/server/panel/data/not_file_history.pl'):
            return True

        his_path = '/www/backup/file_history'
        filename = "{}/{}/{}{}.conf".format(self._vhost_path, web_server, self.config_prefix, self.site_name)
        save_path = "{}{}".format(his_path, filename)
        if not os.path.isdir(save_path):
            os.makedirs(save_path, 384)

        his_list = sorted(os.listdir(save_path), reverse=True)  # 倒序排列已有的历史文件
        try:
            num = int(read_file('data/history_num.pl'))
        except (ValueError, TypeError):
            num = 100

        is_write = True
        if len(his_list) > 0:
            new_file_md5 = self._file_md5(filename)
            last_file_md5 = self._file_md5(os.path.join(save_path, his_list[0]))
            is_write = new_file_md5 != last_file_md5

        if is_write:
            new_name = str(int(time.time()))
            write_file(os.path.join(save_path, new_name), read_file(filename, 'rb'), "wb")
            his_list.insert(0, new_name)

        # 删除多余的副本
        for i in his_list[num:]:
            rm_file = save_path + '/' + i
            if os.path.exists(rm_file):
                os.remove(rm_file)