# coding: utf-8

# nginx配置文件修复


import os
import sys
import re
from typing import Tuple, Optional

os.chdir("/www/server/panel")
sys.path.insert(0, "class/")

import public


def get_conf_files():
    conf_dir = os.path.join(public.get_panel_path(), 'vhost/nginx')
    if not os.path.isdir(conf_dir):
        return []
    conf_list = []
    for tmp in os.scandir(conf_dir):
        if tmp.is_dir():
            continue
        if len(tmp.name) < 5:
            continue
        if tmp.name[-5:] != '.conf':
            continue
        conf_list.append(tmp.path)
    return conf_list


def get_nginx_version() -> Tuple[int, int, int]:
    """
        @name 获取nginx版本
        @return tuple
    """
    version = public.ReadFile('/www/server/nginx/version.pl')
    if not version:
        return 0, 0, 0
    version = version.split('.')
    if len(version) < 3:
        return 0, 0, 0
    return int(version[0]), int(version[1]), int(version[2])


def test_nginx_conf() -> Tuple[Optional[str], Optional[str]]:
    print("-" * 35 + "测试nginx配置文件" + "-" * 35)
    out, err = public.ExecShell(
        "/www/server/nginx/sbin/nginx -t -c /www/server/nginx/conf/nginx.conf"
    )  # type: str, str

    res = (out + "\n" + err).strip()
    print(res)
    print("-" * 90)
    if res.find('[emerg]') == -1 and res.find('[warn]') == -1:
        return None, None
    return out, err


def fix_conf(repair_num: int = 3, base_fix: bool = True):
    nginx_version = get_nginx_version()
    if nginx_version == (0, 0, 0):
        print('未安装nginx')
        return
    out, err = test_nginx_conf()
    if not out and not err:
        print('nginx配置文件无错误，无需修复')
        return

    is_reload = False
    conf_files = get_conf_files()

    if base_fix:   # 版本切换时的基础修复
        if is_change_nginx_http2():
            for i in conf_files:
                if change_nginx_server_http2(i):
                    is_reload = True

        if is_change_nginx_old_http2():
            for i in conf_files:
                if change_nginx_server_old_http2(i):
                    is_reload = True

        if not is_nginx_http3():
            for i in conf_files:
                if remove_nginx_server_quic(i):
                    is_reload = True
        if re.search(r"\[warn]\s+conflicting\s+server\s+name", err):
            for i in conf_files:
                if remove_repetitive_server_name(i):
                    print(i)
                    is_reload = True

    if repair_num >= 0:
        if err.find('well-known') != -1 and err.find("No such file") != -1:
            if repair_not_such_well_know(err):
                is_reload = True

        if err.find('/conf/enable-php') != -1 and err.find("No such file") != -1:
            if repair_not_such_enable_php(err):
                is_reload = True

    if not is_reload:
        print('没有发现需要修复的配置文件')
        return

    out, err = test_nginx_conf()
    if not out and not err:
        start_nginx()
        return
    else:
        fix_conf(repair_num=repair_num-1, base_fix=False)


def start_nginx():
    print("-" * 87)
    res = "\n".join(public.ExecShell("/etc/init.d/nginx reload"))
    print(res.strip())
    if res.find('nginx is not running') != -1:
        print("检测到nginx未启动，尝试启动nginx")
        res = "\n".join(public.ExecShell("/etc/init.d/nginx start"))
        print(res.strip())


def remove_repetitive_server_name(nginx_file):
    if not os.path.isfile(nginx_file):
        return False
    data = public.ReadFile(nginx_file)
    if not isinstance(data, str):
        return False
    rep_sever_name = re.compile(r"^\s*server_name\s+([^\n;]+);\s*\n", re.M)
    rep_index = re.compile(r"^\s*index\s+([^\n;]+);\s*\n", re.M)

    reload = False
    res, data = repetitive_replace(rep_sever_name, data)
    if res:
        reload = True
    res, data = repetitive_replace(rep_index, data)
    if res:
        reload = True

    if reload:

        public.writeFile(nginx_file, data)
    return reload


def repetitive_replace(rep: re.Pattern, data: str) -> Tuple[bool, str]:
    data_list = []
    idx = 0
    res = False
    server_idx_list = []
    for i in re.compile(r"server\s*\{").finditer(data):
        server_idx_list.append(i.start())

    if not server_idx_list:
        return False, data

    next_server = 0
    repetitive = [False] * len(server_idx_list)
    server_idx_list.append(len(data))
    for tmp in rep.finditer(data):
        if tmp.start() > server_idx_list[next_server + 1]:
            next_server += 1

        if not repetitive[next_server] and tmp.start() < server_idx_list[next_server + 1]:
            repetitive[next_server] = True
            continue

        if repetitive[next_server]:
            data_list.append(data[idx: tmp.start()])
            idx = tmp.end()
            res = True

    if not res:
        return False, data

    data_list.append(data[idx:])
    return True, "".join(data_list)


def change_nginx_server_http2(nginx_file: str) -> bool:
    if not os.path.isfile(nginx_file):
        return False
    data = public.ReadFile(nginx_file)
    rep_listen = re.compile(r"\s*listen\s+[\[\]:]*([0-9]+).*;[^\n]*\n", re.M)

    conf_list = []
    start_idx, last_listen_idx = 0, -1
    for tmp in rep_listen.finditer(data):
        listen_str = tmp.group()
        if "http2" in listen_str:
            listen_str = listen_str.replace("http2", "")
            last_listen_idx = len(conf_list) + 2

        conf_list.append(data[start_idx:tmp.start()])
        conf_list.append(listen_str)
        start_idx = tmp.end()

    conf_list.append(data[start_idx:])
    if last_listen_idx > 0:
        conf_list.insert(last_listen_idx, "    http2 on;\n")

        new_conf = "".join(conf_list)
        public.writeFile(nginx_file, new_conf)
        return True
    else:
        return False


def is_change_nginx_http2() -> bool:
    nginx_ver = get_nginx_version()
    if not nginx_ver:
        return False

    if nginx_ver >= (1, 25, 1):
        return True

    return False


def is_change_nginx_old_http2() -> bool:
    nginx_ver = get_nginx_version()
    if not nginx_ver:
        return False
    if nginx_ver < (1, 25, 1):
        return True

    return False


def change_nginx_server_old_http2(nginx_file: str) -> bool:
    if not os.path.isfile(nginx_file):
        return False
    data = public.ReadFile(nginx_file)
    if not isinstance(data, str):
        return False

    rep_http2_on = re.compile(r"\s*http2\s+on;[^\n]*\n", re.M)
    if not rep_http2_on.search(data):
        return False
    else:
        data = rep_http2_on.sub("\n", data)

    rep_listen = re.compile(r"\s*listen\s+[\[\]:]*443.*;[^\n]*\n", re.M)
    conf_list = []
    start_idx = 0
    for tmp in rep_listen.finditer(data):
        listen_str = tmp.group()
        conf_list.append(data[start_idx:tmp.start()])
        conf_list.append(listen_str.replace(";", " http2;"))
        start_idx = tmp.end()

    conf_list.append(data[start_idx:])
    new_conf = "".join(conf_list)
    public.writeFile(nginx_file, new_conf)
    return True


def remove_nginx_server_quic(nginx_file: str) -> bool:
    if not os.path.isfile(nginx_file):
        return False
    data = public.ReadFile(nginx_file)
    if not isinstance(data, str):
        return False

    rep_listen_quic = re.compile(r"\s*listen\s+.*quic;", re.M)
    if not rep_listen_quic.search(data):
        return False

    new_conf = rep_listen_quic.sub('', data)
    public.writeFile(nginx_file, new_conf)
    return True


def is_nginx_http3() -> bool:
    return public.ExecShell("nginx -V 2>&1| grep 'http_v3_module'")[0].strip() != ''


def repair_not_such_well_know(error_msg) -> bool:
    rep_open_failed = re.compile(r'\[emerg]\s+open\(\)\s*"(?P<file>.*)"\s+failed\s+(?P<err>.*)\s+in\s+.*:(\d+)', re.M)
    res = rep_open_failed.search(error_msg)
    if not res:
        return False

    res = False
    for t_res in rep_open_failed.finditer(error_msg):
        if t_res.group("err").find("No such file") != -1 and t_res.group("file").find("vhost/nginx/well-known") != -1:
            if not os.path.exists(t_res.group("file")):
                if not os.path.isdir(os.path.dirname(t_res.group("file"))):
                    os.makedirs(os.path.dirname(t_res.group("file")), 0o755)
                public.writeFile(t_res.group("file"), "")
                res = True
    return res


def repair_not_such_enable_php(error_msg) -> bool:
    rep_open_failed = re.compile(r'\[emerg]\s+open\(\)\s*"(?P<file>.*)"\s+failed\s+(?P<err>.*)\s+in\s+.*:(\d+)', re.M)
    res = rep_open_failed.search(error_msg)
    if not res:
        return False

    res = False
    for t_res in rep_open_failed.finditer(error_msg):
        file_path = t_res.group("file")
        print(file_path)
        if t_res.group("err").find("No such file") != -1 and file_path.find("nginx/conf/enable-php") != -1:
            if os.path.exists(file_path):
                continue
            ver = file_path[-7:-5]
            if ver == "00":
                public.writeFile(file_path, "")
                res = True
                continue
            if ver == "hp":
                ver = phpmyadmin_php_version()
            if not ver.isdigit():
                continue
            public.writeFile(file_path, """    location ~ [^/]\.php(/|$)
    {{
        try_files $uri =404;
        fastcgi_pass  unix:/tmp/php-cgi-{}.sock;
        fastcgi_index index.php;
        include fastcgi.conf;
        include pathinfo.conf;
    }}
""".format(ver))
            res = True

    return res


def phpmyadmin_php_version() -> str:
    # 获取 PhpMyAdmin 默认使用0的php版本， 如果没有就用54版本
    pm_v = public.ReadFile("/www/server/phpmyadmin/version.pl")
    if not pm_v:
        return "54"
    if not os.path.exists("/www/server/php"):
        return "54"

    php_ver = []
    for i in os.listdir("/www/server/php"):
        if os.path.isdir(os.path.join("/www/server/php", i)) and i.isdigit():
            try:
                php_ver.append(int(i))
            except:
                continue
    php_ver.sort(reverse=True)

    ver_list = [i for i in pm_v.split(".")]
    if len(ver_list) > 2:
        ver_list = ver_list[:2]

    pm_v_data = "".join(ver_list)
    if pm_v_data == "40":
        min_php = 52
        max_php = 74
    elif pm_v_data == "44":
        min_php = 54
        max_php = 73
    elif pm_v_data == "49":
        min_php = 56
        max_php = 80
    elif pm_v_data == "50" and pm_v_data == "51" or pm_v_data == "52":
        min_php = 72
        max_php = 1000
    else:
        return "54"

    for i in php_ver:
        if min_php <= i <= max_php:
            return str(i)
    return "54"


if __name__ == '__main__':

    pidfile = '/tmp/nginx_conf_rep.pid'
    if os.path.exists(pidfile):
        old_pid = int(public.ReadFile(pidfile))
        if os.path.exists('/proc/{}'.format(old_pid)):
            print('进程已经在运行中...')
            sys.exit(0)

    pid = os.getpid()
    public.writeFile(pidfile, str(pid))

    fix_conf(repair_num=10)

    os.remove(pidfile)
