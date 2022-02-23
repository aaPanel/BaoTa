#coding: utf-8
import os,sys,time
os.chdir('/www/server/panel/')
sys.path.insert(0,"class/")
import setPanelLets,public
from json import loads
lets_info = public.readFile("/www/server/panel/ssl/lets.info")
if lets_info:
    lets_info = loads(lets_info)
    res = setPanelLets.setPanelLets().check_cert_update(lets_info['domain'])
    if res['status'] and res['msg'] == '1':
        strTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))
        public.writeFile("/tmp/panelSSL.pl","{} Panel certificate updated successfully\n".format(strTime),"a+")
        public.writeFile('/www/server/panel/data/reload.pl',"1")