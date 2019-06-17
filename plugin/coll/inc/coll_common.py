#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------


#+--------------------------------------------------------------------
#|   微架构 - 权限控制
#+--------------------------------------------------------------------
import sys,os,public,time,json
from inc.coll_db import M,write_log
from BTPanel import session, redirect

class coll_common:
    __uid = None
    __nodes = None
    def __init__(self):
        pass

    #校验权限
    def check_access(self,args):
        c = args.c
        f = args.f
        if not 'coll_uid' in session: return redirect('login.html')
        if not self.__uid: self.__uid = session['coll_uid']

        if not 'coll_rules' in session:
            session.coll_rules = self.init_coll()
        r_acc = self.get_access(c,f)
        if r_acc < 1: return r_acc
        return '权限验证通过'
        #return session.coll_rules


    #取当前请求权限
    def get_access(self,c,f):
        if not c in session.coll_rules['module']: return -1
        if not f in session.coll_rules['fun']: return -2
        if session.coll_rules['module'][c]['nid'] != session.coll_rules['fun'][f]['p_nid']: return -3
        unr = M('user_node_realtion')
        if unr.where('uid=? AND (nid=? OR nid=?)',(self.__uid,session.coll_rules['module'][c]['nid'],session.coll_rules['fun'][f]['nid'])).count() < 2: return -4
        return 1

    #初始化控制单元
    def init_coll(self):
        nodes = M('nodes').field('nid,p_nid,level,name').select()
        tmp_nodes = {}
        tmp_nodes['module'] = {}
        tmp_nodes['fun'] = {}
        for node in nodes:
            t_type = 'module'
            if node['level'] != 1:  t_type = 'fun'
            t_name = node['name']
            del(node['name'])
            tmp_nodes[t_type][t_name] = node
        self.__nodes = tmp_nodes
        return tmp_nodes

    #获取服务器列表
    def get_server_list(self):
        data = M('server_list').where('uid=?',(self.__uid,)).field('sid,gid,address,config,panel,token,state,ps,area,addtime').select()
        return data


    #检查是否登录
    def is_login(self):
        if 'coll_login' in session:
            return session['coll_login']
        return False
    