#!/usr/bin/python
#coding: utf-8
# Author: lkqiang<lkq@bt.cn>
# panelWaf.py
# code: 面板基础安全类
# +-------------------------------------------------------------------
import re,json,sys,public,os
flag_file='/www/server/panel/data/tmp1.json'

try:
    import libinjection
except:
    if not os.path.exists(flag_file):
        public.WriteFile(flag_file,'1')
    else:
        count_size=public.ReadFile(flag_file)
        if count_size.strip().isdigit():
            if int(count_size.strip())>= 5:
                    exit(False)
            else:
                public.WriteFile(flag_file, str(int(count_size.strip())+1))
        else:public.WriteFile(flag_file,'1')
    if os.path.exists('/www/server/panel/pyenv/bin/python3'):
        public.ExecShell('/www/server/panel/pyenv/bin/pip install Cython')
        public.ExecShell('/www/server/panel/pyenv/bin/pip install libinjection-python')
    else:
        public.ExecShell('pip install Cython')
        public.ExecShell('pip install libinjection-python')

class panelWaf:
    ##json_data => {"username":"admin","password":"123456!@#$%%^"}
    def is_sql(self,json_data):
        for i in json_data:
            try:
                if type(json_data[i])==str:
                    if libinjection.is_sql_injection(json_data[i])['is_sqli']:
                        return True
            except:continue
        else:return False

    ##json_data => {"username":"admin","password":"123456!@#$%%^"}
    def is_xss(self,json_data):
        for i in json_data:
            try:
                if type(json_data[i]) == str:
                    if libinjection.is_xss(json_data[i])['is_xss']:
                        return True
            except:continue
        else:return False