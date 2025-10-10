# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2017 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwl@bt.cn
# +-------------------------------------------------------------------
# +--------------------------------------------------------------------
# |   前置web服务器控制器
# +--------------------------------------------------------------------

import os
from sys import path as sys_path
from platform import machine

# 设置运行目录
os.chdir('/www/server/panel')

# 添加自定义公共模块路径
if not 'class/' in sys_path:
    sys_path.insert(0,'class/')

# 引入自定义公共模块
import public


class webserver:


    def __init__(self):
        '''
            @name 初始化
        '''
        if not hasattr(public,'get_panel_path'):
            self.__panel_path = '/www/server/panel'
        else:
            self.__panel_path = public.get_panel_path()


        self.__webserver_bin = os.path.join(self.__panel_path,'webserver/sbin/webserver')   # webserver二进制文件
        self.__webserver_conf = os.path.join(self.__panel_path,'webserver/conf/webserver.conf') # webserver配置文件
        self.__webserver_pid = os.path.join(self.__panel_path,'webserver/logs/webserver.pid') # webserver进程PID
        self.__webserver_ctl = os.path.join(self.__panel_path,'script/webserver-ctl.sh')  # webserver控制脚本
        self.__panel_port_file = os.path.join(self.__panel_path, 'data/port.pl')  # 面板端口文件
        self.__ssl_key_file = os.path.join(self.__panel_path, 'ssl/privateKey.pem') # SSL私钥文件
        self.__ssl_crt_file = os.path.join(self.__panel_path,'ssl/certificate.pem') # SSL证书文件
        self.__is_ssl_file = os.path.join(self.__panel_path,'data/ssl.pl') # 是否开启SSL文件
        self.__examples_path = os.path.join(self.__panel_path, 'config/examples') # 配置文件模板目录
        self.__webserver_conf_example = os.path.join(self.__examples_path ,'webserver.conf') # webserver配置文件模板
        self.__webserver_ssl_conf_example = os.path.join(self.__examples_path ,'webserver_ssl.conf') # webserver SSL配置文件模板
        self.__webserver_listen_conf_example = os.path.join(self.__examples_path ,'webserver_listen.conf') # webserver监听配置文件模板
        self.__webserver_listen_ssl_conf_example = os.path.join(self.__examples_path ,'webserver_listen_ssl.conf') # webserver SSL监听配置文件模板
        self.__default_port = 8888 # 默认端口
        self.__log_error = 'ERROR' 
        self.__log_debug = 'DEBUG'
        self.__log_info = 'INFO'
        self.__log_warning = 'WARNING'
    

    def print_log(self,msg,level='INFO'):
        '''
            @name 打印日志
            @param msg str 日志内容
            @param level str 日志级别
            @return void
        '''
        if not hasattr(public,'print_log'):
            print("[{}]".format(level),msg)
        else:
            public.print_log(msg,level)

    def exec_shell(self,cmd):
        '''
            @name 执行shell命令
            @param cmd str shell命令
            @return tuple
        '''
        res = public.ExecShell(cmd)
        if isinstance(res,tuple):
            return res
        else:
            return ('',res)
        
        
        

    # 获取系统架构是X86还是ARM
    def get_machine(self):
        arch = machine()
        return arch
    
    def bin_exists(self):
        '''
            @name 判断webserver二进制文件是否存在
            @return bool
        '''
        return os.path.exists(self.__webserver_bin)
    
    def conf_exists(self):
        '''
            @name 判断webserver配置文件是否存在
            @return bool
        '''
        return os.path.exists(self.__webserver_conf)
    
    def conf_example_exists(self):
        '''
            @name 判断webserver配置文件模板是否存在
            @return bool
        '''
        return os.path.exists(self.__webserver_conf_example)
    
    def pid_exists(self):
        '''
            @name 判断webserver进程PID是否存在
            @return bool
        '''
        return os.path.exists(self.__webserver_pid)
    
    def ctl_exists(self):
        '''
            @name 判断webserver-ctl.sh是否存在
            @return bool
        '''
        return os.path.exists(self.__webserver_ctl)
    
    def hasattr_public(self,defname):
        '''
            @name 判断public模块是否存在
            @return bool
        '''
        if hasattr(public,defname):
            return True
        
        self.print_log('public.{} not found.'.format(defname),self.__log_error)
        return False
    
    def process_status(self):
        '''
            @name 判断webserver进程是否存在
            @return bool
        '''
        if not self.pid_exists():
            return False

        res = self.exec_shell("bash {} status".format(self.__webserver_ctl))

        if res[0].find('not running') != -1:
            return False
        return True
    
    def start(self):
        '''
            @name 启动webserver
            @return bool
        '''
        if self.process_status():
            return False
        


        res = self.exec_shell("bash {} start".format(self.__webserver_ctl))
        if res[0].find('Failed') != -1:
            self.print_log(res,self.__log_warning)
            return False
        
        return True
    
    def stop(self):
        '''
            @name 停止webserver
            @return bool
        '''
        if not self.process_status():
            return False
        res = self.exec_shell("bash {} stop".format(self.__webserver_ctl))
        if res[0].find('Failed') != -1:
            self.print_log(res,self.__log_warning)
            return False
        return True
    
    def restart(self):
        '''
            @name 重启webserver
            @return bool
        '''
        res = self.exec_shell("bash {} restart".format(self.__webserver_ctl))
        if res[0].find('Failed') != -1:
            self.print_log(res,self.__log_warning)
            return False
        return True
    
    def reload(self):
        '''
            @name 重载webserver
            @return bool
        '''
        res = self.exec_shell("bash {} reload".format(self.__webserver_ctl))
        if res[0].find('Failed') != -1:
            self.print_log(res,self.__log_warning)
            return False
        return True
    
    def get_status(self):
        '''
            @name 获取webserver状态
            @return bool
        '''
        return self.process_status()
    
    def configtest(self):
        '''
            @name 测试配置文件是否正确
            @return bool
        '''
        res = self.exec_shell("bash {} configtest".format(self.__webserver_ctl))
        result = "\n".join(res)
        
        if result.find('successful') != -1:
            return True
        
        self.print_log(result,self.__log_warning)
        return False
    
    def get_panel_port(self):
        '''
            @name 获取面板端口
            @return int
        '''
        
        # 如果面板端口文件不存在，则使用默认端口
        if not os.path.exists(self.__panel_port_file):
            return self.__default_port
        
        # 读取面板端口文件
        port = public.ReadFile(self.__panel_port_file)
        if not port:
            return self.__default_port
        
        try:
            # 判断端口是否在1-65535之间
            port = int(port)
            if port < 1 or port > 65535:
                return self.__default_port
        except:
            return self.__default_port
        
        return port
        
    def is_ssl(self):
        '''
            @name 是否开启了SSL
            @return bool
        '''
        if os.path.exists(self.__is_ssl_file):
            # 如果开启了SSL，则判断SSL证书和私钥文件是否存在
            if os.path.exists(self.__ssl_key_file) and os.path.exists(self.__ssl_crt_file):
                return True
        return False
    
    def get_ssl_config(self):
        '''
            @name 获取SSL配置
            @return dict
        '''
        # 如果没有开启SSL，则返回空字符串
        if not self.is_ssl():
            return ''
        
        ssl_conf = public.ReadFile(self.__webserver_ssl_conf_example)
        if not ssl_conf:
            self.print_log('Ssl configuration file not found.',self.__log_warning)
            return ''
        
        return ssl_conf
    
    def get_http3_header(self):
        '''
            @name 获取HTTP3头部
            @return dict
        '''
        http3_header = ''

        # 如果开启了SSL，则添加HTTP3头部
        if self.is_ssl():
            '''h3=":443"; ma=2592000,h3-29=":443"; ma=2592000'''
            http3_header =  "add_header Alt-Svc 'h3=\":{PORT}\"; ma=86400,h3-29=\":{PORT}\"; ma=86400';".format(PORT=self.get_panel_port())

        return http3_header
    
    def get_listen_config(self):
        '''
            @name 获取监听配置
            @return dict
        '''
        default_listen = '''
        listen {PORT};
        listen [::]:{PORT};
'''
        # 是否开启了SSL
        if self.is_ssl():
            
            listen_conf = public.ReadFile(self.__webserver_listen_ssl_conf_example)
        else:
            listen_conf = public.ReadFile(self.__webserver_listen_conf_example)
        
        # 如果没有找到监听配置文件，则使用默认监听配置
        if not listen_conf:
            listen_conf = default_listen
        
        # 替换面板端口
        port = self.get_panel_port()
        listen_conf = listen_conf.format(PORT=port)

        return listen_conf
        
    
    def create_conf(self):
        '''
            @name 创建配置文件
            @return bool
        '''
        if not self.conf_example_exists():
            self.print_log('Web server configuration file template not found.',self.__log_error)
            return False
        
        # 读取配置文件模板
        config_example = public.ReadFile(self.__webserver_conf_example)
        if not config_example:
            self.print_log('Web server configuration file template read failed.',self.__log_error)
            return False
        
        # 获取监听配置
        listen_conf = self.get_listen_config()
        # 获取SSL配置
        ssl_conf = self.get_ssl_config()
        # 获取HTTP3头部
        http3_header = self.get_http3_header()

        config = config_example.format(LISTEN=listen_conf, SSL_CONFIG=ssl_conf, HTTP3_HEADER=http3_header)
        res = public.WriteFile(self.__webserver_conf, config)
        if not res:
            self.print_log("Write Web server configuration file failed",self.__log_error)
            return False

        # 测试配置文件是否正确
        if not self.configtest():
            self.print_log('Web server configuration file test failed.',self.__log_error)
            return False

        return True
    
    def chmod_static_files(self):
        '''
            @name 设置静态文件权限
            @return bool
        '''
        # 设置静态目录链权限
        res = self.exec_shell('chmod 755 /www /www/server /www/server/panel /www/server/panel/BTPanel')
        if res[1] != '':
            self.print_log('\n'.join(res),self.__log_warning)
            return False
        
        # 递归设置静态文件权限
        res = self.exec_shell('chmod  -R 755 /www/server/panel/BTPanel/static')
        if res[1] != '':
            self.print_log('\n'.join(res),self.__log_warning)
            return False
        
        return True
    
    def run_webserver(self):
        '''
            @name 启动web服务器
            @return bool 是否成功
        '''

        try:
            # 判断public模块是否符合要求
            public_function = ['ExecShell','ReadFile','WriteFile','get_error_info','get_panel_path','get_panel_port','print_log']
            for func in public_function:
                if not self.hasattr_public(func):
                    return False

            # 判断webserver二进制文件是否存在，如果不存在则尝试调用下载脚本下载
            if not self.bin_exists():
                if os.path.exists(self.__webserver_ctl):
                    self.exec_shell("bash {} download".format(self.__webserver_ctl))
                self.print_log('Web server binary file not found.',self.__log_error)
                return False
            
            # 判断cli工具脚本是否存在
            if not self.ctl_exists():
                self.print_log('Web server command line tool not found.',self.__log_error)
                return False
            
            # 设置静态文件权限
            if not self.chmod_static_files():
                self.print_log('Web server static file permission setting failed.',self.__log_error)
                return False
            
            # 创建配置文件
            if not self.create_conf():
                self.print_log('Web server configuration file creation failed.',self.__log_error)
                return False
            
            # 检查webserver进程是否存在，如果存在则重载，否则启动
            if self.process_status():
                res = self.reload()
                if not res:
                    self.print_log('Web server reload failed.',self.__log_warning)
            else:
                res = self.start()
                # 检查进程是否正常运行
                if not res:
                    self.print_log('Web server start failed.',self.__log_error)
                    return False
        except:
            # 将错误信息写入到日志
            self.print_log(public.get_error_info(),self.__log_error)
            return False

        return True

if __name__ == '__main__':
    
    web = webserver()
    print(web.run_webserver())
