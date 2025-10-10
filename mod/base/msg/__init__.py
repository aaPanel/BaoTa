import json
import os.path

from .weixin_msg import WeiXinMsg
from .mail_msg import MailMsg
from .web_hook_msg import WebHookMsg
from .feishu_msg import FeiShuMsg
from .dingding_msg import DingDingMsg
from .sms_msg import SMSMsg
from .wx_account_msg import WeChatAccountMsg
from .manager import SenderManager
from .util import read_file,write_file

from mod.base.push_mod import SenderConfig, PUSH_DATA_PATH


# 把旧地告警系统的信息通道更新
def update_mod_push_msg():

    if os.path.exists(PUSH_DATA_PATH + "/update_sender.pl"):
        return
    # else:
    #     with open(PUSH_DATA_PATH + "/update_sender.pl", "w") as f:
    #             f.write("")

    WeChatAccountMsg.refresh_config(force=True)
    sms_status = False
    sc = SenderConfig()
    for conf in sc.config:
        if conf["sender_type"] == "sms":
            sms_status = True
            break

    if not sms_status:
        sc.config.append({
            "id": sc.nwe_id(),
            "used": True,
            "sender_type": "sms",
            "data": {},
            "original": True   # 标记这个通道是该类型 旧有的通道, 同时也是默认通道
        })

    panel_data_path = "/www/server/panel/data"

    # weixin
    if os.path.exists(panel_data_path + "/weixin.json"):
        try:
            weixin_data = json.loads(read_file(panel_data_path + "/weixin.json"))
        except:
            weixin_data = None

        if isinstance(weixin_data, dict) and "weixin_url" in weixin_data and \
                not sc.key_exists("weixin", "url", weixin_data["weixin_url"]):
            sc.config.append({
                "id": sc.nwe_id(),
                "used": True,
                "sender_type": "weixin",
                "data": {
                    "url": weixin_data["weixin_url"],
                    "title": "企业微信" if "title" not in weixin_data else weixin_data["title"]
                },
                "original": True
            })

    # mail
    stmp_file = panel_data_path + "/stmp_mail.json"
    mail_list_file = panel_data_path + "/mail_list.json"
    if os.path.exists(stmp_file) and os.path.exists(mail_list_file):
        stmp_data = None
        try:
            stmp_data = json.loads(read_file(stmp_file))
            mail_list_data = json.loads(read_file(mail_list_file))
        except:
            mail_list_data = None

        if isinstance(stmp_data, dict):
            if 'qq_mail' in stmp_data or 'qq_stmp_pwd' in stmp_data or 'hosts' in stmp_data:
                if not sc.key_exists("mail", "send", stmp_data):
                    sc.config.append({
                        "id": sc.nwe_id(),
                        "used": True,
                        "sender_type": "mail",
                        "data": {
                            "send": stmp_data,
                            "title": "邮箱",
                            "receive": [] if not mail_list_data else mail_list_data,
                        },
                        "original": True
                    })

    # webhook
    webhook_file = panel_data_path + "/hooks_msg.json"
    if os.path.exists(stmp_file) and os.path.exists(mail_list_file):
        try:
            webhook_data = json.loads(read_file(webhook_file))
        except:
            webhook_data = None

        if isinstance(webhook_data, list):
            for i in webhook_data:
                if not sc.key_exists("webhook", "url", i.get("url", None)):
                    i["title"] = i["name"]
                    sc.config.append({
                        "id": sc.nwe_id(),
                        "used": True,
                        "sender_type": "webhook",
                        "data": i,
                    })

    # feishu
    if os.path.exists(panel_data_path + "/feishu.json"):
        try:
            feishu_data = json.loads(read_file(panel_data_path + "/feishu.json"))
        except:
            feishu_data = None

        if isinstance(feishu_data, dict) and "feishu_url" in feishu_data:
            if not sc.key_exists("feishu", "url", feishu_data["feishu_url"]):
                sc.config.append({
                    "id": sc.nwe_id(),
                    "used": True,
                    "sender_type": "feishu",
                    "data": {
                        "url": feishu_data["feishu_url"],
                        "title": "飞书" if "title" not in feishu_data else feishu_data["title"]
                    },
                    "original": True
                })

    # dingding
    if os.path.exists(panel_data_path + "/dingding.json"):
        try:
            dingding_data = json.loads(read_file(panel_data_path + "/dingding.json"))
        except:
            dingding_data = None

        if isinstance(dingding_data, dict) and "dingding_url" in dingding_data:
            if not sc.key_exists("dingding", "url", dingding_data["dingding_url"]):
                sc.config.append({
                    "id": sc.nwe_id(),
                    "used": True,
                    "sender_type": "dingding",
                    "data": {
                        "url": dingding_data["dingding_url"],
                        "title": "钉钉" if "title" not in dingding_data else dingding_data["title"]
                    },
                    "original": True
                })

    sc.save_config()
    write_file(PUSH_DATA_PATH + "/update_sender.pl", "")
