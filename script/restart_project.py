# -*- coding: utf-8 -*-
import sys
import os
from importlib import import_module
from typing import Optional, Any

# 将模块的路径添加到系统路径中
if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, '/www/server/panel/class')

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, '/www/server/panel')


os.chdir('/www/server/panel')


import public


def get_action_model_obj(model_name: str) -> Optional[Any]:
    try:
        if model_name in "java" and os.path.exists("/www/server/panel/mod/project/java/projectMod.py"):
            model = import_module("mod.project.java.projectMod")
        else:
            model = import_module("projectModel." + model_name + "Model")
    except:
        return None

    if not hasattr(model, "main"):
        return None
    main_class = getattr(model, "main")
    if not callable(main_class):
        return None
    return main_class()


def restart_project_based_on_model(model_name: str, project_name: str):
    try:
        print("开始执行重启操作")
        model_obj = get_action_model_obj(model_name)
        if not model_obj:
            print("加载操作类错误")
            return
        get = public.dict_obj()
        if model_name == "python":
            get.name = project_name
            res=model_obj.RestartProject(get)

        else:
            get.project_name = project_name
            res=model_obj.restart_project(get)
        if res['status']:            
            print("重启项目{}成功！".format(project_name))
        else:
            print("重启项目{}失败,请尝试在网站页面是否能够手动启动该项目！".format(project_name))
    except Exception as e:
        print(public.get_error_info())
        print("获取失败" + str(e))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("参数传递错误, 无法执行，您可以删除当前计划任务后，重新添加")
    restart_project_based_on_model(sys.argv[1], sys.argv[2])
