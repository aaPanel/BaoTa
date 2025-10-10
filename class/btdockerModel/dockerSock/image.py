# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------
# docker模型sock 封装库 镜像库
# -------------------------------------------------------------------
import json

import public
from btdockerModel.dockerSock.sockBase import base


class dockerImage(base):
    def __init__(self):
        super(dockerImage, self).__init__()

    # 2024/3/13 上午 11:20 获取所有镜像列表
    def get_images(self):
        '''
            @name 获取所有镜像列表
            @author wzz <2024/3/13 上午 10:54>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            return json.loads(public.ExecShell("curl -s --unix-socket {} http:/{}/images/json?all=1".format(self._sock, self.get_api_version()))[0])
        except Exception as e:
            try:
                c_list = public.ExecShell("whereis curl | awk 'print {$1}'")[0].split(" ")
                for c in c_list:
                    if not c.endswith("/curl"): continue
                    res, err = public.ExecShell("{} -s --unix-socket {} http:/{}/images/json?all=1".format(c, self._sock, self.get_api_version()))
                    if not err: return json.loads(res)
                return []
            except:
                return []

    # 2023/12/13 上午 11:08 镜像搜索
    def search(self, name):
        '''
            @name 镜像搜索
            @author wzz <2023/12/13 下午 3:41>
            @param 参数名<数据类型> 参数描述
            @return 数据类型
        '''
        try:
            return json.loads(public.ExecShell("curl -s --unix-socket {} http:/{}/images/search?term={}".format(self._sock, self.get_api_version(), name))[0],)
        except Exception as e:
            try:
                c_list = public.ExecShell("whereis curl | awk 'print {$1}'")[0].split(" ")
                for c in c_list:
                    if not c.endswith("/curl"): continue
                    res, err = public.ExecShell("{} -s --unix-socket {} http:/{}/images/search?term={}".format(c, self._sock, self.get_api_version(), name))
                    if not err: return json.loads(res)
                return []
            except:
                return []

    # 2024/4/1 下午 2:47 image load
    def load_image(self, path):
        '''
            @name 加载镜像
            @param path <str> 镜像名称
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            return json.loads(public.ExecShell("curl -s --unix-socket {} -X POST http:/{}/images/load -H \"Content-Type: application/x-tar\" --upload-file {}".format(self._sock, self.get_api_version(), path))[0])
        except Exception as e:
            return {}

    # 2024/4/16 上午11:39 获取指定image的inspect信息
    def inspect(self, image):
        '''
            @name 获取指定image的inspect信息
            @param image <str> 镜像名称
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            return json.loads(public.ExecShell("curl -s --unix-socket {} http:/{}/images/{}/json".format(self._sock, self.get_api_version(), image))[0])
        except Exception as e:
            try:
                c_list = public.ExecShell("whereis curl | awk 'print {$1}'")[0].split(" ")
                for c in c_list:
                    if not c.endswith("/curl"): continue
                    res, err = public.ExecShell("{} -s --unix-socket {} http:/{}/images/{}/json".format(c, self._sock, self.get_api_version(), image))
                    if not err: return json.loads(res)
                return {}
            except:
                return {}

    # 2024/10/31 22:43 清理所有构建缓存
    def build_prune(self):
        '''
            @name 清理所有构建缓存
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            return json.loads(public.ExecShell("curl -s --unix-socket {} -X POST http:/{}/build/prune?all=1"
            .format(self._sock, self.get_api_version()))[0])
        except Exception as e:
            return False
