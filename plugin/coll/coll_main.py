#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 6.x
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   微架构 - 主控端
#+--------------------------------------------------------------------
import os,sys
os.chdir('/www/server/panel')
sys.path.insert(0,'class/')
import public
from inc.coll_common import coll_common
from inc.coll_db import M
from BTPanel import session, redirect,g
class coll_main(coll_common):
    __plugin_path = '/www/server/panel/plugin/coll'
    def __init__(self):
        pass

    def _check(self,args):
        return True

    def ajax(self,args):
        if not 'm' in args or  not 'f' in args: return public.returnMsg(False,'错误的参数')
        if args.m.find('./') != -1: return public.returnMsg(False,'错误的请求')
        filename = self.__plugin_path + '/inc/' + args.m + '.py'
        if not os.path.exists(filename): return public.returnMsg(False,'指定模块不存在')
        my_module = __import__('inc.' + args.m)
        try:
            if sys.version_info[0] == 2:
                reload(my_module)
            else:
                from imp import reload
                reload(my_module)
        except:pass
        if not hasattr(my_module,args.m): return public.returnMsg(False,'指定模块不存在')
        mod = getattr(my_module,args.m)
        if not hasattr(mod,args.m): return public.returnMsg(False,'指定模块不存在')
        userObj = getattr(mod,args.m)()
        if not hasattr(userObj,args.f): return public.returnMsg(False,'指定方法不存在!')
        return getattr(userObj,args.f)(args)

    def shell(self,args):
        from inc.coll_shell import coll_shell
        sl = coll_shell()
        data = sl.get_host(args)
        return data

    def login(self,args):
        if self.is_login(): return redirect('user.html',302)
        if not 'coll_code' in session: session['coll_code'] = False
        return {'code':session['coll_code']}

    def index(self,args):
        g.title = '首页'
        serverList = M('server_list').order('sort asc').field('sid,gid,address,state,ps,area').get()
        return {"serverList":serverList}

    def server(self,args):
        g.title = '首页'
        serverList = M('server_list').order('sort asc').field('sid,gid,address,state,ps,area,panel').get()
        return {"serverList":serverList}

    def iframe(self,args):
        g.title = 'iframe'
        return {}

    def terminal(self,args):
        return {}

    def user(self,args):
        from inc.coll_user import coll_user 
        userList = coll_user().get_user_list(args)
        g.title = '用户管理'
        return {'userList':userList}


if __name__ == '__main__':
    p = coll_main()
    print(p.user_admin(None))



