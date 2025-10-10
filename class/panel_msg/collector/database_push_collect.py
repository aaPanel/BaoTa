from typing import List

from .. import Message, collect_message

_self_type = "push_msg"


class DatabasePushMsgCollect:
    # MySQL 密码到期
    @staticmethod
    def mysql_pwd_endtime(s_list: List[str], title: str) -> Message:
        data = "\n".join(s_list)
        msg = collect_message(
            title="MySQL数据库密码到期提醒",
            msg_types=["数据库", "MySQL数据库密码有效期"],
            source=["面板设置", "告警通知", title],
            sub_msg={
                "push_type": "MySQL数据库密码到期提醒",
                "push_title": title,
                "data": data,
                "self_type": _self_type
            },
            level="info",
        )
        if isinstance(msg, Message):
            return msg

        return msg

    # MySQL主从复制异常告警
    @staticmethod
    def mysql_replicate_status(s_list: List[str], title: str) -> Message:
        data = "\n".join(s_list)
        msg = collect_message(
            title="MySQL主从复制异常告警",
            msg_types=["数据库", "MySQL主从复制异常告警"],
            source=["面板设置", "告警通知", title],
            sub_msg={
                "push_type": "MySQL主从复制异常告警",
                "push_title": title,
                "data": data,
                "self_type": _self_type
            },
            level="info",
        )
        if isinstance(msg, Message):
            return msg

        return msg
