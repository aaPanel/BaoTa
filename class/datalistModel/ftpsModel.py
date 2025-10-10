# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: cjxin <cjxin@bt.cn>
# -------------------------------------------------------------------
#
# ------------------------------

import os, sys, time, json, re
import traceback

if '/www/server/panel/class/' not in sys.path:
    sys.path.insert(0, '/www/server/panel/class/')
import public, db
import panelSite
from datalistModel.base import dataBase


class main(dataBase):
    web_server = None
    site_obj = None

    def __init__(self):
        self.site_obj = panelSite.panelSite()

    """
    @name 获取公共数据后，格式化为网站列表需要的数据
    """

    def get_data_list(self, get):
        try:
            get = self._get_site_args(get)
            data_list = get.data_list
            # 获取前端需要的表头
            from config import config
            table_header = config().get_table_header(public.to_dict_obj({'table_name': 'ftpTableColumn'}))
            if table_header['ftpTableColumn'] == '':
                table_header = ['用户名', '密码', '状态', '复制快速连接信息', '根目录', '设置密码有效期', '容量', '备注', '操作']
            else:
                table_header["ftpTableColumn"] = json.loads(table_header["ftpTableColumn"])
                table_header = [i['title'] if 'title' in i else i['label'] for i in table_header["ftpTableColumn"] if
                                (i.get('value', False) == True or i.get('isCustom', True) == True) and ('label' in i.keys() or 'title' in i.keys())]
            # 按需加载
            custom_list = {"容量": "quota", '设置密码有效期': 'end_time'}
            custom_conf = {'quota': {}, "end_time": {}}
            paths = []
            ids = []
            default_quota = {
                "used": 0,
                "size": 0,
                "quota_push": {
                    "size": 0,
                    "used": 0,
                },
                "quota_storage": {
                    "size": 0,
                    "used": 0,
                }}
            [paths.append(val['path']) or ids.append(val['id']) for val in data_list]
            for i, j in custom_list.items():
                if i in table_header:
                    if j == 'quota':
                        custom_conf[j] = self.get_all_quota(paths)
                    if j == 'end_time':
                        custom_conf[j] = self.get_all_ftp_end_time(ids)
            for i in data_list:
                i['quota'] = custom_conf['quota'].get(i['path'], default_quota)
                i['end_time'] = custom_conf['end_time'].get(i['id'], '0')
            return data_list
        except:
            pass

    """
    @name 初始化参数
    """

    def _get_site_args(self, get):
        try:
            if not 'type' in get:
                get.type = 0
                get.type = int(get.p)
        except:
            get.type = 0

        # if not 'project_type' in get:
        #     get.project_type = 'PHP'
        # get.search_key = get.project_type.lower()
        get.search_key = get.table.lower()
        if hasattr(get, 'search'):
            public.set_search_history(get.table,get.search_key,get.search)
        return get

    """
    @name 追加 or条件
    """

    def get_search_where(self, get):

        where = ''
        params = get.search

        conditions = ''
        if '_' in get.search:
            conditions = " escape '/'"
        if params:
            where = "name LIKE ? OR ps LIKE ? {}".format(conditions)
            params = ('%' + params + '%', '%' + params + '%')
        return where, params


    """
    @获取ftp查询条件，追加and查询条件
    """

    def get_data_where(self, get):
        wheres = []
        get = self._get_site_args(get)
        if "type_id" in get and get.type_id:
            type_id = get.get("type_id")
            wheres.append("type_id = {}".format(type_id))
        return wheres

    # 获取ftp到期时间
    def get_all_ftp_end_time(self, ids):
        config_path = '/www/server/panel/data/ftp_push_config.json'
        if not os.path.exists(config_path):
            return {i: "0" for i in ids}

        config = {}
        try:
            config = json.loads(public.readFile(config_path))
        except json.decoder.JSONDecodeError:
            if os.path.exists(config_path):
                import shutil
                shutil.copy(config_path, "{}.bak".format(config_path))
                public.writeFile(config_path, json.dumps({'0': [], '1': [], '2': [], '3': [], 'channel': ''}))

        content = {}
        for _, i in config.items():
            if _ == 'channel':
                continue
            for j in i:
                content[j['id']] = j['end_time']
        return {i: content[i] if i in content.keys() else '0' for i in ids}

