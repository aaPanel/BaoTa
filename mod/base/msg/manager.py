import time
import os

from mod.base.push_mod import SenderConfig
from .weixin_msg import WeiXinMsg
from .mail_msg import MailMsg
from .web_hook_msg import WebHookMsg
from .feishu_msg import FeiShuMsg
from .dingding_msg import DingDingMsg
from .sms_msg import SMSMsg
from .wx_account_msg import WeChatAccountMsg
import json
from mod.base import json_response
from .util import write_file, read_file


# 短信会自动添加到 sender 库中的第一个 且通过官方接口更新
# 微信公众号信息通过官网接口更新， 不写入数据库，需要时由文件中读取并序列化
# 其他告警通道本质都类似于web hook 在确认完数据信息无误后，都可以自行添加或启用
class SenderManager:

    def set_sender_conf(self, get):
        sender_id = None
        try:
            if hasattr(get, "sender_id"):
                sender_id = get.sender_id.strip()
                if not sender_id:
                    sender_id = None
            sender_type = get.sender_type.strip()
            args = json.loads(get.sender_data.strip())
        except (json.JSONDecoder, AttributeError, TypeError):
            return json_response(status=False, msg="参数错误")
        sender_config = SenderConfig()
        if sender_id is not None:
            tmp = sender_config.get_by_id(sender_id)
            if tmp is None:
                sender_id = None
        else:
            # Check if the sender configuration already exists
            existing_sender = any(
                conf for conf in sender_config.config
                if conf['sender_type'] == sender_type and conf['data']['title'] == args.get("title", "")
            )
            if existing_sender:
                return json_response(status=False, msg="同名的发送配置已存在，无法重复添加")

        if sender_type == "weixin":
            data = WeiXinMsg.check_args(args)
            if not isinstance(data, dict):
                return json_response(status=False, data=data, msg="测试发送失败")

        elif sender_type == "mail":
            _, data = MailMsg.check_args(args)
            if not isinstance(data, dict):
                return json_response(status=False, data=data, msg="测试发送失败")

        elif sender_type == "webhook":
            # 检查参数
            data = WebHookMsg.check_args(args)
            if not isinstance(data, dict):
                return json_response(status=False, data=data, msg="测试发送失败")

        elif sender_type == "feishu":
            data = FeiShuMsg.check_args(args)
            if not isinstance(data, dict):
                return json_response(status=False, data=data, msg="测试发送失败")

        elif sender_type == "dingding":
            data = DingDingMsg.check_args(args)
            if not isinstance(data, dict):
                return json_response(status=False, data=data, msg="测试发送失败")
        else:
            return json_response(status=False, msg="当前接口不适应的类型")
        now_sender_id = None
        if not sender_id:
            now_sender_id = sender_config.nwe_id()
            sender_config.config.append(
                {
                    "id": now_sender_id,
                    "sender_type": sender_type,
                    "data": data,
                    "used": True,
                })

        else:
            now_sender_id = sender_id
            tmp = sender_config.get_by_id(sender_id)
            if tmp is None:
                return json_response(status=False, msg="未找到对应发送者")
            if not isinstance(tmp["data"], dict):
                tmp["data"] = {}
            tmp["data"].update(data)

        sender_config.save_config()
        if sender_type == "webhook":
            self.set_default_for_compatible(sender_config.get_by_id(now_sender_id))

        return json_response(status=True, msg="保存成功")

    @staticmethod
    def change_sendr_used(get):
        try:
            sender_id = get.sender_id.strip()
        except (AttributeError, TypeError):
            return json_response(status=False, msg="参数错误")

        sender_config = SenderConfig()
        tmp = sender_config.get_by_id(sender_id)
        if tmp is None:
            return json_response(status=False, msg="未找到对应发送者")
        tmp["used"] = not tmp["used"]

        sender_config.save_config()

        return json_response(status=True, msg="保存成功")

    @classmethod
    def remove_sender(cls, get):
        try:
            sender_id = get.sender_id.strip()
        except (AttributeError, TypeError):
            return json_response(status=False, msg="参数错误")

        sender_config = SenderConfig()
        tmp = sender_config.get_by_id(sender_id)
        if tmp is None:
            return json_response(status=False, msg="未找到对应发送者")
        sender_config.config.remove(tmp)
        sender_config.save_config()
        cls.remove_sender_from_tasks(sender_id)
        return json_response(status=True, msg="删除成功")

    @staticmethod
    def remove_sender_from_tasks(sender_id):
        task_file_path = "/www/server/panel/data/mod_push_data/task.json"
        if not os.path.exists(task_file_path):
            return
        try:
            tasks = json.loads(read_file(task_file_path))
            updated = False
            for task in tasks:
                if "sender" in task and sender_id in task["sender"]:
                    task["sender"].remove(sender_id)
                    updated = True

            # 如果有更新，保存文件
            if updated:
                write_file(task_file_path, json.dumps(tasks))

        except Exception as e:
            pass

    @staticmethod
    def get_sender_list(get):
        # 微信， 飞书， 钉钉， web-hook， 邮箱
        refresh = False
        try:
            if hasattr(get, 'refresh'):
                refresh_str = get.refresh.strip()
                if refresh_str in ("1", "true"):
                    refresh = True
        except (AttributeError, TypeError):
            return json_response(status=False, msg="参数错误")

        res = []
        WeChatAccountMsg.refresh_config(force=refresh)
        simple = ("weixin", "mail", "webhook", "feishu", "dingding")

        for conf in SenderConfig().config:
            if conf["sender_type"] in simple or conf["sender_type"] == "wx_account":
                res.append(conf)
            elif conf["sender_type"] == "sms":
                conf["data"] = SMSMsg(conf).refresh_config(force=refresh)
                res.append(conf)
        res.sort(key=lambda x: x["sender_type"])
        return json_response(status=True, data=res)

    @staticmethod
    def test_send_msg(get):
        try:
            sender_id = get.sender_id.strip()
        except (json.JSONDecoder, AttributeError, TypeError):
            return json_response(status=False, msg="参数错误")

        sender_config = SenderConfig()
        tmp = sender_config.get_by_id(sender_id)
        if tmp is None:
            return json_response(status=False, msg="未找到对应发送者")

        sender_type = tmp["sender_type"]

        if sender_type == "weixin":
            sender_obj = WeiXinMsg(tmp)

        elif sender_type == "mail":
            sender_obj = MailMsg(tmp)

        elif sender_type == "webhook":
            sender_obj = WebHookMsg(tmp)

        elif sender_type == "feishu":
            sender_obj = FeiShuMsg(tmp)

        elif sender_type == "dingding":
            sender_obj = DingDingMsg(tmp)

        elif sender_type == "wx_account":
            sender_obj = WeChatAccountMsg(tmp)
        else:
            return json_response(status=False, msg="当前接口不适应的类型")

        res = sender_obj.test_send_msg()
        if not res:
            return json_response(status=False, data=res, msg="测试发送失败")
        if isinstance(res, str):
            return json_response(status=False, data=res, msg="测试发送失败")
        return json_response(status=True, msg="发送成功")

    @staticmethod
    def set_default_for_compatible(sender_data: dict):
        if sender_data["sender_type"] in ("sms", "wx_account"):
            return

        panel_data = "/www/server/panel/data"
        if sender_data["sender_type"] == "weixin":
            weixin_file = "{}/weixin.json".format(panel_data)
            write_file(weixin_file, json.dumps({
                "state": 1,
                "weixin_url": sender_data["data"]["url"],
                "title": sender_data["data"]["title"],
                "list": {
                    "default": {
                        "data": sender_data["data"]["url"],
                        "title": sender_data["data"]["title"],
                        "status": 1,
                        "addtime": int(time.time())
                    }
                }
            }))

        elif sender_data["sender_type"] == "mail":
            stmp_mail_file = "{}/stmp_mail.json".format(panel_data)
            mail_list_file = "{}/mail_list.json".format(panel_data)
            write_file(stmp_mail_file, json.dumps(sender_data["data"]["send"]))
            write_file(mail_list_file, json.dumps(sender_data["data"]["receive"]))

        elif sender_data["sender_type"] == "feishu":
            feishu_file = "{}/feishu.json".format(panel_data)
            write_file(feishu_file, json.dumps({
                "feishu_url": sender_data["data"]["url"],
                "title": sender_data["data"]["title"],
                "isAtAll": True,
                "user": []
            }))

        elif sender_data["sender_type"] == "dingding":
            dingding_file = "{}/dingding.json".format(panel_data)
            write_file(dingding_file, json.dumps({
                "dingding_url": sender_data["data"]["url"],
                "title": sender_data["data"]["title"],
                "isAtAll": True,
                "user": []
            }))

        elif sender_data["sender_type"] == "webhook":
            webhook_file = "{}/hooks_msg.json".format(panel_data)
            try:
                webhook_data = json.loads(read_file(webhook_file))
            except:
                webhook_data = []
            target_idx = -1
            for idx, i in enumerate(webhook_data):
                if i["name"] == sender_data["data"]["title"]:
                    target_idx = idx
                    break
            else:
                sender_data["data"]["name"] = sender_data["data"]["title"]
                webhook_data.append(sender_data["data"])
            if target_idx != -1:
                sender_data["data"]["name"] = sender_data["data"]["title"]
                webhook_data[target_idx] = sender_data["data"]
            write_file(webhook_file, json.dumps(webhook_data))

    @classmethod
    def sync_default_sender(cls):
        sender_config = SenderConfig()
        all_types = ("feishu", "dingding", "weixin", "mail", "webhook")  # 所有可能的类型

        for sender_type in all_types:
            type_senders = [conf for conf in sender_config.config if conf['sender_type'] == sender_type]

            # 检查是否已有默认通道
            has_default = any(conf.get('original', False) for conf in type_senders)
            if has_default:
                continue

            if len(type_senders) >= 1:
                # 有多个通道，根据添加时间设置默认通道
                sorted_senders = sorted(type_senders, key=lambda x: x['data'].get('create_time', ''))
                cls.set_default_for_compatible(sorted_senders[0])
