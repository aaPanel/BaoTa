# 网站文件相关操作

import os
import re
from typing import Optional, Union, List

from .util import webserver, check_server_config, write_file, read_file, DB, service_reload, pre_re_key, ExecShell


class DirTool:

    def __init__(self, conf_prefix: str = ""):
        self.conf_prefix = conf_prefix
        self._vhost_path = "/www/server/panel/vhost"

    # 修改站点路径
    def modify_site_path(self, site_name: str, old_site_path: str, new_site_path: str) -> Optional[str]:
        """
        修改 站点root 路径
        site_name 站点名称
        old_site_path 旧的root 路径
        new_site_path 新的root 路径
        """
        site_info = DB("sites").where("name=?", (site_name,)).find()
        if not isinstance(site_info, dict):
            return "站点信息查询错误"

        error_msg = check_server_config()
        if error_msg:
            return "服务配置无法重载，请检查配置错误再操作。\n" + error_msg

        if not self._check_site_path(new_site_path):
            return '请不要将网站根目录设置到以下关键目录中'

        if not os.path.exists(new_site_path):
            return '指定的网站根目录不存在，无法设置，请检查输入信息.'
        if old_site_path[-1] == '/':
            old_site_path = old_site_path[:-1]

        if new_site_path[-1] == '/':
            new_site_path = new_site_path[:-1]

        old_run_path = self.get_site_run_path(site_name)
        if old_run_path is None:
            return '读取网站当前运行目录失败，请检查配置文件'
        old_run_path_sub = old_run_path.replace(old_site_path, "")
        new_run_path = new_site_path + old_run_path_sub
        if not os.path.exists(new_site_path):
            new_run_path = new_site_path
        nginx_file = '{}/nginx/{}{}.conf'.format(self._vhost_path, self.conf_prefix, site_name)
        nginx_conf = read_file(nginx_file)
        if nginx_conf:
            rep_root = re.compile(r'\s*root\s+(.+);', re.M)
            new_conf = rep_root.sub("    root {};".format(new_run_path), nginx_conf)
            write_file(nginx_file, new_conf)

        apache_file = '{}/apache/{}{}.conf'.format(self._vhost_path, self.conf_prefix, site_name)
        apache_conf = read_file(apache_file)
        if apache_conf:
            rep_doc = re.compile(r"DocumentRoot\s+.*\n")
            new_conf = rep_doc.sub('DocumentRoot "' + new_run_path + '"\n', apache_conf)

            rep_dir = re.compile(r'''<Directory\s+['"]%s['"]'''% pre_re_key(old_site_path))
            new_conf = rep_dir.sub('<Directory "' + new_run_path + '">\n', new_conf)
            write_file(apache_file, new_conf)

        # 创建basedir
        userIni = new_run_path + '/.user.ini'
        if os.path.exists(userIni):
            ExecShell("chattr -i " + userIni)
        write_file(userIni, 'open_basedir=' + new_run_path + '/:/tmp/')
        ExecShell('chmod 644 ' + userIni)
        ExecShell('chown root:root ' + userIni)
        ExecShell('chattr +i ' + userIni)
        service_reload()
        DB("sites").where("id=?", (site_info["id"],)).setField('path', new_site_path)
        return

    # 修改站点的运行路径
    def modify_site_run_path(self, site_name, site_path, new_run_path_sub: str) -> Optional[str]:
        """
        修改 站点运行路径
        site_name 站点名称
        site_path 站点路径
        new_run_path_sub root路径的子运行目录
        如 site_path -> /www/wwwroots/aaaa
        new_run_path_sub -> bbb/ccc
        new_run_path  -> /www/wwwroots/aaaa/bbb/ccc
        """
        # 处理Nginx
        old_run_path = self.get_site_run_path(site_name)
        if old_run_path is None:
            return '读取网站当前运行目录失败，请检查配置文件'
        if new_run_path_sub.startswith("/"):
            new_run_path_sub = new_run_path_sub[1:]
        new_run_path = os.path.join(site_path, new_run_path_sub)
        filename = '{}/nginx/{}{}.conf'.format(self._vhost_path, self.conf_prefix, site_name)
        nginx_conf = read_file(filename)
        if nginx_conf:
            tmp = re.search(r'\s*root\s+(.+);', nginx_conf)
            if tmp:
                o_path = tmp.groups()[0]
                new_conf = nginx_conf.replace(o_path, new_run_path)
                write_file(filename, new_conf)

        # 处理Apache
        filename = '{}/apache/{}{}.conf'.format(self._vhost_path, self.conf_prefix, site_name)
        ap_conf = read_file(filename)
        if ap_conf:
            tmp = re.search(r'\s*DocumentRoot\s*"(.+)"\s*\n', ap_conf)
            if tmp:
                o_path = tmp.groups()[0]
                new_conf = ap_conf.replace(o_path, new_run_path)
                write_file(filename, new_conf)

        s_path = old_run_path + "/.user.ini"
        d_path = new_run_path + "/.user.ini"
        if s_path != d_path:
            ExecShell("chattr -i {}".format(s_path))
            ExecShell("mv {} {}".format(s_path, d_path))
            ExecShell("chattr +i {}".format(d_path))

        service_reload()

    # 获取站点的运行路径， 返回的路径是完整路径
    def get_site_run_path(self, site_name) -> Optional[str]:
        web_server = webserver()
        filename = "{}/{}/{}{}.conf".format(self._vhost_path, web_server, self.conf_prefix, site_name)
        if not os.path.exists(filename):
            return None
        run_path = None
        conf = read_file(filename)
        if web_server == 'nginx':
            tmp1 = re.search(r'\s*root\s+(?P<path>.+);', conf)
            if tmp1:
                run_path = tmp1.group("path").strip()
        elif web_server == 'apache':
            tmp1 = re.search(r'\s*DocumentRoot\s*"(?P<path>.+)"\s*\n', conf)
            if tmp1:
                run_path = tmp1.group("path")
        else:
            tmp1 = re.search(r"vhRoot\s*(?P<path>.*)", conf)
            if tmp1:
                run_path = tmp1.group("path").strip()

        return run_path

    # 获取index 文件
    def get_index_conf(self, site_name) -> Union[str, List[str]]:
        web_server = webserver()
        filename = "{}/{}/{}{}.conf".format(self._vhost_path, web_server, self.conf_prefix, site_name)
        if not os.path.exists(filename):
            return "配置文件丢失"
        conf = read_file(filename)
        if not conf:
            return "配置文件丢失"
        split_char = " "
        if web_server == 'nginx':
            rep = re.compile(r"\s+index\s+(?P<target>.+);", re.M)
        elif web_server == 'apache':
            rep = re.compile(r"DirectoryIndex\s+(?P<target>.+)", re.M)
        else:
            rep = re.compile(r"indexFiles\s+(?P<target>.+)", re.M)
            split_char = ","
        res = rep.search(conf)
        if not res:
            return "获取失败,配置文件中不存在默认文档"

        res_list = list(filter(None, map(lambda x: x.strip(), res.group("target").split(split_char))))

        return res_list

    # 获取设置index 文件 可以用 filenames 参数依次传入多个， 或 通过 file_list 参数传入index 列表
    def set_index_conf(self, site_name, *filenames: str, file_list: Optional[List[str]] = None):
        index_list = set()
        for i in filenames:
            f = i.strip()
            if not f:
                continue
            index_list.add(f)

        if file_list is not None:
            for i in file_list:
                f = i.strip()
                if not f:
                    continue
                index_list.add(f)

        # nginx
        file = '{}/nginx/{}{}.conf'.format(self._vhost_path, self.conf_prefix, site_name)
        conf = read_file(file)
        if conf:
            rep_index = re.compile(r"\s*index\s+.+;")
            new_conf = rep_index.sub("  index {};".format(" ".join(index_list)), conf)
            write_file(file, new_conf)

        # apache
        file = '{}/apache/{}{}.conf'.format(self._vhost_path, self.conf_prefix, site_name)
        conf = read_file(file)
        if conf:
            rep_index = re.compile(r"\s*DirectoryIndex\s+.+\n")
            new_conf = rep_index.sub("  DirectoryIndex {}\n".format(" ".join(index_list)), conf)
            write_file(file, new_conf)

        # openlitespeed
        file = '{}/openlitespeed/detail/{}{}.conf'.format(self._vhost_path, self.conf_prefix, site_name)
        conf = read_file(file)
        if conf:
            rep_index = re.compile(r"indexFiles\s+.+\n")
            new_conf = rep_index.sub('indexFiles {}\n'.format(",".join(index_list)), conf)
            write_file(file, new_conf)

        service_reload()
        return

    def _check_site_path(self, site_path):
        try:
            if site_path.find('/usr/local/lighthouse/') >= 0:
                return True

            if site_path in ['/', '/usr', '/dev', '/home', '/media', '/mnt', '/opt', '/tmp', '/var']:
                return False
            whites = ['/www/server/tomcat', '/www/server/stop', '/www/server/phpmyadmin']
            for w in whites:
                if site_path.find(w) == 0:
                    return True
            a, error_paths = self._get_sys_path()
            site_path = site_path.strip()
            if site_path[-1] == '/': site_path = site_path[:-1]
            if site_path in a:
                return False
            site_path += '/'
            for ep in error_paths:
                if site_path.find(ep) == 0:
                    return False
            return True
        except:
            return False

    @staticmethod
    def _get_sys_path():
        """
            @name 关键目录
            @author hwliang<2021-06-11>
            @return tuple
        """
        a = ['/www', '/usr', '/', '/dev', '/home', '/media', '/mnt', '/opt', '/tmp', '/var']
        c = ['/www/.Recycle_bin/', '/www/backup/', '/www/php_session/', '/www/wwwlogs/', '/www/server/', '/etc/',
             '/usr/', '/var/', '/boot/', '/proc/', '/sys/', '/tmp/', '/root/', '/lib/', '/bin/', '/sbin/', '/run/',
             '/lib64/', '/lib32/', '/srv/']
        return a, c

