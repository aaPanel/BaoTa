import json
import os
import sys
import time

# ------------------------------
# 商业证书自动续签
# ------------------------------

os.chdir('/www/server/panel/')
sys.path.insert(0, "class/")
sys.path.insert(0, "/www/server/panel/")

import public

from panelSSL import panelSSL
from sslModel import certModel

class RenewCertificate:
    """
    商业证书自动续签
    """

    def __init__(self):
        self.sslmodel = certModel.main()
        self.panelssl = panelSSL()
        self.config_path = '{}/data/ssl/renewCert.json'.format(public.get_panel_path())
        if not os.path.exists(self.config_path):
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

        self.config = public.readFile(self.config_path)
        if not self.config:
            self.config = {
                "renews": {}, # 续签的证书列表 {oid:{}}
                "max_retry": 3, # 最大重试次数
                "retry_interval": 60 # 重试间隔时间(秒)
            }
            self.save_config()
        else:
            self.config = json.loads(self.config)

    def save_config(self):
        """
        保存配置
        """
        public.writeFile(self.config_path, json.dumps(self.config))

    def run(self):
        """
        执行续签
        """
        self.renew_certificate()

    def validate_dns(self, args):
        """
        校验DNS
        """
        res = self.panelssl.get_verify_result(args)
        if res["certStatus"] == "PENDING":
            print("**DNS校验未通过 请检查校验信息...".format(args.oid))
            dcvdnsHost = res["data"]["DCVdnsHost"]
            dcvdnsType = res["data"]["DCVdnsType"]
            dcvdnsValue = res["data"]["DCVdnsValue"]
            print("**主机记录：{}".format(dcvdnsHost))
            print("**记录类型：{}".format(dcvdnsType))
            print("**记录值：{}".format(dcvdnsValue))
            return False
        else:
            return True

    def validate_dns2(self,oid):
        """
        校验DNS
        :param oid: 订单id
        :return: 返回验证结果 true通过 false不通过
        """
        get = public.dict_obj()
        get.oid = oid
        res = self.panelssl.get_order_find(get)
        if res["orderStatus"] == 5:
            return True
        else:
            return False

    def redeploy_cert(self,cert):
        if len(cert['use_site']) == 0:
            return
        last_site = cert['use_site'][-1]
        for site in cert['use_site']:
            print("**正在重新部署证书到站点 {}...".format(site))
            get = public.dict_obj()
            get.oid = cert['oid']
            get.siteName = site
            get.reload = 1 if site == last_site else 0
            self.panelssl.set_cert(get)
        print("**证书{} 重新部署完成...".format(cert['domainName']))

    def renew_certificate(self):
        """
        校验是否需要续签证书
        """
        get = public.dict_obj()
        get.cert_type = "1"
        certs = self.sslmodel.get_cert_list(get)
        for cert in certs["data"]:
            if cert['years'] <= 1:
                continue
            args = public.dict_obj()
            args.oid = cert['oid']
            args.pid = cert['pid']
            args.cert_ssl_type = "1"
            if cert['orderStatus'] == 15:   # 提交续签申请
                print("*证书{} 待续签,开始提交续签...".format(cert['domainName']))
                res = self.panelssl.auto_renew_ca(args) #向官网提交续签证书
                if res['success'] == True:
                    print("*证书续签提交成功...")
                    self.config["renews"][cert['oid']] = cert
                else:
                    print("*证书续签提交失败: {}".format(res['res']))
            if cert['oid'] in self.config["renews"].keys():    # 验证dns
                for i in range(self.config.get("max_retry",5)):
                    print("*证书{} DNS校验中...".format(cert['domainName']))
                    # 校验DNS
                    if self.validate_dns(args) and self.validate_dns2(args.oid):
                        print("*证书{} DNS校验通过...".format(cert['domainName']))
                        print("*证书{} 正在重新部署到所有站点...".format(cert['domainName']))
                        self.redeploy_cert(cert)
                        print("*证书{} 部署完成...".format(cert['domainName']))
                        del self.config["renews"][cert['oid']]
                        self.save_config()
                        break
                    else:
                        print("*证书{} DNS校验失败 正在尝试第{}次...".format(cert['domainName'], i + 1))
                        time.sleep(self.config.get("retry_interval", 10))
                else:
                    print("*证书{} DNS校验失败,请检查DNS记录是否正确... 设置正确后将在下一次运行时重新续签".format(cert['domainName']))


if __name__ == '__main__':
    renew_cert = RenewCertificate()
    try:
        print("**开始执行续签程序...")
        renew_cert.run()
    except Exception as e:
        print("**执行续签程序失败: {}".format(str(e)))
        renew_cert.save_config()