#!/usr/bin/python
#coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# 网站证书过期检测
# -------------------------------------------------------------------

import os,sys,re,public,OpenSSL,time

_title = '网站证书到期检测'
_version = 1.0                              # 版本
_ps = "检测所有已部署安全证书的网站是否过期"    # 描述
_level = 2                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-04'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_site_ssl_expire.pl")
_tips = [
    "请为您的站点续签或更换新的SSL证书，以免影响网站正常访问",
    "SSL证书过期后，用户访问网站将被浏览器提示为不安全，且大部份浏览器会阻止访问，严重影响线上业务"
    ]
_help = ''

def check_run():
    '''
        @name 开始检测
        @author hwliang<2020-08-04>
        @return tuple (status<bool>,msg<string>)
    '''

    site_list = public.M('sites').field('id,name').select()

    not_ssl_list = []
    s_time = time.time()
    for site_info in site_list:
        ng_conf_file = '/www/server/panel/vhost/nginx/' + site_info['name'] + '.conf'
        if not os.path.exists(ng_conf_file): continue
        s_body = public.readFile(ng_conf_file)
        if not s_body: continue
        if s_body.find('ssl_certificate') == -1: continue

        cert_file = '/www/server/panel/vhost/cert/{}/fullchain.pem'.format(site_info['name'])
        if not os.path.exists(cert_file): continue

        cert_timeout = get_cert_timeout(cert_file)
        if s_time > cert_timeout:
            not_ssl_list.append(site_info['name'] + ' 过期时间: ' + public.format_date("%Y-%m-%d",cert_timeout))
        
    if not_ssl_list:
        return False ,'以下站点SSL证书已过期: <br />' + ('<br />'.join(not_ssl_list))
    
    return True,'无风险'
        
        
    
# 获取证书到期时间
def get_cert_timeout(cert_file):
    try:
        cert = split_ca_data(public.readFile(cert_file))
        x509 = OpenSSL.crypto.load_certificate(
            OpenSSL.crypto.FILETYPE_PEM, cert)
        cert_timeout = bytes.decode(x509.get_notAfter())[:-1]
        return int(time.mktime(time.strptime(cert_timeout, '%Y%m%d%H%M%S')))
    except:
        return time.time() + 86400



# 拆分根证书
def split_ca_data(cert):
    datas = cert.split('-----END CERTIFICATE-----')
    return datas[0] + "-----END CERTIFICATE-----\n"
