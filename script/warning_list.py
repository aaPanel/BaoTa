#coding: utf-8
import os,sys
os.chdir('/www/server/panel')
sys.path.insert(0,'class/')
import panelWarning,public,json
args = public.dict_obj()
result = panelWarning.panelWarning().get_list(args)
# 从结果中获取得分
score = result.get('score', 100)  # 如果没有score字段，默认为0

# 输出格式化的结果
print("首页风险扫描结束,当前服务器得分:{},请在首页查看".format(score))
# print(json.dumps(result))  # 保留原有的JSON输出，以防其他程序需要解析