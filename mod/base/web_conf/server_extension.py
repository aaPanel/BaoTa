import os
import re
import shutil

import public

class NginxExtension:
    _EXTENSION_DIR = "{}/vhost/nginx/extension".format(public.get_panel_path())

    @classmethod
    def set_extension(cls, site_name: str, config_path: str) -> str:
        config_data = public.readFile(config_path)
        if not config_data:
            return ""
        return cls.set_extension_by_config(site_name, config_data)

    @classmethod
    def set_extension_by_config(cls, site_name: str, config_data: str) -> str:
        ext_path = "{}/{}".format(cls._EXTENSION_DIR, site_name)
        if os.path.exists(ext_path):
            if not os.path.isdir(ext_path):
                os.remove(ext_path)
                os.makedirs(ext_path)
        else:
            os.makedirs(ext_path)

        rep_exp_list=[
            re.compile(r"(?<!#)server\s*{(([^{\n]*\n)|(\s*#.*\n)){0,20}\s*root\s+/[^\n]*\n"),
            re.compile(r"(?<!#)server\s*{(([^{\n]*\n)|(\s*#.*\n)){0,20}\s*index\s+[^\n]*\n"),
            re.compile(r"(?<!#)server\s*{(([^{\n]*\n)|(\s*#.*\n)){0,20}\s*server_name\s+[^\n]*\n"),
        ]

        insert_ext = "    include {}/*.conf;\n".format(ext_path)
        for rep_exp in rep_exp_list:
            find_list = list(re.finditer(rep_exp, config_data))
            if not find_list:
                continue
            for tmp in find_list[::-1]:
                config_data = config_data[:tmp.end()] + insert_ext + config_data[tmp.end():]
            break

        return config_data

    @classmethod
    def remove_extension(cls, site_name: str, config_path: str):
        ext_path = "{}/{}".format(cls._EXTENSION_DIR, site_name)
        if os.path.isdir(ext_path):
            shutil.rmtree(ext_path)

        config_data= public.readFile(config_path)
        if not config_data:
            return
        return cls.remove_extension_from_config(site_name, config_data)

    @staticmethod
    def remove_extension_from_config(site_name: str, config_data: str):
        regexp = re.compile(r"\s*include\s+/.*extension/.*/\*\.conf;[^\n]*\n")
        return re.sub(regexp, "\n", config_data)

    @staticmethod
    def has_extension(conf_data: str) -> bool:
        regexp = re.compile(r"\s*include\s+/.*extension/.*/\*\.conf;[^\n]*\n")
        return bool(re.search(regexp, conf_data))


class ApacheExtension(NginxExtension):
    _EXTENSION_DIR = "{}/vhost/apache/extension".format(public.get_panel_path())

    @classmethod
    def set_extension_by_config(cls, site_name: str, config_data: str) -> str:
        ext_path = "{}/{}".format(cls._EXTENSION_DIR, site_name)
        if not os.path.exists(ext_path):
            os.makedirs(ext_path)
        else:
            if not os.path.isdir(ext_path):
                os.remove(ext_path)
                os.makedirs(ext_path)

        rep_exp_list=[
            re.compile(r"<VirtualHost\s+\S+:\d+>\s(.*\n){0,8}\s*ServerAlias\s+[^\n]*\n"),
            re.compile(r"<VirtualHost\s+\S+:\d+>\s(.*\n){0,6}\s*DocumentRoot\s+[^\n]*\n"),
        ]

        insert_ext = "    IncludeOptional {}/*.conf\n".format(ext_path)
        for rep_exp in rep_exp_list:
            find_list = list(re.finditer(rep_exp, config_data))
            if not find_list:
                continue
            for tmp in find_list[::-1]:
                config_data = config_data[:tmp.end()] + insert_ext + config_data[tmp.end():]
            break

        return config_data

    @staticmethod
    def remove_extension_from_config(site_name: str, config_data: str):
        regexp = re.compile(r"\s*IncludeOptional\s+/.*extension/.*/\*\.conf[^\n]*\n")
        return re.sub(regexp, "\n", config_data)

    @staticmethod
    def has_extension(conf_data: str) -> bool:
        regexp = re.compile(r"\s*IncludeOptional\s+/.*extension/.*/\*\.conf[^\n]*\n")
        return bool(re.search(regexp, conf_data))
