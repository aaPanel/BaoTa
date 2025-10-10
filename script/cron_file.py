# -*- coding: UTF-8 -*-
"""
@FileName：cron_file.py\n
@Description：\n
@Author：Bacon-Wu\n
@Time：2024/1/20 11:17\n
"""
import sys, os
import time
os.chdir('/www/server/panel')
sys.path.insert(0, "class/")
sys.path.insert(0, '/www/server/panel')
import public
import PluginLoader
from mod.base.push_mod import push_by_task_keyword

class main:
    def __check_auth(self):
        try:
            from pluginAuth import Plugin
            plugin_obj = Plugin(False)
            plugin_list = plugin_obj.get_plugin_list()
            if int(plugin_list['ltd']) > time.time():
                return True
            return False
        except:return False

    def run(self):
        pay = self.__check_auth()
        args = public.dict_obj()
        args.model_index = 'project'
        res = PluginLoader.module_run('safe_detect', 'file_detect', args)
        if isinstance(res, dict) and "err_list" in res and len(res['err_list']) > 0:
            msg_list = ["检测到以下关键执行文件被篡改:"]
            for i in res['err_list']:
                msg_list.append(i['Path'])
            msg_list.append("请及时处理。")

            push_by_task_keyword("file_detect", "file_detect", {"msg_list": msg_list})


if __name__ == '__main__':
    channels = sys.argv[1]
    main = main()
    main.run()
