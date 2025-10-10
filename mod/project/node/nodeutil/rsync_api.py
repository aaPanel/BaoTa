import json
from typing import Optional, Union, Tuple, List, Any, Dict

from .base import ServerNode, LocalNode

import public


class _RsyncAPIBase:

    def has_rsync_perm(self) -> bool:
        raise NotImplementedError()

    def is_setup_rsync(self) -> bool:
        raise NotImplementedError()

    def add_module(self, path: str, name: str, password: str, add_white_ips: List[str]) -> Tuple[Optional[dict], str]:
        raise NotImplementedError()

    def add_send_task(self, sou):
        pass

    def get_secretkey(self, ip_type: str = "local_ip") -> Tuple[str, str]:
        pass

    def check_receiver_conn(self, secret_key: str, work_type: int) -> Tuple[Dict, str]:
        pass



class BtLocalRsyncAPI(LocalNode, _RsyncAPIBase):
    @classmethod
    def new_by_id(cls, node_id: int) -> Optional['BtLocalRsyncAPI']:
        node_data = public.M('node').where('id=?', (node_id,)).find()
        if not node_data:
            return None

        if node_data["api_key"] == "local" and node_data["app_key"] == "local":
            return BtLocalRsyncAPI()

        return None

    @staticmethod
    def _plugin_func(func_name: str, **kwargs) -> Any:
        from panelPlugin import panelPlugin
        return panelPlugin().a(public.to_dict_obj({
            "name": "rsync",
            "s": func_name,
            **kwargs,
        }))

    def has_rsync_perm(self) -> bool:
        from panelPlugin import panelPlugin
        res = panelPlugin().a(public.to_dict_obj({"name": "rsync"}))
        if not res["status"]:
            return False
        return True

    def is_setup_rsync(self) -> bool:
        from panelPlugin import panelPlugin
        res = panelPlugin().get_soft_find(public.to_dict_obj({"sName": "rsync"}))
        try:
            return res["setup"]
        except:
            return False

    def add_module(self, path: str, name: str, password: str, add_white_ips: List[str]) -> Tuple[Optional[dict], str]:
        res = self._plugin_func("add_module", **{
            "path": path,
            "mName": name,
            "password": password,
            "add_white_ips": json.dumps(add_white_ips)
        })
        return res, ""


class BtRsyncAPI(ServerNode, _RsyncAPIBase):

    def _plugin_api_func(self, func_name: str, **kwargs) -> Tuple[Any, str]:
        return self._request("/plugin", "a", pdata={
            "name": "rsync",
            "s": func_name,
            **kwargs
        })

    @classmethod
    def new_by_id(cls, node_id: int) -> Optional['BtRsyncAPI']:
        node_data = public.M('node').where('id=?', (node_id,)).find()
        if not node_data:
            return None

        if node_data["api_key"] == "local" and node_data["app_key"] == "local":
            return None

        if node_data['lpver']:
            return None

        return BtRsyncAPI(node_data["address"], node_data["api_key"], "")

    def has_rsync_perm(self) -> bool:
        data, err = self._request("/plugin", "a", pdata={"name": "rsync"})
        if err:
            return False
        return data["status"]

    def is_setup_rsync(self) -> bool:
        data, err = self._request("/plugin", "get_soft_find", pdata={"sName": "rsync"})
        if err:
            return False
        try:
            return data["setup"]
        except:
            return False

    def add_module(self, path: str, name: str, password: str, add_white_ips: List[str]) -> Tuple[Optional[dict], str]:
        return self._plugin_api_func("add_module", **{
            "path": path,
            "mName": name,
            "password": password,
            "add_white_ips": json.dumps(add_white_ips)
        })



def get_rsync_api_node(node_id: int) -> Optional[Union['BtRsyncAPI', 'BtLocalRsyncAPI']]:
    srv = BtLocalRsyncAPI.new_by_id(node_id)
    if srv:
        return srv
    return BtRsyncAPI.new_by_id(node_id)
