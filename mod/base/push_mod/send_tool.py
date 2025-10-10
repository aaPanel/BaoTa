import ipaddress
import re

from .util import get_config_value


class WxAccountMsgBase:

    @classmethod
    def new_msg(cls):
        return cls()

    def set_ip_address(self, server_ip, local_ip):
        pass

    def to_send_data(self):
        return "", {}


class WxAccountMsg(WxAccountMsgBase):
    def __init__(self):
        self.ip_address: str = ""
        self.thing_type: str = ""
        self.msg: str = ""
        self.next_msg: str = ""

    def set_ip_address(self, server_ip, local_ip):
        self.ip_address = "{}({})".format(server_ip, local_ip)
        if len(self.ip_address) > 32:
            self.ip_address = self.ip_address[:29] + "..."

    def to_send_data(self):
        res = {
            "first": {},
            "keyword1": {
                "value": self.ip_address,
            },
            "keyword2": {
                "value": self.thing_type,
            },
            "keyword3": {
                "value": self.msg,
            }
        }

        if self.next_msg != "":
            res["keyword4"] = {"value": self.next_msg}

        return "", res


class WxAccountLoginMsg(WxAccountMsgBase):
    tid = "RJNG8dBZ5Tb9EK6j6gOlcAgGs2Fjn5Fb07vZIsYg1P4"

    def __init__(self):
        self.login_name: str = ""
        self.login_ip: str = ""
        self.thing_type: str = ""
        self.login_type: str = ""
        self.address: str = ""
        self._server_name: str = ""

    def set_ip_address(self, server_ip, local_ip):
        if self._server_name == "":
            self._server_name = "服务器IP{}".format(server_ip)

    def _get_server_name(self):
        data = get_config_value("title")  # 若获得别名，则使用别名.

        if data != "":
            self._server_name = data

    def to_send_data(self):
        self._get_server_name()
        if self.address.startswith(">归属地："):
            self.address = self.address[5:]
        if self.address == "":
            self.address = "未知的归属地"

        if not _is_ipv4(self.login_ip):
            self.login_ip = "ipv6-can not show"

        res = {
            "thing10": {
                "value": self._server_name,
            },
            "character_string9": {
                "value": self.login_ip,
            },
            "thing7": {
                "value": self.login_type,
            },
            "thing11": {
                "value": self.address,
            },
            "thing2": {
                "value": self.login_name,
            }
        }
        return self.tid, res


# 处理短信告警信息的不规范问题
def sms_msg_normalize(sm_args: dict) -> dict:
    for key, val in sm_args.items():
        sm_args[key] = _norm_sms_push_argv(str(val))
    return sm_args


def _norm_sms_push_argv(data):
    """
    @处理短信参数，否则会被拦截
    """
    if _is_ipv4(data):
        tmp1 = data.split('.')
        return '{}_***_***_{}'.format(tmp1[0], tmp1[3])

    data = data.replace(".", "_").replace("+", "＋")
    return data


def _is_ipv4(data: str) -> bool:
    try:
        ipaddress.IPv4Address(data)
    except:
        return False
    return True


def _is_domain(domain):
    rep_domain = re.compile(r"^([\w\-*]{1,100}\.){1,10}([\w\-]{1,24}|[\w\-]{1,24}\.[\w\-]{1,24})$")
    if rep_domain.match(domain):
        return True
    return False
