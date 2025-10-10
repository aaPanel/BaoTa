#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------

# +-------------------------------------------------------------------
# |  宝塔HTTP通信库
# +-------------------------------------------------------------------
import os,sys,re
import ssl

import public
import json
import socket
import requests
import requests.packages.urllib3.util.connection as urllib3_conn
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class http:
    _ip_type = None
    def __init__(self):
        self._ip_type = self.get_request_iptype()


    def get_request_iptype(self, get=None):
        '''
            @name 获取云端请求线路
            @author hwliang<2022-02-09>
            @return auto/ipv4/ipv6
        '''

        v4_file = '{}/data/v4.pl'.format(public.get_panel_path())
        if not os.path.exists(v4_file): return 'auto'
        iptype = public.readFile(v4_file).strip()
        if not iptype: return 'auto'
        if iptype == '-4': return 'ipv4'
        return 'ipv6'

    def get(self,url,timeout = (6,60),headers = {},verify = False,type = 'python'):
        url = self.quote(url)
        url = public.get_home_node(url)
        if type in ['python','src','php']:
            # public.print_log(url)
            # old_family = urllib3_conn.allowed_gai_family
            # if str(old_family.__code__).find("python3.7/site-packages") == -1:
            #     public.print_log("出错了！！！！！", old_family.__code__)
            try:
                # 默认使用IPv4
                if self._ip_type == 'ipv4':
                    urllib3_conn.allowed_gai_family = lambda: socket.AF_INET
                elif self._ip_type == 'ipv6':
                    urllib3_conn.allowed_gai_family = lambda: socket.AF_INET6

                result = requests.get(url,timeout=timeout,headers=get_headers(headers),verify=verify)
            except Exception as ex:
                # 可能使用了错误的family，尝试清除相关配置
                if(str(ex).find('Cannot assign requested address') != -1):
                    v_file = '{}/data/v4.pl'.format(public.get_panel_path())
                    public.writeFile(v_file,'')
                    self._ip_type = 'auto'

                try:
                    # IPV6？
                    if self._ip_type != 'ipv6':
                        urllib3_conn.allowed_gai_family = lambda: socket.AF_INET6
                        result = requests.get(url,timeout=timeout,headers=get_headers(headers),verify=verify)
                    else:
                        urllib3_conn.allowed_gai_family = lambda: socket.AF_INET
                        result = requests.get(url,timeout=timeout,headers=get_headers(headers),verify=verify)
                except:
                    # 使用CURL
                    result = self._get_curl(url,timeout,headers,verify)
            finally:
                public.reset_allowed_gai_family()

        elif type == 'curl':
            result = self._get_curl(url,timeout,headers,verify)
            if result.status_code == 0:
                if self._ip_type == 'ipv4':
                    self._ip_type = 'ipv6'
                elif self._ip_type == 'ipv6':
                    self._ip_type = 'ipv4'
                else:
                    return result
                result = self._get_curl(url,timeout,headers,verify)
                if result.status_code != 0:
                    self.save_ip_type()
        elif type == 'php':
            result = self._get_php(url,timeout,headers,verify)
            if result.status_code == 0:
                if self._ip_type == 'ipv4':
                    self._ip_type = 'ipv6'
                elif self._ip_type == 'ipv6':
                    self._ip_type = 'ipv4'
                else:
                    return result
                result = self._get_php(url,timeout,headers,verify)
                if result.status_code != 0:
                    self.save_ip_type()
        elif type == 'src':
            if sys.version_info[0] == 2:
                result = self._get_py2(url,timeout,headers,verify)
            else:
                result = self._get_py3(url,timeout,headers,verify)
        return result

    def post(self,url,data,timeout = (6,60),headers = {},verify = False,type = 'python'):
        url = self.quote(url)
        url = public.get_home_node(url)
        if type in ['python','src','php']:
            # old_family = urllib3_conn.allowed_gai_family
            # if str(old_family.__code__).find("python3.7/site-packages") == -1:
            #     public.print_log("出错了！！！！！", old_family.__code__)
            try:
                if self._ip_type == 'ipv4':
                    urllib3_conn.allowed_gai_family = lambda: socket.AF_INET
                elif self._ip_type == 'ipv6':
                    urllib3_conn.allowed_gai_family = lambda: socket.AF_INET6

                result = requests.post(url,data,timeout=timeout,headers=headers,verify=verify)
            except:
                try:
                    # IPV6？
                    if self._ip_type != 'ipv6':
                        urllib3_conn.allowed_gai_family = lambda: socket.AF_INET6
                        result = requests.post(url,data,timeout=timeout,headers=headers,verify=verify)
                    else:
                        urllib3_conn.allowed_gai_family = lambda: socket.AF_INET
                        result = requests.post(url,data,timeout=timeout,headers=headers,verify=verify)
                except:
                    # 使用CURL
                    result = self._post_curl(url,data,timeout,headers,verify)
            public.reset_allowed_gai_family()

        elif type == 'curl':
            result = self._post_curl(url,data,timeout,headers,verify)
            if result.status_code == 0:
                if self._ip_type == 'ipv4':
                    self._ip_type = 'ipv6'
                elif self._ip_type == 'ipv6':
                    self._ip_type = 'ipv4'
                else:
                    return result
                result = self._post_curl(url,data,timeout,headers,verify)

                # 保存有效的请求IP类型
                if result.status_code != 0:
                    self.save_ip_type()
        elif type == 'php':
            result = self._post_php(url,data,timeout,headers,verify)
            if result.status_code == 0:
                if self._ip_type == 'ipv4':
                    self._ip_type = 'ipv6'
                elif self._ip_type == 'ipv6':
                    self._ip_type = 'ipv4'
                else:
                    return result
                result = self._post_php(url,data,timeout,headers,verify)
                if result.status_code != 0:
                    self.save_ip_type()
        elif type == 'src':
            if sys.version_info[0] == 2:
                result = self._post_py2(url,data,timeout,headers,verify)
            else:
                result = self._post_py3(url,data,timeout,headers,verify)
        return result



    def node_check(self,url,timeout = (6,60),headers = {},verify = False,type = 'python'):
        """
        @name 检测节点是否可用
        """
        url = self.quote(url)
        url = public.get_home_node(url)
        if type in ['python','src','php']:
            # old_family = urllib3_conn.allowed_gai_family
            try:
                # 默认使用IPv4
                if self._ip_type == 'ipv4':
                    urllib3_conn.allowed_gai_family = lambda: socket.AF_INET
                elif self._ip_type == 'ipv6':
                    urllib3_conn.allowed_gai_family = lambda: socket.AF_INET6

                result = requests.get(url,timeout=timeout,headers=get_headers(headers),verify=verify)
            except Exception as ex:
                result = False
            finally:
                public.reset_allowed_gai_family()

        elif type == 'curl':
            result = self._get_curl(url,timeout,headers,verify)
            if result.status_code == 0:
                if self._ip_type == 'ipv4':
                    self._ip_type = 'ipv6'
                elif self._ip_type == 'ipv6':
                    self._ip_type = 'ipv4'
                else:
                    return result
                result = self._get_curl(url,timeout,headers,verify)
                if result.status_code != 0:
                    self.save_ip_type()
        elif type == 'php':
            result = self._get_php(url,timeout,headers,verify)
            if result.status_code == 0:
                if self._ip_type == 'ipv4':
                    self._ip_type = 'ipv6'
                elif self._ip_type == 'ipv6':
                    self._ip_type = 'ipv4'
                else:
                    return result
                result = self._get_php(url,timeout,headers,verify)
                if result.status_code != 0:
                    self.save_ip_type()
        elif type == 'src':
            if sys.version_info[0] == 2:
                result = self._get_py2(url,timeout,headers,verify)
            else:
                result = self._get_py3(url,timeout,headers,verify)
        return result

    def save_ip_type(self):
        v_file = '{}/data/v4.pl'.format(public.get_panel_path())
        v_body = 'auto'
        if self._ip_type == 'ipv4':
            v_body = '-4'
        elif self._ip_type == 'ipv6':
            v_body = '-6'
        public.writeFile(v_file,v_body)


    def download_file(self,url,filename,data = None,timeout = 1800,speed_file='/dev/shm/download_speed.pl'):
        '''
            @name 下载文件
            @author hwliang<2021-07-08>
            @param url<string> 下载地址
            @param filename<string> 保存路径
            @param data<dict> POST参数，不传则使用GET方法，否则使用POST方法
            @param timeout<int> 超时时间,默认1800秒
            @param speed_file<string>
        '''
        import requests
        from requests.packages.urllib3.exceptions import InsecureRequestWarning
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        headers = public.get_requests_headers()
        if data is None:
            res = requests.get(url,headers=headers,timeout=timeout,stream=True)
        else:
            res = requests.post(url,data,headers=headers,timeout=timeout,stream=True)
        with open(filename,"wb") as f:
            for _chunk in res.iter_content(chunk_size=8192):
                f.write(_chunk)


    #POST请求 Python2
    def _post_py2(self,url,data,timeout,headers,verify):
        import urllib2
        req = urllib2.Request(url, self._str_py_post(data,headers),headers = headers)
        try:
            if not verify:
                context = ssl._create_unverified_context()
                r_response = urllib2.urlopen(req,timeout = timeout,context = context)
            else:
                r_response = urllib2.urlopen(req,timeout = timeout)
        except urllib2.HTTPError as err:
            return response(str(err),err.code,[])
        except urllib2.URLError as err:
            return response(str(err),0,[])
        return response(r_response.read(),r_response.getcode(),r_response.info().headers)

    #POST请求 Python3
    def _post_py3(self,url,data,timeout,headers,verify):
        import urllib.request
        req = urllib.request.Request(url, self._str_py_post(data,headers),headers = headers)
        try:
            if not verify:
                context = ssl._create_unverified_context()
                r_response = urllib.request.urlopen(req,timeout = timeout,context = context)
            else:
                r_response = urllib.request.urlopen(req,timeout = timeout)
        except urllib.error.HTTPError as err:
            return response(str(err),err.code,[])
        except urllib.error.URLError as err:
            return response(str(err),0,[])
        r_body = r_response.read()
        if type(r_body) == bytes: r_body = r_body.decode('utf-8')
        return response(r_body,r_response.getcode(),r_response.getheaders())

    #POST请求，通过CURL
    def _post_curl(self,url,data,timeout,headers,verify):
        if isinstance(timeout,tuple):
            timeout = timeout[1]
        headers_str = self._str_headers(headers)
        pdata = self._str_post(data,headers_str)
        _ssl_verify = ''
        if not verify: _ssl_verify = ' -k'
        result = public.ExecShell("{} -X POST -sS -i --connect-timeout {} {} {} '{}' 2>&1".format(self._curl_bin() + _ssl_verify,timeout,headers_str,pdata,url))[0]
        r_body,r_headers,r_status_code = self._curl_format(result)
        return response(r_body,r_status_code,r_headers)

    #POST请求，通过PHP
    def _post_php(self,url,data,timeout,headers,verify):
        if isinstance(timeout,tuple):
            timeout = timeout[1]
        php_version = self._get_php_version()
        if not php_version:
            raise Exception('没有可用的PHP版本!')
        ip_type = ''
        if self._ip_type == 'ipv6':
            ip_type = 'curl_setopt($ch, CURLOPT_IPRESOLVE, CURL_IPRESOLVE_V6);'
        elif self._ip_type == 'ipv4':
            ip_type = 'curl_setopt($ch, CURLOPT_IPRESOLVE, CURL_IPRESOLVE_V4);'
        tmp_file = '/dev/shm/http.php'
        http_php = '''<?php
error_reporting(E_ERROR);
if(isset($_POST['data'])){{
    $data = json_decode($_POST['data'],1);
}}else{{
    $s = getopt('',array('post:'));
    $data = json_decode($s['post'],1);
}}
$url  = $data['url'];
$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $url);
curl_setopt($ch, CURLOPT_HTTPHEADER,$data['headers']);
curl_setopt($ch, CURLOPT_HEADER, true);
curl_setopt($ch, CURLINFO_HEADER_OUT, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, $data['data']);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, $data['verify']);
curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, $data['verify']);
curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, $data['timeout']);
curl_setopt($ch, CURLOPT_TIMEOUT, $data['timeout']);
{ip_type}
$result = curl_exec($ch);
$h_size = curl_getinfo($ch, CURLINFO_HEADER_SIZE);
$header = substr($result, 0, $h_size);
$body = substr($result,$h_size,strlen($result));
curl_close($ch);
exit($header."\r\n\r\n".json_encode($body));
?>'''.format(ip_type = ip_type)
        public.writeFile(tmp_file,http_php)
        #if 'Content-Type' in headers:
        #    if headers['Content-Type'].find('application/json') != -1:
        #        data = json.dumps(pdata)

        data = json.dumps({"url":url,"timeout":timeout,"verify":verify,"headers":self._php_headers(headers),"data":data})
        if php_version in ['53']:
            php_version = '/www/server/php/' + php_version + '/bin/php'
        if php_version.find('/www/server/php') != -1:
            result = public.ExecShell(php_version + ' ' + tmp_file + " --post='" + data + "'" )[0]
        else:
            result = public.request_php(php_version,'/http.php','/dev/shm','POST',{"data":data})
            if isinstance(result,bytes): result = result.decode('utf-8')

        if os.path.exists(tmp_file): os.remove(tmp_file)
        r_body,r_headers,r_status_code = self._curl_format(result)
        return response(json.loads(r_body),r_status_code,r_headers)


    #GET请求 Python2
    def _get_py2(self,url,timeout,headers,verify):
        import urllib2
        req = urllib2.Request(url, headers = headers)
        try:
            if not verify:
                context = ssl._create_unverified_context()
                r_response = urllib2.urlopen(req,timeout = timeout,context = context)
            else:
                r_response = urllib2.urlopen(req,timeout = timeout)
        except urllib2.HTTPError as err:
            return response(str(err),err.code,[])
        except urllib2.URLError as err:
            return response(str(err),0,[])
        return response(r_response.read(),r_response.getcode(),r_response.info().headers)

    #URL转码
    def quote(self,url):
        if url.find('[') == -1: return url
        url_tmp = url.split('?')
        if len(url_tmp) == 1: return url
        url_last = url_tmp[0]
        url_args = '?'.join(url_tmp[1:])
        if sys.version_info[0] == 2:
            import urllib2
            url_args = urllib2.quote(url_args)
        else:
            import urllib.parse
            url_args = urllib.parse.quote(url_args)
        return url_last + '?' + url_args

    #GET请求 Python3
    def _get_py3(self,url,timeout,headers,verify):
        import urllib.request
        req = urllib.request.Request(url,headers = headers)
        try:
            if not verify:
                context = ssl._create_unverified_context()
                r_response = urllib.request.urlopen(req,timeout = timeout,context = context)
            else:
                r_response = urllib.request.urlopen(req,timeout = timeout)
        except urllib.error.HTTPError as err:
            return response(str(err),err.code,[])
        except urllib.error.URLError as err:
            return response(str(err),0,[])
        r_body = r_response.read()
        if type(r_body) == bytes: r_body = r_body.decode('utf-8')
        return response(r_body,r_response.getcode(),r_response.getheaders())

    #GET请求，通过CURL
    def _get_curl(self,url,timeout,headers,verify):
        if isinstance(timeout,tuple):
            timeout = timeout[1]
        headers_str = self._str_headers(headers)
        _ssl_verify = ''
        if not verify: _ssl_verify = ' -k'
        result = public.ExecShell("{} -sS -i --connect-timeout {} {} {} 2>&1".format(self._curl_bin() + ' ' +  str(_ssl_verify),timeout,headers_str,url))[0]
        r_body,r_headers,r_status_code = self._curl_format(result)
        return response(r_body,r_status_code,r_headers)

    #GET请求，通过PHP
    def _get_php(self,url,timeout,headers,verify):
        if isinstance(timeout,tuple):
            timeout = timeout[1]
        php_version = self._get_php_version()
        if not php_version:
            raise Exception('没有可用的PHP版本!')

        ip_type = ''
        if self._ip_type == 'ipv6':
            ip_type = 'curl_setopt($ch, CURLOPT_IPRESOLVE, CURL_IPRESOLVE_V6);'
        elif self._ip_type == 'ipv4':
            ip_type = 'curl_setopt($ch, CURLOPT_IPRESOLVE, CURL_IPRESOLVE_V4);'
        tmp_file = '/dev/shm/http.php'
        http_php = '''<?php
error_reporting(E_ERROR);
if(isset($_POST['data'])){{
    $data = json_decode($_POST['data'],1);
}}else{{
    $s = getopt('',array('post:'));
    $data = json_decode($s['post'],1);
}}
$url  = $data['url'];
$ch = curl_init();
$user_agent = "BT-Panel";
curl_setopt($ch, CURLOPT_URL, $url);
curl_setopt($ch, CURLOPT_HTTPHEADER,$data['headers']);
curl_setopt($ch, CURLOPT_HEADER, true);
curl_setopt($ch, CURLINFO_HEADER_OUT, TRUE);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, $data['verify']);
curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, $data['verify']);
curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, $data['timeout']);
curl_setopt($ch, CURLOPT_TIMEOUT, $data['timeout']);
{ip_type}
curl_setopt($ch, CURLOPT_POST, false);
$result = curl_exec($ch);
$h_size = curl_getinfo($ch, CURLINFO_HEADER_SIZE);
$header = substr($result, 0, $h_size);
$body = substr($result,$h_size,strlen($result));
curl_close($ch);
exit($header."\r\n\r\n".json_encode($body));
?>'''.format(ip_type=ip_type)

        public.writeFile(tmp_file,http_php)
        data = json.dumps({"url":url,"timeout":timeout,"verify":verify,"headers":self._php_headers(headers)})
        if php_version in ['53']:
            php_version = '/www/server/php/' + php_version + '/bin/php'
        if php_version.find('/www/server/php') != -1:
            result = public.ExecShell(php_version + ' ' + tmp_file + " --post='" + data + "'" )[0]
        else:
            result = public.request_php(php_version,'/http.php','/dev/shm','POST',{"data":data})
            if isinstance(result,bytes): result = result.decode('utf-8')

        if os.path.exists(tmp_file): os.remove(tmp_file)
        r_body,r_headers,r_status_code = self._curl_format(result)
        return response(json.loads(r_body).strip(),r_status_code,r_headers)



    #取可用的PHP版本
    def _get_php_version(self):
        php_versions = public.get_php_versions()
        php_versions = sorted(php_versions,reverse=True)
        php_path = '/www/server/php/{}/sbin/php-fpm'
        php_sock = '/tmp/php-cgi-{}.sock'
        for pv in php_versions:
            if not os.path.exists(php_path.format(pv)): continue
            if not os.path.exists(php_sock.format(pv)): continue
            return pv
        php_bin = '/www/server/php/{}/bin/php'
        for pv in php_versions:
            pb = php_bin.format(pv)
            if not os.path.exists(pb): continue
            return pb
        return None

    #取CURL路径
    def _curl_bin(self):
        c_bin = ['/usr/local/curl2/bin/curl','/usr/local/curl/bin/curl','/usr/local/bin/curl','/usr/bin/curl']
        curl_bin = 'curl'
        for cb in c_bin:
            if os.path.exists(cb): curl_bin = cb
        if self._ip_type != 'auto':
            v4_file = '{}/data/v4.pl'.format(public.get_panel_path())
            v4_body = public.readFile(v4_file).strip()
            if not self._ip_type in v4_body:
                if self._ip_type == 'ipv4':
                    v4_body = '-4'
                else:
                    v4_body = '-6'
            curl_bin += ' {}'.format(v4_body)
        return curl_bin

    #格式化CURL响应头
    def _curl_format(self,req):
        match = re.search("(.|\n)+\r\n\r\n",req)
        if not match: return req,{},0
        tmp = match.group()
        body = req.replace(tmp,'')
        try:
            for line in tmp.split('\r\n'):
                if line.find('HTTP/') != -1:
                    if line.find('Continue') != -1: continue
                    status_code = int(re.search('HTTP/[\d\.]+\s(\d+)',line).groups()[0])
                    break
            if status_code == 100:
                status_code = 200
        except:
            if body:
                status_code = 200
            else:
                status_code = 0
        return body,tmp,status_code

    #构造适用于PHP的headers
    def _php_headers(self,headers):
        php_headers = []
        for h in headers.keys():
            php_headers.append('{}: {}'.format(h,headers[h]))
        return php_headers

    #构造适用于CURL的headers
    def _str_headers(self,headers):
        str_headers = ''
        for key in headers.keys():
            str_headers += " -H '{}: {}'".format(key,headers[key])
        return str_headers

    #构造适用于CURL的post参数
    def _str_post(self,pdata,headers):
        str_pdata = ''
        if headers.find('application/jose') != -1 \
            or headers.find('application/josn') != -1:
            if type(pdata) == dict:
                pdata = json.dumps(pdata)
            if type(pdata) == bytes:
                pdata = pdata.decode('utf-8')
            str_pdata += " -d '{}'".format(pdata)
            return str_pdata

        for key in pdata.keys():
            str_pdata += " -F '{}={}'".format(key ,pdata[key])
        return str_pdata

    #构造适用于python的post参数
    def _str_py_post(self,pdata,headers):
        if 'Content-Type' in headers:
            if headers['Content-Type'].find('application/jose') != -1 \
               or headers['Content-Type'].find('application/josn') != -1:
                if type(pdata) == dict:
                    pdata = json.dumps(pdata)
                if type(pdata) == str:
                    pdata = pdata.encode('utf-8')
                return pdata
        return public.url_encode(pdata)


#响应头对象
class http_headers:
    def __contains__(self, key):
        return getattr(self,key.lower(),None)
    def __setitem__(self, key, value): setattr(self,key.lower(),value)
    def __getitem__(self, key): return getattr(self,key.lower(),None)
    def __delitem__(self,key): delattr(self,key.lower())
    def __delattr__(self, key): delattr(self,key.lower())
    def get(self,key): return getattr(self,key.lower(),None)
    def get_items(self): return self

#响应对象
class response:
    status_code = None
    status = None
    code = None
    headers = {}
    text = None
    content = None
    def __init__(self,body,status_code,headers):
        self.text = body
        self.content = body
        self.status_code = status_code
        self.status = status_code
        self.code = status_code
        self.headers = http_headers()
        self.format_headers(headers)

    def format_headers(self,raw_headers):
        if isinstance(raw_headers,str):
            raw_headers = raw_headers.strip().split('\r\n')
        if isinstance(raw_headers,dict):
            for k in raw_headers.keys():
                self.headers[k] = raw_headers[k]
            return
        raw = []
        for h in raw_headers:
            if not h: continue
            if type(h) == tuple:
                raw.append(h[0] + ': ' + h[1])
                if len(h) < 2: continue
                self.headers[h[0]] = h[1].strip()
            else:
                raw.append(h.strip())
                tmp = h.split(': ')
                if len(tmp) < 2: continue
                self.headers[tmp[0]] = tmp[1].strip()
        self.headers.raw = '\r\n'.join(raw)

    def close(self):
        self.text = None
        self.content = None
        self.status_code = None
        self.status = None
        self.code = None
        self.headers = None

    #取格式化JSON响应
    def json(self):
        try:
            return json.loads(self.text)
        except:
            return self.text

DEFAULT_HEADERS = {"Content-type":"application/x-www-form-urlencoded","User-Agent":"BT-Panel"}
s_types = ['python','php','curl','src']
DEFAULT_TYPE = 'python'
__version__ = 1.0

#请请求方法
def get_stype(s_type):
    if not s_type:
        s_type_file = '/www/server/panel/data/http_type.pl'
        if os.path.exists(s_type_file):
            tmp_type = public.readFile(s_type_file)
            if tmp_type:
                tmp_type = tmp_type.strip().lower()
                if tmp_type in s_types: s_type = tmp_type
    else:
        s_type = s_type.lower()
        if not s_type in s_types: s_type = DEFAULT_TYPE
    if not s_type: s_type = DEFAULT_TYPE
    return s_type

#获取请求头
def get_headers(headers):
    if type(headers) != dict: headers = {}
    #if not 'Content-type' in headers:
    #    headers['Content-type'] = DEFAULT_HEADERS['Content-type']
    if not 'User-Agent' in headers:
        headers['User-Agent'] = DEFAULT_HEADERS['User-Agent']
    return headers

def post(url,data = {},timeout = (15,120),headers = {},verify = False,s_type = None):
    '''
        POST请求
        @param [url] string URL地址
        @parma [data] dict POST参数
        @param [timeout] int 超时时间 默认60秒
        @param [headers] dict 请求头 默认{"Content-type":"application/x-www-form-urlencoded","User-Agent":"BT-Panel"}
        @param [verify] bool 是否验证ssl证书 默认False
        @param [s_type] string 请求方法 默认python 可选：curl或php
    '''
    if isinstance(timeout,list):
        timeout = tuple(timeout)
    p = http()
    try:
        return p.post(url,data,timeout,get_headers(headers),verify,get_stype(s_type))
    except:
        raise Exception(public.get_error_info())

def get(url,timeout = (15,120),headers = {},verify = False,s_type = None):
    '''
        GET请求
        @param [url] string URL地址
        @param [timeout] int 超时时间 默认60秒
        @param [headers] dict 请求头 默认{"Content-type":"application/x-www-form-urlencoded","User-Agent":"BT-Panel"}
        @param [verify] bool 是否验证ssl证书 默认False
        @param [s_type] string 请求方法 默认python 可选：curl或php
    '''
    if isinstance(timeout,list):
        timeout = tuple(timeout)
    p = http()
    try:
        return p.get(url,timeout,get_headers(headers),verify,get_stype(s_type))
    except:
        raise Exception(public.get_error_info())



def node_check(url,timeout = (15,120),headers = {},verify = False,s_type = None):
    '''
        GET请求
        @param [url] string URL地址
        @param [timeout] int 超时时间 默认60秒
        @param [headers] dict 请求头 默认{"Content-type":"application/x-www-form-urlencoded","User-Agent":"BT-Panel"}
        @param [verify] bool 是否验证ssl证书 默认False
        @param [s_type] string 请求方法 默认python 可选：curl或php
    '''
    if isinstance(timeout,list):
        timeout = tuple(timeout)
    p = http()
    try:
        return p.node_check(url,timeout,get_headers(headers),verify,get_stype(s_type))
    except:
        raise Exception(public.get_error_info())

