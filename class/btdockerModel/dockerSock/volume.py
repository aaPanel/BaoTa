# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------
# docker模型sock 封装库 存储库
# -------------------------------------------------------------------
import json

import public
from btdockerModel.dockerSock.sockBase import base


class dockerVolume(base):
    def __init__(self):
        super(dockerVolume, self).__init__()

    # 2024/3/13 上午 11:20 获取所有存储卷列表
    def get_volumes(self):
        '''
            @name 获取所有存储卷列表
            @author wzz <2024/3/13 上午 10:54>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            return json.loads(public.ExecShell("curl -s --unix-socket {} http:/{}/volumes".format(self._sock, self.get_api_version()))[0])
        except Exception as e:
            try:
                c_list = public.ExecShell("whereis curl | awk 'print {$1}'")[0].split(" ")
                for c in c_list:
                    if not c.endswith("/curl"): continue
                    res, err = public.ExecShell("{} -s --unix-socket {} http:/{}/volumes".format(c, self._sock, self.get_api_version()))
                    if not err: return json.loads(res)
                return []
            except:
                return []
