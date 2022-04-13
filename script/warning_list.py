#coding: utf-8
import os,sys
os.chdir('/www/server/panel')
sys.path.insert(0,'class/')
import panelWarning,public,json
args = public.dict_obj()
result = panelWarning.panelWarning().get_list(args)
print(json.dumps(result))