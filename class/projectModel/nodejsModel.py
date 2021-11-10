#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
#-------------------------------------------------------------------

#------------------------------
# node.js模型
#------------------------------
import os,sys,re,json,shutil,psutil,time
from projectModel.base import projectBase
import public
try:
    from BTPanel import cache
except:
    pass

class main(projectBase):
    _panel_path = public.get_panel_path()
    _nodejs_plugin_path = public.get_plugin_path('nodejs')
    _nodejs_path = '{}/nodejs'.format(public.get_setup_path())
    _log_name = '项目管理'
    _npm_exec_log = '{}/logs/npm-exec.log'.format(_panel_path)
    _node_pid_path = '{}/vhost/pids'.format(_nodejs_path)
    _node_logs_path = '{}/vhost/logs'.format(_nodejs_path)
    _node_run_scripts = '{}/vhost/scripts'.format(_nodejs_path)
    _pids = None
    _vhost_path = '{}/vhost'.format(_panel_path)
    _www_home = '/home/www'



    def __init__(self):
        if not os.path.exists(self._node_run_scripts):
            os.makedirs(self._node_run_scripts,493)

        if not os.path.exists(self._node_pid_path):
            os.makedirs(self._node_pid_path,493)

        if not os.path.exists(self._node_logs_path):
            os.makedirs(self._node_logs_path,493)
        
        if not os.path.exists(self._www_home):
            os.makedirs(self._www_home,493)
            public.set_own(self._www_home,'www')


    def get_exec_logs(self,get):
        '''
            @name 获取执行日志
            @author hwliang<2021-08-09>
            @param get<dict_obj>
            @return string
        '''
        if not os.path.exists(self._npm_exec_log): return public.returnMsg(False,'NODE_NOT_EXISTS')
        return public.GetNumLines(self._npm_exec_log,20)
            

    def get_project_list(self,get):
        '''
            @name 获取项目列表
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''

        if not 'p' in get:  get.p = 1
        if not 'limit' in get: get.limit = 20
        if not 'callback' in get: get.callback = ''
        if not 'order' in get: get.order = 'id desc'

        if 'search' in get:
            get.project_name = get.search.strip()
            search = "%{}%".format(get.project_name)
            count = public.M('sites').where('project_type=? AND (name LIKE ? OR ps LIKE ?)',('Node',search,search)).count()
            data = public.get_page(count,int(get.p),int(get.limit),get.callback)
            data['data'] = public.M('sites').where('project_type=? AND (name LIKE ? OR ps LIKE ?)',('Node',search,search)).limit(data['shift'] + ',' + data['row']).order(get.order).select()
        else:
            count = public.M('sites').where('project_type=?','Node').count()
            data = public.get_page(count,int(get.p),int(get.limit),get.callback)
            data['data'] = public.M('sites').where('project_type=?','Node').limit(data['shift'] + ',' + data['row']).order(get.order).select()

        for i in range(len(data['data'])):
            data['data'][i] = self.get_project_stat(data['data'][i])
        return data


    def get_ssl_end_date(self,project_name):
        '''
            @name 获取SSL信息
            @author hwliang<2021-08-09>
            @param project_name <string> 项目名称
            @return dict
        '''
        import data
        return data.data().get_site_ssl_info('node_{}'.format(project_name))


    
    def is_install_nodejs(self,get):
        '''
            @name 是否安装nodejs版本管理器
            @author hwliang<2021-08-09>
            @param get<dict_obj> 请求数据
            @return bool
        '''
        return os.path.exists(self._nodejs_plugin_path)


    def get_nodejs_version(self,get):
        '''
            @name 获取已安装的nodejs版本
            @author hwliang<2021-08-09>
            @param get<dict_obj> 请求数据
            @return list
        '''
        nodejs_list = []
        if not os.path.exists(self._nodejs_path): return nodejs_list
        for v in os.listdir(self._nodejs_path):
            if v[0] != 'v' or v.find('.') == -1: continue
            nodejs_list.append(v)
        return nodejs_list



    def get_run_list(self,get):
        '''
            @name 获取node项目启动列表
            @author hwliang<2021-08-10>
            @param get<dict_obj>{
                project_cwd: string<项目目录>
            }
        '''
        project_cwd = get.project_cwd.strip()
        if not os.path.exists(project_cwd): return public.return_error('项目目录不存在!')
        package_file = '{}/package.json'.format(project_cwd)
        if not os.path.exists(package_file): return {} #public.return_error('没有在项目目录中找到package.json配置文件!')
        package_info = json.loads(public.readFile(package_file))
        if not 'scripts' in package_info: return {}# public.return_error('没有在项目配置文件package.json中找到scripts配置项!')
        if not package_info['scripts']: return {}# public.return_error('没有找到可用的启动选项!')
        return package_info['scripts']


    def get_npm_bin(self,nodejs_version):
        '''
            @name 获取指定node版本的npm路径
            @author hwliang<2021-08-10>
            @param nodejs_version<string> nodejs版本
            @return string
        '''
        npm_path = '{}/{}/bin/npm'.format(self._nodejs_path,nodejs_version)
        if not os.path.exists(npm_path): return False
        return npm_path

    def get_yarn_bin(self,nodejs_version):
        '''
            @name 获取指定node版本的yarn路径
            @author hwliang<2021-08-28>
            @param nodejs_version<string> nodejs版本
            @return string
        '''
        yarn_path = '{}/{}/bin/yarn'.format(self._nodejs_path,nodejs_version)
        if not os.path.exists(yarn_path): return False
        return yarn_path


    def get_node_bin(self,nodejs_version):
        '''
            @name 获取指定node版本的node路径
            @author hwliang<2021-08-10>
            @param nodejs_version<string> nodejs版本
            @return string
        '''
        node_path = '{}/{}/bin/node'.format(self._nodejs_path,nodejs_version)
        if not os.path.exists(node_path): return False
        return node_path


    def get_last_env(self,nodejs_version,project_cwd = None):
        '''
            @name 获取前置环境变量
            @author hwliang<2021-08-25>
            @param nodejs_version<string> Node版本
            @return string
        '''
        nodejs_bin_path = '{}/{}/bin'.format(self._nodejs_path,nodejs_version)
        if project_cwd:
            _bin = '{}/node_modules/.bin'.format(project_cwd)
            if os.path.exists(_bin):
                nodejs_bin_path = _bin + ':' + nodejs_bin_path
        
        last_env = '''PATH={nodejs_bin_path}:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
'''.format(nodejs_bin_path = nodejs_bin_path)
        return last_env
        

    def install_packages(self,get):
        '''
            @name 安装指定项目的依赖包
            @author hwliang<2021-08-10>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            return dict
        '''
        project_find = self.get_project_find(get.project_name)
        if not project_find: return public.return_error('指定项目不存在!')
        if not os.path.exists(project_find['path']): return public.return_error('项目目录不存在!')
        package_file = '{}/package.json'.format(project_find['path'])
        if not os.path.exists(package_file): return public.return_error('没有在项目目录中找到package.json配置文件!')
        nodejs_version = project_find['project_config']['nodejs_version']
        
        package_lock_file = '{}/package-lock.json'.format(project_find['path'])
        node_modules_path = '{}/node_modules'.format(project_find['path'])

        # 已经安装过的依赖包的情况下，可能存在不同node版本导致的问题，可能需要重新构建依赖包
        rebuild = False
        if os.path.exists(package_lock_file) and os.path.exists(node_modules_path): 
            rebuild = True

        npm_bin = self.get_npm_bin(nodejs_version)
        yarn_bin = self.get_yarn_bin(nodejs_version)
        if not npm_bin and not yarn_bin: 
            return public.return_error('指定nodejs版本不存在!')
        public.writeFile(self._npm_exec_log,"正在安装依赖包...\n")
        public.writeFile(self._npm_exec_log,"正在下载依赖包,请稍后...\n")
        if yarn_bin:
            if os.path.exists(package_lock_file): 
                os.remove(package_lock_file)
            public.ExecShell(self.get_last_env(nodejs_version) + "cd {} && {} install 2>&1 >> {}".format(project_find['path'],yarn_bin,self._npm_exec_log))
        else:
            public.ExecShell(self.get_last_env(nodejs_version) + "cd {} && {} install 2>&1 >> {}".format(project_find['path'],npm_bin,self._npm_exec_log))
        public.writeFile(self._npm_exec_log,"|-Successify --- 命令已执行! ---",'a+')
        public.WriteLog(self._log_name, 'Node项目：{}, 安装依赖包完成!'.format(project_find['name']))
        if rebuild: # 重新构建已安装模块？
            self.rebuild_project(get.project_name)
        return public.return_data(True,'安装依赖包成功!')


    
    def update_packages(self,get):
        '''
            @name 更新指定项目的依赖包
            @author hwliang<2021-08-10>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            return dict
        '''
        project_find = self.get_project_find(get.project_name)
        if not project_find: return public.return_error('指定项目不存在!')
        if not os.path.exists(project_find['path']): return public.return_error('项目目录不存在!')
        package_file = '{}/package.json'.format(project_find['path'])
        if not os.path.exists(package_file): return public.return_error('没有在项目目录中找到package.json配置文件!')
        package_lock_file = '{}/package-lock.json'.format(project_find['path'])
        if not os.path.exists(package_lock_file): return public.return_error('请先安装依赖包!')
        nodejs_version = project_find['project_config']['nodejs_version']
        npm_bin = self.get_npm_bin(nodejs_version)
        if not npm_bin: 
            return public.return_error('指定nodejs版本不存在!')
        
        public.ExecShell(self.get_last_env(nodejs_version) + "cd {} && {} update &> {}".format(project_find['path'],npm_bin,self._npm_exec_log))
        public.WriteLog(self._log_name, '项目[{}]更新所有依赖包'.format(get.project_name))
        return public.return_data(True,'依赖包更新成功!')


    def reinstall_packages(self,get):
        '''
            @name 重新安装指定项目的依赖包
            @author hwliang<2021-08-10>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            return dict
        '''

        project_find = self.get_project_find(get.project_name)
        if not project_find: return public.return_error('指定项目不存在!')
        if not os.path.exists(project_find['path']): return public.return_error('项目目录不存在!')
        package_file = '{}/package.json'.format(project_find['path'])
        if not os.path.exists(package_file): return public.return_error('没有在项目目录中找到package.json配置文件!')

        package_lock_file = '{}/package-lock.json'.format(project_find['path'])
        if os.path.exists(package_lock_file): os.remove(package_lock_file)
        package_path = '{}/node_modules'
        if os.path.exists(package_path): shutil.rmtree(package_path)


        nodejs_version = project_find['project_config']['nodejs_version']
        npm_bin = self.get_npm_bin(nodejs_version)
        if not npm_bin: 
            return public.return_error('指定nodejs版本不存在!')
        public.WriteLog(self._log_name,'Node项目:{}，已重装所有依赖包')
        public.ExecShell(self.get_last_env(nodejs_version) + "cd {} && {} install &> {}".format(project_find['path'],npm_bin,self._npm_exec_log))
        return public.return_data(True,'依赖包重装成功!')

    def get_project_modules(self,get):
        '''
            @name 获取指定项目的依赖包列表
            @author hwliang<2021-08-10>
            @param get<dict_obj>{
                project_name: string<项目名称>
                project_cwd: string<项目目录> 可选
            }
            return list
        '''
        if not 'project_cwd' in get:
            project_find = self.get_project_find(get.project_name)
            if not project_find: return public.return_error('指定项目不存在!')
            project_cwd = project_find['path']
        else:
            project_cwd = get.project_cwd
        mod_path = os.path.join(project_cwd,'node_modules')
        modules = []
        if not os.path.exists(mod_path): return modules
        for mod_name in os.listdir(mod_path):
            try:
                mod_pack_file = os.path.join(mod_path,mod_name,'package.json')
                if not os.path.exists(mod_pack_file): continue
                mod_pack_info = json.loads(public.readFile(mod_pack_file))
                pack_info = {
                    "name": mod_name, 
                    "version": mod_pack_info['version'],
                    "description":mod_pack_info['description'],
                    "license": mod_pack_info['license'] if 'license' in mod_pack_info else 'NULL',
                    "homepage": mod_pack_info['homepage']
                    }
                modules.append(pack_info)
            except:
                continue
        return modules

    def install_module(self,get):
        '''
            @name 安装指定模块
            @author hwliang<2021-08-10>
            @param get<dict_obj>{
                project_name: string<项目名称>
                mod_name: string<模块名称>
            }
            @return dict
        '''

        project_find = self.get_project_find(get.project_name)
        if not project_find: return public.return_error('指定项目不存在!')
        project_cwd = project_find['path']


        mod_name = get.mod_name
        filename = '{}/node_modules/{}/package.json'.format(project_cwd,mod_name)
        if os.path.exists(filename): return public.return_error('指定模块已经安装过了!')

        nodejs_version = project_find['project_config']['nodejs_version']
        npm_bin = self.get_npm_bin(nodejs_version)
        yarn_bin = self.get_yarn_bin(nodejs_version)

        if not npm_bin and not yarn_bin:
            return public.return_error('指定nodejs版本不存在!')
        if yarn_bin:
            public.ExecShell(self.get_last_env(nodejs_version) + "cd {} && {} add {} &> {}".format(project_find['path'],yarn_bin,mod_name,self._npm_exec_log))
        else:
            public.ExecShell(self.get_last_env(nodejs_version) + "cd {} && {} install {} &> {}".format(project_find['path'],npm_bin,mod_name,self._npm_exec_log))
        if not os.path.exists(filename): return public.return_error('指定模块安装失败!')
        public.WriteLog(self._log_name,'Node项目{} , {}模块安装完成!'.format(get.project_name,mod_name))
        return public.return_data(True,'安装成功!')

    def uninstall_module(self,get):
        '''
            @name 卸载指定模块
            @author hwliang<2021-04-08>
            @param get<dict_obj>{
                project_name: string<项目名称>
                mod_name: string<模块名称>
            }
            @return dict
        '''
        project_find = self.get_project_find(get.project_name)
        if not project_find: return public.return_error('指定项目不存在!')
        project_cwd = project_find['path']

        mod_name = get.mod_name
        filename = '{}/node_modules/{}/package.json'.format(project_cwd,mod_name)
        if not os.path.exists(filename): return public.return_error('指定模块未安装!')

        nodejs_version = project_find['project_config']['nodejs_version']
        npm_bin = self.get_npm_bin(nodejs_version)
        yarn_bin = self.get_yarn_bin(nodejs_version)
        if not npm_bin and not yarn_bin: 
            return public.return_error('指定nodejs版本不存在!')
        if yarn_bin:
            result = public.ExecShell(self.get_last_env(nodejs_version) + "cd {} && {} remove {}".format(project_find['path'],yarn_bin,mod_name))
        else:
            result = public.ExecShell(self.get_last_env(nodejs_version) + "cd {} && {} uninstall {}".format(project_find['path'],npm_bin,mod_name))
        if os.path.exists(filename): 
            result = "\n".join(result)
            if result.find('looking for funding') != -1:
                return public.return_error("此模块被其它已安装模块依赖，无法卸载!")
            return public.return_error("无法卸载此模块!")

        public.WriteLog(self._log_name,'Node项目{} , {}模块卸载完成!'.format(get.project_name,mod_name))
        return public.return_data(True,'模块卸载成功!')


    def upgrade_module(self,get):
        '''
            @name 更新指定模块
            @author hwliang<2021-08-10>
            @param get<dict_obj>{
                project_name: string<项目名称>
                mod_name: string<模块名称>
            }
            @return dict
        '''
        project_find = self.get_project_find(get.project_name)
        if not project_find: return public.return_error('指定项目不存在!')
        project_cwd = project_find['path']

        mod_name = get.mod_name
        filename = '{}/node_modules/{}/package.json'.format(project_cwd,mod_name)
        if not os.path.exists(filename): return public.return_error('指定模块未安装!')

        nodejs_version = project_find['project_config']['nodejs_version']
        npm_bin = self.get_npm_bin(nodejs_version)

        if not npm_bin: 
            return public.return_error('指定nodejs版本不存在!')
        public.ExecShell(self.get_last_env(nodejs_version) + "cd {} && {} update {} &> {}".format(project_find['path'],npm_bin,mod_name,self._npm_exec_log))
        public.WriteLog(self._log_name,'Node项目{} , {}模块更新完成!'.format(get.project_name,mod_name))
        return public.return_data(True,'模块更新成功!')
        

    def create_project(self,get):
        '''
            @name 创建新的项目
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
                project_cwd: string<项目目录>
                project_script: string<项目脚本>
                project_ps: string<项目备注信息>
                bind_extranet: int<是否绑定外网> 1:是 0:否
                domains: list<域名列表> ["domain1:80","domain2:80"]  // 在bind_extranet=1时，需要填写
                is_power_on: int<是否开机启动> 1:是 0:否
                run_user: string<运行用户>
                max_memory_limit: int<最大内存限制> // 超出此值项目将被强制重启
                nodejs_version: string<nodejs版本>
            }
            @return dict
        '''
        if not isinstance(get,public.dict_obj): return public.return_error('参数类型错误，需要dict_obj对像')
        if not self.is_install_nodejs(get):
            return public.return_error('请先安装nodejs版本管理器，并安装至少1个node.js版本')

        project_name = get.project_name.strip()
        if not re.match("^\w+$",project_name): 
            return public.return_error('项目名称格式不正确，支持字母、数字、下划线，表达式: ^[0-9A-Za-z_]$')

        if public.M('sites').where('name=?',(get.project_name,)).count():
            return public.return_error('指定项目名称已存在: {}'.format(get.project_name))
        get.project_cwd = get.project_cwd.strip()
        if not os.path.exists(get.project_cwd):
            return public.return_error('项目目录不存在: {}'.format(get.project_cwd))
        
        # 端口占用检测
        if self.check_port_is_used(get.get('port/port')): 
            return public.return_error('指定端口已被其它应用占用，请修改您的项目配置使用其它端口, 端口: {}'.format(get.port))
        
        domains = []
        if get.bind_extranet == 1:
            domains = get.domains
            if not public.is_apache_nginx(): return public.return_error('需要安装Nginx或Apache才能使用外网映射功能')
        for domain in domains:
            domain_arr = domain.split(':')
            if public.M('domain').where('name=?',domain_arr[0]).count():
                return public.return_error('指定域名已存在: {}'.format(domain))
        pdata = {
            'name': get.project_name,
            'path': get.project_cwd,
            'ps': get.project_ps,
            'status':1,
            'type_id':0,
            'project_type': 'Node',
            'project_config': json.dumps(
                {
                    'project_name': get.project_name,
                    'project_cwd': get.project_cwd,
                    'project_script': get.project_script,
                    'bind_extranet': get.bind_extranet,
                    'domains': [],
                    'is_power_on': get.is_power_on,
                    'run_user': get.run_user,
                    'max_memory_limit': get.max_memory_limit,
                    'nodejs_version': get.nodejs_version,
                    'port': int(get.port)
                }
            ),
            'addtime': public.getDate()
        }

        project_id = public.M('sites').insert(pdata)
        if get.bind_extranet == 1:
            format_domains = []
            for domain in domains:
                if domain.find(':') == -1: domain += ':80'
                format_domains.append(domain)
            get.domains = format_domains
            self.project_add_domain(get)
        self.set_config(get.project_name)
        public.WriteLog(self._log_name,'添加Node.js项目{}'.format(get.project_name))
        self.install_packages(get)
        self.start_project(get)
        return public.return_data(True,'添加项目成功',project_id)
        
    def modify_project(self,get):
        '''
            @name 修改指定项目
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
                project_cwd: string<项目目录>
                project_script: string<项目脚本>
                project_ps: string<项目备注信息>
                is_power_on: int<是否开机启动> 1:是 0:否
                run_user: string<运行用户>
                max_memory_limit: int<最大内存限制> // 超出此值项目将被强制重启
                nodejs_version: string<nodejs版本>
            }
            @return dict
        '''
        if not isinstance(get,public.dict_obj): return public.return_error('参数类型错误，需要dict_obj对像')
        if not self.is_install_nodejs(get):
            return public.return_error('请先安装nodejs版本管理器，并安装至少1个node.js版本')
        project_find = self.get_project_find(get.project_name)
        if not project_find:
            return public.return_error('指定项目不存在: {}'.format(get.project_name))

        if not os.path.exists(get.project_cwd):
            return public.return_error('项目目录不存在: {}'.format(get.project_cwd))
        rebuild = False
        if hasattr(get,'port'): 
            if int(project_find['project_config']['port']) != int(get.port):
                if self.check_port_is_used(get.get('port/port'),True): 
                    return public.return_error('指定端口已被其它应用占用，请修改您的项目配置使用其它端口, 端口: {}'.format(get.port))
                project_find['project_config']['port'] = int(get.port)
        if hasattr(get,'project_cwd'): project_find['project_config']['project_cwd'] = get.project_cwd
        if hasattr(get,'project_script'): 
            if not get.project_script.strip():
                return public.return_error('启动命令不能为空')
            project_find['project_config']['project_script'] = get.project_script.strip()
        if hasattr(get,'is_power_on'): project_find['project_config']['is_power_on'] = get.is_power_on
        if hasattr(get,'run_user'): project_find['project_config']['run_user'] = get.run_user
        if hasattr(get,'max_memory_limit'): project_find['project_config']['max_memory_limit'] = get.max_memory_limit
        if hasattr(get,'nodejs_version'): 
            if project_find['project_config']['nodejs_version'] != get.nodejs_version:
                rebuild = True
                project_find['project_config']['nodejs_version'] = get.nodejs_version
        pdata = {
            'path': get.project_cwd,
            'ps': get.project_ps,
            'project_config': json.dumps(project_find['project_config'])
        }

        public.M('sites').where('name=?',(get.project_name,)).update(pdata)
        self.set_config(get.project_name)
        public.WriteLog(self._log_name,'修改Node.js项目{}'.format(get.project_name))
        if rebuild:
            self.rebuild_project(get.project_name)
        return public.return_data(True,'修改项目成功')

    def rebuild_project(self,project_name):
        '''
            @name 重新构建指定项目
            @author hwliang<2021-08-26>
            @param project_name: string<项目名称>
            @return bool
        '''
        project_find = self.get_project_find(project_name)
        if not project_find: return False
        nodejs_version = project_find['project_config']['nodejs_version']
        npm_bin = self.get_npm_bin(nodejs_version)

        public.ExecShell(self.get_last_env(nodejs_version) + "cd {} && {} rebuild 2>&1 >> {}".format(project_find['path'],npm_bin,self._npm_exec_log))
        return True


    def remove_project(self,get):
        '''
            @name 删除指定项目
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        project_find = self.get_project_find(get.project_name)
        if not project_find:
            return public.return_error('指定项目不存在: {}'.format(get.project_name))
        
        self.stop_project(get)
        self.clear_config(get.project_name)
        public.M('domain').where('pid=?',(project_find['id'],)).delete()
        public.M('sites').where('name=?',(get.project_name,)).delete()

        pid_file = "{}/{}.pid".format(self._node_pid_path,get.project_name)
        if os.path.exists(pid_file): os.remove(pid_file)
        script_file = '{}/{}.sh'.format(self._node_run_scripts,get.project_name)
        if os.path.exists(script_file): os.remove(script_file)
        log_file = '{}/{}.log'.format(self._node_logs_path,get.project_name)
        if os.path.exists(log_file): os.remove(log_file)
        public.WriteLog(self._log_name,'删除Node.js项目{}'.format(get.project_name))
        return public.return_data(True,'删除项目成功')


    def project_get_domain(self,get):
        '''
            @name 获取指定项目的域名列表
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        project_id = public.M('sites').where('name=?',(get.project_name,)).getField('id')
        domains = public.M('domain').where('pid=?',(project_id,)).order('id desc').select()
        project_find = self.get_project_find(get.project_name)
        if len(domains) != len(project_find['project_config']['domains']):
            public.M('domain').where('pid=?',(project_id,)).delete()
            if not project_find: return []
            for d in project_find['project_config']['domains']:
                domain = {}
                arr = d.split(':')
                if len(arr) < 2: arr.append(80)
                domain['name'] = arr[0]
                domain['port'] = int(arr[1])
                domain['pid'] = project_id
                domain['addtime'] = public.getDate()
                public.M('domain').insert(domain)
            if project_find['project_config']['domains']:
                domains = public.M('domain').where('pid=?',(project_id,)).select()
        return domains


    def project_add_domain(self,get):
        '''
            @name 为指定项目添加域名
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
                domains: list<域名列表>
            }
            @return dict
        '''
        project_find = self.get_project_find(get.project_name)
        if not project_find: 
            return public.return_error('指定项目不存在')
        project_id = project_find['id']
        
        domains = get.domains
        success_list = []
        error_list = []
        for domain in domains:
            domain = domain.strip()
            domain_arr = domain.split(':')
            if len(domain_arr) == 1: 
                domain_arr.append(80)
                domain += ':80'
            if not public.M('domain').where('name=?',(domain_arr[0],)).count():
                public.M('domain').add('name,pid,port,addtime',(domain_arr[0],project_id,domain_arr[1],public.getDate()))
                if not domain in project_find['project_config']['domains']:
                    project_find['project_config']['domains'].append(domain)
                public.WriteLog(self._log_name,'成功添加域名{}到项目{}'.format(domain,get.project_name))
                success_list.append(domain)
            else:
                public.WriteLog(self._log_name,'添加域名错误，域名{}已存在'.format(domain))
                error_list.append(domain)

        if success_list:
            public.M('sites').where('id=?',(project_id,)).save('project_config',json.dumps(project_find['project_config']))
            self.set_config(get.project_name)

        return public.return_data(True,"成功添加{}个域名，失败{}个!".format(len(success_list),len(error_list)),error_msg=error_list)


    def project_remove_domain(self,get):
        '''
            @name 为指定项目删除域名
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
                domain: string<域名>
            }
            @return dict
        '''
        project_find = self.get_project_find(get.project_name)
        if not project_find: 
            return public.return_error('指定项目不存在')
        last_domain = get.domain
        domain_arr = get.domain.split(':')
        if len(domain_arr) == 1: 
            domain_arr.append(80)
            
        project_id = public.M('sites').where('name=?',(get.project_name,)).getField('id')
        if project_find['project_config']['bind_extranet']:
            if len(project_find['project_config']['domains']) == 1: return public.return_error('已映射外网的项目至少需要一个域名')
        domain_id = public.M('domain').where('name=? AND pid=?',(domain_arr[0],project_id)).getField('id')
        if not domain_id: 
            return public.return_error('指定域名不存在')
        public.M('domain').where('id=?',(domain_id,)).delete()

        if get.domain in project_find['project_config']['domains']:
            project_find['project_config']['domains'].remove(get.domain)
        if get.domain+":80" in project_find['project_config']['domains']:
            project_find['project_config']['domains'].remove(get.domain + ":80")

        public.M('sites').where('id=?',(project_id,)).save('project_config',json.dumps(project_find['project_config']))
        public.WriteLog(self._log_name,'从项目：{}，删除域名{}'.format(get.project_name,get.domain))
        self.set_config(get.project_name)
        return public.return_data(True,'删除域名成功')


    def bind_extranet(self,get):
        '''
            @name 绑定外网
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        if not public.is_apache_nginx(): return public.return_error('需要安装Nginx或Apache才能使用外网映射功能')
        project_name = get.project_name.strip()
        project_find = self.get_project_find(project_name)
        if not project_find: return public.return_error('项目不存在')
        if not project_find['project_config']['domains']: return public.return_error('请先到【域名管理】选项中至少添加一个域名')
        project_find['project_config']['bind_extranet'] = 1
        public.M('sites').where("id=?",(project_find['id'],)).setField('project_config',json.dumps(project_find['project_config']))
        self.set_config(project_name)
        public.WriteLog(self._log_name,'Node项目{}, 开启外网映射'.format(project_name))
        return public.return_data(True,'开启外网映射成功')

    
    def set_config(self,project_name):
        '''
            @name 设置项目配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return bool
        '''
        project_find = self.get_project_find(project_name)
        if not project_find: return False
        if not project_find['project_config']: return False
        if not project_find['project_config']['bind_extranet']: return False
        if not project_find['project_config']['domains']: return False
        self.set_nginx_config(project_find)
        self.set_apache_config(project_find)
        public.serviceReload()
        return True

    def clear_config(self,project_name):
        '''
            @name 清除项目配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return bool
        '''
        project_find = self.get_project_find(project_name)
        if not project_find: return False
        self.clear_nginx_config(project_find)
        self.clear_apache_config(project_find)
        public.serviceReload()
        return True

    def clear_apache_config(self,project_find):
        '''
            @name 清除apache配置
            @author hwliang<2021-08-09>
            @param project_find: dict<项目信息>
            @return bool
        '''
        project_name = project_find['name']
        config_file = "{}/apache/node_{}.conf".format(self._vhost_path,project_name)
        if os.path.exists(config_file):
            os.remove(config_file)
        return True


    def clear_nginx_config(self,project_find):
        '''
            @name 清除nginx配置
            @author hwliang<2021-08-09>
            @param project_find: dict<项目信息>
            @return bool
        '''
        project_name = project_find['name']
        config_file = "{}/nginx/node_{}.conf".format(self._vhost_path,project_name)
        if os.path.exists(config_file):
            os.remove(config_file)
        rewrite_file = "{panel_path}/vhost/rewrite/node_{project_name}.conf".format(panel_path = self._panel_path,project_name = project_name)
        if os.path.exists(rewrite_file):
            os.remove(rewrite_file)
        return True


    def set_nginx_config(self,project_find):
        '''
            @name 设置Nginx配置
            @author hwliang<2021-08-09>
            @param project_find: dict<项目信息>
            @return bool
        '''
        project_name = project_find['name']
        ports = []
        domains = []
        
        for d in project_find['project_config']['domains']:
            domain_tmp = d.split(':')
            if len(domain_tmp) == 1: domain_tmp.append(80)
            if not int(domain_tmp[1]) in ports: 
                ports.append(int(domain_tmp[1]))
            if not domain_tmp[0] in domains:
                domains.append(domain_tmp[0])
        listen_ipv6 = public.listen_ipv6()
        listen_ports = ''
        for p in ports:
            listen_ports += "    listen {};\n".format(p)
            if listen_ipv6:
                listen_ports += "    listen [::]:{};\n".format(p)
        listen_ports = listen_ports.strip()

        is_ssl,is_force_ssl = self.exists_nginx_ssl(project_name)
        ssl_config = ''
        if is_ssl:
            listen_ports += "\n    listen 443 ssl http2;"
            if listen_ipv6: listen_ports += "\n    listen [::]:443 ssl http2;"
        
            ssl_config = '''ssl_certificate    {vhost_path}/cert/{priject_name}/fullchain.pem;
    ssl_certificate_key    {vhost_path}/cert/{priject_name}/privkey.pem;
    ssl_protocols TLSv1.1 TLSv1.2 TLSv1.3;
    ssl_ciphers EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    add_header Strict-Transport-Security "max-age=31536000";
    error_page 497  https://$host$request_uri;'''.format(vhost_path = self._vhost_path,priject_name = project_name)

            if is_force_ssl:
                ssl_config += '''
    #HTTP_TO_HTTPS_START
    if ($server_port !~ 443){
        rewrite ^(/.*)$ https://$host$1 permanent;
    }
    #HTTP_TO_HTTPS_END'''
        
        config_file = "{}/nginx/node_{}.conf".format(self._vhost_path,project_name)
        template_file = "{}/template/nginx/node_http.conf".format(self._vhost_path)
        
        config_body = public.readFile(template_file)
        config_body = config_body.format(
            site_path = project_find['path'],
            domains = ' '.join(domains),
            project_name = project_name,
            panel_path = self._panel_path,
            log_path = public.get_logs_path(),
            url = 'http://127.0.0.1:{}'.format(project_find['project_config']['port']),
            host = '$host',
            listen_ports = listen_ports,
            ssl_config = ssl_config
        )

        # # 恢复旧的SSL配置
        # ssl_config = self.get_nginx_ssl_config(project_name)
        # if ssl_config:
        #     config_body.replace('#error_page 404/404.html;',ssl_config)
            

        rewrite_file = "{panel_path}/vhost/rewrite/node_{project_name}.conf".format(panel_path = self._panel_path,project_name = project_name)
        if not os.path.exists(rewrite_file): public.writeFile(rewrite_file,'# 请将伪静态规则或自定义NGINX配置填写到此处\n')
        public.writeFile(config_file,config_body)
        return True

    def get_nginx_ssl_config(self,project_name):
        '''
            @name 获取项目Nginx SSL配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return string
        '''
        result = ''
        config_file = "{}/nginx/node_{}".format(self._vhost_path,project_name)
        if not os.path.exists(config_file): 
            return result

        config_body = public.readFile(config_file)
        if not config_body: 
            return result
        if config_body.find('ssl_certificate') == -1:
            return result

        ssl_body = re.search("#SSL-START(.|\n)+#SSL-END",config_body)
        if not ssl_body: return result
        result = ssl_body.group()
        return result

    def exists_nginx_ssl(self,project_name):
        '''
            @name 判断项目是否配置Nginx SSL配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return tuple
        '''
        config_file = "{}/nginx/node_{}.conf".format(public.get_vhost_path(),project_name)
        if not os.path.exists(config_file): 
            return False,False

        config_body = public.readFile(config_file)
        if not config_body: 
            return False,False

        is_ssl,is_force_ssl = False,False
        if config_body.find('ssl_certificate') != -1:
            is_ssl = True
        if config_body.find('HTTP_TO_HTTPS_START') != -1:
            is_force_ssl = True
        return is_ssl,is_force_ssl

    def exists_apache_ssl(self,project_name):
        '''
            @name 判断项目是否配置Apache SSL配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return bool
        '''
        config_file = "{}/apache/node_{}.conf".format(public.get_vhost_path(),project_name)
        if not os.path.exists(config_file): 
            return False,False

        config_body = public.readFile(config_file)
        if not config_body: 
            return False,False

        is_ssl,is_force_ssl = False,False
        if config_body.find('SSLCertificateFile') != -1:
            is_ssl = True
        if config_body.find('HTTP_TO_HTTPS_START') != -1:
            is_force_ssl = True
        return is_ssl,is_force_ssl

    def set_apache_config(self,project_find):
        '''
            @name 设置Apache配置
            @author hwliang<2021-08-09>
            @param project_find: dict<项目信息>
            @return bool
        '''
        project_name = project_find['name']

        # 处理域名和端口
        ports = []
        domains = []
        for d in project_find['project_config']['domains']:
            domain_tmp = d.split(':')
            if len(domain_tmp) == 1: domain_tmp.append(80)
            if not int(domain_tmp[1]) in ports: 
                ports.append(int(domain_tmp[1]))
            if not domain_tmp[0] in domains:
                domains.append(domain_tmp[0])

        
        config_file = "{}/apache/node_{}.conf".format(self._vhost_path,project_name)
        template_file = "{}/template/apache/node_http.conf".format(self._vhost_path)
        config_body = public.readFile(template_file)
        apache_config_body = ''

        # 旧的配置文件是否配置SSL
        is_ssl,is_force_ssl  = self.exists_apache_ssl(project_name)
        if is_ssl:
            if not 443 in ports: ports.append(443)
        
        from panelSite import panelSite
        s = panelSite()

        # 根据端口列表生成配置
        for p in ports:
            # 生成SSL配置
            ssl_config = ''
            if p == 443 and is_ssl:
                ssl_key_file = "{vhost_path}/cert/{project_name}/privkey.pem".format(project_name = project_name,vhost_path = public.get_vhost_path())
                if not os.path.exists(ssl_key_file): continue # 不存在证书文件则跳过
                ssl_config = '''#SSL
    SSLEngine On
    SSLCertificateFile {vhost_path}/cert/{project_name}/fullchain.pem
    SSLCertificateKeyFile {vhost_path}/cert/{project_name}/privkey.pem
    SSLCipherSuite EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5
    SSLProtocol All -SSLv2 -SSLv3 -TLSv1
    SSLHonorCipherOrder On'''.format(project_name = project_name,vhost_path = public.get_vhost_path())
            else:
                if is_force_ssl:
                    ssl_config = '''#HTTP_TO_HTTPS_START
    <IfModule mod_rewrite.c>
        RewriteEngine on
        RewriteCond %{SERVER_PORT} !^443$
        RewriteRule (.*) https://%{SERVER_NAME}$1 [L,R=301]
    </IfModule>
    #HTTP_TO_HTTPS_END'''

            # 生成vhost主体配置
            apache_config_body += config_body.format(
                site_path = project_find['path'],
                server_name = '{}.{}'.format(p,project_name),
                domains = ' '.join(domains),
                log_path = public.get_logs_path(),
                server_admin = 'admin@{}'.format(project_name),
                url = 'http://127.0.0.1:{}'.format(project_find['project_config']['port']),
                port = p,
                ssl_config = ssl_config,
                project_name = project_name
            )
            apache_config_body += "\n"

            # 添加端口到主配置文件
            if not p in [80]:
                s.apacheAddPort(p)
        
        # 写.htaccess
        rewrite_file = "{}/.htaccess".format(project_find['path'])
        if not os.path.exists(rewrite_file): public.writeFile(rewrite_file,'# 请将伪静态规则或自定义Apache配置填写到此处\n')

        # 写配置文件
        public.writeFile(config_file,apache_config_body)
        return True
    

    def unbind_extranet(self,get):
        '''
            @name 解绑外网
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        project_name = get.project_name.strip()
        self.clear_config(project_name)
        public.serviceReload()
        project_find = self.get_project_find(project_name)
        project_find['project_config']['bind_extranet'] = 0
        public.M('sites').where("id=?",(project_find['id'],)).setField('project_config',json.dumps(project_find['project_config']))
        public.WriteLog(self._log_name,'Node项目{}, 关闭外网映射'.format(project_name))
        return public.return_data(True,'关闭成功')


    def get_project_pids(self,get = None,pid = None):
        '''
            @name 获取项目进程pid列表
            @author hwliang<2021-08-10>
            @param pid: string<项目pid>
            @return list
        '''
        if get: pid = int(get.pid)
        if not self._pids: self._pids = psutil.pids()
        project_pids = []
        
        for i in self._pids:
            try:
                p = psutil.Process(i)
            except: continue
            if p.ppid() == pid:
                if i in project_pids: continue
                if p.name() in ['bash']: continue
                project_pids.append(i)

        other_pids = []
        for i in project_pids:
            other_pids += self.get_project_pids(pid=i)
        if os.path.exists('/proc/{}'.format(pid)):
            project_pids.append(pid)

        all_pids = list(set(project_pids + other_pids))
        if not all_pids:
            all_pids = self.get_other_pids(pid)
        return sorted(all_pids)

    def get_other_pids(self,pid):
        '''
            @name 获取其他进程pid列表
            @author hwliang<2021-08-10>
            @param pid: string<项目pid>
            @return list
        '''
        plugin_name = None
        for pid_name in os.listdir(self._node_pid_path):
            pid_file = '{}/{}'.format(self._node_pid_path,pid_name)
            #s_pid = int(public.readFile(pid_file))
            data = public.readFile(pid_file)
            if isinstance(data,str) and data:
                s_pid = int(data)
            else:
                return []
            if pid == s_pid:
                plugin_name = pid_name[:-4]
                break
        project_find = self.get_project_find(plugin_name)
        if not project_find: return []
        if not self._pids: self._pids = psutil.pids()
        all_pids = []
        for i in self._pids:
            try:
                p = psutil.Process(i)
                if p.cwd() == project_find['path'] and p.username() == project_find['project_config']['run_user']:
                    if p.name() in ['node','npm','pm2']:
                        all_pids.append(i)
            except: continue
        return all_pids

    def kill_pids(self,get=None,pids = None):
        '''
            @name 结束进程列表
            @author hwliang<2021-08-10>
            @param pids: string<进程pid列表>
            @return dict
        '''
        if get: pids = get.pids
        if not pids: return public.return_data(True, '没有进程')
        pids = sorted(pids,reverse=True)
        for i in pids:
            try:
                p = psutil.Process(i)
                p.kill()
            except:
                pass
        return public.return_data(True, '进程已全部结束')



    
    def start_project(self,get):
        '''
            @name 启动项目
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        pid_file = "{}/{}.pid".format(self._node_pid_path,get.project_name)
        if os.path.exists(pid_file):
            self.stop_project(get)

        project_find = self.get_project_find(get.project_name)
        if not project_find: return public.return_error('项目不存在')

        if not os.path.exists(project_find['path']):
            error_msg = '启动失败，Nodejs项目{}，运行目录{}不存在!'.format(get.project_name,project_find['path'])
            public.WriteLog(self._log_name,error_msg)
            return public.return_error(error_msg)

        # 是否安装依赖模块？
        package_file = "{}/package.json".format(project_find['path'])
        package_info = {}
        if os.path.exists(package_file):
            node_modules_path = "{}/node_modules".format(project_find['path'])
            if not os.path.exists(node_modules_path):
                return public.return_error('请先到模块管理中点击【一键安装项目模块】来安装模块依赖!')
            package_info = json.loads(public.readFile(package_file))
        if not package_info: package_info['scripts'] = {}
        if 'scripts' not in package_info: package_info['scripts'] = {}
        try:
            scripts_keys = package_info['scripts'].keys()
        except:
            scripts_keys = []
                
        
        # 前置准备
        nodejs_version = project_find['project_config']['nodejs_version']
        node_bin = self.get_node_bin(nodejs_version)
        npm_bin = self.get_npm_bin(nodejs_version)
        project_script = project_find['project_config']['project_script'].strip()
        log_file = "{}/{}.log".format(self._node_logs_path,get.project_name)
        if not project_script: return public.return_error('未配置启动脚本')

        last_env = self.get_last_env(nodejs_version,project_find['path'])
        
        # 生成启动脚本
        if os.path.exists(project_script):
            start_cmd = '''{last_env}
cd {project_cwd}
nohup {node_bin} {project_script} 2>&1 >> {log_file} & 
echo $! > {pid_file}
'''.format(
    project_cwd = project_find['path'],
    node_bin = node_bin,
    project_script = project_script,
    log_file = log_file,
    pid_file = pid_file,
    last_env = last_env
)
        elif project_script in scripts_keys:
            start_cmd = '''{last_env}
cd {project_cwd}
nohup {npm_bin} run {project_script} 2>&1 >> {log_file} &
echo $! > {pid_file}
'''.format(
    project_cwd = project_find['path'],
    npm_bin = npm_bin,
    project_script = project_script,
    pid_file = pid_file,
    log_file = log_file,
    last_env = last_env
)
        else:
            start_cmd = '''{last_env}
cd {project_cwd}
nohup {project_script} 2>&1 >> {log_file} &
echo $! > {pid_file}
'''.format(
    project_cwd = project_find['path'],
    project_script = project_script,
    pid_file = pid_file,
    log_file = log_file,
    last_env = last_env
)
        script_file = "{}/{}.sh".format(self._node_run_scripts,get.project_name)

        # 写入启动脚本
        public.writeFile(script_file,start_cmd)
        if os.path.exists(pid_file): os.remove(pid_file)

        # 处理前置权限
        public.ExecShell("chown -R {user}:{user} {project_cwd}".format(user=project_find['project_config']['run_user'],project_cwd=project_find['path']))
        public.ExecShell("chown -R www:www {}/vhost".format(self._nodejs_path))
        public.ExecShell("chmod 755 {} {} {}".format(self._nodejs_path,public.get_setup_path(),'/www'))
        public.set_own(script_file,project_find['project_config']['run_user'],project_find['project_config']['run_user'])
        public.set_mode(script_file,755)

        # 执行脚本文件
        p = public.ExecShell("bash {}".format(script_file),user=project_find['project_config']['run_user'])
        time.sleep(1)
        if not os.path.exists(pid_file):
            p = '\n'.join(p)
            if p.find('[Errno 0]') != -1:
                if os.path.exists('{}/bt_security'.format(public.get_plugin_path())):
                    return public.return_error('启动命令被【堡塔防提权】拦截，请关闭{}用户的防护'.format(project_find['project_config']['run_user']))
                return public.return_error('启动命令被未知安全软件拦截，请检查安装软件日志')
            return public.return_error('启动失败<pre>{}</pre>'.format(p))

        # 获取PID
        try:
            pid = int(public.readFile(pid_file))
        except:
            return public.return_error('启动失败<br>{}'.format(public.GetNumLines(log_file,20)))
        pids = self.get_project_pids(pid=pid)
        if not pids: 
            if os.path.exists(pid_file): os.remove(pid_file)
            return public.return_error('启动失败<br>{}'.format(public.GetNumLines(log_file,20)))

        return public.return_data(True, '启动成功', pids)
        

    def stop_project(self,get):
        '''
            @name 停止项目
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        pid_file = "{}/{}.pid".format(self._node_pid_path,get.project_name)
        if not os.path.exists(pid_file): return public.return_error('项目未启动')
        data = public.readFile(pid_file)
        if isinstance(data,str) and data:
            pid = int(data)
            pids = self.get_project_pids(pid=pid)
        else:
            return  public.return_error('项目未启动')
        if not pids: return public.return_error('项目未启动')
        self.kill_pids(pids=pids)
        if os.path.exists(pid_file): os.remove(pid_file)
        return public.return_data(True, '停止成功')

    def restart_project(self,get):
        '''
            @name 重启项目
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        res = self.stop_project(get)
        if not res['status']: return res
        res = self.start_project(get)
        if not res['status']: return res
        return public.return_data(True, '重启成功')

    def get_project_log(self,get):
        '''
            @name 获取项目日志
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        log_file = "{}/{}.log".format(self._node_logs_path,get.project_name)
        if not os.path.exists(log_file): return public.return_error('日志文件不存在')
        return public.GetNumLines(log_file,200)
    

    def get_project_load_info(self,get = None,project_name = None):
        '''
            @name 获取项目负载信息
            @author hwliang<2021-08-12>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        if get: project_name = get.project_name.strip()
        load_info = {}
        pid_file = "{}/{}.pid".format(self._node_pid_path,project_name)
        if not os.path.exists(pid_file): return load_info
        data = public.readFile(pid_file)
        if isinstance(data,str) and data:
            pid = int(data)
            pids = self.get_project_pids(pid=pid)
        else:
            return load_info
        if not pids: return load_info
        for i in pids:
            process_info = self.get_process_info_by_pid(i)
            if process_info: load_info[i] = process_info
        return load_info


    def object_to_dict(self,obj):
        '''
            @name 将对象转换为字典
            @author hwliang<2021-08-09>
            @param obj<object>
            @return dict
        '''
        result = {}
        for name in dir(obj):
            value = getattr(obj, name)
            if not name.startswith('__') and not callable(value) and not name.startswith('_'): result[name] = value
        return result
    
    
    def list_to_dict(self,data):
        '''
            @name 将列表转换为字典
            @author hwliang<2021-08-09>
            @param data<list>
            @return dict
        '''
        result = []
        for s in data:
            result.append(self.object_to_dict(s))
        return result


    def get_connects(self,pid):
        '''
            @name 获取进程连接信息
            @author hwliang<2021-08-09>
            @param pid<int>
            @return dict
        '''
        connects = 0
        try:
            if pid == 1: return connects
            tp = '/proc/' + str(pid) + '/fd/'
            if not os.path.exists(tp): return connects
            for d in os.listdir(tp):
                fname = tp + d
                if os.path.islink(fname):
                    l = os.readlink(fname)
                    if l.find('socket:') != -1: connects += 1
        except:pass
        return connects


    def format_connections(self,connects):
        '''
            @name 获取进程网络连接信息
            @author hwliang<2021-08-09>
            @param connects<pconn>
            @return list
        '''
        result = []
        for i in connects:
            raddr = i.raddr
            if not i.raddr:
                raddr = ('',0)
            laddr = i.laddr
            if not i.laddr:
                laddr = ('',0)
            result.append({
                "fd": i.fd,
                "family": i.family,
                "local_addr": laddr[0],
                "local_port": laddr[1],
                "client_addr": raddr[0],
                "client_rport": raddr[1],
                "status": i.status
            })
        return result


    def get_process_info_by_pid(self,pid):
        '''
            @name 获取进程信息
            @author hwliang<2021-08-12>
            @param pid: int<进程id>
            @return dict
        '''
        process_info = {}
        try:
            if not os.path.exists('/proc/{}'.format(pid)): return process_info
            p = psutil.Process(pid)
            status_ps = {'sleeping':'睡眠','running':'活动'}
            with p.oneshot():
                p_mem = p.memory_full_info()
                if p_mem.uss + p_mem.rss + p_mem.pss + p_mem.data == 0: return process_info
                p_state = p.status()
                if p_state in status_ps: p_state = status_ps[p_state]
                # process_info['exe'] = p.exe()
                process_info['name'] = p.name()
                process_info['pid'] = pid
                process_info['ppid'] = p.ppid()
                process_info['create_time'] = int(p.create_time())
                process_info['status'] = p_state
                process_info['user'] = p.username()
                process_info['memory_used'] = p_mem.uss
                process_info['cpu_percent'] = self.get_cpu_precent(p)
                process_info['io_write_bytes'],process_info['io_read_bytes'] = self.get_io_speed(p)
                process_info['connections'] = self.format_connections(p.connections())
                process_info['connects'] = self.get_connects(pid)
                process_info['open_files'] = self.list_to_dict(p.open_files())
                process_info['threads'] = p.num_threads()
                process_info['exe'] = ' '.join(p.cmdline())
                return process_info
        except:
            return process_info


    def get_io_speed(self,p):
        '''
            @name 获取磁盘IO速度
            @author hwliang<2021-08-12>
            @param p: Process<进程对像>
            @return list
        '''
        skey = "io_speed_{}".format(p.pid)
        old_pio = cache.get(skey)
        pio = p.io_counters()
        if not old_pio:
            cache.set(skey,[pio,time.time()],3600)
            # time.sleep(0.1)
            old_pio = cache.get(skey)
            pio = p.io_counters()
        
        old_write_bytes = old_pio[0].write_bytes
        old_read_bytes = old_pio[0].read_bytes
        old_time = old_pio[1]

        new_time = time.time()
        write_bytes = pio.write_bytes
        read_bytes = pio.read_bytes

        cache.set(skey,[pio,new_time],3600)

        write_speed = int((write_bytes - old_write_bytes) / (new_time - old_time))
        read_speed = int((read_bytes - old_read_bytes) / (new_time - old_time))
        
        return write_speed,read_speed


    


    def get_cpu_precent(self,p):
        '''
            @name 获取进程cpu使用率
            @author hwliang<2021-08-09>
            @param p: Process<进程对像>
            @return dict
        '''
        skey = "cpu_pre_{}".format(p.pid)
        old_cpu_times = cache.get(skey)
        
        process_cpu_time = self.get_process_cpu_time(p.cpu_times())
        if not old_cpu_times:
            cache.set(skey,[process_cpu_time,time.time()],3600)
            # time.sleep(0.1)
            old_cpu_times = cache.get(skey)
            process_cpu_time = self.get_process_cpu_time(p.cpu_times())
        
        old_process_cpu_time = old_cpu_times[0]
        old_time = old_cpu_times[1]
        new_time = time.time()
        cache.set(skey,[process_cpu_time,new_time],3600)
        percent = round(100.00 * (process_cpu_time - old_process_cpu_time) / (new_time - old_time) / psutil.cpu_count(),2)
        return percent

    
    def get_process_cpu_time(self,cpu_times):
        cpu_time = 0.00
        for s in cpu_times: cpu_time += s
        return cpu_time


    def get_project_run_state(self,get = None,project_name = None):
        '''
            @name 获取项目运行状态
            @author hwliang<2021-08-12>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @param project_name<string> 项目名称
            @return bool
        '''
        if get: project_name = get.project_name.strip()
        pid_file = "{}/{}.pid".format(self._node_pid_path,project_name)
        if not os.path.exists(pid_file): return False
        data=public.readFile(pid_file)
        if isinstance(data,str) and data:
            pid = int(data)
            pids = self.get_project_pids(pid=pid)
        else:
            return False
        if not pids: return False
        return True

    def get_project_find(self,project_name):
        '''
            @name 获取指定项目配置
            @author hwliang<2021-08-09>
            @param project_name<string> 项目名称
            @return dict
        '''
        project_info = public.M('sites').where('project_type=? AND name=?',('Node',project_name)).find()
        if not project_info: return False
        project_info['project_config'] = json.loads(project_info['project_config'])
        return project_info
        

    def get_project_info(self,get):
        '''
            @name 获取指定项目信息
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        project_info = public.M('sites').where('project_type=? AND name=?',('Node',get.project_name)).find()
        if not project_info: return public.return_error('指定项目不存在!')
        project_info = self.get_project_stat(project_info)
        return project_info


    def get_project_stat(self,project_info):
        '''
            @name 获取项目状态信息
            @author hwliang<2021-08-09>
            @param project_info<dict> 项目信息
            @return list
        '''
        project_info['project_config'] = json.loads(project_info['project_config'])
        project_info['run'] = self.get_project_run_state(project_name = project_info['name'])
        project_info['load_info'] = self.get_project_load_info(project_name = project_info['name'])
        project_info['ssl'] = self.get_ssl_end_date(project_name = project_info['name'])
        project_info['listen'] = []
        project_info['listen_ok'] = True
        if project_info['load_info']:
            for pid in project_info['load_info'].keys():
                for conn in project_info['load_info'][pid]['connections']:
                    if not conn['status'] == 'LISTEN': continue
                    if not conn['local_port'] in project_info['listen']:
                        project_info['listen'].append(conn['local_port'])
            if project_info['listen']:
                project_info['listen_ok'] = project_info['project_config']['port'] in project_info['listen']
        return project_info
            
        

    def get_project_state(self,project_name):
        '''
            @name 获取项目状态
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return dict
        '''
        project_info = public.M('sites').where('project_type=? AND name=?',('Node',project_name)).find()
        if not project_info: return False
        return project_info['status']

    def get_project_listen(self,project_name):
        '''
            @name 获取项目监听端口
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return dict
        '''
        project_config = json.loads(public.M('sites').where('name=?',project_name).getField('project_config'))
        if 'listen_port' in project_config: return project_config['listen_port']
        return False


    def set_project_listen(self,get):
        '''
            @name 设置项目监听端口（请设置与实际端口相符的，仅在自动获取不正确时使用）
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
                port: int<端口>
            }
            @return dict
        '''
        project_config = json.loads(public.M('sites').where('name=?',get.project_name).getField('project_config'))
        project_config['listen_port'] = get.port
        public.M('sites').where('name=?',get.project_name).save('project_config',json.dumps(project_config))
        public.WriteLog(self._log_name, '修改项目['+get.project_name+']的端口为为['+get.port+']')
        return public.return_data(True,'设置成功')


    def set_project_nodejs_version(self,get):
        '''
            @name 设置nodejs版本
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
                nodejs_version: string<nodejs版本>
            }
            @return dict
        '''

        project_config = json.loads(public.M('sites').where('name=?',get.project_name).getField('project_config'))
        project_config['nodejs_version'] = get.nodejs_version
        public.M('sites').where('name=?',get.project_name).save('project_config',json.dumps(project_config))
        public.WriteLog(self._log_name, '修改项目['+get.project_name+']的nodejs版本为['+get.nodejs_version+']')
        return public.return_data(True,'设置成功')

    def get_project_nodejs_version(self,project_name):
        '''
            @name 获取nodejs版本
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return string
        '''

        project_config = json.loads(public.M('sites').where('name=?',project_name).getField('project_config'))
        if 'nodejs_version' in project_config: return project_config['nodejs_version']
        return False


    def check_port_is_used(self,port,sock=False):
        '''
            @name 检查端口是否被占用
            @author hwliang<2021-08-09>
            @param port: int<端口>
            @return bool
        '''
        if not isinstance(port,int): port = int(port)
        if port == 0: return False
        project_list = public.M('sites').where('status=? AND project_type=?',(1,'Node')).field('name,path,project_config').select()
        for project_find in project_list:
            project_config = json.loads(project_find['project_config'])
            if not 'port' in project_config: continue
            if int(project_config['port']) == port: return True
        if sock: return False
        return public.check_tcp('127.0.0.1',port)

    def get_project_run_state_byaotu(self,project_name):
        '''
            @name 获取项目运行状态
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return dict
        '''
        pid_file = "{}/{}.pid".format(self._node_pid_path,project_name)
        if not os.path.exists(pid_file): return False
        pid = public.readFile(pid_file)
        pids = self.get_project_pids(pid=pid)
        if not pids: return False
        return True

    def auto_run(self):
        '''
            @name 自动启动所有项目
            @author hwliang<2021-08-09>
            @return bool
        '''
        project_list = public.M('sites').where('project_type=?',('Node',)).field('name,path,project_config').select()
        get= public.dict_obj()
        success_count = 0
        error_count = 0
        for project_find in project_list:
            try:
                project_config = json.loads(project_find['project_config'])
                if project_config['is_power_on'] in [0,False,'0',None]: continue
                project_name = project_find['name']
                project_state = self.get_project_run_state(project_name=project_name)
                if not project_state:
                    get.project_name = project_name
                    result = self.start_project(get)
                    if not result['status']:
                        error_count += 1
                        error_msg = '自动启动Nodej项目['+project_name+']失败!'
                        public.WriteLog(self._log_name, error_msg)
                        public.print_log(error_msg + ", " + result['error_msg'],'ERROR')
                    else:
                        success_count += 1
                        success_msg = '自动启动Nodej项目['+project_name+']成功!'
                        public.WriteLog(self._log_name, success_msg)
                        public.print_log(success_msg,'INFO')
            except:
                error_count += 1
                public.print_log(public.get_error_info(),'ERROR')
        if (success_count + error_count) < 1: return False
        dene_msg = '共需要启动{}个Nodejs项目，成功{}个，失败{}个'.format(success_count + error_count,success_count,error_count)
        public.WriteLog(self._log_name, dene_msg)
        public.print_log(dene_msg,'INFO')
        return True
