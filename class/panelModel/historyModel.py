# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: cjxin <cjxin@bt.cn>
# -------------------------------------------------------------------

import os
import time
import json
import datetime

import public
from panelModel.base import panelBase


class main(panelBase):
    SEARCH_HISTORY_FILE = public.get_panel_path() + '/data/search.json'

    def __init__(self):
        pass

    def clear_search_history(self, get):
        if not hasattr(get, "name"):
            return public.returnMsg(False, "缺少参数！name")
        if not hasattr(get, "key"):
            return public.returnMsg(False, "缺少参数！key")
        name = get.name
        key = get.key

        if not os.path.exists(self.SEARCH_HISTORY_FILE):
            return public.returnMsg(True, "ok")

        try:
            result = json.loads(public.readFile(self.SEARCH_HISTORY_FILE))
        except:
            result = {}

        result[name] = {}
        result[name][key] = []
        public.writeFile(self.SEARCH_HISTORY_FILE, json.dumps(result))
        return public.returnMsg(True, "清空历史记录成功！")

    # 清楚指定搜索历史
    def remove_search_history(self, get):
        if not hasattr(get, "name"):
            return public.returnMsg(False, "缺少参数！name")
        if not hasattr(get, "key"):
            return public.returnMsg(False, "缺少参数！key")
        if not hasattr(get, "val"):
            return public.returnMsg(False, "缺少参数！val")

        name = get.name
        key = get.key
        val = get.val

        if not os.path.exists(self.SEARCH_HISTORY_FILE):
            return public.returnMsg(True, "ok")

        try:
            result = json.loads(public.readFile(self.SEARCH_HISTORY_FILE))
        except:
            result = {}

        if result.get(name) is None: result[name] = {}
        if result[name].get(key) is None:  result[name][key] = []

        for item in result[name][key]:
            if item["val"].strip() == val.strip():
                result[name][key].remove(item)
                break
        public.writeFile(self.SEARCH_HISTORY_FILE, json.dumps(result))
        return public.returnMsg(True, "删除历史记录成功！")

    def set_openfile_history(self, get):
        if not hasattr(get, "name"):
            return public.returnMsg(False, "缺少参数！name")
        name = get.name
        if not os.path.exists(name):
            pass
        path = '/www/server/panel/data/openfile_history.pl'
        if os.path.exists(path):
            conf = json.loads(public.readFile(path))
        else:
            conf = []
        if name in conf:
            conf.remove(name)
            conf.insert(0, name)
        else:
            conf.insert(0, name)
        if len(conf) > 10:
            conf = conf[:10]
        public.writeFile(path, json.dumps(conf))
        return public.returnMsg(True, "保存成功！")

    def get_openfile_history(self, get):
        path = '/www/server/panel/data/openfile_history.pl'
        if not os.path.exists(path):
            return []
        conf = json.loads(public.readFile(path))
        return conf
