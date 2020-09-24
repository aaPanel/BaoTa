#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2019 宝塔软件(http:#bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
#-------------------------------------------------------------------
import public,os
from BTPanel import request,abort,send_file
_PMD_PATH = '/www/server/phpmyadmin/phpmyadmin_b313c665284f1718/'

import time
import fastcgiClient as fcgi_client
import struct
FCGI_Header = '!BBHHBx'

class FPM(object):
    def __init__(self,sock=None, document_root='/www/server/phpmyadmin/phpmyadmin_b313c665284f1718/'):
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

        env = {
            'SCRIPT_FILENAME': '%s%s' % (self.document_root, script_name),
            'QUERY_STRING': query_string,
            'REQUEST_METHOD': request.method,
            'SCRIPT_NAME': '/phpmyadmin/'+script_name,
            'REQUEST_URI': url,
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

def request_php(uri):
    '''
        @name 发起fastcgi请求到PHP-FPM
        @author hwliang<2020-07-11>
        param puri string(URI地址)
        @return socket
    '''
    f = FPM(sock='/tmp/php-cgi-72.sock')
    if request.full_path.find('?') != -1:
        uri = request.full_path[request.full_path.find(uri):]
    sock = f.load_url(uri,content=request.stream)
    return sock

def start(puri):
    '''
        @name 开始处理PHP请求
        @author hwliang<2020-07-11>
        param puri string(URI地址)
        @return socket or Response
    '''
    if puri in ['/','',None]: puri = '/index.php'
    filename = _PMD_PATH + puri
    if not os.path.exists(filename):
        return abort(404)

    #如果是PHP文件
    if puri[-4:] == '.php':
        return request_php(puri)
    
    #如果是静态文件
    return send_file(filename)



#获取头部32KB数据
def get_header_data(sock):
    '''
        @name 获取头部32KB数据
        @author hwliang<2020-07-11>
        param sock socketobject(fastcgi套接字对象)
        @return bytes
    '''
    headers_data = b''
    total_len = 0
    header_len = 1024 * 32
    while True:
        fastcgi_header = sock.recv(8)
        if not fastcgi_header: break
        if len(fastcgi_header) != 8:
            headers_data += fastcgi_header
            break
        fast_pack = struct.unpack(FCGI_Header, fastcgi_header)
        headers_data += sock.recv(fast_pack[3])
        total_len += fast_pack[3]
        if fast_pack[4]:
            sock.recv(fast_pack[4])
        if total_len > header_len: break
    return headers_data

#格式化响应头
def format_header_data(headers_data):
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
        header, value = line.split(b':', 1)
        header = header.strip()
        value = value.strip()
        if header == 'Status':
            status = value
            if status.find(' ') < 0:
                status += ' BTPanel'
        else:
            headers[header] = value
    bdata = headers_data[pos:]
    headers['Transfer-Encoding'] = 'chunked'
    status = int(status.split(' ')[0])
    return status,headers,bdata

#以流的方式发送剩余数据
def resp_sock(sock,bdata):
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
        data = sock.recv(fast_pack[3])
        if fast_pack[4]:
            sock.recv(fast_pack[4])
        if not data: break
        yield data
    sock.close()