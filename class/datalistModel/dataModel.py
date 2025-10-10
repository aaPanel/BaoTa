# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: cjxin <cjxin@bt.cn>
# -------------------------------------------------------------------
# 面板获取列表公共库
# ------------------------------

import os,sys,time,json,db,re
# from turtle import pu

import public
panelPath = '/www/server/panel'
os.chdir(panelPath)
if not panelPath + "/class/" in sys.path:
    sys.path.insert(0, panelPath + "/class/")

class main:

    siteorder_path = None
    __panel_path = public.get_panel_path()
    __SORT_DATA = ['site_ssl', 'rname', 'php_version', 'backup_count', 'total_flow', '7_day_total_flow', 'one_day_total_flow',
                   'one_hour_total_flow']

    sort_file = None
    def __init__(self):
        self.limit_path = '{}/data/limit.pl'.format(self.__panel_path)
        self.siteorder_path = '{}/data/siteorder.pl'.format(self.__panel_path)
        self.sort_file = '{}/data/sort_list.json'.format(self.__panel_path)


    """
    @name 获取表数据
    @param table 表名
    @param p 分页
    @param limit 条数
    @param search 搜索
    @param type 类型
    """
    def get_data_list(self,get):
        if not hasattr(get,'table'):
            return public.returnMsg(False,'缺少参数table')
        get = self._get_args(get)
        try:
            s_list = self.func_models(get,'get_data_where')
        except:
            s_list = []

        where_sql,params = self.get_where(get,s_list)

        data = self.get_page_data(get,where_sql,params)
        get.data_list = data['data']
        data['data'] = self.func_models(get,'get_data_list')
        data = self.get_sort_data(data)
        return data


    """
    @name 清空排序字段
    """
    def del_sorted(self,get):
        return self.func_models(get,'del_sorted')

    """
    @name 设置置顶
    """
    def setSort(self,get):

        return self.func_models(get,'setSort')


    """
    @name 获取查询条件
    @param s_list 查询条件
    """
    def get_where(self, get, s_list):

        search = get.search.strip()
        where, param = self._get_search_where(get.table, search)

        wheres = []
        params = list(param)
        if search:
            try:
                get.where = where
                get.params = params
                res = self.func_models(get, 'get_search_where')
                if not 'status' in res:
                    where, params = res
            except:pass

        if where:
            wheres = ['({})'.format(where)]

        for val in s_list:
            if type(val) == str:
                wheres.append(val)
            else:
                wheres.append(val[0])
                if type(val[1]) == str:
                    params.append(val[1])
                elif type(val[1]) == tuple:
                    params += list(val[1])
                else:
                    params += val[1]

        where_sql = ' AND '.join(wheres)
        return where_sql, params



    def get_page_data(self,get,where_sql,params,result='1,2,3,4,5,8'):

        # 包含分页类
        import page
        # 实例化分页类
        page = page.Page()

        db_obj = public.M(get.table)

        if type(params) == list:
            params = tuple(params)
        info = {}
        info['p'] = get.p
        info['row'] = get.limit
        info['count'] =  public.M(get.table).where(where_sql, params).count()

        try:
            from flask import request
            info['uri'] = public.url_encode(request.full_path)
        except:
            info['uri'] = ''
        info['return_js'] = ''
        if hasattr(get, 'tojs'):
            if re.match(r"^[\w\.\-]+$", get.tojs):
                info['return_js'] = get.tojs

        data = {}
        data['where'] = where_sql
        data['page'] = page.GetPage(info, result)

        o_list = get.order.split(' ')
        if o_list[0] in self.__SORT_DATA:
            data['data'] = db_obj.table(get.table).where(where_sql, params).select()
            data['plist'] = {'shift': page.SHIFT, 'row': page.ROW, 'order': get.order}
        else:

            if len(o_list) > 1:
                if not self.check_field_exists(db_obj,get.table, o_list[0]):
                    o_list[0] = 'id'
                if not o_list[1] in ['asc', 'desc']:
                    o_list[1] = 'desc'

                get.order = ' '.join(o_list)
            data['data'] = db_obj.table(get.table).where(where_sql, params).order(get.order).limit(str(page.SHIFT) + ',' + str(page.ROW)).select()

        try:
            if db_obj.ERR_INFO:
                data['error'] = db_obj.ERR_INFO
        except:pass

        data['search_history'] = []
        if 'search_key' in get and get['search_key']:
            data['search_history'] = public.get_search_history(get.table, get['search_key'])
        return data


    def check_field_exists(self,db_obj,table_name, field_name ):
        """
        @name 检查字段是否存在
        """
        try:
            res = db_obj.query("PRAGMA table_info({})".format(table_name))
            for val in res:
                if field_name == val[1]:
                    return True
        except:pass
        return False

    def get_sort_data(self, data):
        """
        @获取自定义排序数据
        @param data: 数据
        """
        if 'plist' in data:
            plist = data['plist']
            o_list = plist['order'].split(' ')

            reverse = False
            sort_key = o_list[0].strip()

            if o_list[1].strip() == 'desc':
                reverse = True

            if sort_key in ['site_ssl']:
                for info in data['data']:
                    if type(info['ssl']) == int:
                        info[sort_key] = info['ssl']
                    else:
                        try:
                            info[sort_key] = info['ssl']['endtime']
                        except:
                            info[sort_key] = ''
            elif sort_key in ['total_flow', 'one_hour_total_flow', '7_day_total_flow', 'one_day_total_flow']:
                for info in data['data']:
                    info[sort_key] = 0
                    try:
                        if 'net' in info and sort_key in info['net']:
                            info[sort_key] = info['net'][sort_key]
                    except:
                        pass

            sort_reverse = 1 if reverse is True else 0
            data['data'].sort(key=lambda x: (x.get('sort', 0) == sort_reverse, x[sort_key]), reverse=reverse)
            data['data'] = data['data'][plist['shift']: plist['shift'] + plist['row']]

        return data

    """
    @name 设置备注
    """
    def _setPs(self,table,id,ps):
        if public.M(table).where('id=?',(id,)).setField('ps',public.xssencode2(ps)):
            return public.returnMsg(True, 'EDIT_SUCCESS')
        return public.returnMsg(False, 'EDIT_ERROR')


    def _get_search_where(self,table,search):

        where = ''
        params = ()

        if search:
            try:
                search = re.search(r"[\w\x80-\xff\.\_\-]+", search).group()
            except:
                return where, params
            conditions = ''
            if '_' in search:
                search = str(search).replace("_", "/_")
                conditions = " escape '/'"
            wheres = {
                'sites': ("name LIKE ?{} OR ps LIKE ?{}".format(conditions, conditions), ('%' + search + '%', '%' + search + '%')),
                'ftps': ("name LIKE ?{} OR ps LIKE ?{}".format(conditions, conditions), ('%' + search + '%', '%' + search + '%')),
                'databases': ("(name LIKE ?{} OR ps LIKE ?{})".format(conditions, conditions), ("%" + search + "%", "%" + search + "%")),
                'crontab': ("name LIKE ?{}".format(conditions), ('%' + (search) + '%')),
                'logs': ("username=?{} OR type LIKE ?{} OR log{} LIKE ?{}".format(conditions, conditions, conditions, conditions), (search, '%' + search + '%', '%' + search + '%')),
                'backup': ("pid=?", (search,)),
                'users': ("id='?' OR username=?{}".format(conditions), (search, search)),
                'domain': ("pid=? OR name LIKE ?{}".format(conditions), (search, '%' + search + '%')),
                'tasks': ("status=? OR type=?", (search, search)),
            }

        try:
            return wheres[table]
        except:
            return '', ()

    """
    @name 格式化公用参数
    """
    def _get_args(self,get):
        try:
            if not 'p' in get:
                get.p = 1
            get.p = int(get.p)
        except: get.p = 1

        try:
            if not 'limit' in get:
                get.limit = 20
            get.limit = int(get.limit)
        except: get.limit = 20

        if not 'search' in get:
            get.search = ''

        if '_' in get.search:
            get.search = get.search.replace("_", "/_")

        if not 'order' in get  or not get['order']:
            get.order = 'id desc'
        return get


    def get_objectModel(self):
        '''
        获取模型对象
        '''
        from panelController import Controller
        project_obj = Controller()

        return project_obj


    def func_models(self,get,def_name):
        '''
        获取模型对象
        '''

        sfile = '{}/class/datalistModel/{}Model.py'.format(self.__panel_path,get.table)
        if not os.path.exists(sfile):
            raise Exception('模块文件{}不存在'.format(sfile))
        obj_main = self.get_objectModel()

        args = public.dict_obj()
        args['data'] = get
        args['mod_name'] = get.table
        args['def_name'] = def_name

        return obj_main.model(args)

