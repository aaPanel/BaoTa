
#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   宝塔防篡改程序
#+--------------------------------------------------------------------
import sys,os,public,json;
def load_module(pluginCode):
    from imp import new_module
    pluginInfo = None
    if not pluginInfo:
        import panelAuth
        pdata = panelAuth.panelAuth().create_serverid(None)
        pdata['pid'] = pluginCode
        url = 'http://www.bt.cn/api/panel/get_py_module'
        pluginTmp = public.httpPost(url,pdata)
        pluginInfo = json.loads(pluginTmp)
        if pluginInfo['status'] == False: return False

    mod = sys.modules.setdefault(pluginCode, new_module(pluginCode))
    code = compile(pluginInfo['msg'].encode('utf-8'),pluginCode, 'exec')
    mod.__file__ = pluginCode
    mod.__package__ = ''
    exec(code, mod.__dict__)
    return mod
#tamper_proof = load_module('100000015')
tamper_proof = __import__('100000015_main')
class tamper_proof_main(tamper_proof.tamper_proof_init):pass;


