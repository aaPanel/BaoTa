import json
import sys
from mod.base import json_response
from mod.base.web_conf.access_control import cors_manager, BaseCorsManager
from typing import Optional, Dict, Union, List, Tuple, Any, Iterable

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

import public


class main:

    @staticmethod
    def _get_cors_manager(get: public.dict_obj) -> Union[dict, BaseCorsManager]:
        site_name = get.get("siteName", get.get("project_name", get.get("name", "")))
        if not site_name:
            return json_response(status=False, msg="站点名称不能为空")
        site_type = get.get("project_type/s", "php")
        if not site_type:
            site_type = "php"
        if site_type.lower() not in ("php", "java", "node", "wp2", "go", "python", "net", "html", "other"):
            return json_response(status=False, msg="站点类型错误")

        res = cors_manager(site_name, site_type)
        if isinstance(res, str):  # 错误
            return json_response(status=False, msg=res)
        return res

    @classmethod
    def get_cors_config(cls, get: public.dict_obj):
        cm = cls._get_cors_manager(get)
        if isinstance(cm, dict):
            return cm
        data = cm.get_cors_config()
        if not data["allowed_origins"]:
            data["allowed_origins"] = "*"
        return json_response(status=True, data=data)

    @classmethod
    def set_cors_config(cls, get: public.dict_obj):
        allowed_origin = get.get("allowed_origin/s", "").strip()
        if not allowed_origin:
            allowed_origin = ["*"]
        else:
            try:
                allowed_origin = json.loads(allowed_origin)
            except:
                allowed_origin = [i for i in allowed_origin.split(",") if i]
        if not allowed_origin:
            return json_response(status=False, msg="allowed_origin 不能为空")

        allowed_methods = get.get("allowed_methods/s", "").strip()
        allowed_headers = get.get("allowed_headers/s", "").strip()
        exposed_headers = get.get("exposed_headers/s", "").strip()
        allow_credentials = get.get("allow_credentials/s", "").strip()
        if allow_credentials in ("1", "true", "True"):
            allow_credentials = True
        else:
            allow_credentials = False

        cm = cls._get_cors_manager(get)
        if isinstance(cm, dict):
            return cm
        res = cm.add_cors(allowed_origin, allowed_methods, allowed_headers, exposed_headers, allow_credentials)
        if isinstance(res, str):  # 错误
            return json_response(status=False, msg=res)
        return json_response(status=True, msg="设置成功")

    @classmethod
    def remove_cors(cls, get: public.dict_obj):
        cm = cls._get_cors_manager(get)
        if isinstance(cm, dict):
            return cm
        res = cm.remove_cors()
        if isinstance(res, str):  # 错误
            return json_response(status=False, msg=res)
        return json_response(status=True, msg="删除成功")