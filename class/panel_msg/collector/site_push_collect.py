from typing import List

from .. import Message, collect_message

_self_type = "push_msg"


class SitePushMsgCollect:
    @staticmethod
    def ssl(s_list: List[str], title: str) -> Message:
        data = "\n".join(s_list)
        msg = collect_message(
            title="宝塔面板SSL到期提醒",
            msg_types=["网站", "网站证书(SSL)到期"],
            source=["网站", title],
            sub_msg={
                "push_type": "网站证书(SSL)到期",
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
    def site_endtime(s_list: List[str], title: str) -> Message:
        data = "\n".join(s_list)
        msg = collect_message(
            title="宝塔面板网站到期提醒",
            msg_types=["网站", "网站到期"],
            source=["网站", title],
            sub_msg={
                "push_type": "网站到期",
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
    def panel_pwd_endtime(s_list: List[str], title: str) -> Message:
        data = "\n".join(s_list)
        msg = collect_message(
            title="宝塔面板密码到期提醒",
            msg_types=["面板", "面板密码有效期"],
            source=["面板设置", "告警通知", title],
            sub_msg={
                "push_type": "面板密码有效期",
                "push_title": title,
                "data": data,
                "self_type": _self_type
            },
            level="info",
        )
        if isinstance(msg, Message):
            return msg

        return msg

    @staticmethod
    def panel_login(p_list: List[str]) -> Message:
        data = "\n".join(p_list)
        msg = collect_message(
            title="面板登录告警",
            msg_types=["面板", "面板登录告警"],
            source=["面板设置", "告警通知", "面板登录告警"],
            sub_msg={
                "push_type": "面板登录告警",
                "push_title": "面板登录告警",
                "data": data,
                "self_type": _self_type
            },
            level="info",
        )

        if isinstance(msg, Message):
            return msg

        return msg

    @staticmethod
    def ssh_login(data: str) -> Message:
        msg = collect_message(
            title="SSH登录告警",
            msg_types=["软件", "SSH登录告警"],
            source=["面板设置", "告警通知", "SSH登录告警"],
            sub_msg={
                "push_type": "SSH登录告警",
                "push_title": "SSH登录告警",
                "data": data,
                "self_type": _self_type
            },
            level="info",
        )
        if isinstance(msg, Message):
            return msg

        return msg

    @staticmethod
    def ssh_login_error(s_list: List[str]) -> Message:
        data = "\n".join(s_list)
        msg = collect_message(
            title="SSH登录失败告警",
            msg_types=["软件", "SSH登录失败告警"],
            source=["面板设置", "告警通知", "SSH登录失败告警"],
            sub_msg={
                "push_type": "SSH登录失败告警",
                "push_title": "SSH登录失败告警",
                "data": data,
                "self_type": _self_type
            },
            level="info",
        )
        if isinstance(msg, Message):
            return msg

        return msg

    # 特殊，请没有next
    @staticmethod
    def services(s_list: List[str], title: str) -> Message:
        data = "\n".join(s_list)
        msg = collect_message(
            title=title,
            msg_types=["软件", "服务停止告警"],
            source=["面板设置", "告警通知", title],
            sub_msg={
                "push_type": "服务停止告警",
                "push_title": title,
                "data": data,
                "self_type": _self_type
            },
            level="info",
        )
        if isinstance(msg, Message):
            return msg

        return msg

    @staticmethod
    def panel_safe_push(s_list: list) -> Message:
        data = "\n".join(s_list)
        msg = collect_message(
            title="面板安全告警",
            msg_types=["面板", "面板安全告警"],
            source=["面板设置", "告警通知", "面板安全告警"],
            sub_msg={
                "push_type": "面板安全告警",
                "push_title": "面板安全告警",
                "data": data,
                "self_type": _self_type
            },
            level="warning",
        )
        if isinstance(msg, Message):
            return msg

        return msg

    @staticmethod
    def panel_update(s_list: List[str]) -> Message:
        data = "\n".join(s_list)
        msg = collect_message(
            title="面板更新提醒",
            msg_types=["面板", "面板更新提醒"],
            source=["面板设置", "告警通知", "面板更新提醒"],
            sub_msg={
                "push_type": "面板更新提醒",
                "push_title": "面板更新提醒",
                "data": data,
                "self_type": _self_type
            },
            level="info",
        )
        if isinstance(msg, Message):
            return msg

        return msg

    @staticmethod
    def project_status(s_list: List[str], title: str) -> Message:
        data = "\n".join(s_list)
        msg = collect_message(
            title=title,
            msg_types=["网站", "项目停止告警"],
            source=["面板设置", "告警通知", title],
            sub_msg={
                "push_type": "项目停止告警",
                "push_title": title,
                "data": data,
                "self_type": _self_type
            },
            level="info",
        )
        if isinstance(msg, Message):
            return msg

        return msg
