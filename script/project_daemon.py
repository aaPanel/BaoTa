import os
import sys
import time

import psutil

panel_path = '/www/server/panel'
os.chdir(panel_path)
if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

import public


def JavaProDaemons():
    '''
        @name Java 项目守护进程
        @author lkq@bt.cn
        @time 2022-07-19
        @param None
    '''
    if public.M('sites').where('project_type=?', ('Java')).count() >= 1:
        project_info = public.M('sites').where('project_type=?', ('Java')).select()
        for i in project_info:
            try:
                import json
                i['project_config'] = json.loads(i['project_config'])
                # 判断项目是否设置了守护进程
                if i['project_config']['java_type'] != 'springboot': continue
                if 'auth' in i['project_config'] and i['project_config']['auth'] == 1 or i['project_config']['auth'] == '1':
                    print("Java", i['name'])
                    from projectModel import javaModel
                    java = javaModel.main()
                    if java.get_project_run_state(project_name=i['name']):
                        continue
                    else:
                        # 如果项目是在后台停止的，那么就不再启动
                        if os.path.exists("/var/tmp/springboot/vhost/pids/{}.pid".format(i['name'])):
                            get = public.dict_obj()
                            get.project_name = i['name']
                            java.start_project(get)
                            public.WriteLog('守护进程', 'Java项目[{}]已经被守护进程启动'.format(i['name']))
            except:
                continue


def GoDaemons():
    '''
        @name Go 项目守护进程
        @author lkq@bt.cn
        @time 2022-07-19
        @param None
    '''
    if public.M('sites').where('project_type=?', ('Go')).count() >= 1:
        project_info = public.M('sites').where('project_type=?', ('Go')).select()
        for i in project_info:
            try:
                import json
                i['project_config'] = json.loads(i['project_config'])
                if 'is_power_on' in i['project_config'] and i['project_config']['is_power_on'] == 1 or i['project_config']['is_power_on'] == '1':
                    from projectModel import goModel
                    java = goModel.main()
                    if java.get_project_run_state(project_name=i['name']):
                        continue
                    else:
                        # 如果项目是在后台停止的，那么就不再启动
                        if os.path.exists("/var/tmp/gopids/{}.pid".format(i['name'])):
                            get = public.dict_obj()
                            get.project_name = i['name']
                            java.start_project(get)
                            public.WriteLog('守护进程', 'Go项目[{}]已经被守护进程启动'.format(i['name']))
            except:
                continue


def PythonDaemons():
    '''
        @name Python 项目守护进程
        @author baozi@bt.cn
        @time 2023-10-21
    '''
    boot_time = psutil.boot_time()
    now = time.time()
    boot_start = int(now - boot_time) < 60 * 10
    if public.M('sites').where('project_type=?', ('Python')).count() >= 1:
        project_info = public.M('sites').where('project_type=?', ('Python')).select()
        for i in project_info:
            try:
                import json
                from projectModel import pythonModel

                i['project_config'] = json.loads(i['project_config'])
                if 'auto_run' in i['project_config'] and i['project_config']['auto_run'] in ["1", 1, True, "true"]:
                    python_obj = pythonModel.main()
                    if python_obj.get_project_run_state(project_name=i['name']):
                        continue
                    else:
                        if not python_obj.is_stop_by_user(i["id"]) or boot_start:
                            # 如果项目是在后台停止的，那么就不再启动
                            get = public.dict_obj()
                            get.name = i['name']
                            python_obj.StartProject(get)
                            public.WriteLog('守护进程', 'Python项目[{}]已经被守护进程启动'.format(i['name']))
            except:
                continue


def NetDaemons():
    '''
        @name Go 项目守护进程
        @author lkq@bt.cn
        @time 2022-07-19
        @param None
    '''
    if public.M('sites').where('project_type=?', ('net')).count() >= 1:
        project_info = public.M('sites').where('project_type=?', ('net')).select()
        for i in project_info:
            try:
                import json
                i['project_config'] = json.loads(i['project_config'])
                if 'is_power_on' in i['project_config'] and i['project_config']['is_power_on'] == 1 or i['project_config']['is_power_on'] == '1':
                    from projectModel import netModel
                    net = netModel.main()
                    if net.get_project_run_state(project_name=i['name']):
                        continue
                    else:
                        # 如果项目是在后台停止的，那么就不再启动
                        if os.path.exists("/var/tmp/net_project/{}.pid".format(i['name'])):
                            get = public.dict_obj()
                            get.project_name = i['name']
                            net.start_project(get)
                            public.WriteLog('守护进程', 'net项目[{}]已经被守护进程启动'.format(i['name']))
            except:
                continue


def OtherDaemons():
    '''
        @name Other 项目守护进程
        @author lkq@bt.cn
        @time 2022-07-19
        @param None
    '''
    if public.M('sites').where('project_type=?', ('Other',)).count() >= 1:
        project_info = public.M('sites').where('project_type=?', ('Other')).select()
        for i in project_info:
            try:
                import json
                i['project_config'] = json.loads(i['project_config'])
                if 'is_power_on' in i['project_config'] and i['project_config']['is_power_on'] == 1 or i['project_config']['is_power_on'] == '1':
                    from projectModel import otherModel
                    other = otherModel.main()
                    if other.get_project_run_state(project_name=i['name']):
                        continue
                    else:
                        # 如果项目是在后台停止的，那么就不再启动
                        if os.path.exists("/var/tmp/other_project/{}.pid".format(i['name'])):
                            get = public.dict_obj()
                            get.project_name = i['name']
                            other.start_project(get)
                            public.WriteLog('守护进程', '通用项目[{}]已经被守护进程启动'.format(i['name']))
            except:
                continue

if __name__ == '__main__':
    JavaProDaemons()
    GoDaemons()
    PythonDaemons()
    NetDaemons()
    OtherDaemons()
