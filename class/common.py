# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c)  2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author :   hwliang  <hwl@bt.cn>
# +-------------------------------------------------------------------
from BTPanel import session, cache, request, redirect, g, abort,Response
from datetime import datetime
from public import dict_obj
import os
import public
import json
import sys
import time
from theme_config import ThemeConfigManager


class panelSetup:
    def init(self):
        panel_path = public.get_panel_path()
        if os.getcwd() != panel_path: os.chdir(panel_path)

        g.ua = request.headers.get('User-Agent', '')
        if g.ua:
            ua = g.ua.lower()
            if ua.find('spider') != -1 or g.ua.find('bot') != -1:
                return abort(403)

        g.version = '11.3.0'
        g.title = public.GetConfigValue('title')
        g.uri = request.path
        g.debug = os.path.exists('data/debug.pl')
        g.pyversion = sys.version_info[0]
        session['version'] = g.version
        # 初始化主题配置管理器（默认检测是否存在配置文件，并新建）
        theme_manager = ThemeConfigManager()
        # 获取主题配置数据
        theme_manager_data = theme_manager.get_config()
        # 获取主题配置
        g.panel_theme = theme_manager_data['data']

        if not public.get_improvement(): session['is_flush_soft_list'] = 1
        if request.method == 'GET':
            if not g.debug:
                g.cdn_url = public.get_cdn_url()
                if not g.cdn_url:
                    g.cdn_url = '/static'
                else:
                    g.cdn_url = '//' + g.cdn_url + '/' + g.version
            else:
                g.cdn_url = '/static'
            session['title'] = g.title

        g.recycle_bin_open = 0
        if os.path.exists("data/recycle_bin.pl"): g.recycle_bin_open = 1

        g.recycle_bin_db_open = 0
        if os.path.exists("data/recycle_bin_db.pl"): g.recycle_bin_db_open = 1
        g.is_aes = False
        self.other_import()
        return None

    def other_import(self):
        g.o = public.readFile('data/o.pl')
        g.other_css = []
        g.other_js = []
        if g.o:
            s_path = 'BTPanel/static/other/{}'
            css_name = "css/{}.css".format(g.o)
            css_file = s_path.format(css_name)
            if os.path.exists(css_file): g.other_css.append('/static/other/{}'.format(css_name))

            js_name = "js/{}.js".format(g.o)
            js_file = s_path.format(js_name)
            if os.path.exists(js_file): g.other_js.append('/static/other/{}'.format(js_name))

    def auto_complete_params(self,target_params,default_values,param_mapping=None):
        '''
        自动补全参数缺少的值并支持参数名称替换
        参数:
        target_params (dict): 参数字典
        default_values (dict): 默认值字典（默认值）
        param_mapping (dict, optional): 参数名称映射字典，用于替换参数名称
        返回:
        dict: {'status': bool, 'data': dict}
        '''
        # 创建一个新字典，避免修改原始字典
        result = target_params.copy()

        mapping_adjusted = False
        # 处理参数名称替换
        if param_mapping:
            for old_name, new_name in param_mapping.items():
                if old_name in result:
                    result[new_name] = result.pop(old_name)
                    mapping_adjusted = True

        # 遍历默认值字典，检查目标参数字典
        for key, value in default_values.items():
            if key not in result:
                result[key] = value
            elif isinstance(result[key], dict) and isinstance(value, dict):
                # 递归处理嵌套字典
                recursive_result = self.auto_complete_params(result[key], value, param_mapping)
                if not recursive_result['status']:
                    mapping_adjusted = True
                result[key] = recursive_result['data']

        if mapping_adjusted:
            return {'status': False, 'data': {}}
        return {'status': True, 'data': result}


class panelAdmin(panelSetup):
    setupPath = '/www/server'

    # 本地请求
    def local(self):
        result = panelSetup().init()
        if result:
            return result
        result = self.check_login()
        if result:
            return result
        result = self.setSession()
        if result:
            return result
        result = self.checkClose()
        if result:
            return result
        result = self.checkWebType()
        if result:
            return result
        result = self.checkConfig()
        self.GetOS()

    # 设置基础Session
    def setSession(self):
        if request.method == 'GET':
            import config
            con = config.config()
            menus = con.get_menu_list(None)
            g.menus = json.dumps(menus)
            session['menus'] = g.menus
            g.yaer = datetime.now().year

        if not 'brand' in session:
            session['brand'] = public.GetConfigValue('brand')
            session['product'] = public.GetConfigValue('product')
            session['rootPath'] = '/www'
            session['download_url'] = public.GetConfigValue('download')
            session['setupPath'] = session['rootPath'] + '/server'
            session['logsPath'] = '/www/wwwlogs'
            session['yaer'] = datetime.now().year
        # if not 'menu' in session:
        if session.get('uid', None) == 1:
            import config
            con = config.config()
            menus = con.get_menu_list(None)
            g.menus = json.dumps(menus)
            session['menus'] = g.menus
            g.yaer = datetime.now().year
                
        if not 'lan' in session:
            session['lan'] = public.GetLanguage()
        if not 'home' in session:
            session['home'] = public.GetConfigValue('home')
        return False

    # 检查Web服务器类型
    def checkWebType(self):
        # if request.method == 'GET':
        if not 'webserver' in session:
            if os.path.exists('/usr/local/lsws/bin/lswsctrl'):
                session['webserver'] = 'openlitespeed'
            elif os.path.exists(self.setupPath + '/apache/bin/apachectl'):
                session['webserver'] = 'apache'
            else:
                session['webserver'] = 'nginx'
        if not 'webversion' in session:
            if os.path.exists(self.setupPath + '/' + session['webserver'] + '/version.pl'):
                session['webversion'] = public.ReadFile(self.setupPath + '/' + session['webserver'] + '/version.pl').strip()

        if not 'phpmyadminDir' in session:
            filename = self.setupPath + '/data/phpmyadminDirName.pl'
            if os.path.exists(filename):
                session['phpmyadminDir'] = public.ReadFile(filename).strip()
        return False

    # 检查面板是否关闭
    def checkClose(self):
        if os.path.exists('data/close.pl'):
            return redirect('/close')

    # 跳转到登录页面
    def to_login(self,url,msg = "登录已失效，请重新登录"):
        x_http_token = request.headers.get('X-Http-Token', '')
        if x_http_token:
            # 如果是ajax请求
            res = {"status":False,"msg":msg,"redirect":url}
            return Response(json.dumps(res), content_type='application/json')

        return redirect(url)

    # 检查登录
    def check_login(self):
        try:
            api_check = True
            g.api_request = False
            if not 'login' in session:
                api_check = self.get_sk()
                if api_check:
                    return api_check
                g.api_request = True
            else:
                if session['login'] == False:
                    session.clear()
                    return self.to_login(public.get_admin_path())

                if 'tmp_login_expire' in session:
                    s_file = 'data/session/{}'.format(session['tmp_login_id'])
                    if session['tmp_login_expire'] < time.time():
                        session.clear()
                        if os.path.exists(s_file): os.remove(s_file)
                        return self.to_login(public.get_admin_path(), '临时登录已过期，请重新登录')
                    if not os.path.exists(s_file):
                        session.clear()
                        return self.to_login(public.get_admin_path(),'临时登录已失效，请重新登录')

                # 检查客户端hash -- 不要删除
                if not public.check_client_hash():
                    session.clear()
                    return self.to_login(public.get_admin_path(),'客户端验证失败，请重新登录')

            if api_check:
                now_time = time.time()
                session_timeout = session.get('session_timeout', 0)
                if session_timeout < now_time and session_timeout != 0:
                    session.clear()
                    return self.to_login(public.get_admin_path(),"登录会话已过期，请重新登录")

            login_token = session.get('login_token', '')
            if login_token:
                if login_token != public.get_login_token_auth():
                    session.clear()
                    return self.to_login(public.get_admin_path(),'登录验证失败，请重新登录')

            # if api_check:
            #     filename = 'data/sess_files/' + public.get_sess_key()
            #     if not os.path.exists(filename):
            #         session.clear()
            #         return redirect(public.get_admin_path())

            # 标记新的会话过期时间
            self.check_session()
        except:
            session.clear()
            public.print_error()
            return self.to_login('/login','登录已失效，请重新登录')


    def check_session(self):
        white_list = ['/favicon.ico', '/system?action=GetNetWork']
        if g.uri in white_list:
            return
        session['session_timeout'] = time.time() + public.get_session_timeout()

    # 获取sk
    def get_sk(self):
        save_path = '/www/server/panel/config/api.json'
        if not os.path.exists(save_path):
            return public.redirect_to_login()

        try:
            api_config = json.loads(public.ReadFile(save_path))
        except:
            os.remove(save_path)
            return public.redirect_to_login()

        if not api_config['open']:
            return public.redirect_to_login()
        from BTPanel import get_input
        get = get_input()
        client_ip = public.GetClientIp()
        if not 'client_bind_token' in get:
            if not 'request_token' in get or not 'request_time' in get:
                return public.redirect_to_login()

            num_key = client_ip + '_api'
            if not public.get_error_num(num_key, 20):
                return public.returnJson(False, '连续20次验证失败,禁止1小时')

            if not public.is_api_limit_ip(api_config['limit_addr'], client_ip):  # client_ip in api_config['limit_addr']:
                public.set_error_num(num_key)
                return public.returnJson(False, 'IP校验失败,您的访问IP为[' + client_ip + ']')
        else:
            if not public.check_app('app'):
                return public.returnMsg(False, '未绑定用户!')
            num_key = client_ip + '_app'
            if not public.get_error_num(num_key, 20):
                return public.returnJson(False, '连续20次验证失败,禁止1小时')
            a_file = '/dev/shm/' + get.client_bind_token

            if not public.path_safe_check(get.client_bind_token):
                public.set_error_num(num_key)
                return public.returnJson(False, '非法请求')

            if not os.path.exists(a_file):
                import panelApi
                if not panelApi.panelApi().get_app_find(get.client_bind_token):
                    public.set_error_num(num_key)
                    return public.returnJson(False, '未绑定的设备')
                public.writeFile(a_file, '')

            if not 'key' in api_config:
                public.set_error_num(num_key)
                return public.returnJson(False, '密钥校验失败')
            if not 'form_data' in get:
                public.set_error_num(num_key)
                return public.returnJson(False, '没有找到form_data数据')

            g.form_data = json.loads(public.aes_decrypt(get.form_data, api_config['key']))

            get = get_input()
            if not 'request_token' in get or not 'request_time' in get:
                return public.error_not_login('/login')
            g.is_aes = True
            g.aes_key = api_config['key']

        request_token = public.md5(get.request_time + api_config['token'])
        if get.request_token == request_token:
            public.set_error_num(num_key, True)
            session["api_request_tip"] = True
            return False
        public.set_error_num(num_key)
        return public.returnJson(False, '密钥校验失败')

    # 检查系统配置
    def checkConfig(self):
        if not 'config' in session:
            session['config'] = public.M('config').where("id=?", ('1',)).field(
                'webserver,sites_path,backup_path,status,mysql_root').find()
            if session['config'] and not 'email' in session['config']:
                session['config']['email'] = public.M(
                    'users').where("id=?", ('1',)).getField('email')
            if not 'address' in session:
                session['address'] = public.GetLocalIp()
        return False

    # 获取操作系统类型
    def GetOS(self):
        """
        获取操作系统类型
        1. 以 /etc/os-release 为主要判断依据
        2. 多种包管理工具为辅助判断
        3. 添加更多条件判断方式
        """
        if not 'server_os' in session:
            tmp = {
                'x': 'Unknown',  # 默认操作系统类型
                'osname': 'Linux'  # 默认系统名称
            }

            try:
                # 优先使用 /etc/os-release 文件判断（最标准的方式）
                if os.path.exists('/etc/os-release'):
                    os_info = self.parse_os_release('/etc/os-release')
                    tmp['x'] = os_info['type']
                    tmp['osname'] = os_info['name']
                else:
                    # 备用判断方式
                    tmp = self.detect_os_by_traditional_methods(tmp)

            except Exception as e:
                # 记录错误但不影响程序继续执行
                public.WriteLog('系统检测', f'操作系统检测失败: {str(e)}')
                tmp['x'] = 'Unknown'
                tmp['osname'] = 'Linux'
            # public.print_log('系统检测', f'操作系统类型: {tmp["x"]}, 系统名称: {tmp["osname"]}')
            session['server_os'] = tmp
        return False

    @staticmethod
    def parse_os_release(filepath):
        """
        解析 /etc/os-release 文件获取系统信息
        """
        os_type = 'Unknown'
        os_name = 'Linux'

        try:
            with open(filepath, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                os_info = {}
                for line in lines:
                    if '=' in line:
                        key, value = line.split('=', 1)
                        os_info[key] = value.strip('"')

                # 根据 ID 判断系统类型
                if 'ID' in os_info:
                    os_id = os_info['ID'].lower()
                    if os_id in ['centos', 'rhel', 'fedora', 'rocky', 'almalinux', "alinux", "alibaba"
                                 "centos-stream", "opencloudos", "tencentos", "openeuler"]:
                        os_type = 'RHEL'
                    elif os_id in ['ubuntu', 'debian']:
                        os_type = 'Debian'
                    elif os_id in ['opensuse', 'sles']:
                        os_type = 'SUSE'
                    else:
                        os_type = 'RHEL'

                # 获取系统名称
                if 'PRETTY_NAME' in os_info:
                    os_name = os_info['PRETTY_NAME']
                elif 'NAME' in os_info:
                    os_name = os_info['NAME']

        except Exception:
            pass

        return {'type': os_type, 'name': os_name}

    def detect_os_by_traditional_methods(self, tmp):
        """
        使用传统方法检测操作系统
        """
        # RedHat 系列检测
        if os.path.exists('/etc/redhat-release'):
            tmp['x'] = 'RHEL'
            tmp['osname'] = self.get_osname('/etc/redhat-release') or 'RHEL'
        elif os.path.exists('/etc/centos-release'):
            tmp['x'] = 'RHEL'
            tmp['osname'] = self.get_osname('/etc/centos-release') or 'CentOS'
        elif os.path.exists('/etc/fedora-release'):
            tmp['x'] = 'RHEL'
            tmp['osname'] = self.get_osname('/etc/fedora-release') or 'Fedora'

        # Debian 系列检测
        elif os.path.exists('/etc/debian_version'):
            tmp['x'] = 'Debian'
            tmp['osname'] = self.get_osname('/etc/issue') or 'Debian'
        elif os.path.exists('/etc/issue'):
            issue_content = public.ReadFile('/etc/issue') or ''
            if 'Ubuntu' in issue_content:
                tmp['x'] = 'Debian'
                tmp['osname'] = 'Ubuntu'
            elif 'Debian' in issue_content:
                tmp['x'] = 'Debian'
                tmp['osname'] = 'Debian'
            else:
                tmp['x'] = 'Debian'
                tmp['osname'] = self.get_osname('/etc/issue') or 'Linux'

        # 通过包管理器判断
        elif os.path.exists('/usr/bin/yum') or os.path.exists('/bin/yum'):
            tmp['x'] = 'RHEL'
            tmp['osname'] = 'RHEL-based'
        elif os.path.exists('/usr/bin/apt') or os.path.exists('/bin/apt'):
            tmp['x'] = 'Debian'
            tmp['osname'] = 'Debian-based'
        elif os.path.exists('/usr/bin/zypper') or os.path.exists('/bin/zypper'):
            tmp['x'] = 'SUSE'
            tmp['osname'] = 'SUSE'

        return tmp

    def get_osname(self, i_file):
        '''
            @name 从指定文件中获取系统名称
            @author hwliang<2021-04-07>
            @param i_file<string> 指定文件全路径
            @return string
        '''
        if not os.path.exists(i_file): return ''
        issue_str = public.ReadFile(i_file).strip()
        if issue_str: return issue_str.split()[0]
        return ''
