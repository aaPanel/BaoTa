#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http:#bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
#-------------------------------------------------------------------

#------------------------------
# 项目开机自启调用脚本
#------------------------------
import os,sys
panel_path = '/www/server/panel'
os.chdir(panel_path)
if not 'class/' in sys.path: sys.path.insert(0,'class/')
import public,time,psutil
import PluginLoader


def project_model_auto_run():
    '''
        @name 项目模型自启调用
        @author hwliang<2021-08-09>
        @return bool
    '''
    project_model_path = '{}/projectModel'.format(public.get_class_path())
    if not os.path.exists(project_model_path): return False
    for mod_name in os.listdir(project_model_path):
        try:
            if mod_name[-4:] == '.pyc': continue
            if mod_name in ['base.py','__init__.py']: continue
            if mod_name.find('.src.py') != -1: continue
            mod_file = "{}/{}".format(project_model_path,mod_name)
            if not os.path.exists(mod_file): continue
            if not os.path.isfile(mod_file): continue
            try:
                tmp_mod = public.get_script_object(mod_file)
                if not hasattr(tmp_mod,'main'): continue
                run_object = getattr(tmp_mod.main(),'auto_run',None)
                if run_object: run_object()
            except Exception as ex:
                if str(ex).find('invalid token') == -1: continue
                args = public.dict_obj()
                args.module_get_object = 1
                mod_name_last = mod_name.replace("Model.py","")
                run_object = PluginLoader.module_run(mod_name_last,'auto_run',args)
                if isinstance(run_object,dict): continue
                if run_object: run_object()
        except:
            print(public.get_error_info())


def start():
    run_tips = '/dev/shm/bt_auto_run.pl'
    boot_time = psutil.boot_time()
    stime = time.time()
    if os.path.exists(run_tips):
        last_time = int(public.readFile(run_tips))
        if boot_time < last_time: return False
    if stime - 3600 > boot_time: return False

    # --------------------- 调用自启动程序 ---------------------

    project_model_auto_run()

    # --------------------- 结束调用 ---------------------

    public.writeFile(run_tips,str(int(stime)))


if __name__ == '__main__':
    start()