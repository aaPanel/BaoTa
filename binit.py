#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------
import sys,os
os.chdir('/www/server/panel')
sys.path.insert(0,'class')
import public

f_list = [
    {"s_file":"./class/panelPlugin_backup.py","d_file":"./class/panelPlugin.py"},
    {"s_file":"./class/panelAuth_backup.py","d_file":"./class/panelAuth.py"},
    {"s_file":"./BTPanel/__init___backup.py","d_file":"./BTPanel/__init__.py"}
    ]


for i in range(len(f_list)):
    if not os.path.exists(f_list[i]['s_file']): print("file not exists: %s" % f_list[i]['s_file'])
    t_body = public.readFile(f_list[i]['s_file'])
    d_body = public.to_btint(t_body)
    s_body = '''#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------
import sys,os
os.chdir('/www/server/panel')
sys.path.insert(0,'class')
import public
exec(public.to_string(%s))
''' % d_body
    public.writeFile(f_list[i]['d_file'],s_body)
    print("Successify : %s" % f_list[i]['d_file'])


