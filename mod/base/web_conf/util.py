import os
import sys
from typing import Optional, Tuple, Callable

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

import public


def webserver() -> Optional[str]:
    if os.path.exists('/www/server/apache/bin/apachectl'):
        web_server = 'apache'
    elif os.path.exists('/www/server/nginx/sbin/nginx'):
        web_server = 'nginx'
    elif os.path.exists('/usr/local/lsws/bin/lswsctrl'):
        web_server = 'openlitespeed'
    else:
        web_server = None
    return web_server


def check_server_config() -> Optional[str]:
    w_s = webserver()
    setup_path = "/www/server"
    if w_s == 'nginx':
        shell_str = (
            "ulimit -n 8192; "
            "{setup_path}/nginx/sbin/nginx -t -c {setup_path}/nginx/conf/nginx.conf"
        ).format(setup_path=setup_path)
        result: Tuple[str, str] = public.ExecShell(shell_str)
        searchStr = 'successful'
    elif w_s == 'apache':
        shell_str = (
            "ulimit -n 8192; "
            "{setup_path}/apache/bin/apachectl -t"
        ).format(setup_path=setup_path)
        result: Tuple[str, str] = public.ExecShell(shell_str)
        searchStr = 'Syntax OK'
    else:
        return None
    if result[1].find(searchStr) == -1:
        public.WriteLog("TYPE_SOFT", 'CONF_CHECK_ERR', (result[1],))
        return result[1]


def read_file(filename, mode='r') -> Optional[str]:
    """
    读取文件内容
    @filename 文件名
    return string(bin) 若文件不存在，则返回None
    """
    import os
    if not os.path.exists(filename):
        return None
    fp = None
    try:
        fp = open(filename, mode=mode)
        f_body = fp.read()
    except:
        return None
    finally:
        if fp and not fp.closed:
            fp.close()
    return f_body


def write_file(filename: str, s_body: str, mode='w+') -> bool:
    """
    写入文件内容
    @filename 文件名
    @s_body 欲写入的内容
    return bool 若文件不存在则尝试自动创建
    """
    try:
        fp = open(filename, mode=mode)
        fp.write(s_body)
        fp.close()
        return True
    except:
        try:
            fp = open(filename, mode=mode, encoding="utf-8")
            fp.write(s_body)
            fp.close()
            return True
        except:
            return False


def debug_api_warp(fn):
    def inner(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except:
            public.print_log(public.get_error_info())
            return {

            }

    return inner


# 重载Web服务配置
def service_reload():
    setup_path = "/www/server"
    if os.path.exists('{}/nginx/sbin/nginx'.format(setup_path)):
        result = public.ExecShell('/etc/init.d/nginx reload')
        if result[1].find('nginx.pid') != -1:
            public.ExecShell('pkill -9 nginx && sleep 1')
            public.ExecShell('/etc/init.d/nginx start')
    elif os.path.exists('{}/apache/bin/apachectl'.format(setup_path)):
        result = public.ExecShell('/etc/init.d/httpd reload')
    else:
        result = public.ExecShell('rm -f /tmp/lshttpd/*.sock* && /usr/local/lsws/bin/lswsctrl restart')
    return result


# 防正则转译
def pre_re_key(input_str: str) -> str:
    re_char = ['$', '(', ')', '*', '+', '.', '[', ']', '{', '}', '?', '^', '|', '\\']
    res = []
    for i in input_str:
        if i in re_char:
            res.append("\\" + i)
        else:
            res.append(i)
    return "".join(res)


def get_log_path() -> str:
    log_path = public.readFile("{}/data/sites_log_path.pl".format(public.get_panel_path()))
    if isinstance(log_path, str) and os.path.isdir(log_path):
        return log_path
    return public.GetConfigValue('logs_path')



# 2024/4/18 上午9:44 域名编码转换
def to_puny_code(domain):
    try:
        try:
            import idna
        except:
            os.system("btpip install idna -I")
            import idna

        import re
        match = re.search(u"[^u\0000-u\001f]+", domain)
        if not match:
            return domain
        try:
            if domain.startswith("*."):
                return "*." + idna.encode(domain[2:]).decode("utf8")
            else:
                return idna.encode(domain).decode("utf8")
        except:
            return domain
    except:
        return domain


# 2024/4/18 下午5:48 中文路径处理
def to_puny_code_path(path):
    if sys.version_info[0] == 2: path = path.encode('utf-8')
    if os.path.exists(path): return path
    import re
    match = re.search(u"[\x80-\xff]+", path)
    if not match: match = re.search(u"[\u4e00-\u9fa5]+", path)
    if not match: return path
    npath = ''
    for ph in path.split('/'):
        npath += '/' + to_puny_code(ph)
    return npath.replace('//', '/')



class _DB:

    def __call__(self, table: str):
        import db
        with db.Sql() as t:
            t.table(table)
            return t


DB = _DB()

GET_CLASS = public.dict_obj

listen_ipv6: Callable[[], bool] = public.listen_ipv6

ExecShell: Callable = public.ExecShell


def use_http2() -> bool:
    versionStr = public.readFile('/www/server/nginx/version.pl')
    if isinstance(versionStr, str):
        if versionStr.find('1.8.1') == -1:
            return True
    return False
