#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http:#bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
#-------------------------------------------------------------------

#------------------------------
# 开机自启模块
#------------------------------

import os,sys,time,json,psutil,re
import public
import signal

class panelRun:
    __panel_path = public.get_panel_path()
    __run_config_path = '{}/config/run_config'.format(__panel_path)
    __run_pids_path = '{}/logs/run_pids'.format(__panel_path)
    __run_logs_path = '{}/logs/run_logs'.format(__panel_path)
    __log_name = '开机启动项'


    def __init__(self):
        if not os.path.exists(self.__run_config_path):
            os.makedirs(self.__run_config_path)
        if not os.path.exists(self.__run_pids_path):
            os.makedirs(self.__run_pids_path)

    def get_run_list(self,get):
        '''
            @name 获取启动配置列表
            @author hwliang<2021-08-06>
            @param get<dict_obj>{
                run_type: string<启动类型>
            }
            @return list
        '''
        run_type = None
        if 'run_type' in get:
            run_type = get['run_type']
        run_list = []
        for run_name in os.listdir(self.__run_config_path):
            run_file = '{}/{}'.format(self.__run_config_path,run_name)
            if not os.path.isfile(run_file):
                continue

            run_info = json.loads(public.readFile(run_file))
            if run_type:
                if run_info['run_type'] != run_type: continue


            run_list.append(run_info)

        return run_list


    def get_run_info(self,get = None,run_name = None):
        '''
            @name 获取启动配置信息
            @author hwliang<2021-08-06>
            @param get<dict_obj>{
                run_name: string<启动项名称>
            }
            @return dict
        '''
        if get: run_name = get['run_name']
        run_file = '{}/{}'.format(self.__run_config_path,run_name)
        if not os.path.isfile(run_file):
            return public.returnMsg(False,'启动配置不存在!')

        run_info = json.loads(public.readFile(run_file))
        return run_info


    def create_run(self,get):
        '''
            @name 创建启动配置
            @author hwliang<2021-08-06>
            @param get<dict_obj>{
                run_title: string<启动项显示标题>
                run_name: string<启动项名称> 格式：\w
                run_type: string<启动类型> python shell php node java等，也可以是一个可执行文件的路径 或直接为空
                run_path: string<运行目录>
                run_script: string<启动脚本>
                run_script_args: string<启动脚本参数>
                run_env: list<启动环境变量>
            }
            @return dict
        '''
        run_name = get['run_name']
        run_title = get['run_title']
        run_type = get['run_type']
        run_path = get['run_path']
        run_script = get['run_script']
        run_script_args = get['run_script_args']
        run_env = json.loads(get['run_env'])
        if not os.path.exists(run_path):
            return public.returnMsg(False,'指定运行目录{}不存在!'.format(run_path))

        if not re.match(r'^\w+$',run_name):
            return public.returnMsg(False, '启动项名称格式不正确，支持:[a-zA-Z0-9_]!')

        run_file = '{}/{}'.format(self.__run_config_path,run_name)
        if os.path.exists(run_file):
            return public.returnMsg(False,'启动配置已存在!')

        run_info = {
            'run_title': run_title,
            'run_name': run_name,
            'run_path': run_path,
            'run_script': run_script,
            'run_env':run_env,
            'run_status': 1
        }
        run_info = json.dumps(run_info)
        public.writeFile(run_file,run_info)
        public.WriteLog(self.__log_name,'创建启动项[]成功!'.format(run_title))
        return public.returnMsg(True,'创建成功!')


    def modify_run(self,get):
        '''
            @name 修改启动配置
            @author hwliang<2021-08-06>
            @param get<dict_obj>{
                run_name: string<启动项名称>
                run_title: string<启动项显示标题>
                run_type: string<启动类型>
                run_path: string<启动路径>
                run_script: string<启动脚本>
                run_script_args: string<启动脚本参数>
            }
            @return dict
        '''

        run_name = get['run_name']
        run_title = get['run_title']
        run_type = get['run_type']
        run_path = get['run_path']
        run_script = get['run_script']
        run_script_args = get['run_script_args']
        run_env = json.loads(get['run_env'])

        if not os.path.exists(run_path):
            return public.returnMsg(False,'指定运行目录{}不存在!'.format(run_path))

        if not re.match(r'^\w+$',run_name):
            return public.returnMsg(False, '启动项名称格式不正确，支持:[a-zA-Z0-9_]!')


        run_file = '{}/{}'.format(self.__run_config_path,run_name)
        if not os.path.exists(run_file):
            return public.returnMsg(False,'启动配置不存在!')

        run_info = json.loads(public.readFile(run_file))
        run_info['run_title'] = run_title
        run_info['run_path'] = run_path
        run_info['run_script'] = run_script
        run_info['run_env'] = run_env
        run_info = json.dumps(run_info)
        public.writeFile(run_file,run_info)
        public.WriteLog(self.__log_name,'修改启动项[]成功!'.format(run_title))
        return public.returnMsg(True,'修改成功!')


    def remove_run(self,get):
        '''
            @name 删除启动配置
            @author hwliang<2021-08-06>
            @param get<dict_obj>{
                run_name: string<启动项名称>
            }
            @return dict
        '''
        run_name = get['run_name']
        run_file = '{}/{}'.format(self.__run_config_path,run_name)
        if not os.path.isfile(run_file):
            return public.returnMsg(False,'启动配置不存在!')

        os.remove(run_file)
        public.WriteLog(self.__log_name,'删除启动项[]成功!'.format(run_name))
        return public.returnMsg(True,'删除成功!')

    def set_run_status(self,get):
        '''
            @name 设置启动项状态
            @author hwliang<2021-08-06>
            @param get<dict_obj>{
                run_name: string<启动项名称>
                run_status: int<启动项状态>
            }
            @return dict
        '''
        run_name = get['run_name']
        run_status = get['run_status']

        run_file = '{}/{}'.format(self.__run_config_path,run_name)
        if not os.path.isfile(run_file):
            return public.returnMsg(False,'启动配置不存在!')

        run_info = json.loads(public.readFile(run_file))
        run_info['run_status'] = run_status
        run_info = json.dumps(run_info)
        public.writeFile(run_file,run_info)
        public.WriteLog(self.__log_name,'设置启动项[]状态成功!'.format(run_info['title']))
        return public.returnMsg(True,'设置成功!')


    def stop_run(self,run_name = None):
        '''
            @name 关闭启动进程
            @author hwliang<2021-08-06>
            @param run_name: string<启动项名称>
            @return dict
        '''
        pid = self.get_run_pid(run_name)
        if not pid: return True
        os.kill(pid,signal.SIGKILL)
        public.WriteLog(self.__log_name,'关闭启动项[]成功!'.format(run_name))
        return True


    def pid_exists(self,pid):
        '''
            @name 检测PID是否存在
            @author hwliang<2021-08-06>
            @param pid int<PID>
            @return bool
        '''
        if not isinstance(pid,int):
            pid = int(pid)
        if pid == 0:
            return True
        if not os.path.exists('/proc/{}'.format(pid)):
            return False
        return True


    def get_run_pid(self,run_name):
        '''
            @name 获取启动项PID
            @author hwliang<2021-08-06>
            @param run_name string<启动项名称>
            @return dict
        '''
        pid_file = '{}/{}.pid'.format(self.__run_pids_path,run_name)
        if not os.path.exists(pid_file):
            return None

        run_pid = int(public.readFile(pid_file))
        if run_pid is 0:
            return None

        if not self.pid_exists(run_pid):
            return None
        return run_pid


    def get_run_status(self,run_name):
        '''
            @name 获取启动项状态
            @author hwliang<2021-08-06>
            @param run_name string<启动项名称>
            @return dict
        '''
        pid = self.get_run_pid(run_name)
        if not pid: return public.returnMsg(False,'未启动')
        process_info = self.get_process_info(pid)
        if not process_info: return public.returnMsg(False,'无法获取进程信息')
        return process_info

    def get_process_info(self,pid):
        '''
            @name 获取进程信息
            @author hwliang<2021-08-06>
            @param pid int<PID>
            @return dict
        '''
        process_info = {}
        p = psutil.Process(pid)
        status_ps = {'sleeping':'睡眠','running':'活动'}
        with p.oneshot():
            p_mem = p.memory_full_info()
            if p_mem.uss + p_mem.rss + p_mem.pss + p_mem.data == 0: return False
            pio = p.io_counters()
            p_cpus= p.cpu_times()
            p_state = p.status()
            if p_state in status_ps: p_state = status_ps[p_state]
            process_info['exe'] = p.exe()
            process_info['name'] = p.name()
            process_info['pid'] = pid
            process_info['ppid'] = p.ppid()
            process_info['create_time'] = int(p.create_time())
            process_info['status'] = p_state
            process_info['user'] = p.username()
            process_info['memory_used'] = p_mem.uss
            # process_info['cpu_percent'] = self.get_cpu_percent(str(pid),p_cpus,self.new_info['cpu_time'])
            process_info['io_write_bytes'] = pio.write_bytes
            process_info['io_read_bytes'] = pio.read_bytes
            # process_info['io_write_speed'] = self.get_io_write(str(pid),pio.write_bytes)
            # process_info['io_read_speed'] = self.get_io_read(str(pid),pio.read_bytes)
            process_info['connects'] = self.get_connects(pid)
            process_info['threads'] = p.num_threads()
        return process_info


    def get_connects(self,pid):
        '''
            @name 获取进程连接数
            @author hwliang<2021-08-06>
            @param pid int<PID>
            @return dict
        '''
        connects = 0
        if pid == 1: return connects
        tp = '/proc/' + str(pid) + '/fd/'
        if not os.path.exists(tp): return connects
        for d in os.listdir(tp):
            fname = tp + d
            if os.path.islink(fname):
                l = os.readlink(fname)
                if l.find('socket:') != -1: connects += 1
        return connects

    def is_run(self,run_name):
        '''
            @name 检测启动项是否在运行
            @author hwliang<2021-08-06>
            @param run_name string<启动项名称>
            @return bool
        '''
        pid = self.get_run_pid(run_name)
        if not pid: return False
        return True


    def get_script_pid(self,run_info):
        '''
            @name 获取脚本进程PID
            @author hwliang<2021-08-06>
            @param run_info dict<脚本文件路径>
            @return int<PID>
        '''
        script_last = run_info['run_script'].split(' ')[0]
        for pid in psutil.pids():
            p = psutil.Process(pid)
            if p.exe() == script_last and p.cwd() == run_info['run_path']:
                return pid
        return None


    def start_run(self,run_name):
        '''
            @name 启动指定启动项
            @author hwliang<2021-08-06>
            @param run_name string<启动项名称>
            @return bool
        '''
        run_info = self.get_run_info(run_name)
        if not run_info: return False

        log_file = '{}/{}.log'.format(self.__run_logs_path,run_name)
        pid_file = '{}/{}.pid'.format(self.__run_pids_path,run_name)
        public.ExecShell("nohup {} 2>&1 >> {} & $! > {}".format(run_info['run_script'],log_file,pid_file),cwd=run_info['run_path'],env=run_info['run_env'])[0]
        time.sleep(1)
        pid = self.get_script_pid(run_info)
        public.writeFile(pid_file,str(pid))
        public.WriteLog(self.__log_name, '开机启动{}成功, PID: {}'.format(run_name,pid))
        return True


    def start(self):
        '''
            @name 启动所有启动项
            @author hwliang<2021-08-06>
            @param
            @return bool
        '''
        run_list = self.get_run_list(public.dict_obj())
        for run_name in run_list:
            if not self.is_run(run_name):
                self.start_run(run_name)
        return True

