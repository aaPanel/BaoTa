#!/usr/bin/python
# coding: utf-8
# -----------------------------
# 自动续签Let's Encrypt证书
# -----------------------------

import os,sys, time, re
os.chdir('/www/server/panel')
sys.path.insert(0,'./')
sys.path.insert(1,'class/')
import public
from mailModel import mainModel
from acme_v2 import acme_v2

acme = acme_v2()
domain_data = mainModel.main().get_domains(public.to_dict_obj({"p": 1, "limit": 99999999}))["msg"]

for domain in domain_data["data"]:
    print("正在续签：{}".format(domain['domain']))
    if domain['ssl_info'].get("issuer_O") != "Let's Encrypt" or not domain['ssl_status']:
        print("证书不符合续签条件，跳过")
        continue
    if domain['ssl_info']["endtime"] >= 30:
        print("证书到期时间大于30天，跳过")
        continue
    cert = acme.apply_cert(domain['ssl_info']['dns'], "dns", str(domain['ssl_info']['dns']))
    if cert.get("cert") and cert.get("private_key") and cert.get("root"):
        mainModel.main().set_mail_certificate_multiple(public.to_dict_obj({"domain": domain["domain"], "key": cert.get("private_key"), "csr": cert.get("cert") + cert.get("root"), "act": "add"}))
        print("证书续签成功")
    else:
        print("证书续签失败")
