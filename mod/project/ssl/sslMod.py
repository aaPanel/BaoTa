import json
import os.path

import public
from sslModel import base, dataModel
class main:

    # 获取dns-api列表和托管的域名
    def get_dns_api_and_domains(self, get=None):
        # 获取域名列表
        domain_list = public.M("ssl_domains").select()
        # 获取dns-api列表
        ssl_base_obj = base.sslBase()
        dns_api_data = ssl_base_obj.get_dns_data(None)

        # 宝塔域名
        dns_api_data.update({"bt": {"dns_name": "宝塔DNS", "id": "bt", "dns_type": "宝塔DNS", "domains": []}})

        for domain in domain_list:
            if not dns_api_data.get(domain["dns_id"], None):
                if "cloud_id=" in domain["dns_id"]:
                    dns_api_data["bt"]["domains"].append(domain["domain"])
                continue
            if not dns_api_data[domain["dns_id"]].get("domains", None):
                dns_api_data[domain["dns_id"]]["domains"] = []

            dns_api_data[domain["dns_id"]]["domains"].append(domain["domain"])

        dns_api_list = []
        for k in dns_api_data:
            if not dns_api_data[k].get("domains", None):
                dns_api_data[k]["domains"] = []
            # 移除敏感数据
            dns_api_data[k].pop("user_name", None)
            dns_api_data[k].pop("api_password", None)
            dns_api_data[k].pop("secret_id", None)
            dns_api_data[k].pop("secret_key", None)
            dns_api_data[k].pop("ID", None)
            dns_api_data[k].pop("Token", None)
            dns_api_data[k].pop("SecretKey", None)
            dns_api_data[k].pop("AccessKey", None)
            dns_api_data[k].pop("project_id", None)
            dns_api_data[k].pop("API Key", None)
            dns_api_data[k].pop("E-Mail", None)
            dns_api_list.insert(0, dns_api_data[k])

        dns_api_list.insert(0, {"dns_name": "手动解析", "id": "manual", "dns_type": "手动解析", "domains": []})

        return dns_api_list

    # 设置解析记录
    def set_dns_record(self, domain_name, dns_value, dns_id=None, record_type="TXT",sub_domain=""):
        if sub_domain:
            domain_name="{}.{}".format(sub_domain,domain_name)
        # 宝塔域名
        if dns_id == "bt":
            # 查询域名云端ID
            root, sub = public.split_domain_sld(domain_name)
            domain_data = public.M("ssl_domains").where("domain=?", (root,)).find()
            if not domain_data:
                return public.returnMsg(False, "域名【{}】非宝塔域名，请确定域名是在宝塔域名注册或已转入宝塔域名后，在域名管理中刷新本地缓存后重试！".format(root))
            dns_id = domain_data["dns_id"]
            if dns_id.find("cloud_id=") == -1:
                return public.returnMsg(False, "域名【{}】非宝塔域名，请确定域名是在宝塔域名注册或已转入宝塔域名后，在域名管理中刷新本地缓存后重试！".format(root))
            domain_id = dns_id.split("cloud_id=")[1]
            from mod.project.domain import domainMod
            domain_obj = domainMod.main()
            rep = domain_obj.request({"url": "/api/v1/dns/record/create", "domain_type": 1, "domain_id": domain_id,
                                      "record": sub, "value": dns_value, "type": record_type,
                                      "mx": 10, "ttl": 600, "remark": "", "view_id": 0})
            return rep
        elif dns_id == "manual":
            return public.returnMsg(True, "请手动添加DNS解析记录，解析类型：{}，解析值：{}".format(record_type, dns_value))
        else:
            ssl_data_obj = dataModel.main()
            args = {
                "fun_name": "create_dns_record",
                "dns_id": dns_id,
                "domain_dns_value": dns_value,
                "record_type": record_type,
                "domain_name": domain_name,
                "mx": 10,
            }
            return ssl_data_obj.run_fun(public.to_dict_obj(args))

    # 写验证文件
    def write_verify_file(self, domain_name, file_name, file_value):
        # 获取域名所在网站
        domain_data = public.M("domain").where("name=?", (domain_name,)).find()
        if not domain_data:
            return public.returnMsg(False, "域名【{}】未绑定到任何网站，请先将域名解析到本服务器并绑定网站后重试！".format(domain_name))
        site_data = public.M("sites").where("id=?", (domain_data["pid"],)).find()
        if not site_data:
            return public.returnMsg(False, "域名【{}】绑定的网站不存在，请先将域名解析到本服务器并绑定网站后重试！".format(domain_name))
        site_path = site_data["path"]
        if not site_path or not os.path.exists(site_path):
            return public.returnMsg(False, "域名【{}】绑定的网站根目录不存在，请先将域名解析到本服务器并绑定网站后重试！".format(domain_name))
        verify_path = os.path.join(site_path, file_name)
        if not os.path.exists(os.path.dirname(verify_path)):
            os.makedirs(os.path.dirname(verify_path), exist_ok=True)
        try:
            public.writeFile(verify_path, file_value)
            return public.returnMsg(True, "success")
        except Exception as e:
            return public.returnMsg(False, "写入验证文件【{}】失败，错误信息：{}".format(verify_path, str(e)))

    # 自动设置验证
    def auto_set_ssl_verify(self, get=None):
        if not "verify_type" in get or not get.verify_type:
            return public.returnMsg(False, "验证类型不能为空！")
        verify_type = get.verify_type
        if not "verify_data" in get or not get.verify_data:
            return public.returnMsg(False, "验证数据不能为空！")
        verify_data = get.verify_data.strip()
        # 是否设置验证值
        set_verify_value = False
        if "set_verify_value" in get:
           set_verify_value = get.set_verify_value
        try:
            verify_info = json.loads(verify_data)
        except Exception as e:
            return public.returnMsg(False, "验证数据格式错误，必须为JSON格式！")
        result = []
        if verify_type == "dns":
            for item in verify_info:
                if not item.get("domain", None):
                    return public.returnMsg(False, "域名不能为空！")
                domain_name = item["domain"].strip()
                # 特殊处理垦派多级域名的情况
                sub_domain = item.get("sub_domain", "")
                if domain_name.startswith("*."):
                    domain_name = domain_name[2:]
                root, sub = public.split_domain_sld(domain_name)
                if "_certum" in sub_domain and len(sub_domain.split(".")) > 1 and sub != "":
                    sub_domain = "_certum"

                record_type = item.get("record_type", "TXT")
                dns_value = item.get("dns_value", "")
                dns_id = item.get("dns_id", None)

                # 本地验证
                local_verify = False
                try:
                    import dns.resolver
                    ns = dns.resolver.query(sub_domain+"."+domain_name, record_type)
                    for j in ns.response.answer:
                        for i in j.items:
                            txt_value = i.to_text().replace('"', '').strip()
                            if txt_value == dns_value:
                                local_verify = True
                except Exception as e:
                    pass
                rep = {"local_verify": local_verify, "status": None, "msg": None}
                if not local_verify and set_verify_value in (True, "True", "true"):
                    rep.update(self.set_dns_record(domain_name, dns_value, dns_id=dns_id, record_type=record_type, sub_domain=sub_domain))
                    try:
                        import dns.resolver
                        ns = dns.resolver.query(sub_domain + "." + domain_name, record_type)
                        for j in ns.response.answer:
                            for i in j.items:
                                txt_value = i.to_text().replace('"', '').strip()
                                if txt_value == dns_value:
                                    rep["local_verify"] = True
                    except Exception as e:
                        pass
                result.append({"domain": domain_name, "rep": rep})
        elif verify_type == "file":
            for item in verify_info:
                if not item.get("domain", None):
                    return public.returnMsg(False, "域名不能为空！")
                domain_name = item["domain"].strip()
                file_name = item.get("file_name", "")
                file_value = item.get("file_value", "")

                # 本地验证
                local_verify = False
                import requests
                url = "http://{}/{}".format(domain_name, file_name)
                try:
                    response = requests.get(url, timeout=5)

                    if response.status_code == 200:
                        if response.text.strip() == file_value.strip():
                            local_verify = True
                except Exception as e:
                    pass
                rep = {"local_verify": local_verify, "status": None, "msg": None}
                if not local_verify:
                    rep.update(self.write_verify_file(domain_name, file_name, file_value))
                else:
                    rep.update(public.returnMsg(True, "验证文件已存在且内容正确，无需重复写入！"))
                result.append({"domain": domain_name, "rep": rep})
        else:
            return public.returnMsg(False, "不支持的验证类型：{}！".format(verify_type))
        return {"status": True, "msg": "success", "data": result}

