#coding: utf-8
import sys,os
os.chdir('/www/server/panel/')
sys.path.insert(0,"class/")
import public
import http_requests
http_requests.DEFAULT_TYPE = 'src'

url1 = 'https://check.bt.cn/api/panel/check_files'
pdata = {'panel_version': public.version(), 'address': public.get_ipaddress()}
result = http_requests.post(url1, pdata).text
print(result)
