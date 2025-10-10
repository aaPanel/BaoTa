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
from datalistModel.base import dataBase


class main(dataBase):

    def __init__(self):
        pass

    """
    @name 获取公共数据后，格式化为网站列表需要的数据
    """
    def get_data_list(self, get):
        return get.data_list

    """
    @追加and查询条件
    """
    def get_data_where(self,get):
        wheres = []
        if 'pid' in get:
            wheres.append(("(pid = ?)", (get.pid)))
        return wheres