#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2020 宝塔软件(http://www.bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 沐落 <cjx@bt.cn>
# | Author: lx
# | 消息通道邮箱模块
# +-------------------------------------------------------------------

import smtplib
import traceback
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Tuple, Union, Optional

from mod.base.msg.util import write_push_log, write_mail_push_log, get_test_msg


class MailMsg:

    def __init__(self, mail_data):
        self.id = mail_data["id"]
        self.config = mail_data["data"]

    @classmethod
    def check_args(cls, args: dict) -> Tuple[bool, Union[dict, str]]:
        if "send" not in args or "receive" not in args or len(args["receive"]) < 1:
            return False, "信息不完整，必须有发送方和至少一个接收方"

        if "title" not in args:
            return False, "没有必要的备注信息"

        title = args["title"]
        if len(title) > 15:
            return False, '备注名称不能超过15个字符'

        send_data = args["send"]
        send = {}
        for i in ("qq_mail", "qq_stmp_pwd", "hosts", "port"):
            if i not in send_data:
                return False, "发送方配置信息不完整"
            send[i] = send_data[i].strip()

        receive_data = args["receive"]
        if isinstance(receive_data, str):
            receive_list = [i.strip() for i in receive_data.split("\n") if i.strip()]
        else:
            receive_list = [i.strip() for i in receive_data if i.strip()]

        data = {
            "send": send,
            "title": title,
            "receive": receive_list,
        }

        test_obj = cls({"data": data, "id": None})
        test_msg = {
            "msg_list": ['>配置状态：成功<br>']
        }

        test_task = get_test_msg("消息通道配置提醒")

        res = test_obj.send_msg(
            test_task.to_mail_msg(test_msg, test_task.the_push_public_data()),
            "消息通道配置提醒"
        )
        if res is True or res.find("部分接收者时失败") != -1:
            return True, data

        return False, res

    def send_msg(self, msg: str, title: str):
        """
        邮箱发送
        @msg 消息正文
        @title 消息标题
        """
        if not self.config:
            return '未正确配置邮箱信息。'

        if 'port' not in self.config['send']: 
            self.config['send']['port'] = 465

        receive_list = self.config['receive']

        error_list, success_list = [], []
        error_msg_dict = {}
        for email in receive_list:
            if not email.strip():
                continue
            try:
                data = MIMEText(msg, 'html', 'utf-8')
                data['From'] = formataddr((self.config['send']['qq_mail'], self.config['send']['qq_mail']))
                data['To'] = formataddr((self.config['send']['qq_mail'], email.strip()))
                data['Subject'] = title
                if int(self.config['send']['port']) == 465:
                    server = smtplib.SMTP_SSL(str(self.config['send']['hosts']), int(self.config['send']['port']))
                else:
                    server = smtplib.SMTP(str(self.config['send']['hosts']), int(self.config['send']['port']))

                server.login(self.config['send']['qq_mail'], self.config['send']['qq_stmp_pwd'])
                server.sendmail(self.config['send']['qq_mail'], [email.strip(), ], data.as_string())
                server.quit()
                success_list.append(email)
            except:
                error_list.append(email)
                error_msg_dict[email] = traceback.format_exc()

        if not error_list and not success_list:  # 没有接收者
            return "未配置接收邮箱"
        if not error_list:
            write_push_log("邮箱", True, title, success_list)  # 没有失败
            return True
        if not success_list:
            write_push_log("邮箱", False, title, error_list)  # 全都失败
            return "发送信息失败, 发送失败的接收人：{}".format(error_list)
        write_mail_push_log(title, error_list, success_list)

        return "发送邮件到部分接收者时失败，包含：{}".format(error_list)

    def test_send_msg(self) -> Optional[str]:
        test_msg = {
            "msg_list": ['>配置状态：<font color=#20a53a>成功</font>\n\n']
        }
        test_task = get_test_msg("消息通道配置提醒")
        res = self.send_msg(
            test_task.to_mail_msg(test_msg, test_task.the_push_public_data()),
            "消息通道配置提醒"
        )
        if res is None:
            return None
        return res

