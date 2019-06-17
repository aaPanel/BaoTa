#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 6.x
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   微架构 - 服务器管理
#+--------------------------------------------------------------------
import re,sys,os,public,time,json
from inc.coll_db import M,write_log
from BTPanel import session


class coll_server:
    __log_type = '服务器管理'
    __server_field = 'sid,uid,gid,address,config,panel,ps,area,state,addtime,sort,token'

    def __init__(self):
        pass

    #取服务器列表
    def get_server_list(self,args):
        data = M('server_list').order('sort asc').get()
        return data

    #取指定服务器信息
    def get_server_find(self,args):
        sid = int(args.sid)
        data = M('server_list').where('sid=?',(sid,)).field(self.__server_field + ',AccessToekn,AccessKeyId').find()
        return data

    #添加服务器
    def add_server(self,args):
        pdata = {}
        pdata['uid'] = session['coll_uid']
        pdata['gid'] = 0
        pdata['address'] = args.address
        pdata['config'] = '{}'
        pdata['panel'] = args.panel
        #pdata['AccessToekn'] = args.AccessToekn
        #pdata['AccessKeyId'] = args.AccessKeyId
        pdata['state'] = 1
        pdata['ps'] = args.ps
        #pdata['area'] = args.area
        pdata['token'] = args.token
        pdata['addtime'] = int(time.time())
        pdata['sort'] = 1
        ser =  M('server_list')
        if ser.where('address=?',(pdata['address'],)).count(): return public.returnMsg(False,'指定服务器已存在!')
        ser.insert(pdata)
        write_log(self.__log_type,'添加服务器[%s][%s]' % (pdata['address'],pdata['ps']))
        return public.returnMsg(True,'添加成功!')      

    #编辑服务器
    def modify_server(self,args):
        sid = int(args.sid)
        ser =  M('server_list')
        if not ser.where('sid=?',(sid,)).count(): return public.returnMsg(False,'指定服务器不存在!')
        pdata = {}
        if 'gid' in args: pdata['gid'] = int(args.gid)
        if 'address' in args: pdata['address'] = args.address
        if 'config' in args: pdata['config'] = args.config
        if 'panel' in args: pdata['panel'] = args.panel
        if 'AccessKeyId' in args: pdata['AccessKeyId'] = args.AccessKeyId
        if 'AccessToekn' in args: pdata['AccessToekn'] = args.AccessToekn
        if 'state' in args: pdata['state'] = args.state
        if 'ps' in args: pdata['ps'] = args.ps
        if 'area' in args: pdata['area'] = args.area
        if 'sort' in args: pdata['sort'] = args.sort
        if 'token' in args: pdata['token'] = args.token.strip()
        ser.where('sid=?',(sid,)).update(pdata)
        write_log(self.__log_type,'编辑服务器[%s]' % sid)
        return public.returnMsg(True,'编辑成功!')

    #删除服务器
    def remove_server(self,args):
        sid = int(args.sid)
        ser =  M('server_list')
        if not ser.where('sid=?',(sid,)).count(): return public.returnMsg(False,'指定服务器不存在!')
        ser.where('sid=?',(sid,)).delete()
        M('user_node_realtion').where('sid=?',(sid,)).delete()
        write_log(self.__log_type,'删除服务器[%s]' % sid)
        return public.returnMsg(True,'删除成功!')

    #获取分组列表
    def get_group_list(self,args):
        data = M('server_group').field('gid,group_name,ps').select()
        return data

    #获取指定分组信息
    def get_group_find(self,args):
        gid = int(args.gid)
        data = M('server_group').where('gid=?',(gid,)).field('gid,group_name,ps').find()
        return data


    #添加服务器分组
    def add_group(self,args):
        pdata = {}
        pdata['group_name'] = args.group_name
        pdata['uid'] = session['coll_uid']
        pdata['ps'] = args.ps
        M('server_group').insert(pdata)
        write_log(self.__log_type,'添加分组[%s]' % pdata['group_name'])
        return public.returnMsg(True,'添加成功!')

    #编辑服务器分组 
    def modify_group(self,args):
        gid = int(args.gid)
        pdata = {}
        pdata['group_name'] = args.group_name
        pdata['ps'] = args.ps
        M('server_group').where('gid=?',(gid,)).update(pdata)
        write_log(self.__log_type,'编辑分组[%s]' % pdata['group_name'])
        return public.returnMsg(True,'编辑成功!')

    #删除服务器分组
    def remove_group(self,args):
        gid = int(args.gid)
        M('server_group').where('gid=?',(gid,)).delete()
        write_log(self.__log_type,'删除分组[%s]' % gid)
        return public.returnMsg(True,'删除成功')


    #将指定服务器移动到指定分组
    #param s_ids json
    #param gid int
    def move_to_group(self,args):
        s_ids = json.loads(args.s_ids)
        gid = int(args.gid)
        sql = M('server_list')
        for sid in s_ids:
            sql.where('sid=?',(sid,)).setField('gid',gid)
            write_log('服务器管理','将服务器[%s]的分组设置为[%s]' % (sid,gid))
        return public.returnMsg(True,'操作成功!')
    
    #发送指令到面板
    def send_panel(self,args):
        sid = int(args.sid)
        serverInfo = M('server_list').where('sid=?',(sid,)).field('panel,token').find()
        pdata = json.loads(args.pdata)
        pdata = self.__get_key_data(pdata,serverInfo['token'])
        result = self.__http_post_cookie(serverInfo['panel'] + '/' + args.p_uri,pdata,sid)
        try:
            result = json.loads(result)
        except:
            return result
        return result


    #构造带有签名的关联数组
    def __get_key_data(self,pdata,token):
        pdata['request_time'] = int(time.time())
        pdata['request_token'] =  public.md5(str(pdata['request_time']) + '' + public.md5(str(token)))
        return pdata

    #发送POST请求并保存Cookie
    #@url 被请求的URL地址(必需)
    #@data POST参数，可以是字符串或字典(必需)
    #@timeout 超时时间默认1800秒
    #return string
    def __http_post_cookie(self,url,p_data,sid=1,timeout=1800):
        cookie_path = '/www/server/panel/plugin/coll/cookies'
        if not os.path.exists(cookie_path): os.makedirs(cookie_path,mode=384)
        cookie_file = cookie_path + '/' + public.md5(str(sid)) + '.cookie';
        if sys.version_info[0] == 2:
            #Python2
            import urllib,urllib2,ssl,cookielib

            #创建cookie对象
            cookie_obj = cookielib.MozillaCookieJar(cookie_file)

            #加载已保存的cookie
            if os.path.exists(cookie_file):cookie_obj.load(cookie_file,ignore_discard=True,ignore_expires=True)

            ssl._create_default_https_context = ssl._create_unverified_context

            data = urllib.urlencode(p_data)
            req = urllib2.Request(url, data)
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_obj))
            response = opener.open(req,timeout=timeout)

            #保存cookie
            cookie_obj.save(ignore_discard=True, ignore_expires=True)
            return response.read()
        else:
            #Python3
            import urllib.request,ssl,http.cookiejar
            cookie_obj = http.cookiejar.MozillaCookieJar(cookie_file)
            if os.path.exists(cookie_file): cookie_obj.load(cookie_file,ignore_discard=True,ignore_expires=True)
            handler = urllib.request.HTTPCookieProcessor(cookie_obj)
            data = urllib.parse.urlencode(p_data).encode('utf-8')
            req = urllib.request.Request(url, data)
            opener = urllib.request.build_opener(handler)
            response = opener.open(req,timeout = timeout)
            cookie_obj.save(ignore_discard=True, ignore_expires=True)
            result = response.read()
            if type(result) == bytes: result = result.decode('utf-8')
            return result

    def get_tmp_token(self,args):
        try:
            sid = int(args.sid)
            server_info = M('server_list').where('sid=?',(sid,)).find();
            pdata = {}
            pdata = self.__get_key_data(pdata,server_info['token'])
            result = self.__http_post_cookie(server_info['panel'] + '/config?action=get_tmp_token',pdata,sid)
            return json.loads(result)
        except:
            return public.returnMsg(False,'连接服务器失败!');
