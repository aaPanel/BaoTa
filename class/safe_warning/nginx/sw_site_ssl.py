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
# 网站证书检测
# -------------------------------------------------------------------

import os,sys,re,public

_title = '网站证书(SSL)'
_version = 2.0
_ps = "检测生产环境网站是否部署安全证书"
_level = 1
_date = '2025-01-15'
_ignore = os.path.exists("data/warning/ignore/sw_site_ssl.pl")
_tips = [
    "请考虑为您的生产环境网站部署SSL证书，以提升网站的安全性"
    ]
_help = ''
_remind = 'SSL证书确保了网站通信的安全性，防止数据传输过程中被黑客窃取。'


def is_test_domain(domain):
    """
    判断是否为测试/开发域名
    测试域名特征：
    1. 包含test、dev、staging、demo等关键字
    2. 使用IP地址作为域名
    3. 使用example.com、test.com等示例域名
    4. 使用随机字符串域名（如hhhhh.com、wegweg.com）
    """
    domain_lower = domain.lower().strip()

    # 检查是否为IP地址
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', domain_lower):
        return True

    # 测试/开发域名关键字
    test_keywords = [
        'test', 'testing', 'tests',
        'dev', 'devel', 'development',
        'staging', 'stage',
        'demo', 'demos',
        'example', 'examples',
        'localhost', 'local',
        'temp', 'temporary',
        'lab', 'labs',
        'beta',
        'alpha'
    ]

    # 检查是否包含测试关键字
    for keyword in test_keywords:
        if keyword in domain_lower:
            return True

    # 检查是否为常见的示例域名
    example_domains = [
        'example.com', 'example.org', 'example.net',
        'test.com', 'tests.com',
        'demo.com', 'demos.com'
    ]
    if domain_lower in example_domains:
        return True

    # 检查是否为随机字符串域名（连续重复字符或无意义字符串）
    # 例如：hhhhh.com, wegweg.com, abcabc.com
    if re.match(r'^([a-z])\1{3,}', domain_lower):  # 连续重复字符
        return True
    if re.match(r'^([a-z]{3,})\1+$', domain_lower):  # 重复字符串
        return True

    # 检查域名长度，短于5个字符的可能是测试域名
    if len(domain_lower.split('.')[0]) < 4:
        return True

    return False


def check_run():
    '''
        @name 开始检测
        @author hwliang<2020-08-04>
        @return tuple (status<bool>,msg<string>)
    '''

    site_list = public.M('sites').field('id,name').select()

    not_ssl_list = []
    test_domain_list = []

    for site_info in site_list:
        domain = site_info['name']

        # 跳过测试域名
        if is_test_domain(domain):
            test_domain_list.append(domain)
            continue

        ng_conf_file = '/www/server/panel/vhost/nginx/' + domain + '.conf'
        if not os.path.exists(ng_conf_file): continue
        s_body = public.readFile(ng_conf_file)
        if not s_body: continue
        if s_body.find('ssl_certificate') == -1:
            not_ssl_list.append(domain)

    # 如果有生产环境站点未部署SSL
    if not_ssl_list:
        msg = '以下生产环境站点未部署SSL证书:\n' + '\n'.join(not_ssl_list)
        if test_domain_list:
            msg += '\n\n已跳过测试/开发域名:\n' + '\n'.join(test_domain_list[:5])
            if len(test_domain_list) > 5:
                msg += f' 等{len(test_domain_list)}个测试域名'
        return False, msg

    # 所有生产环境站点都已部署SSL
    return True, '无风险'
