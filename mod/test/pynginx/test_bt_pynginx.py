import json
import os
import sys
import time
from unittest import TestCase

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

from mod.base.pynginx.btnginx import BtNginxConf, bt_nginx_format, ng_detect, NginxInstance, CreateSiteUtil, ConfigFileUtil

def test_main(ng_ins):

    tmp_path = "/tmp/1111_nginx_test/bt_nginx_format"
    if os.path.exists(tmp_path + "/site_conf.json"):
        ConfigFileUtil(tmp_path).unuse()
    ret = bt_nginx_format(ng_ins, tmp_path="/tmp/1111_nginx_test")
    ret.test_nginx(ng_ins.nginx_bin)
    print("\n\n")
    # ret.save_conf()
    # with open(os.path.join(ret.tmp_conf_path, "site_conf.json"), "r") as f:
    #     site_data = json.load(f)
    #
    # c_util = ConfigFileUtil(ret.tmp_conf_path)
    # with c_util.test_env():
    #     for site in site_data:
    #         print(site)
    #         if site["site_type"] == "proxy":
    #             print(CreateSiteUtil(ret.tmp_conf_path).create_proxy_site(site))
    #         elif site["site_type"] == "html":
    #             print(CreateSiteUtil(ret.tmp_conf_path).create_html_site(site))
    #         elif site["site_type"] == "PHP":
    #             print(CreateSiteUtil(ret.tmp_conf_path).create_php_site(site))
    #
    # ConfigFileUtil(tmp_path).use2panel()



def main():

    # test_unit = (
    #     os.path.join(os.path.dirname(__file__), "test_configs/test1_multi_server_https/nginx.conf"),
    #     os.path.join(os.path.dirname(__file__), "test_configs/test4_no_default_site/nginx.conf"),
    #     os.path.join(os.path.dirname(__file__), "test_configs/test5_complex_all/nginx.conf"),
    # )
    # for file in test_unit:
    #     print("test file:", file)
    #     print("file content:", open(file, "r", encoding="utf-8").read())
    #     test_main(file)
    #     print("\n"+"$$$$"*10+"\n")

    ret = ng_detect(only_running=True)
    print(ret)
    for i in ret:
        print(i.nginx_bin, i.nginx_conf)
        test_main(i)

    # test_main("/www/server/nginx/conf/nginx.conf")


if __name__ == "__main__":
    main()