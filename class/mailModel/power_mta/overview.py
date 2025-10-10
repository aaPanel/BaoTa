import copy
from datetime import datetime
import typing
from mod.base import public_aap as public
import time
from mailModel.power_mta.maillog_stat import query_maillog_with_time_section


class overview:
    def __init__(self):
        import PluginLoader
        self.__IS_PRO_MEMBER: bool = PluginLoader.get_auth_state() > 0

    # 过滤与准备时间范围
    def __filter_and_prepare_time_section(self, start_time: int = -1, end_time: int = -1) -> typing.Tuple[int, int]:
        if start_time > 0 and end_time < 0:
            end_time = int(time.time())

        if start_time > end_time:
            raise public.HintException(public.lang('end_time must greater than start_time'))

        return start_time, end_time

    # 创建统计数据查询基础query
    def __build_base_query(self, campaign_id: int = -1, domain: typing.Optional[str] = None, start_time: int = -1, end_time: int = -1) -> public.S:
        query = public.S('send_mails').alias('sm').prefix('')
        query.left_join('senders s', 'sm.postfix_message_id=s.postfix_message_id')
        query.where('s.postfix_message_id is not null')

        if domain is not None:
            query.where('s.sender like ?', '%@{}'.format(domain))

        if start_time > 0:
            query.where('sm.log_time > ?', start_time - 1)

        if end_time > 0:
            query.where('sm.log_time < ?', end_time + 1)

        return query

    # 概览图表
    def overview(self, campaign_id: int = -1, domain: typing.Optional[str] = None, start_time: int = -1, end_time: int = -1) -> typing.Dict:
        return {
            'dashboard': self.overview_dashboard(campaign_id, domain, start_time, end_time),
            'mail_providers': self.overview_providers(campaign_id, domain, start_time, end_time),
            'send_mail_chart': self.chart_send_mail(campaign_id, domain, start_time, end_time),
            'bounce_rate_chart': self.chart_bounce_rate(campaign_id, domain, start_time, end_time),
            'open_rate_chart': self.chart_open_rate(campaign_id, domain, start_time, end_time),
            'click_rate_chart': self.chart_click_rate(campaign_id, domain, start_time, end_time),
        }

    # 仪表盘数据总览
    def overview_dashboard(self, campaign_id: int = -1, domain: typing.Optional[str] = None, start_time: int = -1, end_time: int = -1) -> typing.Dict:
        start_time, end_time = self.__filter_and_prepare_time_section(start_time, end_time)

        query = self.__build_base_query(campaign_id, domain, start_time, end_time)

        query.left_join(public.S('opened').prefix('').field('distinct `postfix_message_id`').build_sql(True, 'o'), 'sm.postfix_message_id=o.postfix_message_id')
        query.left_join(public.S('clicked').prefix('').field('distinct `postfix_message_id`').build_sql(True, 'c'), 'sm.postfix_message_id=c.postfix_message_id')

        query.field('count(*) as `sends`')
        query.field('ifnull(sum(`status`=\'sent\' and `dsn`=\'2.0.0\'), 0) as `delivered`')

        if self.__IS_PRO_MEMBER:
            query.field('count(o.postfix_message_id) as `opened`')
            query.field('count(c.postfix_message_id) as `clicked`')
            query.field('ifnull(sum(`status`=\'bounced\'), 0) as `bounced`')

        ret = query_maillog_with_time_section(query, start_time, end_time)

        aggregate = {
            'sends': 0,
            'delivered': 0,
            'opened': 0,
            'clicked': 0,
            'bounced': 0,
        }

        for item in ret:
            for k, v in item.items():
                if k in aggregate:
                    aggregate[k] += int(v)

        aggregate['delivery_rate'] = round(aggregate['delivered'] / aggregate['sends'] * 100, 2) if aggregate['sends'] > 0 else 0

        if self.__IS_PRO_MEMBER:
            aggregate['bounce_rate'] = round(aggregate['bounced'] / aggregate['sends'] * 100, 2) if aggregate['sends'] > 0 else 0
            aggregate['open_rate'] = round(aggregate['opened'] / aggregate['delivered'] * 100, 2) if aggregate['delivered'] > 0 else 0
            aggregate['click_rate'] = round(aggregate['clicked'] / aggregate['delivered'] * 100, 2) if aggregate['delivered'] > 0 else 0
        else:
            aggregate['opened'] = -1
            aggregate['clicked'] = -1
            aggregate['bounced'] = -1
            aggregate['bounce_rate'] = -1
            aggregate['open_rate'] = -1
            aggregate['click_rate'] = -1

        return aggregate

    # 统计邮件服务商
    def overview_providers(self, campaign_id: int = -1, domain: typing.Optional[str] = None, start_time: int = -1, end_time: int = -1) -> typing.List:
        if not self.__IS_PRO_MEMBER:
            return [
                {
                    'mail_provider': 'google',
                    'sends': -1,
                    'delivered': -1,
                    'opened': -1,
                    'clicked': -1,
                    'bounce_rate': -1,
                    'delivery_rate': -1,
                    'open_rate': -1,
                    'click_rate': -1,
                },
                {
                    'mail_provider': 'outlook',
                    'sends': -1,
                    'delivered': -1,
                    'opened': -1,
                    'clicked': -1,
                    'bounce_rate': -1,
                    'delivery_rate': -1,
                    'open_rate': -1,
                    'click_rate': -1,
                },
                {
                    'mail_provider': 'yahoo',
                    'sends': -1,
                    'delivered': -1,
                    'opened': -1,
                    'clicked': -1,
                    'bounce_rate': -1,
                    'delivery_rate': -1,
                    'open_rate': -1,
                    'click_rate': -1,
                },
                {
                    'mail_provider': 'other',
                    'sends': -1,
                    'delivered': -1,
                    'opened': -1,
                    'clicked': -1,
                    'bounce_rate': -1,
                    'delivery_rate': -1,
                    'open_rate': -1,
                    'click_rate': -1,
                }
            ]

        start_time, end_time = self.__filter_and_prepare_time_section(start_time, end_time)

        query = self.__build_base_query(campaign_id, domain, start_time, end_time)

        query.left_join(public.S('opened').prefix('').field('distinct `postfix_message_id`').build_sql(True, 'o'),
                        'sm.postfix_message_id=o.postfix_message_id')
        query.left_join(public.S('clicked').prefix('').field('distinct `postfix_message_id`').build_sql(True, 'c'),
                        'sm.postfix_message_id=c.postfix_message_id')

        query.field('sm.mail_provider')
        query.field('count(*) as `sends`')
        query.field('ifnull(sum(`status`=\'sent\' and `dsn`=\'2.0.0\'), 0) as `delivered`')
        query.field('count(o.postfix_message_id) as `opened`')
        query.field('count(c.postfix_message_id) as `clicked`')
        query.field('ifnull(sum(`status`=\'bounced\'), 0) as `bounced`')

        query.group('sm.mail_provider')

        ret = query_maillog_with_time_section(query, start_time, end_time)

        aggregate = {
            'sends': 0,
            'delivered': 0,
            'opened': 0,
            'clicked': 0,
            'bounced': 0,
        }

        m = {}

        for item in ret:
            if 'mail_provider' not in m:
                m[item['mail_provider']] = copy.deepcopy(aggregate)

            for k, v in item.items():
                if k in aggregate:
                    m[item['mail_provider']][k] += int(v)

        lst = []
        for k, item in m.items():
            item['mail_provider'] = k
            item['delivery_rate'] = round(item['delivered'] / item['sends'] * 100, 2) if item['sends'] > 0 else 0
            item['bounce_rate'] = round(item['bounced'] / item['sends'] * 100, 2) if item['sends'] > 0 else 0
            item['open_rate'] = round(item['opened'] / item['delivered'] * 100, 2) if item['delivered'] > 0 else 0
            item['click_rate'] = round(item['clicked'] / item['delivered'] * 100, 2) if item['delivered'] > 0 else 0
            lst.append(item)

        return sorted(lst, key=lambda x: x['sends'], reverse=True)

    # 图表数据序列填充
    def fill_chart_data(self, data: typing.List, fill_item: typing.Dict, fill_type: str = 'daily', fill_key: str = 'x', start_time: int = -1, end_time: int = -1) -> typing.List:
        '''
            @name 图表数据序列填充
            @param data list 图表数据序列
            @param fill_item dict 填充项
            @param fill_type str 填充类型 daily|hourly|monthly
            @param fill_key str 填充字段
            @return list
        '''
        if fill_type == 'daily':
            return self.fill_chart_data_daily(data, fill_item, fill_key, start_time, end_time)
        elif fill_type == 'hourly':
            return self.fill_chart_data_hourly(data, fill_item, fill_key)
        elif fill_type == 'monthly':
            return self.fill_chart_data_monthly(data, fill_item, fill_key, start_time, end_time)
        else:
            return data

    # 图表数据序列小时填充
    def fill_chart_data_hourly(self, data: typing.List, fill_item: typing.Dict, fill_key: str = 'x') -> typing.List:
        for item in data:
            item[fill_key] = int(item['x'])

        if len(data) == 24:
            return data

        m = {}
        for item in data:
            m[int(item[fill_key])] = item

        lst = []
        for i in range(24):
            if i in m:
                lst.append(m[i])
                continue

            item = copy.deepcopy(fill_item)
            item[fill_key] = i
            lst.append(item)

        return lst

    # 图表数据序列日填充
    def fill_chart_data_daily(self, data: typing.List, fill_item: typing.Dict, fill_key: str = 'x', start_time: int = -1, end_time: int = -1) -> typing.List:
        if start_time < 0 or end_time < 0:
            return data

        if start_time > 0 and end_time < 0:
            end_time = int(time.time())

        if start_time > end_time:
            return data

        m = {}
        for item in data:
            m[item[fill_key]] = item

        lst = []
        for i in range(start_time, end_time + 1, 86400):
            day_date_obj = datetime.fromtimestamp(i)
            day_date = day_date_obj.strftime('%Y-%m-%d')
            day_time = int(datetime(day_date_obj.year, day_date_obj.month, day_date_obj.day, 0, 0, 0).timestamp())
            if day_date in m:
                m[day_date][fill_key] = day_time
                lst.append(m[day_date])
                continue

            item = copy.deepcopy(fill_item)
            item[fill_key] = day_time
            lst.append(item)

        return lst

    # 图表数据序列月填充
    def fill_chart_data_monthly(self, data: typing.List, fill_item: typing.Dict, fill_key: str = 'x',
                              start_time: int = -1, end_time: int = -1) -> typing.List:
        if start_time < 0 or end_time < 0:
            return data

        if start_time > 0 and end_time < 0:
            end_time = int(time.time())

        if start_time > end_time:
            return data

        m = {}
        for item in data:
            m[item[fill_key]] = item

        lst = []
        for i in range(start_time, end_time + 1, 86400):
            day_date_obj = datetime.fromtimestamp(i)
            day_date = day_date_obj.strftime('%Y-%m-%d')
            day_time = int(datetime(day_date_obj.year, day_date_obj.month, day_date_obj.day, 0, 0, 0).timestamp())
            if day_date in m:
                m[day_date][fill_key] = day_time
                lst.append(m[day_date])
                continue

            item = copy.deepcopy(fill_item)
            item[fill_key] = day_time
            lst.append(item)

        return lst

    # 统计邮件发送数据总览
    def send_mail_dashboard(self, campaign_id: int = -1, domain: typing.Optional[str] = None, start_time: int = -1, end_time: int = -1) -> typing.Dict:
        start_time, end_time = self.__filter_and_prepare_time_section(start_time, end_time)

        query = self.__build_base_query(campaign_id, domain, start_time, end_time)

        query.field('count(*) as `sends`')
        query.field('ifnull(sum(`status`=\'sent\' and `dsn`=\'2.0.0\'), 0) as `delivered`')
        query.field('count(*) - ifnull(sum(`status`=\'sent\' and `dsn`=\'2.0.0\'), 0) as `failed`')

        ret = query_maillog_with_time_section(query, start_time, end_time)

        aggregate = {
            'sends': 0,
            'delivered': 0,
            'failed': 0,
        }

        for item in ret:
            for k, v in item.items():
                if k in aggregate:
                    aggregate[k] += int(v)

        aggregate['delivery_rate'] = round(aggregate['delivered'] / aggregate['sends'] * 100, 2) if aggregate['sends'] > 0 else 0
        aggregate['failure_rate'] = round(aggregate['failed'] / aggregate['sends'] * 100, 2) if aggregate['sends'] > 0 else 0

        return aggregate

    # 准备邮件发送数据图表
    def __prepare_chart_data(self, start_time: int = -1, end_time: int = -1) -> typing.Tuple[str, str]:
        column_type = 'daily'
        datetime_format = '%Y-%m-%d'
        secs = end_time - start_time

        if secs < 86400:
            column_type = 'hourly'
            datetime_format = '%H'

        x_axis_field = 'strftime(\'{}\', `sm`.`log_time`, \'unixepoch\', \'localtime\') as `x`'.format(datetime_format)

        return column_type, x_axis_field

    # 统计邮件发送数据图表
    def chart_send_mail(self, campaign_id: int = -1, domain: typing.Optional[str] = None, start_time: int = -1, end_time: int = -1) -> typing.Dict:
        start_time, end_time = self.__filter_and_prepare_time_section(start_time, end_time)

        query = self.__build_base_query(campaign_id, domain, start_time, end_time)

        column_type, x_axis_field = self.__prepare_chart_data(start_time, end_time)

        query.field(x_axis_field)
        query.field('count(*) as `sends`')
        query.field('ifnull(sum(`status`=\'sent\' and `dsn`=\'2.0.0\'), 0) as `delivered`')
        query.field('count(*) - ifnull(sum(`status`=\'sent\' and `dsn`=\'2.0.0\'), 0) as `failed`')

        query.group('x')
        query.order('x')

        ret = query_maillog_with_time_section(query, start_time, end_time)

        fill_item = {
            'sends': 0,
            'delivered': 0,
            'failed': 0,
        }

        return {
            'column_type': column_type,
            'dashboard': self.send_mail_dashboard(campaign_id, domain, start_time, end_time),
            'data': self.fill_chart_data(ret, fill_item, column_type, 'x', start_time, end_time)
        }

    # 统计邮件退件率数据图表
    def chart_bounce_rate(self, campaign_id: int = -1, domain: typing.Optional[str] = None, start_time: int = -1, end_time: int = -1) -> typing.Dict:
        if not self.__IS_PRO_MEMBER:
            return {
                'column_type': None,
                'data': None,
            }

        start_time, end_time = self.__filter_and_prepare_time_section(start_time, end_time)

        query = self.__build_base_query(campaign_id, domain, start_time, end_time)

        column_type, x_axis_field = self.__prepare_chart_data(start_time, end_time)

        query.field(x_axis_field)
        query.field('case when count(*) > 0 then round(1.0 * ifnull(sum(`status`=\'bounced\'), 0) / count(*) * 100.0, 2) else 0.0 end as `bounce_rate`')

        query.group('x')
        query.order('x')

        ret = query_maillog_with_time_section(query, start_time, end_time)

        fill_item = {
            'bounce_rate': 0.0,
        }

        return {
            'column_type': column_type,
            'data': self.fill_chart_data(ret, fill_item, column_type, 'x', start_time, end_time),
        }

    # 统计邮件打开率数据图表
    def chart_open_rate(self, campaign_id: int = -1, domain: typing.Optional[str] = None, start_time: int = -1, end_time: int = -1) -> typing.Dict:
        if not self.__IS_PRO_MEMBER:
            return {
                'column_type': None,
                'data': None,
            }

        start_time, end_time = self.__filter_and_prepare_time_section(start_time, end_time)

        query = self.__build_base_query(campaign_id, domain, start_time, end_time)

        column_type, x_axis_field = self.__prepare_chart_data(start_time, end_time)

        query.left_join(public.S('opened').prefix('').field('distinct `postfix_message_id`').build_sql(True, 'o'),
                        'sm.postfix_message_id=o.postfix_message_id')

        query.field(x_axis_field)
        query.field('case when ifnull(sum(`status`=\'sent\' and `dsn`=\'2.0.0\'), 0) > 0 then round(1.0 * count(o.postfix_message_id) / ifnull(sum(`status`=\'sent\' and `dsn`=\'2.0.0\'), 0) * 100, 2) else 0.0 end as `open_rate`')

        query.group('x')

        ret = query_maillog_with_time_section(query, start_time, end_time)

        fill_item = {
            'open_rate': 0.0,
        }

        return {
            'column_type': column_type,
            'data': self.fill_chart_data(ret, fill_item, column_type, 'x', start_time, end_time),
        }

    # 统计邮件点击率数据图表
    def chart_click_rate(self, campaign_id: int = -1, domain: typing.Optional[str] = None, start_time: int = -1, end_time: int = -1) -> typing.Dict:
        if not self.__IS_PRO_MEMBER:
            return {
                'column_type': None,
                'data': None,
            }

        start_time, end_time = self.__filter_and_prepare_time_section(start_time, end_time)

        query = self.__build_base_query(campaign_id, domain, start_time, end_time)

        column_type, x_axis_field = self.__prepare_chart_data(start_time, end_time)

        query.left_join(public.S('clicked').prefix('').field('distinct `postfix_message_id`').build_sql(True, 'c'),
                        'sm.postfix_message_id=c.postfix_message_id')

        query.field(x_axis_field)
        query.field('case when ifnull(sum(`status`=\'sent\' and `dsn`=\'2.0.0\'), 0) > 0 then round(1.0 * count(c.postfix_message_id) / ifnull(sum(`status`=\'sent\' and `dsn`=\'2.0.0\'), 0) * 100, 2) else 0.0 end as `click_rate`')

        query.group('x')

        ret = query_maillog_with_time_section(query, start_time, end_time)

        fill_item = {
            'click_rate': 0.0,
        }

        return {
            'column_type': column_type,
            'data': self.fill_chart_data(ret, fill_item, column_type, 'x', start_time, end_time),
        }
