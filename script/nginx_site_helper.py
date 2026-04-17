import json
import os
import shutil
import sys
import traceback
from typing import List

os.chdir('/www/server/panel')
sys.path.insert(0, "class/")
sys.path.insert(0, '/www/server/panel')

from mod.base.pynginx.btnginx import BtNginxConf, bt_nginx_format, ng_detect, NginxInstance, \
    CreateSiteUtil, ConfigFileUtil, ng_detect_by_bin

_HELPER_PATH_TMP = "/www/server/panel/data/ng_helper_data"


def ng_ins_select(nginx_ins_list: List[NginxInstance]) -> NginxInstance:
    while True:
        print("=" * 20)
        for idx, ins in enumerate(nginx_ins_list):
            print("[{}] version: {}\n    nginx-bin: {}\n    config-file:{}\n    work-path:{}".format(
                idx + 1, ins.version, ins.nginx_bin, ins.nginx_conf, ins.working_dir
            ))
            if idx < len(nginx_ins_list) - 1:
                print("-" * 20)
        print("=" * 20)
        target_idx = input("请选择nginx实例(1-{}/quit/q):".format(len(nginx_ins_list)))
        if target_idx.strip().lower() in ("q", "quit"):
            sys.exit(0)
        try:
            target_idx = int(target_idx) - 1
            if 0 <= target_idx < len(nginx_ins_list):
                return nginx_ins_list[target_idx]
        except ValueError:
            continue
        except KeyboardInterrupt:
            sys.exit(0)


def parser_and_show_nginx(ins: NginxInstance) -> BtNginxConf:
    parsed_data_dir = os.path.join(_HELPER_PATH_TMP, "bt_nginx_format")
    if os.path.exists(parsed_data_dir + "/site_conf.json"):
        y = input("已存在解析记录，是否覆盖(y/n):")
        if y.strip().lower() in ("y", "yes"):
            shutil.rmtree(parsed_data_dir)
        else:
            sys.exit(0)
    try:
        res = bt_nginx_format(ins, tmp_path=_HELPER_PATH_TMP)
    except:
        traceback.print_exc()
        print("解析异常!!")
        sys.exit(1)

    if len(res.sites_conf) == 0:
        print("无可用站点!!")
        shutil.rmtree(_HELPER_PATH_TMP)
        sys.exit(0)
    print("配置{}中，共解析到{}个网站".format(ins.nginx_conf, len(res.sites_conf)))
    return res


def save_sites(bt_ng: BtNginxConf):
    print("=" * 20)
    for idx, site in enumerate(bt_ng.sites_conf.values()):
        print("[{}] 网站类型：{}\t网站名称：{}\n域名：{}\n网站目录：{}".format(
            idx+1, site.site_type(), site.name, ",".join(site.site_names), site.site_path
        ))
        if site.site_type() == "proxy":
            for po in (*site.proxy_info, site.root_proxy):
                if not po:
                    continue
                p_show = "代理路径：{}\t, 目标：{}{}".format(
                    po["path"], po["proxy_pass"],
                    "" if not po["send_host"] else "({})".format(po["send_host"])
                )
                print(p_show)
        elif site.site_type() == "PHP":
            print("PHP-sock:{}".format(site.php_sock))

        if idx < len(bt_ng.sites_conf.values()) - 1:
            print("-" * 20)
    print("=" * 20)
    if bt_ng.todo_warning_list:
        print("="* 8 + "警告"+"="*8)
        for i, msg in enumerate(bt_ng.todo_warning_list):
            print("[{}] {}".format(i+1, msg))
        print("=" * 20)
    y = input("是否保存以上配置(y/n):")
    if y.strip().lower() == "y":
        return _real_save()
    else:
        print("取消保存")

def _real_save():
    parsed_data_dir = os.path.join(_HELPER_PATH_TMP, "bt_nginx_format")

    with open(os.path.join(parsed_data_dir, "site_conf.json"), "r") as f:
        site_data = json.load(f)

    logs_data = []
    c_util = ConfigFileUtil(parsed_data_dir)
    try:
        create_util = CreateSiteUtil(parsed_data_dir)
        has_error = False
        with c_util.test_env():
            for site in site_data:
                if site["site_type"] == "proxy":
                    res = create_util.create_proxy_site(site)
                elif site["site_type"] == "html":
                    res = create_util.create_html_site(site)
                elif site["site_type"] == "PHP":
                    res = create_util.create_php_site(site)
                else:
                    res = "无法识别的网站类型"
                if res:
                    has_error = True
                logs_data.append({"name": site["name"], "msg": res or "保存成功"})
        with open(os.path.join(_HELPER_PATH_TMP, "last_log.json"), "w") as f:
            f.write(json.dumps(logs_data))
        if not has_error:
            c_util.use2panel()
        for log in logs_data:
            print("网站:[{}]，{}".format(log["name"], log["msg"]))
    except:
        traceback.print_exc()
        print("保存失败")


def re_bak_last():
    parsed_data_dir = os.path.join(_HELPER_PATH_TMP, "bt_nginx_format")
    if os.path.exists(parsed_data_dir + "/site_conf.json"):
        ConfigFileUtil(parsed_data_dir).unuse()
        print("已恢复上次配置")
    else:
        print("没有上次解析的记录，无法执行恢复")

def mian(bin_path: str):
    if not bin_path:
        nginx_ins_list = ng_detect()
    else:
        nginx_ins_list = []
        ng_ins = ng_detect_by_bin(bin_path)
        if ng_ins:
            nginx_ins_list.append(ng_ins)

    if not nginx_ins_list:
        print("无可用的nginx实例")
        sys.exit(0)

    if len(nginx_ins_list) > 1:
        target_nginx = ng_ins_select(nginx_ins_list)
    else:
        target_nginx = nginx_ins_list[0]

    ret = parser_and_show_nginx(target_nginx)
    save_sites(ret)


if __name__ == '__main__':
    if "-h" in sys.argv:
        print("""
    -h              显示帮助
    -b <nginx-bin>  指定nginx-bin
    recovery        恢复除网站之外的，其他配置文件，网站配置请在面板上删除
""")
        sys.exit(0)
    if len(sys.argv) > 1:
        if sys.argv[1] == "-b" and len(sys.argv) > 2:
            _bin_path = sys.argv[2]
            mian(_bin_path)
        elif sys.argv[1] == "recovery":
            re_bak_last()
    else:
        mian("")
