
import os,sys
panel_path = '/www/server/panel'
os.chdir(panel_path)
if not 'class/' in sys.path: sys.path.insert(0,'class/')

import PluginLoader
import public

if __name__ == '__main__':
    import argparse
    args_obj = argparse.ArgumentParser(usage="必要的参数：--echo_id 任务id!")
    args_obj.add_argument("--echo_id", help="任务id")
    args = args_obj.parse_args()
    if not args.echo_id:
        args_obj.print_help()

    get = public.dict_obj()
    get.model_index = "project"
    get.echo_id = args.echo_id
    PluginLoader.module_run("binlog", "execute_by_comandline", get)

