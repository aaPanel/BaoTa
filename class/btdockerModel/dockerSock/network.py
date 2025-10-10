# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------
# docker模型sock 封装库 网络库
# -------------------------------------------------------------------
import json

import public
from btdockerModel.dockerSock.sockBase import base


class dockerNetWork(base):
    def __init__(self):
        super(dockerNetWork, self).__init__()

    # 2024/11/27 14:31 list network
    def list_network(self):
        '''
            @name list network
        '''
        try:
            return json.loads(public.ExecShell("curl -s --unix-socket {} http:/{}/networks".format(self._sock, self.get_api_version()))[0])
        except Exception as e:
            try:
                c_list = public.ExecShell("whereis curl | awk 'print {$1}'")[0].split(" ")
                for c in c_list:
                    if not c.endswith("/curl"): continue
                    res, err = public.ExecShell("{} -s --unix-socket {} http:/{}/networks".format(c, self._sock, self.get_api_version()))
                    if not err: return json.loads(res)
                return []
            except:
                return []

    # 2024/11/27 14:33 inspect a network
    def inspect_network(self, get):
        '''
            @name inspect a network
        '''
        try:
            return json.loads(public.ExecShell("curl -s --unix-socket {} http:/{}/networks/{}".format(self._sock, self.get_api_version(), get.id))[0])
        except Exception as e:
            try:
                c_list = public.ExecShell("whereis curl | awk 'print {$1}'")[0].split(" ")
                for c in c_list:
                    if not c.endswith("/curl"): continue
                    res, err = public.ExecShell("{} -s --unix-socket {} http:/{}/networks/{}".format(c, self._sock, self.get_api_version(), get.id))
                    if not err: return json.loads(res)
                return {}
            except:
                return {}

    # 2024/11/27 14:34 remove network
    def remove_network(self, get):
        '''
            @name remove network
        '''
        try:
            return json.loads(public.ExecShell("curl -s -X DELETE --unix-socket {} http:/{}/networks/{}".format(self._sock, self.get_api_version(), get.id))[0])
        except Exception as e:
            try:
                c_list = public.ExecShell("whereis curl | awk 'print {$1}'")[0].split(" ")
                for c in c_list:
                    if not c.endswith("/curl"): continue
                    res, err = public.ExecShell("{} -s -X DELETE --unix-socket {} http:/{}/networks/{}".format(c, self._sock, self.get_api_version(), get.id))
                    if not err: return json.loads(res)
                return {}
            except:
                return {}

    # 2024/11/27 14:34 create network
    def create_network(self, get):
        '''
            @name create network
        '''
        try:
            return json.loads(public.ExecShell("curl -s -X POST --unix-socket {} http:/{}/networks/create -H \"Content-Type: application/json\" -d '{}'".format(self._sock, self.get_api_version(), json.dumps(get.post_data)))[0])
        except Exception as e:
            try:
                c_list = public.ExecShell("whereis curl | awk 'print {$1}'")[0].split(" ")
                for c in c_list:
                    if not c.endswith("/curl"): continue
                    res, err = public.ExecShell("{} -s -X POST --unix-socket {} http:/{}/networks/create -H \"Content-Type: application/json\" -d '{}'".format(c, self._sock, self.get_api_version(), json.dumps(get.post_data)))
                    if not err: return json.loads(res)
                return {}
            except:
                return {}
