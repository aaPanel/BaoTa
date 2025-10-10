import datetime
import json
import pathlib
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from threading import RLock
from typing import List

from mod.project.proxy import tools
from mod.project.proxy.tools import split_ip

if "/www/server/panel/class" not in sys.path:
    sys.path.append('/www/server/panel/class')
import public

NGINX_STREAM_TEMP="""
server {{
    listen {c.listen};
    proxy_pass {c.proxy_pass};
    access_log {c.access_log} tcp_format;
    error_log {c.error_log};
    allow {c.allow};
    deny {c.deny};
{c.custom}
}}
"""


class BaseProxy:
    name = 'base'
    config_path = pathlib.Path('/www/server/panel/vhost/nginx/')


@dataclass
class StreamRequest:
    handle: str = field(default=None)
    protocol: str = field(default=None)
    listen: str = field(default=None)
    proxy_pass: str = field(default=None)
    deny: str = field(default=None)
    allow: str = field(default=None)
    custom: str = field(default=None)
    ps: str = field(default=None)


@dataclass
class StreamListRequest:
    data: List[StreamRequest] = field(default=None)


@dataclass
class StreamServerConfig:
    listen: str = field(default="")
    proxy_pass: str = field(default="")
    allow: str = field(default="")
    deny: str = field(default="")
    custom: str = field(default="")
    access_log: str = field(default="")
    error_log: str = field(default="")


@dataclass
class StreamConfig(StreamServerConfig):
    addtime: str = field(default=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    ps: str = field(default='')
    id: str = field(default=str(int(time.time() * 1000)))
    conf_path: str = field(default='')
    protocol: str = field(default='tcp')


@dataclass
class Message:
    create: str = field(default="端口【{port}】: 成功添加")
    update: str = field(default="端口【{port}】: 更新成功")
    delete: str = field(default="端口【{port}】: 删除成功")
    allow: str = field(default="端口【{port}】: 白名单更新成功")
    deny: str = field(default="端口【{port}】: 黑名单更新成功")

    @dataclass
    class Error:
        arg: str = field(default="请求参数不合法")
        port: str = field(default="端口【{port}】未找到，请先添加端口")
        delete: str = field(default="端口【{port}】删除失败：{err}")
        proxy: str = field(default="端口【{protocol}-{port}】未找到，请添加端口")
        exist: str = field(default="端口【{protocol}-{port}】已存在")


def load_data(path: pathlib.Path):
    data = {}
    if (path / 'data.json').exists():
        jdata: dict = json.loads((path / 'data.json').read_text('utf8'))
        for k, v in jdata.items():
            _config = StreamConfig()
            data[k] = tools.update_attr(_config, v)
    return data


def open_firewall(request: StreamRequest):
    # 后置处理
    from firewallModel.comModel import main as comModel
    firewall_com = comModel()
    get = public.dict_obj()
    if request.protocol == 'tcp':
        get.port = request.listen
        firewall_com.set_port_rule(get)
    elif request.protocol == 'udp':
        get.port = request.listen.split(' ')[0]
        get.protocol = request.protocol
        firewall_com.set_port_rule(get)
    public.serviceReload()


class StreamProxy(BaseProxy, ABC):
    name = 'stream'
    config_path = pathlib.Path('/www/server/panel/vhost/nginx/tcp/')
    data: dict = load_data(config_path)

    def __init__(self):
        self.config = StreamConfig()
        self.file_name = '0.conf'
        self.lock = RLock()

    def write_config(self):
        file = self.config_path / self.file_name
        self.delete_config()

        _config = StreamServerConfig()
        tools.update_attr(_config, self.config)
        with open(file=file, mode='w', encoding='utf8') as f:
            if _config.custom is not None and isinstance(_config.custom, str) and len(_config.custom) > 0:
                _custom = " " * 4 + ('\n' + ' ' * 4).join(
                    map(lambda x: x.strip(), _config.custom.split('\n'))
                ) + '\n' # 处理自定义配置
                _config.custom = _custom
            public.print_log(NGINX_STREAM_TEMP.format(c=_config))
            config_str = NGINX_STREAM_TEMP.format(c=_config)

            f.writelines(config_str)
            # for k, v in tools.items(_config):
                # v: str
                # if v is None or len(v) == 0:
                #     continue
                # elif k == 'custom':
                #     v_list = list()
                #     f.writelines()
                # elif k == 'access_log':
                #     v = v + ' tcp_format'
                #     v = "{key} {value};".format(key=k, value=v)
                #     f.writelines(" " * 4 + v + '\n')
                # else:
                #     v = "{key} {value};".format(key=k, value=v)
                #     f.writelines(" " * 4 + v + '\n')
        public.serviceReload()

    def delete_config(self):
        file = self.config_path / self.file_name
        if file.exists():
            file.unlink()
        public.serviceReload()

    def delete_logfile(self):
        _err_file = pathlib.Path(self.config.error_log)
        _acc_file = pathlib.Path(self.config.access_log)
        _log_dir = self.config_path / self.file_name.split('.')[0]
        if _err_file.exists():
            _err_file.unlink()
        if _acc_file.exists():
            _acc_file.unlink()
        if _log_dir.exists():
            _log_dir.rmdir()

    def save_data(self):
        with self.lock:
            data_file = self.config_path / 'data.json'
            j_data = {k: tools.to_dict(v) for k, v in self.data.items()}
            data_str = json.dumps(j_data)
            with open(data_file, mode='w', encoding='utf8') as file:
                file.write(data_str)

    @abstractmethod
    def create(self, request: StreamRequest):
        tools.update_attr(self.config, request)
        if len(self.config.proxy_pass.split(':')) != 2:
            raise ValueError(Message.Error.proxy.format(protocol=self.config.proxy_pass, port=request.listen))
        public.print_log(tools.to_dict(self.config))
        self.set_default_config()
        self.write_config()
        self.data[request.listen] = self.config
        self.save_data()
        # self.save_database()
        public.print_log("开放防火墙: {}".format(request))
        open_firewall(request)

        return Message.create.format(port=request.listen)

    @abstractmethod
    def delete(self, request: StreamRequest):
        self.config = self.data.get(request.listen, None)
        if self.config is None:
            raise ValueError(Message.Error.port.format(request=request.listen))
        self.delete_config()
        self.data[request.listen] = None
        self.data.pop(request.listen)
        self.save_data()
        # self.delete_database()
        self.delete_logfile()
        return Message.delete.format(port=request.listen)

    @abstractmethod
    def update(self, request: StreamRequest):
        self.config = self.data.get(request.listen, StreamConfig())

        StreamProxy.create(self, request)
        return Message.update.format(port=request.listen)

    # @abstractmethod
    def list(self, request: StreamRequest):
        _data = []
        # public.print_log(self.data.items())
        for k, v in self.data.items():
            _dict = tools.to_dict(v)
            _dict['listen_port'] = _dict.get('listen')
            _data.append(_dict)
        sorted(_data, key=lambda x: x['id'], reverse=True)
        return _data

    @abstractmethod
    def delete_list(self, request: StreamRequest):
        # TODO: bug udp
        for port in request.listen.split(' '):
            self.delete_config()
            self.data[port] = None
        self.save_data()

    @abstractmethod
    def allow(self, request: StreamRequest):
        self.config = self.data.get(request.listen, None)
        if self.config is None:
            raise ValueError(Message.Error.port.format(request=request.listen))

        if self.config.allow is None:
            self.config.allow = ''
        else:
            self.config.allow = self.config.allow.strip() + ' '
        # public.print_log(self.config.allow + ' '.join(split_ip(request.allow)))
        request.allow = self.config.allow + ' '.join(split_ip(request.allow))
        StreamProxy.create(self, request)
        return Message.allow.format(port=request.listen)

    @abstractmethod
    def deny(self, request: StreamRequest):
        self.config = self.data.get(request.listen, None)
        if self.config is None:
            raise ValueError(Message.Error.port.format(request=request.listen))

        if self.config.deny is None:
            self.config.deny = ''
        else:
            self.config.deny = self.config.deny.strip() + ' '
        request.deny = self.config.deny + ' '.join(split_ip(request.deny))
        StreamProxy.create(self, request)
        return Message.deny.format(port=request.listen)

    def com_list(self, request: StreamRequest = None):
        _result = []
        _list = self.list(StreamRequest())
        public.print_log(_list)
        for i in range(len(_list)):
            _data = {
                'name': _list[i].get('listen_port'),
                'ps': _list[i].get('ps'),
                'ssl': -1,
                'proxy_pass': _list[i].get('proxy_pass'),
                "waf": {
                    "status": False
                },
                'addtime': _list[i].get('addtime')
            }
            _result.append(_data)
        return _result

    @abstractmethod
    def port(self, request: StreamRequest):
        _port = request.listen
        _dict = tools.to_dict(self.data[_port])
        _dict['listen_port'] = _dict.get('listen')
        return _dict

    def save_database(self):
        _port = self.config.listen
        self.delete_database()

        pdata = {
            'name': self.config.listen,
            'path': self.config.conf_path,
            'ps': self.config.ps,
            'status': 1,
            'type_id': 0,
            'project_type': 'proxy.stream',
            'project_config': json.dumps(tools.to_dict(self.config)),
            'addtime': self.config.addtime
        }
        public.M('sites').insert(pdata)

    def delete_database(self):
        if public.M('sites').where('name=?', (self.config.listen,)).count():
            public.M('sites').where('name=?', (self.config.listen,)).delete()

    @abstractmethod
    def delete_allow(self, request: StreamRequest):
        if request.allow is None or len(request.allow) == 0:
            raise ValueError(Message.Error.delete.format(port=request.listen, err=Message.Error.arg))
        _need_delete = [_ip.strip() for _ip in request.allow.split(' ')]
        self.config = self.data.get(request.listen)
        if self.config is None:
            raise ValueError(Message.Error.delete.format(port=request.listen, err=Message.Error.arg))
        _ip_list = []
        if self.config.allow is None or len(self.config.allow) == 0:
            return Message.delete.format(port=request.listen)

        for _allow_ip in self.config.allow.split(' '):
            if _allow_ip.strip() in _need_delete:
                continue
            else:
                _ip_list.append(_allow_ip.strip())
        if len(_ip_list) == 0:
            self.config.allow = ''
        request.allow = " ".join(_ip_list)
        self.update(request)
        return Message.delete.format(port=request.listen)

    @abstractmethod
    def delete_deny(self, request: StreamRequest):
        if request.deny is None or len(request.deny) == 0:
            raise ValueError(Message.Error.delete.format(port=request.listen, err=Message.Error.arg))
        _need_delete = [_ip.strip() for _ip in request.deny.split(' ')]
        self.config = self.data.get(request.listen)
        if self.config is None:
            raise ValueError(Message.Error.delete.format(port=request.listen, err=Message.Error.arg))

        _ip_list = []
        if self.config.deny is None or len(self.config.deny) == 0:
            return Message.delete.format(port=request.listen)

        for _deny_ip in self.config.deny.split(' '):
            if _deny_ip.strip() in _need_delete:
                continue
            else:
                _ip_list.append(_deny_ip.strip())
        public.print_log(_ip_list, _ip_list)
        if len(_ip_list) == 0:
            self.config.deny = ''
        request.deny = " ".join(_ip_list)
        self.update(request)
        return Message.delete.format(port=request.listen)

    @abstractmethod
    def log(self, request: StreamRequest):
        self.config = self.data[request.listen]
        # if self.config.listen is None:
        #     return None

        _error_log_file = pathlib.Path(self.config.error_log)
        _access_log_file = pathlib.Path(self.config.access_log)
        public.print_log(_access_log_file.stat().st_mtime, _error_log_file.stat().st_mtime,
                         _access_log_file.stat().st_mtime > _error_log_file.stat().st_mtime)
        if _access_log_file.exists() and _error_log_file.exists():
            if _access_log_file.stat().st_mtime > _error_log_file.stat().st_mtime:
                return _access_log_file.read_text('utf8')
            else:
                public.print_log("TXT:", _error_log_file.read_text('utf8'))
                return _error_log_file.read_text('utf8')
        elif _access_log_file.exists():
            return _access_log_file.read_text('utf8')
        elif _error_log_file.exists():
            return _error_log_file.read_text('utf8')
        else:
            return None

    def set_default_config(self):
        _conf_path = self.config_path / self.file_name
        public.print_log(_conf_path)

        try:
            _log_path = self.config_path / self.file_name.split('.')[0]
        except:
            raise ValueError("File Name Error:{}".format(self.file_name))

        self.config.conf_path = str(_conf_path)
        self.config.access_log = str(_log_path / 'access.log')
        self.config.error_log = str(_log_path / 'error.log')

        if _log_path.exists() and not _log_path.is_dir():
            raise FileExistsError("{} is Exists and Not a Dir".format(_log_path))
        elif not _log_path.exists():
            pathlib.Path(_log_path).mkdir(mode=755)

        if not (_log_path / 'access.log').exists():
            pathlib.Path(self.config.access_log).touch(mode=755)
        if not (_log_path / 'error.log').exists():
            pathlib.Path(self.config.error_log).touch(mode=755)

        self.config.addtime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.config.id = str(int(time.time() * 1000))


if __name__ == '__main__':
    c = StreamServerConfig()
    c.listen_port = '1009'
    print(c.listen_port)
