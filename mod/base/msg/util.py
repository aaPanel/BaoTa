import sys
from typing import Optional, List, Tuple
from mod.base.push_mod import BaseTask, WxAccountMsgBase, WxAccountMsg, get_push_public_data

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

import public


PANEL_PATH = "/www/server/panel"
public_http_post = public.httpPost
reset_allowed_gai_family = public.reset_allowed_gai_family


def write_push_log(
        module_name: str,
        status: bool,
        title: str,
        user: Optional[List[str]] = None):
    """
    记录 告警推送情况
    @param module_name: 通道方式
    @param status: 是否成功
    @param title: 标题
    @param user: 推送到的用户，可以为空，如：钉钉 不需要
    @return:
    """
    if status:
        status_str = '<span style="color:#20a53a;">成功</span>'
    else:
        status_str = '<span style="color:red;">失败</span>'

    if not user:
        user_str = '[ 默认 ]'
    else:
        user_str = '[ {} ]'.format(",".join(user))

    log = '标题：【{}】，通知方式：【{}】，结果：【{}】，收件人：{}'.format(title, module_name, status_str, user_str)
    public.WriteLog('告警通知', log)
    return True


def write_mail_push_log(
        title: str,
        error_user: List[str],
        success_user: List[str],
):
    """
    记录 告警推送情况
    @param title: 标题
    @param error_user: 失败的用户
    @param success_user: 成功的用户
    @return:
    """
    e_fmt = '<span style="color:#20a53a;">{}</span>'
    s_fmt = '<span style="color:red;">{}</span>'
    error_user_msg = ",".join([e_fmt.format(i) for i in error_user])
    success_user = ",".join([s_fmt.format(i) for i in success_user])
    log = '标题：【{}】，通知方式：【邮箱】，发送失败的收件人：{}，发送成功的收件人：{}'.format(
        title, error_user_msg, success_user
    )
    public.WriteLog('告警通知', log)
    return True


def write_file(filename: str, s_body: str, mode='w+') -> bool:
    """
    写入文件内容
    @filename 文件名
    @s_body 欲写入的内容
    return bool 若文件不存在则尝试自动创建
    """
    try:
        fp = open(filename, mode=mode)
        fp.write(s_body)
        fp.close()
        return True
    except:
        try:
            fp = open(filename, mode=mode, encoding="utf-8")
            fp.write(s_body)
            fp.close()
            return True
        except:
            return False


def read_file(filename, mode='r') -> Optional[str]:
    """
    读取文件内容
    @filename 文件名
    return string(bin) 若文件不存在，则返回None
    """
    import os
    if not os.path.exists(filename):
        return None
    fp = None
    try:
        fp = open(filename, mode=mode)
        f_body = fp.read()
    except:
        return None
    finally:
        if fp and not fp.closed:
            fp.close()
    return f_body


class _TestMsgTask(BaseTask):
    """
    用来测试的短息
    """

    @staticmethod
    def the_push_public_data():
        return get_push_public_data()

    def get_keywords(self, task_data: dict) -> str:
        pass

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        raise NotImplementedError()

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = self.title
        msg.msg = "消息通道配置成功"
        return msg


def get_test_msg(title: str, task_name="消息通道配置提醒") -> _TestMsgTask:
    """
    用来测试的短息
    """
    t = _TestMsgTask()

    t.title = title
    t.template_name = task_name
    return t
