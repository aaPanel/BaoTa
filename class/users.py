#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http:#bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwliang@bt.cn>
#-------------------------------------------------------------------

#------------------------------
# 面板多用户管理
#------------------------------
import os,sys,json
import time
import public
from BTPanel import session
class users_main:

    #取用户列表
    def get_users(self,args):
        if not 'uid' in session: session['uid'] = 1
        data = public.M('users').field('id,username').select()
        return data

    # 创建新用户
    def create_user(self,args):
        if session['uid'] != 1: return public.returnMsg(False,'没有权限!')
        if len(args.username) < 2: return public.returnMsg(False,'用户名不能少于2位')
        if len(args.password) < 8: return public.returnMsg(False,'密码不能少于8位')
        salt = public.GetRandomString(12)
        pdata = {
            "username": args.username.strip(),
            'salt': salt,
            "password": public.md5(public.md5(public.md5(args.password.strip())+'_bt.cn')+salt)
        }

        if(public.M('users').where('username=?',(pdata['username'],)).count()):
            return public.returnMsg(False,'指定用户名已存在!')

        if(public.M('users').insert(pdata)):
            public.WriteLog('用户管理','创建新用户{}'.format(pdata['username']))
            return public.returnMsg(True,'创建新用户{}成功!'.format(pdata['username']))
        return public.returnMsg(False,'创建新用户失败!')

    # 删除用户
    def remove_user(self,args):
        if session['uid'] != 1: return public.returnMsg(False,'没有权限!')
        if int(args.id) == 1: return public.returnMsg(False,'不能删除初始默认用户!')
        username = public.M('users').where('id=?',(args.id,)).getField('username')
        if not username: return public.returnMsg(False,'指定用户不存在!')
        if(public.M('users').where('id=?',(args.id,)).delete()):
            public.WriteLog('用户管理','删除用户[{}]'.format(username))
            return public.returnMsg(True,'删除用户{}成功!'.format(username))
        return public.returnMsg(False,'用户删除失败!')

    # 修改用户
    def modify_user(self,args):
        if session['uid'] != 1: return public.returnMsg(False,'没有权限!')
        username = public.M('users').where('id=?',(args.id,)).getField('username')
        pdata = {}
        if 'username' in args:
            if len(args.username) < 2: return public.returnMsg(False,'用户名不能少于2位')
            pdata['username'] = args.username.strip()

        if 'password' in args:
            if args.password:
                if len(args.password) < 8: return public.returnMsg(False,'密码不能少于8位')
                pdata['password'] = public.password_salt(public.md5(args.password.strip()),args.id)

        if(public.M('users').where('id=?',(args.id,)).update(pdata)):
            public.WriteLog('用户管理',"编辑用户{}".format(username))
            return public.returnMsg(True,'修改成功!')
        return public.returnMsg(False,'没有提交修改!')

