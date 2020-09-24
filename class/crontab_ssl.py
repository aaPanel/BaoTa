# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2016 宝塔软件(http:#bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author:  <290070744@qq.com>
# -------------------------------------------------------------------

# ------------------------------
# ssl自动续订定时任务脚本
# ------------------------------
import os, json, sys, time

os.chdir("/www/server/panel")
if not 'class/' in sys.path:
    sys.path.insert(0,'class/')
import public

sys.path.append(".")
import panelSSL
import panelSite


class dict_obj:
    def __contains__(self, key):
        return getattr(self, key, None)

    def __setitem__(self, key, value): setattr(self, key, value)

    def __getitem__(self, key): return getattr(self, key, None)

    def __delitem__(self, key): delattr(self, key)

    def __delattr__(self, key): delattr(self, key)

    def get_items(self): return self


if __name__ == "__main__":
    get = dict_obj()
    obj = panelSSL.panelSSL()
    CertList = obj.GetCertList(get)
    cmd_list = json.loads(public.ReadFile("/www/server/panel/vhost/crontab.json"))
    panelSite_=panelSite.panelSite()
    for i in CertList:
        timeArray = time.strptime(i['notAfter'], "%Y-%m-%d")
        timestamp = time.mktime(timeArray)
        if int(timestamp) - time.time() < 86400 * 30:  # 如果证书到期时间小于多少天就续订
            subject = i['subject']
            for j in cmd_list:
                if subject == j['siteName']:
                    cmd = j['cmd']
                    public.ExecShell(cmd)
                    # 保存证书
                    get.siteName=subject
                    result = panelSite_.save_cert(get)
                    public.serviceReload()
