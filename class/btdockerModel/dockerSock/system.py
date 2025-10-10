# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------
# docker模型sock 封装库 系统信息库
# -------------------------------------------------------------------


import json
import public
from btdockerModel.dockerSock.sockBase import base


class dockerSystem(base):
    def __init__(self):
        super(dockerSystem, self).__init__()

    # 2024/12/16 17:47 获取系统信息
    def get_system_info(self):
        '''
            @name 获取系统信息
        '''
        try:
            return json.loads(public.ExecShell("curl -s --unix-socket {} http:/{}/info".format(self._sock, self.get_api_version()))[0])
        except Exception as e:
            try:
                c_list = public.ExecShell("whereis curl | awk 'print {$1}'")[0].split(" ")
                for c in c_list:
                    if not c.endswith("/curl"): continue
                    res, err = public.ExecShell("{} -s --unix-socket {} http:/{}/info".format(c, self._sock, self.get_api_version()))
                    if not err: return json.loads(res)
                return []
            except:
                return []

