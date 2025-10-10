#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
#-------------------------------------------------------------------

#------------------------------
# 任务脚本
#------------------------------

from crontabModel.base import crontabBase
import db
import public
import time
import json
import os
import sys

class main(crontabBase):

    _sql = None
    _return_type = ['string','int','float']
    _script_type = ['bash','python']
    _log_type = '任务编排-脚本库'

    def __init__(self) -> None:
        try:
            super().__init__()
        except:
            public.repair_db()
            super().__init__()
        self._sql = db.Sql().dbfile(self.dbfile)

    def get_script_list(self,args = None):
        '''
            @name 获取脚本列表
            @author hwliang
            @param args<dict_obj>{
                p<int> 分页
                rows<int> 每页数量
                search<string> 搜索关键字
            }
            @return list
        '''
        p = 1
        if args and 'p' in args: p = int(args.p)
        rows = 10
        if args and 'rows' in args: rows = int(args.rows)
        search = ''
        if args and 'search' in args: search = args.search
        tojs = ''
        if args and 'tojs' in args: tojs = args.tojs
        where = ''
        params = []
        if search:
            where = "(name like ? or ps like ?)"
            params.append('%' + search + '%')
            params.append('%' + search + '%')

        if 'type_id' in args:
            if where: where += ' and '
            where += "type_id=?"

            params.append(args.type_id)

        if 'is_baota' in args:
            if where: where += ' and '
            where += "is_baota=?"
            params.append(args.is_baota)

        if 'return_type' in args:
            if where: where += ' and '
            where += "return_type=?"
            params.append(args.return_type)

        if 'script_type' in args:
            if where: where += ' and '
            where += "script_type=?"
            params.append(args.script_type)

        if 'status' in args:
            if where: where += ' and '
            where += "status=?"
            params.append(args.status)

        count = self._sql.table('scripts').where(where,params).count()
        data = public.get_page(count,p,rows,tojs)
        data['data'] = self._sql.table('scripts').where(where,params).order('script_id desc').limit(data['row'],data['shift']).select()
        for i in data['data']:
            i['last_exec_time'] = self._sql.table('tasks').where('script_id=?',(i['script_id'],)).order('log_id desc').getField('start_time')
        return data


    def get_script_list_by_type(self,args):
        '''
            @name 按分类获取脚本列表
            @author hwliang
            @return list
        '''
        try:
            data = self._sql.table('types').select()
            for i in data:
                i['script_list'] = self._sql.table('scripts').where('type_id=?',i['type_id']).select()
        except Exception as ex:
            if str(ex).find('integers') != -1:
                journal = self.dbfile + '-journal'
                if os.path.exists(self.dbfile) and os.path.exists(journal):
                    os.remove(journal)
                    os.remove(self.dbfile)

                self.create_table()
                data = self._sql.table('types').select()
                for i in data:
                    i['script_list'] = self._sql.table('scripts').where('type_id=?',i['type_id']).select()

        return data

    def get_type_list(self,args):
        '''
            @name 获取分类列表
            @author hwliang
            @return list
        '''
        return self._sql.table('types').select()

    def get_script_type(self,script_body):
        '''
            @name 获取脚本类型
            @param script_body<string> 脚本内容
            @return string
        '''

        if script_body.find('import ') != -1:
            return 'python'
        elif script_body.find('#!/bin/bash') != -1:
            return 'bash'
        elif script_body.find('#!/bin/sh') != -1:
            return 'bash'
        elif script_body.find('#!/usr/bin/env python') != -1:
            return 'python'
        elif script_body.find('#!/usr/bin/env bash') != -1:
            return 'bash'
        elif script_body.find('#!/usr/bin/env sh') != -1:
            return 'bash'
        elif script_body.find('#!/usr/bin/python') != -1:
            return 'python'
        elif script_body.find('#!/usr/bin/python3') != -1:
            return 'python'
        elif script_body.find('#!/usr/bin/python2') != -1:
            return 'python'
        elif script_body.find('#!/usr/bin/bash') != -1:
            return 'bash'
        elif script_body.find('#!/usr/bin/sh') != -1:
            return 'bash'
        elif script_body.find('#!/bin/python') != -1:
            return 'python'
        elif script_body.find('#!/bin/python3') != -1:
            return 'python'
        elif script_body.find('#!/bin/python2') != -1:
            return 'python'
        elif script_body.find('#coding: utf-8') != -1:
            return 'python'
        elif script_body.find('#coding:utf-8') != -1:
            return 'python'
        elif script_body.find('#coding:gbk') != -1:
            return 'python'
        elif script_body.find('#coding: gbk') != -1:
            return 'python'
        elif script_body.find('#coding:gb2312') != -1:
            return 'python'
        elif script_body.find('#coding: gb2312') != -1:
            return 'python'
        elif script_body.find('#coding:utf-8') != -1:
            return 'python'
        elif script_body.find('#coding:utf-8') != -1:
            return 'python'
        else:
            return 'bash'




    def create_script(self,args):
        '''
            @name 创建脚本
            @author hwliang
            @param args<dict_obj>{
                name<string> 脚本名称
                script<string> 脚本内容
                type_id<int> 脚本类型
                ps<string> 脚本描述
                return_type<string> 返回类型 (string|int|float|json_object)
            }
            @return bool
        '''
        name = args.get('name','')
        script = args.get('script','')
        type_id = args.get('type_id',7)
        is_baota = args.get('is_baota',0)
        author = args.get('author','')
        ps = args.get('ps','')
        return_type = args.get('return_type','string')
        script_type = self.get_script_type(script)
        version = args.get('version','1.0')
        is_args = args.get('is_args/d',0)
        args_title = args.get('args_title','')
        args_ps = args.get('args_ps','')
        if not type_id: return public.returnMsg(False,'分类ID不能为空')
        if not name or not script: return public.returnMsg(False,'脚本名称或脚本内容不能为空')
        if not return_type in self._return_type: return public.returnMsg(False,'返回类型错误')
        if not script_type in self._script_type: return public.returnMsg(False,'脚本类型错误')

        pdata = {
            'name':name,
            'script':script,
            'type_id':type_id,
            'is_baota':is_baota,
            'author':author,
            'ps':ps,
            'return_type':return_type,
            'script_type':script_type,
            'version':version,
            'is_args':is_args,
            'args_title':args_title,
            'args_ps':args_ps,
            'create_time':int(time.time())
        }

        if self._sql.table('scripts').where("name=?",(name,)).count():
            return public.returnMsg(False,'脚本名称已存在')
        res = self._sql.table('scripts').insert(pdata)
        if not res:
            return public.returnMsg(False,'创建失败')
        public.WriteLog(self._log_type,'创建脚本[' + name + ']成功')
        return public.returnMsg(True,'创建成功')




    def remove_script(self,args):
        '''
            @name 删除脚本
            @author hwliang
            @param args<dict_obj>{
                script_id<int> 脚本ID
            }
            @return dict
        '''
        script_id = args.get('script_id',0)
        if not script_id: return public.returnMsg(False,'脚本ID不能为空')
        script_info = self._sql.table('scripts').where('script_id=?',(script_id,)).find()
        if not script_info: return public.returnMsg(False,'指定脚本不存在')
        if script_info['is_baota'] == 1: return public.returnMsg(False,'宝塔内置脚本不能删除')
        trigger_name = self._sql.table('trigger').where('script_id=?',(script_id,)).getField('name')
        if trigger_name:
            return public.returnMsg(False,'该脚本当前正在被任务[{}]使用,请先删除任务!'.format(trigger_name))

        trigger_id = self._sql.table('operator_where').where('script_id=?',(script_id,)).getField('trigger_id')
        if trigger_id:
            trigger_name = self._sql.table('trigger').where('id=?',(trigger_id,)).getField('name')
            return public.returnMsg(False,'该脚本当前正在被任务[{}]的事件使用,请先删除该任务事件!'.format(trigger_name))

        if not self._sql.table('scripts').where('script_id=?',(script_id,)).delete():
            return public.returnMsg(False,'删除失败')
        self._sql.table('tasks').where('script_id=? and where_id=0 and trigger_id=0',(script_id,)).delete()
        public.WriteLog(self._log_type,'删除脚本[' + script_info['name'] + ']成功')
        return public.returnMsg(True,'删除成功')


    def modify_script(self,args):
        '''
            @name 修改脚本信息
            @author hwliang
            @param args<dict_obj>{
                id<int> 脚本ID
                name<string> 脚本名称
                script<string> 脚本内容
                type<string> 脚本类型
                ps<string> 脚本描述
                return_type<string> 返回类型 (string|int|float)
            }
            @return bool
        '''

        script_id = args.get('script_id',0)
        name = args.get('name','')
        script = args.get('script','')
        type_id = args.get('type_id',7)
        # is_baota = args.get('is_baota',0)
        # author = args.get('author','')
        ps = args.get('ps','')
        return_type = args.get('return_type','string')
        is_args = args.get('is_args/d',0)
        args_title = args.get('args_title','')
        args_ps = args.get('args_ps','')
        script_type = self.get_script_type(script)
        # version = args.get('version','1.0')
        if not script_id: return public.returnMsg(False,'脚本ID不能为空')
        if not name or not script: return public.returnMsg(False,'脚本名称或脚本内容不能为空')
        if not return_type in self._return_type: return public.returnMsg(False,'返回类型错误')
        if not script_type in self._script_type: return public.returnMsg(False,'脚本类型错误')

        pdata = {
            'name':name,
            'script':script,
            'type_id':type_id,
            'ps':ps,
            'return_type':return_type,
            'script_type':script_type,
            'is_args':is_args,
            'args_title':args_title,
            'args_ps':args_ps,
        }

        script_info = self._sql.table('scripts').where('script_id=?',(script_id,)).find()
        if not script_info:
            return public.returnMsg(False,'指定脚本不存在')
        if not self._sql.table('scripts').where('script_id=?',(script_id,)).update(pdata):
            return public.returnMsg(False,'修改失败')
        public.WriteLog(self._log_type,'修改脚本[' + name + ']成功')
        return public.returnMsg(True,'修改成功')

    def add_task_log(self,script_id,trigger_id,where_id,status,result_succ,result_err,start_time,end_time):
        '''
            @name 添加任务日志
            @param script_id<int> 脚本ID
            @param trigger_id<int> 触发器ID
            @param where_id<int> 事件ID
            @param status<int> 任务状态
            @param result_succ<string> 成功结果
            @param result_err<string> 错误结果
            @param start_time<int> 开始时间
            @param end_time<int> 结束时间
            @return bool
        '''
        return self._sql.table('tasks').add('script_id,trigger_id,where_id,status,result_succ,result_err,start_time,end_time',
            (script_id,trigger_id,where_id,status,result_succ,result_err,start_time,end_time))


    def get_script_logs(self,args):
        '''
            @name 获取脚本执行日志
            @param args<dict_obj>{
                "script_id": <int> 脚本ID
                "p": <int> 页码
                "rows": <int> 每页数量
            }
        '''
        script_id = int(args.get('script_id',0))
        if not script_id: return public.returnMsg(False,'脚本ID不能为空')
        p = 1
        if 'p' in args: p = int(args['p'])
        rows = 10
        if 'rows' in args: rows = int(args['rows'])
        tojs = ''
        if 'tojs' in args: tojs = args.tojs

        where = 'script_id=?'
        where_args = (script_id,)
        count = self._sql.table('tasks').where(where,where_args).count()
        page = public.get_page(count,p,rows,tojs)
        page['data'] = self._sql.table('tasks').where(where,where_args).limit(page['row'],page['shift']).order('log_id desc').select()
        return page

    def test_script(self,args):
        '''
            @name 测试运行脚本
            @author hwliang
            @param args<dict_obj>{
                script_id<int> 脚本ID
            }
            @return dict
        '''
        script_start_time = int(time.time())
        script_id = args.get('script_id',0)
        if not script_id: return public.returnMsg(False,'脚本ID不能为空')
        script_info = self._sql.table('scripts').where('script_id=?',(script_id,)).field('script,script_type,return_type').find()
        script_args = args.get('args/s','')
        if script_args: script_args = ' ' + script_args
        if 'is_args' in script_info and script_info['is_args'] and not script_args:
            return public.returnMsg(False,'该脚本需要参数')
        if not script_info: return public.returnMsg(False,'指定脚本不存在')
        tmp_file= '{}/tmp/{}.tmp'.format(public.get_panel_path(),public.md5(script_info['script']))
        try:
            public.writeFile(tmp_file,script_info['script'])
            if script_info['script_type'] == 'bash':
                result = public.ExecShell("bash {}{}".format(tmp_file,script_args))
            elif script_info['script_type'] == 'python':
                python_bin = public.get_python_bin()
                result = public.ExecShell('{} -u {}{}'.format(python_bin,tmp_file,script_args))
            res = result[0].strip()
            if result[1]:
                self.add_task_log(script_id,0,0,0,result[0],result[1],script_start_time,int(time.time()))
                return public.returnMsg(False,'脚本运行错误，请检查脚本代码是否有误: \n{}'.format(result[0] + "\n" +  result[1].split('.tmp:')[-1]))
        except Exception as ex:
            error_msg = public.get_error_info()
            self.add_task_log(script_id,0,0,0,'',error_msg,script_start_time,int(time.time()))
            return public.returnMsg(False,'执行失败,错误信息:\n{}'.format(error_msg))
        finally:
            if os.path.exists(tmp_file): os.remove(tmp_file)
        self.add_task_log(script_id,0,0,1,result[0],result[1],script_start_time,int(time.time()))
        return public.returnMsg(True,"执行成功: \n{}".format(public.xssencode2(res)))










