#!/usr/bin/python
#coding: utf-8

import os, re, public


_title = 'tomcat后台访问弱口令检测'
_version = 1.0  # 版本
_ps = "tomcat后台访问弱口令检测"  # 描述
_level = 3  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-13'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_tomcat_pass.pl")
_tips = [
    "在【/usr/local/bttomcat/tomcat/conf/tomcat-users.xml】中修改password弱口令",
]
_help = ''
_remind = '此方案通过加强tomcat后台登录密码强度，降低被爆破的风险，避免被黑客利用tomcat入侵服务器。'


def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    tomcat_conf = '/usr/local/bttomcat/tomcat{}/conf/tomcat-users.xml'
    version = ['7','8','9']
    vul_list = []
    # 第一步先用正则找到密码的输入点
    rep = 'password(\s*)=(\s*)[\"\'](.*?)[\"\']'
    for v in version:
        annotator = 0
        if not os.path.exists(tomcat_conf.format(v)):
            continue
        with open(tomcat_conf.format(v)) as f:
            lines = f.readlines()
            # 通过逐行判断是否存在注释符闭合，以annotator作锁计数，存在左闭合则+1，存在右闭合-1，当annotator值为0时才不在闭合范围内
            for l in lines:
                if '<!--' in l:
                    annotator += 1
                if '-->' in l:
                    annotator -= 1
                if '<!--' in l and '-->' in l:
                    continue
                if annotator != 0:
                    continue
                if 'manager-gui' in l and 'password' in l:
                    tmp = re.search(rep, l.rstrip())
                    passwd = tmp.group(3).strip()
                    for d in get_pass_list():
                        if passwd == d:
                            vul_list.append(v)
    if vul_list:
        return False, 'tomcat{}存在后台弱口令'.format('、'.join(vul_list))
    else:
        return True, '无风险'


# 获取弱口令字典
def get_pass_list():
    pass_info = public.ReadFile("/www/server/panel/config/weak_pass.txt")
    return pass_info.split('\n')
