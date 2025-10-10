import os
import time
from hashlib import md5
from typing import Optional, List, Union, Dict, Any

from .util import DB, ExecShell, write_file, write_log
from .versions_tool import VersionTool


class BackupTool:

    def __init__(self):
        self._backup_path: Optional[str] = None
        self._sub_dir_name: str = ""
        self.exec_log_file = "/tmp/mod_backup_exec.log"

    @staticmethod
    def _hash_src_name(name: Union[str, bytes]) -> str:
        if isinstance(name, str):
            name = name.encode('utf-8')
        md5_obj = md5()
        md5_obj.update(name)
        return md5_obj.hexdigest()

    @property
    def backup_path(self) -> str:
        if self._backup_path is None:
            config_data = DB("config").where("id=?", (1,)).select()
            if isinstance(config_data, dict):
                path = config_data["backup_path"]
            else:  # 查询出错
                path = "/www/backup"
            self._backup_path = path
        return self._backup_path

    # sub_dir 可以设置为多级子目录， 如 "site/aaa", 或使用列表传递如：["site", "aaa"]
    def set_sub_dir(self, sub_dir: Union[str, List[str]]) -> Optional[str]:
        if isinstance(sub_dir, str):
            self._sub_dir_name = sub_dir.strip("./")
        elif isinstance(sub_dir, list):
            self._sub_dir_name = "/".join(filter(None, [i.strip("./") for i in sub_dir]))
        else:
            return "不支持的类型设置"

    def backup(self,
               src: str,  # 源文件位置
               backup_path: Optional[str] = None,  # 备份位置
               sub_dir: Union[str, List[str]] = None,  # 备份目录的子目录
               site_info: Dict[str, Any] = None,  # 关联的站点信息， 必须包含 id 和 name
               sync=False  # 是否同步执行， 默认异步由单独的线程放入后台执行
               ) -> Optional[str]:  # 返回执行错误的信息

        if not os.path.exists(src):
            return "源路径不存在"
        if backup_path is None:
            backup_path = self.backup_path

        if not os.path.exists(backup_path):
            return "备份目录不存在"
        if sub_dir is not None:
            set_res = self.set_sub_dir(sub_dir)
            if set_res is not None:
                return set_res

        target_path = os.path.join(backup_path, self._sub_dir_name)
        if not os.path.isdir(target_path):
            os.makedirs(target_path)
        zip_name = "{}_{}.tar.gz".format(os.path.basename(src), time.strftime('%Y%m%d_%H%M%S', time.localtime()))
        if sync:
            return self._sync_backup(src, target_path, zip_name, site_info)
        else:
            return self._async_backup(src, target_path, zip_name, site_info)

    def _sync_backup(self, src: str, target_path: str, zip_name: str, site_info: dict):
        try:
            write_file(self.exec_log_file, "")
            execStr = ("cd {} && "
                       "tar -zcvf '{}' --exclude=.user.ini ./ 2>&1 > {} \n"
                       "echo '---备份执行完成---' >> {}"
                       ).format(src, os.path.join(target_path, zip_name), self.exec_log_file, self.exec_log_file)
            ExecShell(execStr)
            if site_info is not None and "id" in site_info and "name" in site_info:
                DB('backup').add(
                    'type,name,pid,filename,size,addtime',
                    (0, zip_name, site_info["id"], os.path.join(target_path, zip_name), 0, self.get_date())
                )
                write_log('TYPE_SITE', 'SITE_BACKUP_SUCCESS', (site_info["name"],))
        except:
            return "备份执行失败"

    def _async_backup(self, src: str, target_path: str, zip_name: str, site_info: dict):
        import threading

        hash_name = self._hash_src_name(src)
        backup_tip_path = "/tmp/mod_backup_tip"
        if os.path.exists(backup_tip_path):
            os.makedirs(backup_tip_path)

        tip_file = os.path.join(backup_tip_path, hash_name)
        if os.path.isfile(tip_file):
            mtime = os.stat(tip_file).st_mtime
            if time.time() - mtime > 60 * 20:  # 20 分钟未执行，认为出现在不可抗力，导致备份失败，允许再次备份
                os.remove(tip_file)
            else:
                return "备份进行中，请勿继续操作"

        write_file(tip_file, "")

        def _back_p():
            try:
                write_file(self.exec_log_file, "")
                execStr = ("cd {} && "
                           "tar -zcvf '{}' --exclude=.user.ini ./ 2>&1 > {} \n"
                           "echo '---备份执行完成---' >> {}"
                           ).format(src, os.path.join(target_path, zip_name), self.exec_log_file, self.exec_log_file)
                ExecShell(execStr)
                if site_info is not None and "id" in site_info and "name" in site_info:
                    DB('backup').add(
                        'type,name,pid,filename,size,addtime',
                        (0, zip_name, site_info["id"], os.path.join(target_path, zip_name), 0, self.get_date())
                    )
                    write_log('TYPE_SITE', 'SITE_BACKUP_SUCCESS', (site_info["name"],))
            except:
                pass
            finally:
                if os.path.exists(tip_file):
                    os.remove(tip_file)

        t = threading.Thread(target=_back_p)
        t.start()

    @staticmethod
    def get_date():
        # 取格式时间
        return time.strftime('%Y-%m-%d %X', time.localtime())
