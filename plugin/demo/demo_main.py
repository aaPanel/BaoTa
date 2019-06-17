#!/usr/bin/python
# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: xxx <xxxx@qq.com>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   宝塔第三方应用开发DEMO
#+--------------------------------------------------------------------
import sys,os,json

#设置运行目录
os.chdir("/www/server/panel")

#添加包引用位置并引用公共包
sys.path.append("class/")
import public

#from common import dict_obj
#get = dict_obj();


#在非命令行模式下引用面板缓存和session对象
if __name__ != '__main__':
    from BTPanel import cache,session,redirect

    #设置缓存(超时10秒) cache.set('key',value,10)
    #获取缓存 cache.get('key')
    #删除缓存 cache.delete('key')

    #设置session:  session['key'] = value
    #获取session:  value = session['key']
    #删除session:  del(session['key'])


class demo_main:
    __plugin_path = "/www/server/panel/plugin/demo/"
    __config = None

    #构造方法
    def  __init__(self):
        pass

    #自定义访问权限检查
    #一但声明此方法，这意味着可以不登录面板的情况下，直接访问此插件，由_check方法来检测是否有访问权限
    #如果您的插件必需登录后才能访问的话，请不要声明此方法，这可能导致严重的安全漏洞
    #如果权限验证通过，请返回True,否则返回 False 或 public.returnMsg(False,'失败原因')
    #示例未登录面板的情况下访问get_logs方法： /demo/get_logs.json  或 /demo/get_logs.html (使用模板)
    #可通过args.fun获取被请求的方法名称
    #可通过args.client_ip获取客户IP
    def _check(self,args):
        #token = '123456'
        #limit_addr = ['192.168.1.2','192.168.1.3']
        #if args.token != token: return public.returnMsg(False,'Token验证失败!')
        #if not args.client_ip in limit_addr: return public.returnMsg(False,'IP访问受限!')
        #return redirect('/login')
        return True

    #访问/demo/index.html时调用的方法，需要在templates中有index.html，否则无法正确响应模板
    def index(self,args):
        return self.get_logs(args)


    #获取面板日志列表
    #传统方式访问get_logs方法：/plugin?action=a&name=demo&s=get_logs
    #使用动态路由模板输出： /demo/get_logs.html
    #使用动态路由输出JSON： /demo/get_logs.json
    def get_logs(self,args):
        #处理前端传过来的参数
        if not 'p' in args: args.p = 1
        if not 'rows' in args: args.rows = 12
        if not 'callback' in args: args.callback = ''
        args.p = int(args.p)
        args.rows = int(args.rows)

        #取日志总行数
        count = public.M('logs').count()

        #获取分页数据
        page_data = public.get_page(count,args.p,args.rows,args.callback)

        #获取当前页的数据列表
        log_list = public.M('logs').order('id desc').limit(page_data['shift'] + ',' + page_data['row']).field('id,type,log,addtime').select()
        
        #返回数据到前端
        return {'data': log_list,'page':page_data['page'] }
        
    #读取配置项(插件自身的配置文件)
    #@param key 取指定配置项，若不传则取所有配置[可选]
    #@param force 强制从文件重新读取配置项[可选]
    def __get_config(self,key=None,force=False):
        #判断是否从文件读取配置
        if not self.__config or force:
            config_file = self.__plugin_path + 'config.json'
            if not os.path.exists(config_file): return None
            f_body = public.ReadFile(config_file)
            if not f_body: return None
            self.__config = json.loads(f_body)

        #取指定配置项
        if key:
            if key in self.__config: return self.__config[key]
            return None
        return self.__config

    #设置配置项(插件自身的配置文件)
    #@param key 要被修改或添加的配置项[可选]
    #@param value 配置值[可选]
    def __set_config(self,key=None,value=None):
        #是否需要初始化配置项
        if not self.__config: self.__config = {}

        #是否需要设置配置值
        if key:
            self.__config[key] = value

        #写入到配置文件
        config_file = self.__plugin_path + 'config.json'
        public.WriteFile(config_file,json.dumps(self.__config))
        return True

