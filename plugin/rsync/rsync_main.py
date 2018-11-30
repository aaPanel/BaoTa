 #coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2019 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------
import sys,os,public;
rsync_init = public.load_module('100000005')
class rsync_main(rsync_init.plugin_rsync_init): pass;
if __name__ == "__main__":
    if sys.argv[1] == 'new':
        p = rsync_main()
        p.to_new_version(None)
