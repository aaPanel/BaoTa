# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author:  cjxin <cjxin@bt.cn>
# -------------------------------------------------------------------

# 备份
# ------------------------------
import os, sys, re, json, shutil, psutil, time
import uuid

from sslModel.base import sslBase
import public


class main(sslBase):

    def __init__(self):
        super().__init__()
        # self.__init_data()
        self.__create_table()



    def run_fun(self,get):
        """
        @name 执行指定函数
        @param get.def_name 函数名
        @param get.dns_type dns类型
        """

        if 'fun_name' not in get:
            return public.returnMsg(False,'缺少参数 fun_name')

        if not get.fun_name in ['delete_dns_record','create_dns_record','get_dns_record','update_dns_record','set_dns_record_status', 'get_domain_list']:
            return public.returnMsg(False,'参数错误，未知的函数名')

        dns_type = False
        try:
            dns_data = self.get_dns_data(get)
            dns_type = dns_data[get.dns_id]['dns_type']
        except: pass
        if not dns_type:
            return public.returnMsg(False,'未知的dns_id')
        get.dns_type = dns_type
        try:
            res = self.func_models(get, get.fun_name)
            return res
        except Exception as e:
            return public.returnMsg(False,'执行失败:{}'.format(str(e)))


    def get_domain_list(self,get):
        """
        @name 获取域名列表
        """
        # self.__init_data()

        filter_sql = ''
        if get.get('search'):
            filter_sql += ' and domain like {}'.format("'%"+get.search+"%'")
            public.set_search_history('ssl', 'get_domain_list', get.search)
        if get.get('type_id'):
            filter_sql += " and type_id = '{}'".format(get.type_id)

        p = 1
        if 'p' in get:
            p = int(get.p)
        collback = ''
        if 'collback' in get:
            collback = get.collback
        limit = 20
        if 'limit' in get:
            limit = int(get.limit)

        # count = public.M('ssl_domains').where("dns_id not like 'cloud_id=%' {}".format(filter_sql), ()).count()
        # page_data = public.get_page(count, p, limit, collback)

        dns_data = self.get_dns_data(get)
        data = public.M('ssl_domains').field('id,domain,type_id,dns_id,endtime,ps').where("dns_id not like 'cloud_id=%' {}".format(filter_sql), ()).select()

        record_data = self.get_record_data()

        from mod.project.push import taskMod
        report_data = taskMod.main().get_task_list().get('data')
        report_data_dic = {}
        if report_data:
            report_data_dic = {i["keyword"]: i["id"] for i in report_data if i["source"] == "domain_endtime" and i["status"]}

        domain_list = []
        _data = []
        remove_ids = []
        for val in data:
            if val['domain'] in domain_list:
                remove_ids.append(str(val['id']))
                continue
            if self._is_ip(val['domain']):
                continue
            domain_list.append(val['domain'])
            val["report_id"] = report_data_dic.get(val['domain'], "") or ""

            if val['dns_id'] == '0': val['dns_id'] = ''

            val['dns'] = dns_data.get(val['dns_id'],{})
            # 获取子域名数量
            val['sbd_count'] = record_data.get(val["domain"], {}).get('info', {}).get('record_total', '-')

            if val['dns_id'] != '':
                _data.append(val)
            else:
                remove_ids.append(str(val['id']))

        count = len(_data)

        begin = (p - 1) * limit
        end = begin + limit
        _data = _data[begin:end]
        page_data = public.get_page(count, p, limit, collback)
        try:
            public.M('ssl_domains').where("id in ({})".format(",".join(remove_ids)), ()).delete()
        except Exception as e:
            print(e)

        search_history = public.get_search_history('ssl', 'get_domain_list')
        page_data.update({'data': _data, 'search_history': search_history})
        public.set_module_logs('ssl', 'get_domain_list', 1)
        return page_data


    def set_domain_ps(self,get):
        """
        @name 设置域名备注
        @param get.id 域名id
        @param get.ps 备注
        """
        id = get.id
        ps = get.ps
        res = public.M('ssl_domains').where('id=?',(id,)).setField('ps',ps)
        if not res:
            return public.returnMsg(False,'设置失败!')
        return public.returnMsg(True,'设置成功!')

    def set_domain_dns(self,get):
        """
        @name 给域名设置dns
        @param get.ids 域名id [1,2,3]
        @param get.dns_id dns_id
        """
        try:
            ids = json.loads(get.ids)
        except: pass

        if not ids:
            return public.returnMsg(False,'请选择要设置的域名!')

        dns_id = get.dns_id
        dns_data = self.get_dns_data(get)
        if dns_id not in dns_data:
            return public.returnMsg(False,'指定DNS不存在!')

        params = []
        for id in ids:
            params.append((dns_id,id))

        res = public.M('ssl_domains').executemany('update ssl_domains set dns_id=? where id=?',params)
        if type(res) != int:
            return public.returnMsg(False,'设置失败!')
        if res != len(ids):
            insert_res = public.M('ssl_domains').executemany('insert into ssl_domains (dns_id,domain) values (?,?)', params)
            return public.returnMsg(True, '设置成功，已更新 {} 条记录，新增 {} 条记录!'.format(res, insert_res))

        return public.returnMsg(True,'设置成功，已更新 {} 条记录!'.format(res))

    def set_domain_endtime(self,get):
        """
        @name 设置域名到期时间
        @param get.ids 域名id [1,2,3]
        @param get.endtime 到期时间
        """
        try:
            ids = json.loads(get.ids)
        except: pass

        if not ids:
            return public.returnMsg(False,'请选择要设置的域名!')

        endtime = get.endtime
        params = []
        for id in ids:
            params.append((endtime,id))

        res = public.M('ssl_domains').executemany('update ssl_domains set endtime=? where id=?',params)
        if type(res) != int:
            return public.returnMsg(False,'设置失败!')

        return public.returnMsg(True,'设置成功，已更新 {} 条记录!'.format(res))

    def set_domain_type(self,get):
        """
        @设置域名到期时间
        @param get.ids 域名id [1,2,3]
        @param get.type_id 类型id
        """
        try:
            ids = json.loads(get.ids)
        except: pass

        if not ids:
            return public.returnMsg(False,'请选择要设置的域名!')

        type_id = get.type_id
        params = []
        for id in ids:
            params.append((type_id,id))

        res = public.M('ssl_domains').executemany('update ssl_domains set type_id=? where id=?',params)
        if type(res) != int:
            return public.returnMsg(False,'设置失败!')

        return public.returnMsg(True,'设置成功，已更新 {} 条记录!'.format(res))


    def get_domain_type(self,get):
        """
        @name 获取域名类型
        """
        data = [{'type_id': 0, 'name': '默认分组'}]
        try:
            sfile = '{}/data/domains_type.json'.format(public.get_panel_path())
            data.extend(json.loads(public.readFile(sfile)))
        except:pass

        return data

    def add_domain_type(self,get):
        """
        @name 添加域名分类
        @param get.name 分类名称
        @param get.type_id 分类类型

        """
        sfile = '{}/data/domains_type.json'.format(public.get_panel_path())
        try:
            data = json.loads(public.readFile(sfile))
        except:
            data = []
        type_id = str(uuid.uuid4().hex)
        if 'type_id' in get:
            type_id = get.type_id
        for i in data:
            if get.name == i["name"] or get.name == '默认分组':
                return public.returnMsg(False, '此类型已存在')

        data.append({'name':get.name,'type_id':type_id})
        public.writeFile(sfile,json.dumps(data))
        return public.returnMsg(True,'添加成功')
    
    def del_domain_type(self, get):
        sfile = '{}/data/domains_type.json'.format(public.get_panel_path())
        try:
            data = json.loads(public.readFile(sfile))
            i = 0
            while i < len(data):
                if data[i]["type_id"] == get.type_id:
                    del data[i]
                    break
                i += 1
            public.writeFile(sfile, json.dumps(data))
            return public.returnMsg(True, '删除成功')
        except:
            return public.returnMsg(True, '删除失败')
        

    # def __init_data(self):
    #     """
    #     @name 同步数据
    #     """
    #     # 检查表是否存在
    #     self.__create_table()
    #
    #     # 根据文件修改时间判断是否要同步
    #     check_path = "/www/server/panel/data/sync_domains.pl"
    #     m_time = str(os.stat("/www/server/panel/data/db/site.db").st_mtime)
    #     check_path_docker = "/www/server/panel/data/sync_domains_docker.pl"
    #     m_time_docker = str(os.stat("/www/server/panel/data/db/docker.db").st_mtime)
    #     if os.path.exists(check_path) and os.path.exists(check_path_docker):
    #         if m_time == public.readFile(check_path) and m_time_docker == public.readFile(check_path_docker):
    #             return
    #     public.writeFile(check_path, m_time)
    #     public.writeFile(check_path_docker, m_time)
    #
    #     # 获取手动删除的域名
    #     del_path = '{}/config/del_domains.pl'.format(public.get_panel_path())
    #     try:
    #         skip_domains = json.loads(public.readFile(del_path))
    #     except:
    #         skip_domains = []
    #
    #     root_domains = {i['domain'] for i in public.M('ssl_domains').field('domain').select()}
    #     site_domains = set()
    #     for i in public.M('domain').field('name').select():
    #         if not self._is_ip(i['name']):
    #             site_domains.add(self.extract_zone(i['name'])[0])
    #
    #     docker_site_domains = set()
    #     for i in public.M('docker_domain').field('name').select():
    #         if not self._is_ip(i['name']):
    #             docker_site_domains.add(self.extract_zone(i['name'])[0])
    #     add_domains = (site_domains | docker_site_domains) - root_domains - set(skip_domains)
    #     # del_domains = root_domains - (docker_site_domains | site_domains)
    #
    #     # 添加域名
    #     for domain in add_domains:
    #         public.M('ssl_domains').add('domain,dns_id,type_id,endtime,ps', (domain, 0, 0, 0, ''))
    #
    #     # 删除域名
    #     # for domain in del_domains:
    #     #     public.M('ssl_domains').where("domain=?", (domain,)).delete()

    def del_domains(self, get):
        """
        @name 删除域名
        @param get.domains 域名列表，以逗号分隔
        """
        domains = get.domains.split(',')
        try:
            public.M('ssl_domains').where("domain in ('{}')".format("','".join(domains)), ()).delete()
            path = '{}/config/del_domains.pl'.format(public.get_panel_path())
            try:
                del_domains = json.loads(public.readFile(path))
                del_domains.extend(domains)
                public.writeFile(path, json.dumps(del_domains))
            except:
                public.writeFile(path, json.dumps(domains))
            return public.returnMsg(True, '删除成功')
        except:
            return public.returnMsg(False, '删除失败')

    # # 手动同步域名
    # def sync_domains(self, get):
    #     """
    #     @name 手动同步域名
    #     """
    #     root_domains = {i['domain'] for i in public.M('ssl_domains').field('domain').select()}
    #     site_domains = set()
    #     for i in public.M('domain').field('name').select():
    #         if not self._is_ip(i['name']):
    #             site_domains.add(self.extract_zone(i['name'])[0])
    #
    #     docker_site_domains=set()
    #     for i in public.M('docker_domain').field('name').select():
    #         if not self._is_ip(i['name']):
    #             docker_site_domains.add(self.extract_zone(i['name'])[0])
    #
    #     add_domains = (site_domains | docker_site_domains) - root_domains
    #     del_domains = root_domains - (docker_site_domains | site_domains)
    #
    #     # 添加域名
    #     for domain in add_domains:
    #         public.M('ssl_domains').add('domain,dns_id,type_id,endtime,ps', (domain, 0, 0, 0, ''))
    #     # 删除域名
    #     for domain in del_domains:
    #         public.M('ssl_domains').where("domain=?", (domain,)).delete()
    #     # 删除文件
    #     try:
    #         os.remove('{}/config/del_domains.pl'.format(public.get_panel_path()))
    #     except: pass
    #     return public.returnMsg(True, '同步成功')

    @staticmethod
    def _is_ip(data: str):
        import ipaddress
        try:
            ipaddress.ip_address(data)
        except:
            return False
        return True

    def __create_table(self):
        """
        @name 检查表是否存在
        """
        public.check_table('ssl_domains',"""CREATE TABLE IF NOT EXISTS `ssl_domains` (
	`id` INTEGER PRIMARY KEY AUTOINCREMENT,
	`domain` TEXT,
	`dns_id` TEXT,
	`type_id` INTEGER,
	`endtime` INTEGER,
	`ps` TEXT
)
""")

    def check_table(self):
        self.__create_table()

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

        if 'dns_type' not in get:
            raise Exception('缺少参数 dns_type')

        sfile = '{}/class/sslModel/{}Model.py'.format(public.get_panel_path(),get.dns_type)
        if not os.path.exists(sfile):
            raise Exception('模块文件{}不存在'.format(sfile))
        obj_main = self.get_objectModel()

        args = public.dict_obj()
        args['data'] = get
        args['mod_name'] = get.dns_type
        args['def_name'] = def_name

        return obj_main.model(args)

    def get_domain_dns_config(self, get):
        # self.__init_data()

        dns_data = self.get_dns_data(get)
        root_data = public.M('ssl_domains').field('id,domain,dns_id').select()
        where_sql = '1=1'
        param = []
        if 'domain_name' in get:
            where_sql += " AND name like ?"
            param.append('%{}%'.format(get.domain_name))
        if 'site_id' in get:
            where_sql += " AND pid in ({})".format(get.site_id)
            data = public.M('domain').where(where_sql, param).field('name,pid as site_id').select()
        elif 'docker_site_id' in get:
            where_sql += " AND pid in ({})".format(get.docker_site_id)
            data = public.M('docker_domain').where(where_sql, param).field('name,pid as site_id').select()
        else:
            data = public.M('domain').where(where_sql, param).field('name,pid as site_id').select() + public.M('docker_domain').where(where_sql, param).field('name,pid as site_id').select()
        for i in data:
            root, sub_domain, _ = self.extract_zone(i['name'])
            i["status"] = 0
            i["domain_id"] = root
            for j in root_data:
                if j['domain'] == root:
                    i["domain_id"] = j["id"]
                    i["status"] = 1 if j["dns_id"].find("cloud_id=")!=-1 or j["dns_id"] in dns_data.keys()else 0
                    break
        if 'auto_wildcard' in get and get.auto_wildcard == '1':
            new_data = []
            for i in data:
                root, _, _ = self.extract_zone(i['name'])
                # 创建新对象以避免修改原数据
                new_item = i.copy()
                new_item['name'] = root
                if new_item not in new_data:
                    new_data.append(new_item)

                # 处理通配符域名
                wildcard_item = new_item.copy()
                wildcard_item['name'] = "*." + root
                if wildcard_item not in new_data:
                    new_data.append(wildcard_item)
            data = new_data
        return data

    def get_site_list(self, get):
        # 自动部署不兼容docker网站
        # return public.M('sites').field("name,id,'site_id' as type").select() + public.M('docker_sites').field("name,id,'docker_site_id' as type").select()
        return public.M('sites').field("name,id,'site_id' as type").select()

    def create_report_task(self, get):
        from mod.base.push_mod import manager

        sender_lsit = get.sender.split(",")
        task_data = {"task_data":{"tid":"70","type":"domain_endtime","title":"域名到期","status":True,"count":0,"interval":600,"project":get.domain,"cycle":int(get.cycle)},"sender":sender_lsit,"number_rule":{"day_num":0,"total":int(get.total)},"time_rule":{"send_interval":0,"time_range":[0,86399]}}
        get.template_id = "70"
        get.task_data = json.dumps(task_data)

        return manager.PushManager().set_task_conf(get)

    def remove_report_task(self, get):
        from mod.base.push_mod import manager
        return manager.PushManager().remove_task_conf(get)

    def add_dns_value_by_domain(self, domain, dns_value, record_type="TXT", is_let_txt=False, mx=10):
        root, sub, subd = self.extract_zone(domain, is_let_txt)
        domain_name = subd+'.'+root if is_let_txt else domain
        try:
            data = public.M('ssl_domains').field('dns_id').where("domain=?", (root,)).select()
            dns_id = data[0]['dns_id']
        except:
            dns_id = ''
        if dns_id.find("cloud_id=") != -1:
            domain_id = dns_id.split("cloud_id=")[1]
            from mod.project.domain import domainMod
            domain_obj = domainMod.main()
            rep = domain_obj.request({"url":"/api/v1/dns/record/create","domain_type":1,"domain_id":domain_id,"record":subd if is_let_txt else sub,"value":dns_value,"type":record_type,"mx":mx,"ttl":600,"remark":"","view_id":0})
            if not rep["status"] and '记录已存在' not in rep["msg"]:
                public.print_log(rep)
                raise Exception("设置解析记录失败：{}".format(rep["msg"]))
            else:
                return rep
        else:
            for dns_config in self.get_dns_data(public.dict_obj()).values():
                if root in dns_config.get("domains", []) or str(dns_id) == dns_config["id"]:
                    args = {
                        "fun_name": "create_dns_record",
                        "dns_id": dns_id,
                        "domain_dns_value": dns_value,
                        "record_type": record_type,
                        "domain_name": domain_name,
                        "mx": mx,
                    }
                    _return = self.run_fun(public.to_dict_obj(args))
                    if not _return["status"] and '记录已存在' not in _return["msg"]:
                        raise Exception("设置解析记录失败：{}".format(_return["msg"]))
                    else:
                        return _return
        raise Exception("设置解析记录失败：没有找到域名为{}的有效的DNS API密钥信息".format(domain))

    def get_dns_value_by_domain(self, domain, record_type="TXT", is_let_txt=False):
        root, sub, subd = self.extract_zone(domain, is_let_txt)
        domain_name = subd + '.' + root if is_let_txt else domain
        try:
            data = public.M('ssl_domains').field('dns_id').where("domain=?", (root,)).select()
            dns_id = data[0]['dns_id']
        except:
            dns_id = ''
        if dns_id.find("cloud_id=") != -1:
            domain_id = dns_id.split("cloud_id=")[1]
            from mod.project.domain import domainMod
            domain_obj = domainMod.main()
            record_data = domain_obj.request({"url": "/api/v1/dns/record/list", "domain_type": 1, "domain_id": domain_id, "searchKey": "record", "searchValue": subd if is_let_txt else sub})
            _return = []
            for record in record_data["data"].get("data", []):
                if record["type"] == record_type and record["record"] == (subd if is_let_txt else sub):
                    _return.append(record["record_id"])
            return _return, dns_id
        else:
            for dns_config in self.get_dns_data(public.dict_obj()).values():
                if root in dns_config.get("domains", []) or str(dns_id) == dns_config["id"]:
                    args = {
                        "fun_name": "get_dns_record",
                        "dns_id": dns_id,
                        "domain_name": domain,
                    }
                    record_data = self.run_fun(public.to_dict_obj(args))
                    _return = []
                    for record in record_data.get("list", []):
                        if record["type"] == record_type and record["name"] == domain_name:
                            _return.append(record["RecordId"])
                    return _return, dns_id
        return [], ""

    def del_dns_value_by_domain(self, domain, record_type="TXT", is_let_txt=False):
        ids, dns_id = self.get_dns_value_by_domain(domain, record_type, is_let_txt)
        if dns_id.find("cloud_id=") != -1:
            domain_id = dns_id.split("cloud_id=")[1]
            from mod.project.domain import domainMod
            domain_obj = domainMod.main()
            for record_id in ids:
                rep = domain_obj.request({"url": "/api/v1/dns/record/delete", "domain_type": 1, "domain_id": domain_id, "record_id": record_id})
                if not rep["status"]:
                    raise Exception("删除解析记录失败：{}".format(rep["msg"]))
            return
        else:
            for record_id in ids:
                args = {
                    "fun_name": "delete_dns_record",
                    "dns_id": dns_id,
                    "RecordId": record_id,
                    "domain_name": domain,
                }
                _return = self.run_fun(public.to_dict_obj(args))
                if not _return["status"]:
                    raise Exception("删除解析记录失败：{}".format(_return["msg"]))

    def get_sub_domains(self, get):
        import socket
        root_domain = get.root_domain
        domains = public.M('domain').where("name like ?", ('%'+root_domain,)).field('name,pid').select()
        for domain in domains:
            site_data = public.M('sites').where("id = ?", (domain['pid'],)).find()
            domain.update({"site_name": site_data['name']})
            domain.update({"record_a": socket.gethostbyname(domain['name'])})
        return domains

    def add_domain(self, get):
        domain_name = get.domain_name
        dns_id = get.dns_id

        # 检查是否为顶级域名
        root, sub, _ = self.extract_zone(domain_name)
        if sub != '':
            return public.returnMsg(False, '只能添加顶级域名')

        data = public.M('ssl_domains').field('id').where("domain=?", (domain_name,)).select()
        if data:
            return public.returnMsg(False, '域名已存在')
        public.M('ssl_domains').add('domain,dns_id,type_id,endtime,ps', (domain_name, dns_id, 0, 0, ''))
        return public.returnMsg(True, '添加成功')



