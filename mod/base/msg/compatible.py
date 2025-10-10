# 临时解决，处理旧版告警问题

import re
from .weixin_msg import WeiXinMsg
from .mail_msg import MailMsg
from .web_hook_msg import WebHookMsg
from .feishu_msg import FeiShuMsg
from .dingding_msg import DingDingMsg
from .wx_account_msg import WeChatAccountMsg
from mod.base.push_mod import SenderConfig, WxAccountMsg
from typing import Union, Dict, Optional, Tuple


class WarpToOld:

    def __init__(self,
                 sender: Union[WeiXinMsg, MailMsg, WebHookMsg, FeiShuMsg, DingDingMsg, WeChatAccountMsg],
                 default_title: str):
        self.sender = sender
        self.default_title = default_title

    def send_msg(self, msg: str, title: str = None) -> Dict:
        msg, tmp_title = self._get_title_by_msg(msg)
        if tmp_title is not None:
            title = tmp_title
        if title is None:
            title = self.default_title
        res = self.sender.send_msg(msg, title)
        if res is None:
            return {"status": True, "msg": "发送成功"}
        else:
            return {"status": False, "msg": res}

    def push_data(self, data: dict) -> Dict:
        if "msg" not in data:
            return {"status": False, "msg": "消息内容不能为空"}
        return self.sender.send_msg(data["msg"], data.get("title", None))

    @staticmethod
    def _get_title_by_msg(msg: str) -> Tuple[str, Optional[str]]:
        title = None
        try:
            if msg.find("####") >= 0:
                try:
                    title = re.search(r"####(.+)", msg).groups()[0]
                except:
                    pass

                msg = msg.replace("####", ">").replace("\n\n", "\n").strip()
                s_list = msg.split('\n')

                if len(s_list) > 3:
                    s_title = s_list[0].replace(" ", "")
                    s_list = s_list[3:]
                    s_list.insert(0, s_title)
                    msg = '\n'.join(s_list)

            s_list = []
            regexp = re.compile(r'<font.+>(.+)</font>')
            for msg_info in msg.split('\n'):
                tmp = regexp.search(msg_info)
                if tmp:
                    tmp = tmp.groups()[0]
                    msg_info = regexp.sub(tmp, msg_info)
                s_list.append(msg_info)
            msg = '\n'.join(s_list)
        except:
            pass
        return msg, title

    def get_config(self, get=None):
        if hasattr(self.sender, "config"):
            return getattr(self.sender, "config")
        if hasattr(self.sender, "data"):
            return getattr(self.sender, "data")
        return {}


class WarpWebHookMsg(WarpToOld):

    def __init__(self,
                 sender: WebHookMsg,
                 default_title: str):
        super().__init__(sender, default_title)

    def send_msg(self, msg: str, title: str = None, push_type: str = None) -> Dict:
        msg, tmp_title = self._get_title_by_msg(msg)
        if tmp_title is not None:
            title = tmp_title
        if title is None:
            title = self.default_title

        if push_type is None:
            push_type = "unknown"
        res = self.sender.send_msg(msg, title, push_type)
        if res is None:
            return {"status": True, "msg": "发送成功"}
        else:
            return {"status": False, "msg": res}

    def push_data(self, data: dict) -> Dict:
        if "msg" not in data:
            return {"status": False, "msg": "消息内容不能为空"}
        return self.send_msg(data["msg"], data.get("title", None), data.get("push_type", None))


class WarpWeChatAccountMsg(WarpToOld):
    def __init__(self,
                 sender: WeChatAccountMsg,
                 default_title: str):
        super().__init__(sender, default_title)

    def send_msg(self, msg: str, title: str = None) -> Dict:
        msg, tmp_title = self._get_title_by_msg(msg)
        if tmp_title is not None:
            title = tmp_title
        if title is None:
            title = self.default_title

        wxmsg = WxAccountMsg.new_msg()
        wxmsg.thing_type = title
        wxmsg.msg = msg
        res = self.sender.send_msg(wxmsg)
        if res is None:
            return {"status": True, "msg": "发送成功"}
        else:
            return {"status": False, "msg": res}

    def push_data(self, data: dict) -> Dict:
        if "msg" not in data:
            return {"status": False, "msg": "消息内容不能为空"}
        return self.send_msg(data["msg"], data.get("title", None))


def get_sender_by_id(channel_id: str) -> Optional[WarpToOld]:
    sc = SenderConfig()
    if re.match(r"^[0-9a-f]{16}$", channel_id):
        sender_config = sc.get_by_id(channel_id)
        if sender_config is None:
            return None
        if sender_config["sender_type"] == "webhook":
            return WarpWebHookMsg(WebHookMsg(sender_config), "宝塔Web Hook告警通知")
        elif sender_config["sender_type"] == "mail":
            return WarpToOld(MailMsg(sender_config), "宝塔邮件告警通知")
        elif sender_config["sender_type"] == "weixin":
            return WarpToOld(WeiXinMsg(sender_config), "宝塔微信告警通知")
        elif sender_config["sender_type"] == "feishu":
            return WarpToOld(FeiShuMsg(sender_config), "宝塔飞书告警通知")
        elif sender_config["sender_type"] == "dingding":
            return WarpToOld(DingDingMsg(sender_config), "宝塔钉钉告警通知")
        elif sender_config["sender_type"] == "wx_account":
            return WarpWeChatAccountMsg(WeChatAccountMsg(sender_config), "宝塔告警通知")
        return None

    return None

