import sys
import os
import shutil
import traceback
from typing import Optional

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

import public
from firewallModel.comModel import main as fire_main
if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

from mod.project.java.utils import TomCat

GLOBAL_TOMCAT_PATH = "/usr/local/bttomcat"
INDEP_PROJECT_TOMCAT_PATH = "/www/server/bt_tomcat_web"
PS_FILE_TMPL = "{tomcat_path}/ps.txt"


def open_firewall(prot: str):
    f_get = public.dict_obj()
    f_get.protocol = "tcp"
    f_get.port = prot
    f_get.choose = "all"
    f_get.types = "accept"
    f_get.brief = ""
    f_get.domain = ""
    f_get.chain = "INPUT"
    f_get.operation = "add"
    f_get.strategy = "accept"
    fire_main().set_port_rule(f_get)


# install_version 7 8 9 10
# install_type global or custom
def make(install_version: str,
         install_type: str,
         jdk_path: str,
         install_name: Optional[str],
         port:Optional[str],
         user:Optional[str],
         auto_start: bool = False,
         release_firewall: bool = False,
         ps: Optional[str] = None):
    if not os.path.exists(GLOBAL_TOMCAT_PATH + "/tomcat" + install_version):
        print("tomcat{}安装失败".format(install_version))
        return

    if install_type == "global":  # 全局安装不在做更多检查
        tomcat = TomCat(GLOBAL_TOMCAT_PATH + "/tomcat" + install_version)
        if port and port.isdigit() and int(port) > 0:
            tomcat.set_port(int(port))
            if release_firewall:
                print("正在执行放行防火墙端口...")
                open_firewall(port)
        tomcat.start()
        print("tomcat{}安装完成".format(install_version))
        return

    tomcat_path = GLOBAL_TOMCAT_PATH + "/tomcat_bak" + install_version
    if not install_name:
        print("tomcat {} 未指定安装名称".format(install_version))

    try:
        shutil.copytree(tomcat_path, INDEP_PROJECT_TOMCAT_PATH + "/" + install_name)
    except:
        print("tomcat {} 安装失败".format(install_version))
        traceback.print_exc()
        return

    ps_file = PS_FILE_TMPL.format(tomcat_path=INDEP_PROJECT_TOMCAT_PATH + "/" + install_name)
    if not os.path.exists(ps_file) or ps:
        with open(ps_file, "w") as f:
            f.write(ps or "")

    tomcat = TomCat(INDEP_PROJECT_TOMCAT_PATH + "/" + install_name)
    if port and port.isdigit() and int(port) > 0:
        tomcat.set_port(int(port))
        if release_firewall:
            print("正在执行放行防火墙端口...")
            open_firewall(port)

    print("正在执行替换JDK版本...")
    res = tomcat.replace_jdk(jdk_path)
    if res is not None:
        print("tomcat {} 安装失败： {}".format(install_version, res))
        return

    if user:
        res = tomcat.change_default_user(user)
        if res is False:
            print("tomcat {} 安装失败: 修改用户失败".format(install_version))
            return

    if auto_start:
        tomcat.set_service(user, auto_start)

    if not tomcat.save_config_xml():
        print("tomcat {} 安装失败: 配置文件保存失败".format(install_version))
        return

    tomcat.restart()
    print("安装完成")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Tomcat 安装管理工具")

    # 必要位置参数
    parser.add_argument("install_version", type=str,
                        choices=["7", "8", "9", "10"],
                        help="Tomcat 版本号 (7/8/9/10)")
    parser.add_argument("install_type", type=str,
                        choices=["global", "custom"],
                        help="安装类型: global(全局) 或 custom(自定义)")

    # 可选参数
    parser.add_argument("--jdk-path", type=str,
                        help="指定JDK路径 (例如: /usr/lib/jvm/java-11-openjdk)")
    parser.add_argument("--name", type=str,
                        help="自定义安装名称（当install_type为custom时必填）")
    parser.add_argument("--port", type=int,
                        help="Tomcat 端口（需大于0）")
    parser.add_argument("--user", type=str,
                        help="指定运行用户")
    parser.add_argument("--auto-start", action="store_true",
                        help="安装后自动启动服务")
    parser.add_argument("--release-firewall", action="store_true",
                        help="自动放行防火墙端口")
    parser.add_argument("--ps", type=str,
                        help="指定ps文件内容")

    args = parser.parse_args()

    # 参数校验
    if args.install_type == "custom" and not args.name:
        parser.error("自定义安装时必须指定--name参数")
    if args.port and args.port <= 0:
        parser.error("端口必须大于0")

    # 调用安装函数
    make(
        install_version=args.install_version,
        install_type=args.install_type,
        jdk_path=args.jdk_path,
        install_name=args.name,
        port=str(args.port) if args.port else None,
        user=args.user,
        auto_start=args.auto_start,
        release_firewall=args.release_firewall,
        ps=args.ps
    )
