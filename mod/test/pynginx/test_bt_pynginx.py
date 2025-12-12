import json
import os
import sys
import time
from unittest import TestCase

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

from mod.base.pynginx.btnginx import BtNginxConf, bt_nginx_format, ng_detect

def test_main(mian_file: str):
    ret =  bt_nginx_format(mian_file, tmp_path="/tmp/1111_nginx_test")
    print("\n\n")
    # ret.save_conf()


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
        test_main(i.nginx_conf)

    # test_main("/www/server/nginx/conf/nginx.conf")


if __name__ == "__main__":
    main()