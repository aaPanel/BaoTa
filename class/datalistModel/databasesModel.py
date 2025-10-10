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
            table_header = config().get_table_header(public.to_dict_obj({'table_name': 'mysqlTableColumn'}))
            if not table_header:
                if table_header['mysqlTableColumn'] == '': table_header['mysqlTableColumn'] = '{}'
                table_header["mysqlTableColumn"] = json.loads(table_header["mysqlTableColumn"])
                table_header = [i['title'] if 'title' in i else i['label'] for i in table_header["mysqlTableColumn"] if
                                (i.get('value', False) == True or i.get('isCustom', True) == True) and ('label' in i.keys() or 'title' in i.keys())]
            else:
                table_header = ["容量", "备份"]
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
            # 按需加载
            custom_list = {"容量": "quota", "备份": "backup_count"}
            custom_conf = {'quota': {}, 'backup_count': {}}
            names = []
            ids = []
            [ids.append(str(val['id'])) or names.append(val['name']) for val in data_list]
            for i, j in custom_list.items():
                if i in table_header:
                    if j == 'quota':
                        custom_conf[j] = self.get_database_quota(names)
                    if j == 'backup_count':
                        custom_conf[j] = self.get_database_backup_count(ids)

            for i in data_list:
                i['conn_config'] = json.loads(i['conn_config'])
                i['quota'] = custom_conf['quota'].get(i['name'], default_quota)
                i['backup_count'] = custom_conf['backup_count'].get(i['id'], 0)
            return data_list
        except:
            pass

    """
    @name 初始化参数
    """

    def _get_site_args(self, get):



        get.search_key=get.table
        if hasattr(get, 'search'):
            get.search_key=get.table
            public.set_search_history(get.table,get.search_key,get.search)
        
        return get

    """
    @name 追加 or条件
    """

    def get_search_where(self, get):

        return get.where, get.params

    """
    @获取网站查询条件，追加and查询条件
    """

    def get_data_where(self, get):
        get = self._get_site_args(get)
        wheres = ["LOWER(type) = LOWER('MySQL')"]
        if "sid" in get:
            sid = get.get("sid")
            wheres.append("sid = {}".format(sid))
        if "type_id" in get:
            type_id = get.get("type_id")
            wheres.append("type_id = {}".format(type_id))
        return wheres

    def get_database_quota(self, names):
        '''
            @name 获取网站目录配额信息
            @author hwliang<2022-02-15>
            @param path<string> 网站目录
            @return dict
        '''
        res = {
            "used": 0,
            "size": 0,
            "quota_push": {
                "size": 0,
                "used": 0,
            },
            "quota_storage": {
                "size": 0,
                "used": 0,
            }
        }
        resutl = {}
        for name in names:
            content = res
            try:
                import PluginLoader
                quota_info = PluginLoader.module_run('quota', 'get_quota_mysql', name)
                if isinstance(quota_info, dict):
                    quota_info["size"] = quota_info["quota_storage"]["size"]
                    content = quota_info
            except:
                pass
            resutl[name] = content
        return resutl

    def get_database_backup_count(self, ids):
        '''
            @name 获取网站目录备份数量信息
        '''
        try:
            res = public.M('backup').query("SELECT pid,COUNT(*) as count FROM backup WHERE pid in ({}) AND type='1' GROUP BY pid".format(','.join(ids)))
            return {i[0]: i[1] for i in res}
        except:
            return {}
