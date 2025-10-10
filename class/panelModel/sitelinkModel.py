# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: sww <sww@bt.cn>
# -------------------------------------------------------------------
# 网站关联数据库，ftp模块
# ------------------------------
import traceback

from panelModel.base import panelBase
import public, config


class main(panelBase):

    def get_site_info(self, get=None):
        """
        @name 获取网站关联信息
        """

        sites = public.M('sites').where('project_type=?', ('PHP',)).select()
        if type(sites) == str:
            raise public.PanelError(sites)
        site_id = {}
        for i in sites:
            if i.get('rname','') == '':
                i['rname'] = i['name']
            del i['name']
            site_id[i['id']] = i
            site_id[i['id']]['ftp'] = {}
            site_id[i['id']]['mysql'] = {}
        ftps = public.M('ftps').field('id,pid,name').select()
        mysqls = public.M('databases').where('type=?', ('MySQL',)).field('id,pid,name').select()
        for i in ftps:
            if i['pid'] != 0 and i['pid'] in site_id.keys():
                site_id[i['pid']]['ftp'] = i
        for i in mysqls:
            if i['pid'] != 0 and i['pid'] in site_id.keys():
                site_id[i['pid']]['mysql'] = i
        return list(site_id.values())

    def get_mysql_info(self, get=None):
        try:
            mysqls = public.M('databases').where('type=?', ('MySQL',)).field('id,pid,name').select()
            for i in mysqls:
                if i['pid'] != 0:
                    site = public.M('sites').where('id=?', (i['pid'],)).field('name,rname').select()
                    if type(site) != str and site:
                        site = site[0]
                    else:
                        site = {'name': '', 'rname': ''}
                    if site['rname'] == '':
                        site['rname'] = site['name']
                    i['rname'] = site['rname']
                    i['is_band'] = 1
            return mysqls
        except:
            return traceback.format_exc()

    def get_ftp_info(self, get=None):
        ftps = public.M('ftps').field('id,pid,name').select()
        return ftps

    def modify_mysql_link(self, get):
        try:
            if not hasattr(get, 'sql_id') or not get.sql_id:
                return public.returnMsg(False, '参数错误!')
            if not hasattr(get, 'pid') or not get.pid:
                return public.returnMsg(False, '参数错误!')
            sql_id = get.sql_id
            pid = get.pid
            data = public.M('databases').where('id=?', (sql_id,)).field('id,pid,name')
            if type(data) != str and data:
                if public.M('databases').where('pid=?', (pid,)).count() > 0:
                    old_link = public.M('databases').where('pid=?', (pid,)).field('id,pid,name').select()
                    for i in old_link:
                        public.M('databases').where('id=?', (i['id'],)).setField('pid', 0)

                public.M('databases').where('id=?', (sql_id,)).setField('pid', pid)
                return public.returnMsg(True, '修改成功!')
            return public.returnMsg(False, '修改失败!')
        except:
            return traceback.format_exc()

    def modify_ftp_link(self, get):
        try:
            if not hasattr(get, 'ftp_id') or not get.ftp_id:
                return public.returnMsg(False, '参数错误!')
            if not hasattr(get, 'pid') or not get.pid:
                return public.returnMsg(False, '参数错误!')
            ftp_id = get.ftp_id
            pid = get.pid
            data = public.M('ftps').where('id=?', (ftp_id,)).select()
            if type(data) != str and data:
                if public.M('ftps').where('pid=?', (pid,)).count() > 0:
                    old_link = public.M('ftps').where('pid=?', (pid,)).field('id,pid,name').select()
                    for i in old_link:
                        public.M('ftps').where('id=?', (i['id'],)).setField('pid', 0)
                public.M('ftps').where('id=?', (ftp_id,)).setField('pid', pid)
                return public.returnMsg(True, '修改成功!')
            return public.returnMsg(False, '修改失败!')
        except:
            return traceback.format_exc()
