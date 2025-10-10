# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------

# ------------------------------
# Docker模型 - Docker应用
# ------------------------------
import public
import os
import time
import json
import re
from btdockerModel import dk_public as dp
from btdockerModel.dockerBase import dockerBase


class main(dockerBase):

    def __init__(self):
        pass

    # 2024/2/20 下午 4:31 获取/搜索docker应用的列表
    def get_app_list(self, get=None):
        '''
            @name 获取docker应用的 1列表
            @author wzz <2024/2/20 下午 4:32>
            @param "data":{"参数名":""} <数据类型> `参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        from btdockerModel import registryModel as dr
        dr.main().registry_list(get)

        from panelPlugin import panelPlugin
        pp = panelPlugin()
        get.type = 13
        get.force = get.force if "force" in get and get.force else 0
        if not hasattr(get, "query"):
            get.query = ""
        get.tojs = "soft.get_list"
        if get.query != "":
            get.row = 1000
            softList = pp.get_soft_list(get)
            softList['list'] = self.struct_list(softList['list'])
            softList['list'] = pp.get_page(softList['list']['data'], get)
        else:
            softList = pp.get_soft_list(get)

        return softList['list']

    # 2024/2/20 下午 4:47 处理云端软件列表，只需要list中type=13的数据
    def struct_list(self, softList: dict):
        '''
            @name 处理云端软件列表，只需要list中type=13的数据
            @param softList:
            @return:
        '''
        new_list = []
        for i in softList['data']:
            if i['type'] == 13:
                new_list.append(i)

        softList['data'] = new_list

        return softList
