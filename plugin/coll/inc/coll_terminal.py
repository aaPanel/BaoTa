#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 6.x
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   微架构 - 终端
#+--------------------------------------------------------------------
import base64,binascii
class coll_terminal:
    
    def __init__(self):
        pass
    
    def __get_find(self,sid):
        pass

    def test(self,msg):
        return {'msg':msg}
    


    def _encode(self,data):
        data = base64.b64encode(data)
        return binascii.hexlify(data)

    def _decode(self,data):
         data = binascii.unhexlify(data)
         return base64.b64decode(data)