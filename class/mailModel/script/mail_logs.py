#coding: utf-8

#------------------------------
# 发送结束后筛选日志
#------------------------------
import os,sys
os.chdir('/www/server/panel')
sys.path.insert(0,'class/')
import public


plugin_name = 'mail_sys'
def_name = 'handle_email_log'
import PluginLoader

try:

    args = public.dict_obj()
    # args.plugin_get_object = 1
    print("plugin_name--{}    def_name--{}".format(plugin_name,def_name))
    from mailModel import mainModel
    data = mainModel.main().handle_email_log(args)
    # data = PluginLoader.plugin_run(plugin_name,def_name,args)
    print("|- 发送后过滤日志-{} ".format(data))
except Exception as ex:
    public.print_log(public.get_error_info())
    print(public.get_error_info())
    # print("|- 报错r: " + str(ex))
    print("|- 发送后过滤日志 error: " + str(ex))
