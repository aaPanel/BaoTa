from typing import List

from .. import Message, collect_message

_self_type = "push_msg"


class SystemPushMsgCollect:

    @staticmethod
    def system_disk(s_list: List[str], title: str) -> Message:
        data = "\n".join(s_list)
        msg = collect_message(
            title="磁盘余量告警",
            msg_types=["主机", "首页磁盘告警"],
            source=["首页", title],
            sub_msg={
                "push_type": "首页磁盘告警",
                "push_title": title,
                "data": data,
                "self_type": _self_type
            },
            level="warning",
        )
        if isinstance(msg, Message):
            return msg

        return msg

    @staticmethod
    def system_mem(s_list: List[str], title: str) -> Message:
        data = "\n".join(s_list)
        msg = collect_message(
            title="内存高占用告警",
            msg_types=["主机", "首页内存告警"],
            source=["首页", title],
            sub_msg={
                "push_type": "首页内存告警",
                "push_title": title,
                "data": data,
                "self_type": _self_type
            },
            level="warning",
        )
        if isinstance(msg, Message):
            return msg

        return msg

    @staticmethod
    def system_load(s_list: List[str], title: str) -> Message:
        data = "\n".join(s_list)
        msg = collect_message(
            title="负载超标告警",
            msg_types=["主机", "首页负载告警"],
            source=["首页", title],
            sub_msg={
                "push_type": "首页负载告警",
                "push_title": title,
                "data": data,
                "self_type": _self_type
            },
            level="warning",
        )
        if isinstance(msg, Message):
            return msg

        return msg

    @staticmethod
    def system_cpu(s_list: List[str], title: str) -> Message:
        data = "\n".join(s_list)
        msg = collect_message(
            title="CPU高占用告警",
            msg_types=["主机", "首页CPU告警"],
            source=["首页", title],
            sub_msg={
                "push_type": "首页CPU告警",
                "push_title": title,
                "data": data,
                "self_type": _self_type
            },
            level="warning",
        )
        if isinstance(msg, Message):
            return msg

        return msg

