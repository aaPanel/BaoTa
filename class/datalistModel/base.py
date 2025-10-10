# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: cjxin <cjxin@bt.cn>
# -------------------------------------------------------------------
# 面板获取列表公共库
# ------------------------------

import os,sys,time,json,db,re
import public


class dataBase:

    quota_conf = os.path.join(public.get_panel_path(), "config/quota_list.json")

    def __init__(self):
        pass

    """
    @name 获取配额数据列表
    """
    def get_quota_list(self):
        quota_dict = {}
        try:
            quota_dict = json.loads(public.readFile(self.quota_conf))
        except:
            pass
        return quota_dict


    """
    @name 批量获取所有容量配额
    """
    def get_all_quota(self,paths = []):
        n_paths = []
        confs = self.get_quota_list()


        for path in paths:
            if path in n_paths: continue
            if not path in confs: continue
            n_paths.append(path.strip())

        res = public.get_size_total(n_paths)

        n_data = {}
        for val in n_paths:
            n_data[val] = {"used":0,"size":0,"quota_push":{"size":0,"used":0},"quota_storage":{"size":0,"used":0}}
            if val in confs.keys():
                n_data[val] = confs[val]

            n_data[val]['used'] = -1
            for key in res.keys():
                if key != val: continue

                n_data[val]['used'] = res[val]
                n_data[val]['quota_storage']['used'] = res[val]
                n_data[val]['quota_push']['used'] = res[val]

        print(n_data)
        return n_data