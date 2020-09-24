#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------

import os,sys
os.chdir('/www/server/panel')
sys.path.insert(0,'class')
import public

p = public.get_modules('class/safe_warning')
print(p['sw_site_spath'].check_run())