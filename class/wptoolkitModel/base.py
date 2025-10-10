# import copy
# import re
# import json
# import socket
# import os
# import sys
# import typing
# import collections
# from types import MethodType
#
# os.chdir("/www/server/panel")
# if 'class/' not in sys.path:
#     sys.path.insert(0, 'class/')
# import public
#
# re_key_match = re.compile(r'^[\w\s\[\]\-.]+$')
# re_key_match2 = re.compile(r'^\.?__[\w\s[\]\-]+__\.?$')
# key_filter_list = ['get', 'set', 'get_items', 'exists', '__contains__', '__setitem__', '__getitem__', '__delitem__',
#                    '__delattr__', '__setattr__', '__getattr__', '__class__', 'get_file']
# # 匹配IP地址
# match_ipv4 = re.compile(r'^(?:(?:25[0-5]|(?:2[0-4]|1?\d)?\d)\.){3}(?:25[0-5]|(?:2[0-4]|1?\d)?\d)$')
# match_ipv6 = re.compile(r'^(?:(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4})|(?:(?:[0-9a-fA-F]{1,4}:){1,7}:)|(?:(?:[0-9a-fA-F]{1,4}:){6}:[0-9a-fA-F]{1,4})|(?:(?:[0-9a-fA-F]{1,4}:){5}(?::[0-9a-fA-F]{1,4}){1,2})|(?:(?:[0-9a-fA-F]{1,4}:){4}(?::[0-9a-fA-F]{1,4}){1,3})|(?:(?:[0-9a-fA-F]{1,4}:){3}(?::[0-9a-fA-F]{1,4}){1,4})|(?:(?:[0-9a-fA-F]{1,4}:){2}(?::[0-9a-fA-F]{1,4}){1,5})|(?:(?:[0-9a-fA-F]{1,4}:){1}(?::[0-9a-fA-F]{1,4}){1,6})|(?::(?:(?::[0-9a-fA-F]{1,4}){1,7}|:))')
# # 安全文件路径
# match_safe_path = re.compile(r'^[\w\s./\-]*$')
# # HOST基本格式
# match_based_host = re.compile(r'^[\w.:\-]+$')
# # 匹配类私有属性名称
# match_class_private_property = re.compile(r'^(?:_\w+)?__\w+')
# # 通用版本号格式验证 major.minor[.patch]/主版本.子版本[.修订号]
# match_general_version_format = re.compile(r'^\d+(?:\.\d+){1,2}$')
# # md5格式验证
# match_md5_format = re.compile(r'^[a-fA-F0-9]{32}$')
#
# aap_t_simple_result = collections.namedtuple('aap_t_simple_result', ['success', 'msg'])
#
# class HintException(Exception):
#     pass
#
#
# class Param:
#     __VALIDATE_OPTS = [
#         '>',
#         '<',
#         '>=',
#         '<=',
#         '=',
#         'in',
#         'not in',
#     ]
#
#     def __init__(self, name: str):
#         self.name: str = name
#         self.__validate_rules: typing.List[_ValidateRule] = []
#         self.__filters: typing.List[callable] = []
#
#     # 验证器 Begin ----->
#
#     def Require(self):
#         """
#             必选参数
#             @return: self
#         """
#         self.__validate_rules.append(_RequireValidation(self.name))
#         return self
#
#     def Date(self):
#         """
#             日期字符串
#             @return: self
#         """
#         self.__validate_rules.append(_DateValidation(self.name))
#         return self
#
#     def Timestamp(self):
#         """
#             Unix时间戳
#             @return: self
#         """
#         self.__validate_rules.append(_TimestampValidation(self.name))
#         return self
#
#     def Url(self):
#         """
#             URL
#             @return: self
#         """
#         self.__validate_rules.append(_UrlValidation(self.name))
#         return self
#
#     def Ip(self):
#         """
#             IP地址
#             @return: self
#         """
#         self.__validate_rules.append(_IpValidation(self.name))
#         return self
#
#     def Ipv4(self):
#         """
#             IPv4地址
#             @return: self
#         """
#         self.__validate_rules.append(_Ipv4Validation(self.name))
#         return self
#
#     def Ipv6(self):
#         """
#             IPv6地址
#             @return: self
#         """
#         self.__validate_rules.append(_Ipv6Validation(self.name))
#         return self
#
#     def Host(self):
#         """
#             主机地址（可以包含端口号）
#             @return: self
#         """
#         self.__validate_rules.append(_HostValidation(self.name))
#         return self
#
#     def Port(self):
#         """
#             端口号
#             @return: self
#         """
#         return self.Integer('between', [1, 65535])
#
#     def Json(self):
#         """
#             JSON字符串
#             @return: self
#         """
#         self.__validate_rules.append(_JsonValidation(self.name))
#         return self
#
#     def Array(self):
#         """
#             JSON-Array字符串
#             @return: self
#         """
#         self.__validate_rules.append(_ArrayValidation(self.name))
#         return self
#
#     def Object(self):
#         """
#             JSON-Object字符串
#             @return: self
#         """
#         self.__validate_rules.append(_ObjectValidation(self.name))
#         return self
#
#     def List(self):
#         """
#             限制参数数据类型：list
#             @return: self
#         """
#         self.__validate_rules.append(_ListValidation(self.name))
#         return self
#
#     def Tuple(self):
#         """
#             限制参数数据类型：tuple
#             @return: self
#         """
#         self.__validate_rules.append(_TupleValidation(self.name))
#         return self
#
#     def Dict(self):
#         """
#             限制参数数据类型：dict
#             @return: self
#         """
#         self.__validate_rules.append(_DictValidation(self.name))
#         return self
#
#     def Bool(self):
#         """
#             布尔值或boolean字符串 true/false
#             @return: self
#         """
#         self.__validate_rules.append(_BoolValidation(self.name))
#         return self
#
#     def String(self, opt: typing.Optional[str] = None, length_or_list: typing.Optional[typing.Union[int, typing.List[typing.Union[int, str]]]] = None):
#         """
#             字符串
#             @param opt: str 运算符
#             @param length_or_list: int|list[int|str]|None 字符串长度或字符串集合
#             @return: self
#         """
#         self.__validate_rules.append(_StringValidation(self.name, opt, length_or_list))
#         return self
#
#     def Number(self, opt: typing.Optional[str] = None, num: typing.Optional[typing.Union[int, float, typing.List[typing.Union[int, float]]]] = None):
#         """
#             数值
#             @param opt: str 运算符
#             @param num: int 数值大小
#             @return: self
#         """
#         self.__validate_rules.append(_NumberValidation(self.name, opt, num))
#         return self
#
#     def Integer(self, opt: typing.Optional[str] = None, num: typing.Optional[typing.Union[typing.Union[int, typing.List[int]]]] = None):
#         """
#             整数
#             @param opt: str 运算符
#             @param num: int 数值大小
#             @return: self
#         """
#         self.__validate_rules.append(_IntegerValidation(self.name, opt, num))
#         return self
#
#     def Float(self, opt: typing.Optional[str] = None, num: typing.Optional[typing.Union[int, float, typing.List[typing.Union[int, float]]]] = None):
#         """
#             浮点数
#             @param opt: str 运算符
#             @param num: int 数值大小
#             @return: self
#         """
#         self.__validate_rules.append(_FloatValidation(self.name, opt, num))
#         return self
#
#     def Alpha(self, opt: typing.Optional[str] = None, length_or_list: typing.Optional[typing.Union[int, typing.List[typing.Union[int, str]]]] = None):
#         """
#             纯字母
#             @param opt: str 运算符
#             @param length_or_list: int|list[int|str]|None 字符串长度或字符串集合
#             @return: self
#         """
#         self.__validate_rules.append(_AlphaValidation(self.name, opt, length_or_list))
#         return self
#
#     def Alphanum(self, opt: typing.Optional[str] = None, length_or_list: typing.Optional[typing.Union[int, typing.List[typing.Union[int, str]]]] = None):
#         """
#             字母+数字
#             @param opt: str 运算符
#             @param length_or_list: int|list[int|str]|None 字符串长度或字符串集合
#             @return: self
#         """
#         self.__validate_rules.append(_AlphanumValidation(self.name, opt, length_or_list))
#         return self
#
#     def Mobile(self):
#         """
#             （中国）手机号码
#             @return: self
#         """
#         self.__validate_rules.append(_MobileValidation(self.name))
#         return self
#
#     def Email(self):
#         """
#             邮箱地址
#             @return: self
#         """
#         self.__validate_rules.append(_EmailValidation(self.name))
#         return self
#
#     def Regexp(self, exp: str):
#         """
#             正则表达式
#             @param exp: str 正则表达式
#             @return: self
#         """
#         self.__validate_rules.append(_RegexpValidation(self.name, exp))
#         return self
#
#     def File(self):
#         """
#             文件上传
#             @return: self
#         """
#         self.__validate_rules.append(_FileValidation(self.name))
#         return self
#
#     def Size(self, opt: typing.Optional[str] = None, size: typing.Optional[typing.Union[int, typing.List[int]]] = None):
#         """
#             上传文件大小
#             @param opt: str 运算符
#             @param size: int 上传文件大小bytes
#             @return: self
#         """
#         self.__validate_rules.append(_SizeValidation(self.name, opt, size))
#         return self
#
#     def Mime(self, opt: typing.Optional[str] = None, mime_type: typing.Optional[typing.Union[str, typing.List[str]]] = None):
#         """
#             上传文件Mimetype
#             @param opt: str 运算符
#             @param mime_type: str 上传文件Mimetype
#             @return: self
#         """
#         self.__validate_rules.append(_MimeValidation(self.name, opt, mime_type))
#         return self
#
#     def Ext(self, opt: typing.Optional[str] = None, ext: typing.Optional[typing.Union[str, typing.List[str]]] = None):
#         """
#             上传文件后缀名
#             @param opt: str 运算符
#             @param ext: str 上传文件后缀名
#             @return: self
#         """
#         self.__validate_rules.append(_ExtValidation(self.name, opt, ext))
#         return self
#
#     def SafePath(self):
#         """
#             文件路径
#             @return: self
#         """
#         self.__validate_rules.append(_SafePathValidation(self.name))
#         return self
#
#     # <------- 验证器 End
#
#     # 过滤器 Begin ------>
#
#     def Trim(self):
#         """
#             去除字符串两端空白字符
#             @return: self
#         """
#         self.__filters.append(lambda x: str(x).strip())
#         return self
#
#     def Xss(self):
#         """
#             XSS过滤
#             @return: self
#         """
#         self.__filters.append(_xssencode)
#         return self
#
#     def Filter(self, f: callable):
#         """
#             自定义参数过滤器
#             @param f: callable func(x: any) -> any
#             @return: self
#         """
#         self.__filters.append(f)
#         return self
#
#     # <------- 过滤器 End
#
#     def do_validate(self, args: dict):
#         """
#             执行验证器
#             @param args: dict 请求参数列表
#             @return: self
#         """
#         for v in self.__validate_rules:
#             v.validate(args)
#
#         return self
#
#     def do_filter(self, val, extra_filters: typing.Union[typing.List[callable], typing.Tuple[callable]] = ()) -> any:
#         """
#             执行参数过滤器
#             @param val: any
#             @param extra_filters: list[callable]|tuple[callable]
#             @return: any
#         """
#         from functools import reduce
#         return reduce(lambda x, y: y(x), list(extra_filters) + self.__filters, val)
#
#
# class _ValidateRule:
#     def validate(self, args: dict):
#         raise NotImplementedError('method validate() not implemented.')
#
#
# class _RequireValidation(_ValidateRule):
#     """
#         必选参数验证类
#     """
#
#     def __init__(self, name: str):
#         self.name: str = name
#         self.errmsg: str = '{} is required'
#
#     def validate(self, args: dict):
#         if self.name in args:
#             return
#
#         if 'FILES' in args and self.name in args['FILES']:
#             return
#
#         raise HintException(self.errmsg.format(self.name))
#
#
# class _DateValidation(_ValidateRule):
#     """
#         日期字符串验证类
#     """
#
#     def __init__(self, name: str):
#         self.name: str = name
#         self.errmsg: str = '{} not valid datetime'
#
#     def validate(self, args: dict):
#         if self.name not in args:
#             return
#
#         if re.match(r'^(?:\d{2}-\d{2}-\d{2}|\d{2}/\d{2}/\d{2})(?: \d{2}:\d{2}(?::\d{2})?)?$',
#                     str(args[self.name]).strip()):
#             return
#
#         raise HintException(self.errmsg.format(self.name))
#
#
# class _TimestampValidation(_ValidateRule):
#     """
#         Unix时间戳验证类
#     """
#
#     def __init__(self, name: str):
#         self.name: str = name
#         self.errmsg: str = '{} not valid timestamp'
#
#     def validate(self, args: dict):
#         if self.name not in args:
#             return
#
#         if re.match(r'^\d{10}$', str(args[self.name]).strip()):
#             return
#
#         raise HintException(self.errmsg.format(self.name))
#
#
# class _UrlValidation(_ValidateRule):
#     """
#         URL地址验证类
#     """
#
#     def __init__(self, name: str):
#         self.name: str = name
#         self.errmsg: str = '{} not valid URL'
#
#     def validate(self, args: dict):
#         if self.name not in args:
#             return
#
#         regex_obj = re.compile(
#             r'^(?:http|ftp)s?://'
#             r'(?:(?:[A-Z0-9_](?:[A-Z0-9-_]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-_]{2,}\.?)|'
#             r'localhost|'
#             r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
#             r'(?::\d+)?'
#             r'(?:/?|[/?]\S+)$', re.IGNORECASE)
#
#         if regex_obj.match(str(args[self.name]).strip()):
#             return
#
#         raise HintException(self.errmsg.format(self.name))
#
#
# class _IpValidation(_ValidateRule):
#     """
#         IP地址验证类
#     """
#
#     def __init__(self, name: str):
#         self.name: str = name
#         self.errmsg: str = '{} not valid IP'
#
#     def validate(self, args: dict):
#         if self.name not in args:
#             return
#
#         ipstr = str(args[self.name]).strip()
#
#         if _is_ipv4(ipstr) or _is_ipv6(ipstr):
#             return
#
#         raise HintException(self.errmsg.format(self.name))
#
#
# class _Ipv4Validation(_ValidateRule):
#     """
#         IPv4地址验证类
#     """
#
#     def __init__(self, name: str):
#         self.name: str = name
#         self.errmsg: str = '{} not valid IPv4'
#
#     def validate(self, args: dict):
#         if self.name not in args:
#             return
#
#         if _is_ipv4(str(args[self.name]).strip()):
#             return
#
#         raise HintException(self.errmsg.format(self.name))
#
#
# class _Ipv6Validation(_ValidateRule):
#     """
#         IPv6地址验证类
#     """
#
#     def __init__(self, name: str):
#         self.name: str = name
#         self.errmsg: str = '{} not valid IPv4'
#
#     def validate(self, args: dict):
#         if self.name not in args:
#             return
#
#         if _is_ipv6(str(args[self.name]).strip()):
#             return
#
#         raise HintException(self.errmsg.format(self.name))
#
#
# class _HostValidation(_ValidateRule):
#     """
#         主机地址验证类
#     """
#
#     def __init__(self, name: str):
#         self.name: str = name
#         self.errmsg: str = '{} not valid HOST'
#
#     def validate(self, args: dict):
#         if self.name not in args:
#             return
#
#         if match_based_host.match(str(args[self.name]).strip()):
#             return
#
#         raise HintException(self.errmsg.format(self.name))
#
#
# class _JsonValidation(_ValidateRule):
#     """
#         JSON字符串验证类
#     """
#
#     def __init__(self, name: str):
#         self.name: str = name
#         self.errmsg: str = '{} not valid JSON'
#
#     def validate(self, args: dict):
#         if self.name not in args:
#             return
#
#         try:
#             json.loads(str(args[self.name]).strip())
#             return
#         except:
#             pass
#
#         raise HintException(self.errmsg.format(self.name))
#
#
# class _ArrayValidation(_ValidateRule):
#     """
#         JSON-Array字符串验证类
#     """
#
#     def __init__(self, name: str):
#         self.name: str = name
#         self.errmsg: str = '{} not valid JSON Array'
#
#     def validate(self, args: dict):
#         if self.name not in args:
#             return
#
#         try:
#             obj = json.loads(str(args[self.name]).strip())
#
#             if isinstance(obj, list):
#                 return
#         except:
#             pass
#
#         raise HintException(self.errmsg.format(self.name))
#
#
# class _ObjectValidation(_ValidateRule):
#     """
#         JSON-Object字符串验证类
#     """
#
#     def __init__(self, name: str):
#         self.name: str = name
#         self.errmsg: str = '{} not valid JSON Object'
#
#     def validate(self, args: dict):
#         if self.name not in args:
#             return
#
#         try:
#             obj = json.loads(str(args[self.name]).strip())
#
#             if isinstance(obj, dict):
#                 return
#         except:
#             pass
#
#         raise HintException(self.errmsg.format(self.name))
#
#
# class _BoolValidation(_ValidateRule):
#     """
#         bool字符串验证类
#     """
#
#     def __init__(self, name: str):
#         self.name: str = name
#         self.errmsg: str = '{} must be bool'
#
#     def validate(self, args: dict):
#         if self.name not in args:
#             return
#
#         val = args[self.name]
#
#         if isinstance(val, bool) or re.match(r'^true|false$', str(args[self.name]).strip(), re.IGNORECASE):
#             return
#
#         raise HintException(self.errmsg.format(self.name))
#
#
# class _ListValidation(_ValidateRule):
#     """
#         list数据类型验证类
#     """
#
#     def __init__(self, name: str):
#         self.name: str = name
#         self.errmsg: str = '{} must be list'
#
#     def validate(self, args: dict):
#         if self.name not in args:
#             return
#
#         if isinstance(args[self.name], list):
#             return
#
#         raise HintException(self.errmsg.format(self.name))
#
#
# class _TupleValidation(_ValidateRule):
#     """
#         tuple数据类型验证类
#     """
#
#     def __init__(self, name: str):
#         self.name: str = name
#         self.errmsg: str = '{} must be tuple'
#
#     def validate(self, args: dict):
#         if self.name not in args:
#             return
#
#         if isinstance(args[self.name], tuple):
#             return
#
#         raise HintException(self.errmsg.format(self.name))
#
#
# class _DictValidation(_ValidateRule):
#     """
#         dict数据类型验证类
#     """
#
#     def __init__(self, name: str):
#         self.name: str = name
#         self.errmsg: str = '{} must be dict'
#
#     def validate(self, args: dict):
#         if self.name not in args:
#             return
#
#         if isinstance(args[self.name], dict):
#             return
#
#         raise HintException(self.errmsg.format(self.name))
#
#
# class _OperationHelper:
#     """
#         运算辅助类
#     """
#
#     def __init__(self, name: str, opt: typing.Optional[str], operand: typing.Optional[typing.Union[str, int, float, typing.List[typing.Union[str, int, float]]]], data_type):
#         self.name: str = name
#         self.opt = opt
#         self.operand = operand
#         self.data_type = data_type
#         self._opt_check()
#         self._data_type_check()
#
#     def do(self, val: typing.Union[str, int, float], data_type=None):
#         val = str(val).strip()
#
#         if data_type is not None:
#             self.data_type = data_type
#             self._data_type_check()
#
#         if self.opt is None:
#             return
#
#         if self.operand is None:
#             return
#
#         if self.opt == '=':
#             self._eq(self._calc_num(val))
#         elif self.opt == '>':
#             self._gt(self._calc_num(val))
#         elif self.opt == '>=':
#             self._gte(self._calc_num(val))
#         elif self.opt == '<':
#             self._lt(self._calc_num(val))
#         elif self.opt == '<=':
#             self._lte(self._calc_num(val))
#         elif self.opt == 'between':
#             self._between(self._calc_num(val))
#         elif self.opt == 'in':
#             self._in(self.data_type(val))
#         elif self.opt == 'not in':
#             self._not_in(self.data_type(val))
#
#     def _calc_num(self, val: str) -> typing.Union[int, float]:
#         if self.data_type is str:
#             return len(val)
#
#         return self.data_type(val)
#
#     def _opt_check(self):
#         if self.opt is None:
#             return
#
#         self.opt = self.opt.lower()
#
#         if self.operand is None:
#             return
#
#         if self.opt in ['=', '>', '<', '>=', '<='] and not isinstance(self.operand, int):
#             raise HintException('当运算符opt是 \'{}\' 时，运算数只能是int类型或float类型，当前类型 {}'.format(self.opt, type(self.operand)))
#
#         if self.opt in ['in', 'not in', 'between'] and not isinstance(self.operand, list):
#             raise HintException('当运算符opt是 \'{}\' 时，运算数只能是list类型，当前类型 {}'.format(self.opt, type(self.operand)))
#
#     def _data_type_check(self):
#         if self.data_type is str:
#             return
#
#         if self.data_type is int:
#             return
#
#         if self.data_type is float:
#             return
#
#         raise HintException('data_type只能是str、int、float 当前 {}'.format(self.data_type))
#
#     def _eq(self, num: typing.Union[int, float]):
#         if num == self.operand:
#             return
#
#         raise HintException(
#             '{}{} must equal {}'.format(self.name, ' length' if isinstance(self.data_type, str) else '', self.operand))
#
#     def _gt(self, num: typing.Union[int, float]):
#         if num > self.operand:
#             return
#
#         raise HintException(
#             '{}{} must greater than {}'.format(self.name, ' length' if isinstance(self.data_type, str) else '',
#                                                self.operand))
#
#     def _gte(self, num: typing.Union[int, float]):
#         if num >= self.operand:
#             return
#
#         raise HintException(
#             '{}{} must greater than or equal {}'.format(self.name, ' length' if isinstance(self.data_type, str) else '',
#                                                         self.operand))
#
#     def _lt(self, num: typing.Union[int, float]):
#         if num < self.operand:
#             return
#
#         raise HintException(
#             '{}{} must less than {}'.format(self.name, ' length' if isinstance(self.data_type, str) else '',
#                                             self.operand))
#
#     def _lte(self, num: typing.Union[int, float]):
#         if num <= self.operand:
#             return
#
#         raise HintException(
#             '{}{} must less than or equal {}'.format(self.name, ' length' if isinstance(self.data_type, str) else '',
#                                                      self.operand))
#
#     def _between(self, num: typing.Union[int, float]):
#         if len(self.operand) != 2:
#             raise HintException('当运算符opt是 \'between\' 时，运算数只能是list类型，并且list的长度只能是2，当前list长度 {}'.format(len(self.operand)))
#
#         if num >= self.operand[0] and num <= self.operand[1]:
#             return
#
#         raise HintException(
#             '{}{} must between {} and {}'.format(self.name, ' length' if isinstance(self.data_type, str) else '',
#                                                  self.operand[0], self.operand[1]))
#
#     def _in(self, item: typing.Union[int, float, str]):
#         if len(self.operand) < 1:
#             raise HintException('当运算符opt是 \'{}\' 时，运算数只能是list类型，并且list的长度必须大于0，当前list长度 0'.format(self.opt))
#
#         if item in self.operand:
#             return
#
#         raise HintException('{} must in {}'.format(self.name, self.operand))
#
#     def _not_in(self, item: typing.Union[int, float, str]):
#         if len(self.operand) < 1:
#             raise HintException('当运算符opt是 \'{}\' 时，运算数只能是list类型，并且list的长度必须大于0，当前list长度 0'.format(self.opt))
#
#         if item in self.operand:
#             raise HintException('{} must not in {}'.format(self.name, self.operand))
#
#
# class _StringValidation(_ValidateRule):
#     """
#         字符串验证类
#     """
#
#     def __init__(self, name: str, opt: typing.Optional[str] = None, v: typing.Optional[typing.Union[int, typing.List[typing.Union[int, str]]]] = None):
#         self.name: str = name
#         self.errmsg: str = '{} must be string'
#         self.op = _OperationHelper(name, opt, v, str)
#
#     def validate(self, args: dict):
#         if self.name not in args:
#             return
#
#         s = args[self.name]
#
#         if isinstance(s, str):
#             self.op.do(s)
#             return
#
#         raise HintException(self.errmsg.format(self.name))
#
#
# class _NumberValidation(_ValidateRule):
#     """
#         数字验证类
#     """
#
#     def __init__(self, name: str, opt: typing.Optional[str] = None, num: typing.Optional[typing.Union[int, float, typing.List[typing.Union[int, float]]]] = None):
#         self.name: str = name
#         self.errmsg: str = '{} must be number'
#         self.op = _OperationHelper(name, opt, num, float)
#
#     def validate(self, args: dict):
#         if self.name not in args:
#             return
#
#         num = args[self.name]
#
#         if _is_number(num):
#             self.op.do(num, _get_number_data_type(num))
#             return
#
#         raise HintException(self.errmsg.format(self.name))
#
#
# class _IntegerValidation(_ValidateRule):
#     """
#         整数验证类
#     """
#
#     def __init__(self, name: str, opt: typing.Optional[str] = None, num: typing.Optional[typing.Union[int, typing.List[int]]] = None):
#         self.name: str = name
#         self.errmsg: str = '{} must be integer'
#         self.op = _OperationHelper(name, opt, num, int)
#
#     def validate(self, args: dict):
#         if self.name not in args:
#             return
#
#         num = args[self.name]
#
#         if _is_int(num):
#             self.op.do(num)
#             return
#
#         raise HintException(self.errmsg.format(self.name))
#
#
# class _FloatValidation(_ValidateRule):
#     """
#         浮点数验证类
#     """
#
#     def __init__(self, name: str, opt: typing.Optional[str] = None, num: typing.Optional[typing.Union[float, typing.List[float]]] = None):
#         self.name: str = name
#         self.errmsg: str = '{} must be float'
#         self.op = _OperationHelper(name, opt, num, float)
#
#     def validate(self, args: dict):
#         if self.name not in args:
#             return
#
#         num = args[self.name]
#
#         if _is_float(num):
#             self.op.do(num)
#             return
#
#         raise HintException(self.errmsg.format(self.name))
#
#
# class _AlphaValidation(_ValidateRule):
#     """
#         纯字母验证类
#     """
#
#     def __init__(self, name: str, opt: typing.Optional[str] = None, v: typing.Optional[typing.Union[int, typing.List[typing.Union[int, str]]]] = None):
#         self.name: str = name
#         self.errmsg: str = '{} must be alpha'
#         self.op = _OperationHelper(name, opt, v, str)
#
#     def validate(self, args: dict):
#         if self.name not in args:
#             return
#
#         s = str(args[self.name]).strip()
#
#         if re.match(r'^[a-zA-Z]+$', s):
#             self.op.do(s)
#             return
#
#         raise HintException(self.errmsg.format(self.name))
#
#
# class _AlphanumValidation(_ValidateRule):
#     """
#         字母数字验证类
#     """
#
#     def __init__(self, name: str, opt: typing.Optional[str] = None, v: typing.Optional[typing.Union[int, typing.List[typing.Union[int, str]]]] = None):
#         self.name: str = name
#         self.errmsg: str = '{} must be alphanum'
#         self.op = _OperationHelper(name, opt, v, str)
#
#     def validate(self, args: dict):
#         if self.name not in args:
#             return
#
#         s = str(args[self.name]).strip()
#
#         if re.match(r'^[a-zA-Z0-9]+$', s):
#             self.op.do(s)
#             return
#
#         raise HintException(self.errmsg.format(self.name))
#
#
# class _MobileValidation(_ValidateRule):
#     """
#         （中国）手机号码验证类
#     """
#
#     def __init__(self, name: str):
#         self.name: str = name
#         self.errmsg: str = '{} not valid mobile'
#
#     def validate(self, args: dict):
#         if self.name not in args:
#             return
#
#         s = str(args[self.name]).strip()
#
#         if re.match(r'^1[3-9]\d{9}$', s):
#             return
#
#         raise HintException(self.errmsg.format(self.name))
#
#
# class _EmailValidation(_ValidateRule):
#     """
#         邮箱地址验证类
#     """
#
#     def __init__(self, name: str):
#         self.name: str = name
#         self.errmsg: str = '{} not valid email'
#
#     def validate(self, args: dict):
#         if self.name not in args:
#             return
#
#         s = str(args[self.name]).strip()
#
#         if re.match(r'^.+@(\[?)[a-zA-Z0-9\-.]+\.(?:[a-zA-Z]{2,}|\d{1,3})\1$', s):
#             return
#
#         raise HintException(self.errmsg.format(self.name))
#
#
# class _RegexpValidation(_ValidateRule):
#     """
#         正则表达式验证类
#     """
#
#     def __init__(self, name: str, regexp: str):
#         self.name: str = name
#         self.errmsg: str = '{} not success verified by regexp'
#         self.regexp: str = regexp
#
#     def validate(self, args: dict):
#         if self.name not in args:
#             return
#
#         s = str(args[self.name]).strip()
#
#         if re.match(self.regexp, s):
#             return
#
#         raise HintException(self.errmsg.format(self.name))
#
#
# class _FileValidation(_ValidateRule):
#     """
#         文件上传验证类
#     """
#
#     def __init__(self, name: str):
#         self.name: str = name
#         self.errmsg: str = '{} not valid file'
#
#     def validate(self, args: dict):
#         if 'FILES' in args and self.name in args['FILES']:
#             return
#
#         raise HintException(self.errmsg.format(self.name))
#
#
# class _SizeValidation(_ValidateRule):
#     """
#         文件大小验证类
#     """
#
#     def __init__(self, name: str, opt: typing.Optional[str] = None, size: typing.Optional[typing.Union[int, typing.List[int]]] = None):
#         self.name: str = name
#         self.op = _OperationHelper(name, opt, size, int)
#
#     def validate(self, args: dict):
#         if 'FILES' not in args or self.name not in args['FILES']:
#             return
#
#         self.op.do(args['FILES'][self.name].content_length)
#
#
# class _MimeValidation(_ValidateRule):
#     """
#         文件mimetype验证类
#     """
#
#     def __init__(self, name: str, opt: typing.Optional[str] = None, mime_type: typing.Optional[typing.Union[str, typing.List[str]]] = None):
#         self.name: str = name
#         self.op = _OperationHelper(name, opt, mime_type, str)
#
#     def validate(self, args: dict):
#         if 'FILES' not in args or self.name not in args['FILES']:
#             return
#
#         self.op.do(args['FILES'][self.name].mimetype)
#
#
# class _ExtValidation(_ValidateRule):
#     """
#         文件后缀名验证类
#     """
#
#     def __init__(self, name: str, opt: typing.Optional[str] = None, ext: typing.Optional[typing.Union[str, typing.List[str]]] = None):
#         self.name: str = name
#         self.op = _OperationHelper(name, opt, ext, str)
#
#     def validate(self, args: dict):
#         if 'FILES' not in args or self.name not in args['FILES']:
#             return
#
#         f = args['FILES'][self.name]
#
#         self.op.do(os.path.splitext(f.filename)[-1])
#
#
# class _SafePathValidation(_ValidateRule):
#     """
#         文件路径名验证类
#     """
#
#     def __init__(self, name: str):
#         self.name: str = name
#         self.errmsg = '{} not safe path'
#
#     def validate(self, args: dict):
#         if self.name not in args:
#             return
#
#         if _is_safe_path(str(args[self.name]).strip()):
#             return
#
#         raise HintException(self.errmsg.format(self.name))
#
#
# def trim_filter() -> callable:
#     """
#         获取Trim参数过滤器
#         @return: callable
#     """
#     return lambda x: str(x).strip()
#
#
# def xss_filter() -> callable:
#     """
#         获取XSS参数过滤器
#         @return: callable
#     """
#     return _xssencode
#
#
# def _is_ipv4(ip: str) -> bool:
#     '''
#         @name 是否是IPV4地址
#         @author hwliang
#         @param ip<string> IP地址
#         @return True/False
#     '''
#     # 验证基本格式
#     if not match_ipv4.match(ip):
#         return False
#
#     # 验证每个段是否在合理范围
#     try:
#         socket.inet_pton(socket.AF_INET, ip)
#     except AttributeError:
#         try:
#             socket.inet_aton(ip)
#         except socket.error:
#             return False
#     except socket.error:
#         return False
#     return True
#
#
# def _is_ipv6(ip: str) -> bool:
#     '''
#         @name 是否为IPv6地址
#         @author hwliang
#         @param ip<string> 地址
#         @return True/False
#     '''
#     # 验证基本格式
#     if not match_ipv6.match(ip):
#         return False
#
#     # 验证IPv6地址
#     try:
#         socket.inet_pton(socket.AF_INET6, ip)
#     except socket.error:
#         return False
#     return True
#
#
# def _xssencode(text: str) -> str:
#     """
#         XSS过滤
#         @param text: str
#         @return bool
#     """
#     try:
#         from cgi import html
#         list = ['`', '~', '&', '#', '/', '*', '$', '@', '<', '>', '\"', '\'', ';', '%', ',', '.', '\\u']
#         ret = []
#         for i in text:
#             if i in list:
#                 i = ''
#             ret.append(i)
#         str_convert = ''.join(ret)
#         text2 = html.escape(str_convert, quote=True)
#         return text2
#     except:
#         return text.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
#
#
# def _is_safe_path(path: str, force: bool = True) -> bool:
#     """
#         文件路径过滤
#         @param path: str
#         @param force: bool
#         @return: bool
#     """
#     if len(path) > 256:
#         return False
#
#     checks = ['..', './', '\\', '%', '$', '^', '&', '*', '~', '"', "'", ';', '|', '{', '}', '`']
#
#     for c in checks:
#         if path.find(c) > -1:
#             return False
#
#     if force:
#         if not match_safe_path.match(path):
#             return False
#
#     return True
#
#
# def _is_number(s) -> bool:
#     """
#         @name 判断输入参数是否一个数字
#         @author Zhj<2022-07-18>
#         @param  s<string|integer|float> 输入参数
#         @return bool
#     """
#     try:
#         float(s)
#         return True
#     except ValueError:
#         pass
#
#     try:
#         import unicodedata
#         unicodedata.numeric(s)
#         return True
#     except (TypeError, ValueError):
#         pass
#
#     return False
#
#
# def _is_int(s) -> bool:
#     """
#         判断输入是否是整数
#         @param s: any
#         @return bool
#     """
#     try:
#         int(s)
#         return True
#     except ValueError:
#         pass
#
#     return False
#
#
# def _is_float(s) -> bool:
#     """
#         判断输入是否是浮点数
#         @param s: any
#         @return bool
#     """
#     try:
#         float(s)
#         return True
#     except ValueError:
#         pass
#
#     return False
#
#
# def _get_number_data_type(s):
#     """
#         获取数字的数据类型
#         @param s<string> 输入参数
#         @return int|float
#     """
#     try:
#         int(s)
#         return int
#     except ValueError:
#         pass
#
#     return float
#
#
# # 参数验证器
# class Validator:
#     def __init__(self, rules: typing.Union[typing.Tuple[Param], typing.List[Param]], raise_exc: bool = True):
#         self.__RULES = list(rules)
#         self.__RAISE_EXC = raise_exc
#
#     # 参数格式校验
#     def check(self, args: dict) -> aap_t_simple_result:
#         try:
#             for v in self.__RULES:
#                 v.do_validate(args)
#         except Exception as e:
#             if self.__RAISE_EXC:
#                 raise
#
#             return aap_t_simple_result(False, str(e))
#
#         return aap_t_simple_result(True, 'ok')
#
#     # 参数列表过滤
#     def filter(self, args: dict) -> typing.Dict:
#         new_args = {}
#
#         for v in self.__RULES:
#             if v.name not in args:
#                 continue
#
#             new_args = v.do_filter(args[v.name])
#
#         return new_args
#
#
# class wpbase(object):
#     __validated = set()
#     __store = {}
#     def __init__(self, get=None):
#         # self.__validated = set()
#         # self.__store = {}
#         if get:
#             self.__store = vars(get)
#             # for key, value in vars(get).items():
#             #     self.set(key, value)
#         # print(self.__store)
#
#
#     def __setattr__(self, key, value):
#         if match_class_private_property.match(key):
#             object.__setattr__(self, key, value)
#             return
#
#         self.__store[key] = value
#
#     # def set(self, key, value):
#     #     # if not isinstance(value, str) or not isinstance(key, str): return False
#     #     if key in key_filter_list:
#     #         raise ValueError("wrong field name")
#     #     if not re_key_match.match(key) or re_key_match2.match(key):
#     #         raise ValueError("wrong field name")
#     #     return setattr(self, key, value)
#
#     def get_items(self):
#         return self.__store
#
#     def validate(self, validate_rules: typing.List[Param], filters: typing.List[callable] = (trim_filter(),), args=None) -> None:
#         """
#             @name 验证请求参数
#             @param validate_rules: list[validate.Param] 参数验证规则
#             @param filters: list[callable] 参数过滤器
#             @raise Error
#         """
#         filters = list(filters)
#         if args:
#             if not isinstance(args, dict):
#                 self.__store = vars(args)
#             else:
#                 self.__store = args
#         for v in validate_rules:
#             v.do_validate(self.__store)
#
#             if v.name in self.__store:
#                 self.__store[v.name] = v.do_filter(self.__store[v.name], filters)
#
#             self.__validated.add(v.name)
class wpbase(object):
    def __init__(self, get=None):
        pass