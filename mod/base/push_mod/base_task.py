from typing import Union, Optional, List, Tuple, Any
from .send_tool import WxAccountMsg


class BaseTaskViewMsg:

    def get_msg(self, task: dict) -> Optional[str]:
        return ""

# 告警系统在处理每个任务时，都会重新建立有一个Task的对象，(请勿在__init__的初始化函数中添加任何参数)
# 故每个对象中都可以大胆存放本任务所有数据，不会影响同类型的其他任务
class BaseTask:
    VIEW_MSG = BaseTaskViewMsg

    def __init__(self):
        self.source_name: str = ''
        self.title: str = ''   # 这个是告警任务的标题(根据实际情况改变)
        self.template_name: str = ''   # 这个告警模板的标题(不会改变)

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        """
        检查设置的告警参数（是否合理）
        @param task_data: 传入的告警参数，提前会经过默认值处理（即没有的字段添加默认值）
        @return: 当检查无误时，返回一个 dict 当做后续的添加和修改的数据，
                当检查有误时， 直接返回错误信息的字符串
        """
        raise NotImplementedError()

    def get_keyword(self, task_data: dict) -> str:
        """
        返回一个关键字，用于后续查询或执行任务时使用， 例如：防篡改告警，可以根据其规则id生成一个关键字，
        后续通过规则id和来源tamper 查询并使用
        @param task_data: 通过check_args后生成的告警参数字典
        @return: 返回一个关键词字符串
        """
        raise NotImplementedError()

    def get_title(self, task_data: dict) -> str:
        """
        返回一个标题
        @param task_data: 通过check_args后生成的告警参数字典
        @return: 返回一个关键词字符串
        """
        if self.title:
            return self.title
        return self.template_name

    def task_run_end_hook(self, res: dict) -> None:
        """
        在告警系统中。执行完了任务后，会去掉用这个函数
        @type res: dict, 执行任务的结果
        @return:
        """
        return
    
    def task_config_update_hook(self, task: dict) -> Optional[str]:
        """
        在告警管理中。更新任务数据后，会去掉用这个函数
        task 是任务的全部配置信息
        @return: 当返回None值时，表示 更新没有问题，正常储存，否则会将返回的错误信息直接返回前端，不在写入
        例如：检查到这个任务依赖的信息不足时
         >
         > return "该任务需要到xxx处设置添加，无法直接在告警中添加"
         >
        此时会直接跳过
        """
        return 
    
    def task_config_remove_hook(self, task: dict) -> None:
        """
        在告警管理中。移除这个任务后，会去掉用这个函数
        task 是任务的全部配置信息
        @return:
        """
        return 
    
    def task_config_create_hook(self, task: dict) -> Optional[str]:
        """
        在告警管理中。新建这个任务后，会去掉用这个函数
        task 是任务的全部配置信息
        @return: 同 task_config_update_hook
        """
        return 

    def check_time_rule(self, time_rule: dict) -> Union[dict, str]:
        """
        检查和修改设置的告警的时间控制参数是是否合理
        可以添加参数 get_by_func 字段用于指定使用本类中的那个函数执行时间判断标准, 替换标准的时间规则判断功能
         ↑示例如本类中的: can_send_by_time_rule
        @param time_rule: 传入的告警参数，提前会经过默认值处理（即没有的字段添加默认值）
        @return: 当检查无误时，返回一个 dict 当做后续的添加和修改的数据，
                当检查有误时， 直接返回错误信息的字符串
        """
        return time_rule

    def check_num_rule(self, num_rule: dict) -> Union[dict, str]:
        """
        检查和修改设置的告警的次数控制参数是是否合理
        可以添加参数 get_by_func 字段用于指定使用本类中的那个函数执行次数判断标准, 替换标准的次数规则判断功能
         ↑示例如本类中的: can_send_by_num_rule
        @param num_rule: 传入的告警参数，提前会经过默认值处理（即没有的字段添加默认值）
        @return: 当检查无误时，返回一个 dict 当做后续的添加和修改的数据，
                当检查有误时， 直接返回错误信息的字符串
        """
        return num_rule

    def can_send_by_num_rule(self, task_id: str, task_data: dict, number_rule: dict, push_data: dict) -> Optional[str]:
        """
        这是一个通过函数判断是否能够发送告警的示例，并非每一个告警任务都需要有
        @param task_id: 任务id
        @param task_data: 告警参数信息
        @param number_rule: 次数控制信息
        @param push_data: 本次要发送的告警信息的原文，应当为字典, 来自 get_push_data 函数的返回值
        @return: 返回None
        """
        return None

    def can_send_by_time_rule(self, task_id: str, task_data: dict, time_rule: dict, push_data: dict) -> Optional[str]:
        """
        这是一个通过函数判断是否能够发送告警的示例，并非每一个告警任务都需要有
        @param task_id: 任务id
        @param task_data: 告警参数信息
        @param time_rule: 时间控制信息
        @param push_data: 本次要发送的告警信息的原文，应当为字典, 来自 get_push_data 函数的返回值
        @return:
        """
        return None

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        """
        判断这个任务是否需要返送
        @param task_id: 任务id
        @param task_data: 任务的告警参数
        @return: 如果触发了告警，返回一个dict的原文，作为告警信息，否则应当返回None表示未触发
                返回之中应当包含一个 msg_list 的键（值为List[str]类型），将主要的信息返回
                用于以下信息的自动序列化包含[dingding, feishu, mail, weixin, web_hook]
                短信和微信公众号由于长度问题，必须每个任务手动实现
        """
        raise NotImplementedError()

    def filter_template(self, template: dict) -> Optional[dict]:
        """
        过滤 和 更改模板中的信息, 返回空表是当前无法设置该任务
        @param template: 任务的模板信息
        @return:
        """
        raise NotImplementedError()

    # push_public_data 公共的告警参数提取位置
    # 内容包含：
    #   ip  网络ip
    #   local_ip  本机ip
    #   time  时间日志的字符串
    #   timestamp  当前的时间戳
    #   server_name  服务器别名
    def to_dingding_msg(self, push_data: dict, push_public_data: dict) -> str:
        msg_list = push_data.get('msg_list', None)
        if msg_list is None:
            raise ValueError("任务：{}的告警推送数据参数错误, 没有msg_list字段".format(self.title))
        return self.public_headers_msg(push_public_data,dingding=True) + "\n\n" + "\n\n".join(msg_list)

    def to_feishu_msg(self, push_data: dict, push_public_data: dict) -> str:
        msg_list = push_data.get('msg_list', None)
        if msg_list is None:
            raise ValueError("任务：{}的告警推送数据参数错误, 没有msg_list字段".format(self.title))
        return self.public_headers_msg(push_public_data) + "\n" + "\n".join(msg_list)

    def to_mail_msg(self, push_data: dict, push_public_data: dict) -> str:
        msg_list = push_data.get('msg_list', None)
        if msg_list is None:
            raise ValueError("任务：{}的告警推送数据参数错误, 没有msg_list字段".format(self.title))
        public_headers = self.public_headers_msg(push_public_data, "<br>")
        return public_headers + "<br>" + "<br>".join(msg_list)

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        """
        返回 短信告警的类型和数据
        @param push_data:
        @param push_public_data:
        @return: 第一项是类型， 第二项是数据
        """
        raise NotImplementedError()

    def to_weixin_msg(self, push_data: dict, push_public_data: dict) -> str:
        msg_list = push_data.get('msg_list', None)
        if msg_list is None:
            raise ValueError("任务：{}的告警推送数据参数错误, 没有msg_list字段".format(self.title))
        spc = "\n                "
        public_headers = self.public_headers_msg(push_public_data, "\n                ")
        return public_headers + spc + spc.join(msg_list)

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        raise NotImplementedError()

    def to_web_hook_msg(self, push_data: dict, push_public_data: dict) -> str:
        msg_list = push_data.get('msg_list', None)
        if msg_list is None:
            raise ValueError("任务：{}的告警推送数据参数错误, 没有msg_list字段".format(self.title))
        public_headers = self.public_headers_msg(push_public_data, "\n")
        return public_headers + "\n" + "\n".join(msg_list)

    def public_headers_msg(self, push_public_data: dict, spc: str = None, dingding=False) -> str:
        if spc is None:
            spc = "\n\n"
        title = self.title

        if dingding:
            if "面板" not in title:
                title += "面板"

        return spc.join([
            "#### {}".format(title),
            ">服务器：" + push_public_data['server_name'],
            ">IP地址：{}(外) {}(内)".format(push_public_data['ip'], push_public_data['local_ip']),
            ">发送时间：" + push_public_data['time']
        ])
