import itertools
import os
import re
import zipfile

import psutil
import yaml
import public
from mod.project.java import utils

from typing import Optional, List, Tuple, AnyStr, Dict, Callable, Any

"""
针对jar包的【spring boot】配置文件加载逻辑

原理：spring boot 会在固定路径下寻找配置文件
    PWD = 运行目录
    CLASSES = jar包中的类目录
    默认路径顺序：
        PWD/config > PWD > CLASSES/config > CLASSES

# 补充  
 --spring.config.name == application   可以用于指定配置文件前缀

这个些路径可以被配置项spring.config.location 更改，可以指定为多个目录或文件，但该配置项目，一般不会在配置文件中使用，而是在命令行
或者环境变量中使用。
在加载完成application.properties 或 application.yml文件后，一般会根据配置项spring.profiles.active 来加载
子配制项， 例如 spring.profiles.active=dev， 则会加载application-dev.properties 或 application-dev.yml文件。
同时，spring boot 会根据配置项spring.profiles.include 来加载子配制项， 例如 spring.profiles.include=dev1,dev2， 
则会加载application-dev1（2）.properties 或 application-dev1（2）.yml文件。
按照激活顺序，后面的配置项将会覆盖前面的配置项。

故： 该模块主要支持从jar、命令行中环境变量中获取spring boot配置信息

判断依据：命令行 > 环境变量 > jar包中配置文件
命令行 和 环境变量 
    先检查spring.config.location （SPRING_CONFIG_LOCATION）
        有： 从location 位置加载
        无： 从jar加载
    在检查 spring.profiles.active （SPRING_CONFIG_ACTIVE）
        有： 记录一下激活的 flag
        无： 不记录

    解析文件
    先从 jar 和 location 加载所有配置
    然后 如果没有 flag ： 从配置所有 主配置 （application.properties 或 application.yml）中加载 flag项（spring.profiles.active）
    然后 从包含的 flag 和 主配置 加载 spring.profiles.include

    最后 组合这些项目并分析其中的外部依赖

"""


class SpringConfigParser:
    other_server_keywords = (
        "redis",
        "rabbitmq",
        "rocketmq",
        "kafka",
        "elasticsearch",
    )
    rep_jdbc_url = re.compile(r"jdbc:(?P<db>\S+)://(?P<host>.*?):(?P<port>\d+)/(?P<name>[^?\s]*)")
    localhost_key = ("localhost", "127.0.0.1", "0.0.0.0", public.get_server_ip(), public.get_network_ip())

    # 其他服务解析host时， 不支持 ${XXX} 的格式
    rep_host_port = re.compile(
        r'^(?P<host>(((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|'  # ipv4
        r'(\[?(([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|::[0-9a-fA-F]{0,4})]?)|localhost))'  # ipv6 + localhost
        r':(?P<port>[0-9]{1,5})$')  # 端口

    def __init__(self, jar_path: str, process: int = -1, cmd: str = None,
                 env_list: List[dict] = None, env_file: str = None):
        self.jar_path = jar_path
        self.find_flag_list = []  # 获取到的配置文件flag列表
        self.location_conf_list = []  # 从外部加载的配置文件列表
        self.not_used_flag_list = []  # 从外部加载的配置文件列表
        self.cmd = cmd
        self.pwd: str = ""
        self.config_name = "application"
        if not isinstance(process, int) or process <= 0:
            process = -1
        try:
            p = psutil.Process(process)
            self.pwd = p.cwd()
        except:
            self.process_env = {}
        else:
            self.process_env = p.environ()
            if not self.cmd:
                self.cmd = " ".join(p.cmdline())

        self.find_by_default = True

        if not self.pwd or not os.path.isdir(self.pwd):
            self.pwd = os.path.dirname(self.jar_path)

        self.my_sql_root_auth = None

        if env_list:
            for i in env_list:
                if "k" in i and "v" in i:
                    self.process_env[i["k"]] = i["v"]
                    break
        if env_file:
            self.process_env.update(self.get_env_file_data(env_file))

        self.location_tip_list = []
        self.raw_data = {}

    @staticmethod
    def get_env_file_data(env_file) -> dict:
        if not os.path.exists(env_file):
            return {}
        data = {}
        out, _ = public.ExecShell(". {} && env".format(env_file), env={"PATH": os.environ["PATH"]})
        for i in out.split('\n'):
            if "=" not in i:
                continue
            k, v = i.split("=", 1)
            if k in ("PATH", "SHLVL", "PWD", "_"):
                continue
            if k and v:
                data[k] = v
        return data

    def format_location_conf(self, location_str: str) -> List[str]:
        res = []
        for i in location_str.split(","):
            tmp = i.strip()
            if not tmp:
                continue
            if tmp.startswith("file:"):
                tmp = tmp[5:]
            if tmp.startswith("/"):
                if os.path.exists(tmp):
                    res.append(tmp)
                else:
                    self.location_tip_list.append({
                        "type": "config_location",
                        "level": "error",
                        "msg": "配置文件路径：{}不存在于文件系统中".format(tmp)
                    })
            else:
                path = os.path.abspath(os.path.join(self.pwd, tmp))
                if os.path.exists(path):
                    res.append(os.path.join(self.pwd, tmp))
                else:
                    self.location_tip_list.append({
                        "type": "config_location",
                        "level": "error",
                        "msg": "配置文件路径：{}不存在于文件系统中".format(tmp)
                    })

        return res

    def _parser_by_cmd_or_env(self):
        """从命令行或者环境变量中获取配置信息"""
        # 检查 location 配置项
        # 先从cmd中获取, 再从环境变量中获取
        location_find = False
        name_find = False
        flag_find = False
        if self.cmd:
            rep_location = re.compile(r"-[-D]spring\.config\.location=(?P<location>\S+)")
            rep_name = re.compile(r"-[-D]spring\.config\.name=(?P<name>\S+)")
            rep_flag = re.compile(r"-[-D]spring\.profiles\.active=(?P<flag>\S+)")

            res = rep_location.search(self.cmd)
            if res:
                location_find = True
                location_str = res.group("location").strip("'\"")
                location_file = self.format_location_conf(location_str)
                self.location_conf_list.extend(location_file)
                self.find_by_default = False

            res = rep_name.search(self.cmd)
            if res:
                name_find = True
                self.config_name = res.group("name").strip().strip("'\"")

            res = rep_flag.search(self.cmd)
            if res:
                flag_find = True
                flags = res.group("flag").strip("'\"").split(",")
                self.find_flag_list.extend(flags)

        if self.process_env:
            if "SPRING_PROFILES_ACTIVE" in self.process_env and not flag_find:
                flags = self.process_env["SPRING_PROFILES_ACTIVE"].split(",")
                self.find_flag_list.extend(flags)

            if "SPRING_CONFIG_NAME" in self.process_env and not name_find:
                self.config_name = self.process_env["SPRING_CONFIG_NAME"]

            if "SPRING_CONFIG_LOCATION" in self.process_env and not location_find:
                location_str = self.process_env["SPRING_CONFIG_LOCATION"]
                location_file = self.format_location_conf(location_str)
                self.location_conf_list.extend(location_file)
                self.find_by_default = False

    # 从默认路径结构中获取配置文件信息
    def _get_all_config_by_default(self) -> List[Tuple[str, Dict]]:
        y_jar, p_jar = self.get_jar_config(self.jar_path)
        y_custom, p_custom = self.search_config_file_by_path(self.pwd)
        if os.path.exists(os.path.join(self.pwd, "config")):
            y_custom_c, p_custom_c = self.search_config_file_by_path(os.path.join(self.pwd, "config"))
            y_custom += y_custom_c
            p_custom += p_custom_c

        y_jar = self.to_utf8(y_jar)
        p_jar = self.to_utf8(p_jar)

        for i, data in itertools.chain(y_jar, y_custom, p_jar, p_custom):
            self.raw_data[i] = data

        ret = self.parse_application_yaml(y_custom + y_jar) + self.parse_application_properties(p_custom + p_jar)
        ret.sort(key=lambda x: x[0].startswith("/"), reverse=True)
        return ret

    def _get_all_config_by_location(self) -> List[Tuple[str, Dict]]:
        y_list, p_list = [], []
        for i in self.location_conf_list:
            if os.path.isdir(i):
                y_list_tmp, p_list_tmp = self.search_config_file_by_path(i)
                y_list.extend(y_list_tmp)
                p_list.extend(p_list_tmp)
            elif os.path.isfile(i):
                if i.endswith(".yml") or i.endswith(".yaml"):
                    data = public.readFile(i)
                    if data:
                        y_list.append((i, data))
                elif i.endswith(".properties"):
                    data = public.readFile(i)
                    if data:
                        p_list.append((i, data))

        for i, data in itertools.chain(y_list, p_list):
            self.raw_data[i] = data

        return self.parse_application_yaml(y_list) + self.parse_application_properties(p_list)

    def app_config(self) -> Tuple[List[Tuple[str, dict]], List[Tuple[str, dict]]]:
        """获取所有的配置信息， 并分为主配置和其他配置"""
        self._parser_by_cmd_or_env()
        if self.find_by_default:
            all_config = self._get_all_config_by_default()
        else:
            all_config = self._get_all_config_by_location()

        mian_conf, other_conf = [], []
        main_name = [self.config_name + i for i in (".yml", ".yaml", ".properties")]
        for i, conf in all_config:
            file_name = os.path.basename(i)
            if file_name in main_name:
                mian_conf.append((i, conf))
            else:
                other_conf.append((i, conf))

        used_conf = mian_conf
        self._get_flags_by_mian_conf(mian_conf)

        use_flag = []
        ned_del_other_conf = set()
        if self.find_flag_list:
            for idx, conf_data in enumerate(other_conf):
                file_name = os.path.basename(conf_data[0])
                tmp_flag = file_name[len(self.config_name) + 1:].rsplit(".", 1)[0]
                if tmp_flag in self.find_flag_list:
                    use_flag.append(tmp_flag)
                    used_conf.append(conf_data)
                    ned_del_other_conf.add(idx)

        self.not_used_flag_list = [i for i in self.find_flag_list if i not in use_flag]

        include_list = self._get_include_by_config_list(used_conf)
        if include_list:
            for idx, conf_data in enumerate(other_conf):
                file_name = os.path.basename(conf_data[0])
                tmp_flag = file_name[len(self.config_name) + 1:].rsplit(".", 1)[0]
                if tmp_flag in include_list:
                    used_conf.append(conf_data)
                    ned_del_other_conf.add(idx)

        ned_del_other_conf_idx = list(ned_del_other_conf)
        ned_del_other_conf_idx.sort(reverse=True)
        for i in ned_del_other_conf_idx:
            del other_conf[i]

        cmd_or_env_data = self.get_cmd_or_env_config()
        used_conf.append(("命令行或环境变量", cmd_or_env_data))  # 加到最后，优先级最高
        # public.print_log(used_conf)
        return used_conf, other_conf

    def get_cmd_or_env_config(self) -> dict:
        data = {}
        if self.process_env:
            for k, v in self.process_env.items():
                if not k.startswith("SPRING"):
                    continue

                key_list = [j.strip().lower() for j in k.split("_") if j.strip()]
                node = data
                for n in key_list[:-1]:
                    if n not in node:
                        node[n] = {}
                    node = node[n]
                node[key_list[-1]] = v

        if self.cmd:
            rep_spring = re.compile(r"-[-D]spring\.(?P<key>\S*?)=(?P<value>\S+)")
            for i in rep_spring.finditer(self.cmd):
                key = "spring." + i.group("key").lower()
                value = i.group("value")
                key_list = [j.strip() for j in key.split(".") if j.strip()]
                node = data
                for n in key_list[:-1]:
                    if n not in node:
                        node[n] = {}
                    node = node[n]
                node[key_list[-1]] = value

        return data

    def _get_flags_by_mian_conf(self, mian_conf: List[Tuple[str, dict]]):
        if self.find_flag_list:  # 在命令和环境变量中找到了就不需要了
            return

        try:
            flags = ""
            for i, conf in mian_conf:
                tmp_f = conf.get("spring", {}).get("profiles", {}).get("active", None)  # active 只有最后一个生效
                if isinstance(tmp_f, str):
                    flags = tmp_f

            if isinstance(flags, str) and flags:
                self.find_flag_list.extend([i.strip() for i in flags.split(",") if i.strip()])
        except:
            pass

    @staticmethod
    def _get_include_by_config_list(config_list: List[Tuple[str, dict]]) -> List[str]:
        include_list = []
        try:
            for i, conf in config_list:
                flags = conf.get("spring", {}).get("profiles", {}).get("include", None)
                if isinstance(flags, str):
                    include_list.extend([i.strip() for i in flags.split(",") if i.strip()])
        except:
            pass
        return include_list

    def get_jar_config(self, jar_file: str) -> Tuple[List[Tuple[str, AnyStr]], List[Tuple[str, AnyStr]]]:
        """获取jar文件中的配置文件"""
        if not os.path.exists(jar_file):
            return [], []
        if not zipfile.is_zipfile(jar_file):  # 判断是否为zip文件
            return [], []
        # 打开jar文件
        yaml_list = []
        prop_list = []
        with zipfile.ZipFile(jar_file, 'r') as jar:
            for i in jar.namelist():
                # 查询所有文件中可能是配置文件的项目
                i_base_name = os.path.basename(i)
                if i_base_name.find(self.config_name) == -1:
                    continue

                try:
                    if i_base_name.endswith(".yml") or i_base_name.endswith(".yaml"):
                        with jar.open(i) as f:
                            yaml_list.append((i, f.read()))

                    if i.endswith(".properties"):
                        with jar.open(i) as f:
                            prop_list.append((i, f.read()))
                except:
                    # public.print_log("压缩文件读取错误" + public.get_error_info())
                    continue

        return yaml_list, prop_list

    # 检测是不是项目的目录
    # 暂不使用
    @staticmethod
    def test_spring_boot_name(spring_path: str, target_name: str) -> bool:
        if os.path.isfile(spring_path + "/pom.xml"):
            data = public.readFile(spring_path + "/pom.xml")
            if data:
                start_idx = data.find("<artifactId>")
                if start_idx != -1:
                    name = data[start_idx + 12: data.find("</artifactId>", start_idx)]
                    if target_name.startswith(name):
                        return True

        if os.path.isfile(spring_path + "/build.gradle"):
            data = public.readFile(spring_path + "/build.gradle")
            if data:
                base_name_rep = re.compile(r'''archivesBaseName\s*=\s*['"]?(?P<name>\S+)["']?''', re.M)
                res = base_name_rep.search(data)
                if res and target_name.startswith(res.group("name")):
                    return True
        return False

    # 暂不使用
    def get_spring_project_src_by_path(self, path: str, target_name: str) -> Optional[str]:
        """"
        尝试寻找项目源文件位置
        寻找本层级、父层级、和两个子层级的spring boot项目目录  "src/main/resources"目录 和 "src/pom.xml"
        """
        if not os.path.isdir(path):
            return None

        parent_path = os.path.dirname(path)
        if os.path.isdir(parent_path + "/src/main/resources"):
            if self.test_spring_boot_name(parent_path, target_name):
                return parent_path

        def _get_by_sub(inpt_path: str, limit_num: int) -> Optional[str]:
            if limit_num < 0:
                return None

            for i in os.listdir(inpt_path):
                if i.startswith("."):
                    continue
                p = os.path.join(inpt_path, i)
                if os.path.isdir(p):
                    if os.path.isdir(p + "/src/main/resources"):
                        if self.test_spring_boot_name(p, target_name):
                            return p
                    if limit_num >= 1:
                        res = _get_by_sub(p, limit_num - 1)
                        if res is not None:
                            return res
            return None

        return _get_by_sub(path, 2)

    # 暂不使用
    def get_custom_spring_config(self, path: str) -> Tuple[List[Tuple[str, AnyStr]], List[Tuple[str, AnyStr]]]:
        """
        尝试寻找外部配置文件
        寻找本层级和子层级的spring boot配置文件
        """
        if not os.path.isdir(path):
            return [], []

        yaml_list, prop_list = [], []

        def _get_by_sub(inpt_path: str, limit_num: int):
            if limit_num < 0:
                return None
            y, p = self.search_config_file_by_path(inpt_path)
            yaml_list.extend(y)
            prop_list.extend(p)

            for i in os.listdir(inpt_path):
                tmp_p = os.path.join(inpt_path, i)
                if os.path.isdir(tmp_p):
                    _get_by_sub(tmp_p, limit_num - 1)

        _get_by_sub(path, 2)
        return yaml_list, prop_list

    # 用于搜索外部配置文件
    def search_config_file_by_path(self, path: str) -> Tuple[List[Tuple[str, AnyStr]], List[Tuple[str, AnyStr]]]:
        yaml_list, prop_list = [], []
        for i in os.listdir(path):
            # 查询所有文件中可能是配置文件的项目
            p = os.path.join(path, i)
            if i.find(self.config_name) != -1 and os.path.isfile(p):
                if i.endswith(".yml") or i.endswith(".yaml"):
                    tmp_data = public.readFile(p)
                    if isinstance(tmp_data, str):
                        yaml_list.append((p, tmp_data))

                if i.endswith(".properties"):
                    tmp_data = public.readFile(p)
                    if isinstance(tmp_data, str):
                        prop_list.append((p, tmp_data))

        return yaml_list, prop_list

    @staticmethod
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

    # 合并两个配置文件
    @classmethod
    def merge_dict_tries(cls, root: dict, node: dict):
        # 合并字典树， 用于分档的yaml配置文件
        for k, v in node.items():
            if isinstance(v, dict):
                if k not in root:
                    root[k] = {}
                cls.merge_dict_tries(root[k], v)
            else:
                root[k] = v

    @classmethod
    def parse_application_yaml(cls, conf_data_list: List[Tuple[str, AnyStr]]) -> List[Tuple[str, Dict]]:
        res_list = []
        for i, data in conf_data_list:
            try:
                d = yaml.safe_load_all(data)
                if isinstance(d, dict):
                    res_list.append((i, d))
                else:
                    tmp = {}
                    for j in d:
                        cls.merge_dict_tries(tmp, j)
                    res_list.append((i, tmp))
            except:
                print("yaml解析错误", i)
                continue

        return res_list

    @classmethod
    def _change_yaml_other_key_string(cls, conf_data_list: List[Tuple[str, Dict]]) -> List[Tuple[str, Dict]]:
        """将yml配置中的 非str类型的key转换为str， 因为spring boot配置中不存在单一的非str项目，方便后续spring boot配置检查"""

        def _change_dict_any(tmp_data: Dict[Any, Any]):
            keys = list(tmp_data.keys())
            for k in keys:
                v = tmp_data[k]
                if not isinstance(k, str):
                    new_key = str(k)
                    tmp_data[new_key] = v
                    del tmp_data[k]
                if isinstance(v, dict):
                    _change_dict_any(v)

        for _, data in conf_data_list:
            _change_dict_any(data)

        return conf_data_list

    @staticmethod
    def _parse_application_properties(data: str) -> dict:
        res_dict = {}

        # 添加时处理key
        def add_to_res_dict(res_dict_data: dict, tmp_k: str, tmp_value: str):
            key_list = tmp_k.split(".")
            if len(key_list) == 1:
                res_dict_data[key_list[0]] = tmp_value
                return

            node = res_dict_data
            for n in key_list[:-1]:
                if n not in node:
                    node[n] = {}
                node = node[n]
            node[key_list[-1]] = tmp_value

        last_line = ""
        for line in data.split("\n"):
            line = line.lstrip()  # type: str
            if line.startswith("#"):
                continue
            if line.endswith("\\"):
                last_line += line.rstrip("\\")
                continue
            else:
                if last_line:
                    line = last_line + line
                    last_line = ""
            if "=" in line:
                k, v = line.split("=", 1)
                tmp_v = v.strip()

                if "#" not in tmp_v and not tmp_v.startswith("'") and not tmp_v.startswith('"'):
                    add_to_res_dict(res_dict, k.strip(), tmp_v)
                    continue

                if (tmp_v.startswith("'") and tmp_v.endswith("'")) or (tmp_v.startswith('"') and tmp_v.endswith('"')):
                    value = tmp_v.strip("\"'")
                    add_to_res_dict(res_dict, k.strip(), value)
                    continue

                if tmp_v.startswith("#"):
                    continue

                last_idx = 0
                for _ in range(tmp_v.count("#")):
                    idx = tmp_v.find("#", last_idx + 1)
                    last_idx = idx
                    if tmp_v[idx - 1] != "\\":
                        break

                add_to_res_dict(res_dict, k.strip(), tmp_v[:last_idx].strip())

        return res_dict

    @classmethod
    def parse_application_properties(cls, conf_data_list: List[Tuple[str, AnyStr]]) -> List[Tuple[str, Dict]]:
        res_list = []
        for i, data in conf_data_list:
            try:
                tmp = cls._parse_application_properties(data)
                if tmp:
                    res_list.append((i, tmp))
            except:
                print("properties解析错误", i)
                continue

        return res_list

    def check_config_env(self, use_conf: List[Tuple[str, dict]]):
        """
        检测项目依赖的环境是否存在
        MySQL、Redis、RabbitMQ、Kafka、Elasticsearch、MongoDB

        Mysql检测用户是否存在
        """
        db_conf = {}
        other_server_conf = {}
        for i, spring_conf in use_conf:  # 检查的同时根据配置路径即 .spring.data.redis
            self.check_one_config_env(spring_conf, i, db_conf, other_server_conf)

        l_db, s_db = self.check_db_env(list(db_conf.values()))
        l_service, s_service = self.check_service_env(list(other_server_conf.values()))
        return l_db, s_db, l_service, s_service

    def check_one_config_env(self,
                             conf: dict,
                             file: str,
                             db_conf: Dict[str, dict] = None,
                             other_server_conf: Dict[str, dict] = None,
                             ) -> None:

        def _parse_keyword_nodes(node: dict) -> Tuple[str, str]:
            """
            形式1:   使用:分割
                # Kafka
                spring.kafka.bootstrap-servers = localhost:9092
                # 该字段见 Kafka 安装包中的 consumer.proerties，可自行修改, 修改完毕后需要重启 Kafka
                spring.kafka.consumer.group-id = test-consumer-group
                spring.kafka.consumer.enable-auto-commit = true
                spring.kafka.consumer.auto-commit-interval = 3000

            形式2:
                spring.data.redis.init.database = 11
                spring.data.redis.init.host = localhost
                spring.data.redis.init.port = 6379
            """
            host, port = "", ""
            if "host" in node:
                host = node["host"]
            if "port" in node:
                port = node["port"]

            if host and port:
                return host, port

            for v in node.values():
                if isinstance(v, dict):
                    host, port = _parse_keyword_nodes(v)
                    if host and port:
                        return host, port

                elif isinstance(v, str):
                    if ":" not in v:
                        continue
                    res = self.rep_host_port.search(v)
                    if res:
                        return res.group("host"), res.group("port")
            return "", ""

        def traversal_all_node(node: dict, last_key: str):
            for k, v in node.items():
                if not isinstance(v, dict):  # 如果子层级不是字典，不在检查
                    continue
                # 检查是不是一个数据库配置， 如果是就不必要检查子层级
                if "url" in v and isinstance(v["url"], str):
                    res = self.rep_jdbc_url.search(v["url"])
                    if res:
                        tmp = {
                            "url": v["url"],
                            "db": res.group("db"),
                            "host": res.group("host"),
                            "port": res.group("port"),
                            "name": res.group("name"),
                            "file": file,
                        }
                        if last_key + "." + k in db_conf:
                            db_conf[last_key + "." + k].update(tmp)
                            if "password" in v:
                                db_conf[last_key + "." + k]["password"] = v["password"]
                            if "username" in v:
                                db_conf[last_key + "." + k]["username"] = v["username"]
                        else:
                            tmp["password"] = v.get("password", "")
                            tmp["username"] = v.get("username", "")
                            db_conf[last_key + "." + k] = tmp
                        continue

                # 检测关键字
                if k in self.other_server_keywords:
                    host, port = _parse_keyword_nodes(v)
                    if host and port:
                        tmp = {
                            "key": k,
                            "host": host,
                            "port": port,
                            "file": file,
                        }
                        if last_key + "." + k in other_server_conf:
                            other_server_conf[last_key + "." + k].update(tmp)
                        else:
                            other_server_conf[last_key + "." + k] = tmp
                        continue

                # 不是一个数据库配置， 检查子层级
                traversal_all_node(v, last_key + "." + k)

        traversal_all_node(conf, "")

        # 处理 ${XXX} 格式的名称
        for i in db_conf.values():
            for tmp_k, tmp_v in i.items():
                if isinstance(tmp_v, str) and tmp_v.startswith("${") and tmp_v.endswith("}"):
                    tmp_v_list = tmp_v[2:-1].split(".")
                    tmp_node = conf
                    for j in tmp_v_list[:-1]:
                        tmp_node = tmp_node.get(j, {})
                    i[tmp_k] = tmp_node.get(tmp_v_list[-1], "")

        for i in other_server_conf.values():
            for tmp_k, tmp_v in i.items():
                public.print_log(tmp_k, tmp_v)
                if isinstance(tmp_v, str) and tmp_v.startswith("${") and tmp_v.endswith("}"):
                    public.print_log(tmp_v)
                    tmp_v_list = tmp_v[2:-1].split(".")
                    public.print_log(tmp_v_list)
                    tmp_node = conf
                    for j in tmp_v_list[:-1]:
                        tmp_node = tmp_node.get(j, {})
                    i[tmp_k] = tmp_node.get(tmp_v_list[-1], "")

        return None

    def check_db_env(self, db_conf: List[dict]):
        local_conf = []
        server_conf = []
        for i in db_conf:
            i["database"] = True  # 远程数据库默认不检查
            i["listening"] = True
            i["auth"] = True
            if i["host"] in self.localhost_key:
                i["is_local"] = True
                local_conf.append(i)
                if i["db"] in ("mysql", "postgresql", "mongodb"):
                    i["database"], i["auth"] = self.has_database(i["db"], i["name"], i["username"], i["password"])

                i["listening"] = False
                try:
                    i["listening"] = utils.check_port_with_net_connections(int(i["port"])) is False
                except:
                    pass

            else:
                i["is_local"] = False
                i["listening"] = self.port_is_open(i["host"], i["port"])
                server_conf.append(i)

        return local_conf, server_conf

    def check_service_env(self, service_conf: List[dict]):
        local_conf = []
        server_conf = []
        for i in service_conf:
            i["listening"] = True  # 远程数据库默认不检查
            if i["host"] in self.localhost_key:
                i["is_local"] = True
                local_conf.append(i)
                i["listening"] = False
                try:
                    i["listening"] = utils.check_port_with_net_connections(int(i["port"])) is False
                except:
                    pass

            else:
                i["is_local"] = False
                i["listening"] = self.port_is_open(i["host"], i["port"])
                server_conf.append(i)

        return local_conf, server_conf

    @staticmethod
    def port_is_open(host: str, port):
        import socket
        try:

            # 创建一个socket对象
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # 设置超时时间，防止连接挂起
            sock.settimeout(0.1)  # 5秒超时
            # 尝试连接到指定的端口
            result = sock.connect_ex((host, int(port)))
            # 关闭socket
            sock.close()
            # 如果连接成功，connect_ex返回0，否则返回错误代码
            return result == 0
        except Exception:
            return False

    def has_database(self, db_type: str, db_name: str, user_name: str, password: str) -> Tuple[bool, bool]:
        """
        返回数据库是否存在， 和数据库密码是否正确
        """
        if self.my_sql_root_auth is None and db_type == "mysql":
            try:
                self.my_sql_root_auth = public.M("config").where("id=1", ()).find()["mysql_root"]
            except:
                self.my_sql_root_auth = False
        try:
            find = public.M("databases").where("name=? AND LOWER(type)=?", (db_name, db_type.lower())).find()
            if find:
                if find["username"] == user_name and find["password"] == password:
                    return True, True  # 数据库和密码都存在
                if user_name == "root" and db_type == "mysql":
                    if self.my_sql_root_auth == password or self.my_sql_root_auth is False:
                        return True, True  # 数据库存在， 用的root密码
                return True, False  # 数据库存在， 密码未知
            else:
                if user_name == "root" and db_type == "mysql" and \
                        (self.my_sql_root_auth == password or self.my_sql_root_auth is False):
                    return False, True  # 数据库不存在， 用的root密码
                return False, False
        except:
            return False, False

    # 被外部调用的函数
    def get_tip(self) -> List[dict]:
        use, other = self.app_config()
        l_db, s_db, l_service, s_service = self.check_config_env(use)
        res = []
        # error 大概率存在错误的
        # 配置文件路径不存在
        if self.location_tip_list:
            res.extend(self.location_tip_list)

        # 本地数据库不存在
        for i in l_db:
            if i["listening"] is False:
                res.append({
                    "type": "local_database",
                    "level": "error",
                    "msg": "链接本地{}数据库的端口{}未被监听，可能是配置错误或数据库服务未开启".format(i["db"],
                                                                                                      i["port"])
                })

        # 本地数据连接不上
        for i in l_db:
            if i["auth"] is False:
                res.append({
                    "type": "local_database_auth",
                    "level": "warn",
                    "file": i["file"],
                    "msg": "链接到本地的{}数据库【{}】的用户名【{}】或密码【{}】可能错误".format(
                        i["db"], i["name"], i["username"], i["password"])
                })

        # warn 可能存在错误的
        # 本地数据库中没有数据数据库
        if l_db:
            for i in l_db:
                if i["database"] is False:
                    res.append({
                        "type": "local_database",
                        "level": "warn",
                        "file": i["file"],
                        "msg": "本地的{}数据库服务中未检测到数据库【{}】".format(i["db"], i["name"])
                    })
        # 本地服务未监听端口
        if l_service:
            for i in l_service:
                if i["listening"] is False:
                    res.append({
                        "type": "local_service",
                        "level": "warn",
                        "file": i["file"],
                        "msg": "链接本地【{}服务】的端口{}未被监听，可能是配置错误或服务未开启".format(i["key"], i["port"])
                    })

        # tip 有较低可能得存在的问题
        # 远程服务 或 远程数据库

        if s_db or s_service:
            for i in itertools.chain(s_db, s_service):
                if i["listening"] is False:
                    if "db" in i:
                        msg = "链接远程{}数据库服务【{}:{}/{}】，可能存在问题".format(
                            i["db"], i["host"], i["port"], i["name"]
                        )
                    else:
                        msg = "链接远程{}服务【{}:{}】，可能存在问题".format(i["key"], i["host"], i["port"])
                    res.append({
                        "type": "service",
                        "level": "tip",
                        "file": i["file"],
                        "msg": msg
                    })

        if self.not_used_flag_list:
            res.append({
                "type": "spring_profiles",
                "level": "tip",
                "file": None,
                "msg": "配置文件中提及了这些profiles ->【{}】，但实际未找到相关配置文件".format(
                    ",".join(self.not_used_flag_list))
            })

        return res


class SpringLogConfigParser(SpringConfigParser):
    """
    日志解析部分，主要依靠在配置中指定的logging.config
    """

    @staticmethod
    def get_config_data_by_use(use: List[Tuple[str, dict]], key: str) -> Optional[str]:
        key_list = [i for i in key.split(".") if i]
        if len(key_list) == 0:
            return None

        res_data = None
        for _, config in use:
            tmp_config = config
            for k in key_list:
                if k not in tmp_config:
                    break
                tmp_config = tmp_config[k]
            else:
                # 如果没有退出表示上面的key依序存在，且最后一次取出来的就是所需要的值
                res_data = tmp_config

        if not res_data or not isinstance(res_data, str):
            return None

        return res_data

    # 获取jar包内文件
    @staticmethod
    def get_jar_file_path(jar_file: str, jar_file_path: str) -> str:
        if not zipfile.is_zipfile(jar_file):  # 判断是否为zip文件
            return ""
        # 打开jar文件
        data = b''
        with zipfile.ZipFile(jar_file, 'r') as jar:
            if jar_file_path in jar.namelist():
                with jar.open(jar_file_path) as f:
                    data = f.read()

        if isinstance(data, bytes):
            try:
                return data.decode("utf-8")
            except:
                pass
        elif isinstance(data, str):
            return data

        return ""

    def get_all_log_ptah(self) -> List[str]:
        use, other = self.app_config()
        logging_config_data = self.get_config_data_by_use(use, "logging.config")
        if not logging_config_data:
            return []
        if not logging_config_data.endswith(".xml"):
            return []
        if logging_config_data.startswith("classpath:"):
            jar_file_path = "BOOT-INF/classes/{}".format(logging_config_data[10:].lstrip("/"))
            file_data = self.get_jar_file_path(self.jar_path, jar_file_path)
            filename = os.path.basename(jar_file_path)
        else:
            if logging_config_data.startswith("file:"):
                logging_config_data = logging_config_data[5:]
            file_data = public.readFile(logging_config_data)
            filename = os.path.basename(logging_config_data)

        if not file_data or not isinstance(file_data, str):
            return []

        # 闭包处理获取信息的过程
        def get_config(key: str) -> Optional[str]:
            return self.get_config_data_by_use(use, key)

        if filename.find("logback") != -1:
            return self.logback_parser(file_data, get_config)
        elif filename.find("log4j") != -1:
            return self.log4j_parser(file_data)
        elif file_data.find("rollingPolicy") != -1:
            return self.logback_parser(file_data, get_config)
        elif file_data.find("RollingFile") != -1:
            return self.log4j_parser(file_data)

        return []

    # 从property标签加属性获取是通用的
    def __update_property_by_attr(self, file_data: str, property_dict: dict):
        rep_property = re.compile(r'''<[pP]roperty.*?/([pP]roperty)?>''')
        rep_attr = re.compile(r'''(?P<k>\S+)=['"](?P<v>.*?)['"]''')

        rep_env_value = re.compile(r"\$\{env:(?P<value>[^:}]*)(:(?P<default>[^}]*))?}")

        for tmp in rep_property.finditer(file_data):
            tmp_dict = {}
            for attr in rep_attr.finditer(tmp.group()):
                tmp_dict[attr.group("k")] = attr.group("v")
            if "name" in tmp_dict and "value" in tmp_dict:
                prop = tmp_dict["value"]
                env_value = rep_env_value.search(prop)
                if env_value:
                    value = env_value.group("value")
                    if value in self.process_env:
                        prop = self.process_env[value]
                    else:
                        prop = str(env_value.group("default"))

                property_dict[tmp_dict["name"]] = prop

    def logback_parser(self, file_data: str, get_config: Callable[[str], Optional[str]]) -> List[str]:
        property_dict = dict()
        rep_spring_property = re.compile(r'''<springProperty(.|\n)*?/(springProperty)?>''')
        rep_attr = re.compile(r'''(?P<k>\S+)=['"](?P<v>.*?)['"]''')
        rep_file_name_pattern = re.compile(r"<fileNamePattern.*?>(?P<file_name_pattern>.*?)</")
        rep_var = re.compile(r"\$\{(?P<var>[^}]*)}")

        for tmp in rep_spring_property.finditer(file_data):
            tmp_dict = {}
            for attr in rep_attr.finditer(tmp.group()):
                tmp_dict[attr.group("k")] = attr.group("v")
            if "name" in tmp_dict and "source" in tmp_dict:
                source_data = get_config(tmp_dict["source"])
                if source_data:
                    property_dict[tmp_dict["name"]] = source_data

        self.__update_property_by_attr(file_data, property_dict)

        res_list = []
        for tmp in rep_file_name_pattern.finditer(file_data):
            tmp_data = tmp.group("file_name_pattern")
            for var in rep_var.finditer(tmp_data):
                if var.group("var") in property_dict:
                    tmp_data = tmp_data.replace(var.group(), property_dict[var.group("var")])
            res_list.append(tmp_data)
        return self.__normalize_res_list(res_list)

    def log4j_parser(self, file_data: str) -> List[str]:
        property_dict = dict()
        rep_property = re.compile(r'<[pP]roperty.*?>(?P<prop>.*?)</')

        rep_name_attr = re.compile(r'''name=['"](?P<value>.+?)['"]''')
        rep_file_name = re.compile(r'''<[Rr]ollingFile.*fileName=['"](?P<file_name>[^'"]*?)['"](.|\n)*?>''')
        rep_var = re.compile(r"\$\{(?P<var>[^}]*)}")

        for tmp in rep_property.finditer(file_data):
            tmp_search = rep_name_attr.search(tmp.group())
            if tmp_search:
                property_dict[tmp_search.group("value")] = tmp.group("prop")

        self.__update_property_by_attr(file_data, property_dict)

        res_list = []
        for tmp in rep_file_name.finditer(file_data):
            tmp_data = tmp.group("file_name")
            for var in rep_var.finditer(tmp_data):
                var_str = var.group("var")
                if var_str in property_dict:
                    tmp_data = tmp_data.replace(var.group(), property_dict[var_str])

            res_list.append(tmp_data)

        return self.__normalize_res_list(res_list)

    def __normalize_res_list(self, res_list: List[str]) -> List[str]:
        res = []
        for i in res_list:
            file_path = os.path.dirname(i)
            if not file_path.startswith("/"):
                file_path = os.path.abspath(os.path.join(self.pwd, file_path))
            # 可能还有占位符
            if os.path.basename(file_path).find("%") != -1 and not os.path.isdir(file_path):
                file_path = os.path.dirname(file_path)

            if os.path.isdir(file_path) and file_path not in res:
                res.append(file_path)
        return res
