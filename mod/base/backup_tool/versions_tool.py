import json
import os
import shutil
import tarfile
import time
from hashlib import md5
from typing import Optional, List, Union, Dict, Any

from .util import DB, ExecShell, write_file, write_log, read_file


class VersionTool:
    _config_file = "/www/server/panel/data/version_config.json"

    def __init__(self):
        self._config: Optional[Dict[str, List[Dict[str, Any]]]] = None
        self._pack_class = BasePack
        self.pack_path = "/www/backup/versions"
        if not os.path.isdir(self.pack_path):
            os.makedirs(self.pack_path)

    @property
    def config(self) -> Dict[str, List[Dict[str, Any]]]:
        if self._config is not None:
            return self._config

        data = {}
        try:
            res = read_file(self._config_file)
            if isinstance(res, str):
                data = json.loads(res)
        except (json.JSONDecoder, TypeError, ValueError):
            pass
        self._config = data
        return self._config

    def save_config(self):
        if self._config is not None:
            write_file(self._config_file, json.dumps(self._config))

    def add_to_config(self, data: dict):
        project_name = data.get("project_name")
        self._config = None
        if project_name not in self.config:
            self.config[project_name] = []
        self.config[project_name].append(data)
        self.save_config()

    def set_pack_class(self, pack_cls):
        self._pack_class = pack_cls

    def version_list(self, project_name: str):
        if project_name in self.config:
            return self.config[project_name]
        return []

    def get_version_info(self, project_name: str, version: str) -> Optional[dict]:
        if project_name in self.config:
            for i in self.config[project_name]:
                if i.get("version") == version:
                    return i
        return None

    # 把某个路径下的文件打包并发布为一个版本
    def publish_by_src_path(self,
                            project_name: str,  # 名称
                            src_path: str,  # 源路径
                            version: str,  # 版本号
                            ps: Optional[str] = None,  # 备注
                            other: Optional[dict] = None,  # 其他信息
                            sync: bool = False,  # 是否同步执行
                            ):

        if project_name in self.config:
            for i in self.config[project_name]:
                if i["version"] == version:
                    return "当前版本已存在"
        if not os.path.isdir(src_path):
            return "源路径不存在"

        if ps is None:
            ps = ''

        if other is None:
            other = {}

        zip_name = "{}_{}.tar.gz".format(
            os.path.basename(src_path), time.strftime('%Y%m%d_%H%M%S', time.localtime())
        )

        data = {
            "project_name": project_name,
            "version": version,
            "ps": ps,
            "other": other,
            "zip_name": zip_name,
            "backup_time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        }
        return self._pack_class(src_path, self.pack_path, zip_name, sync=sync, vt=self, data=data)(**other)

    def recover(self,
                project_name: str,  # 名称
                version: str,  # 版本
                target_path: str,  # 目标路径
                run_path=None
                ):
        if not run_path:
            run_path = target_path
        if project_name not in self.config:
            return '项目不存在'

        target = None
        for i in self.config[project_name]:
            if i["version"] == version:
                target = i
                break

        if target is None:
            return '版本不存在'

        file = os.path.join(self.pack_path, target["zip_name"])
        if not os.path.exists(file):
            return '版本文件丢失'

        tmp_path = '/tmp/version_{}'.format(int(time.time()))
        tar = tarfile.open(file, mode='r')
        tar.extractall(tmp_path)
        user_data = None
        if os.path.exists(target_path):
            ExecShell("chattr -i -R {}/".format(target_path))
            user_data = read_file(run_path + "/.user.ini")
            ExecShell("rm -rf {}".format(target_path))
            os.makedirs(target_path)
        if not os.path.exists(target_path):
            os.makedirs(target_path)
        ExecShell("\cp -rf {}/* {}".format(tmp_path, target_path))
        if user_data:
            write_file(target_path + "/.user.ini", run_path)
            ExecShell("chattr +i {}/.user.ini".format(run_path))
        ExecShell("rm -rf  {}".format(tmp_path))
        return True

    def publish_by_file(self,
                        project_name: str,  # 名称
                        src_file: str,  # 源路径
                        version: str,  # 版本号
                        ps: Optional[str] = None,  # 备注
                        other: Optional[dict] = None,  # 其他信息
                        ):

        if project_name in self.config:
            for i in self.config[project_name]:
                if i["version"] == version:
                    return "当前版本已存在"

        if not os.path.isfile(src_file):
            return "源路径不存在"

        if ps is None:
            ps = ''

        if other is None:
            other = {}

        zip_name = os.path.basename(src_file)

        data = {
            "project_name": project_name,
            "version": version,
            "ps": ps,
            "other": other,
            "zip_name": zip_name,
            "backup_time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        }
        try:
            shutil.copy(src_file, self.pack_path + "/" + zip_name)
        except:
            return "文件保存失败"
        self.add_to_config(data)
        return None

    def remove(self,
               project_name: str,  # 名称
               version: str,  # 版本
               ) -> Optional[str]:

        if project_name not in self.config:
            return '项目不存在'

        target = None
        for i in self.config[project_name]:
            if i["version"] == version:
                target = i
                break

        if target is None:
            return '版本不存在'

        file = os.path.join(self.pack_path, target["zip_name"])
        if os.path.isfile(file):
            os.remove(file)

        self.config[project_name].remove(target)

        self.save_config()
        return None

    def set_ps(self, name: str, version: str, ps: str):
        [i.update({'ps': ps}) for i in self.config[name] if i["version"] == version]
        self.save_config()
        return True


class BasePack:
    exec_log_file = "/tmp/project_pack.log"

    def __init__(self, src_path, target_path, zip_name, sync=False, vt: VersionTool = None, data: dict = None):
        self.src_path = src_path
        self.target_path = target_path
        self.zip_name = zip_name
        self.sync = sync
        self.v = vt
        self._add_data = data

    def save_config(self):
        self.v.add_to_config(self._add_data)

    def __call__(self, *args, **kwargs) -> Optional[str]:
        if not os.path.exists(self.src_path):
            return "源路径不存在"
        target_path = "/www/backup/versions"

        if not os.path.isdir(target_path):
            os.makedirs(target_path)
        if self.sync:
            return self._sync_backup(self.src_path, target_path, self.zip_name)
        else:
            return self._async_backup(self.src_path, target_path, self.zip_name)

    def _sync_backup(self, src: str, target_path: str, zip_name: str) -> Optional[str]:
        try:
            write_file(self.exec_log_file, "")
            execStr = ("cd {} && "
                       "tar -zcvf '{}' --exclude=.user.ini ./ 2>&1 > {} \n"
                       "echo '---打包执行完成---' >> {}"
                       ).format(src, os.path.join(target_path, zip_name), self.exec_log_file, self.exec_log_file)
            ExecShell(execStr)
            self.save_config()
        except:
            return "打包执行失败"

    def _async_backup(self, src: str, target_path: str, zip_name: str):
        import threading
        hash_name = self._hash_src_name(src)
        backup_tip_path = "/tmp/mod_version_tip"
        if os.path.exists(backup_tip_path):
            os.makedirs(backup_tip_path)

        tip_file = os.path.join(backup_tip_path, hash_name)
        if os.path.isfile(tip_file):
            mtime = os.stat(tip_file).st_mtime
            if time.time() - mtime > 60 * 20:  # 20 分钟未执行，认为出现在不可抗力，导致备份失败，允许再次备份
                os.remove(tip_file)
            else:
                return "打包进行中，请勿继续操作"

        write_file(tip_file, "")

        def _back_p():
            try:
                write_file(self.exec_log_file, "")
                execStr = ("cd {} && "
                           "tar -zcvf '{}' --exclude=.user.ini ./ 2>&1 > {} \n"
                           "echo '---备份执行完成---' >> {}"
                           ).format(src, os.path.join(target_path, zip_name), self.exec_log_file, self.exec_log_file)
                ExecShell(execStr)
                self.save_config()
            except:
                pass
            finally:
                if os.path.exists(tip_file):
                    os.remove(tip_file)

        t = threading.Thread(target=_back_p)
        t.start()

    @staticmethod
    def _hash_src_name(name: Union[str, bytes]) -> str:
        if isinstance(name, str):
            name = name.encode('utf-8')
        md5_obj = md5()
        md5_obj.update(name)
        return md5_obj.hexdigest()
