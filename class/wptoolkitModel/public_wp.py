import collections
import contextlib
import json
import os
import re
import sys
import time

import pymysql
import werkzeug

os.chdir("/www/server/panel")
if 'class/' not in sys.path:
    sys.path.insert(0, 'class/')
from public import *

aap_t_simple_result = collections.namedtuple('aap_t_simple_result', ['success', 'msg'])
aap_t_http_multipart = collections.namedtuple('aap_t_http_multipart', ['headers', 'body'])
aap_t_mysql_dump_info = collections.namedtuple('aap_t_mysql_dump_info', ['db_name', 'file', 'dump_time'])
search_sql_special_chars = re.compile(r'''(?<!\\)(?:[%_]|\\(?![^\\abfnrtvxuUN'"0-7]))''')
search_php_first_fatal_error = re.compile(r'PHP Fatal error: \s*([^\r\n]+)')


def get_msg_gettext(msg, args=()):
    try:
        msg = msg.format(*args)
    except:
        pass
    finally:
        return msg

def return_msg_gettext(status, msg, args=()):
    """
        @name 取通用dict返回
        @author hwliang
        @date 2022.9.20
    """
    msg = get_msg_gettext(msg, args)
    if status in(0, "0"):
        status = True
    elif status in(-1, "-1"):
        status = False
    return {'status': status, 'msg': msg}

def success_v2(res, format_args=()):
    """
        @name V2版本的成功响应函数
        @author Zhj<2024-06-05>
        @param res<any> 响应数据
        @param format_args<tuple> 响应文本提示时的format参数
        @return dict
    """
    if isinstance(res, str):
        res = get_msg_gettext(res, format_args)

    return returnMsg(True, res)

def fail_v2(res, format_args=()):
    if isinstance(res, str):
        res = get_msg_gettext(res, format_args)

    return returnMsg(False, res)

def return_message(status, message, data=None):
    if status in(0, "0"):
        status = True
    elif status in(-1, "-1"):
        status = False
    return returnMsg(status, data)

def lang(msg, *args):
    return msg.format(*args)

def make_panel_tmp_path() -> str:
    tmp_path = '{}/temp/tmp_{}_{}'.format(get_panel_path(), int(time.time()), GetRandomString(32))
    if not os.path.exists(tmp_path):
        os.makedirs(tmp_path, 0o755)
    return tmp_path


# 创建临时目录（使用上下文管理器）
@contextlib.contextmanager
def make_panel_tmp_path_with_context():
    tmp_path = make_panel_tmp_path()

    import shutil

    try:
        yield tmp_path
    finally:
        # 删除临时目录
        shutil.rmtree(tmp_path)

def back_file(file, act=None):
    """
        @name 备份配置文件
        @author zhwen<zhw@aapanel.com>
        @param file 需要备份的文件
        @param act 如果存在，则备份一份作为默认配置
    """
    file_type = "_bak"
    if act:
        file_type = "_def"
    ExecShell("/usr/bin/cp -p {0} {1}".format(file, file + file_type))

def OfficialApiBase():
    return 'https://www.aapanel.com'

class HintException(Exception):
    pass

class PanelError(Exception):
    '''
        @name 面板通用异常对像
        @author hwliang<2021-06-25>
    '''

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return ("An error occurred while the panel was running: {}".format(str(self.value)))

def is_number(s) -> bool:
    """
        @name 判断输入参数是否一个数字
        @author Zhj<2022-07-18>
        @param  s<string|integer|float> 输入参数
        @return bool
    """
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass

    return False

class MysqlConn:
    # def __init__(self, db=None, user='root', password=None, port=3306, host='localhost'):
    #     if user == 'root':
    #         password = M('config').where('id=?', (1,)).getField('mysql_root')
    #     self.conn = pymysql.connect(user=user, password=password, db=db, port=port, host=host)
    #
    # def find(self, sql):
    #     cursor = self.conn.cursor()
    #     cursor.execute(sql)
    #     result = cursor.fetchall()
    #     cursor.close()
    #     return result

    def __init__(self, db_name=None, db_user: str = 'root', db_pwd=None, db_host: str = 'localhost'):
        self.__CONN = None
        self.__DB_NAME = db_name
        self.__HOST = db_host
        self.__PORT = 3306
        self.__USERNAME = db_user
        self.__PASSWORD = db_pwd
        self.__CHARSET = 'utf8mb4'
        self.__CONNECT_TIMEOUT = 10
        self.__UNIX_SOCK = None

    def __enter__(self):
        if self.__CONN:
            return self

        if self.__HOST in ('localhost', '127.0.0.1'):
            self.__UNIX_SOCK = '/tmp/mysql.sock'
            self.__CONNECT_TIMEOUT = 1

            myconf = readFile('/etc/my.cnf')
            m = re.search(r"socket\s*=\s*(.+)", myconf)
            if m:
                self.__UNIX_SOCK = m.group(1)

            m = re.search(r"port\s*=\s*([0-9]+)", myconf)
            if m:
                self.__PORT = int(m.group(1))

            if self.__USERNAME == 'root':
                self.__PASSWORD = M('config').where('id=?', (1,)).getField('mysql_root')

        import pymysql

        try:
            self.__CONN = pymysql.connect(host=self.__HOST, user=self.__USERNAME, passwd=self.__PASSWORD,
                                             port=self.__PORT, charset=self.__CHARSET, database=self.__DB_NAME,
                                             connect_timeout=self.__CONNECT_TIMEOUT,
                                             cursorclass=pymysql.cursors.DictCursor, unix_socket=self.__UNIX_SOCK)
        except pymysql.Error:
            if self.__HOST == 'localhost':
                self.__HOST = '127.0.0.1'
                self.__CONN = pymysql.connect(host=self.__HOST, user=self.__USERNAME, passwd=self.__PASSWORD,
                                                 port=self.__PORT, charset=self.__CHARSET, database=self.__DB_NAME,
                                                 connect_timeout=self.__CONNECT_TIMEOUT,
                                                 cursorclass=pymysql.cursors.DictCursor, unix_socket=self.__UNIX_SOCK)
            raise

        return self

    def __del__(self):
        if self.__CONN:
            self.__CONN.close()
            self.__CONN = None

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__CONN.close()
        self.__CONN = None

    def query(self, sql):
        cur = self.__CONN.cursor()

        try:
            row_count = cur.execute(sql)

            if row_count == 0:
                return []

            return cur.fetchall()
        finally:
            cur.close()

    # 查询单条
    def find(self, sql):
        ret = self.query(sql)

        if len(ret) == 0:
            return None

        return ret[0]

    # 执行SQL
    def execute(self, sql):
        cur = self.__CONN.cursor()

        try:
            row_count = cur.execute(sql)

            self.__CONN.commit()

            return row_count
        finally:
            cur.close()

import copy
import re
import json
import socket
import os
import sys
import typing
import collections
from types import MethodType

os.chdir("/www/server/panel")
if 'class/' not in sys.path:
    sys.path.insert(0, 'class/')
import public

re_key_match = re.compile(r'^[\w\s\[\]\-.]+$')
re_key_match2 = re.compile(r'^\.?__[\w\s[\]\-]+__\.?$')
key_filter_list = ['get', 'set', 'get_items', 'exists', '__contains__', '__setitem__', '__getitem__', '__delitem__',
                   '__delattr__', '__setattr__', '__getattr__', '__class__', 'get_file']
# 匹配IP地址
match_ipv4 = re.compile(r'^(?:(?:25[0-5]|(?:2[0-4]|1?\d)?\d)\.){3}(?:25[0-5]|(?:2[0-4]|1?\d)?\d)$')
match_ipv6 = re.compile(r'^(?:(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4})|(?:(?:[0-9a-fA-F]{1,4}:){1,7}:)|(?:(?:[0-9a-fA-F]{1,4}:){6}:[0-9a-fA-F]{1,4})|(?:(?:[0-9a-fA-F]{1,4}:){5}(?::[0-9a-fA-F]{1,4}){1,2})|(?:(?:[0-9a-fA-F]{1,4}:){4}(?::[0-9a-fA-F]{1,4}){1,3})|(?:(?:[0-9a-fA-F]{1,4}:){3}(?::[0-9a-fA-F]{1,4}){1,4})|(?:(?:[0-9a-fA-F]{1,4}:){2}(?::[0-9a-fA-F]{1,4}){1,5})|(?:(?:[0-9a-fA-F]{1,4}:){1}(?::[0-9a-fA-F]{1,4}){1,6})|(?::(?:(?::[0-9a-fA-F]{1,4}){1,7}|:))')
# 安全文件路径
match_safe_path = re.compile(r'^[\w\s./\-]*$')
# HOST基本格式
match_based_host = re.compile(r'^[\w.:\-]+$')
# 匹配类私有属性名称
match_class_private_property = re.compile(r'^(?:_\w+)?__\w+')
# 通用版本号格式验证 major.minor[.patch]/主版本.子版本[.修订号]
match_general_version_format = re.compile(r'^\d+(?:\.\d+){1,2}$')
# md5格式验证
match_md5_format = re.compile(r'^[a-fA-F0-9]{32}$')

aap_t_simple_result = collections.namedtuple('aap_t_simple_result', ['success', 'msg'])

class HintException(Exception):
    pass


class Param:
    __VALIDATE_OPTS = [
        '>',
        '<',
        '>=',
        '<=',
        '=',
        'in',
        'not in',
    ]

    def __init__(self, name: str):
        self.name: str = name
        self.__validate_rules: typing.List[_ValidateRule] = []
        self.__filters: typing.List[callable] = []

    # 验证器 Begin ----->

    def Require(self):
        """
            必选参数
            @return: self
        """
        self.__validate_rules.append(_RequireValidation(self.name))
        return self

    def Date(self):
        """
            日期字符串
            @return: self
        """
        self.__validate_rules.append(_DateValidation(self.name))
        return self

    def Timestamp(self):
        """
            Unix时间戳
            @return: self
        """
        self.__validate_rules.append(_TimestampValidation(self.name))
        return self

    def Url(self):
        """
            URL
            @return: self
        """
        self.__validate_rules.append(_UrlValidation(self.name))
        return self

    def Ip(self):
        """
            IP地址
            @return: self
        """
        self.__validate_rules.append(_IpValidation(self.name))
        return self

    def Ipv4(self):
        """
            IPv4地址
            @return: self
        """
        self.__validate_rules.append(_Ipv4Validation(self.name))
        return self

    def Ipv6(self):
        """
            IPv6地址
            @return: self
        """
        self.__validate_rules.append(_Ipv6Validation(self.name))
        return self

    def Host(self):
        """
            主机地址（可以包含端口号）
            @return: self
        """
        self.__validate_rules.append(_HostValidation(self.name))
        return self

    def Port(self):
        """
            端口号
            @return: self
        """
        return self.Integer('between', [1, 65535])

    def Json(self):
        """
            JSON字符串
            @return: self
        """
        self.__validate_rules.append(_JsonValidation(self.name))
        return self

    def Array(self):
        """
            JSON-Array字符串
            @return: self
        """
        self.__validate_rules.append(_ArrayValidation(self.name))
        return self

    def Object(self):
        """
            JSON-Object字符串
            @return: self
        """
        self.__validate_rules.append(_ObjectValidation(self.name))
        return self

    def List(self):
        """
            限制参数数据类型：list
            @return: self
        """
        self.__validate_rules.append(_ListValidation(self.name))
        return self

    def Tuple(self):
        """
            限制参数数据类型：tuple
            @return: self
        """
        self.__validate_rules.append(_TupleValidation(self.name))
        return self

    def Dict(self):
        """
            限制参数数据类型：dict
            @return: self
        """
        self.__validate_rules.append(_DictValidation(self.name))
        return self

    def Bool(self):
        """
            布尔值或boolean字符串 true/false
            @return: self
        """
        self.__validate_rules.append(_BoolValidation(self.name))
        return self

    def String(self, opt: typing.Optional[str] = None, length_or_list: typing.Optional[typing.Union[int, typing.List[typing.Union[int, str]]]] = None):
        """
            字符串
            @param opt: str 运算符
            @param length_or_list: int|list[int|str]|None 字符串长度或字符串集合
            @return: self
        """
        self.__validate_rules.append(_StringValidation(self.name, opt, length_or_list))
        return self

    def Number(self, opt: typing.Optional[str] = None, num: typing.Optional[typing.Union[int, float, typing.List[typing.Union[int, float]]]] = None):
        """
            数值
            @param opt: str 运算符
            @param num: int 数值大小
            @return: self
        """
        self.__validate_rules.append(_NumberValidation(self.name, opt, num))
        return self

    def Integer(self, opt: typing.Optional[str] = None, num: typing.Optional[typing.Union[typing.Union[int, typing.List[int]]]] = None):
        """
            整数
            @param opt: str 运算符
            @param num: int 数值大小
            @return: self
        """
        self.__validate_rules.append(_IntegerValidation(self.name, opt, num))
        return self

    def Float(self, opt: typing.Optional[str] = None, num: typing.Optional[typing.Union[int, float, typing.List[typing.Union[int, float]]]] = None):
        """
            浮点数
            @param opt: str 运算符
            @param num: int 数值大小
            @return: self
        """
        self.__validate_rules.append(_FloatValidation(self.name, opt, num))
        return self

    def Alpha(self, opt: typing.Optional[str] = None, length_or_list: typing.Optional[typing.Union[int, typing.List[typing.Union[int, str]]]] = None):
        """
            纯字母
            @param opt: str 运算符
            @param length_or_list: int|list[int|str]|None 字符串长度或字符串集合
            @return: self
        """
        self.__validate_rules.append(_AlphaValidation(self.name, opt, length_or_list))
        return self

    def Alphanum(self, opt: typing.Optional[str] = None, length_or_list: typing.Optional[typing.Union[int, typing.List[typing.Union[int, str]]]] = None):
        """
            字母+数字
            @param opt: str 运算符
            @param length_or_list: int|list[int|str]|None 字符串长度或字符串集合
            @return: self
        """
        self.__validate_rules.append(_AlphanumValidation(self.name, opt, length_or_list))
        return self

    def Mobile(self):
        """
            （中国）手机号码
            @return: self
        """
        self.__validate_rules.append(_MobileValidation(self.name))
        return self

    def Email(self):
        """
            邮箱地址
            @return: self
        """
        self.__validate_rules.append(_EmailValidation(self.name))
        return self

    def Regexp(self, exp: str):
        """
            正则表达式
            @param exp: str 正则表达式
            @return: self
        """
        self.__validate_rules.append(_RegexpValidation(self.name, exp))
        return self

    def File(self):
        """
            文件上传
            @return: self
        """
        self.__validate_rules.append(_FileValidation(self.name))
        return self

    def Size(self, opt: typing.Optional[str] = None, size: typing.Optional[typing.Union[int, typing.List[int]]] = None):
        """
            上传文件大小
            @param opt: str 运算符
            @param size: int 上传文件大小bytes
            @return: self
        """
        self.__validate_rules.append(_SizeValidation(self.name, opt, size))
        return self

    def Mime(self, opt: typing.Optional[str] = None, mime_type: typing.Optional[typing.Union[str, typing.List[str]]] = None):
        """
            上传文件Mimetype
            @param opt: str 运算符
            @param mime_type: str 上传文件Mimetype
            @return: self
        """
        self.__validate_rules.append(_MimeValidation(self.name, opt, mime_type))
        return self

    def Ext(self, opt: typing.Optional[str] = None, ext: typing.Optional[typing.Union[str, typing.List[str]]] = None):
        """
            上传文件后缀名
            @param opt: str 运算符
            @param ext: str 上传文件后缀名
            @return: self
        """
        self.__validate_rules.append(_ExtValidation(self.name, opt, ext))
        return self

    def SafePath(self):
        """
            文件路径
            @return: self
        """
        self.__validate_rules.append(_SafePathValidation(self.name))
        return self

    # <------- 验证器 End

    # 过滤器 Begin ------>

    def Trim(self):
        """
            去除字符串两端空白字符
            @return: self
        """
        self.__filters.append(lambda x: str(x).strip())
        return self

    def Xss(self):
        """
            XSS过滤
            @return: self
        """
        self.__filters.append(_xssencode)
        return self

    def Filter(self, f: callable):
        """
            自定义参数过滤器
            @param f: callable func(x: any) -> any
            @return: self
        """
        self.__filters.append(f)
        return self

    # <------- 过滤器 End

    def do_validate(self, args: dict):
        """
            执行验证器
            @param args: dict 请求参数列表
            @return: self
        """
        for v in self.__validate_rules:
            v.validate(args)

        return self

    def do_filter(self, val, extra_filters: typing.Union[typing.List[callable], typing.Tuple[callable]] = ()) -> any:
        """
            执行参数过滤器
            @param val: any
            @param extra_filters: list[callable]|tuple[callable]
            @return: any
        """
        from functools import reduce
        return reduce(lambda x, y: y(x), list(extra_filters) + self.__filters, val)


class _ValidateRule:
    def validate(self, args: dict):
        raise NotImplementedError('method validate() not implemented.')


class _RequireValidation(_ValidateRule):
    """
        必选参数验证类
    """

    def __init__(self, name: str):
        self.name: str = name
        self.errmsg: str = '{} is required'

    def validate(self, args: dict):
        if self.name in args:
            return

        if 'FILES' in args and self.name in args['FILES']:
            return

        raise HintException(self.errmsg.format(self.name))


class _DateValidation(_ValidateRule):
    """
        日期字符串验证类
    """

    def __init__(self, name: str):
        self.name: str = name
        self.errmsg: str = '{} not valid datetime'

    def validate(self, args: dict):
        if self.name not in args:
            return

        if re.match(r'^(?:\d{2}-\d{2}-\d{2}|\d{2}/\d{2}/\d{2})(?: \d{2}:\d{2}(?::\d{2})?)?$',
                    str(args[self.name]).strip()):
            return

        raise HintException(self.errmsg.format(self.name))


class _TimestampValidation(_ValidateRule):
    """
        Unix时间戳验证类
    """

    def __init__(self, name: str):
        self.name: str = name
        self.errmsg: str = '{} not valid timestamp'

    def validate(self, args: dict):
        if self.name not in args:
            return

        if re.match(r'^\d{10}$', str(args[self.name]).strip()):
            return

        raise HintException(self.errmsg.format(self.name))


class _UrlValidation(_ValidateRule):
    """
        URL地址验证类
    """

    def __init__(self, name: str):
        self.name: str = name
        self.errmsg: str = '{} not valid URL'

    def validate(self, args: dict):
        if self.name not in args:
            return

        regex_obj = re.compile(
            r'^(?:http|ftp)s?://'
            r'(?:(?:[A-Z0-9_](?:[A-Z0-9-_]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-_]{2,}\.?)|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        if regex_obj.match(str(args[self.name]).strip()):
            return

        raise HintException(self.errmsg.format(self.name))


class _IpValidation(_ValidateRule):
    """
        IP地址验证类
    """

    def __init__(self, name: str):
        self.name: str = name
        self.errmsg: str = '{} not valid IP'

    def validate(self, args: dict):
        if self.name not in args:
            return

        ipstr = str(args[self.name]).strip()

        if _is_ipv4(ipstr) or _is_ipv6(ipstr):
            return

        raise HintException(self.errmsg.format(self.name))


class _Ipv4Validation(_ValidateRule):
    """
        IPv4地址验证类
    """

    def __init__(self, name: str):
        self.name: str = name
        self.errmsg: str = '{} not valid IPv4'

    def validate(self, args: dict):
        if self.name not in args:
            return

        if _is_ipv4(str(args[self.name]).strip()):
            return

        raise HintException(self.errmsg.format(self.name))


class _Ipv6Validation(_ValidateRule):
    """
        IPv6地址验证类
    """

    def __init__(self, name: str):
        self.name: str = name
        self.errmsg: str = '{} not valid IPv4'

    def validate(self, args: dict):
        if self.name not in args:
            return

        if _is_ipv6(str(args[self.name]).strip()):
            return

        raise HintException(self.errmsg.format(self.name))


class _HostValidation(_ValidateRule):
    """
        主机地址验证类
    """

    def __init__(self, name: str):
        self.name: str = name
        self.errmsg: str = '{} not valid HOST'

    def validate(self, args: dict):
        if self.name not in args:
            return

        if match_based_host.match(str(args[self.name]).strip()):
            return

        raise HintException(self.errmsg.format(self.name))


class _JsonValidation(_ValidateRule):
    """
        JSON字符串验证类
    """

    def __init__(self, name: str):
        self.name: str = name
        self.errmsg: str = '{} not valid JSON'

    def validate(self, args: dict):
        if self.name not in args:
            return

        try:
            json.loads(str(args[self.name]).strip())
            return
        except:
            pass

        raise HintException(self.errmsg.format(self.name))


class _ArrayValidation(_ValidateRule):
    """
        JSON-Array字符串验证类
    """

    def __init__(self, name: str):
        self.name: str = name
        self.errmsg: str = '{} not valid JSON Array'

    def validate(self, args: dict):
        if self.name not in args:
            return

        try:
            obj = json.loads(str(args[self.name]).strip())

            if isinstance(obj, list):
                return
        except:
            pass

        raise HintException(self.errmsg.format(self.name))


class _ObjectValidation(_ValidateRule):
    """
        JSON-Object字符串验证类
    """

    def __init__(self, name: str):
        self.name: str = name
        self.errmsg: str = '{} not valid JSON Object'

    def validate(self, args: dict):
        if self.name not in args:
            return

        try:
            obj = json.loads(str(args[self.name]).strip())

            if isinstance(obj, dict):
                return
        except:
            pass

        raise HintException(self.errmsg.format(self.name))


class _BoolValidation(_ValidateRule):
    """
        bool字符串验证类
    """

    def __init__(self, name: str):
        self.name: str = name
        self.errmsg: str = '{} must be bool'

    def validate(self, args: dict):
        if self.name not in args:
            return

        val = args[self.name]

        if isinstance(val, bool) or re.match(r'^true|false$', str(args[self.name]).strip(), re.IGNORECASE):
            return

        raise HintException(self.errmsg.format(self.name))


class _ListValidation(_ValidateRule):
    """
        list数据类型验证类
    """

    def __init__(self, name: str):
        self.name: str = name
        self.errmsg: str = '{} must be list'

    def validate(self, args: dict):
        if self.name not in args:
            return

        if isinstance(args[self.name], list):
            return

        raise HintException(self.errmsg.format(self.name))


class _TupleValidation(_ValidateRule):
    """
        tuple数据类型验证类
    """

    def __init__(self, name: str):
        self.name: str = name
        self.errmsg: str = '{} must be tuple'

    def validate(self, args: dict):
        if self.name not in args:
            return

        if isinstance(args[self.name], tuple):
            return

        raise HintException(self.errmsg.format(self.name))


class _DictValidation(_ValidateRule):
    """
        dict数据类型验证类
    """

    def __init__(self, name: str):
        self.name: str = name
        self.errmsg: str = '{} must be dict'

    def validate(self, args: dict):
        if self.name not in args:
            return

        if isinstance(args[self.name], dict):
            return

        raise HintException(self.errmsg.format(self.name))


class _OperationHelper:
    """
        运算辅助类
    """

    def __init__(self, name: str, opt: typing.Optional[str], operand: typing.Optional[typing.Union[str, int, float, typing.List[typing.Union[str, int, float]]]], data_type):
        self.name: str = name
        self.opt = opt
        self.operand = operand
        self.data_type = data_type
        self._opt_check()
        self._data_type_check()

    def do(self, val: typing.Union[str, int, float], data_type=None):
        val = str(val).strip()

        if data_type is not None:
            self.data_type = data_type
            self._data_type_check()

        if self.opt is None:
            return

        if self.operand is None:
            return

        if self.opt == '=':
            self._eq(self._calc_num(val))
        elif self.opt == '>':
            self._gt(self._calc_num(val))
        elif self.opt == '>=':
            self._gte(self._calc_num(val))
        elif self.opt == '<':
            self._lt(self._calc_num(val))
        elif self.opt == '<=':
            self._lte(self._calc_num(val))
        elif self.opt == 'between':
            self._between(self._calc_num(val))
        elif self.opt == 'in':
            self._in(self.data_type(val))
        elif self.opt == 'not in':
            self._not_in(self.data_type(val))

    def _calc_num(self, val: str) -> typing.Union[int, float]:
        if self.data_type is str:
            return len(val)

        return self.data_type(val)

    def _opt_check(self):
        if self.opt is None:
            return

        self.opt = self.opt.lower()

        if self.operand is None:
            return

        if self.opt in ['=', '>', '<', '>=', '<='] and not isinstance(self.operand, int):
            raise HintException('当运算符opt是 \'{}\' 时，运算数只能是int类型或float类型，当前类型 {}'.format(self.opt, type(self.operand)))

        if self.opt in ['in', 'not in', 'between'] and not isinstance(self.operand, list):
            raise HintException('当运算符opt是 \'{}\' 时，运算数只能是list类型，当前类型 {}'.format(self.opt, type(self.operand)))

    def _data_type_check(self):
        if self.data_type is str:
            return

        if self.data_type is int:
            return

        if self.data_type is float:
            return

        raise HintException('data_type只能是str、int、float 当前 {}'.format(self.data_type))

    def _eq(self, num: typing.Union[int, float]):
        if num == self.operand:
            return

        raise HintException(
            '{}{} must equal {}'.format(self.name, ' length' if isinstance(self.data_type, str) else '', self.operand))

    def _gt(self, num: typing.Union[int, float]):
        if num > self.operand:
            return

        raise HintException(
            '{}{} must greater than {}'.format(self.name, ' length' if isinstance(self.data_type, str) else '',
                                               self.operand))

    def _gte(self, num: typing.Union[int, float]):
        if num >= self.operand:
            return

        raise HintException(
            '{}{} must greater than or equal {}'.format(self.name, ' length' if isinstance(self.data_type, str) else '',
                                                        self.operand))

    def _lt(self, num: typing.Union[int, float]):
        if num < self.operand:
            return

        raise HintException(
            '{}{} must less than {}'.format(self.name, ' length' if isinstance(self.data_type, str) else '',
                                            self.operand))

    def _lte(self, num: typing.Union[int, float]):
        if num <= self.operand:
            return

        raise HintException(
            '{}{} must less than or equal {}'.format(self.name, ' length' if isinstance(self.data_type, str) else '',
                                                     self.operand))

    def _between(self, num: typing.Union[int, float]):
        if len(self.operand) != 2:
            raise HintException('当运算符opt是 \'between\' 时，运算数只能是list类型，并且list的长度只能是2，当前list长度 {}'.format(len(self.operand)))

        if num >= self.operand[0] and num <= self.operand[1]:
            return

        raise HintException(
            '{}{} must between {} and {}'.format(self.name, ' length' if isinstance(self.data_type, str) else '',
                                                 self.operand[0], self.operand[1]))

    def _in(self, item: typing.Union[int, float, str]):
        if len(self.operand) < 1:
            raise HintException('当运算符opt是 \'{}\' 时，运算数只能是list类型，并且list的长度必须大于0，当前list长度 0'.format(self.opt))

        if item in self.operand:
            return

        raise HintException('{} must in {}'.format(self.name, self.operand))

    def _not_in(self, item: typing.Union[int, float, str]):
        if len(self.operand) < 1:
            raise HintException('当运算符opt是 \'{}\' 时，运算数只能是list类型，并且list的长度必须大于0，当前list长度 0'.format(self.opt))

        if item in self.operand:
            raise HintException('{} must not in {}'.format(self.name, self.operand))


class _StringValidation(_ValidateRule):
    """
        字符串验证类
    """

    def __init__(self, name: str, opt: typing.Optional[str] = None, v: typing.Optional[typing.Union[int, typing.List[typing.Union[int, str]]]] = None):
        self.name: str = name
        self.errmsg: str = '{} must be string'
        self.op = _OperationHelper(name, opt, v, str)

    def validate(self, args: dict):
        if self.name not in args:
            return

        s = args[self.name]

        if isinstance(s, str):
            self.op.do(s)
            return

        raise HintException(self.errmsg.format(self.name))


class _NumberValidation(_ValidateRule):
    """
        数字验证类
    """

    def __init__(self, name: str, opt: typing.Optional[str] = None, num: typing.Optional[typing.Union[int, float, typing.List[typing.Union[int, float]]]] = None):
        self.name: str = name
        self.errmsg: str = '{} must be number'
        self.op = _OperationHelper(name, opt, num, float)

    def validate(self, args: dict):
        if self.name not in args:
            return

        num = args[self.name]

        if _is_number(num):
            self.op.do(num, _get_number_data_type(num))
            return

        raise HintException(self.errmsg.format(self.name))


class _IntegerValidation(_ValidateRule):
    """
        整数验证类
    """

    def __init__(self, name: str, opt: typing.Optional[str] = None, num: typing.Optional[typing.Union[int, typing.List[int]]] = None):
        self.name: str = name
        self.errmsg: str = '{} must be integer'
        self.op = _OperationHelper(name, opt, num, int)

    def validate(self, args: dict):
        if self.name not in args:
            return

        num = args[self.name]

        if _is_int(num):
            self.op.do(num)
            return

        raise HintException(self.errmsg.format(self.name))


class _FloatValidation(_ValidateRule):
    """
        浮点数验证类
    """

    def __init__(self, name: str, opt: typing.Optional[str] = None, num: typing.Optional[typing.Union[float, typing.List[float]]] = None):
        self.name: str = name
        self.errmsg: str = '{} must be float'
        self.op = _OperationHelper(name, opt, num, float)

    def validate(self, args: dict):
        if self.name not in args:
            return

        num = args[self.name]

        if _is_float(num):
            self.op.do(num)
            return

        raise HintException(self.errmsg.format(self.name))


class _AlphaValidation(_ValidateRule):
    """
        纯字母验证类
    """

    def __init__(self, name: str, opt: typing.Optional[str] = None, v: typing.Optional[typing.Union[int, typing.List[typing.Union[int, str]]]] = None):
        self.name: str = name
        self.errmsg: str = '{} must be alpha'
        self.op = _OperationHelper(name, opt, v, str)

    def validate(self, args: dict):
        if self.name not in args:
            return

        s = str(args[self.name]).strip()

        if re.match(r'^[a-zA-Z]+$', s):
            self.op.do(s)
            return

        raise HintException(self.errmsg.format(self.name))


class _AlphanumValidation(_ValidateRule):
    """
        字母数字验证类
    """

    def __init__(self, name: str, opt: typing.Optional[str] = None, v: typing.Optional[typing.Union[int, typing.List[typing.Union[int, str]]]] = None):
        self.name: str = name
        self.errmsg: str = '{} must be alphanum'
        self.op = _OperationHelper(name, opt, v, str)

    def validate(self, args: dict):
        if self.name not in args:
            return

        s = str(args[self.name]).strip()

        if re.match(r'^[a-zA-Z0-9]+$', s):
            self.op.do(s)
            return

        raise HintException(self.errmsg.format(self.name))


class _MobileValidation(_ValidateRule):
    """
        （中国）手机号码验证类
    """

    def __init__(self, name: str):
        self.name: str = name
        self.errmsg: str = '{} not valid mobile'

    def validate(self, args: dict):
        if self.name not in args:
            return

        s = str(args[self.name]).strip()

        if re.match(r'^1[3-9]\d{9}$', s):
            return

        raise HintException(self.errmsg.format(self.name))


class _EmailValidation(_ValidateRule):
    """
        邮箱地址验证类
    """

    def __init__(self, name: str):
        self.name: str = name
        self.errmsg: str = '{} not valid email'

    def validate(self, args: dict):
        if self.name not in args:
            return

        s = str(args[self.name]).strip()

        if re.match(r'^.+@(\[?)[a-zA-Z0-9\-.]+\.(?:[a-zA-Z]{2,}|\d{1,3})\1$', s):
            return

        raise HintException(self.errmsg.format(self.name))


class _RegexpValidation(_ValidateRule):
    """
        正则表达式验证类
    """

    def __init__(self, name: str, regexp: str):
        self.name: str = name
        self.errmsg: str = '{} not success verified by regexp'
        self.regexp: str = regexp

    def validate(self, args: dict):
        if self.name not in args:
            return

        s = str(args[self.name]).strip()

        if re.match(self.regexp, s):
            return

        raise HintException(self.errmsg.format(self.name))


class _FileValidation(_ValidateRule):
    """
        文件上传验证类
    """

    def __init__(self, name: str):
        self.name: str = name
        self.errmsg: str = '{} not valid file'

    def validate(self, args: dict):
        if 'FILES' in args and self.name in args['FILES']:
            return

        raise HintException(self.errmsg.format(self.name))


class _SizeValidation(_ValidateRule):
    """
        文件大小验证类
    """

    def __init__(self, name: str, opt: typing.Optional[str] = None, size: typing.Optional[typing.Union[int, typing.List[int]]] = None):
        self.name: str = name
        self.op = _OperationHelper(name, opt, size, int)

    def validate(self, args: dict):
        if 'FILES' not in args or self.name not in args['FILES']:
            return

        self.op.do(args['FILES'][self.name].content_length)


class _MimeValidation(_ValidateRule):
    """
        文件mimetype验证类
    """

    def __init__(self, name: str, opt: typing.Optional[str] = None, mime_type: typing.Optional[typing.Union[str, typing.List[str]]] = None):
        self.name: str = name
        self.op = _OperationHelper(name, opt, mime_type, str)

    def validate(self, args: dict):
        if 'FILES' not in args or self.name not in args['FILES']:
            return

        self.op.do(args['FILES'][self.name].mimetype)


class _ExtValidation(_ValidateRule):
    """
        文件后缀名验证类
    """

    def __init__(self, name: str, opt: typing.Optional[str] = None, ext: typing.Optional[typing.Union[str, typing.List[str]]] = None):
        self.name: str = name
        self.op = _OperationHelper(name, opt, ext, str)

    def validate(self, args: dict):
        if 'FILES' not in args or self.name not in args['FILES']:
            return

        f = args['FILES'][self.name]

        self.op.do(os.path.splitext(f.filename)[-1])


class _SafePathValidation(_ValidateRule):
    """
        文件路径名验证类
    """

    def __init__(self, name: str):
        self.name: str = name
        self.errmsg = '{} not safe path'

    def validate(self, args: dict):
        if self.name not in args:
            return

        if _is_safe_path(str(args[self.name]).strip()):
            return

        raise HintException(self.errmsg.format(self.name))


def trim_filter() -> callable:
    """
        获取Trim参数过滤器
        @return: callable
    """
    return lambda x: str(x).strip()


def xss_filter() -> callable:
    """
        获取XSS参数过滤器
        @return: callable
    """
    return _xssencode


def _is_ipv4(ip: str) -> bool:
    '''
        @name 是否是IPV4地址
        @author hwliang
        @param ip<string> IP地址
        @return True/False
    '''
    # 验证基本格式
    if not match_ipv4.match(ip):
        return False

    # 验证每个段是否在合理范围
    try:
        socket.inet_pton(socket.AF_INET, ip)
    except AttributeError:
        try:
            socket.inet_aton(ip)
        except socket.error:
            return False
    except socket.error:
        return False
    return True


def _is_ipv6(ip: str) -> bool:
    '''
        @name 是否为IPv6地址
        @author hwliang
        @param ip<string> 地址
        @return True/False
    '''
    # 验证基本格式
    if not match_ipv6.match(ip):
        return False

    # 验证IPv6地址
    try:
        socket.inet_pton(socket.AF_INET6, ip)
    except socket.error:
        return False
    return True


def _xssencode(text: str) -> str:
    """
        XSS过滤
        @param text: str
        @return bool
    """
    try:
        from cgi import html
        list = ['`', '~', '&', '#', '/', '*', '$', '@', '<', '>', '\"', '\'', ';', '%', ',', '.', '\\u']
        ret = []
        for i in text:
            if i in list:
                i = ''
            ret.append(i)
        str_convert = ''.join(ret)
        text2 = html.escape(str_convert, quote=True)
        return text2
    except:
        return text.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')


def _is_safe_path(path: str, force: bool = True) -> bool:
    """
        文件路径过滤
        @param path: str
        @param force: bool
        @return: bool
    """
    if len(path) > 256:
        return False

    checks = ['..', './', '\\', '%', '$', '^', '&', '*', '~', '"', "'", ';', '|', '{', '}', '`']

    for c in checks:
        if path.find(c) > -1:
            return False

    if force:
        if not match_safe_path.match(path):
            return False

    return True


def _is_number(s) -> bool:
    """
        @name 判断输入参数是否一个数字
        @author Zhj<2022-07-18>
        @param  s<string|integer|float> 输入参数
        @return bool
    """
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass

    return False


def _is_int(s) -> bool:
    """
        判断输入是否是整数
        @param s: any
        @return bool
    """
    try:
        int(s)
        return True
    except ValueError:
        pass

    return False


def _is_float(s) -> bool:
    """
        判断输入是否是浮点数
        @param s: any
        @return bool
    """
    try:
        float(s)
        return True
    except ValueError:
        pass

    return False


def _get_number_data_type(s):
    """
        获取数字的数据类型
        @param s<string> 输入参数
        @return int|float
    """
    try:
        int(s)
        return int
    except ValueError:
        pass

    return float


# 参数验证器
class Validator:
    def __init__(self, rules: typing.Union[typing.Tuple[Param], typing.List[Param]], raise_exc: bool = True):
        self.__RULES = list(rules)
        self.__RAISE_EXC = raise_exc

    # 参数格式校验
    def check(self, args: dict) -> aap_t_simple_result:
        try:
            for v in self.__RULES:
                v.do_validate(args)
        except Exception as e:
            if self.__RAISE_EXC:
                raise

            return aap_t_simple_result(False, str(e))

        return aap_t_simple_result(True, 'ok')

    # 参数列表过滤
    def filter(self, args: dict) -> typing.Dict:
        new_args = {}

        for v in self.__RULES:
            if v.name not in args:
                continue

            new_args = v.do_filter(args[v.name])

        return new_args

class dict_obj(dict_obj):
    def __init__(self):
        super().__init__()
        # 存放数据
        self.__store = {}

        # 检测数据是否经过校验
        self.__validated = set()

    def __contains__(self, key):
        return hasattr(self, key)

    def __setitem__(self, key, value):
        if key in key_filter_list:
            raise ValueError("wrong field name")

        if not re_key_match.match(key) or re_key_match2.match(key):
            raise ValueError("wrong field name")

        self.__store[key] = value

    def __getitem__(self, key):
        return getattr(self, key)

    def __delitem__(self, key):
        delattr(self, key)

    def __delattr__(self, key):
        delattr(self, key)

    def __setattr__(self, key, value):
        if match_class_private_property.match(key):
            object.__setattr__(self, key, value)
            return

        self.__store[key] = value

    def __getattr__(self, key):
        if key in self.__store:
            # 未经过校验的数据不允许获取
            # if key not in self.__validated:
            #     raise ValueError('参数值获取失败：参数 {} 尚未通过校验，请先调用 validate() 完成校验后再尝试重新获取参数值'.format(key))
            return self.__store[key]

        raise AttributeError('\'{}\' object has no attribute \'{}\''.format(self.__class__.__name__, key))

    @property
    def __dict__(self):
        return self.__store

    def get_items(self):
        return self.__store

    def validate(self, validate_rules: typing.List[Param], filters: typing.List[callable] = (trim_filter(),)) -> None:
        """
            @name 验证请求参数
            @param validate_rules: list[validate.Param] 参数验证规则
            @param filters: list[callable] 参数过滤器
            @raise Error
        """
        filters = list(filters)

        for v in validate_rules:
            v.do_validate(self.__store)

            if v.name in self.__store:
                self.__store[v.name] = v.do_filter(self.__store[v.name], filters)

            self.__validated.add(v.name)

    def set(self, key, value):
        if not isinstance(value, str) or not isinstance(key, str): return False
        if key in key_filter_list:
            raise ValueError("wrong field name")
        if not re_key_match.match(key) or re_key_match2.match(key):
            raise ValueError("wrong field name")
        return setattr(self, key, value)

def to_dict_obj(data: dict) -> dict_obj:
    '''
        @name 将dict转换为dict_obj
        @author hwliang<2021-07-15>
        @param data<dict> 要被转换的数据
        @return dict_obj
    '''
    if not isinstance(data, dict):
        raise returnMsg(False, 'parameter error: only support transform dict to dict_obj.')
    pdata = dict_obj()
    for key in data.keys():
        pdata[key] = data[key]
    return pdata

def S(table_name: typing.Optional[str] = None, db_name: str = 'default'):
    from wptoolkitModel.sqlite_easy import Db

    query = Db(db_name).query()

    if table_name is not None and str(table_name).strip() != '':
        query.table(str(table_name).strip())

    return query

def OfficialDownloadBase():
    return 'https://node.aapanel.com'

def build_multipart(data: typing.Dict) -> aap_t_http_multipart:
    boundary = b'----AapanelFormBoundary' + GetRandomString(16).encode('utf-8')
    body = b''

    # 标准的HTTP请求报文是使用\r\n换行
    # \n换行也能被解析，可能存在兼容性问题
    eol = b'\r\n'

    for k in data.keys():
        v = data[k]

        # 二进制数据（文件上传）(bytes, filename)
        if isinstance(v, tuple) and len(v) == 2:
            bs, filename = v

            if isinstance(bs, bytes) and isinstance(filename, str):
                body += b'--' + boundary + eol + b'Content-Disposition: form-data; name="' + k.encode('utf-8') + b'"; filename="' + filename.encode('utf-8') + b'"' + eol + b'Content-Type: application/octet-stream' + eol + eol + bs + eol
        # 普通参数
        else:
            # str/number 转 bytes
            if isinstance(v, str) or is_number(v):
                v = str(v).encode('utf-8')

            # 仅处理bytes
            if isinstance(v, bytes):
                body += b'--' + boundary + eol + b'Content-Disposition: form-data; name="' + k.encode('utf-8') + b'"' + eol + eol + v + eol

    body += b'--' + boundary + b'--' + eol

    return aap_t_http_multipart(headers={
        'Content-Type': 'multipart/form-data; boundary=' + boundary.decode('utf-8'),
        'Content-Length': str(len(body)),
    }, body=body)

def SqliteConn(db_name: str = 'default'):
    from wptoolkitModel.sqlite_easy import Db
    return Db(db_name)

aap_t_simple_site_info = collections.namedtuple('aap_t_simple_site_info', ['site_id', 'database_id'])


# 获取当前部署的Web服务器
def get_webserver():
    if os.path.exists('{}/apache/bin/apachectl'.format(get_setup_path())):
        webserver = 'apache'
    elif os.path.exists('/usr/local/lsws/bin/lswsctrl'):
        webserver = 'openlitespeed'
    else:
        webserver = 'nginx'
    return webserver


# 查询网站对应的PHP版本
def get_site_php_version(siteName: str) -> str:
    try:
        webserver = get_webserver()
        setup_path = get_setup_path()

        conf = readFile(
            '{setup_path}/panel/vhost/{webserver}/{siteName}.conf'.format(setup_path=setup_path, webserver=webserver,
                                                                          siteName=siteName))
        if webserver == 'openlitespeed':
            conf = readFile(setup_path + '/panel/vhost/' + webserver + '/detail/' + siteName + '.conf')
        if webserver == 'nginx':
            rep = r"enable-php-(\w{2,5})[-\w]*\.conf"
        elif webserver == 'apache':
            rep = r"php-cgi-(\w{2,5})\.sock"
        else:
            rep = r"path\s*/usr/local/lsws/lsphp(\d+)/bin/lsphp"

        tmp = re.search(rep, conf).groups()

        if tmp[0] == '00':
            return 'Static'

        if tmp[0] == 'other':
            return 'Other'

        return tmp[0][0] + '.' + tmp[0][1]
    except:
        return 'Static'


# 修复网站文件权限
def fix_permissions(site_root_path_or_site_file: str) -> aap_t_simple_result:
    """
    :param site_root_path_or_site_file: str 网站根目录或者单一网站文件
    :return:
    """
    from files import files
    data = files().fix_permissions(to_dict_obj({'path': site_root_path_or_site_file}))

    if int(data.get('status', 0)) != 0:
        return aap_t_simple_result(False, data.get('msg', 'Failed to fix permission'))

    return aap_t_simple_result(True, data.get('msg', 'Fix permission successfully'))


def run_plugin(plugin_name: str, def_name: str, args: dict_obj):
    import PluginLoader
    res = PluginLoader.plugin_run(plugin_name, def_name, args)
    if isinstance(res, dict):
        if 'status' in res and res['status'] == False and 'msg' in res:
            if isinstance(res['msg'], str):
                if res['msg'].find('Traceback ') != -1:
                    raise PanelError(res['msg'])
    return res

# 数据库导出
def dumpsql_with_aap(database_id: int, backup_path: typing.Optional[str] = None):
    import shlex
    db_find = M('databases').where("id=?", (database_id,)).find()

    if not isinstance(db_find, dict):
        raise HintException(get_msg_gettext('Table {} has been corrupted', ('databases',)))

    if backup_path is None:
        backup_path_tmp = M('config').order('`id` desc').limit(1).field('backup_path').find()

        if not isinstance(backup_path_tmp, dict):
            raise HintException(get_msg_gettext('Table {} has been corrupted', ('config',)))

        backup_path = os.path.join(str(backup_path_tmp['backup_path']), 'database')

    name = db_find['name']
    fileName = name + '_' + time.strftime('%Y%m%d_%H%M%S', time.localtime()) + '.sql.gz'
    backupName = os.path.join(backup_path, fileName)
    mysqldump_bin = get_mysqldump_bin()

    from database import database
    database_obj = database()

    if db_find['db_type'] in ['0', 0]:
        # 本地数据库
        # 测试数据库连接
        with MysqlConn() as conn:
            conn.execute("show databases")

        root = M('config').where('id=?', (1,)).getField('mysql_root')
        if not os.path.exists(backup_path):
            os.makedirs(backup_path, 0o600)

        if not database_obj.mypass(True, root):
            raise HintException(get_msg_gettext("Database configuration file failed to get checked, please check "
                                                "if MySQL configuration file exists [/etc/my.cnf]"))

        try:
            password = M('config').where('id=?', (1,)).getField('mysql_root')
            if not password:
                raise HintException(get_msg_gettext("Database password cannot be empty"))

            password = shlex.quote(str(password))
            os.environ["MYSQL_PWD"] = password
            ExecShell(mysqldump_bin + " -R -E --triggers=false --default-character-set=" + get_database_character(name) + " --force --opt \"" + name + "\"  -u root -p" + password + " | gzip > " + backupName)
        finally:
            os.environ["MYSQL_PWD"] = ""

        database_obj.mypass(False, root)

    elif db_find['db_type'] in ['1', 1]:
        # 远程数据库
        try:
            conn_config = json.loads(db_find['conn_config'])
            res = database_obj.CheckCloudDatabase(conn_config)
            if isinstance(res, dict):
                raise HintException(res.get('msg', get_msg_gettext('Cannot connect to remote MySQL')))

            password = shlex.quote(str(conn_config['db_password']))
            os.environ["MYSQL_PWD"] = password
            ExecShell(mysqldump_bin + " -h " + conn_config['db_host'] + " -P " + str(int(conn_config['db_port'])) + " -R -E --triggers=false --default-character-set=" + get_database_character(name) + " --force --opt \"" + str(db_find['name']) + "\"  -u " + str(conn_config['db_user']) + " -p" + password + " | gzip > " + backupName)
        finally:
            os.environ["MYSQL_PWD"] = ""

    elif db_find['db_type'] in ['2', 2]:
        try:
            conn_config = M('database_servers').where('id=?', db_find['sid']).find()
            res = database_obj.CheckCloudDatabase(conn_config)
            if isinstance(res, dict):
                raise HintException(res.get('msg', get_msg_gettext('Cannot connect to remote MySQL')))

            password = shlex.quote(str(conn_config['db_password']))
            os.environ["MYSQL_PWD"] = password
            ExecShell(mysqldump_bin + " -h " + conn_config['db_host'] + " -P " + str(int(conn_config['db_port'])) + " -R -E --triggers=false --default-character-set=" + get_database_character(name) + " --force --opt \"" + str(db_find['name']) + "\"  -u " + str(conn_config['db_user']) + " -p" + str(conn_config['db_password']) + " | gzip > " + backupName)
        finally:
            os.environ["MYSQL_PWD"] = ""

    else:
        raise HintException(get_msg_gettext("Unsupported database type"))

    if not os.path.exists(backupName):
        raise HintException(get_msg_gettext("Backup error"))

    # # 将备份信息添加到数据库中
    # bak_id = M('backup').add('type,name,pid,filename,size,addtime', (1, fileName, id, backupName, 0, time.strftime('%Y-%m-%d %X', time.localtime())))

    return aap_t_mysql_dump_info(db_name=str(db_find['name']), file=backupName, dump_time=int(time.time()))

def restore(db_name: str, bak_file: str):
    from database import database
    data = database().InputSql(to_dict_obj({'name': db_name, 'file': bak_file}))
    return data

def get_available_php_ver_shorts(without_static: bool = True) -> typing.List[str]:
    from panelSite import panelSite
    lst = panelSite().GetPHPVersion(to_dict_obj({}))

    if without_static:
        lst = filter(lambda x: x['version'] != '00', lst)

    return list(map(lambda x: x['version'], lst))

def create_php_site_with_mysql(domain: str, site_path: str, php_ver_short: str, db_user: str, db_pwd: str, another_domains: typing.List = ()) -> aap_t_simple_site_info:
    """
    :param domain: str              网站主域名
    :param site_path: str           网站根目录（绝对路径）
    :param php_ver_short: str       PHP版本号缩写 54、74、80、81...
    :param db_user: str             数据库用户名
    :param db_pwd: str              数据库用户密码
    :param another_domains: list    网站其它解析域名
    :return: aap_t_simple_site_info
    """
    from panelSite import panelSite
    data = panelSite().AddSite(to_dict_obj({
        'webname': json.dumps({
            'domain': domain,
            'domainlist': list(another_domains),
            'count': 0,
        }),
        'ftp': '0',
        'type': 'PHP',
        'version': php_ver_short,
        'port': '80',
        'path': site_path,
        'sql': 'MySQL',
        'datauser': db_user,
        'datapassword': db_pwd,
        'codeing': 'utf8mb4',
        'ps': domain.replace('.', '_').replace('-', '_'),
    }))

    # if int(data.get('status', 0)) != 0:
    #     raise HintException(data.get('message', {})['result'])
    #
    # data = data.get('message', {})
    if "status" in data and not data["status"]:
        return data
    print(data)
    if int(data.get('databaseStatus', 0)) != 1:
        raise HintException('数据库创建失败，请检查mysql运行状态并重试')
    db_data = M('databases').where('pid=?', (data['siteId'],)).find()
    data['d_id'] = db_data['id']
    return aap_t_simple_site_info(data['siteId'], data['d_id'])

def remove_site(site_id: int) -> aap_t_simple_result:
    site_info = M('sites').where('`id` = ?', (site_id,)).field('name').find()

    if not isinstance(site_info, dict):
        return aap_t_simple_result(False, '没找到站点信息 {}'.format(site_id))

    from panelSite import panelSite
    data = panelSite().DeleteSite(to_dict_obj({
        'id': site_id,
        'webname': site_info['name'],
        'ftp': '1',
        'path': '1',
        'database': '1',
    }))
    print(data)

    return data

def escape_sql_str(s: str) -> str:
    return search_sql_special_chars.sub(r'\\\g<0>', s)

def check_password(password):
    """
    密码强度：
    0           弱
    1           中
    2           强
    """
    l = 0
    low = False
    up = False
    symbol = False
    digit = False
    p_len = len(password)
    if p_len < 8:
        return l
    for i in password:
        if i.islower():
            low = True
        if i.isupper():
            up = True
        if i in ['~', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '-', '=', '+', '<', '>', ',', '.', '/',
                 '"', '|', '\\', "'", '?']:
            symbol = True
        if i.isdigit():
            digit = True
    # 判断重复出现
    tmp = len(set([i for i in password]))
    if tmp >= 2:
        if low and up and symbol and digit:
            l = 2
        if p_len >= 11:
            l = 1
    return l

def restore_file(file, act=None):
    """
        @name 还原配置文件
        @author zhwen<zhw@aapanel.com>
        @param file 需要还原的文件
        @param act 如果存在，则还原默认配置
    """
    file_type = "_bak"
    if act:
        file_type = "_def"
    ExecShell("/usr/bin/cp -p {1} {0}".format(file, file + file_type))