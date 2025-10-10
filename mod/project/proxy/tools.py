import json
import pathlib
from types import MethodType, FunctionType
from typing import Dict
import sqlite3

def gen_config():
    pass


def update_attr(self: object, get: object):
    for k, v in items(get):
        if isinstance(v, MethodType) or isinstance(v, FunctionType):
            continue
        elif hasattr(self, k) and v is not None and len(v) > 0:
            try:
                setattr(self, k, v)
            except:
                pass
    return self


def items(self):
    data = {}
    if isinstance(self, Dict):
        _items = self.items()
    else:
        _items = self.__dict__.items()

    for k, v in _items:
        if isinstance(v, MethodType) or isinstance(v, FunctionType):
            continue
        else:
            data[k] = v
    return data.items()


def to_dict(self):
    data = {}

    for k, v in items(self):
        if isinstance(v, MethodType) or isinstance(v, FunctionType):
            continue
        else:
            data[k] = v
    return data


def split_ip(ips: str):
    ip_list = []
    for ip in ips.split('\n'):
        ip = ip.strip()
        ip_list.append(ip)
    return ip_list
