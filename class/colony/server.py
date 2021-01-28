# coding: utf-8
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: wzj <wzj@bt.cn>
# +-------------------------------------------------------------------
# +-------------------------------------------------------------------
# | 服务器管理操作类库
# +-------------------------------------------------------------------
import sys
import os
import time

os.chdir('/www/server/panel')
sys.path.insert(0, 'class/')
import public


class server(object):
    def __init__(self):
        self.create_table()

    def create_table(self):
        '''
        创建表
        '''
        if not public.M('sqlite_master').where('type=? AND name=?', ('table', 'colony_server')).count():
            public.M('').execute('''CREATE TABLE "colony_server" (
                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "host" TEXT,
                "port" INTEGER DEFAULT 22,
                "username" TEXT,
                "password" TEXT DEFAULT '',
                "c_type" INTEGER DEFAULT 0,
                "pkey" TEXT DEFAULT '',
                "ps" TEXT DEFAULT '',
                "addtime" INTEGER);''')

    def get_server_list(self, args):
        '''
        取服务器资源列表
        '''
        if 'p' not in args:
            args.p = 1
        server_list = public.M('colony_server').select()
        if hasattr(args, 'query'):
            tmpList = []
            for server in server_list:
                if server['host'].find(args.query) != -1 or server['ps'].find(args.query) != -1:
                    tmpList.append(server)
            server_list = tmpList

        return self.get_page(server_list, args)

    def get_page(self, data, get):
        '''
        分页
        '''
        import page

        page = page.Page()

        info = {}
        info['count'] = len(data)
        info['row'] = 15
        info['p'] = 1
        if hasattr(get, 'p'):
            info['p'] = int(get['p'])
        info['uri'] = {}
        info['return_js'] = ''
        if hasattr(get, 'tojs'):
            info['return_js'] = get.tojs

        # 获取分页数据
        result = {}
        result['page'] = page.GetPage(info, limit='1,2,3,4,5,8')
        n = 0
        result['data'] = []
        for i in range(info['count']):
            if n >= page.ROW: break
            if i < page.SHIFT: continue
            n += 1
            result['data'].append(data[i])
        return result

    def get_server_info(self, args):
        '''
        取指定服务器的资源信息
        '''
        data = public.M('colony_server').where('id=?', args['id']).find()
        return data

    def add_server(self, args):
        '''
        添加服务器资源
        '''
        pdata = {}
        pdata['username'] = args.username
        if 'password' in args: pdata['password'] = args.password
        if 'pkey' in args: pdata['pkey'] = args.pkey
        pdata['c_type'] = int(args.c_type)
        pdata['host'] = args.host
        if 'port' in args: pdata['port'] = int(args.port)
        if 'ps' in args: pdata['ps'] = args.ps
        pdata['addtime'] = int(time.time())

        table = public.M('colony_server')
        if table.where('host=?', pdata['host']).count():
            return public.returnMsg(False, '该服务器已经添加过了!')
        table.insert(pdata)
        return public.returnMsg(True, '新增成功!')

    def modify_server(self, args):
        '''
        编辑服务器资源
        '''
        pdata = {}
        pdata['username'] = args.username
        if 'password' in args: pdata['password'] = args.password
        if 'pkey' in args: pdata['pkey'] = args.pkey
        pdata['c_type'] = int(args.c_type)
        pdata['host'] = args.host
        if 'port' in args: pdata['port'] = int(args.port)
        if 'ps' in args: pdata['ps'] = args.ps

        public.M('colony_server').where('id=?', args.id).update(pdata)
        return public.returnMsg(True, '编辑成功!')

    def del_server(self, args):
        '''
        删除服务器资源
        '''
        public.M('colony_server').where('id=?', args.id).delete()
        return public.returnMsg(True, '删除成功!')
