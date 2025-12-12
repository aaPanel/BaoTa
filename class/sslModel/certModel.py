import os, sys, re, json, shutil, psutil, time
import uuid
from datetime import datetime
from hashlib import md5

from sslModel.base import sslBase
import public
from panelAes import AesCryptPy3
from ssl_manage import SSLManger


class main(sslBase):

    def __init__(self):
        self.__init_data()

    def __init_data(self):
        self.__create_table()
        self.check_and_add_ps_column()

    def __create_table(self):
        """
        @name 检查表是否存在
        """
        public.check_table('ssl_info',
                           "CREATE TABLE IF NOT EXISTS 'ssl_info' ("
                           "'id' INTEGER PRIMARY KEY AUTOINCREMENT, "
                           "'group_id' INTEGER NOT NULL DEFAULT 0, "
                           "'hash' TEXT NOT NULL UNIQUE, "
                           "'path' TEXT NOT NULL, "
                           "'dns' TEXT NOT NULL, "
                           "'subject' TEXT NOT NULL, "
                           "'info' TEXT NOT NULL DEFAULT '', "
                           "'cloud_id' INTEGER NOT NULL DEFAULT -1, "
                           "'not_after' TEXT NOT NULL, "
                           "'use_for_panel' INTEGER NOT NULL DEFAULT 0, "
                           "'use_for_site' TEXT NOT NULL DEFAULT '[]', "
                           "'auth_info' TEXT NOT NULL DEFAULT '{}', "
                           "'ps' TEXT DEFAULT '', "  # 新增字段ps，用于存储备份说明
                           "'create_time' INTEGER NOT NULL DEFAULT (strftime('%s'))"
                           ");"
                           )

    def check_and_add_ps_column(self):
        try:
            public.M('ssl_info').field('group_id').select()
        except Exception as e:
            if "no such column: group_id" in str(e):
                try:
                    public.M('ssl_info').execute("ALTER TABLE 'ssl_info' ADD 'group_id' INTEGER NOT NULL DEFAULT 0", ())
                except Exception as e:
                    pass

    def get_cert_group(self, get):
        """
        @name 获取证书分组
        """
        data = []
        try:
            sfile = '{}/data/cert_group.json'.format(public.get_panel_path())
            if not os.path.isfile(sfile):
                data = [{'name': '默认分组', 'group_id': '0', 'ssl': {"1": [], "2": [], "3": []}}]
                public.writeFile(sfile, json.dumps(data))
                return data
            data = json.loads(public.readFile(sfile))
            for i in data:
                if not i.get('ssl'):
                    i['ssl'] = {"1": [], "2": [], "3": []}
            public.writeFile(sfile, json.dumps(data))
        except:
            pass

        return data

    def add_cert_group(self, get):
        """
        @name 添加证书分组
        """
        sfile = '{}/data/cert_group.json'.format(public.get_panel_path())
        try:
            data = json.loads(public.readFile(sfile))
        except:
            data = []

        for i in data:
            if get.name == i["name"]:
                return public.returnMsg(False, '此分组已存在')
        data.append({'name': get.name, 'group_id': uuid.uuid4().hex, 'ssl': {"1": [], "2": [], "3": []}})
        public.writeFile(sfile, json.dumps(data))
        return public.returnMsg(True, '添加成功')

    def del_cert_group(self, get):

        sfile = '{}/data/cert_group.json'.format(public.get_panel_path())
        try:
            data = json.loads(public.readFile(sfile))
            i = 0
            while i < len(data):
                if data[i]["group_id"] == str(get.group_id):
                    del data[i]
                    break
                i += 1
            public.writeFile(sfile, json.dumps(data))
            return public.returnMsg(True, '删除成功')
        except:
            return public.returnMsg(False, '删除失败')

    def set_cert_group(self, get):
        sfile = '{}/data/cert_group.json'.format(public.get_panel_path())
        try:
            ids = json.loads(get.ids)
        except:
            return public.returnMsg(False, "请选择证书")
        data = self.get_cert_group(get)
        for i in data:
            for j in ids:
                while str(j['id']) in i['ssl'][j['type']]:
                    i['ssl'][j['type']].remove(str(j['id']))
                if get.group_id == i['group_id']:
                    i['ssl'][j['type']].append(str(j['id']))

        public.writeFile(sfile, json.dumps(data))
        return public.returnMsg(True, '设置成功')

    def get_group_data(self, get):
        data = self.get_cert_group(get)
        type1 = {}
        type2 = {}
        type3 = {}
        for i in data:
            if not i.get('ssl'):
                continue
            type1.update({j: i['name'] for j in i['ssl']["1"] if i['ssl'].get("1")})
            type2.update({j: i['name'] for j in i['ssl']["2"] if i['ssl'].get("2")})
            type3.update({j: i['name'] for j in i['ssl']["3"] if i['ssl'].get("3")})
        return {"1": type1, "2": type2, "3": type3}

    def get_cert_to_site(self, pure=False):
        """
        获取证书部署网站
        """
        import acme_v2
        from mod.base.web_conf.ssl import RealSSLManger
        from datalistModel import sitesModel
        acme = acme_v2.acme_v2()
        sites_model = sitesModel.main()
        hash_data = acme.get_exclude_hash(public.to_dict_obj({}))
        hash_dic = {}
        hash_dic.update(hash_data.get("exclude_hash") or {})
        hash_dic.update(hash_data.get("exclude_hash_let") or {})

        # 获取所有网站
        site_data = public.M('sites').field('name,project_type').select()
        path = "/www/server/panel/vhost/cert/"
        data = {'cancel': []} if not pure else {}
        for cert in site_data:
            if cert['project_type'] in ['PHP', 'proxy', 'WP2']:
                if sites_model.get_site_ssl_info(cert['name']) == -1:
                    continue
            else:
                if not RealSSLManger('{}_'.format(cert['project_type'].lower())).get_site_ssl_info(cert['name']):
                    continue
            cert_name = cert["name"]
            cert_path = path + cert_name
            cert_index = ''
            if os.path.exists(cert_path + '/fullchain.pem'):
                try:
                    cert_index = self._hash(cert_filename=cert_path + '/fullchain.pem')
                except:
                    continue
                if not pure:
                    for k, v in hash_dic.items():
                        if v == cert_index:
                            # cert_index = k
                            if k not in data.keys():
                                data.update({k: [cert_name]})
                            else:
                                data[k].append(cert_name)
                            break
            if cert_index:
                if cert_index not in data.keys():
                    data.update({cert_index: [cert_name]})
                else:
                    data[cert_index].append(cert_name)
        return data

    def get_cert_brand(self):
        path = '{}/data/cert_brand.json'.format(public.get_panel_path())
        if not os.path.exists(path):
            data = {
                "comodo-positivessl-wildcard": "Sectigo RSA Domain Validation Secure Server CA",
                "comodo-positivessl": "Sectigo RSA Domain Validation Secure Server CA",
            }
            public.writeFile(path, json.dumps(data))
            return data
        return json.loads(public.readFile(path))

    def set_cert_brand(self, brand):
        path = '{}/data/cert_brand.json'.format(public.get_panel_path())
        data = self.get_cert_brand()
        data.update(brand)
        public.writeFile(path, json.dumps(data))


    def get_cert_list(self, get):
        """
        获取证书列表
        """
        import panelSSL

        search = get.get('search', '')
        group_id = get.get('group_id', '')
        status_id = get.get('status_id', '')
        search_domain = get.get('search_domain', '')
        cert_type = get.get('cert_type', '0')
        if status_id:
            status_id = int(status_id)
        if search:
            public.set_search_history('ssl', 'get_cert_list', search)

        group_data = self.get_cert_group(get)
        group_name_dic = self.get_group_data(get)
        group_name = None
        ssl_ids = None
        exclude_ids = {'1': [], '2': [], '3': []}

        for i in group_data:
            if str(i['group_id']) == str(group_id):
                group_name = i["name"]
                ssl_ids = i["ssl"]
            else:
                exclude_ids['1'].extend(i["ssl"]['1'])
                exclude_ids['2'].extend(i["ssl"]['2'])
                exclude_ids['3'].extend(i["ssl"]['3'])


        # 找不到分组直接置空
        if not ssl_ids and group_id:
            return {}

        p = 1
        if 'p' in get:
            p = int(get.p)
        collback = ''
        if 'collback' in get:
            collback = get.collback
        limit = 999999999
        if 'limit' in get:
            limit = int(get.limit)

        # 部署网站
        use_site_dic = self.get_cert_to_site()
        # 证书夹排除数据
        exclude_hash = panelSSL.panelSSL().get_exclude_hash(get)
        # 告警数据
        report_data_dic = self.get_report_task()

        format_time_strs = ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S")
        from datetime import datetime
        today_time = datetime.today().timestamp()

        cancel_list = []
        if exclude_hash.get('exclude_hash'):
            cancel_list.extend(exclude_hash['exclude_hash'].values())
        if exclude_hash.get('exclude_hash_let'):
            cancel_list.extend(exclude_hash['exclude_hash_let'].values())

        will_num = 0
        end_num = 0
        data = []

        if cert_type in ("4", "0"):
            # 证书夹数据
            cert_data = []
            if status_id != 0:
                cert_data = public.M('ssl_info').field(
                    'id,hash,dns,cloud_id,not_after,auth_info,info,ps,group_id'
                ).select()

            for cert in cert_data:
                if not isinstance(cert,dict):
                    continue
                if cert['hash'] in cancel_list:
                    continue
                end_time = 90
                for f_str in format_time_strs:

                    try:
                        end_time = int(
                            (datetime.strptime(cert["not_after"], f_str).timestamp() - today_time) / (60 * 60 * 24)
                        )
                    except Exception as e:
                        continue

                cert["sort"] = cert['endDay'] = end_time

                if 0 < cert['endDay'] <= 30:
                    will_num += 1
                elif cert['endDay'] <= 0:
                    end_num += 1

                if status_id == 1 and cert['endDay'] <= 0:
                    continue
                elif status_id == 2 and (cert['endDay'] > 30 or cert['endDay'] <= 0):
                    continue
                elif status_id == 3 and (cert['endDay'] > 0):
                    continue

                if ssl_ids and str(cert['id']) not in ssl_ids['3']:
                    if str(group_id) == '0':
                        if str(cert['id']) in exclude_ids['3']:
                            continue
                    else:
                        continue
                cert['group_name'] = group_name if group_name else group_name_dic["3"].get(str(cert['id']), "默认分组")
                info = json.loads(cert["info"])
                cert['title'] = info['issuer']

                cert["domainName"] = json.loads(cert["dns"])
                domainName = ",".join(cert['domainName'] or [])
                if search.lower() not in domainName.lower() and search.lower() not in cert['title'].lower():
                    continue
                if search_domain and search_domain not in cert["domainName"]:
                    continue
                cert["auth_info"] = json.loads(cert["auth_info"])

                cert['type'] = "3"
                cert["use_site"] = use_site_dic.get(cert["hash"], [])
                cert["ssl_id"] = cert["hash"]
                cert["report_id"] = report_data_dic.get(cert['ssl_id'], "") or ""
                data.append(cert)

        if cert_type in ("1", "0"):
            brand_data = self.get_cert_brand()

            # 商用证书订单数据
            import ssl_info
            try:
                _cert_data = panelSSL.panelSSL().get_order_list(get)
            except:
                _cert_data = []
            if not isinstance(_cert_data, list):
                _cert_data = []
            for cert in _cert_data:
                if cert['endDate']:
                    cert['endDay'] = int(
                        (cert['endDate'] - today_time) / (60 * 60 * 24)
                    )
                if 0 < cert['endDay'] <= 30:
                    will_num += 1
                elif cert['endDay'] <= 0 and cert['orderStatus'] in ('COMPLETE', "EXPIRED", 5):
                    end_num += 1
                if status_id == 0 and cert['orderStatus'] not in ("PENDING", "", None, 0, 1, 2, 3, 4, 9, 10):
                    continue
                elif status_id == 1 and (cert['endDay'] <= 0 or cert['orderStatus'] not in ('COMPLETE', 5, 6, 7, 8, 11, 12)):
                    continue
                elif status_id == 2 and ((cert['endDay'] > 30 or cert['endDay'] <= 0) or cert['orderStatus'] not in ('COMPLETE', 5, 6, 7, 8, 11, 12)):
                    continue
                elif status_id == 3 and (cert['endDay'] > 0 or cert['orderStatus'] not in ('COMPLETE', "EXPIRED", 5, 6, 7, 8, 11, 12)):
                    continue

                cert['id'] = cert['oid']
                if ssl_ids and str(cert['id']) not in ssl_ids['1']:
                    if str(group_id) == '0':
                        if str(cert['id']) in exclude_ids['1']:
                            continue
                    else:
                        continue
                if cert['orderStatus'] in ('COMPLETE', "EXPIRED"):
                    title = brand_data.get(cert['code'], "")
                    if title:
                        cert["title"] = title
                    else:
                        # 证书信息
                        get.oid = cert['oid']
                        certInfo = panelSSL.panelSSL().get_order_find(get)
                        if certInfo['certificate'] and certInfo['caCertificate']:
                            _info = ssl_info.ssl_info().load_ssl_info_by_data(certInfo['certificate']+"\n"+certInfo['caCertificate'])
                            if _info and _info.get('issuer'):
                                cert["title"] = _info['issuer']
                                self.set_cert_brand({cert['code']: title})

                cert['group_name'] = group_name if group_name else group_name_dic["1"].get(str(cert['id']), "默认分组")
                domainName = ",".join(cert['domainName'] or [])
                if search.lower() not in domainName.lower() and search.lower() not in cert["title"].lower():
                    continue
                # if search_domain and (search_domain not in cert["domainName"] or not cert['domainName']):
                #     continue
                cert['type'] = "1"
                cert["use_site"] = use_site_dic.get(str(cert["oid"]), [])
                cert["ssl_id"] = str(cert["oid"])
                cert["report_id"] = report_data_dic.get(cert['ssl_id'], "") or ""
                # if cert["orderStatus"] in ("", None):
                #     cert["sort"] = 99998
                # elif cert["orderStatus"] in ("PENDING", 0, 1, 2, 3, 4, 9, 10):
                #     cert["sort"] = 99999
                cert['download_status'] = True if cert['orderStatus'] == 'COMPLETE' and cert['status'] == 1 else False
                # cert["title"] = title
                data.append(cert)

        if cert_type in ("2", "0"):
            # 测试证书订单数据
            try:
                test_cert_data = panelSSL.panelSSL().GetOrderList(get)
            except:
                test_cert_data = {}
            for cert in test_cert_data.get('data', []):

                try:
                    end_time = int(
                        (cert["endtime"]/1000 - today_time) / (60 * 60 * 24)
                    )
                except Exception as e:
                    end_time = 90
                cert['endDay'] = end_time

                if 0 < cert['endDay'] <= 30 and cert['stateCode'] == "COMPLETED":
                    will_num += 1
                elif cert['endDay'] <= 0 and cert['stateCode'] == "COMPLETED":
                    end_num += 1

                if status_id == 0 and cert['stateCode'] != "WF_DOMAIN_APPROVAL":
                    continue
                elif status_id == 1 and (cert['endDay'] <= 0 or cert['stateCode'] != "COMPLETED"):
                    continue
                elif status_id == 2 and ((cert['endDay'] > 30 or cert['endDay'] <= 0) or cert['stateCode'] != "COMPLETED"):
                    continue
                elif status_id == 3 and (cert['endDay'] > 0 or cert['stateCode'] != "COMPLETED"):
                    continue

                cert['ssl_id'] = str(cert['ssl_id'])
                cert['id'] = cert['ssl_id']
                if ssl_ids and str(cert['id']) not in ssl_ids['2']:
                    if str(group_id) == '0':
                        if str(cert['id']) in exclude_ids['2']:
                            continue
                    else:
                        continue

                cert['group_name'] = group_name if group_name else group_name_dic["2"].get(str(cert['id']), "默认分组")
                cert['title'] = "TrustAsia RSA DV TLS CA G2"
                if search.lower() not in cert["authDomain"].lower() and search.lower() not in cert['title'].lower():
                    continue

                cert['domainName'] = [cert['authDomain']]
                # if search_domain and search_domain not in cert["domainName"]:
                #     continue
                cert['type'] = "2"
                cert["use_site"] = use_site_dic.get(cert["partnerOrderId"], [])
                cert["report_id"] = report_data_dic.get(cert['ssl_id'], "") or ""
                cert["sort"] = -99999999
                if cert['stateCode'] != 'COMPLETED':
                    del cert['endDay']
                    # cert["sort"] = 99999
                data.append(cert)

        if cert_type in ("3", "0"):
            # 计划任务
            crontab_data = self.get_crontab()
            # let's encrypt证书订单数据
            import acme_v2
            let_cert_data = acme_v2.acme_v2().get_order_list(get)
            for cert in let_cert_data:
                if 0 < cert['endDay'] <= 30:
                    will_num += 1
                elif cert['endDay'] <= 0:
                    end_num += 1
                # 状态
                if status_id == 0 and (cert['status'] != "pending" or cert['endDay'] <= 0):
                    continue
                elif status_id == 1 and (cert['endDay'] <= 0 or cert['status'] == "pending"):
                    continue
                elif status_id == 2 and (cert['endDay'] > 30 or cert['endDay'] <= 0):
                    continue
                elif status_id == 3 and (cert['endDay'] > 0):
                    continue
                # 搜索
                cert['title'] = "let's Encrypt"
                cert['domainName'] = cert['domains']
                # if search_domain and search_domain not in cert["domainName"]:
                #     continue
                domainName = ",".join(cert['domainName'] or [])
                if search.lower() not in domainName.lower() and search.lower() not in cert["title"].lower():
                    continue

                if ssl_ids and str(cert['index']) not in ssl_ids['3']:
                    if str(group_id) == '0':
                        if str(cert['index']) in exclude_ids['3']:
                            continue
                    else:
                        continue

                cert['type'] = "3"
                cert['order_status'] = cert['status']
                cert['order_status_nm'] = cert['status']
                if cert['status'] == 'pending':
                    cert['order_status_nm'] = '待验证'
                    if cert.get('auth_tag'):
                        cert['status'] = 'invalid'
                        cert['order_status'] = 'invalid'
                        cert['order_status_nm'] = '验证失败'
                elif cert['status'] == 'valid':
                    cert['order_status_nm'] = '已完成'

                cert['group_name'] = group_name if group_name else group_name_dic["3"].get(str(cert['index']), "默认分组")
                cert["ssl_id"] = cert["index"]
                cert["id"] = cert["index"]
                cert["report_id"] = report_data_dic.get(cert['ssl_id'], "") or ""
                cert["use_site"] = use_site_dic.get(str(cert["index"]), [])
                cert["cloud_id"] = 1
                cert['crontab_id'] = -1
                for crontab in crontab_data:
                    if not crontab['sBody']:
                        continue
                    if cert['index'] in crontab['sBody']:
                        cert['crontab_id'] = crontab['id']
                        try:
                            renew_data = json.loads(public.readFile("{}/config/letsencrypt_auto_renew.json".format(public.get_panel_path())))
                        except:
                            renew_data = {}
                        cert['crontab_data'] = renew_data.get(str(cert['index']), {"status": 1, "error_msg": ""})
                        break
                cert["sort"] = cert['endDay']
                if cert['status'] == 'pending' and cert['endDay'] > 0:
                    cert["sort"] = 99999
                data.append(cert)

        reverse = True
        sort = 'sort'
        if status_id == 2:
            sort = 'endDay'
            reverse = False
        data = sorted(data, key=lambda k: k.get(sort, 0) or 0, reverse=reverse)

        count = len(data)
        start = (p - 1) * limit
        end = start + limit
        if end > count:
            end = count

        search_history = public.get_search_history('ssl', 'get_cert_list')
        page_data = public.get_page(count, p, limit, collback)
        page_data.update({"data": data[start: end], 'search_history': search_history, 'will_num': will_num, 'end_num': end_num})
        return page_data

    def get_cert_list_to_push(self, get):
        items = [
            {
                "title": "{} | {}".format(i["title"], ",".join(i.get("domainName", []) or "无")),
                "value": i["ssl_id"]
            }
            for i in self.get_cert_list(public.to_dict_obj({"status_id": 1}))['data'] if i.get("endDay")
        ]
        items.insert(0, {
              "title": "所有证书",
              "value": "all"
            })
        return items

    def remove_cloud_cert(self, get):
        ssl_id = None
        ssl_hash = None
        index = None
        local = False
        cloud = False
        force = False
        try:
            if "ssl_id" in get:
                ssl_id = int(get.ssl_id)
            if "ssl_hash" in get:
                ssl_hash = get.ssl_hash.strip()
            if "index" in get:
                index = get.index.strip()

            if "local" in get and get.local.strip() in ("1", 1, True, "true"):
                local = True
            if "cloud" in get and get.cloud.strip() in ("1", 1, True, "true"):
                cloud = True
            # if "force" in get and get.force.strip() in ("1", 1, True, "true"):
            #     force = True

        except (ValueError, AttributeError, KeyError):
            return public.ReturnMsg(False, "参数错误")
        try:
            finish_list = []
            if get.get("oid"):
                import panelSSL
                finish_list = panelSSL.panelSSL().batch_soft_release(public.to_dict_obj({"oid": get.oid}))['finish_list']
            import acme_v2
            _return = acme_v2.acme_v2()._delete_order(public.to_dict_obj({"index": index, "ssl_hash": ssl_hash, "local": local, "cloud": cloud, "force": force}))
            _return['finish_list'].extend(finish_list)
            return _return
        except ValueError as e:
            return public.ReturnMsg(status=False, msg=str(e))
        except Exception as e:
            return public.ReturnMsg(status=False, msg="操作错误：" + str(e))

    def del_site_cert(self, ssl_hash, no_site_list):
        import panelSite
        if not ssl_hash:
            return
        path = "/www/server/panel/vhost/cert"
        for cert_path in os.listdir(path):
            try:
                cert_hash = self._hash('{}/{}/fullchain.pem'.format(path, cert_path))
            except:
                continue
            if cert_hash == ssl_hash:
                if cert_path in no_site_list:
                    panelSite.panelSite().CloseSSLConf(public.to_dict_obj({"siteName": cert_path}))
                shutil.rmtree('{}/{}'.format(path, cert_path))

    def remove_cert(self, ssl_id=None, ssl_hash=None, local: bool = False, cloud: bool = False, force=False):

        target = self.find_ssl_info(ssl_id=ssl_id, ssl_hash=ssl_hash)
        if not target:
            return None

        if local:
            hash_dic = self.get_cert_to_site()
            no_site_list = hash_dic.get(target["hash"], [])
            if no_site_list and not force:
                raise ValueError("证书正在被网站【{}】使用，请关闭这些网站的SSL或将这些网站配置成其他的证书后再删除".format(",".join(no_site_list)))
            if os.path.exists(target["path"]):
                shutil.rmtree(target["path"])
            self._remove_ssl_from_local(target["hash"])  # 把ssl下的也删除
            # 删除cert
            self.del_site_cert(target["hash"], no_site_list)
            public.M('ssl_info').delete(id=target["id"])

        if target["cloud_id"] != -1 and cloud:
            _, _, user_info = self._get_cbc_key_and_iv(with_uer_info=True)
            if user_info is None:
                raise ValueError('面板未登录，无法上传云端!')
            url = "https://www.bt.cn/api/Cert_cloud_deploy/del_cert"
            try:
                res_text = public.httpPost(url, {
                    "cert_id": target["cloud_id"],
                    "hashVal": target["hash"],
                    "uid": user_info["uid"],
                    "access_key": user_info["access_key"],
                    "serverid": user_info["serverid"],
                })
                res_data = json.loads(res_text)
                if res_data["status"] is False:
                    return res_data
            except:
                if local:
                    raise ValueError("本地删除成功， 链接云端失败, 无法删除云端数据")
                raise ValueError("链接云端失败, 无法删除云端数据")

            public.M('ssl_info').where("id = ?", (target["id"],)).update({"cloud_id": -1})

        return public.returnMsg(True, "删除成功")

    def batch_remove_cert(self, get):
        return self.remove_cloud_cert(get)

    def upload_cert_to_cloud(self, get):
        ssl_id = None
        ssl_hash = None
        try:
            if "ssl_id" in get:
                ssl_id = int(get.ssl_id)
            if "ssl_hash" in get:
                ssl_hash = get.ssl_hash.strip()
        except (ValueError, AttributeError, KeyError):
            return public.ReturnMsg(False, "参数错误")
        try:
            data = self.upload_cert(ssl_id, ssl_hash)
            return data
        except ValueError as e:
            return public.ReturnMsg(False, str(e))
        except Exception as e:
            return public.ReturnMsg(False, "操作错误：" + str(e))

    def upload_cert(self, ssl_id=None, ssl_hash=None):
        key, iv, user_info = self._get_cbc_key_and_iv()
        if key is None or iv is None:
            raise ValueError(False, '面板未登录，无法上传云端!')

        target = self.find_ssl_info(ssl_id=ssl_id, ssl_hash=ssl_hash)
        if not target:
            raise ValueError("没有指定的证书信息")

        data = {
            'privateKey': public.readFile(target["path"] + '/privkey.pem'),
            'certificate': public.readFile(target["path"] + '/fullchain.pem'),
            "encryptWay": "AES-128-CBC",
            "hashVal": target['hash'],
            "uid": user_info["uid"],
            "access_key": user_info["access_key"],
            "serverid": user_info["serverid"],
        }

        if data["privateKey"] is False or data["certificate"] is False:
            raise ValueError('证书文件读取错误')

        AES = AesCryptPy3(key, "CBC", iv, char_set="utf8")
        data["privateKey"] = AES.aes_encrypt(data["privateKey"])
        data["certificate"] = AES.aes_encrypt(data["certificate"])
        # 对接云端
        url = "https://www.bt.cn/api/Cert_cloud_deploy/cloud_deploy"

        try:
            res_text = public.httpPost(url, data)
            res_data = json.loads(res_text)
            if res_data["status"] is True:
                cloud_id = int(res_data["data"].get("id"))
                public.M('ssl_info').where("id = ?", (target["id"],)).update({"cloud_id": cloud_id})

                return res_data
            else:
                return res_data
        except:
            raise ValueError('链接云端失败')

    def _remove_ssl_from_local(self, ssl_hash):
        local_path = '/www/server/panel/vhost/ssl'
        if not os.path.exists(local_path):
            return

        for p_name in os.listdir(local_path):
            pem_file = "{}/{}/fullchain.pem".format(local_path, p_name)

            if os.path.isfile(pem_file):
                hash_data = self._hash(cert_filename=pem_file)
                if hash_data == ssl_hash:
                    shutil.rmtree("{}/{}".format(local_path, p_name))

    def _hash(self, cert_filename: str = None, certificate: str = None, ignore_errors: bool = False):
        if cert_filename is not None and os.path.isfile(cert_filename):
            certificate = public.readFile(cert_filename)

        if not isinstance(certificate, str) or not certificate.startswith("-----BEGIN"):
            if ignore_errors:
                return None
            raise ValueError("证书格式错误")

        md5_obj = md5()
        md5_obj.update(certificate.encode("utf-8"))
        return md5_obj.hexdigest()

    @staticmethod
    def _get_cbc_key_and_iv(with_uer_info=True):
        uer_info_file = "{}/data/userInfo.json".format(public.get_panel_path())
        try:
            user_info = json.loads(public.readFile(uer_info_file))
            uid = user_info["uid"]
        except (json.JSONDecodeError, KeyError):
            return None, None, None

        md5_obj = md5()
        md5_obj.update(str(uid).encode('utf8'))
        bytes_data = md5_obj.hexdigest()

        key = ''
        iv = ''
        for i in range(len(bytes_data)):
            if i % 2 == 0:
                iv += bytes_data[i]
            else:
                key += bytes_data[i]

        if with_uer_info:
            return key, iv, user_info

        return key, iv, None

    @staticmethod
    def find_ssl_info(ssl_id=None, ssl_hash=None):
        tmp_conn = public.M('ssl_info')
        if ssl_id is None and ssl_hash is None:
            raise ValueError("没有参数信息")
        if ssl_id is not None:
            tmp_conn.where("id = ?", (ssl_id,))
        else:
            tmp_conn.where("hash = ?", (ssl_hash,))

        target = tmp_conn.find()
        if isinstance(target, str) and target.startswith("error"):
            raise ValueError("数据库查询错误：" + target)

        if not bool(target):
            return None

        target["auth_info"] = json.loads(target["auth_info"])
        target["use_for_site"] = json.loads(target["use_for_site"])
        target["dns"] = json.loads(target["dns"])
        target["info"] = json.loads(target["info"])
        target['endtime'] = int((datetime.strptime(target['not_after'][:10], "%Y-%m-%d").timestamp()
                                 - datetime.today().timestamp()) / (60 * 60 * 24))
        return target

    def GetCert(self, get):
        from ssl_manage import SSLManger
        if "ssl_hash" in get:
            return SSLManger.get_cert_for_deploy(get.ssl_hash.strip())
        else:
            if "index" in get:
                import acme_v2
                acme = acme_v2.acme_v2()
                exclude_data = acme.get_exclude_hash(get)
                ssl_hash = exclude_data['exclude_hash_let'].get(get.index)
                return SSLManger.get_cert_for_deploy(ssl_hash.strip())

        vpath = os.path.join('/www/server/panel/vhost/ssl', get.certName.replace("*.", ''))
        if not os.path.exists(vpath): return public.returnMsg(False, '证书不存在!')
        data = {}
        data['privkey'] = public.readFile(vpath + '/privkey.pem')
        data['fullchain'] = public.readFile(vpath + '/fullchain.pem')
        return data

    # 部署
    def SetCertToSite(self, get):

        try:
            if 'ssl_hash' in get or "index" in get:
                result = self.GetCert(get)
            else:
                result = {"privkey": get.privkey, "fullchain": get.fullchain}
            if not 'privkey' in result: return result
            siteName = get.siteName
            path = '/www/server/panel/vhost/cert/' + siteName
            if not os.path.exists(path):
                public.ExecShell('mkdir -p ' + path)
            csrpath = path + "/fullchain.pem"
            keypath = path + "/privkey.pem"

            # 清理旧的证书链
            public.ExecShell('rm -f ' + keypath)
            public.ExecShell('rm -f ' + csrpath)
            public.ExecShell('rm -rf ' + path + '-00*')
            public.ExecShell('rm -rf /etc/letsencrypt/archive/' + get.siteName)
            public.ExecShell('rm -rf /etc/letsencrypt/archive/' + get.siteName + '-00*')
            public.ExecShell('rm -f /etc/letsencrypt/renewal/' + get.siteName + '.conf')
            public.ExecShell('rm -f /etc/letsencrypt/renewal/' + get.siteName + '-00*.conf')
            public.ExecShell('rm -f ' + path + '/README')
            if os.path.exists(path + '/certOrderId'): os.remove(path + '/certOrderId')

            public.writeFile(keypath, result['privkey'])
            public.writeFile(csrpath, result['fullchain'])
            import panelSite
            return panelSite.panelSite().SetSSLConf(get)
        except Exception as ex:
            if 'isBatch' in get: return False
            return public.returnMsg(False, 'SET_ERROR,' + public.get_error_info())

    def SetBatchCertToSite(self, get):
        """
        @name 批量部署证书
        @auther hezhihong
        """

        if not hasattr(get, 'BatchInfo') or not get.BatchInfo:
            return public.returnMsg(False, '参数错误')
        else:
            ssl_list = json.loads(get.BatchInfo)
        if isinstance(ssl_list, list):
            total_num = len(ssl_list)
            resultinfo = {"total": total_num, "success": 0, "faild": 0, "successList": [], "faildList": []}
            successList = []
            faildList = []
            successnum = 0
            failnum = 0
            for Info in ssl_list:
                set_result = {'status': True}
                get.certName = set_result['certName'] = Info.get('certName')
                get.siteName = set_result['siteName'] = str(Info['siteName'])  # 站点名称必定为字符串
                get.isBatch = True
                if "ssl_hash" in Info:
                    get.ssl_hash = Info.get('ssl_hash')
                result = self.SetCertToSite(get)
                if not result:
                    set_result['status'] = False
                    failnum += 1
                    faildList.append(set_result)
                else:
                    successnum += 1
                    successList.append(set_result)
                public.writeSpeed('setssl', successnum + failnum, total_num)
            import firewalls
            get.port = '443'
            get.ps = 'HTTPS'
            firewalls.firewalls().AddAcceptPort(get)
            public.serviceReload()
            resultinfo['success'] = successnum
            resultinfo['faild'] = failnum
            resultinfo['successList'] = successList
            resultinfo['faildList'] = faildList

            if hasattr(get, "set_https_mode") and get.set_https_mode.strip() in (True, 1, "1", "true"):
                import panelSite
                sites_obj = panelSite.panelSite()
                if not sites_obj.get_https_mode():
                    sites_obj.set_https_mode()

        else:
            return public.returnMsg(False, '参数类型错误')
        return resultinfo

    # 证书转为pkcs12
    def dump_pkcs12(self, key_pem=None, cert_pem=None, ca_pem=None, friendly_name=None):
        """
        @证书转为pkcs12
        @key_pem string 私钥数据
        @cert_pem string 证书数据
        @ca_pem string 可选的CA证书数据
        @friendly_name string 可选的证书名称
        """
        try:
            from acme_v2 import acme_v2
            result = acme_v2().dump_pkcs12(key_pem, cert_pem, ca_pem, friendly_name)
        except:
            import ssl_info
            result = ssl_info.ssl_info().dump_pkcs12_new(key_pem, cert_pem, ca_pem, friendly_name)
        return result

    def download_cert(self, get):
        # 兼容订单下载
        if 'index' in get:
            import acme_v2
            return acme_v2.acme_v2().download_cert_to_local(get)
        if 'ssl_id' in get:
            target = self.find_ssl_info(ssl_id=get.ssl_id)
        elif 'ssl_hash' in get:
            target = self.find_ssl_info(ssl_hash=get.ssl_hash)
        else:
            return public.returnMsg(False, "缺少参数")
        if not target:
            return public.returnMsg(False, "未找到证书信息")
        csrpath = os.path.join(target['path'], "fullchain.pem")
        keypath = os.path.join(target['path'], "privkey.pem")
        data_hash = self._hash(csrpath)
        if not os.path.isfile(csrpath) or get.ssl_hash != data_hash:
            return public.returnMsg(False, "下载失败，未找到此证书")
        key = public.readFile(keypath)
        csr = public.readFile(csrpath)

        rpath = '{}/temp/ssl'.format(public.get_panel_path())
        if os.path.exists(rpath): shutil.rmtree(rpath)
        path = '{}/{}'.format(rpath, data_hash)
        domain_cert = csr.split('-----END CERTIFICATE-----')[0] + "-----END CERTIFICATE-----\n"
        ca_cert = csr.replace(domain_cert, '')

        p12 = self.dump_pkcs12(key, '{}\n{}'.format(domain_cert.strip(), ca_cert), ca_cert)

        for x in ['IIS', 'Apache', 'Nginx', '其他证书']:
            d_file = '{}/{}'.format(path, x)
            if not os.path.exists(d_file): os.makedirs(d_file)

            if x == 'IIS' and p12 is not None:
                public.writeFile2(d_file + '/fullchain.pfx', p12, 'wb+')
                public.writeFile(d_file + '/password.txt', get['pwd'])
            elif x == 'Apache':
                public.writeFile(d_file + '/privkey.key', key)
                public.writeFile(d_file + '/root_bundle.crt', ca_cert)
                public.writeFile(d_file + '/domain.crt', domain_cert)
            else:
                public.writeFile(d_file + '/privkey.key', key)
                public.writeFile(d_file + '/fullchain.pem', '{}\n{}'.format(domain_cert.strip(), ca_cert))

        flist = []
        public.get_file_list(path, flist)

        zfile = '{}/{}.zip'.format(rpath, target["dns"][0]+"_"+data_hash)
        import zipfile
        f = zipfile.ZipFile(zfile, 'w', zipfile.ZIP_DEFLATED)
        for item in flist:
            s_path = item.replace(path, '')
            if s_path: f.write(item, s_path)
        f.close()

        port = str(public.get_panel_port())
        # host = public.GetLocalIp()  # 获取服务器地址
        from flask import request
        host = request.host.split(":")[0]
        ssl = "https" if public.is_ssl() else "http"

        zfile = '{}://{}:{}/download?filename={}'.format(ssl, host, port, zfile)

        return public.returnMsg(True, zfile)

    def get_order_download_data(self, index):
        import acme_v2
        acme = acme_v2.acme_v2()
        exclude_data = acme.get_exclude_hash(None)
        ssl_hash = exclude_data.get("exclude_hash_let", {}).get(index, "")
        data = self.find_ssl_info(ssl_hash=ssl_hash)
        if not data:
            raise ValueError('未找到证书信息')
        data['info'] = json.dumps({"issuer": "let's Encrypt"})
        return data

    def batch_download_cert(self, get):
        if not 'ssl_hash' in get and not 'index' in get and not 'oid' in get:
            return public.returnMsg(False, "缺少必填参数")
        finish_list = []
        cert_data = []
        if 'ssl_hash' in get and get.ssl_hash.strip():
            hash_list = get.ssl_hash.split(',')
            ssl_hash = "','".join(hash_list) if len(hash_list) > 1 else hash_list[0]
            cert_data = public.M('ssl_info').where("hash in ('{}')".format(ssl_hash), ()).select()

        if 'index'in get and get.index.strip():
            index_list = get.index.split(',')
            for index in index_list:
                try:
                    cert_data.append(self.get_order_download_data(index))
                except:
                    finish_list.append({"status": False, "cert": {"info": json.dumps({"issuer": "let's Encrypt"})}})

        rpath = '{}/temp/_ssl'.format(public.get_panel_path())
        if os.path.exists(rpath): shutil.rmtree(rpath)

        if 'oid' in get and get.oid.strip():
            import panelSSL
            import base64

            os.makedirs(rpath)
            oid_list = get.oid.split(',')
            for oid in oid_list:

                try:
                    result = panelSSL.panelSSL().download_cert(public.to_dict_obj({'oid': oid}))
                    if not result or not result.get('data') or not result.get('filename'):
                        finish_list.append({"status": False, "cert": {"info": json.dumps({"issuer": oid})}})
                        continue
                    with open(rpath + '/{}_{}'.format(oid, result['filename']), 'wb') as f:
                        f.write(base64.b64decode(result['data']))
                    finish_list.append({"status": True, "cert": {"info": json.dumps({"issuer": oid})}})
                except:
                    finish_list.append({"status": False, "cert": {"info": json.dumps({"issuer": oid})}})

        for cert in cert_data:
            csrpath = os.path.join(cert['path'], "fullchain.pem")
            keypath = os.path.join(cert['path'], "privkey.pem")
            data_hash = self._hash(csrpath)

            if not os.path.exists(csrpath) or not os.path.exists(keypath):
                finish_list.append({"status": False, "cert": cert})

            key = public.readFile(keypath)
            csr = public.readFile(csrpath)
            try:
                dns = json.loads(cert['dns'])
            except:
                dns = cert.get('dns')

            path = '{}/{}'.format(rpath, dns[0]+"_"+data_hash)
            domain_cert = csr.split('-----END CERTIFICATE-----')[0] + "-----END CERTIFICATE-----\n"
            ca_cert = csr.replace(domain_cert, '')

            p12 = self.dump_pkcs12(key, '{}\n{}'.format(domain_cert.strip(), ca_cert), ca_cert)

            for x in ['IIS', 'Apache', 'Nginx', '其他证书']:
                d_file = '{}/{}'.format(path, x)
                if not os.path.exists(d_file): os.makedirs(d_file)

                if x == 'IIS' and p12 is not None:
                    public.writeFile2(d_file + '/fullchain.pfx', p12, 'wb+')
                    public.writeFile(d_file + '/password.txt', get['pwd'])
                elif x == 'Apache':
                    public.writeFile(d_file + '/privkey.key', key)
                    public.writeFile(d_file + '/root_bundle.crt', ca_cert)
                    public.writeFile(d_file + '/domain.crt', domain_cert)
                else:
                    public.writeFile(d_file + '/privkey.key', key)
                    public.writeFile(d_file + '/fullchain.pem', '{}\n{}'.format(domain_cert.strip(), ca_cert))
            finish_list.append({"status": True, "cert": cert})

        if os.path.exists(rpath) and os.listdir(rpath):
            flist = []
            public.get_file_list(rpath, flist)
            zfile = '{}.zip'.format(rpath)
            import zipfile
            f = zipfile.ZipFile(zfile, 'w', zipfile.ZIP_DEFLATED)
            for item in flist:
                s_path = item.replace(rpath, '')
                if s_path: f.write(item, s_path)
            f.close()
            port = str(public.get_panel_port())
            # host = public.GetLocalIp()  # 获取服务器地址
            from flask import request
            host = request.host.split(":")[0]
            ssl = "https" if public.is_ssl() else "http"
            zfile = '{}://{}:{}/download?filename={}'.format(ssl, host, port, zfile)
        else:
            zfile = ''
        return {'finish_list': finish_list, 'url': zfile}

    def parse_certificate(self, get):
        """
        获取证书信息
        """
        try:
            from cryptography import x509
            from cryptography.hazmat.backends import default_backend

            cert = x509.load_pem_x509_certificate(get.csr, default_backend())
            try:
                # 提取品牌（证书颁发对象）
                brand = cert.issuer.get_attributes_for_oid(x509.NameOID.COMMON_NAME)[0].value
                # 提取 CA 名称
                ca_name = cert.issuer.get_attributes_for_oid(x509.NameOID.ORGANIZATION_NAME)[0].value
            except:
                brand = "未知"
                ca_name = "未知"

            # 提取认证域名
            try:
                cn = cert.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)[0].value
            except IndexError:
                cn = None

            # 提取 SAN（Subject Alternative Name）
            try:
                san_extension = cert.extensions.get_extension_for_oid(x509.ExtensionOID.SUBJECT_ALTERNATIVE_NAME).value
                san_domains = san_extension.get_values_for_type(x509.DNSName)
            except x509.ExtensionNotFound:
                san_domains = []
                # 合并 CN 和 SAN，并去重
            all_domains = set(san_domains)
            if cn:
                all_domains.add(cn)

            # 提取到期时间
            try:
                expiration_date = cert.not_valid_after_utc.timestamp()
            except:
                expiration_date = "未知"

        except Exception as e:
            public.print_log(str(e))
            brand = "未知"
            all_domains = []
            expiration_date = "未知"
            ca_name = "未知"

        return {
            "brand": brand,
            "domains": list(all_domains),
            "expiration_date": expiration_date,
            "ca_name": ca_name
        }

    def save_cert(self, get):
        from panelSite import panelSite
        import ssl_info
        ssl_info = ssl_info.ssl_info()
        create_order = False

        key = get.key.strip()
        csr = get.csr.strip()

        issuer = panelSite().analyze_ssl(csr)
        if issuer.get("organizationName") == "Let's Encrypt":
            create_order = True
            csr += "\n"

        # 验证证书和密钥是否匹配格式是否为pem
        check_flag, check_msg = ssl_info.verify_certificate_and_key_match(get.key, get.csr)
        if not check_flag: return public.returnMsg(False, check_msg)
        # 验证证书链是否完整
        check_chain_flag, check_chain_msg = ssl_info.verify_certificate_chain(get.csr)
        if not check_chain_flag: return public.returnMsg(False, check_chain_msg)

        hash_data = self._hash(certificate=csr)
        path = "/www/server/panel/vhost/ssl_saved/" + hash_data
        csrpath = path + "/fullchain.pem"
        keypath = path + "/privkey.pem"

        # 判断是否存在
        if os.path.exists(path): return {"status": True, "msg": "证书已存在", "creat_order": create_order, "ssl_hash": hash_data}

        # 保存文件
        public.ExecShell('mkdir -p ' + path)
        public.writeFile(keypath, key)
        public.writeFile(csrpath, csr)
        # 解析数据
        cert_data = {}
        if csr:
            get.certPath = csrpath
            import panelSSL
            cert_data = panelSSL.panelSSL().GetCertName(get)

        # 写入数据库
        target = self.find_ssl_info(ssl_hash=hash_data)
        if target:
            public.M('ssl_info').where(
                "id = ?", (target["id"],)
            ).update(
                ({
                    "path": path,
                    "dns": json.dumps(cert_data["dns"]),
                    "subject": cert_data["subject"],
                    "info": json.dumps(cert_data),
                    "not_after": cert_data["notAfter"]
                })
            )
        else:
            public.M('ssl_info').add(
                'hash,path,dns,subject,info,not_after'
                , (hash_data, path, json.dumps(cert_data["dns"]), cert_data["subject"], json.dumps(cert_data), cert_data["notAfter"])
            )

        return {"status": True, "msg": "保存成功", "creat_order": create_order, "ssl_hash": hash_data}

    def create_order(self, get):
        try:
            target = self.find_ssl_info(ssl_hash=get.ssl_hash)
            ssl_info = target.get('info')

            if not ssl_info:
                return public.returnMsg(False, "未找到证书信息")
            if ssl_info.get("issuer_O") != "Let's Encrypt":
                return public.returnMsg(False, "证书不是Let's Encrypt颁发的")
            index = public.md5(str(uuid.uuid4()))
            order_data = {
                "status": "valid",
                "auth_type": "dns",
                "domains": ssl_info.get("dns"),
                "auth_to": "dns",
                "certificate_url": "",
                "save_path": "vhost/ssl_saved/{}".format(get.ssl_hash),
                "index": index,
                "cert_timeout": datetime.strptime(ssl_info.get("notAfter"), "%Y-%m-%d").timestamp(),
                "renew_time": 0,
                "retry_count": 0,
                "next_retry_time": 0
            }
            # 写入config
            config_path = "/www/server/panel/config/letsencrypt_v2.json"
            try:
                config_data = json.loads(public.readFile(config_path))
            except:
                config_data = {}
            config_data["orders"][index] = order_data
            public.writeFile(config_path, json.dumps(config_data))

            import acme_v2
            acm_obj = acme_v2.acme_v2()
            pem = public.readFile("vhost/ssl_saved/{}/fullchain.pem".format(get.ssl_hash))
            acm_obj.set_exclude_hash(index, pem)
            return {"status": True, "msg": "创建成功", "index": index}
        except:
            public.print_log(public.get_error_info())
            return public.returnMsg(False, "创建失败")

    def apply_for_cert(self, get):
        """
        申请证书
        """
        from acme_v2 import acme_v2
        acm_obj = acme_v2()
        index = None
        if "index" in get:
            index = get.index
        if index:
            return acm_obj.apply_cert([], "dns", "dns", index=index)

        if 'auto_wildcard' in get and get.auto_wildcard == '1':
            acm_obj._auto_wildcard = True

        domains = json.loads(get.domains)
        auth_type = get.auth_type
        auth_to = get.auth_to

        return acm_obj.apply_cert(domains, auth_type, auth_to)

    def update_cert_from_cloud(self, get):
        """
        从云端同步到本地
        """
        key, iv, user_info = self._get_cbc_key_and_iv(with_uer_info=True)
        if key is None or iv is None:
            return public.returnMsg(False, '面板未登录，无法链接云端!')
        # 获取本地证书
        local_cert = public.M('ssl_info').field(
            'hash'
        ).select()
        hash_list = [i['hash'] for i in local_cert]

        AES = AesCryptPy3(key, "CBC", iv, char_set="utf8")

        # 对接云端
        url = "https://www.bt.cn/api/Cert_cloud_deploy/get_cert_list"
        try:
            res_text = public.httpPost(url, {
                "uid": user_info["uid"],
                "access_key": user_info["access_key"],
                "serverid": user_info["serverid"],
            })
            res_data = json.loads(res_text)
            if res_data["status"] is False:
                return public.returnMsg(False, '获取云端数据失败')

            res_list = res_data['data']
        except:
            return public.returnMsg(False, '链接云端失败')
        x = 0
        for data in res_list:
            try:
                get.key = AES.aes_decrypt(data["privateKey"])
                get.csr = AES.aes_decrypt(data["certificate"])
                cloud_id = data["id"]
                hash_data = self._hash(certificate=get.csr)

                if hash_data in hash_list:
                    # 删除本地证书
                    public.ExecShell('rm -rf /www/server/panel/vhost/ssl_saved/' + hash_data)
                self.save_cert(get)
                public.M('ssl_info').where("hash = ?", (hash_data,)).update({"cloud_id": cloud_id})
                x += 1
            except Exception as e:
                pass
        return public.returnMsg(True, "已同步{}个证书".format(str(x)))

    def get_report_task(self):

        from mod.project.push import taskMod
        report_data = taskMod.main().get_task_list().get('data')
        report_data_dic = {}
        if report_data:
            report_data_dic = {i["keyword"]: i["id"] for i in report_data if
                               i["source"] == "cert_endtime" and i["status"]}
        return report_data_dic

    def create_report_task(self, get):
        from mod.base.push_mod import manager

        data = self.get_cert_list(public.to_dict_obj({"status_id": 1}))["data"]
        if not get.ssl_id in [i['ssl_id'] for i in data]:
            return public.returnMsg(False, "未找到证书信息")
        sender_lsit = get.sender.split(",")
        task_data = {"task_data":{"tid":"71","type":"cert_endtime","title":"证书到期","status":True,"count":0,"interval":600,"project":get.ssl_id,"cycle":int(get.cycle)},"sender":sender_lsit,"number_rule":{"day_num":0,"total":int(get.total)},"time_rule":{"send_interval":0,"time_range":[0,86399]}}
        get.template_id = "71"
        get.task_data = json.dumps(task_data)

        return manager.PushManager().set_task_conf(get)

    def remove_report_task(self, get):
        from mod.base.push_mod import manager
        return manager.PushManager().remove_task_conf(get)

    def renewal_cert(self, get):
        import acme_v2
        if 'index' not in get:
            return public.returnMsg(False, '缺少必填参数')
        return acme_v2.acme_v2().renew_cert(get.index)

    def get_crontab(self):
        data = public.M('crontab').select()
        return data

    def add_renewal_task(self, get):
        import crontab
        import random
        cron = crontab.crontab()
        get.name = "续签Lets Encrypt证书[{}]".format(get.name).replace("'", "")
        get.sBody = "/www/server/panel/pyenv/bin/python3 -u /www/server/panel/class/acme_v2.py --renew=1 --index={} --cycle={}".format(get.index, get.cycle)
        get.type = "day"
        get.week = 1
        get.hour = random.randint(0, 23)
        get.minute = random.randint(0, 59)
        get.second = ""
        get.sName = ""
        get.backupTo = ""
        get.save = ""
        get.urladdress = ""
        get.notice_channel = ""
        get.datab_name = ""
        get.tables_name = ""
        get.keyword = ""
        get.where1 = 1
        get.timeSet = 1
        get.timeType = 'sday'
        get.sType = 'toShell'
        get.save_local = 0
        get.notice = 0
        get.flock = 1

        return cron.AddCrontab(get)

    def del_renewal_task(self, get):
        import crontab
        cron = crontab.crontab()
        get.id = get.crontab_id
        return cron.DelCrontab(get)

    def get_cert_content(self, get):
        """
        获取证书内容
        """
        if 'ssl_hash' in get and get.ssl_hash:
            ssl_hash = get.ssl_hash
        else:
            if 'index' in get and get.index:
                import acme_v2
                acme = acme_v2.acme_v2()
                exclude_data = acme.get_exclude_hash(None)
                ssl_hash = exclude_data.get("exclude_hash_let", {}).get(get.index, "")
            else:
                return public.returnMsg(False, '缺少必填参数')
        if not ssl_hash:
            return public.returnMsg(False, '未找到证书信息')
        ssl_info = self.find_ssl_info(ssl_hash=ssl_hash)
        ssl_info["key"] = public.readFile("/www/server/panel/vhost/ssl_saved/{}/privkey.pem".format(ssl_hash))
        ssl_info["cert"] = public.readFile("/www/server/panel/vhost/ssl_saved/{}/fullchain.pem".format(ssl_hash))
        return {"status": True, "msg": "获取成功", "content": ssl_info}

    def new_ssl_proxy(self, get):
        """
        创建SSL代理
        """

        return self.new_ssl_proxy_request(vars(get))

    def new_ssl_proxy_request(self, params=None):
        if params is None:
            params = {}
        request_url = "https://api.bt.cn/v2/NewSsl/proxy"
        user_info = public.get_user_info()


        # 特殊处理优惠券列表和证书列表
        if params["url"] in ("/api/v1/ssl/get_order_list", "/api/v1/ssl/get_user_discount_list"):
            try:
                newssl_discount_serverid = json.loads(public.readFile("/www/server/panel/data/newssl_discount.json"))["serverid"]
            except:
                data = self._get_newssl_discount()
                newssl_discount_serverid = data["data"]["serverid"] if data["status"] else ""
            if user_info["serverid"] != newssl_discount_serverid:
                params["exclude_discount_id"] = "22,23,24"

        params = {"data": json.dumps(params)}

        params.update(user_info)

        msg = '接口请求失败（{}）'.format(request_url)
        try:
            res = public.httpPost(request_url, params)

            if res == False:
                raise public.error_conn_cloud(msg)
        except Exception as ex:
            raise public.error_conn_cloud(str(ex))

        result = public.returnMsg(False, msg)
        try:
            result = json.loads(res.strip())
        except:
            pass
        return result

    def get_newssl_discount(self, get=None):
        result = {"status": False, "msg": "", "data": {}}
        if public.get_oem_name() != "ssl251104":
            return result
        if os.path.exists("/www/server/panel/data/newssl_discount.json"):
            try:
                data = json.loads(public.readFile("/www/server/panel/data/newssl_discount.json"))
                if data and "serverid" in data:
                    self._get_newssl_discount()
            except:
                self._get_newssl_discount()
            return result
        else:
            disc_dic = {22: "0元购DV单域名商用SSL*1张", 23: "4.9元购DV单域名商用SSL*1张", 24: "9.9元购DV单域名商用SSL*1张"}
            try:
                data = self._get_newssl_discount()
                if not data["status"] or not data["data"]:
                    return result
                data = data["data"]
                user_info = public.get_user_info()
                if data["serverid"] != user_info["serverid"]:
                    return result
                data.update({"discount_info": disc_dic[data["discount_id"]] if data["discount_id"] in disc_dic else "未知优惠券"})
                result["status"] = True
                result["msg"] = "领取成功"
                result["data"] = data
                return result
            except:
                return {"status": False, "msg": "", "data": {}}


    def _get_newssl_discount(self):
        """
        获取NewSSL状态
        """

        request_url = "https://api.bt.cn/v2/new_ssl/claim_ssl_package"
        user_info = public.get_user_info()

        msg = '接口请求失败（{}）'.format(request_url)
        try:
            res = public.httpPost(request_url, user_info)

            if res == False:
                raise public.error_conn_cloud(msg)
        except Exception as ex:
            raise public.error_conn_cloud(str(ex))

        result = public.returnMsg(False, msg)
        try:
            result = json.loads(res.strip())
        except:
            pass

        if result["status"]:
            public.writeFile("/www/server/panel/data/newssl_discount.json", json.dumps(result["data"]))
        return result




