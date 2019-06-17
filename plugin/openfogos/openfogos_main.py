#!/usr/bin/python
# coding: utf-8

import sys, os, json

os.chdir("/www/server/panel")

sys.path.append("class/")
import public

#在非命令行模式下引用面板缓存和session对象
if __name__ != '__main__':
    from BTPanel import cache,session


class openfogos_main:
    __plugin_path = "/www/server/panel/plugin/openfogos/"
    __config = None
    def __init__(self):
        pass 

    def start(self, args):
        # os.popen("wget -O /www/server/panel/plugin/openfogos/openfog https://download.openfogos.com/linux/openfog && /www/server/panel/plugin/openfogos/openfog")
        # os.system("/www/server/panel/plugin/openfogos/openfog")
        ret = os.popen("docker container start openfog && docker ps | grep openfog").readlines()[-1]
        return {'result': ret}
    def state(self, args):
        ret = os.popen("docker ps | grep openfog").readlines()[-1]
        return {'result': ret}
    def stop(self, args):
        ret = os.popen("docker container stop openfog").readlines()[-1]
        return {'result': ret}
    def info(self, args):
        http_body = public.HttpGet("http://localhost:49193/api?method=info", timeout=60)
        return http_body
    def bind(self, args):
        http_body = public.HttpGet("http://localhost:49193/method?p=" + args.phone, timeout=60)
        return http_body

