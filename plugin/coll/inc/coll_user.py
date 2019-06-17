#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 6.x
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   微架构 - 用户管理
#+--------------------------------------------------------------------
import re,sys,os,public,time,json
from inc.coll_db import M,write_log
from BTPanel import session, redirect,cache

class coll_user:
    __users_field = 'uid,username,last_login,login_num,last_login_time,state,addtime,ps'
    __nodes_field = 'nid,p_nid,name,title,level,state,sort,ps'
    __uid = None
    def __init__(self):
        if 'coll_uid' in session:
            self.__uid = session['coll_uid']

    #取用户列表
    def get_user_list(self,args):
        data = {}
        user = M('users')
        #count = user.count()
        #if not hasattr(args,'p'): args.p = 1
        #if not hasattr(args,'collback'): args.collback = ''
        #my_page = public.get_page(count,int(args.p),15,args.collback)
        #data['page'] = my_page['page']
        data =  user.field(self.__users_field).order('uid asc').select()
        return data

    #取一条用户信息
    def get_user_find(self,args):
        uid = int(args.uid)
        data =  M('users').where('uid=?',(uid,)).field(self.__users_field).select()
        return data

    #添加用户
    def create_user(self,args):
        pdata = {}
        pdata['username'] = args.username.strip()
        pdata['salt'] = public.GetRandomString(12)
        #密码加密
        pdata['password'] = public.md5(public.md5(pdata['salt'] + args.password.strip()) + pdata['salt'])
        pdata['state'] = 1
        pdata['addtime'] = int(time.time())
        pdata['login_num'] = 0
        pdata['ps'] = args.ps

        #输入校验
        rep = '^[\w\u4e00-\u9fa5-\.]+$'
        if not re.match(rep,pdata['username']): return public.returnMsg(False,'用户名格式不合法 >> %s' % rep)
        if len(args.password) < 6: return public.returnMsg(False,'密码长度不能少于6位')
        if M('users').where('username=?',(pdata['username'],)).count() > 0: return public.returnMsg(False,'指定用户名已存在!')

        #插入数据
        M('users').insert(pdata)
        write_log('用户管理','添加用户[%s]' % pdata['username'])
        return public.returnMsg(True,'用户添加成功!')

    #编辑用户
    def modify_user(self,args):
        pdata = {}
        uid = int(args.uid)
        username = M('users').where('uid=?',(uid,)).getField('username')
        if not username: return public.returnMsg(False,'指定用户不存在!')
        if 'username' in args:
            pdata['username'] = args.username.strip()
        if 'password' in args:
            pdata['salt'] = public.GetRandomString(12)
            pdata['password'] = public.md5(public.md5(pdata['salt'] + args.password.strip()) + pdata['salt'])
        if 'state'in args:
            pdata['state'] = args.state
        if 'ps' in args:
            pdata['ps'] = args.ps

        if not pdata: return public.returnMsg(False,'参数错误!')
        M('users').where('uid=?',(uid,)).update(pdata)
        write_log('用户管理','编辑用户[%s]' % username)
        return public.returnMsg(True,'用户编辑成功!')

    #删除用户
    def remove_user(self,args):
        uid = int(args.uid)
        username =  M('users').where('uid=?',(uid,)).getField('username')
        M('users').where('uid=?',(uid,)).delete()
        write_log('用户管理','删除用户[%s]' % username)
        return public.returnMsg(True,'删除成功!')

    #修改密码
    def modify_password(self,args):
        if not 'coll_uid' in session: return public.returnMsg(False,'请先登录!')
        args.uid = session.coll_uid
        return self.modify_user(args)

    #设置用户状态
    def set_user_stat(self,args):
        return self.modify_user(args)
        
    #设置用户权限
    def set_user_rule(self,args):
        uid = int(args.uid)
        nodes = json.loads(args.nodes)
        if not nodes: return public.returnMsg(False,'无效的用户权限!')
        mydb = M('user_node_realtion')
        mydb.where('uid=?',(uid,)).delete()
        for nid in nodes:
            mydb.addAll('uid,nid',(uid,nid))
        mydb.commit()
        username =  M('users').where('uid=?',(uid,)).getField('username')
        write_log('用户管理','设置用户权限[%s]' % username)
        return public.returnMsg(True,'权限已保存!')

    #添加节点
    def add_node(self,args):
        pdata = {}
        pdata['name'] = args.name.strip()
        pdata['title'] = args.title.strip()
        pdata['level'] = int(args.level)
        pdata['sort'] = float(args.sort)
        pdata['p_nid'] = int(args.p_nid)
        pdata['ps'] = args.ps
        pdata['state'] = 1
        if M('nodes').where('name=? AND level=?',(pdata['name'],pdata['level'])).count(): return public.returnMsg(False,'指定节点已存在')
        M('nodes').insert(pdata)
        write_log('用户管理','添加权限节点[%s][%s]' % (pdata['name'],pdata['title']))
        return public.returnMsg(True,'添加成功!')


    #编辑节点
    def modify_node(self,args):
        nid = int(args.nid)
        pdata = {}
        pdata['name'] = args.name.strip()
        pdata['title'] = args.title.strip()
        pdata['level'] = int(args.level)
        pdata['sort'] = float(args.sort)
        pdata['p_nid'] = int(args.p_nid)
        pdata['state'] = int(args.state)
        pdata['ps'] = args.ps
        if M('nodes').where('name=? AND level=? AND nid!=?',(pdata['name'],pdata['level'],nid)).count(): return public.returnMsg(False,'已存在重名节点')
        M('nodes').where('nid=?',(nid,)).update(pdata)
        write_log('用户管理','编辑权限节点[%s][%s]' % (pdata['name'],pdata['title']))
        return public.returnMsg(True,'编辑成功!')

    #删除节点
    def remove_node(self,args):
        nid = int(args.nid)
        pdata = M('nodes').where('nid=?',(nid,)).field('name,title').find()
        if not pdata: return public.returnMsg(False,'指定节点不存在')
        M('nodes').where('nid=?',(nid,)).delete()
        M('user_node_realtion').where('nid=?',(nid,)).delete()
        write_log('用户管理','删除权限节点[%s][%s]' % (pdata['name'],pdata['title']))
        return public.returnMsg(True,'删除成功!')

    #取所有父节点
    def get_last_nodes(self,args):
        data = M('nodes').where('level=?',(1,)).field(self.__nodes_field).order('sort asc').select()
        return data

    #取所有节点
    def get_nodes(self,args):
        data = M('nodes').field(self.__nodes_field).order('sort asc').select()
        return self.format_nodes(data)

    #整理节点
    def format_nodes(self,nodes):
        data = []
        sql = M('user_node_realtion')
        for node in nodes:
            tmp = {}
            tmp['id'] = node['nid']
            tmp['name'] = node['title']
            tmp['pId'] = node['p_nid']
            tmp['checked'] = True if sql.where('uid=? AND nid=?',(self.__uid,tmp['id'])).count() else False
            data.append(tmp)
        return data

    #取指定子节点
    def get_son_node(self,nid,nodes):
        data = []
        for node in nodes:
            if node['p_nid'] == nid: data.append(node)
        return data

    #取指定节点
    def get_node_find(self,args):
        nid = int(args.nid)
        data = M('nodes').where('nid=?',(nid,)).field(self.__nodes_field).find()
        return data

    #指定节点下的取所有子节点
    def get_list_nodes(self,args):
        nid = int(args.nid)
        data = M('nodes').where('p_nid=?',(nid,)).field(self.__nodes_field).order('sort asc').select()
        return data


    #取用户权限
    def get_user_rule(self,args):
        uid = int(args.uid)
        nodes = M('user_node_realtion').where('uid=?',(uid,)).field('nid').select()
        return nodes

    #用户登录
    def login(self,args):
        if not (hasattr(args, 'username') or hasattr(args, 'password') or hasattr(args, 'code')):
            return public.returnMsg(False,'LOGIN_USER_EMPTY')
        
        self.error_num(False)
        if self.limit_address('?') < 1: return public.returnMsg(False,'LOGIN_ERR_LIMIT')
        args.username = args.username.strip();
        userInfo = M('users').where("username=?",(args.username,)).field('uid,username,password,salt').find()
        if not userInfo: return public.returnMsg(False,'LOGIN_USER_ERR')
        password = public.md5(public.md5(userInfo['salt'] + args.password.strip()) + userInfo['salt'])

        if 'coll_code' in session:
            if session['coll_code']:
                if not public.checkCode(args.code):
                    write_log('用户登录','验证码错误，IP[%s]'% public.GetClientIp());
                    return public.returnMsg(False,'CODE_ERR')
        try:
            if userInfo['username'] != args.username or userInfo['password'] != password:
                write_log('用户登录','密码错误，IP[%s]' % public.GetClientIp());
                num = self.limit_address('+');
                return public.returnMsg(False,'LOGIN_USER_ERR',(str(num),))
            
            session['coll_login'] = True;
            session['coll_username'] = userInfo['username']
            session['coll_uid'] = userInfo['uid']

            write_log('用户登录','登录成功,[%s],[%s]' % (userInfo['username'],public.GetClientIp()));
            self.limit_address('-');
            cache.delete('coll_panelNum')
            cache.delete('coll_dologin')
            return public.returnMsg(True,'LOGIN_SUCCESS')
        except Exception as ex:
            stringEx = str(ex)
            write_log('用户登录','密码错误，IP[%s]' % public.GetClientIp());
            num = self.limit_address('+');
            return public.returnMsg(False,'LOGIN_USER_ERR',(str(num),))

    #退出登录
    def loginout(self,args):
        if 'coll_login' in session:
            session['coll_login'] = None
            session['coll_username'] = None
            session['coll_uid'] = None
            
        return redirect('login.html')


    #防暴破
    def error_num(self,s = True):
        nKey = 'coll_panelNum'
        num = cache.get(nKey)
        if not num:
            cache.set(nKey,1)
            num = 1
        if s: cache.inc(nKey,1)
        if num > 6: session['coll_code'] = True;
    
    #IP限制
    def limit_address(self,type):
        import time
        clientIp = public.GetClientIp();
        numKey = 'coll_limitIpNum_' + clientIp
        limit = 6;
        outTime = 600;
        try:
            #初始化
            num1 = cache.get(numKey)
            if not num1:
                cache.set(numKey,1,outTime);
                num1 = 1;
                        
            #计数
            if type == '+':
                cache.inc(numKey,1)
                self.error_num();
                session['coll_code'] = True;
                return limit - (num1+1);
            
            #清空
            if type == '-':
                cache.delete(numKey);
                session['coll_code'] = False;
                return 1;
            return limit - num1;
        except:
            return limit;

    