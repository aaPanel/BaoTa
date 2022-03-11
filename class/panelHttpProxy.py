#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
#-------------------------------------------------------------------

#------------------------------
# HTTP代理模块
#------------------------------

import requests,os,re,time
from BTPanel import request,Response,public,app,get_phpmyadmin_dir,session
from http.cookies import SimpleCookie
import requests.packages.urllib3.util.connection as urllib3_conn
import socket


class HttpProxy:
    _pma_path = None
    def get_res_headers(self,p_res):
        '''
            @name 获取响应头
            @author hwliang<2022-01-19>
            @param p_res<Response> requests响应对像
            @return dict
        '''
        headers = {}
        for h in p_res.headers.keys():
            if h in ['Content-Encoding','Transfer-Encoding']: continue
            headers[h] = p_res.headers[h]
            if h in ['Location']:
                
                if headers[h].find('phpmyadmin_') != -1:
                    if not self._pma_path: 
                        self._pma_path = get_phpmyadmin_dir()
                        if self._pma_path: 
                            self._pma_path = self._pma_path[0]
                        else:
                            self._pma_path = ''
                    headers[h] = headers[h].replace(self._pma_path,'phpmyadmin')

                if headers[h].find('127.0.0.1') != -1:
                    headers[h] = re.sub(r"https?://127.0.0.1(:\d+)?/",request.url_root,headers[h])
                if request.url_root.find('https://') == 0:
                    headers[h] = headers[h].replace('http://','https://')
        return headers

    def set_res_headers(self,res,p_res):
        '''
            @name 设置响应头
            @author hwliang<2022-01-19>
            @param res<Response> flask响应对像
            @param p_res<Response> requests响应对像
            @return res<Response>
        '''
        # from datetime import datetime
        # cookie_dict = p_res.cookies.get_dict()
        # expires = datetime.utcnow() + app.permanent_session_lifetime
        # for k in cookie_dict.keys():
        #     httponly = True
        #     if k in ['phpMyAdmin']: httponly = True
        #     res.set_cookie(k, cookie_dict[k],
        #                         expires=expires, httponly=httponly,
        #                         path='/')
        
        return res

    def get_pma_phpversion(self):
        '''
            @name 获取phpmyadmin的php版本
            @author hwliang<2022-01-19>
            @return str
        '''
        from panelPlugin import panelPlugin
        pma_status = panelPlugin().getPHPMyAdminStatus()
        if 'phpversion' in pma_status:
            return pma_status['phpversion']
        return None

    def get_pma_version(self):
        '''
            @name 获取phpmyadmin的版本
            @author hwliang<2022-01-19>
            @return str
        '''
        pma_vfile = public.get_setup_path() + '/phpmyadmin/version.pl'
        if not os.path.exists(pma_vfile): return ''
        pma_version = public.readFile(pma_vfile).strip()
        if not pma_version: return ''
        return pma_version

    def set_pma_phpversion(self):
        '''
            @name 设置phpmyadmin兼容的php版本
            @author hwliang<2022-01-19>
            @return str
        '''
        
        pma_version = self.get_pma_version()
        if not pma_version: return False

        old_phpversion = self.get_pma_phpversion()
        if not old_phpversion: return False
        if pma_version == '4.0':
            php_versions = ['52','53','54']
        elif pma_version == '4.4':
            php_versions = ['54','55','56']
        elif pma_version == '4.9':
            php_versions = ['55','56','70','71','72','73','74']
        elif pma_version == '5.0':
            php_versions = ['70','71','72','73','74']
        elif pma_version == '5.1':
            php_versions = ['71','72','73','74','80']
        elif pma_version == '5.2':
            php_versions = ['72','73','74','80','81']
        elif pma_version == '5.3':
            php_versions = ['72','73','74','80','81']
        else:
            return False

        if old_phpversion in php_versions: return True

        installed_php_versions = []
        php_install_path = '/www/server/php'
        for version in php_versions:
            php_bin = php_install_path + '/' + version + '/bin/php'
            if os.path.exists(php_bin):
                installed_php_versions.append(version)
        
        if not installed_php_versions: return False

        php_version = installed_php_versions[-1]
        
        import ajax
        args = public.dict_obj()
        args.phpversion = php_version
        ajax.ajax().setPHPMyAdmin(args)
        public.WriteLog('数据库','检测到phpMyAdmin使用的PHP版本不兼容，已自动修改为最佳兼容版本: PHP-' + php_version)
        time.sleep(0.5)
        

    def get_request_headers(self):
        '''
            @name 获取请求头
            @author hwliang<2022-01-19>
            @return dict
        '''
        headers = {}
        rm_cookies = [app.config['SESSION_COOKIE_NAME'],'bt_user_info','file_recycle_status','ltd_end',
        'memSize','page_number','pro_end','request_token','serverType','site_model',
        'sites_path','soft_remarks','load_page','Path','distribution','order']
        for k in request.headers.keys():
            headers[k] = request.headers.get(k)
            if k == 'Cookie':
                cookie_dict = SimpleCookie(headers[k])
                for rm_cookie in rm_cookies:
                    if rm_cookie in cookie_dict:
                        del(cookie_dict[rm_cookie])
                headers[k] = cookie_dict.output(header='',sep=';').strip()
        return headers

    def form_to_dict(self,form):
        '''
            @name 将表单转为字典
            @author hwliang<2022-02-18>
            @param form<request.form> 表单数据
            @return dict
        '''

        data = {}
        for k in form.keys():
            data[k] = form.getlist(k)
            if len(data[k]) == 1: data[k] = data[k][0]
        return data
        
    def proxy(self,proxy_url):
        '''
            @name 代理指定URL地址
            @author hwliang<2022-01-19>
            @param proxy_url<string> 被代理的URL地址
            @return Response
        '''
        try:
            urllib3_conn.allowed_gai_family = lambda: socket.AF_INET
            s_key = 'proxy_{}_{}'.format(app.secret_key,self.get_pma_version())

            if not s_key in session:
                session[s_key] = requests.Session()
                session[s_key].keep_alive = False
                session[s_key].headers = {
                    'User-Agent':'BT-Panel',
                    'Connection':'close'
                }
                try:
                    session[s_key].headers['Host'] = public.en_punycode(request.url_root).replace('http://','').replace('https://','').split('/')[0]
                except:pass
                if proxy_url.find('phpmyadmin') != -1:
                    if proxy_url.find('https://') == 0:
                        session[s_key].cookies.update({'pma_lang_https':'zh_CN'})
                    else:
                        session[s_key].cookies.update({'pma_lang':'zh_CN'})
                    self.set_pma_phpversion()
                
            if 'Authorization' in request.headers:
                session[s_key].headers['Authorization'] = request.headers['Authorization']
            # headers = self.get_request_headers()
            headers = None
            if request.method == 'GET':
                # 转发GET请求
                p_res = session[s_key].get(proxy_url,headers=headers,verify=False,allow_redirects=False)
            elif request.method == 'POST':
                # 转发POST请求
                if request.files: # 如果上传文件
                    tmp_path = '{}/tmp'.format(public.get_panel_path())
                    if not os.path.exists(tmp_path): os.makedirs(tmp_path,384)
    
                    # 处理请求头
                    if headers:
                        if 'Content-Type' in headers: del(headers['Content-Type'])
                        if 'Content-Length' in headers: del(headers['Content-Length'])
    
                    # 遍历form表单中的所有文件
                    files = {}
                    f_list = {}
                    for key in request.files:
                        upload_files = request.files.getlist(key)
                        filename = upload_files[0].filename
                        if not filename: filename = public.GetRandomString(12)
                        tmp_file = '{}/{}'.format(tmp_path,filename)
                        
                        
                        # 保存上传文件到临时目录
                        with open(tmp_file,'wb') as f:
                            for tmp_f in upload_files:
                                f.write(tmp_f.read())
                            f.close()
    
                        # 构造文件上传对象
                        f_list[key] = open(tmp_file,'rb')
                        files[key] = (filename, f_list[key])
    
                        # 删除临时文件
                        if os.path.exists(tmp_file): os.remove(tmp_file)
    
                    # 转发上传请求
                    
                    p_res = session[s_key].post(proxy_url,self.form_to_dict(request.form),headers=headers,files=files,verify=False,allow_redirects=False)
    
                    # 释放文件对象
                    for fkey in f_list.keys():
                        f_list[fkey].close()
                else:
                    p_res = session[s_key].post(proxy_url,self.form_to_dict(request.form),headers=headers,verify=False,allow_redirects=False)
            else:
                return Response('不支持的请求类型',500)
            
            # PHP版本自动切换处理
            if proxy_url.find('phpmyadmin') != -1 and proxy_url.find('/index.php') != -1:
                if len(p_res.content) < 1024:
                    if p_res.content.find(b'syntax error, unexpected') != -1 or p_res.content.find(b'offset access syntax with') != -1 or p_res.content.find(b'+ is required') != -1:
                        self.set_pma_phpversion()
                        return '不兼容的PHP版本,已尝试自动切换到兼容的PHP版本,请刷新页面重试!'
                elif p_res.content.find(b'<strong>Deprecation Notice</strong>') != -1 and not session.get('set_pma_phpversion'):
                    self.set_pma_phpversion()
                    session['set_pma_phpversion'] = True
                    return '不兼容的PHP版本,已尝试自动切换到兼容的PHP版本,请刷新页面重试!'
            
            res = Response(p_res.content,headers=self.get_res_headers(p_res),content_type=p_res.headers.get('content-type',None),status=p_res.status_code)
            res = self.set_res_headers(res,p_res)
            return res
        except Exception as ex:
            return Response(str(ex),500)