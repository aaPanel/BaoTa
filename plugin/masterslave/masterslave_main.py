#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------

import sys,os
sys.path.append('/www/server/panel/class')
import public
masterslave = public.load_module('100000008')
class masterslave_main(masterslave.masterslave_init):pass;
                
                
    