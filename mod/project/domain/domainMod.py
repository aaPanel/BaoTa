import json

import public
import requests


class main:
    def __init__(self):
        self.user_info = public.get_user_info()

    def request(self, params=None):
        if params is None:
            params = {}
        request_url = "https://api.bt.cn/v2/domain/proxy"

        url = params.get("url", "")

        params = {"data": json.dumps(params)}
        # params = {"data": panelSSL.De_Code(params)}


        params.update(self.user_info)
        # public.print_log(params)

        msg = '接口请求失败（{}）'.format(request_url)
        try:
            res = public.httpPost(request_url, params)
            # public.print_log(res)

            if res == False:
                raise public.error_conn_cloud(msg)
        except Exception as ex:
            raise public.error_conn_cloud(str(ex))

        result = public.returnMsg(False, msg)
        try:
            result = json.loads(res.strip())
        except:
            pass
        try:
            if url == "/api/v1/order/payment/status":
                if result["data"] and result["data"].get("status") == 1:
                    public.set_module_logs("domain_payment_status", "order_payment_status")
            if url == "/api/v1/dns/record/create":
                public.set_module_logs("domain_record_create", "dns_record_create")
        except:
            pass
        return result

    def domain_proxy(self, get):

        # public.print_log(type(vars(get).get("years")))
        return self.request(vars(get))

    def get_public_ip(self, get):
        url = public.GetConfigValue('home') + '/Api/getIpAddress'
        ip = public.HttpGet(url)
        return {
            "code": 0,
            "data": ip,
            "msg": "获取成功",
            "status": True
        }

    def get_analysis_ip(self, get=None):
        path = "/www/server/panel/data/domain_ip.pl"
        ip = public.readFile(path)
        if not ip:
            ip = public.GetLocalIp()
            public.writeFile(path, ip)
        return {
            "code": 0,
            "data": ip,
            "msg": "获取成功",
            "status": True
        }

    def set_analysis_ip(self, get):
        path = "/www/server/panel/data/domain_ip.pl"
        public.writeFile(path, get.ip)
        return {
            "code": 0,
            "data": get.ip,
            "msg": "设置成功",
            "status": True
        }

    def get_domain_status(self, get):
        domains = get.domains.split(",")
        domain_string = "','".join(domains)
        data = public.M("domain").where("name in ('{}')".format(domain_string), ()).select()

        exist_list = [i["name"] for i in data]

        res = {i: i not in exist_list for i in domains}

        return {
            "code": 0,
            "data": res,
            "msg": "获取成功",
            "status": True
        }

    def create_dns_record(self, get):
        public.set_module_logs("domain_create_site", "create_dns_record")
        try:
            data = json.loads(get.domain_list)
        except Exception as e:
            return {
                "code": 0,
                "data": None,
                "msg": "数据格式错误: {}".format(str(e)),
                "status": False
            }

        ip_data = self.get_analysis_ip()
        if not ip_data["status"] or not ip_data["data"]:
            return {
                "code": 0,
                "data": None,
                "msg": "请先设置解析IP",
                "status": False
            }
        ip = ip_data["data"]

        domain_dic = {}
        for i in data:
            _res = {
                "code": 0,
                "data": None,
                "msg": "",
                "status": False
            }
            if "name" not in i:
                _res["msg"] = "缺少域名"
                domain_dic[i["name"]]=_res
                continue

            if "record" not in i:
                _res["msg"] = "缺少主机记录"
                domain_dic[i["name"]]=_res
                continue

            if "domain_id" in i:
                i["url"] = "/api/v1/dns/record/create"
                i["type"] = "A"
                i["value"] = ip
                domain_dic[i["name"]] = self.request(i)
            elif "local_domain_id" in i:
                from sslModel import dataModel
                dataModel = dataModel.main()
                try:
                    domain_dic[i["name"]] = dataModel.add_dns_value_by_domain(i["name"], ip, "A")
                except Exception as e:
                    _res["msg"] = str(e)
                    domain_dic[i["name"]] = _res
                    continue
            else:
                _res["msg"] = "缺少域名ID"
                domain_dic[i["name"]] = _res
                continue

        if "ssl_hash" in get and get.ssl_hash:
            public.set_module_logs("domain_set_ssl", "create_dns_record")
            if "site_name" not in get or not get.site_name:
                if "site_id" not in get or not get.site_id:
                    return {
                        "code": 0,
                        "data": None,
                        "msg": "缺少站点ID",
                        "status": False
                    }
                site_name = public.M("sites").where("id=?", (get.site_id,)).getField("name")
            else:
                site_name = get.site_name
            if not site_name:
                return {
                    "code": 0,
                    "data": None,
                    "msg": "站点不存在",
                    "status": False
                }
            import panelSSL
            panelSSL = panelSSL.panelSSL()
            get.siteName = site_name
            panelSSL.SetCertToSite(get)
            if "https" in get and get.https in (1, '1', True, 'true', 'True'):
                import panelSite
                panelSite = panelSite.panelSite()
                panelSite.HttpToHttps(get)
            else:
                public.serviceReload()

        return {
            "code": 0,
            "data": domain_dic,
            "msg": "解析完成",
            "status": True
        }

    def poxy_whois_query(self, get):
        public.set_module_logs("poxy_whois_query", "poxy_whois_query")
        rep = requests.get("https://www.bt.cn/api/whois/query", vars(get))
        try:
            data = rep.json()
        except Exception as e:
            public.print_log(public.get_error_info())
            data = {
                "code": 1,
                "data": None,
                "msg": "请求失败: {}".format(str(e)),
                "status": False
            }
        return data

    # 刷新域名缓存
    def refresh_domain_cache(self, get=None):
        from sslModel import dataModel
        dataModel.main()
        # 清空本地域名缓存
        public.M("ssl_domains").where("dns_id like 'cloud_id=%'",()).update({"dns_id": 0})

        # 获取云端域名列表
        cloud_domain_data = self.request({"url": "/api/v1/domain/manage/list", "p": 1, "rows": 9999})
        if not cloud_domain_data["status"]:
            return cloud_domain_data
        cloud_domain_list = cloud_domain_data["data"]["data"]
        for cloud_domain in cloud_domain_list:
            if not cloud_domain["status"] or not cloud_domain["real_name_status"] or not cloud_domain["ns_status"]:
                continue
            domain = cloud_domain["full_domain"]
            dns_id = "cloud_id={}".format(cloud_domain["id"])

            domain_info = public.M("ssl_domains").where("domain=?", (domain,)).find()
            if not domain_info:
                public.M("ssl_domains").add('domain,dns_id,type_id,endtime,ps', (domain, dns_id, 0, 0, ''))
            else:
                public.M("ssl_domains").where("domain=?", (domain,)).update({"dns_id": dns_id})
        return cloud_domain_data










