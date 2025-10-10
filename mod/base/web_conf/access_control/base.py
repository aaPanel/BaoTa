import os.path
import sys
from typing import List, Optional, Dict, Iterable, Union

def web_type() -> str:
    if "/www/server/panel/class" not in sys.path:
        sys.path.insert(0, "/www/server/panel/class")

    import public
    return public.get_webserver()


class BaseCorsManager:
    access_control_path = "/www/server/panel/vhost/%s/access_control"

    def __init__(self, config_path: str):
        self.config_path = config_path
        self._main_backup: Optional[str] = None
        self._sub_backup: Optional[str] = None
        if web_type() == "nginx":
            self.access_control_path = self.access_control_path % "nginx"
        else:
            self.access_control_path = self.access_control_path % "apache"

        if not os.path.exists(self.access_control_path):
            os.makedirs(self.access_control_path)

        self.access_control_file = os.path.join(self.access_control_path, os.path.basename(self.config_path))

    @staticmethod
    def check_config() -> Optional[str]:
        """检查配置文件"""
        if "/www/server/panel/class" not in sys.path:
            sys.path.insert(0, "/www/server/panel/class")

        import public

        error = public.checkWebConfig()
        if isinstance(error, str):
            return error
        return None

    def read_main_config(self) -> str:
        """读取配置文件内容"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._main_backup = f.read()
            return self._main_backup

    def read_sub_config(self) -> str:
        """读取子配置文件内容"""
        if not os.path.exists(self.access_control_file):
            self._sub_backup = ""
            return ""
        with open(self.access_control_file, 'r', encoding='utf-8') as f:
            self._sub_backup = f.read()
            return self._sub_backup

    def write_config(self, main_conf: str, sub_conf: str) -> Optional[str]:
        """写入配置文件内容"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            f.write(main_conf)
        with open(self.access_control_file, 'w', encoding='utf-8') as f:
            f.write(sub_conf)

        res = self.check_config()
        if res is None:
            return None

        with open(self.config_path, 'w', encoding='utf-8') as f:
            f.write(self._main_backup)
        with open(self.access_control_file, 'w', encoding='utf-8') as f:
            f.write(self._sub_backup)
        return res

    def _get_main_status(self) -> bool:
        raise NotImplementedError

    def _get_sub_data(self) -> Optional[Dict[str, Union[str, bool, list]]]:
        raise NotImplementedError

    def get_cors_config(self) -> Dict[str, Union[str, bool, list]]:
        """获取CORS配置"""
        status = self._get_main_status()
        if not status:
            return {
                "status": False,
                "allowed_origins": [],
                "allow_methods": "",
                "allow_headers": "",
                "expose_headers": "",
                "allow_credentials": False,
            }
        else:
            res = {"status": True}
        sub_data = self._get_sub_data()
        if not sub_data:
            return {
                "status": False,
                "allowed_origins": [],
                "allow_methods": "",
                "allow_headers": "",
                "expose_headers": "",
                "allow_credentials": False,
            }
        res.update(**sub_data)
        return res

    def _add_to_main(self, main_conf: str) -> str:
        raise NotImplementedError

    def _make_sub_conf(self,
                       allowed_origins: List[str],
                       allow_methods: Optional[str],
                       allow_headers: Optional[str],
                       expose_headers: Optional[str],
                       allow_credentials: bool) -> str:
        """生成子配置文件内容"""
        raise NotImplementedError

    def add_cors(self,
                 allowed_origins: List[str] = None,
                 allow_methods: Optional[str] = None,
                 allow_headers: Optional[str] = None,
                 expose_headers: Optional[str] = None,
                 allow_credentials: bool = False,) -> Optional[str]:
        """添加CORS配置"""

        main_conf = self.read_main_config()
        self.read_sub_config() # backup sub conf

        main_conf = self._add_to_main(main_conf)
        allow_methods = allow_methods or "GET,POST,OPTIONS,PUT,DELETE"
        allow_headers = allow_headers or "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization"
        expose_headers = expose_headers or "Content-Length,Content-Range"
        if isinstance(allowed_origins, Iterable):
            allowed_origins = [origin for origin in allowed_origins if origin != '*']
        else:
            allowed_origins = []

        sub_conf = self._make_sub_conf(allowed_origins, allow_methods, allow_headers, expose_headers, allow_credentials)

        return self.write_config(main_conf, sub_conf)

    def _remove_from_main(self, main_conf: str) -> str:
        """从主配置文件中移除CORS配置"""
        raise NotImplementedError

    def remove_cors(self) -> Optional[str]:
        main_conf = self.read_main_config()
        self.read_sub_config() # backup sub conf
        main_conf = self._remove_from_main(main_conf)
        return self.write_config(main_conf, "")
