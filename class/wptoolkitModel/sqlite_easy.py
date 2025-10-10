# Easy Sqlite Toolkit
# Author Zhj<2022-12-06>

import typing
import fcntl
import os
import sqlite3
import time
import traceback
import re
import copy
import weakref
from functools import reduce
from contextlib import contextmanager
from wptoolkitModel.gcmanager import gc_enable, gc_disable
from public_wp import is_number
from public_wp import HintException, PanelError


_BASE_DIR = '/www/server/panel'


# 记录错误日志
def _log(e):
    if isinstance(e, HintException):
        return

    # 日志目录
    log_dir = '{}/logs/sqlite_easy/{}'.format(_BASE_DIR, time.strftime('%Y%m'))

    # 确保目录已创建
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, 0o600)

    # 记录错误日志
    with open('{}/{}.log'.format(log_dir, time.strftime('%d')), 'a') as fp:
        fp.write('[{}]{}\n'.format(time.strftime('%Y-%m-%d %X'), str(e)))

        # 如果是异常，打印异常堆栈信息
        if isinstance(e, BaseException):
            fp.write('{}\n'.format(traceback.format_exc()))


# 日志打印
def _log2(s, log_file='sqlite_client.log'):
    log_dir = '{}/logs'.format(_BASE_DIR)

    # 确保目录已创建
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, 0o600)

    with open('{}/{}'.format(log_dir, log_file), 'a') as fp:
        fp.write('[{}]{}\n'.format(time.strftime('%Y-%m-%d %X'), s))


def _to_tuple(p):
    '''
        @name 将输入参数转为元组
        @author Zhj<2022-07-16>
        @param  p<mixed> 输入参数
        @return tuple
    '''
    # 输入参数为元组时 直接返回
    if isinstance(p, tuple):
        return p

    # 输入参数为列表时 转为元组
    if isinstance(p, list):
        return tuple(p)

    # 其他情况 直接创建一个元组 并将参数放入其中
    return (p,)


# 正则表达式列表
# 匹配SQL字段名称的正则表达式
match_field_reg = re.compile(r'^(?:`?(\w+)`?\.)?`?(\w+)`?$', flags=re.IGNORECASE)

# 匹配表名的正则表达式
match_table_name_reg = re.compile(r'^([\w`]+)(?:(?:\s+AS\s+|\s+)([\w`]+))?$', flags=re.IGNORECASE)

# 匹配【?】号的正则表达式
search_question_reg = re.compile(r'\?')

# 匹配查询字段名称的正则表达式
match_row_key_reg = re.compile(r'^(?:distinct\s+)?(?:[\w`]+\.)?([\w`]+)(?:(?:\s+AS\s+|\s+)([\w`]+))?$', flags=re.IGNORECASE)

# 匹配查询字段别名的正则表达式
search_row_key_reg = re.compile(r'(?:\s+AS\s+|\s+)([\w`]+)$', flags=re.IGNORECASE)

# 匹配SQL逻辑操作符【AND】【OR】的正则表达式
search_logic_opt_reg = re.compile(r'\s+(?:AND|OR)\s+', flags=re.IGNORECASE)

# 匹配以【1 AND 】开头的WHERE语句的正则表达式
match_where_str_begin_reg = re.compile(r'^1\s+(?:AND|OR)\s+', flags=re.IGNORECASE)

# 匹配引号【'】【"】的正则表达式
search_quote_reg = re.compile(r'(?<!\\)([\'"])')

# 匹配子查询的正则表达式
search_subquery_reg = re.compile(r'^(\([\s\S]+?\))(?:(?:\s+AS\s+|\s+)([\w`]+))?$', flags=re.IGNORECASE)


def _add_backtick_for_field(field):
    '''
        @name 给字段名添加反引号
        @author Zhj<2022-07-16>
        @param  field<string> 字段名
        @return string
    '''
    return match_field_reg.sub(lambda m: '{}{}'.format(
        '' if m.group(1) is None else '`%s`.' % m.group(1),
        '`%s`' % m.group(2)
    ), str(field).strip())


def _format_cursor(cursor):
    '''
        @name 将cursor对象转换为list对象
        @author Zhj<2023-04-25>
        @param  cursor<sqlite.Cursor> 游标对象
        @return list
    '''
    gc_disable()
    cols = tuple(map(lambda x: x[0], cursor.description))
    data = []
    for row in cursor:
        d = {}
        i = 0
        for col in cols:
            d[col] = row[i]
            i += 1
        data.append(d)
    cursor.close()
    gc_enable()
    return data


@contextmanager
def _auto_repair_context(db_path):
    '''
        @name 自动修复sqlite数据库的上下文环境
        @author Zhj<2023-03-15>
        @param  db_path<string> sqlite数据库绝对路径
        @return void
    '''

    # os.chdir(_BASE_DIR)
    # sys.path.insert(0, _BASE_DIR)
    #
    # import core.include.public as public
    # path = os.getcwd()
    # monitor_backpath = path + '/backupDB/monitor_mgr_bak.db'
    # safety_backpath = path + '/backupDB/safety_bak.db'
    try:
        yield
    except BaseException as e:
        if str(db_path).startswith(':memory:'):
            raise e

        if str(e) in ['database disk image is malformed', 'file is not a database']:
            # TODO 修复数据库
            # public.ExecShell('\cp -rf %s %s' % (monitor_backpath,db_path))
            # public.ExecShell('\cp -rf %s %s' % (safety_backpath,db_path))
            pass

        raise e


class Where:
    '''
        @name where条件收集类
        @author Zhj<2022-07-16>
    '''
    __slots__ = ['__WHERE_STR', '__BIND_PARAMS']

    def __init__(self):
        self.__WHERE_STR = '1'
        self.__BIND_PARAMS = ()

    # def __del__(self):
    #     self.clear()

    def add(self, condition, bind_params=(), logic='AND'):
        '''
            @name 添加where条件
            @author Zhj<2022-07-16>
            @param  condition<string>       where条件
            @param  bind_params<tuple|list> 绑定参数
            @param  logic<string>           逻辑运算符 AND|OR
            @return self
        '''
        # 当检测condition为字段名且存在参数绑定时，自动添加"=?"
        if match_field_reg.match(condition) and len(_to_tuple(bind_params)) > 0:
            condition = '{} = ?'.format(_add_backtick_for_field(condition))

        where_str = ' {} ({})' if search_logic_opt_reg.search(condition) else ' {} {}'
        self.__WHERE_STR += where_str.format(logic.upper(), str(condition))
        self.__BIND_PARAMS += _to_tuple(bind_params)
        return self

    def add_where_in(self, field, vals, logic='AND', not_in=False):
        '''
            @name 添加where IN查询条件
            @param  field<string>       字段名
            @param  vals<list|tuple>    查询条件
            @param  logic<string>       逻辑运算符 AND|OR
            @param  not_in<bool>        是否为NOT IN
            @return self
        '''
        if isinstance(vals, str) or isinstance(vals, int) or isinstance(vals, float):
            vals = [vals]

        # 空列表
        # (IN)构建where 0
        # (NOT IN)构建where 1
        if len(vals) == 0:
            self.__WHERE_STR += ' {} {}'.format(logic.upper(), 1 if not_in else 0)
            return self

        # 元组转列表
        if isinstance(vals, tuple):
            vals = list(vals)

        # 去重
        vals = list(set(vals))

        # 构造where条件
        tmp = []
        where_params = ()

        # 绑定参数过多时使用字符串拼接
        is_to_more_vals = len(vals) > 300

        if is_to_more_vals:
            for val in vals:
                if is_number(val):
                    tmp.append(str(val))
                    continue

                tmp.append("'{}'".format(search_quote_reg.sub(r'\\\1', str(val))))
        else:
            for val in vals:
                tmp.append('?')
                where_params += (val,)

        self.__WHERE_STR += ' {} {} {} ({})'.format(
            logic.upper(),
            _add_backtick_for_field(field),
            'IN' if not not_in else 'NOT IN',
            ','.join(tmp)
        )
        self.__BIND_PARAMS += where_params

        return self

    def build(self):
        '''
            @name 获取where条件表达式和绑定参数
            @author Zhj<2022-07-16>
            @return (where条件<string>, 绑定参数<tuple>)
        '''
        where_str = match_where_str_begin_reg.sub('', self.__WHERE_STR)

        if len(where_str) == 0:
            return '', ()

        return ' WHERE {}'.format(where_str), self.__BIND_PARAMS

    def clear(self):
        '''
            @name 清空收集数据
            @author Zhj<2022-07-16>
            @return self
        '''
        self.__WHERE_STR = '1'
        self.__BIND_PARAMS = ()

        return self


class Limit:
    '''
        @name limit条件收集类
        @author Zhj<2022-07-16>
    '''
    __slots__ = ['__LIMIT', '__SKIP']

    def __init__(self):
        self.__LIMIT = None
        self.__SKIP = None

    # def __del__(self):
    #     self.clear()

    def set_limit(self, limit):
        '''
            @name 设置limit
            @author Zhj<2022-07-16>
            @param  limit<integer>  查询行数
            @return self
        '''
        self.__LIMIT = int(limit)
        return self

    def set_skip(self, skip):
        '''
            @name 设置skip
            @author Zhj<2022-07-16>
            @param  skip<integer> 跳过的行数
            @return self
        '''
        self.__SKIP = int(skip)
        return self

    def build(self):
        '''
            @name 获取limit条件表达式
            @author Zhj<2022-17-16>
            @return string
        '''
        if self.__LIMIT is None:
            return ''

        if self.__SKIP is None:
            return ' LIMIT {}'.format(str(self.__LIMIT))

        return ' LIMIT {},{}'.format(str(self.__SKIP), str(self.__LIMIT))

    def clear(self):
        '''
            @name 清空收集数据
            @author Zhj<2022-07-16>
            @return self
        '''
        self.__LIMIT = None
        self.__SKIP = None

        return self


class Order:
    '''
        @name order排序条件收集类
        @author ZHj<2022-07-16>
    '''
    __slots__ = ['__ORDERS', '__BIND_PARAMS']

    def __init__(self):
        self.__ORDERS = []
        self.__BIND_PARAMS = ()

    # def __del__(self):
    #     self.clear()

    def add_order(self, field, ordering='ASC', params=()):
        '''
            @name 添加排序条件
            @author Zhj<2022-07-16>
            @param  field<string>       字段名
            @param  ordering<string>    排序方式 ASC|DESC
            @param  params<list|tuple>  绑定参数
            @return self
        '''
        self.__ORDERS.append('{} {}'.format(
            _add_backtick_for_field(field),
            ordering.upper()
        ))
        self.__BIND_PARAMS += _to_tuple(params)
        return self

    def build(self):
        '''
            @name 获取排序条件表达式和绑定参数
            @author Zhj<2022-07-16>
            @return (排序条件表达式<string>, 绑定参数<tuple>)
        '''
        if len(self.__ORDERS) == 0:
            return '', ()

        return ' ORDER BY {}'.format(', '.join(self.__ORDERS)), self.__BIND_PARAMS

    def clear(self):
        '''
            @name 清空收集数据
            @author Zhj<2022-07-16>
            @return self
        '''
        self.__ORDERS = []
        self.__BIND_PARAMS = ()
        return self


class Field:
    '''
        @name 查询字段收集类
        @author Zhj<2022-07-16>
    '''
    __slots__ = ['__FIELDS']

    def __init__(self):
        self.__FIELDS = []

    # def __del__(self):
    #     self.clear()

    def set_fields(self, *fields):
        '''
            @name 设置查询字段
            @author Zhj<2022-07-17>
            @param  fields<tuple>   查询字段列表
            @return self
        '''
        self.__FIELDS = list(
            map(lambda field: _add_backtick_for_field(field),
                filter(lambda x: x is not None, fields)
                )
        )
        return self

    def add_fields(self, *fields):
        '''
            @name 添加查询字段
            @author Zhj<2022-07-16>
            @param  fields<tuple>   查询字段列表
            @return self
        '''
        self.__FIELDS += list(
            map(lambda field: _add_backtick_for_field(field),
                filter(lambda x: x is not None, fields)
                )
        )
        return self

    def build(self):
        '''
            @name 获取查询字段列表
            @author Zhj<2022-07-16>
            @return string
        '''
        if len(self.__FIELDS) == 0:
            return '*'

        return ', '.join(list(set(self.__FIELDS)))

    def is_empty(self):
        '''
            @name 检查是否为空
            @author Zhj<2022-07-20>
            @return bool
        '''
        return len(self.__FIELDS) == 0

    def clear(self):
        '''
            @name 清空收集数据
            @author Zhj<2022-07-16>
            @return self
        '''
        self.__FIELDS = []
        return self


class Group:
    '''
        @name 分组条件收集类
        @author Zhj<2022-07-16>
    '''
    __slots__ = ['__GROUPS', '__BIND_PARAMS']

    def __init__(self):
        self.__GROUPS = []
        self.__BIND_PARAMS = ()

    # def __del__(self):
    #     self.clear()

    def add_group(self, condition, params=()):
        '''
            @name 添加分组条件
            @author Zhj<2022-07-16>
            @param  condition<string>   分组条件
            @param  params<list|tuple>  绑定参数
            @return self
        '''
        self.__GROUPS.append(str(condition).strip())
        self.__BIND_PARAMS += _to_tuple(params)
        return self

    def build(self):
        '''
            @name 获取分组条件表达式和绑定参数
            @author Zhj<2022-07-16>
            @return (分组条件表达式<string>, 绑定参数<tuple>)
        '''
        if len(self.__GROUPS) == 0:
            return '', ()

        return ' GROUP BY {}'.format(', '.join(self.__GROUPS)), self.__BIND_PARAMS

    def clear(self):
        '''
            @name 清空收集数据
            @author Zhj<2022-07-16>
            @return self
        '''
        self.__GROUPS = []
        self.__BIND_PARAMS = ()
        return self


class Having:
    '''
        @name 分组筛选条件收集类
        @author Zhj<2022-07-16>
    '''
    __slots__ = ['__HAVINGS', '__BIND_PARAMS']

    def __init__(self):
        self.__HAVINGS = []
        self.__BIND_PARAMS = ()

    # def __del__(self):
    #     self.clear()

    def add_having(self, condition, params=()):
        '''
            @name 添加分组筛选条件
            @author Zhj<2022-07-16>
            @param  condition<string>   分组筛选条件
            @param  params<list|tuple>  绑定参数
            @return self
        '''
        self.__HAVINGS.append(str(condition).strip())
        self.__BIND_PARAMS += _to_tuple(params)
        return self

    def build(self):
        '''
            @name 获取分组筛选条件表达式和绑定参数
            @author Zhj<2022-07-16>
            @return (分组筛选条件表达式<string>, 绑定参数<tuple>)
        '''
        if len(self.__HAVINGS) == 0:
            return '', ()

        return ' HAVING {}'.format(', '.join(self.__HAVINGS)), self.__BIND_PARAMS

    def clear(self):
        '''
            @name 清空收集数据
            @author Zhj<2022-07-16>
            @return self
        '''
        self.__HAVINGS = []
        self.__BIND_PARAMS = ()
        return self


class Join:
    '''
        @name 关联条件收集类
        @author Zhj<2022-07-16>
    '''
    __slots__ = ['__JOINS']

    def __init__(self):
        self.__JOINS = []

    # def __del__(self):
    #     self.clear()

    def add_join(self, expression, condition, join_type='INNER', table_prefix=''):
        '''
            @name 添加关联条件
            @author Zhj<2022-07-16>
            @param  expression<string>      表达式
            @param  condition<string>       关联条件
            @param  join_type<string>       关联方式 INNER|LEFT|RIGHT
            @param  table_prefix<string>    表前缀
            @return self
        '''
        m = match_table_name_reg.match(expression)

        if m:
            expression = '{}{}'.format(
                _add_backtick_for_field('{}{}'.format(table_prefix, m.group(1).strip('`'))),
                '' if m.group(2) is None else ' AS {}'.format(_add_backtick_for_field(m.group(2)))
            )

        self.__JOINS.append('{} JOIN {} ON {}'.format(
            join_type.upper(),
            str(expression).strip(),
            str(condition).strip()
        ))
        return self

    def build(self):
        '''
            @name 获取关联条件表达式
            @author Zhj<2022-07-16>
            @return string
        '''
        if len(self.__JOINS) == 0:
            return ''

        return ' ' + ' '.join(self.__JOINS)

    def clear(self):
        '''
            @name 清空收集数据
            @author Zhj<2022-07-16>
            @return self
        '''
        self.__JOINS = []
        return self


class Update:
    '''
        @name Update条件
        @author Zhj<2022-07017>
    '''
    __slots__ = ['__UPDATES', '__BIND_PARAMS']

    def __init__(self):
        self.__UPDATES = []
        self.__BIND_PARAMS = ()

    # def __del__(self):
    #     self.clear()

    def add(self, field, value):
        '''
            @name 添加更新条件
            @author Zhj<2022-07-17>
            @param  field<string>           字段名
            @param  value<integer|string>   值
            @return self
        '''
        self.__UPDATES.append('{} = ?'.format(_add_backtick_for_field(field)))
        self.__BIND_PARAMS += _to_tuple(value)
        return self

    def increment(self, field, step=1):
        '''
            @name 自增
            @author Zhj<2022-07-17>
            @param  field<string>    字段名
            @param  step<integer>    值
            @return self
        '''
        self.__UPDATES.append('{field} = {field} + {step}'.format(
            field=_add_backtick_for_field(field),
            step=str(int(step))
        ))
        return self

    def decrement(self, field, step=1):
        '''
            @name 自减
            @author Zhj<2022-07-17>
            @param  field<string>    字段名
            @param  step<integer>    值
            @return self
        '''
        self.__UPDATES.append('{field} = {field} - {step}'.format(
            field=_add_backtick_for_field(field),
            step=str(int(step))
        ))
        return self

    def exp(self, field, exp):
        '''
            @name 添加原生表达式
            @author Zhj<2022-12-08>
            @param field<string>  字段名
            @param exp<string>    原生表达式
            @return:
        '''
        self.__UPDATES.append('{field} = {exp}'.format(
            field=_add_backtick_for_field(field),
            exp=str(exp)
        ))
        return self

    def build(self):
        '''
            @name 获取更新表达式和绑定参数
            @author Zhj<2022-07-17>
            @return self
        '''
        if self.is_empty():
            return '', ()

        return ', '.join(self.__UPDATES), self.__BIND_PARAMS

    def is_empty(self):
        '''
            @name 检查update条件是否为空
            @author Zhj<2022-07-17>
            @return bool
        '''
        return len(self.__UPDATES) == 0

    def clear(self):
        '''
            @name 清空收集数据
            @author Zhj<2022-07-17>
            @return self
        '''
        self.__UPDATES = []
        self.__BIND_PARAMS = ()
        return self


class AlterTable:
    __slots__ = ['__weakref__', '__QUERY', '__COLUMNS', '__RENAME_TABLE', '__ALTERS']

    def __init__(self, query):
        if not isinstance(query, SqliteEasy):
            raise RuntimeError('参数query必须是一个SqliteEasy类型')
        self.__QUERY = weakref.proxy(query)
        self.__COLUMNS = []
        self.__RENAME_TABLE = None
        self.__ALTERS = []

    # def __del__(self):
    #     self.clear()
    #     self.__COLUMNS = []
    #     self.__ALTERS = []
    #     self.__QUERY = None

    def rename_table(self, new_table_name):
        '''
            @name 更新表名
            @author Zhj<2022-09-21>
            @param  new_table_name<string> 新表名
            @return self
        '''
        self.__RENAME_TABLE = ' RENAME TO {}'.format(_add_backtick_for_field(new_table_name))
        return self

    def rename_column(self, col_name, new_col_name):
        '''
            @name 更新字段名
            @author Zhj<2022-09-21>
            @param  col_name<string>        当前字段名
            @param  new_col_name<string>    新字段名
            @return self
        '''
        if self.__column_exists(col_name):
            self.__ALTERS.append(' RENAME COLUMN {} TO {}'.format(_add_backtick_for_field(col_name), _add_backtick_for_field(new_col_name)))
            self.__COLUMNS.remove(col_name)
            self.__COLUMNS.append(new_col_name)
        return self

    def add_column(self, col_name, prop, force=False):
        '''
            @name 新增字段
            @author Zhj<2022-09-21>
            @param  col_name<string> 字段名
            @param  prop<string>     字段属性
            @param  force<?bool>     是否强制新增(删除旧的字段)[可选]
            @return self
        '''
        if force:
            self.drop_column(col_name)

        if not self.__column_exists(col_name):
            self.__ALTERS.append(' ADD COLUMN {} {}'.format(_add_backtick_for_field(col_name), prop))
            self.__COLUMNS.append(col_name)

        return self

    def drop_column(self, col_name):
        '''
            @name 删除字段
            @author Zhj<2022-09-21>
            @param  col_name<string> 字段名
            @return self
        '''
        if self.__column_exists(col_name):
            self.__ALTERS.append(' DROP COLUMN {}'.format(_add_backtick_for_field(col_name)))
            self.__COLUMNS.remove(col_name)
        return self

    def __column_exists(self, col_name):
        '''
            @name 检查字段是否已经存在
            @author Zhj<2022-09-21>
            @param  col_name<string> 字段名
            @return bool
        '''
        if len(self.__COLUMNS) == 0:
            self.__COLUMNS = self.__QUERY.get_columns()

        return col_name in self.__COLUMNS

    def build(self, table_name):
        '''
            @name 构建语句
            @author Zhj<2022-09-21>
            @param  table_name<string> 表名
            @return string|None
        '''
        if self.is_empty():
            return None

        ret = "begin;\n"
        ret += "\n".join(list(map(lambda x: 'ALTER TABLE {}{};'.format(table_name, x), self.__ALTERS)))
        ret += "ALTER TABLE {}{};\n".format(table_name,
                                            self.__RENAME_TABLE) if self.__RENAME_TABLE is not None else "\n"
        ret += 'commit;'

        return ret

    def is_empty(self):
        '''
            @name 检查更新条件是否为空
            @author Zhj<2022-09-21>
            @return bool
        '''
        return self.__RENAME_TABLE is None and len(self.__ALTERS) == 0

    def clear(self):
        '''
            @name 清空收集数据
            @author Zhj<2022-09-21>
            @return self
        '''
        self.__ALTERS = []
        return self


class DbConnection:
    '''
        @name Sqlite数据库连接类(相比Db类更加底层)
        @author Zhj<2022-12-13>
    '''
    __slots__ = ['__DB_NAME', '__DB_PATH', '__DB_LOCK_FILE', '__CONN', '__DEBUG_LOG']

    def __init__(self, db_name):
        '''
            @name 初始化函数
            @author Zhj<2022-12-14>
            @param db_name<string>  数据库名称(全路径 不包含.db)
            @return void
        '''
        self.__DB_NAME = db_name
        self.__DB_PATH = '{}.db'.format(db_name)

        if str(db_name).startswith(':memory:'):
           self.__DB_PATH = ':memory:'

        # 数据库连接对象
        self.__CONN: typing.Optional[sqlite3.Connection] = None

        # 数据库并发文件锁
        self.__DB_LOCK_FILE = None
        if self.__DB_PATH != ':memory:':
            self.__DB_LOCK_FILE = '/tmp/aap_locks/{}.lock'.format(self.__DB_PATH.replace('/', '____'))
            dirname = os.path.dirname(self.__DB_LOCK_FILE)
            if not os.path.exists(dirname):
                os.makedirs(dirname, 0o775)
            if not os.path.exists(self.__DB_LOCK_FILE):
                with open(self.__DB_LOCK_FILE, 'ab'):
                    pass

        # 连接数据库
        self.connect()

    # # 析构函数
    # def __del__(self):
    #     try:
    #         # 关闭数据库连接
    #         self.close()
    #     except BaseException as e:
    #         _log(e)

    # 数据库读操作并发锁
    @contextmanager
    def __rlock(self):
        if self.__DB_LOCK_FILE is not None:
            with open(self.__DB_LOCK_FILE, 'rb') as fp:
                fcntl.flock(fp.fileno(), fcntl.LOCK_SH)
                yield
        else:
            yield

    # 数据库写操作并发锁
    @contextmanager
    def __wlock(self):
        if self.__DB_LOCK_FILE is not None:
            with open(self.__DB_LOCK_FILE, 'rb+') as fp:
                fcntl.flock(fp.fileno(), fcntl.LOCK_EX)
                yield
        else:
            yield

    # 获取sqlite连接对象
    def conn_obj(self) -> sqlite3.Connection:
        '''
            @name 获取sqlite数据库连接对象<sqlite3.Connection>
            @author Zhj<2022-12-22>
            @return sqlite3.Connection|None
        '''
        return self.__CONN

    # 连接sqlite
    def connect(self):
        if isinstance(self.__CONN, sqlite3.Connection):
            return self.__CONN

        # 连接数据库(写)
        self.__CONN = sqlite3.connect(self.__DB_PATH, timeout=15, check_same_thread=False)
        self.__CONN.text_factory = str
        self.__CONN.isolation_level = 'IMMEDIATE'

    # 关闭连接
    def close(self):
        '''
            @name 关闭sqlite连接
        '''
        # 关闭sqlite数据库连接
        if isinstance(self.__CONN, sqlite3.Connection):
            try:
                self.__CONN.close()
            except BaseException as e:
                _log(e)

    # 开启事务(sqlite自动开启，无需手动调用)
    def start_transaction(self):
        '''
            @name 开启事务
            @return bool
        '''
        return True

    # 提交事务
    def commit(self) -> bool:
        '''
            @name 提交事务
            @return bool
        '''
        if isinstance(self.__CONN, sqlite3.Connection) and self.__CONN.in_transaction:
            self.__CONN.commit()
            return True

        return False

    # 回滚事务
    def rollback(self) -> bool:
        '''
            @name 回滚事务
            @return bool
        '''
        if isinstance(self.__CONN, sqlite3.Connection) and self.__CONN.in_transaction:
            self.__CONN.rollback()
            return True

        return False

    # 重试辅助函数
    def __sqlite_retry_help(self, fn, *args, **kwargs):
        retries = 25  # 尝试最大次数
        retry_interval = 20  # 每次尝试间隔时间/ms

        while retries > 0:
            try:
                return fn(*args, **kwargs)
            except (
            SystemError, KeyError, sqlite3.InterfaceError, sqlite3.InternalError, sqlite3.OperationalError) as e:
                # 数据库操作错误，不是锁协议错误，直接抛出异常
                if isinstance(e, sqlite3.OperationalError) and str(e) not in ['locking protocol',
                                                                              'database is locked']:
                    raise e

                # 最后一次尝试失败后直接raise异常
                if retries == 1:
                    raise e

                # 打印异常信息
                _log(e)
                e = None
                del (e,)

                time.sleep(retry_interval * 0.001)
            finally:
                retries -= 1

    # 查询
    def query(self, sql, params=(), take_first=False):
        '''
            @name 执行查询SQL
            @param sql<string>          sql语句
            @param params<list|tuple>   绑定参数[可选]
            @param take_first<bool>     是否只获取一行数据[可选 默认获取所有行]
            @return list|dict|None
        '''
        # 读锁
        with self.__rlock():
            s_time = time.time()
            e_time = s_time

            try:
                ret = self.__sqlite_retry_help(self.__query_help, sql, params, take_first)
                e_time = time.time()
                return ret
            finally:
                if e_time - s_time > 1:
                    _log2('{}s {}'.format(round(e_time - s_time, 2),
                                          reduce(lambda x, y: search_question_reg.sub(
                                              str(y) if is_number(y) else "'%s'" % y, x, 1), params, sql)),
                          'sqlite_slow.log')

    # 查询(辅助函数)
    def __query_help(self, sql, params=(), take_first=False):
        with _auto_repair_context(self.__DB_PATH):
            try:
                # 执行SQL
                # 获取游标对象
                cur = self.__CONN.execute(sql, _to_tuple(params))
            except:
                # 打印sql语句与绑定参数
                _log('{}\nbindings: {}\ndb: {}'.format(sql, params, self.__DB_NAME))

                cur = None
                del (cur,)

                # 抛出异常
                raise

            try:
                s_time = time.time()

                ret = _format_cursor(cur)

                e_time = time.time()

                if e_time - s_time > 1:
                    _log2('{}s format_cursor'.format(round(e_time - s_time, 2)), 'sqlite_slow.log')

                del (cur,)

                # 只获取首行数据
                if take_first:
                    if len(ret) == 0:
                        return None
                    return ret[0]

                return list(ret)
            except:
                # 打印sql语句与绑定参数
                _log('{}\nbindings: {}\ndb: {}'.format(sql, params, self.__DB_NAME))

                cur = None
                del (cur,)

                raise

    # 执行单条SQL语句
    def execute(self, sql, params=(), get_rowid=False):
        '''
            @name 执行SQL
            @param sql<string>          sql语句
            @param params<tuple|list>   绑定参数
            @param get_rowid<bool>      获取插入ID
            @return int 影响行数或插入ID
        '''
        # 写锁
        with self.__wlock():
            return self.__sqlite_retry_help(self.__execute_help, sql, params, get_rowid)

    # 执行单条SQL语句(辅助函数)
    def __execute_help(self, sql, params=(), get_rowid=False):
        with _auto_repair_context(self.__DB_PATH):
            try:
                # 获取游标对象
                cur = self.__CONN.cursor()

                # 执行SQL
                cur.execute(sql, _to_tuple(params))
            except:
                # 打印sql语句与绑定参数
                _log('{}\nbindings: {}\ndb: {}'.format(sql, params, self.__DB_NAME))

                cur = None
                del (cur,)

                # 抛出异常
                raise

            try:
                # 获取新插入数据ID
                if get_rowid:
                    return cur.lastrowid

                # 返回受影响的行数
                return cur.rowcount
            finally:
                # 主动关闭Cursor
                cur.close()

                cur = None
                del (cur,)

    # 执行批量写入
    def execute_many(self, sql, params=()):
        '''
            @name 批量插入
            @param sql<string>          sql语句
            @param params<tuple|list>   绑定参数
            @return int 影响行数
        '''
        # 写锁
        with self.__wlock():
            return self.__sqlite_retry_help(self.__execute_many_help, sql, params)

    # 执行批量写入(辅助函数)
    def __execute_many_help(self, sql, params=()):
        with _auto_repair_context(self.__DB_PATH):
            try:
                # 获取游标对象
                cur = self.__CONN.cursor()

                # 执行SQL
                cur.executemany(sql, params)
            except:
                # 打印sql语句与绑定参数
                _log('{}\nbindings: {}\ndb: {}'.format(sql, params, self.__DB_NAME))

                cur = None
                del (cur,)

                # 抛出异常
                raise

            rowcount = cur.rowcount

            # 主动关闭Cursor
            cur.close()

            cur = None
            del (cur,)

            return rowcount

    # 执行多条SQL语句
    def execute_script(self, sql):
        '''
            @name 批量执行SQL
            @param sql<string> sql语句集合
            @return bool
        '''
        # 写锁
        with self.__wlock():
            return self.__sqlite_retry_help(self.__execute_script_help, sql)

    # 执行多条SQL语句(辅助函数)
    def __execute_script_help(self, sql):
        with _auto_repair_context(self.__DB_PATH):
            try:
                # 获取游标对象
                cur = self.__CONN.cursor()

                # 执行SQL
                cur.executescript(sql)
            except:
                # 打印sql语句与绑定参数
                _log('{}\ndb: {}'.format(sql, self.__DB_NAME))

                cur = None
                del (cur,)

                # 抛出异常
                raise

            # 主动关闭Cursor
            cur.close()

            cur = None
            del (cur,)

            return True

    # 执行vacuum整理数据库空间
    def vacuum(self):
        '''
            @name 执行vaccum整理数据库空间
            @author Zhj<2022-12-22>
            @return int
        '''
        # 写锁
        with self.__wlock():
            return self.execute('vacuum')

    # 备份数据库
    def backup(self, dest_conn) -> bool:
        '''
            @name 将当前数据库备份到目标数据库
            @author Zhj<2022-12-22>
            @param dest_conn<DbConnection> 目标数据库连接对象
            @return bool
        '''
        if dest_conn.conn_obj() is None:
            raise PanelError('dest_conn not connect to sqlite.')

        # 写锁
        with self.__wlock():
            with _auto_repair_context(self.__DB_PATH):
                # 开始备份(全量备份)
                self.__CONN.backup(dest_conn.conn_obj())

                return True

    # 导出数据库
    def dump(self, dest_file: str, row_check_func: typing.Optional[callable] = None) -> bool:
        """
            @name 导出数据库
            @author Zhj<2024-08-08>
            @param dest_file<str>               目标文件
            @param row_check_func<?callable>    语句行检查函数 row_check_func(row: str) -> bool
            @return bool
        """
        # 写锁
        with self.__wlock():
            with open(dest_file, 'w') as fp:
                for row in self.__CONN.iterdump():
                    # 当传入了语句行检查函数时，执行检查函数
                    if row_check_func is not None and not row_check_func(row):
                        continue

                    # 导出数据行
                    fp.write(row + '\n')

        return True


class Db:
    '''
        @name Sqlite数据库连接类
        @author Zhj<2022-07-18>
    '''
    __slots__ = ['__DB_NAME', '__DB_CONN', '__AUTO_COMMIT', '__AUTO_VACUUM', '__NEED_VACUUM', '__DEBUG_LOG', '__QUERIES']

    __DB_ROOT_DIR = '{}/data/db/'.format(_BASE_DIR)

    def __init__(self, db_name):
        '''
            @name 初始化函数
            @author Zhj<2022-12-14>
            @param db_name<string>  数据库名称
            @param brandnew<bool>   是否开启一个全新连接
            @return void
        '''
        if str(db_name).startswith(':memory:'):
            self.__DB_NAME = db_name  # 内存数据库
        else:
            self.__DB_NAME = os.path.join(self.__DB_ROOT_DIR, re.sub(r'\.db$', '', db_name))  # 数据库名称(全路径 不带.db)
        self.__DB_CONN: typing.Optional[DbConnection] = None  # 数据库连接对象
        self.__AUTO_COMMIT = True  # 是否自动提交事务(默认自动提交)
        self.__AUTO_VACUUM = False  # 是否自动释放空间
        self.__NEED_VACUUM = False  # 事务提交后是否需要释放空间
        self.__DEBUG_LOG = False  # 是否开启调试日志
        self.__QUERIES = []  # 查询构造器数量

        self.__connect()

    def __del__(self):
        self.close()
        del (self.__DB_CONN,)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_trackback):
        self.close()

    def __connect(self):
        '''
            @name   连接Sqlite数据库
            @author Zhj<2022-07-16>
            @return self
        '''
        self.__DB_CONN = DbConnection(self.__DB_NAME)
        return self

    def close(self):
        '''
            @name 将数据库连接返回连接池
            @author Zhj<2022-07-16>
            @return self
        '''
        try:
            # 释放数据库连接
            if self.__DB_CONN is None:
                return
            self.__DB_CONN.close()
            self.__DB_CONN = None
        except BaseException as e:
            _log(e)

    def client(self):
        '''
            @name 获取数据库连接对象
            @return SqliteClient
        '''
        return self.__DB_CONN

    def db_name(self):
        '''
            @name 获取数据库名称
            @author Zhj<2022-09-07>
            @return string
        '''
        return self.__DB_NAME

    def auto_vacuum(self, auto_vacuum=True):
        '''
            @name 设置是否自动释放空间
            @author Zhj<2022-09-27>
            @param  auto_vacuum<?bool> 是否自动释放空间
            @return self
        '''
        self.__AUTO_VACUUM = auto_vacuum
        return self

    def need_vacuum(self, need_vacuum=True):
        '''
            @name 设置是否需要清理空间
            @author Zhj<2022-09-02>
            @param need_vacuum<?bool> 是否需要清理空间
            @return self
        '''
        self.__NEED_VACUUM = need_vacuum
        return self

    def autocommit(self, autocommit=True):
        '''
            @name 设置自动提交事务状态
            @author Zhj<2022-07-17>
            @param  autocommit<bool>    是否自动提交事务
            @return self
        '''
        self.__AUTO_COMMIT = autocommit
        return self

    def is_autocommit(self):
        '''
            @name 是否自动提交事务
            @return bool
        '''
        return self.__AUTO_COMMIT

    def is_autovacuum(self):
        '''
            @name 是否自动释放空间
            @return bool
        '''
        return self.__AUTO_VACUUM

    def commit(self):
        '''
            @name 提交事务
            @author Zhj<2022-07-17>
            @return bool
        '''
        if self.__DB_CONN is None:
            return False

        # 记录commit语句执行开始时间
        s_time = time.time()

        # 提交事务
        ret = self.__DB_CONN.commit()

        # 写日志
        if self.is_debug():
            self.debug_log('commit', self.db_name(), time.time() - s_time)

        # 开启了自动释放空间时
        # 释放空间
        if self.__NEED_VACUUM and self.is_autovacuum():
            self.__NEED_VACUUM = False
            self.vacuum()

        return ret

    def rollback(self):
        '''
            @name 回滚事务
            @author Zhj<2022-07-17>
            @return bool
        '''
        if self.__DB_CONN is None:
            return False

        self.__NEED_VACUUM = False

        # 记录rollback语句执行开始时间
        s_time = time.time()

        ret = self.__DB_CONN.rollback()

        # 写日志
        if self.is_debug():
            self.debug_log('rollback', self.db_name(), time.time() - s_time)

        return ret

    def query(self):
        '''
            @name 获取查询构造器对象
            @author Zhj<2022-07-18>
            @return SqliteEasy
        '''
        self.__QUERIES.append(None)
        return SqliteEasy(self)

    def query_done(self):
        '''
            @name 标记查询构造器已关闭
            @author Zhj<2023-02-08>
            @return None
        '''
        del (self.__QUERIES[-1:],)

    def queries(self):
        '''
            @name 查看当前查询构造器数量
            @author Zhj<2023-02-08>
            @return int
        '''
        return len(self.__QUERIES)

    def vacuum(self):
        '''
            @name 释放空间
            @author Zhj<2022-12-22>
            @return int
        '''
        # 记录vacuum语句执行开始时间
        s_time = time.time()

        # 执行vacuum
        ret = self.__DB_CONN.vacuum()

        # 写日志
        if self.is_debug():
            self.debug_log('vacuum', self.db_name(), time.time() - s_time)

        return ret

    def backup(self, dest_db):
        '''
            @name 备份数据库(>=py3.7)
            @author Zhj<2022-12-22>
            @param  dest_db<Db>     目标数据库连接对象
            @return bool
        '''
        if not isinstance(dest_db, Db):
            raise PanelError('dest_db must a Db object.')

        # 记录执行备份开始时间
        s_time = time.time()

        # 开始备份
        ret = self.__DB_CONN.backup(dest_db.client())

        # 写日志
        if self.is_debug():
            self.debug_log('backup to {}'.format(dest_db.db_name()), self.db_name(), time.time() - s_time)

        return ret

    def dump(self, dest_file: str, row_check_func: typing.Optional[callable] = None) -> bool:
        '''
            @name 导出数据库(>=py3.7)
            @author Zhj<2024-08-08>
            @param dest_file<str>               目标文件
            @param row_check_func<?callable>    语句行检查函数 row_check_func(row: str) -> bool
            @return bool
        '''
        # 记录执行导出开始时间
        s_time = time.time()

        # 开始导出
        ret = self.__DB_CONN.dump(dest_file, row_check_func)

        # 写日志
        if self.is_debug():
            self.debug_log('dump to {}'.format(dest_file), self.db_name(), time.time() - s_time)

        return ret

    def debug(self, debug_state=True):
        '''
            @name 设置调试
            @param debug_state<bool> 调试状态
            @return self
        '''
        self.__DEBUG_LOG = debug_state
        return self

    def is_debug(self):
        '''
            @name 检查当前是否开启了调试日志
            @return bool
        '''
        return self.__DEBUG_LOG

    def debug_log(self, content, db_name, cost_time):
        '''
            @name 写查询日志
            @author Zhj<2022-09-27>
            @param  content<string>     sql语句
            @param  db_name<string>     数据库名称
            @param  cost_time<float>    执行耗时/s
            @return void
        '''
        # 获取当前日期时间
        cur_datetime = time.strftime('%Y-%m-%d %X')

        # sql查询日志目录
        log_dir = '{}/logs/sql_log/{}'.format(_BASE_DIR, time.strftime('%Y%m'))

        # 目录不存在时创建
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, 0o600)

        with open('{}/{}.log'.format(log_dir, cur_datetime[8:10]), 'a') as fp:
            fp.write('[{}]{} {}ms {}\n'.format(cur_datetime, db_name, round(cost_time * 1000, 2), content))

    def synchronous_off(self):
        '''
            @name 关闭同步
            @author Zhj<2023-02-17>
            @return self
        '''
        self.__DB_CONN.execute_script('PRAGMA synchronous=0;')
        return self

    def synchronous_off_wal(self):
        '''
            @name 设置WAL日志模式并关闭同步
            @author Zhj<2023-02-17>
            @return self
        '''
        self.__DB_CONN.execute_script('PRAGMA journal_mode=wal;\nPRAGMA synchronous=0;\nPRAGMA temp_store=memory;\nPRAGMA mmap_size=30000000000;')
        return self

    def integrity_check(self):
        '''
            @name 检查数据库是否完整
            @author Zhj<2023-03-15>
            @return bool
        '''
        try:
            ret = self.__DB_CONN.query('PRAGMA integrity_check', take_first=True)
            return ret['integrity_check'] == 'ok'
        except:
            return False


class SqliteEasy:
    '''
        @name Sqlite查询类
        @author Zhj<2022-07-15>
    '''
    __slots__ = ['__weakref__', '__DB', '__DB_TABLE', '__FETCH_SQL', '__EXPLAIN', '__PK', '__OPT_PREFIX', '__OPT_ALIAS',
                 '__OPT_WHERE', '__OPT_LIMIT', '__OPT_ORDER', '__OPT_FIELD', '__OPT_GROUP', '__OPT_HAVING',
                 '__OPT_JOIN', '__OPT_UPDATE', '__OPT_ALTER_TABLE', '__FROM_SUB_QUERY', '__CONFLICT_OPTIONS']

    def __init__(self, db: typing.Optional[Db] = None):
        self.__DB = None  # 数据库对象
        self.__DB_TABLE = None  # 表名(包含前缀)
        self.__FETCH_SQL = False  # 是否输出sql语句
        self.__EXPLAIN = False  # 分析sql语句
        self.__PK = None  # 主键字段名
        self.__OPT_PREFIX = 'bt_'  # 表前缀
        self.__OPT_ALIAS = None  # 表别名
        self.__OPT_WHERE = Where()  # where条件
        self.__OPT_LIMIT = Limit()  # limit条件
        self.__OPT_ORDER = Order()  # order条件
        self.__OPT_FIELD = Field()  # field条件
        self.__OPT_GROUP = Group()  # group条件
        self.__OPT_HAVING = Having()  # having条件
        self.__OPT_JOIN = Join()  # 联表条件
        self.__OPT_UPDATE = Update()  # update条件
        self.__OPT_ALTER_TABLE = AlterTable(self)  # 更新表结构条件
        self.__FROM_SUB_QUERY = False  # 是否通过子查询
        self.__CONFLICT_OPTIONS = (
            'ROLLBACK',     # 回滚
            'ABORT',        # 撤销
            'FAIL',         # 抛出失败异常
            'IGNORE',       # 忽略
            'REPLACE',      # 覆盖
        )  # 发生约束冲突时，额外的处理选项

        if db is not None:
            self.__DB = db

    def __del__(self):
        self.close()

        self.__OPT_WHERE = None
        self.__OPT_LIMIT = None
        self.__OPT_ORDER = None
        self.__OPT_FIELD = None
        self.__OPT_GROUP = None
        self.__OPT_HAVING = None
        self.__OPT_JOIN = None
        self.__OPT_UPDATE = None
        self.__OPT_ALTER_TABLE = None

        del (self.__OPT_WHERE,
             self.__OPT_LIMIT,
             self.__OPT_ORDER,
             self.__OPT_FIELD,
             self.__OPT_GROUP,
             self.__OPT_HAVING,
             self.__OPT_JOIN,
             self.__OPT_UPDATE,
             self.__OPT_ALTER_TABLE,)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()

    def set_db(self, db):
        '''
            @name 设置数据库对象
            @author Zhj<2022-07-18>
            @param  db<Db>  数据库对象
            @return self
        '''
        if not isinstance(db, Db):
            raise PanelError('db must a instance of core.include.sqlite_server.Db')

        self.__DB = db
        return self

    def get_db(self):
        '''
            @name 获取数据库对象
            @author Zhj<2022-07-18>
            @return Db|None
        '''
        return self.__DB

    def set_pk(self, pk):
        '''
            @name 设置主键字段名
            @author Zhj<2022-07-19>
            @param  pk<string> 主键字段名
            @return self
        '''
        self.__PK = pk
        return self

    def set_where_obj(self, where_obj):
        '''
            @name 设置Where对象
            @author Zhj<2022-07-19>
            @param  where_obj<Where> Where对象
            @return self
        '''
        if not isinstance(where_obj, Where):
            raise PanelError('where_obj must a instance of core.include.sqlite_server.Where')

        self.__OPT_WHERE = where_obj
        return self

    def set_limit_obj(self, limit_obj):
        '''
            @name 设置Limit对象
            @author Zhj<2022-07-19>
            @param  limit_obj<Limit> Limit对象
            @return self
        '''
        if not isinstance(limit_obj, Limit):
            raise PanelError('limit_obj must a instance of core.include.sqlite_server.Limit')

        self.__OPT_LIMIT = limit_obj
        return self

    def set_order_obj(self, order_obj):
        '''
            @name 设置Order对象
            @author Zhj<2022-07-19>
            @param  order_obj<Order> Order对象
            @return self
        '''
        if not isinstance(order_obj, Order):
            raise PanelError('order_obj must a instance of core.include.sqlite_server.Order')

        self.__OPT_ORDER = order_obj
        return self

    def set_field_obj(self, field_obj):
        '''
            @name 设置Field对象
            @author Zhj<2022-07-19>
            @param  field_obj<Field> Field对象
            @return self
        '''
        if not isinstance(field_obj, Field):
            raise PanelError('field_obj must a instance of core.include.sqlite_server.Field')

        self.__OPT_FIELD = field_obj
        return self

    def set_group_obj(self, group_obj):
        '''
            @name 设置Field对象
            @author Zhj<2022-07-19>
            @param  field_obj<Field> Field对象
            @return self
        '''
        if not isinstance(group_obj, Group):
            raise PanelError('group_obj must a instance of core.include.sqlite_server.Group')

        self.__OPT_GROUP = group_obj
        return self

    def set_having_obj(self, having_obj):
        '''
            @name 设置Having对象
            @author Zhj<2022-07-19>
            @param  having_obj<Having> Having对象
            @return self
        '''
        if not isinstance(having_obj, Having):
            raise PanelError('having_obj must a instance of core.include.sqlite_server.Having')

        self.__OPT_HAVING = having_obj
        return self

    def set_join_obj(self, join_obj):
        '''
            @name 设置Field对象
            @author Zhj<2022-07-19>
            @param  join_obj<Join> Join对象
            @return self
        '''
        if not isinstance(join_obj, Join):
            raise PanelError('join_obj must a instance of core.include.sqlite_server.Join')

        self.__OPT_JOIN = join_obj
        return self

    def set_update_obj(self, update_obj):
        '''
            @name 设置Field对象
            @author Zhj<2022-07-19>
            @param  update_obj<Update> Update对象
            @return self
        '''
        if not isinstance(update_obj, Update):
            raise PanelError('update_obj must a instance of core.include.sqlite_server.Update')

        self.__OPT_UPDATE = update_obj
        return self

    def close(self):
        '''
            @name 关闭游标并将数据库连接返回连接池
            @author Zhj<2022-07-16>
            @return self
        '''
        try:
            self.__DB.query_done()
            self.__DB = None

            # 清理查询条件
            self.__clear()
        except:
            pass

    def autocommit(self, autocommit=True):
        '''
            @name 设置自动提交事务状态
            @author Zhj<2022-07-17>
            @param  autocommit<bool>    是否自动提交事务
            @return self
        '''
        if self.__DB is not None:
            self.__DB.autocommit(autocommit)

        return self

    def commit(self):
        '''
            @name 提交事务
            @author Zhj<2022-07-17>
            @return bool
        '''
        if self.__DB is None:
            return False

        # 提交事务
        return self.__DB.commit()

    def rollback(self):
        '''
            @name 回滚事务
            @author Zhj<2022-07-17>
            @return bool
        '''
        if self.__DB is None:
            return False

        # 回滚事务
        return self.__DB.rollback()

    def vacuum(self):
        """
            @name 释放空间
            @author Zhj<2023-11-13>
            @return bool
        """
        if self.__DB is None:
            return False

        return self.__DB.vacuum()

    def fetch_sql(self, fetch_sql=True):
        '''
            @name 设置是否输入sql原生语句
            @author Zhj<2022-07-18>
            @param  fetch_sql<bool> 是否输入sql原生语句
            @return self
        '''
        self.__FETCH_SQL = fetch_sql
        return self

    def explain(self, explain=True):
        '''
            @name 设置EXPLAIN
            @author Zhj<2022-07-20>
            @param  explain<bool>   是否开启EXPLAIN
            @return self
        '''
        self.__EXPLAIN = explain
        return self

    def prefix(self, prefix):
        '''
            @name 设置表前缀
            @author Zhj<2022-07-16>
            @param  prefix<string> 表前缀
            @return self
        '''
        self.__OPT_PREFIX = prefix
        return self

    def name(self, table_name):
        '''
            @name 设置表名(不包含前缀)
            @author Zhj<2022-07-16>
            @param  table_name<string>  表名(不包含前缀)
            @return self
        '''
        return self.table(table_name, False)

    def table(self, table_name, is_fullname=True):
        '''
            @name 设置表名(包含前缀)
            @param table_name<string>   表名
            @param is_fullname<bool>    是否完整表名(不包含前缀)
            @return self
        '''
        m = match_table_name_reg.match(table_name)

        if m is None or m.group(1) is None:
            raise PanelError('Invalid table name：{}'.format(table_name))

        self.__DB_TABLE = m.group(1).strip('`')

        # 添加前缀
        if not is_fullname and self.__OPT_PREFIX is not None:
            self.__DB_TABLE = self.__OPT_PREFIX + self.__DB_TABLE

        if m.group(2) is not None:
            self.__OPT_ALIAS = m.group(2).strip('`')

        # 重置主键字段名
        self.__PK = None

        return self

    # 使用子查询
    def from_sub_query(self, sub_query):
        # 当传入查询构造器对象时，将其转为SQL语句
        if isinstance(sub_query, SqliteEasy):
            sub_query = sub_query.build_sql(True)

        m = search_subquery_reg.search(str(sub_query))

        if m is None or m.group(1) is None:
            raise PanelError('Invalid sub-query：{}'.format(sub_query))

        self.__DB_TABLE = m.group(1)

        if m.group(2) is not None:
            self.__OPT_ALIAS = m.group(2).strip('`')

        # 重置主键字段名
        self.__PK = None

        self.__FROM_SUB_QUERY = True

        return self

    def alias(self, alias):
        '''
            @name 设置表别名
            @author Zhj<2022-07-16>
            @param  alias<string> 表别名
            @return self
        '''
        self.__OPT_ALIAS = alias
        return self

    def field(self, *fields):
        '''
            @name 添加查询字段
            @author Zhj<2022-07-15>
            @param  fields<tuple>   查询字段列表
            @return self
        '''
        self.__OPT_FIELD.add_fields(*fields)
        return self

    def join(self, exp, condition, join_type='INNER', add_table_prefix=True):
        '''
            @name 添加关联条件
            @author Zhj<2022-07-17>
            @param  exp<string>             表达式
            @param  condition<string>       关联条件
            @param  join_type<string>       关联方式 INNER|LEFT|RIGHT
            @param  add_table_prefix<bool>  是否添加表前缀[可选 默认自动添加]
            @return self
        '''
        table_prefix = ''

        if add_table_prefix and self.__OPT_PREFIX is not None:
            table_prefix = self.__OPT_PREFIX

        self.__OPT_JOIN.add_join(exp, condition, join_type, table_prefix)
        return self

    def inner_join(self, exp, condition, add_table_prefix=True):
        '''
            @name 添加内连接关联条件
            @param  exp<string>          表达式
            @param  condition<string>    关联条件
            @param  add_table_prefix<bool>  是否添加表前缀[可选 默认自动添加]
            @return self
        '''
        return self.join(exp, condition, 'INNER', add_table_prefix)

    def left_join(self, exp, condition, add_table_prefix=True):
        '''
            @name 添加左连接关联条件
            @author Zhj<2022-07-17>
            @param  exp<string>          表达式
            @param  condition<string>    关联条件
            @param  add_table_prefix<bool>  是否添加表前缀[可选 默认自动添加]
            @return self
        '''
        return self.join(exp, condition, 'LEFT', add_table_prefix)

    def right_join(self, exp, condition, add_table_prefix=True):
        '''
            @name 添加右连接关联条件
            @author Zhj<2022-07-17>
            @param  exp<string>          表达式
            @param  condition<string>    关联条件
            @param  add_table_prefix<bool>  是否添加表前缀[可选 默认自动添加]
            @return self
        '''
        return self.join(exp, condition, 'RIGHT', add_table_prefix)

    def where(self, condition, params=()):
        '''
            @name 添加where条件 AND
            @author Zhj<2022-07-16>
            @param  condition<string>   where条件
            @param  params<list|tuple>  绑定参数
            @return self
        '''
        self.__OPT_WHERE.add(condition, params)
        return self

    def where_or(self, condition, params=()):
        '''
            @name 添加where条件 OR
            @author Zhj<2022-07-16>
            @param  condition<string>   where条件
            @param  params<list|tuple>  绑定参数
            @return self
        '''
        self.__OPT_WHERE.add(condition, params, 'OR')
        return self

    def where_in(self, field, vals, logic='AND'):
        '''
            @name 添加where条件 IN
            @author Zhj<2022-07-16>
            @param  field<string>       字段名
            @param  vals<list|tuple>    查询参数列表
            @param  logic<string>       逻辑运算符 AND|OR
            @return self
        '''
        self.__OPT_WHERE.add_where_in(field, vals, logic)
        return self

    def where_not_in(self, field, vals, logic='AND'):
        '''
            @name 添加where条件 IN
            @author Zhj<2022-07-16>
            @param  field<string>       字段名
            @param  vals<list|tuple>    查询参数列表
            @param  logic<string>       逻辑运算符 AND|OR
            @return self
        '''
        self.__OPT_WHERE.add_where_in(field, vals, logic, True)
        return self

    # TODO 嵌套where
    @contextmanager
    def where_nest(self):
        yield self

    def group(self, condition, params=()):
        '''
            @name 添加分组条件
            @author Zhj<2022-07-17>
            @param  condition<string>   分组条件
            @param  params<list|tuple>  绑定参数
            @return self
        '''
        self.__OPT_GROUP.add_group(condition, params)
        return self

    def having(self, condition, params=()):
        '''
            @name 添加分组筛选条件
            @author Zhj<2022-07-17>
            @param  condition<string>   分组筛选条件
            @param  params<list|tuple>  绑定参数
            @return self
        '''
        self.__OPT_HAVING.add_having(condition, params)
        return self

    def order(self, field, ordering='ASC', params=()):
        '''
            @name 添加排序条件
            @author Zhj<2022-07-17>
            @param  field<string>       字段名
            @param  ordering<string>    排序方式 ASC|DESC
            @param  params<list|tuple>  绑定参数
            @return self
        '''
        self.__OPT_ORDER.add_order(field, ordering, params)
        return self

    def limit(self, limit, skip=None):
        '''
            @name 设置返回行数
            @author Zhj<2022-07-16>
            @param  limit<integer>  返回的行数
            @param  skip<?integer>  跳过的行数
            @return self
        '''
        self.__OPT_LIMIT.set_limit(limit)

        if skip is not None:
            self.__OPT_LIMIT.set_skip(skip)

        return self

    def skip(self, skip):
        '''
            @name 设置跳过的行数
            @author Zhj<2022-07-16>
            @param  skip<integer> 跳过的行数
            @return self
        '''
        self.__OPT_LIMIT.set_skip(skip)
        return self

    def query(self, raw_sql, params=(), take_first=False, clear_conditions=True):
        '''
            @name 查询
            @author Zhj<2022-07-17>
            @param  raw_sql<string>         sql语句
            @param  params<list|tuple>      绑定参数[可选]
            @param  take_first<bool>        是否只获取一行数据[可选 默认获取所有行]
            @param  clear_conditions<?bool> 是否清空查询条件[可选 默认清空]
            @return list|dict|None
        '''
        if self.__DB is None:
            return None

        # 记录语句执行开始时间
        s_time = time.time()

        # 执行sql语句
        ret = self.__DB.client().query(raw_sql, _to_tuple(params), take_first)

        # 写日志
        if self.__DB.is_debug():
            self.__DB.debug_log(self.__to_raw_sql(raw_sql, _to_tuple(params)), self.__DB.db_name(),
                                time.time() - s_time)

        # 自动提交事务
        # if self.__is_autocommit():
        #     self.commit()

        # 清空查询条件
        if clear_conditions:
            self.__clear()

        return ret

    def execute(self, raw_sql, params=(), get_rowid=False, clear_conditions=True):
        '''
            @name 执行一条sql语句并返回影响的行数
            @author Zhj<2022-07-18>
            @param  raw_sql<string>         sql语句
            @param  params<list|tuple>      绑定参数[可选]
            @param  get_rowid<bool>         获取插入ID[可选 默认返回影响的行数]
            @param  clear_conditions<?bool> 是否清空查询条件[可选 默认清空]
            @return integer
        '''
        if self.__DB is None:
            return 0

        # 记录语句执行开始时间
        s_time = time.time()

        # 执行sql语句
        ret = self.__DB.client().execute(raw_sql, _to_tuple(params), get_rowid)

        # 写日志
        if self.__DB.is_debug():
            self.__DB.debug_log(self.__to_raw_sql(raw_sql, _to_tuple(params)), self.__DB.db_name(),
                                time.time() - s_time)

        # 自动提交事务
        if self.__is_autocommit():
            self.commit()

        # 清空查询条件
        if clear_conditions:
            self.__clear()

        return ret

    def execute_script(self, sql_script, clear_conditions=True):
        '''
            @name 执行多条sql语句(注意：执行这个方法会自动提交之前的事务，本次执行不会加入事务，事务请编写在sql脚本中)
            @author Zhj<2022-07-18>
            @param  sql_script<string>      sql语句
            @param  clear_conditions<?bool> 是否清空查询条件[可选 默认清空]
            @return bool
        '''
        if self.__DB is None:
            return False

        # 记录语句执行开始时间
        s_time = time.time()

        # 执行sql语句
        self.__DB.client().execute_script(sql_script)

        # 写日志
        if self.__DB.is_debug():
            self.__DB.debug_log(sql_script, self.__DB.db_name(), time.time() - s_time)

        # 清空查询条件
        if clear_conditions:
            self.__clear()

        return True

    def insert(self, data, option=None, get_rowid=True):
        '''
            @name 插入一条数据
            @author Zhj<2022-07-17>
            @param  data<dict|list>     插入数据
            @param  option<?string>     额外选项[可选]
            @param  get_rowid<bool>     获取插入ID[可选 默认返回影响的行数]
            @return integer|string
        '''
        if self.__DB_TABLE is None:
            raise PanelError('Insert failed: table name not provide.')

        # 传入dict类型之外的情况
        if not isinstance(data, dict):
            # list类型：尝试insert_all
            if isinstance(data, list):
                return self.insert_all(data, option=option)

            # 其它类型：抛出异常提示
            raise PanelError('Insert failed: parameter "data" type must be dict.')

        # 检查冲突选项是否正确
        if option is not None and str(option).upper() not in self.__CONFLICT_OPTIONS:
            raise PanelError('option must be one of: {}'.format(', '.join(self.__CONFLICT_OPTIONS)))

        placeholders = []
        ks = data.keys()
        params = ()

        for k in ks:
            placeholders.append('?')
            params += (data[k],)

        raw_sql = 'INSERT{} INTO {} ({}) VALUES ({})'.format(
            ' OR {}'.format(str(option).upper()) if option is not None else '',
            _add_backtick_for_field(self.__DB_TABLE),
            ', '.join(list(map(lambda x: _add_backtick_for_field(x), ks))),
            ','.join(placeholders)
        )

        # 输出sql原生语句
        if self.__FETCH_SQL:
            return self.__to_raw_sql(raw_sql, params)

        # 输出SQL语句分析信息
        if self.__EXPLAIN:
            return self.explain_raw_sql(raw_sql, params)

        # 执行sql语句
        return self.execute(raw_sql, params, get_rowid)

    def insert_all(self, data_list, clear_conditions=True, option=None):
        '''
            @name 批量插入数据
            @author Zhj<2022-07-17>
            @param  data_list<list>         批量插入数据
            @param  clear_conditions<?bool> 是否清空查询条件[可选 默认清空]
            @param  option<?string>         额外选项[可选]
            @return integer
        '''
        if self.__DB is None or len(data_list) == 0:
            return 0

        # 检查冲突选项是否正确
        if option is not None and str(option).upper() not in self.__CONFLICT_OPTIONS:
            raise PanelError('option must be one of: {}'.format(', '.join(self.__CONFLICT_OPTIONS)))

        ks = data_list[0].keys()

        # 生成sql语句
        raw_sql = 'INSERT{} INTO {} ({}) VALUES ({})'.format(
            ' OR {}'.format(str(option).upper()) if option is not None else '',
            _add_backtick_for_field(self.__DB_TABLE),
            ', '.join(list(map(lambda x: _add_backtick_for_field(x), ks))),
            ','.join(list(map(lambda x: '?', ks)))
        )

        # 绑定参数
        params = list(map(lambda x: _to_tuple(list(map(lambda y: x[y], ks))), data_list))

        # 记录语句执行开始时间
        s_time = time.time()

        # 执行sql语句
        ret = self.__DB.client().execute_many(raw_sql, params)

        # 写日志
        if self.__DB.is_debug():
            # 构造一个真实的批量写入sql
            debug_raw_sql = raw_sql
            i = len(params) - 1
            pad_str = ', ({})'.format(','.join(list(map(lambda x: '?', ks))))

            while i:
                debug_raw_sql += pad_str
                i -= 1

            # 将绑定参数扁平化
            debug_params = ()
            for p in params:
                debug_params += p

            self.__DB.debug_log(self.__to_raw_sql(debug_raw_sql, _to_tuple(debug_params)), self.__DB.db_name(),
                                time.time() - s_time)

        # 自动提交事务
        if self.__is_autocommit():
            self.commit()

        # 清空查询条件
        if clear_conditions:
            self.__clear()

        # 返回新增的行数
        return ret

    def increment(self, field, step=1):
        '''
            @name 自增数值
            @author Zhj<2022-07-17>
            @param  field<string>   字段名
            @param  step<integer>   值
            @return self
        '''
        self.__OPT_UPDATE.increment(field, step)
        return self

    def decrement(self, field, step=1):
        '''
            @name 自减数值
            @author Zhj<2022-07-17>
            @param  field<string>   字段名
            @param  step<integer>   值
            @return self
        '''
        self.__OPT_UPDATE.decrement(field, step)
        return self

    def exp(self, field, exp):
        '''
            @name 使用原生表达式更新
            @param field<string>    字段名
            @param exp<string>      原生表达式
            @return self
        '''
        self.__OPT_UPDATE.exp(field, exp)
        return self

    def update(self, data=None):
        '''
            @name 更新表数据
            @author Zhj<2022-07-17>
            @param  data<?dict>     更新数据
            @return integer|string
        '''
        if data is not None:
            # 更新数据不是字典类型 返回0
            if not isinstance(data, dict):
                return 0

            for k, v in data.items():
                self.__OPT_UPDATE.add(k, v)

        # 更新条件为空 返回0
        if self.__OPT_UPDATE.is_empty():
            return 0

        update_str, update_params = self.__OPT_UPDATE.build()
        join_str = self.__OPT_JOIN.build()
        where_str, where_params = self.__OPT_WHERE.build()
        limit_str = self.__OPT_LIMIT.build()

        raw_sql = 'UPDATE {table_name}{join_condition} SET {exprission}' \
                  '{where_condition}{limit_condition}'.format_map({
            'table_name': self.__build_table_name(True),
            'join_condition': join_str,
            'exprission': update_str,
            'where_condition': where_str,
            'limit_condition': limit_str,
        })
        bind_params = update_params + where_params

        # 输出原生sql语句
        if self.__FETCH_SQL:
            return self.__to_raw_sql(raw_sql, bind_params)

        # 输出SQL语句分析信息
        if self.__EXPLAIN:
            return self.explain_raw_sql(raw_sql, bind_params)

        # 执行sql语句
        return self.execute(raw_sql, bind_params)

    def delete(self):
        '''
            @name 删除表数据
            @author Zhj<2022-07-17>
            @return integer|string
        '''
        join_str = self.__OPT_JOIN.build()
        where_str, where_params = self.__OPT_WHERE.build()
        limit_str = self.__OPT_LIMIT.build()

        raw_sql = 'DELETE FROM {table_name}{join_condition}{where_condition}{limit_condition}'.format(
            table_name=self.__build_table_name(True),
            join_condition=join_str,
            where_condition=where_str,
            limit_condition=limit_str
        )

        # 输出原生sql语句
        if self.__FETCH_SQL:
            return self.__to_raw_sql(raw_sql, where_params)

        # 输出SQL语句分析信息
        if self.__EXPLAIN:
            return self.explain_raw_sql(raw_sql, where_params)

        # 执行sql语句
        ret = self.execute(raw_sql, where_params)

        # 自动提交事务时
        # 且开启了自动释放空间时
        # 释放空间
        if self.__is_autocommit() and self.__is_autovacuum():
            self.__DB.vacuum()
        # 否则
        # 记录本次事务提交后需要释放空间
        else:
            self.__DB.need_vacuum()

        return ret

    def find(self):
        '''
            @name 查询一行数据
            @author Zhj<2022-07-17>
            @return dict|None|string
        '''
        self.__OPT_LIMIT.set_limit(1)

        # 构建sql语句和绑定参数
        raw_sql, bind_params = self.__build_sql()

        # 输出原生sql语句
        if self.__FETCH_SQL:
            return self.__to_raw_sql(raw_sql, bind_params)

        # 输出SQL语句分析信息
        if self.__EXPLAIN:
            return self.explain_raw_sql(raw_sql, bind_params)

        return self.query(raw_sql, bind_params, True)

    def select(self):
        '''
            @name 查询多行数据
            @author Zhj<2022-07-17>
            @return list|None|string
        '''
        # 构建sql语句和绑定参数
        raw_sql, bind_params = self.__build_sql()

        # 输出原生sql语句
        if self.__FETCH_SQL:
            return self.__to_raw_sql(raw_sql, bind_params)

        # 输出SQL语句分析信息
        if self.__EXPLAIN:
            return self.explain_raw_sql(raw_sql, bind_params)

        return self.query(raw_sql, bind_params)

    def value(self, field):
        '''
            @name 获取某个字段的值
            @author Zhj<2022-07-17>
            @param  field<string>   字段名
            @return string|integer|None
        '''
        self.__OPT_FIELD.set_fields(field)
        ret = self.find()

        # 输出原生sql语句或SQL语句分析信息
        if self.__FETCH_SQL or self.__EXPLAIN:
            return ret

        if ret is None:
            return None

        return ret.get(self.__get_row_key(field), None)

    def column(self, field, dict_key=None):
        '''
            @name 获取指定字段的值列表或字典
            @author Zhj<2022-07-17>
            @param  field<string|None>   字段名
            @param  dict_key<?string>               字典键(字段名)
            @return list|dict|string
        '''
        if self.__OPT_FIELD.is_empty() and field is not None:
            self.__OPT_FIELD.set_fields(*filter(lambda x: x is not None, [field, dict_key]))

        ret = self.select()

        # 输出原生sql语句或SQL语句分析信息
        if self.__FETCH_SQL or self.__EXPLAIN:
            return ret

        if ret is None:
            # 指定了键时 返回字典
            if dict_key is not None:
                return {}

            return []

        # 返回列表
        if dict_key is None:
            return list(map(lambda x: x.get(self.__get_row_key(field), None), ret))

        # 返回字典
        d = {}
        f_k = None if field is None else self.__get_row_key(field)
        d_k = self.__get_row_key(dict_key)

        for item in ret:
            k = item.get(d_k, None)

            if k is None:
                continue

            d[k] = item if f_k is None else item.get(f_k, None)

        return d

    def count(self):
        '''
            @name 统计行数
            @author Zhj<2022-07-17>
            @return integer
        '''
        ret = self.value('COUNT(*)')

        # 输出原生sql语句或SQL语句分析信息
        if self.__FETCH_SQL or self.__EXPLAIN:
            return ret

        if ret is None:
            ret = 0

        return int(ret)

    def avg(self, field, precsicion=None):
        '''
            @name 统计平均值
            @author Zhj<2022-07-17>
            @param  field<string>       字段名
            @param  precision<?integer> 小数点精度
            @return float
        '''
        field = 'AVG({})'.format(_add_backtick_for_field(field))

        if precsicion is not None and is_number(precsicion):
            field = 'ROUND({},{})'.format(field, precsicion)

        ret = self.value(field)

        # 输出原生sql语句或SQL语句分析信息
        if self.__FETCH_SQL or self.__EXPLAIN:
            return ret

        if ret is None:
            ret = 0

        return float(ret)

    def sum(self, field, precsicion=None):
        '''
            @name 统计总和
            @author Zhj<2022-07-17>
            @param  field<string>       字段名
            @param  precision<?integer> 小数点精度
            @return integer
        '''
        field = 'SUM({})'.format(_add_backtick_for_field(field))

        if precsicion is not None and is_number(precsicion):
            field = 'ROUND({},{})'.format(field, precsicion)

        ret = self.value(field)

        # 输出原生sql语句或SQL语句分析信息
        if self.__FETCH_SQL or self.__EXPLAIN:
            return ret

        if ret is None:
            ret = 0

        return int(ret)

    def exists(self):
        '''
            @name 检查数据是否存在
            @author Zhj<2022-07-18>
            @return bool
        '''
        self.__OPT_LIMIT.set_limit(1)

        # 构建sql语句和绑定参数
        raw_sql, bind_params = self.__build_sql()

        k = 'bt__exists'

        raw_sql = 'SELECT EXISTS({}) AS `{}`'.format(raw_sql, k)

        # 输出原生sql语句
        if self.__FETCH_SQL:
            return self.__to_raw_sql(raw_sql, bind_params)

        # 输出SQL语句分析信息
        if self.__EXPLAIN:
            return self.explain_raw_sql(raw_sql, bind_params)

        # 执行sql语句
        ret = self.query(raw_sql, bind_params, True)

        if ret is None or not isinstance(ret, dict):
            return False

        return True if int(ret.get(k, 0)) == 1 else False

    # TODO 设置insert时唯一索引重复时的更新操作
    def duplicate(self, update: typing.Dict[str, str]):
        pass

    # TODO 强制索引
    def force_index(self, index_name: str):
        pass

    def build_sql(self, sub_query=False):
        '''
            @name 构建sql查询语句(合并绑定参数)
            @author Zhj<2022-07-17>
            @param  sub_query<bool> 是否为子查询
            @return string
        '''
        raw_sql = self.__to_raw_sql(*self.__build_sql())

        # 子查询
        if sub_query:
            raw_sql = '(%s)' % raw_sql

        return raw_sql

    def get_pk(self):
        '''
            @name 获取主键字段名
            @author Zhj<2022-07-18>
            @return string|None
        '''
        if self.__PK is not None:
            return self.__PK

        ret = self.query('PRAGMA TABLE_INFO({})'.format(self.__build_table_name(False)), take_first=True,
                         clear_conditions=False)

        if ret is None:
            return None

        self.__PK = ret.get('name', None)

        return self.__PK

    def get_columns(self):
        '''
            @name 获取所有列名
            @author Zhj<2022-09-21>
            @return list
        '''
        ret = self.query('PRAGMA TABLE_INFO({})'.format(self.__build_table_name(False)), clear_conditions=False)

        return [column['name'] for column in ret]

    def add_column(self, col_name, prop, force=False):
        '''
            @name 新建字段
            @author Zhj<2022-09-21>
            @param  col_name<string> 字段名
            @param  prop<string>     字段属性
            @param  force<?bool>     是否强制新增(删除旧的字段)[可选]
            @return self
        '''
        self.__OPT_ALTER_TABLE.add_column(col_name, prop, force)
        return self

    def drop_column(self, col_name):
        '''
            @name 删除字段
            @author Zhj<2022-09-21>
            @param  col_name<string> 字段名
            @return self
        '''
        self.__OPT_ALTER_TABLE.drop_column(col_name)
        return self

    def rename_column(self, col_name, new_col_name):
        '''
            @name 更新字段名
            @author Zhj<2022-09-21>
            @param  col_name<string>        当前字段名
            @param  new_col_name<string>    新字段名
            @return self
        '''
        self.__OPT_ALTER_TABLE.rename_column(col_name, new_col_name)
        return self

    def alter_table(self):
        '''
            @name 更新表结构
            @author Zhj<2022-09-21>
            @return bool
        '''
        if self.__OPT_ALTER_TABLE.is_empty():
            return False

        raw_sql = self.__OPT_ALTER_TABLE.build(self.__build_table_name(False))

        self.execute_script(raw_sql)

        return True

    def add_index(self, idx_name, idx_col):
        '''
            @name 创建索引
            @author Zhj<2022-10-11>
            @param  idx_name<string>        索引名称
            @param  idx_col<string|list>    字段名称
            @return self
        '''
        if not isinstance(idx_col, list):
            idx_col = [idx_col]

        self.execute('CREATE INDEX IF NOT EXISTS {} ON {} ({})'.format(
            _add_backtick_for_field(idx_name),
            self.__build_table_name(False),
            ','.join(list(map(lambda x: _add_backtick_for_field(x), idx_col)))
        ))

        return self

    def drop_index(self, idx_name):
        '''
            @name 删除索引
            @author Zhj<2022-10-11>
            @param  idx_name<string> 索引名称
            @return self
        '''
        self.execute('DROP INDEX IF EXISTS {} ON {}'.format(
            _add_backtick_for_field(idx_name),
            self.__build_table_name(False)
        ))

        return self

    def fork(self):
        '''
            @name 克隆一个查询构造器
            @author Zhj<2022-07-19>
            @return SqliteEasy|None
        '''
        if self.__DB is None:
            return None

        query = self.__DB.query()
        query.set_pk(self.__PK)
        if self.__FROM_SUB_QUERY:
            query.from_sub_query(self.__DB_TABLE)
        else:
            query.table(self.__DB_TABLE)
        query.prefix(self.__OPT_PREFIX)
        query.alias(self.__OPT_ALIAS)
        query.set_where_obj(copy.deepcopy(self.__OPT_WHERE))
        query.set_limit_obj(copy.deepcopy(self.__OPT_LIMIT))
        query.set_order_obj(copy.deepcopy(self.__OPT_ORDER))
        query.set_field_obj(copy.deepcopy(self.__OPT_FIELD))
        query.set_group_obj(copy.deepcopy(self.__OPT_GROUP))
        query.set_having_obj(copy.deepcopy(self.__OPT_HAVING))
        query.set_join_obj(copy.deepcopy(self.__OPT_JOIN))
        query.set_update_obj(copy.deepcopy(self.__OPT_UPDATE))

        return query

    def explain_raw_sql(self, raw_sql, bind_params=()):
        '''
            @name 分析SQL语句
            @author Zhj<2022-07-21>
            @param  raw_sql<string>         SQL语句
            @param  bind_params<list|tuple> 绑定参数
            @return string|None
        '''
        ret = self.query('EXPLAIN QUERY PLAN {}'.format(raw_sql), _to_tuple(bind_params))

        if ret is None:
            return None

        return "\n".join(list(map(lambda x: x.get('detail', ''), ret)))

    def __to_raw_sql(self, raw_sql, bind_params=()):
        '''
            @name 将sql语句和绑定参数合并
            @author Zhj<2022-07-18>
            @param  raw_sql<string>     sql语句(含有参数绑定占位符)
            @param  bind_params<tuple>  绑定参数
            @return string
        '''
        return reduce(lambda x, y: search_question_reg.sub(str(y) if is_number(y) else "'%s'" % y, x, 1), bind_params, repr(raw_sql)[1:-1])

    def __build_sql(self):
        '''
            @name 构建sql查询语句与绑定参数
            @author Zhj<2022-07-18>
            @return (sql语句<string>, 绑定参数<tuple>)
        '''
        fields = self.__OPT_FIELD.build()
        join_condition = self.__OPT_JOIN.build()
        where_condition, where_params = self.__OPT_WHERE.build()
        group_condition, group_params = self.__OPT_GROUP.build()
        having_condition, having_params = self.__OPT_HAVING.build()
        order_condition, order_params = self.__OPT_ORDER.build()
        limit_condition = self.__OPT_LIMIT.build()

        # 查询语句
        raw_sql = 'SELECT {fields} FROM {table_name}' \
                  '{join_condition}{where_condition}{group_condition}' \
                  '{order_condition}{having_condition}{limit_condition}'.format_map({
            'fields': fields,
            'table_name': self.__build_table_name(),
            'join_condition': join_condition,
            'where_condition': where_condition,
            'group_condition': group_condition,
            'having_condition': having_condition,
            'order_condition': order_condition,
            'limit_condition': limit_condition,
        })

        # 绑定参数
        bind_params = ()

        bind_params += where_params
        bind_params += group_params
        bind_params += having_params
        bind_params += order_params

        return raw_sql, bind_params

    def __build_table_name(self, contain_alias=True):
        '''
            @name 构建表名
            @author Zhj<2022-07-17>
            @param  contain_alias<bool> 是否包含别名
            @return string
        '''
        table_name = self.__DB_TABLE if self.__FROM_SUB_QUERY else _add_backtick_for_field(self.__DB_TABLE)
        table_alias = ''

        if contain_alias:
            table_alias = '' if self.__OPT_ALIAS is None else ' AS {}'.format(
                _add_backtick_for_field(self.__OPT_ALIAS)
            )

        return '{}{}'.format(table_name, table_alias)

    def __get_row_key(self, field):
        '''
            @name 获取字段名对应的字典键名
            @author Zhj<2022-07-18>
            @param  field<string>   字段名
            @return string|None
        '''
        # 移除字符串两段空白字符
        field = str(field).strip()

        m = match_row_key_reg.match(field)

        # 不符合字段规则
        # 返回None
        if m is None:
            # 检查有无设置别名
            m = search_row_key_reg.search(field)

            # 设置了别名
            if m:
                return m.group(1).strip('`')

            return field

        # 设置了别名时
        # 获取别名
        if m.group(2) is not None:
            return m.group(2).strip('`')

        # 获取字段名 不包含前缀表名
        return m.group(1).strip('`')

    def __is_autocommit(self):
        '''
            @name 检查是否自动提交事务
            @author Zhj<2022-07-18>
            @return bool
        '''
        if self.__DB is None:
            return False

        return self.__DB.is_autocommit()

    def __is_autovacuum(self):
        '''
            @name 检查是否自动释放空间
            @author Zhj<2022-09-27>
            @return bool
        '''
        if self.__DB is None:
            return False

        return self.__DB.is_autovacuum()

    def __clear(self):
        '''
            @name 清空查询条件
            @author Zhj<2022-07-17>
            @return void
        '''
        self.__PK = None
        self.__OPT_ALIAS = None
        self.__OPT_FIELD.clear()
        self.__OPT_JOIN.clear()
        self.__OPT_WHERE.clear()
        self.__OPT_GROUP.clear()
        self.__OPT_HAVING.clear()
        self.__OPT_ORDER.clear()
        self.__OPT_LIMIT.clear()
        self.__OPT_UPDATE.clear()
