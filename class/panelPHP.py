#coding:utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------

# +-------------------------------------------------------------------
# | PHP插件兼容模块
# +-------------------------------------------------------------------

import json,os,public,time,re,sys   
import time
import fastcgiClient as fcgi_client
import struct
FCGI_Header = '!BBHHBx'

if sys.version_info[0] == 2:
    try:
        from cStringIO import StringIO
    except:
        from StringIO import StringIO
else:
    from io import BytesIO as StringIO

class panelPHP:
    re_io = None
    def __init__(self,plugin_name = None):
        if plugin_name:
            self.__plugin_name = plugin_name
            self.__plugin_path = "/www/server/panel/plugin/%s" % plugin_name
            self.__args_dir = self.__plugin_path + '/args'
            self.__args_tmp = self.__args_dir + '/' + public.GetRandomString(32)
            if not os.path.exists(self.__args_dir): os.makedirs(self.__args_dir, 384)
        
    #调用PHP插件
    def exec_php_script(self,args):
        #取PHP执行文件和CLI配置参数
        php_bin = self.__get_php_bin()
        if not php_bin: return public.returnMsg(False,'没有找到兼容的PHP版本，请先安装')
        #是否将参数写到文件
        self.__write_args(args)
        result = os.popen("cd " + self.__plugin_path + " && %s /www/server/panel/class/panel_php_run.php --args_tmp=\"%s\" --plugin_name=\"%s\" --fun=\"%s\"" % 
                          (php_bin,self.__args_tmp,self.__plugin_name,args.s)).read()
        try:
            #解析执行结果
            result = json.loads(result)
        except: pass
        #删除参数文件
        if os.path.exists(self.__args_tmp): 
            os.remove(self.__args_tmp)
        return result
    
    #将参数写到文件
    def __write_args(self,args):
        from BTPanel import request
        if os.path.exists(self.__args_tmp): os.remove(self.__args_tmp)
        self.__clean_args_file()
        data = {}
        data['GET'] = request.args.to_dict()
        data['POST'] = {}
        x_token = request.headers.get('x-http-token')
        if x_token:
            aes_pwd = x_token[:8] + x_token[40:48]
        for key in request.form.keys():
            data['POST'][key] = str(request.form.get(key,''))
            if x_token:
                if len(data['POST'][key]) > 5:
                    if data['POST'][key][:6] == 'BT-CRT':
                        data['POST'][key] = public.aes_decrypt(data['POST'][key][6:],aes_pwd)
        data['POST']['client_ip'] = public.GetClientIp()
        data = json.dumps(data)
        public.writeFile(self.__args_tmp,data)
    
    #清理参数文件
    def __clean_args_file(self):
        args_dir = self.__plugin_path + '/args'
        if not os.path.exists(args_dir): return False
        now_time = time.time()
        for f_name in os.listdir(args_dir):
            filename = args_dir + '/' + f_name
            if not os.path.exists(filename): continue
            #清理创建时间超过60秒的参数文件
            if now_time - os.path.getctime(filename) > 60: os.remove(filename)
    
    #取PHP-CLI执行命令
    def __get_php_bin(self):
        #如果有指定兼容的PHP版本
        php_v_file = self.__plugin_path + '/php_version.json'
        if os.path.exists(php_v_file): 
             php_vs = json.loads(public.readFile(php_v_file).replace('.',''))
        else:
            #否则兼容所有版本
            php_vs = ["80","74","73","72","71","70","56","55","54","53","52"]
        #判段兼容的PHP版本是否安装
        php_path = "/www/server/php/"
        php_v = None
        for pv in php_vs:
            php_bin = php_path + pv + "/bin/php"
            if os.path.exists(php_bin): 
                php_v = pv
                break
        
        #如果没安装直接返回False
        if not php_v: return False
        #处理PHP-CLI-INI配置文件
        php_ini = self.__plugin_path + '/php_cli_'+php_v+'.ini'
        if not os.path.exists(php_ini):
            #如果不存在，则从PHP安装目录下复制一份
            src_php_ini = php_path + php_v + '/etc/php.ini'
            import shutil
            shutil.copy(src_php_ini,php_ini)
            #解除所有禁用函数
            php_ini_body = public.readFile(php_ini)
            php_ini_body = re.sub(r"disable_functions\s*=.*","disable_functions = ",php_ini_body)
            php_ini_body = re.sub(r".*bt_filter.+","",php_ini_body)
            public.writeFile(php_ini,php_ini_body)
        return php_path + php_v + '/bin/php -c ' + php_ini

    def get_php_version(self,php_version):
        if php_version:
            if not isinstance(php_version,list):
                php_vs = [php_version]
            else:
                php_vs = sorted(php_version,reverse=True)
        else:
            php_vs = ["80","74","73","72","71","70","56","55","54","53","52"]
        php_path = "/www/server/php/"
        php_v = None
        for pv in php_vs:
            php_bin = php_path + pv + "/bin/php"
            if os.path.exists(php_bin) and os.path.exists("/tmp/php-cgi-{}.sock".format(pv)): 
                php_v = pv
                break
        return php_v

#     def get_phpmyadmin_phpversion(self):
#         '''
#             @name 获取当前phpmyadmin设置的PHP版本
#             @author hwliang<2020-07-13>
#             @return string
#         '''
#         from BTPanel import cache
#         ikey = 'pma_phpv'
#         phpv = cache.get(ikey)
#         if phpv: return phpv
#         webserver = public.get_webserver()
#         if webserver == 'nginx':
#             filename = public.GetConfigValue('setup_path') + '/nginx/conf/enable-php.conf'
#             conf = public.readFile(filename)
#             if not conf: return None
#             rep = r"php-cgi-(\d+)\.sock"
#             phpv = re.findall(rep,conf)
#         elif webserver == 'openlitespeed':
#             filename = public.GetConfigValue('setup_path') + "/panel/vhost/openlitespeed/detail/phpmyadmin.conf"
#             conf = public.readFile(filename)
#             if not conf: return None
#             rep = r"/usr/local/lsws/lsphp(\d+)/bin/lsphp"
#             phpv = re.findall(rep,conf)
#         else:
#             filename = public.GetConfigValue('setup_path') + '/apache/conf/extra/httpd-vhosts.conf'
#             conf = public.readFile(filename)
#             if not conf: return None
#             rep = r"php-cgi-(\d+)\.sock"
#             phpv = re.findall(rep,conf)

#         if not phpv: return None
#         cache.set(ikey,phpv[0],3)
#         return phpv[0]

#     def get_pma_root(self):
#         '''
#             @name 获取phpmyadmin根目录
#             @author hwliang<2020-07-13>
#             @return string
#         '''
#         pma_path = '/www/server/phpmyadmin/'
#         if not os.path.exists(pma_path):
#             os.makedirs(pma_path)
#         for dname in os.listdir(pma_path):
#             if dname.find('phpmyadmin_') != -1:
#                 return os.path.join(pma_path,dname)
#         return None

#     def check_phpmyadmin_phpversion(self):
#         '''
#             @name 检查当前phpmyadmin版本可用的php版本列表
#             @author hwliang<2020-07-13>
#             @return list
#         '''
#         pma_path = '/www/server/phpmyadmin/'
#         pma_version_f1 = os.path.join(pma_path,'version_check.pl')
#         pma_root = os.path.join(pma_path,'pma')
#         pma_version_f2 = os.path.join(pma_root,'version_check.pl')
#         if not os.path.exists(pma_version_f1):
#             src_vfile = os.path.join(pma_path,'version.pl')
#             if os.path.exists(src_vfile):
#                 public.writeFile(pma_version_f1,public.readFile(src_vfile))
#         v_sync = public.readFile(pma_version_f1) == public.readFile(pma_version_f2)
        
#         if not os.path.exists(pma_root + '/index.php') or not v_sync:
#             o_pma_root = self.get_pma_root()
            
#             if o_pma_root:
#                 if not os.path.exists(pma_root):
#                     os.makedirs(pma_root)
#                 public.ExecShell("\cp -arf {}/* {}/".format(o_pma_root,pma_root))
#                 public.ExecShell("chown -R www:www {}".format(pma_root))
#                 public.ExecShell("chmod -R 700 {}".format(pma_root))
#                 public.ExecShell("\cp -arf {} {}".format(pma_version_f1,pma_version_f2))
#                 index = public.readFile(pma_root + '/index.php')
#                 if index:
#                     if index.find("use PhpMyAdmin\\Util") != -1:
#                         resp = "use PhpMyAdmin\\Util;\nif(function_exists('opcache_invalidate')) opcache_invalidate('/www/server/phpmyadmin/pma/config.inc.php');"
#                         index = index.replace("use PhpMyAdmin\\Util;",resp)
#                     elif index.find("use PMA\libraries\LanguageManager;") != -1:
#                         resp = "use PMA\libraries\LanguageManager;\nif(function_exists('opcache_invalidate')) opcache_invalidate('/www/server/phpmyadmin/pma/config.inc.php');"
#                         index = index.replace("use PMA\libraries\LanguageManager;",resp)
#                     elif index.find("require_once 'libraries/common.inc.php';") != -1:
#                         resp = "if(function_exists('opcache_invalidate')) opcache_invalidate('/www/server/phpmyadmin/pma/config.inc.php');\nrequire_once 'libraries/common.inc.php';"
#                         index = index.replace("require_once 'libraries/common.inc.php';",resp)

                    
#                     public.writeFile(pma_root + '/index.php',index)
        
#         if not os.path.exists(pma_version_f2):
#             return False

#         pma_version = public.readFile(pma_version_f2)
#         self.pma_version = pma_version
#         if pma_version:
#             pma_version = pma_version[:3]

#         if pma_version == '4.4':
#             return ['53','54','55','56']
#         elif pma_version == '4.0':
#             return ['52','53']
#         elif pma_version == '4.6':
#             return None
#         elif pma_version == '4.7':
#             return ['55','56','70','71','72']
#         elif pma_version in ['4.8','4.9','5.0']:
#             return ['70','71','72','73','74']
#         else:
#             return ['55','56','70','71','72']

#     def get_mysql_port(self):
#         '''
#             @name 获取mysql当前端口号
#             @author hwliang<2020-07-13>
#             @return int
#         '''
#         try:
#             myconf = public.readFile('/etc/my.cnf')
#             rep = r"port\s*=\s*([0-9]+)"
#             port = int(re.search(rep,myconf).groups()[0])
#             if not port: port = 3306
#             return port
#         except:
#             return 3306

#     def write_pma_passwd(self,username,password):
#         '''
#             @name 写入mysql帐号密码到配置文件
#             @author hwliang<2020-07-13>
#             @param username string(用户名)
#             @param password string(密码)
#             @return bool
#         '''

#         self.check_phpmyadmin_phpversion()
#         pconfig = 'cookie'
#         if username:
#             pconfig = 'config'
#         pma_path = '/www/server/phpmyadmin/'
#         pma_config_file = os.path.join(pma_path,'pma/config.inc.php')
#         conf = public.readFile(pma_config_file)
#         if not conf: return False
#         rep = r"/\* Authentication type \*/(.|\n)+/\* Server parameters \*/"
#         rstr = '''/* Authentication type */
# $cfg['Servers'][$i]['auth_type'] = '{}';
# $cfg['Servers'][$i]['host'] = 'localhost'; 
# $cfg['Servers'][$i]['port'] = '{}';
# $cfg['Servers'][$i]['user'] = '{}'; 
# $cfg['Servers'][$i]['password'] = '{}'; 
# /* Server parameters */'''.format(pconfig,self.get_mysql_port(),username,password)
#         conf = re.sub(rep,rstr,conf)
#         public.writeFile(pma_config_file,conf)
#         return True

#     def request_php(self,uri):
#         '''
#             @name 发起fastcgi请求到PHP-FPM
#             @author hwliang<2020-07-11>
#             @param puri string(URI地址)
#             @return socket
#         '''
#         php_unix_socket = '/tmp/php-cgi-{}.sock'.format(self.php_version)
#         f = FPM(php_unix_socket,self.document_root,self.last_path)
#         from BTPanel import request
#         if request.full_path.find('?') != -1:
#             uri = request.full_path[request.full_path.find(uri):]
#         if self.re_io:
#             sock = f.load_url(uri,content=self.re_io)
#         else:
#             sock = f.load_url(uri,content=request.stream)
#         return sock

#     def start(self,puri,document_root,last_path = ''):
#         '''
#             @name 开始处理PHP请求
#             @author hwliang<2020-07-11>
#             @param puri string(URI地址)
#             @return socket or Response
#         '''
#         if puri in ['/','',None]: puri = 'index.php'
#         if puri[0] == '/': puri = puri[1:]
#         self.document_root = document_root
#         self.last_path = last_path
#         filename = document_root + puri
        
#         from BTPanel import request,abort,send_file,Resp,cache
#         #如果是PHP文件
#         if puri[-4:] == '.php':
#             if  request.path.find('/phpmyadmin/') != -1:
#                 ikey = 'pma_php_version'
#                 self.php_version = cache.get(ikey)
#                 if not self.php_version:
#                     php_version = self.get_phpmyadmin_phpversion()
#                     php_versions = self.check_phpmyadmin_phpversion()
#                     if not php_versions:
#                         if php_versions == False:
#                             return Resp('因安全问题，已停止对phpMyAdmin4.6的支持，到软件商店卸载并安装其它安全版本!')
#                         else:
#                             return Resp('未安装phpmyadmin')
#                     if not php_version or not php_version in php_versions:
#                         php_version = php_versions
#                     self.php_version = self.get_php_version(php_version)
#                     if not self.php_version:
#                         php_version = self.check_phpmyadmin_phpversion()
#                         self.php_version = self.get_php_version(php_version)
#                         if not php_version:
#                             return Resp('没有找到支持的PHP版本: {}'.format(php_versions))

#                     if not self.php_version in php_versions:
#                         self.php_version = self.get_php_version(php_versions)
                    
#                         if not self.php_version:
#                                 return Resp('没有找到支持的PHP版本: {}'.format(php_versions))
#                     cache.set(ikey,self.php_version,1)

#                 if request.method == 'POST':
#                     #登录phpmyadmin
#                     if puri in ['index.php','/index.php']:
#                         content = public.url_encode(request.form.to_dict())
#                         if not isinstance(content,bytes):
#                             content = content.encode()
#                         self.re_io = StringIO(content)
#                         username = request.form.get('pma_username')
#                         if username:
#                             password = request.form.get('pma_password')
#                             if not self.write_pma_passwd(username,password):
#                                 return Resp('未安装phpmyadmin')

#                 if puri in ['logout.php','/logout.php']:
#                     self.write_pma_passwd(None,None)
#             else:
#                 src_path = '/www/server/panel/adminer'
#                 dst_path = '/www/server/adminer'
#                 if os.path.exists(src_path):
#                     if not os.path.exists(dst_path): os.makedirs(dst_path)
#                     public.ExecShell("\cp -arf {}/* {}/".format(src_path,dst_path))
#                     public.ExecShell("chown -R www:www {}".format(dst_path))
#                     public.ExecShell("chmod -R 700 {}".format(dst_path))
#                     public.ExecShell("rm -rf {}".format(src_path))

#                 if not os.path.exists(dst_path + '/index.php'):
#                     return Resp("adminer文件缺失，请在首页[修复]面板后重试!")

#                 ikey = 'aer_php_version'
#                 self.php_version = cache.get(ikey)
#                 if not self.php_version:
#                     self.php_version = self.get_php_version(None)
#                     cache.set(ikey,self.php_version,10)
#                     if not self.php_version:
#                         return Resp('没有找到可用的PHP版本')
                    

#             #文件是否存在？
#             if not os.path.exists(filename):
#                return abort(404)
            
#             #发送到FPM
#             try:
                
#                 return self.request_php(puri)
#             except Exception as ex:
#                 if str(ex).find('No such file or directory') != -1:
#                     return Resp('指定PHP版本: {}，未启动，或无法连接!'.format(self.php_version))
#                 return Resp(str(ex))

#         if not os.path.exists(filename):
#             return abort(404)
        
#         #如果是静态文件
#         return send_file(filename)

    

    #获取头部32KB数据
    def get_header_data(self,sock):
        '''
            @name 获取头部32KB数据
            @author hwliang<2020-07-11>
            @param sock socketobject(fastcgi套接字对象)
            @return bytes
        '''
        headers_data = b''
        total_len = 0
        header_len = 1024 * 128 
        while True:
            fastcgi_header = sock.recv(8)
            if not fastcgi_header: break
            if len(fastcgi_header) != 8:
                headers_data += fastcgi_header
                break
            fast_pack = struct.unpack(FCGI_Header, fastcgi_header)
            if fast_pack[1] == 3: break
            
            tlen = fast_pack[3]
            while tlen > 0:
                sd = sock.recv(tlen)
                if not sd: break
                headers_data += sd
                tlen -= len(sd)
            
            total_len += fast_pack[3]
            if fast_pack[4]:
                sock.recv(fast_pack[4])
            if total_len > header_len: break
        return headers_data
    
    #格式化响应头
    def format_header_data(self,headers_data):
        '''
            @name 格式化响应头
            @author hwliang<2020-07-11>
            @param headers_data bytes(fastcgi头部32KB数据)
            @return status int(响应状态), headers dict(响应头), bdata bytes(格式化响应头后的多余数据)
        '''
        status = '200 OK'
        headers = {}
        pos = 0
        while True:
            eolpos = headers_data.find(b'\n', pos)
            if eolpos < 0: break
            line = headers_data[pos:eolpos-1]
            pos = eolpos + 1
            line = line.strip()
            if len(line) < 2: break
            if line.find(b':') == -1: continue
            header, value = line.split(b':', 1)
            header = header.strip()
            value = value.strip()
            if isinstance(header,bytes):
                header = header.decode()
                value = value.decode()
            if header == 'Status':
                status = value
                if status.find(' ') < 0:
                    status += ' BTPanel'
            else:
                headers[header] = value
        bdata = headers_data[pos:]
        status = int(status.split(' ')[0])
        return status,headers,bdata

    #以流的方式发送剩余数据
    def resp_sock(self,sock,bdata):
        '''
            @name 以流的方式发送剩余数据
            @author hwliang<2020-07-11>
            @param sock socketobject(fastcgi套接字对象)
            @param bdata bytes(格式化响应头后的多余数据)
            @return yield bytes
        '''
        #发送除响应头以外的多余头部数据
        yield bdata
        while True:
            fastcgi_header = sock.recv(8)
            if not fastcgi_header: break
            if len(fastcgi_header) != 8:
                yield fastcgi_header
                break
            fast_pack = struct.unpack(FCGI_Header, fastcgi_header)
            if fast_pack[1] == 3: break
            tlen = fast_pack[3]
            while tlen > 0:
                sd = sock.recv(tlen)
                if not sd: break
                tlen -= len(sd)
                if sd:
                    yield sd

            if fast_pack[4]:
                sock.recv(fast_pack[4])
        sock.close()




class FPM(object):
    def __init__(self,sock=None, document_root='',last_path = ''):
        '''
            @name 实例化FPM对象
            @author hwliang<2020-07-11>
            @param sock string(unixsocket路径)
            @param document_root string(PHP文档根目录)
            @return FPM
        '''
        if sock:
            self.fcgi_sock = sock
            if document_root[-1:] != '/':
                document_root += '/'
            self.document_root = document_root
            self.last_path = last_path

    def load_url(self, url, content=b''):
        '''
            @name 转发URL到PHP-FPM
            @author hwliang<2020-07-11>
            @param url string(URI地址)
            @param content stream(POST数据io对象)
            @return fastcgi-socket
        '''
        
        fcgi = fcgi_client.FCGIApp(connect=self.fcgi_sock)
        try:
            script_name, query_string = url.split('?')
        except ValueError:
            script_name = url
            query_string = ''
        from BTPanel import request
        env = {
            'SCRIPT_FILENAME': '%s%s' % (self.document_root, script_name),
            'QUERY_STRING': query_string,
            'REQUEST_METHOD': request.method,
            'SCRIPT_NAME': self.last_path + script_name,
            'REQUEST_URI': self.last_path + url,
            'GATEWAY_INTERFACE': 'CGI/1.1',
            'SERVER_SOFTWARE': 'BT-Panel',
            'REDIRECT_STATUS': '200',
            'CONTENT_TYPE': request.headers.get('Content-Type','application/x-www-form-urlencoded'),
            'CONTENT_LENGTH': str(request.headers.get('Content-Length','0')),
            'DOCUMENT_URI': request.path,
            'DOCUMENT_ROOT': self.document_root,
            'SERVER_PROTOCOL' : 'HTTP/1.1',
            'REMOTE_ADDR': request.remote_addr.replace('::ffff:',''),
            'REMOTE_PORT': str(request.environ.get('REMOTE_PORT')),
            'SERVER_ADDR': request.headers.get('host'),
            'SERVER_PORT': '80',
            'SERVER_NAME': 'BT-Panel',
        }
        
        for k in request.headers.keys():
            key = 'HTTP_' + k.replace('-','_').upper()
            env[key] = request.headers[k]
        fpm_sock = fcgi(env, content)
        return fpm_sock

    def load_url_public(self,url,content = b'',method='GET',content_type='application/x-www-form-urlencoded'):
        '''
            @name 转发URL到PHP-FPM 公共
            @author hwliang<2020-07-11>
            @param url string(URI地址)
            @param content stream(POST数据io对象)
            @return fastcgi-socket
        '''
        fcgi = fcgi_client.FCGIApp(connect=self.fcgi_sock)
        try:
            script_name, query_string = url.split('?')
        except ValueError:
            script_name = url
            query_string = ''

        content_length = len(content)
        if content:
            content = StringIO(content)

        env = {
            'SCRIPT_FILENAME': '%s%s' % (self.document_root, script_name),
            'QUERY_STRING': query_string,
            'REQUEST_METHOD': method,
            'SCRIPT_NAME': self.last_path + script_name,
            'REQUEST_URI': url,
            'GATEWAY_INTERFACE': 'CGI/1.1',
            'SERVER_SOFTWARE': 'BT-Panel',
            'REDIRECT_STATUS': '200',
            'CONTENT_TYPE': content_type,
            'CONTENT_LENGTH': str(content_length),
            'DOCUMENT_URI': script_name,
            'DOCUMENT_ROOT': self.document_root,
            'SERVER_PROTOCOL' : 'HTTP/1.1',
            'REMOTE_ADDR': '127.0.0.1',
            'REMOTE_PORT': '8888',
            'SERVER_ADDR': '127.0.0.1',
            'SERVER_PORT': '80',
            'SERVER_NAME': 'BT-Panel'
        }

        fpm_sock = fcgi(env, content)
        _data = b''
        while True:
            fastcgi_header = fpm_sock.recv(8)
            if not fastcgi_header: break
            if len(fastcgi_header) != 8:
                _data += fastcgi_header
                break
            fast_pack = struct.unpack(FCGI_Header, fastcgi_header)
            if fast_pack[1] == 3: break
            tlen = fast_pack[3]
            while tlen > 0:
                sd = fpm_sock.recv(tlen)
                if not sd: break
                tlen -= len(sd)
                _data += sd
            if fast_pack[4]:
                fpm_sock.recv(fast_pack[4])
        status,headers,data = panelPHP().format_header_data(_data)
        return data
