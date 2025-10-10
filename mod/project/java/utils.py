import json
import re
import sys
import time
import zipfile
import os
import yaml
import psutil
import platform
import configparser
from xml.etree.ElementTree import Element, ElementTree, parse, XMLParser
from typing import Optional, Dict, Tuple, AnyStr, List, Any
import threading
import itertools

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

import public

def get_jar_war_config(jar_war_file: str) -> Optional[List[Tuple[str, AnyStr]]]:
    """获取jar文件中的配置文件"""
    if not os.path.exists(jar_war_file):
        return None
    if not zipfile.is_zipfile(jar_war_file):  # 判断是否为zip文件
        return None
    # 打开jar文件
    res_list = []
    with zipfile.ZipFile(jar_war_file, 'r') as jar:
        for i in jar.namelist():
            # 查询所有文件中可能是配置文件的项目
            if i.endswith("application.yaml") or i.endswith("application.yml"):
                with jar.open(i) as f:
                    res_list.append((i, f.read()))

    if not res_list:
        return None

    return res_list

def to_utf8(file_data_list: List[Tuple[str, AnyStr]]) -> List[Tuple[str, str]]:
    res_list = []
    for i, data in file_data_list:
        if isinstance(data, bytes):
            try:
                new_data = data.decode("utf-8")
            except:
                continue
            else:
                res_list.append((i, new_data))
    return res_list

def parse_application_yaml(conf_data_list: List[Tuple[str, AnyStr]]) -> List[Tuple[str, Dict]]:
    res_list = []
    for i, data in conf_data_list:
        d = yaml.safe_load(data)
        if isinstance(d, dict):
            res_list.append((i, d))

    return res_list

# 接收一个jdk路径并将其规范化
def normalize_jdk_path(jdk_path: str) -> Optional[str]:
    if jdk_path.endswith("/java"):
        jdk_path = os.path.dirname(jdk_path)
    if jdk_path.endswith("/bin"):
        jdk_path = os.path.dirname(jdk_path)
    if jdk_path.endswith("/jre"):
        jdk_path = os.path.dirname(jdk_path)
    if not os.path.isdir(jdk_path):
        return None
    if not os.path.exists(os.path.join(jdk_path, "bin/java")):
        return None
    return jdk_path

def test_jdk(jdk_path: str) -> bool:
    java_bin = os.path.join(jdk_path, "bin/java")
    if os.path.exists(java_bin):
        out, err = public.ExecShell("{} -version 2>&1".format(java_bin))
        # type: str, str
        if out.lower().find("version") != -1:
            return True
    return False

class TomCat:

    def __init__(self, tomcat_path: str):
        self.path = tomcat_path.rstrip("/")  # 移除多余的右"/" 统一管理
        self._jdk_path: Optional[str] = None
        self._config_xml: Optional[ElementTree] = None
        self._bt_tomcat_conf: Optional[dict] = None
        self._log_file = None
        self._version = None
        self._service_name = None

    @property
    def service_name(self):
        if self._service_name is not None:
            return self._service_name
        if self.path.startswith("/www/server/bt_tomcat_web/"):
            service_name = self.path.split("/")[-1]
        else:
            service_name = "bt_tomcat_{}".format(self.path[-1])
        self._service_name = service_name
        return self._service_name

    @property
    def service_exists(self) -> bool:
        return os.path.exists("/usr/lib/systemd/system/{}.service".format(self.service_name))

    def set_service(self, user: str = "root", auto_start: bool = False):
        with tmp_close_security(user) as t:
            from mod.base.process.server import RealServer
            change_auto_start = self.get_auto_restart() != auto_start
            if self.service_exists and self.service_name.startswith("bt_tomcat_") and not change_auto_start:  # 内置项目
                self.restart()
                return

            # 独立项目
            self._init_log_file(user)
            self.stop()
            res = RealServer().create_daemon(
                server_name=self.service_name,
                pid_file="",
                start_exec="{}/bin/daemon.sh start".format(self.path),
                stop_exec="{}/bin/daemon.sh stop".format(self.path),
                restart_type="always" if auto_start else "no",
                fork_time_out=0,
                workingdirectory=self.path,
                # environments="ExecStartPost={}".format(ppid_sh),
                user=user,
                is_fork=1,
                is_power_on=1 if auto_start else 0,
            )

    def remove_service(self):
        from mod.base.process.server import RealServer
        RealServer().del_daemon(self.service_name)

    @property
    def jdk_path(self) -> Optional[str]:
        p = os.path.join(self.path, "bin/daemon.sh")
        if not os.path.exists(p):
            return None

        tmp_data = public.readFile(p)
        if isinstance(tmp_data, str):
            rep_deemon_sh = re.compile(r"^JAVA_HOME=(?P<path>.*)\n", re.M)
            re_res_jdk_path = rep_deemon_sh.search(tmp_data)
            if re_res_jdk_path:
                self._jdk_path = re_res_jdk_path.group("path").strip()
                self._jdk_path = normalize_jdk_path(self._jdk_path)
                return self._jdk_path

        return None

    def version(self) -> Optional[int]:
        if isinstance(self._version, int):
            return self._version
        v_file = os.path.join(self.path, "version.pl")
        if os.path.isfile(v_file):
            ver = public.readFile(v_file)
            if isinstance(ver, str):
                try:
                    ver_int = int(ver.split(".")[0])
                    self._version = ver_int
                    return self._version
                except:
                    pass
        return None

    @property
    def log_file(self) -> str:
        if self._log_file is not None:
            return self._log_file
        default_file = os.path.join(self.path, "logs/catalina-daemon.out")
        target_sh = os.path.join(self.path, "bin/daemon.sh")
        file_data = public.readFile(target_sh)
        conf_path = os.path.join(self.path, "conf/logpath.conf")
        if not isinstance(file_data, str):
            return default_file
        rep = re.compile(r'''\n\s?test ?"\.\$CATALINA_OUT" ?= ?\. +&& +CATALINA_OUT=['"](?P<path>\S+)['"]''')
        if rep.search(file_data):
            self._log_file = rep.search(file_data).group("path")
            public.writeFile(conf_path, os.path.dirname(self._log_file))
            return self._log_file

        if os.path.isfile(conf_path):
            path = public.readFile(conf_path)
        else:
            return default_file
        log_file = os.path.join(path, "catalina-daemon.out")
        if os.path.exists(log_file):
            self._log_file = log_file
            return self._log_file

        ver = self.version()
        if ver:
            public.print_log(ver)
            # public.print_log(log_file)
            log_file = os.path.join(path, "catalina-daemon-{}.out".format(ver))
            public.print_log(log_file)
            return log_file
        else:
            return os.path.join(path, "catalina-daemon.out")

    @property
    def bt_tomcat_conf(self) -> Optional[dict]:
        if self._bt_tomcat_conf is None:
            p = os.path.join(self.path, "bt_tomcat.json")
            if not os.path.exists(p):
                self._bt_tomcat_conf = { }
                return self._bt_tomcat_conf
            try:
                self._bt_tomcat_conf = json.loads(public.readFile(p))
            except:
                self._bt_tomcat_conf = { }
        return self._bt_tomcat_conf

    def save_bt_tomcat_conf(self):
        if self._bt_tomcat_conf is not None:
            p = os.path.join(self.path, "bt_tomcat.json")
            public.writeFile(p, json.dumps(self._bt_tomcat_conf))

    def change_log_path(self, log_path: str, prefix: str = "") -> bool:
        log_path = log_path.rstrip("/")
        target_sh = os.path.join(self.path, "bin/daemon.sh")
        if not os.path.exists(target_sh):
            return False
        file_data = public.readFile(target_sh)
        if not isinstance(file_data, str):
            return False
        rep = re.compile(r'''\n ?test ?"\.\$CATALINA_OUT" ?= ?\. && {0,3}CATALINA_OUT="[^\n]*"[^\n]*\n''')
        if prefix and not prefix.startswith("-"):
            prefix = "-{}".format(prefix)
        log_file = "{}/catalina-daemon{}.out".format(log_path, prefix)
        if not os.path.isfile(log_file):
            public.writeFile(log_file, "")
        repl = '\ntest ".$CATALINA_OUT" = . && CATALINA_OUT="{}"\n'.format(log_file)
        file_data = rep.sub(repl, file_data)
        public.writeFile(target_sh, file_data)
        conf_path = os.path.join(self.path, "conf/logpath.conf")
        public.WriteFile(conf_path, log_path)
        return True

    def change_default_user(self, user: str) -> bool:
        target_sh = os.path.join(self.path, "bin/daemon.sh")
        if not os.path.exists(target_sh):
            return False

        file_data = public.readFile(target_sh)
        if not isinstance(file_data, str):
            return False

        new_list = []
        for i in file_data.split("\n"):
            if i.startswith('test ".$TOMCAT_USER" = . && TOMCAT_USER='):
                new_list.append('test ".$TOMCAT_USER" = . && TOMCAT_USER="{}"'.format(user))
            else:
                new_list.append(i)
        public.writeFile(target_sh, "\n".join(new_list))
        # *同步更改tomcat安装目录所有者
        public.ExecShell(
            "chown -R {user}:{user} {tomcat_path}".format(
                user=user,
                tomcat_path=self.path
            )
        )
        return True

    @property
    def config_xml(self) -> Optional[ElementTree]:
        if self._config_xml is None:
            p = os.path.join(self.path, "conf/server.xml")
            if not os.path.exists(p):
                return None

            self._config_xml = parse(p, parser=XMLParser(encoding="utf-8"))
        return self._config_xml

    def is_error_config_xml(self) -> bool:
        try:
            _ = self.config_xml
        except:
            return True
        return False

    def set_port(self, port: int) -> bool:
        if self.config_xml is None:
            return False
        conf_elem = self.config_xml.findall("Service/Connector")
        if conf_elem is None:
            return False
        for i in conf_elem:
            if 'protocol' in i.attrib and 'port' in i.attrib:
                if i.attrib['protocol'] == 'HTTP/1.1':
                    i.attrib['port'] = str(port)
                    return True
        return False

    def pid(self) -> Optional[int]:
        if os.path.exists(self.pid_file()):
            # 使用psutil判断进程是否在运行
            try:
                pid = public.readFile(self.pid_file())
                return int(pid)
            except:
                return None
        return None

    def pid_file(self) -> str:
        return os.path.join(self.path, 'logs/catalina-daemon.pid')

    def port(self) -> int:
        try:
            if self.config_xml is None:
                return 0
            for i in self.config_xml.findall("Service/Connector"):
                if i.attrib.get("protocol") == "HTTP/1.1" and 'port' in i.attrib:
                    return int(i.attrib.get("port"))
        except:
            pass
        return 8080

    @property
    def installed(self) -> bool:
        start_path = os.path.join(self.path, 'bin/daemon.sh')
        conf_path = os.path.join(self.path, 'conf/server.xml')
        if not os.path.exists(self.path):
            return False
        if not os.path.isfile(start_path):
            return False
        if not os.path.isfile(conf_path):
            return False
        return True

    def running(self) -> bool:
        pid = self.pid()
        if pid:
            try:
                p = psutil.Process(pid)
                return p.is_running()
            except:
                return False
        return False

    def get_auto_restart(self) -> bool:
        out, _ = public.ExecShell("systemctl is-enabled {} 2> /dev/null".format(self.service_name))
        return out.strip() == "enabled"

    def status(self) -> dict:
        return {
            "status": os.path.exists(self.path) and os.path.exists(os.path.join(self.path, "bin/daemon.sh")),
            "jdk_path": self.jdk_path,
            "path": self.path,
            "running": self.running(),
            "port": self.port(),
            "auto_restart": self.get_auto_restart(),
            "stype": "built" if os.path.exists(os.path.join(self.path, "conf/server.xml")) else "uninstall"
        }

    def save_config_xml(self) -> bool:
        if self.config_xml is None:
            return False
        p = os.path.join(self.path, "conf/server.xml")

        def _indent(elem: Element, level=0):
            i = "\n" + level * "  "
            if len(elem):
                if not elem.text or not elem.text.strip():
                    elem.text = i + "  "
                if not elem.tail or not elem.tail.strip():
                    elem.tail = i
                for elem in elem:
                    _indent(elem, level + 1)
                if not elem.tail or not elem.tail.strip():
                    elem.tail = i
            else:
                if level and (not elem.tail or not elem.tail.strip()):
                    elem.tail = i

        _indent(self.config_xml.getroot())
        self.config_xml.write(p, encoding="utf-8", xml_declaration=True)
        return True

    def host_by_name(self, name: str) -> Optional[Element]:
        if self.config_xml is None:
            return None
        engines = self.config_xml.findall("Service/Engine")
        if not engines:
            return None
        engine = engines[0]
        for h in engine:
            if h.tag == "Host" and h.attrib.get("name", None) == name:
                return h
        return None

    def conf_has_doc_base(self, doc_base: str) -> bool:
        if self.config_xml is None:
            return False
        engines = self.config_xml.findall("Service/Engine")
        if not engines:
            return False
        engine = engines[0]
        context = engine.findall("Host/Context")
        for i in context:
            if i.attrib.get("docBase", None) == doc_base:
                return True
        return False

    def add_host(self, name: str, path: str, context_path: str = "") -> bool:
        if self.config_xml is None:
            return False
        if not os.path.exists(path):
            os.makedirs(path)

        if context_path and not context_path.startswith("/"):
            context_path = "/" + context_path
        context = Element(
            "Context",
            attrib={
                "docBase": path,
                "path": context_path,
                "reloadable": "true",
                "crossContext": "true",
            },
        )

        if self.host_by_name(name):
            # *相同域名时仅context添加
            hosts = self.config_xml.findall("Service/Engine/Host")
            for host in hosts:
                if host.get("name", "") == name:
                    host.append(context)
                    return True
            return False
        else:
            engines = self.config_xml.findall("Service/Engine")
            if not engines:
                return False
            engine = engines[0]

        host = Element(
            "Host",
            attrib={
                "autoDeploy": "true",
                "name": name,
                "unpackWARs": "true",
                "xmlNamespaceAware": "false",
                "xmlValidation": "false",
            },
        )
        host.append(context)
        engine.append(host)
        return True

    def set_host_path_by_name(self, name: str, path: str) -> bool:
        if self.config_xml is None:
            return False
        for i in self.config_xml.findall("Service/Engine/Host"):
            if i.attrib.get("name", None) != name:
                continue
            for j in i:
                if j.tag == "Context":
                    j.attrib["docBase"] = path
                    return True
        return False

    def remove_host(self, host_name: str, context_path: str = "") -> bool:
        # 增加仅移除context
        if self.config_xml is None:
            return False
        host, engines = self.host_by_name(host_name), self.config_xml.findall("Service/Engine")
        if not host or not engines:
            return False
        target_context, other_context_count = None, 0
        for i in host:
            if i.tag == "Context":
                if i.attrib["path"] == context_path:
                    target_context = i
                else:
                    other_context_count += 1
        if target_context is not None:
            host.remove(target_context)
        if not other_context_count:
            engines[0].remove(host)
        return True

    def mutil_remove_host(self, name_list: List[str]) -> bool:
        if self.config_xml is None:
            return False
        for name in name_list:
            self.remove_host(name)
        return False

    def _init_log_file(self, by_user: str = ""):
        if not by_user:
            by_user = self.user

        if not os.path.exists(self.log_file):
            public.writeFile(self.log_file, "")
        public.set_mode(self.log_file, "666")  # 保障其他用户也可以写入日志（syslog）
        public.ExecShell(
            "chown {usr}:{usr} {file}".format(usr=by_user, file=self.log_file)
        )
        pass_dir_for_user(os.path.dirname(self.log_file), by_user)

    def start(self, by_user: str = "") -> bool:
        with tmp_close_security(by_user) as t:
            if not by_user:
                by_user = self.user

            if self.running():
                return True

            self._init_log_file(by_user)
            self.change_default_user(by_user)
            if self.service_exists:
                public.ExecShell("systemctl start {}".format(self.service_name))
                if self.running():
                    return True

            daemon_file = os.path.join(self.path, "bin/daemon.sh")
            if not os.path.isfile(self.log_file):
                public.ExecShell("touch {}".format(self.log_file))
            public.ExecShell("chown {}:{} {}".format(by_user, by_user, self.log_file))
            public.ExecShell("bash {} start".format(daemon_file), user=by_user)

            return self.running()

    def stop(self) -> bool:
        if not self.running():
            return True

        if self.service_exists:
            public.ExecShell("systemctl stop {}".format(self.service_name))
            if not self.running():
                return True

        daemon_file = os.path.join(self.path, "bin/daemon.sh")
        public.ExecShell("bash {} stop".format(daemon_file))
        return not self.running()

    def restart(self, by_user: str = "") -> bool:
        with tmp_close_security(by_user) as t:
            if not by_user:
                by_user = self.user

            if self.service_exists:
                if not os.path.exists(self.log_file):
                    public.ExecShell(
                        "touch {file} && chown {user}:{user} {file}".format(file=self.log_file, user=by_user)
                    )

                self.change_default_user(by_user)

                public.ExecShell("systemctl restart {}".format(self.service_name))
                if self.running():
                    return True

            if self.running():
                self.stop()
            return self.start(by_user)

    @property
    def user(self) -> str:
        tomcat_path = self.path
        user = ""
        flag = 'test ".$TOMCAT_USER" = . && TOMCAT_USER='
        target_sh = os.path.join(tomcat_path, "bin/daemon.sh")
        if os.path.exists(target_sh):
            file_data = public.readFile(target_sh)
            if isinstance(file_data, str):
                for i in file_data.split("\n"):
                    if i.startswith(flag):
                        user = i.replace(flag, "").replace("\"", "").strip()
        return user

    def replace_jdk(self, jdk_path: str) -> Optional[str]:
        jdk_path = normalize_jdk_path(jdk_path)
        if not jdk_path:
            return "jdk路径错误或无法识别"

        deemon_sh_path = "{}/bin/daemon.sh".format(self.path)
        if not os.path.isfile(deemon_sh_path):
            return 'Tomcat启动文件丢失!'

        deemon_sh_data = public.readFile(deemon_sh_path)
        if not isinstance(deemon_sh_data, str):
            return 'Tomcat启动文件读取失败!'

        # deemon_sh
        rep_deemon_sh = re.compile(r"^JAVA_HOME=(?P<path>.*)\n", re.M)
        re_res_deemon_sh = rep_deemon_sh.search(deemon_sh_data)
        if not re_res_deemon_sh:
            return 'Tomcat启动文件解析失败!'

        jsvc_make_path = None
        for i in os.listdir(self.path + "/bin"):
            tmp_dir = "{}/bin/{}".format(self.path, i)
            if i.startswith("commons-daemon") and os.path.isdir(tmp_dir):
                make_path = tmp_dir + "/unix"
                if os.path.isdir(make_path):
                    jsvc_make_path = make_path
                    break

        if jsvc_make_path is None:
            return 'Jsvc文件丢失!'

        # 重装jsvc
        if os.path.isfile(self.path + "/bin/jsvc"):
            os.rename(self.path + "/bin/jsvc", self.path + "/bin/jsvc_back")

        if os.path.isfile(jsvc_make_path + "/jsvc"):
            os.remove(jsvc_make_path + "/jsvc")

        shell_str = r'''
cd {}
make clean
./configure --with-java={}
make
    '''.format(jsvc_make_path, jdk_path)
        public.ExecShell(shell_str)
        if os.path.isfile(jsvc_make_path + "/jsvc"):
            os.rename(jsvc_make_path + "/jsvc", self.path + "/bin/jsvc")
            public.ExecShell("chmod +x {}/bin/jsvc".format(self.path))
            os.remove(self.path + "/bin/jsvc_back")
        else:
            if os.path.isfile(self.path + "/bin/jsvc_back"):
                os.rename(self.path + "/bin/jsvc_back", self.path + "/bin/jsvc")
            return 'Jsvc编译失败!'

        new_deemon_sh_data = deemon_sh_data[:re_res_deemon_sh.start()] + (
            'JAVA_HOME={}\n'.format(jdk_path)
        ) + deemon_sh_data[re_res_deemon_sh.end():]
        public.writeFile(deemon_sh_path, new_deemon_sh_data)
        return None

    def reset_tomcat_server_config(self, port: int):
        ret = '''<Server port="{}" shutdown="SHUTDOWN">
    <Listener className="org.apache.catalina.startup.VersionLoggerListener" />
    <Listener SSLEngine="on" className="org.apache.catalina.core.AprLifecycleListener" />
    <Listener className="org.apache.catalina.core.JreMemoryLeakPreventionListener" />
    <Listener className="org.apache.catalina.mbeans.GlobalResourcesLifecycleListener" />
    <Listener className="org.apache.catalina.core.ThreadLocalLeakPreventionListener" />
    <GlobalNamingResources>
    <Resource auth="Container" description="User database that can be updated and saved" factory="org.apache.catalina.users.MemoryUserDatabaseFactory" name="UserDatabase" pathname="conf/tomcat-users.xml" type="org.apache.catalina.UserDatabase" />
    </GlobalNamingResources>
    <Service name="Catalina">
    <Connector connectionTimeout="20000" port="{}" protocol="HTTP/1.1" redirectPort="8490" />
    <Engine defaultHost="localhost" name="Catalina">
        <Realm className="org.apache.catalina.realm.LockOutRealm">
            <Realm className="org.apache.catalina.realm.UserDatabaseRealm" resourceName="UserDatabase" />
        </Realm>
        <Host appBase="webapps" autoDeploy="true" name="localhost" unpackWARs="true">
            <Valve className="org.apache.catalina.valves.AccessLogValve" directory="logs" pattern="%h %l %u %t &quot;%r&quot; %s %b" prefix="localhost_access_log" suffix=".txt" />
        </Host>
    </Engine>
    </Service>
</Server>'''.format(create_a_not_used_port(), port)
        public.WriteFile(self.path + '/conf/server.xml', ret)

    @staticmethod
    def _get_os_version() -> str:
        # 获取Centos
        if os.path.exists('/usr/bin/yum') and os.path.exists('/etc/yum.conf'):
            return 'Centos'
        # 获取Ubuntu
        if os.path.exists('/usr/bin/apt-get') and os.path.exists('/usr/bin/dpkg'):
            return 'Ubuntu'
        return 'Unknown'

    @classmethod
    def async_install_tomcat_new(cls, version: str, jdk_path: Optional[str], install_manage_sh: Optional[str] =None) -> Optional[str]:
        os_ver = cls._get_os_version()
        if version == "7" and os_ver == 'Ubuntu':
            return '当前系统不支持安装tomcat7！请安装其他版本'

        if jdk_path:
            jdk_path = normalize_jdk_path(jdk_path)
            if not jdk_path:
                return 'jdk路径错误或无法识别'
            if not test_jdk(jdk_path):
                return '指定的jdk不可用'

        if not jdk_path:
            jdk_path = ''

        shell_str = (
            'rm -rf /tmp/1.sh && '
            'wget -O /tmp/1.sh %s/install/src/webserver/shell/new_jdk.sh && '
            'bash /tmp/1.sh install %s %s'
        ) % (public.get_url(), version, jdk_path)

        if install_manage_sh:
            shell_str += '\n' + install_manage_sh

        if not os.path.exists("/tmp/panelTask.pl"):  # 如果当前任务队列并未执行，就把日志清空
            public.writeFile('/tmp/panelExec.log', '')
        soft_name = "Java项目Tomcat-" + version
        task_id = public.M('tasks').add(
            'id,name,type,status,addtime,execstr',
            (None, '安装[{}]'.format(soft_name), 'execshell', '0', time.strftime('%Y-%m-%d %H:%M:%S'), "{{\n{}\n}}".format(shell_str))
        )
        cls._create_install_wait_msg(task_id, version)

    @staticmethod
    def _create_install_wait_msg(task_id: int, version: str):
        from panel_msg.msg_file import message_mgr

        file_path = "/tmp/panelExec.log"
        if not os.path.exists(file_path):
            public.writeFile(file_path, "")

        soft_name = "Java项目Tomcat-" + version
        data = {
            "soft_name": soft_name,
            "install_status": "等待安装" + soft_name,
            "file_name": file_path,
            "self_type": "soft_install",
            "status": 0,
            "task_id": task_id
        }
        title = "等待安装" + soft_name
        res = message_mgr.collect_message(title, ["Java环境管理", soft_name], data)
        if isinstance(res, str):
            public.WriteLog("消息盒子", "安装信息收集失败")
            return None
        return res

    def default_port(self) -> Optional[int]:
        if self.path.find("bt_tomcat_web") != -1:  # 独立项目没有默认端口
            return None
        ver = self.version()
        default_dict = {
            7: 8231,
            8: 8232,
            9: 8233,
            10: 8234,
        }
        return default_dict.get(ver, None)

    # 修复配置文件
    def repair_config(self, config_list: List[Dict], port: int = None) -> Optional[str]:
        public.print_log("修复配置文件")
        if not port:
            port = self.default_port()
        if not port:
            return "没有Tomcat的默认端口，无法修复"

        self.reset_tomcat_server_config(port)
        self._config_xml = None

        engines = self.config_xml.findall("Service/Engine")
        if not engines:
            return None
        engine = engines[0]

        for cfg in config_list:
            if "name" not in cfg or "path" not in cfg:
                continue
            path = cfg["path"]
            name = cfg["name"]
            path_name = ""

            if not os.path.isfile(path):
                app_base = path
            else:
                app_base = os.path.dirname(path)
                if path.endswith(".war"):
                    path_name = os.path.basename(path).rsplit(".", 1)[0]

            host = Element(
                "Host", attrib={
                    # "appBase": app_base,
                    "autoDeploy": "true",
                    "name": name,
                    "unpackWARs": "true",
                    "xmlNamespaceAware": "false",
                    "xmlValidation": "false",
                }
            )

            host.append(
                Element(
                    "Context", attrib={
                        "docBase": path,
                        "path": path_name,
                        "reloadable": "true",
                        "crossContext": "true",
                    }
                )
            )

            engine.append(host)

        self.save_config_xml()

    def check_config(self, name: str, path: str, access_mode: str):
        # public.print_log(name)
        if self.is_error_config_xml():
            return "配置文件出错，请尝试修复项目"
        if not self.installed:
            return "Tomcat丢失请尝试修复项目"
        if access_mode == "domain":
            # public.print_log(self.host_by_name(name))
            if not self.host_by_name(name):
                return "Tomcat配置中没有当前域名，请尝试修复项目"
        else:
            if not self.conf_has_doc_base(path):
                return "Tomcat配置中没有当前项目路径，请尝试修复项目"
        return None

    @staticmethod
    def build_make_sh(get: public.dict_obj):
        version: str = get.base_version
        if version.startswith("tomcat"):
            version = version.replace("tomcat", "")
        args_list: List[str] = [version, get.install_type]
        if get.name:
            args_list.append("--name={}".format(get.name))
        if get.port:
            args_list.append("--port={}".format(get.port))
        if get.jdk_path:
            args_list.append("--jdk-path={}".format(get.jdk_path))
        if get.user:
            args_list.append("--user={}".format(get.user))
        if get.release_firewall:
            args_list.append("--release-firewall")
        if get.auto_start:
            args_list.append("--auto-start")
        if get.ps:
            args_list.append("--ps={}".format(get.ps))

        return "{}/pyenv/bin/python3 {}/script/manager_tomcat.py {}".format(
            public.get_panel_path(),
            public.get_panel_path(),
            " ".join(args_list)
        )


class SiteTomcat(TomCat):

    # 将某个Host之外的其他host都删除，实现ROOT访问的效果（不需要前置应用）
    def host_to_root(self, host_name: str, path: str, port: int) -> Optional[str]:
        if self.config_xml is None:
            return "配置文件读取错误，无法更改"
        target_host = self.host_by_name(host_name)
        engines = self.config_xml.findall("Service/Engine")
        if not engines:
            self.repair_config([{ "name": host_name, "path": path }], port=port)
            return "配置文件出错，已进行修复，请尝试重试"
        path_name = ""
        if os.path.isfile(path):
            app_base = os.path.dirname(path)
            if path.endswith(".war"):
                path_name = os.path.basename(path).rsplit(".", 1)[0]
        else:
            app_base = path
        engine = engines[0]
        remove_hosts = [i for i in engine.findall("Host")]
        for host in remove_hosts:
            engine.remove(host)

        if target_host:
            engine.append(target_host)
            target_host.set("name", "localhost")
        else:
            host = Element(
                "Host", attrib={
                    "autoDeploy": "true",
                    "name": "localhost",
                    "unpackWARs": "true",
                    "xmlNamespaceAware": "false",
                    "xmlValidation": "false",
                }
            )

            context = Element(
                "Context", attrib={
                    "docBase": path,
                    "path": path_name,
                    "reloadable": "true",
                    "crossContext": "true",
                }
            )
            host.append(context)
            engine.append(host)

        # public.print_log(list(engine))
        return

    def root_to_host(self, host_name: str, path: str, port: int) -> Optional[str]:
        if self.config_xml is None:
            return "配置文件读取错误，无法更改"

        path_name = ""
        if os.path.isfile(path):
            app_base = os.path.dirname(path)
            if path.endswith(".war"):
                path_name = os.path.basename(path).rsplit(".", 1)[0]
        else:
            app_base = path

        engines = self.config_xml.findall("Service/Engine")
        if not engines:
            return None
        engine = engines[0]

        host_list = engine.findall("Host")
        host_name_dict = { }
        for host in host_list:
            tmp_host_name = host.attrib.get("name", None)
            if not tmp_host_name:
                continue
            if tmp_host_name in host_name_dict:  # 出现重复的host name 则直接修复配置文件
                return self.repair_config([{ "name": host_name, "path": path }], port=port)
            host_name_dict[tmp_host_name] = host

        if host_name in host_name_dict:
            target_host = host_name_dict[host_name]
            # target_host.set("appBase", app_base)
            attr = target_host.attrib.copy()
            target_host.clear()
            for k, v in attr.items():
                target_host.set(k, v)
            context = Element(
                "Context", attrib={
                    "docBase": path,
                    "path": path_name,
                    "reloadable": "true",
                    "crossContext": "true",
                }
            )
            target_host.append(context)

            return None

        if "localhost" in host_name_dict and host_name_dict["localhost"].attrib.get("appBase") == path:
            target_host = host_name_dict["localhost"]
            target_host.set("name", host_name)

            default_host = Element(
                "Host", attrib={
                    "appBase": "webapps",
                    "autoDeploy": "true",
                    "name": "localhost",
                    "unpackWARs": "true",
                }
            )
            default_host.append(
                Element(
                    "Valve", attrib={
                        "className": "org.apache.catalina.valves.AccessLogValve",
                        "directory": "logs",
                        "prefix": "localhost_access_log",
                        "suffix": ".txt",
                        "pattern": "%h %l %u %t &quot;%r&quot; %s %b"
                    }
                )
            )
            engine.insert(1, default_host)
            return

        return self.repair_config([{ "name": host_name, "path": path }], port=port)

def bt_tomcat(ver: int) -> Optional[TomCat]:
    if ver not in (7, 8, 9, 10) and ver not in ("7", "8", "9", "10"):
        return None
    return TomCat(tomcat_path="/usr/local/bttomcat/tomcat%d" % int(ver))

def site_tomcat(site_name: str) -> Optional[SiteTomcat]:
    tomcat_path = os.path.join("/www/server/bt_tomcat_web", site_name)
    if not os.path.exists(tomcat_path):
        return None
    return SiteTomcat(tomcat_path=tomcat_path)

class JDKManager:

    def __init__(self):
        self._versions_list: Optional[List[str]] = None
        self._custom_jdk_list: Optional[List[str]] = None
        self._jdk_path = "/www/server/java"
        self._custom_file = "/www/server/panel/data/get_local_jdk.json"
        if not os.path.exists(self._jdk_path):
            os.makedirs(self._jdk_path, 0o755)

    @property
    def versions_list(self) -> List[str]:
        if self._versions_list:
            return self._versions_list
        jdk_json_file = '/www/server/panel/data/jdk.json'
        tip_file = '/www/server/panel/data/jdk.json.pl'
        try:
            last_refresh = int(public.readFile(tip_file))
        except ValueError:
            last_refresh = 0
        versions_data = public.readFile(jdk_json_file)
        if time.time() - last_refresh > 3600:
            public.run_thread(public.downloadFile, ('{}/src/jdk/jdk.json'.format(public.get_url()), jdk_json_file))
            public.writeFile(tip_file, str(int(time.time())))

        try:
            versions = json.loads(versions_data)
        except Exception:
            versions = {
                "x64": [
                    "jdk1.7.0_80", "jdk1.8.0_371", "jdk-9.0.4", "jdk-10.0.2",
                    "jdk-11.0.19", "jdk-12.0.2", "jdk-13.0.2", "jdk-14.0.2",
                    "jdk-15.0.2", "jdk-16.0.2", "jdk-17.0.8", "jdk-18.0.2.1",
                    "jdk-19.0.2", "jdk-20.0.2"
                ],
                "arm": [
                    "jdk1.8.0_371", "jdk-11.0.19", "jdk-15.0.2", "jdk-16.0.2",
                    "jdk-17.0.8", "jdk-18.0.2.1", "jdk-19.0.2", "jdk-20.0.2"
                ],
                "loongarch64": [
                    "jdk-8.1.18", "jdk-11.0.22", "jdk-17.0.10", "jdk-21.0.2"
                ]
            }
        arch = platform.machine()
        if arch == "aarch64" or 'arm' in arch:
            arch = "arm"
        elif arch == "loongarch64":
            arch = "loongarch64"
        elif arch == "x86_64":
            arch = "x64"

        self._versions_list = versions.get(arch, [])
        return self._versions_list

    def jdk_list_path(self) -> List[str]:
        return ["{}/{}".format(self._jdk_path, i) for i in self.versions_list]

    @property
    def custom_jdk_list(self) -> List[str]:
        if self._custom_jdk_list:
            return self._custom_jdk_list

        try:
            self._custom_jdk_list = json.loads(public.readFile(self._custom_file))
        except:
            self._custom_jdk_list = []

        if not isinstance(self._custom_jdk_list, list):
            self._custom_jdk_list = []

        return self._custom_jdk_list

    def add_custom_jdk(self, jdk_path: str) -> Optional[str]:
        jdk_path = normalize_jdk_path(jdk_path)
        if not jdk_path:
            return "jdk路径错误或无法识别"

        if jdk_path in self.custom_jdk_list or jdk_path in self.jdk_list_path:
            return

        self.custom_jdk_list.append(jdk_path)
        public.writeFile(self._custom_file, json.dumps(self.custom_jdk_list))

    def remove_custom_jdk(self, jdk_path: str) -> None:
        if jdk_path not in self.custom_jdk_list:
            return

        self.custom_jdk_list.remove(jdk_path)
        public.writeFile(self._custom_file, json.dumps(self.custom_jdk_list))

    def async_install_jdk(self, version: str) -> None:
        sh_str = "cd /www/server/panel/install && /bin/bash install_soft.sh {} install {} {}".format(0, 'jdk', version)

        if not os.path.exists("/tmp/panelTask.pl"):  # 如果当前任务队列并未执行，就把日志清空
            public.writeFile('/tmp/panelExec.log', '')
        task_id = public.M('tasks').add(
            'id,name,type,status,addtime,execstr',
            (None, '安装[{}]'.format(version), 'execshell', '0', time.strftime('%Y-%m-%d %H:%M:%S'), sh_str)
        )

        self._create_install_wait_msg(task_id, version)

    @staticmethod
    def _create_install_wait_msg(task_id: int, version: str):
        from panel_msg.msg_file import message_mgr

        file_path = "/tmp/panelExec.log"
        if not os.path.exists(file_path):
            public.writeFile(file_path, "")

        data = {
            "soft_name": version,
            "install_status": "等待安装" + version,
            "file_name": file_path,
            "self_type": "soft_install",
            "status": 0,
            "task_id": task_id
        }
        title = "等待安装" + version
        res = message_mgr.collect_message(title, ["Java环境管理", version], data)
        if isinstance(res, str):
            public.WriteLog("消息盒子", "安装信息收集失败：" + res)
            return None
        return res

    def install_jdk(self, version: str) -> Optional[str]:
        if version not in self.versions_list:
            return "版本不存在, 无法安装"

        if os.path.exists(self._jdk_path + "/" + version):
            return "已存在的版本, 无法再次安装，如需再次安装请先卸载"

        if os.path.exists("{}/{}.pl".format(self._jdk_path, version)):
            return "安装任务进行中，请勿再次添加"

        public.writeFile("{}/{}.pl".format(self._jdk_path, version), "installing")
        t = threading.Thread(target=self._install_jdk, args=(version,))
        t.start()
        return None

    def _install_jdk(self, version: str) -> None:
        try:
            log_file = "{}/{}_install.log".format(self._jdk_path, version)
            if not os.path.exists('/www/server/panel/install/jdk.sh'):
                public.ExecShell('wget -O /www/server/panel/install/jdk.sh ' + public.get_url() + '/install/0/jdk.sh')
            public.ExecShell('bash /www/server/panel/install/jdk.sh install {} 2>&1 > {}'.format(version, log_file))
        except:
            pass
        public.ExecShell('rm -rf /www/server/java/{}.*'.format(version))

    def uninstall_jdk(self, version: str) -> Optional[str]:
        if not os.path.exists(self._jdk_path + "/" + version):
            return "没有安装指定的版本，无法卸载"
        public.ExecShell('rm -rf /www/server/java/{}*'.format(version))
        return

    @staticmethod
    def set_jdk_env(jdk_path) -> Optional[str]:
        if jdk_path != "":
            jdk_path = normalize_jdk_path(jdk_path)
            if not jdk_path:
                return "jdk路径错误或无法识别"

        # 写入全局的shell配置文件
        profile_path = '/etc/profile'
        java_home_line = "export JAVA_HOME={}".format(jdk_path) if jdk_path else ""
        path_line = "export PATH=$JAVA_HOME/bin:$PATH"
        profile_data = public.readFile(profile_path)
        if not isinstance(profile_data, str):
            return "无法读取环境变量文件"

        rep_java_home = re.compile(r"export\s+JAVA_HOME=.*\n")
        rep_path = re.compile(r"export\s+PATH=\$JAVA_HOME/bin:\$PATH\s*?\n")
        if rep_java_home.search(profile_data):
            profile_data = rep_java_home.sub(java_home_line, profile_data)
        elif jdk_path:
            profile_data = profile_data + "\n" + java_home_line

        if rep_path.search(profile_data):
            if not jdk_path:
                profile_data = rep_path.sub("", profile_data)
        elif jdk_path:
            profile_data = profile_data + "\n" + path_line

        try:
            with open(profile_path, "w") as f:
                f.write(profile_data)
        except PermissionError:
            return "无法修改环境变量，可能是系统加固插件拒绝了操作"
        except:
            return "修改失败"

        return

    @staticmethod
    def get_env_jdk() -> Optional[str]:
        profile_data = public.readFile('/etc/profile')
        if not isinstance(profile_data, str):
            return None
        current_java_home = None
        for line in profile_data.split("\n"):
            if 'export JAVA_HOME=' in line:
                current_java_home = line.split('=')[1].strip().replace('"', '').replace("'", "")

        return current_java_home

# 通过JVM临时目录获取进程pid，速度较快，不一定准确
# 默认 /tmp 下所有用户的java进程
def jps(tmp_path: str = None, user_name: str = None) -> List[int]:
    if not tmp_path:
        tmp_path = "/tmp"
    else:
        tmp_path = tmp_path.rstrip("/")
    if not os.path.exists(tmp_path):
        return []
    if user_name:
        dir_list = [i for i in os.listdir(tmp_path) if i == "hsperfdata_{}".format(user_name)]
    else:
        dir_list = [i for i in os.listdir(tmp_path) if i.startswith("hsperfdata_")]
    return [int(j) for j in itertools.chain(*[os.listdir(tmp_path + "/" + i) for i in dir_list]) if j.isdecimal()]

def js_value_to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "yes", "1")
    return bool(value)

def check_port_with_net_connections(port: int) -> bool:
    try:
        for conn in psutil.net_connections():
            if conn.status == 'LISTEN' and conn.laddr.port == port:
                return False
    except:
        pass
    return True

def check_port(port) -> bool:
    """
    返回false表示端口不可用
    """
    try:
        if not isinstance(port, int):
            port = int(port)
    except:
        return False
    if port == 0:
        return False
    if not 0 < port < 65535:
        return False
    project_list = public.M('sites').field('name,path,project_config').select()
    for project_find in project_list:
        try:
            project_config = json.loads(project_find['project_config'])
        except json.JSONDecodeError:
            continue
        if 'port' not in project_config or not project_config['port']:  # '' 0 None 时都跳过
            continue
        if int(project_config['port']) == port:
            return False

    try:
        for conn in psutil.net_connections():
            if conn.status == 'LISTEN' and conn.laddr.port == port:
                return False
    except:
        pass

    # 检测特殊端口
    return public.checkPort(str(port))

def pass_dir_for_user(path_dir: str, user: str):
    """
    给某个用户，对应目录的执行权限
    """
    import stat
    if not os.path.isdir(path_dir):
        return
    try:
        import pwd
        uid_data = pwd.getpwnam(user)
        uid = uid_data.pw_uid
        gid = uid_data.pw_gid
    except:
        return

    if uid == 0:
        return

    if path_dir[:-1] == "/":
        path_dir = path_dir[:-1]

    while path_dir != "/":
        path_dir_stat = os.stat(path_dir)
        if path_dir_stat.st_uid == 0:
            old_mod = stat.S_IMODE(path_dir_stat.st_mode)
            if not old_mod & (1 << 3):
                os.chmod(path_dir, old_mod + (1 << 3))  # chmod g+x
        if path_dir_stat.st_uid == uid:
            old_mod = stat.S_IMODE(path_dir_stat.st_mode)
            if not old_mod & (1 << 6):
                os.chmod(path_dir, old_mod + (1 << 6))  # chmod u+x
        elif path_dir_stat.st_gid == gid:
            old_mod = stat.S_IMODE(path_dir_stat.st_mode)
            if not old_mod & (1 << 3):
                os.chmod(path_dir, old_mod + (1 << 6))  # chmod g+x
        elif path_dir_stat.st_uid != uid or path_dir_stat.st_gid != gid:
            old_mod = stat.S_IMODE(path_dir_stat.st_mode)
            if not old_mod & 1:
                os.chmod(path_dir, old_mod + 1)  # chmod o+x
        path_dir = os.path.dirname(path_dir)

def create_a_not_used_port() -> int:
    """
    生成一个可用的端口
    """
    import random
    while True:
        port = random.randint(2000, 65535)
        if check_port_with_net_connections(port):
            return port

# 记录项目是通过用户停止的
def stop_by_user(project_id):
    file_path = "{}/data/push/tips/project_stop.json".format(public.get_panel_path())
    if not os.path.exists(file_path):
        data = { }
    else:
        data_content = public.readFile(file_path)
        try:
            data = json.loads(data_content)
        except json.JSONDecodeError:
            data = { }
    data[str(project_id)] = True
    public.writeFile(file_path, json.dumps(data))

# 记录项目是通过用户操作启动的
def start_by_user(project_id):
    file_path = "{}/data/push/tips/project_stop.json".format(public.get_panel_path())
    if not os.path.exists(file_path):
        data = { }
    else:
        data_content = public.readFile(file_path)
        try:
            data = json.loads(data_content)
        except json.JSONDecodeError:
            data = { }
    data[str(project_id)] = False
    public.writeFile(file_path, json.dumps(data))

def is_stop_by_user(project_id):
    file_path = "{}/data/push/tips/project_stop.json".format(public.get_panel_path())
    if not os.path.exists(file_path):
        data = { }
    else:
        data_content = public.readFile(file_path)
        try:
            data = json.loads(data_content)
        except json.JSONDecodeError:
            data = { }
    if str(project_id) not in data:
        return False
    return data[str(project_id)]

# # 内置项目复制Tomcat
# def check_and_copy_tomcat(version: int):
#     old_path = "/usr/local/bttomcat/tomcat_bak%d"
#     new_path = "/usr/local/bt_mod_tomcat/tomcat%d"
#     if not os.path.exists("/usr/local/bt_mod_tomcat"):
#         os.makedirs("/usr/local/bt_mod_tomcat", 0o755)
#
#     src_path = old_path % version
#     if not os.path.exists(old_path % version) or not os.path.isfile(src_path + '/conf/server.xml'):
#         return
#     if os.path.exists(new_path % version):
#         return
#     else:
#         os.makedirs(new_path % version)
#
#     public.ExecShell('cp -r %s/* %s ' % (src_path, new_path % version,))
#     t = bt_tomcat(version)
#     if t:
#         t.reset_tomcat_server_config(8330 + version - 6)


# def tomcat_install_status() -> List[dict]:
#     res_list = []
#     install_path = "/usr/local/bttomcat/tomcat_bak%d"
#     for i in range(7, 11):
#         src_path = install_path % i
#         start_path = src_path + '/bin/daemon.sh'
#         conf_path = src_path + '/conf/server.xml'
#         if os.path.exists(src_path) and os.path.isfile(start_path) and os.path.isfile(conf_path):
#             res_list.append({"version": i, "installed": True})
#         else:
#             res_list.append({"version": i, "installed": False})
#     return res_list


class TemporaryBtSecurityCloser:
    _ini_file = "/usr/local/usranalyse/etc/usranalyse.ini"

    def __init__(self, user_name: str):
        self.has_bt_security = os.path.isfile(self._ini_file)
        self.user_name = user_name
        self.old_status = False

    def __enter__(self):
        if not self.has_bt_security:
            return self

        conf = configparser.ConfigParser()
        conf.read(self._ini_file)
        try:
            stop_chain = conf.get("usranalyse", "userstop_chain")
            stop_chain_data = stop_chain.strip().strip('"')
        except:
            stop_chain_data = ""
        if stop_chain_data and isinstance(stop_chain_data, str) and stop_chain_data.startswith("stop_uid:"):
            stop_users = stop_chain_data[len("stop_uid:"):].split(",")
            if self.user_name in stop_users:
                self.old_status = True
                stop_users.remove(self.user_name)
                conf.set("usranalyse", "userstop_chain",'"stop_uid:{}"'.format(",".join(stop_users)))
                conf.write(open(self._ini_file, "w"))
        return  self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.has_bt_security or not self.old_status:
            return

        conf = configparser.ConfigParser()
        conf.read(self._ini_file)
        try:
            stop_chain = conf.get("usranalyse", "userstop_chain")
            stop_chain_data = stop_chain.strip().strip('"')
        except:
            return
        if stop_chain_data and isinstance(stop_chain_data, str) and stop_chain_data.startswith("stop_uid:"):
            stop_users = stop_chain_data[len("stop_uid:"):].split(",")
            if self.user_name not in stop_users:
                stop_users.append(self.user_name)
                conf.set("usranalyse", "userstop_chain", '"stop_uid:{}"'.format(",".join(stop_users)))
                conf.write(open(self._ini_file, "w"))
        return


def tmp_close_security(user: str):
    return TemporaryBtSecurityCloser(user)


def not_systemd() -> bool:
    res = public.readFile("/proc/1/comm")
    if isinstance(res, str) and res.strip() == "systemd":
        return False
    return True