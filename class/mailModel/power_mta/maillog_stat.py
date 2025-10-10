# maillog statistics
import io
import json
import logging
import threading
import typing

from mod.base import public_aap as public
from mod.base.public_aap.validate import Param
from datetime import datetime
import re
import time
import os
import pyinotify
from glob import glob
from Crypto.Cipher import AES
import base64
from PIL import Image
from BTPanel import Response, redirect
from urllib.parse import urlparse
import fcntl

# definition the sys distributor, ubuntu was default.
sys_distributor = 'ubuntu'

if public.get_linux_distribution().lower().find('ubuntu') < 0:
    sys_distributor = 'centos'

# definition the default maillog path
default_maillog_path = '/var/log/mail.log'

if not os.path.exists(default_maillog_path):
    default_maillog_path = '/var/log/maillog'

default_postfix_main_conf = '/etc/postfix/main.cf'

default_latest_log_time_file = '{}/data/last_maillog_time'.format(public.get_panel_path())


# get/set last_maillog_time
def last_maillog_time(latest_maillog_time: float = -1) -> float:
    cur_maillog_time: float = 0.0

    if os.path.exists(default_latest_log_time_file):
        with open(default_latest_log_time_file, 'r') as fp:
            try:
                cur_maillog_time = float(fp.read().strip())
            except:
                pass

    # try update local file
    if latest_maillog_time > 0 and latest_maillog_time > cur_maillog_time:
        with open(default_latest_log_time_file, 'w') as fp:
            fp.write(str(latest_maillog_time))
        cur_maillog_time = latest_maillog_time

    return cur_maillog_time


class AbstractMailRecord:
    __slots__ = ['postfix_message_id', 'log_time']

    def to_dict(self):
        d = {}
        for k in self.__slots__:
            if hasattr(self, k):
                d[k] = getattr(self, k)
                if k == 'log_time':
                    d[k] = int(d[k])
        return d

    def log_day_date(self):
        return datetime.fromtimestamp(self.log_time).strftime('%Y%m%d')


class MailSendRecord(AbstractMailRecord):
    __slots__ = ['postfix_message_id', 'recipient', 'mail_provider', 'status', 'delay',
                 'delays', 'dsn', 'relay', 'description', 'log_time']


class MailMessageId(AbstractMailRecord):
    __slots__ = ['postfix_message_id', 'message_id', 'log_time']


class MailSender(AbstractMailRecord):
    __slots__ = ['postfix_message_id', 'sender', 'size', 'log_time']


class MailRemoved(AbstractMailRecord):
    __slots__ = ['postfix_message_id', 'log_time']


class MailDeferredRecord(AbstractMailRecord):
    __slots__ = ['postfix_message_id', 'delay', 'delays', 'dsn', 'relay',
                 'description', 'log_time']


class MaillogStat:
    # prepare compile regular expression
    status_pattern = re.compile(r'status=(\S+) ')
    recipient_pattern = re.compile(r'to=<([^>]+)>')
    delay_pattern = re.compile(r'delay=(\d+(?:\.\d+)?),')
    delays_pattern = re.compile(r'delays=(\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?){3}),')
    dsn_pattern = re.compile(r'dsn=([^,]+),')
    relay_pattern = re.compile(r'relay=([^,]+),')
    description_pattern = re.compile(r'\((.*?)\)$')
    custom_message_id_pattern = re.compile(r'message-id=<([^>]+)>')
    message_id_pattern = re.compile(r'postfix/[^\[]+\[\d+]: *([^:]+):')
    mail_removed_pattern = re.compile(r'postfix/qmgr\[\d+]: *([^:]+): *removed$')
    mail_sender_pattern = re.compile(r'postfix/qmgr\[\d+]: *([^:]+): *from=<([^>]+)>, +size=(\d+),')

    myhostname_pattern = re.compile(r'myhostname *= *([^\r\n]+)')
    virtual_transport_pattern = re.compile(r'virtual_transport *= *([^\r\n]+)')

    split_pattern = re.compile(r' +')

    def __init__(self, maillog_path: str = default_maillog_path, start_time: float = -1, end_time: float = -1, do_summary: bool = False):
        self.__maillog_path = maillog_path
        self.__start_time = start_time
        self.__end_time = end_time
        self.__do_summary = do_summary
        self.__ignore_relays = set()
        self.__ignore_mail_addresses = set()
        self.__current_year = datetime.now().year
        self.__delivered = 0
        self.__bounced = 0
        self.__deferred = 0
        self.__deferred_total = 0
        self.__bounce_details = {}
        self.__deferral_details = {}
        self.__mail_hostname = None
        self.__standard_maillog_head_pattern: typing.Optional[re.Pattern] = None
        self.__month_map = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
            'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
            'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }

        self.__reset_datas()
        self.__init_ignore_relays()
        self.__init_ignore_mail_addresses()
        self.__compile_standard_maillog_head_pattern()

    # reset datas
    def __reset_datas(self):
        self.__bounce_details.clear()
        self.__deferral_details.clear()
        self.__current_year = datetime.fromtimestamp(os.path.getmtime(self.__maillog_path)).year
        self.__delivered = 0
        self.__bounced = 0
        self.__deferred = 0
        self.__deferred_total = 0

    # initialize __ignore_relays
    def __init_ignore_relays(self):
        if not os.path.exists(default_postfix_main_conf):
            return

        myhostname = None
        virtual_transport = None

        with open(default_postfix_main_conf) as fp:
            for line in fp:
                line = line.strip()

                if line == '':
                    continue

                if myhostname is not None and virtual_transport is not None:
                    break

                if myhostname is None:
                    m = self.myhostname_pattern.search(line)

                    if m is not None:
                        myhostname = m.group(1)
                        continue

                if virtual_transport is None:
                    m = self.virtual_transport_pattern.search(line)

                    if m is not None:
                        virtual_transport = m.group(1)
                        continue

        if myhostname is None or virtual_transport is None:
            return

        self.__mail_hostname = myhostname

        self.__ignore_relays.add('{}[{}]'.format(myhostname, virtual_transport.split(':')[-1]))

    # initialize __ignore_mail_addresses
    def __init_ignore_mail_addresses(self):
        self.__ignore_mail_addresses.add('root@localhost')

        if self.__mail_hostname is not None:
            self.__ignore_mail_addresses.add('root@{}'.format(self.__mail_hostname))

    # compile standard_maillog_head_pattern
    def __compile_standard_maillog_head_pattern(self):
        if self.__mail_hostname is None:
            return

        top_host = str(self.__mail_hostname).split('.', 2)[0]
        regexp = r'((?:[A-Z][a-z]{2} \d{1,2} \d{2}(?::\d{2}){2}|\d{4}(?:-\d{2}){2}T\d{2}(?::\d{2}){2}(?:\.\d+)?(?:Z|\+\d{2}:\d{2})) ' + top_host + r' postfix/[^[]+\[\d+]: )'
        self.__standard_maillog_head_pattern = re.compile(regexp)

    # get mailProvider from email address
    def __get_mail_provider(self, email: str) -> str:
        hostname = email.split('@')[-1]

        # google
        if hostname in ['gmail.com', 'googlemail.com']:
            return 'google'

        # outlook
        if hostname in ['outlook.com', 'hotmail.com', 'live.com', 'msn.com'] or hostname.startswith('outlook.'):
            return 'outlook'

        # yahoo!
        if hostname in ['yahoo.com', 'ymail.com', 'rocketmail.com'] or hostname.startswith('yahoo.'):
            return 'yahoo'

        # Apple
        if hostname in ['icloud.com', 'me.com', 'mac.com', 'apple.com']:
            return 'apple'

        # proton
        if hostname in ['protonmail.com', 'proton.me', 'pm.me']:
            return 'proton'

        # zoho
        if hostname in ['zoho.com', 'zohomail.com', 'zohocorp.com', 'zmail.com'] or hostname.startswith('zoho.'):
            return 'zoho'

        # amazon
        if hostname in ['kindle.com', 'amazon.com', 'awsapps.com']:
            return 'amazon'

        return 'other'

    # transform log datetime to timestamp
    def __parse_log_time(self, line: str) -> float:
        try:
            import dateutil.parser
        except:
            public.ExecShell("btpip install python-dateutil==2.9.0.post0")
            import dateutil.parser
        # trim
        line = line.strip()

        try:
            # First try ISO 8601 format and RFC 3339 format
            if line[:4].isdigit():
                return dateutil.parser.parse(line.split(' ', 2)[0]).timestamp()

            parts = self.split_pattern.split(line, 4)

            if len(parts) < 4 or parts[0] not in self.__month_map:
                # return -1 if parse failed
                return -1

            # parse sys datetime format
            month = self.__month_map[parts[0]]
            day = int(parts[1])
            hour, minute, second = map(int, parts[2].split(':'))

            return datetime(self.__current_year, month, day, hour, minute, second).timestamp()
        except:
            public.print_error()

            # return -1 if parse failed
            return -1

    # split standard postfix logs on one line
    def __separate_logs_with_line(self, line: str) -> typing.List[str]:
        if self.__standard_maillog_head_pattern is None:
            return [line]

        parts = self.__standard_maillog_head_pattern.split(line)
        parts_len = len(parts)

        if parts_len < 3:
            return [line]

        lines = []
        for i in range(1, len(parts), 2):
            lines.append(str(parts[i] + parts[i + 1]).strip())

        return lines

    # start analysis maillog
    def analysis(self, maillog_path: typing.Optional[str] = None, start_time: float = -1, end_time: float = -1, do_summary: typing.Optional[bool] = None):
        # reset datas
        self.__reset_datas()

        # get current timestamp
        # cur_time = int(time.time())

        if maillog_path is None or not os.path.exists(maillog_path):
            maillog_path = self.__maillog_path

        if maillog_path != self.__maillog_path:
            self.__current_year = datetime.fromtimestamp(os.path.getmtime(maillog_path)).year

        if start_time < 1:
            start_time = self.__start_time

        if end_time < 1:
            end_time = self.__end_time

        if do_summary is None:
            do_summary = self.__do_summary

        # collect analysis failed logs
        maillog_analysis_faileds = []
        maillog_analysis_failed_file = '{}/data/maillog_analysis_failed.log'.format(public.get_panel_path())

        using_gzip = maillog_path.endswith('.gz')

        # read log file reverse
        for line_tmp in public.read_file_each_reverse(maillog_path, using_gzip=using_gzip):
            analysis_fn = self.__get_analysis_fn(line_tmp)

            if analysis_fn is None:
                continue

            line = line_tmp.strip()

            # transform log datetime to timestamp
            log_time = self.__parse_log_time(line)

            # continue if parse log_time failed
            if log_time < 1:
                maillog_analysis_faileds.append(line)

                if len(maillog_analysis_faileds) == 5000:
                    with open(maillog_analysis_failed_file, 'a') as fp:
                        fp.write('{}\n'.format('\n'.join(maillog_analysis_faileds)))
                    maillog_analysis_faileds = []

                continue

            # check end time
            if end_time > 0 and log_time > end_time - 0.000001:
                continue

            # check start time
            if start_time > 0 and log_time < start_time + 0.000001:
                break

            record = analysis_fn(line, log_time, do_summary)

            if record is None:
                continue

            if isinstance(record, MailSendRecord) and record.status == 'deferred':
                deferred_record = MailDeferredRecord()
                deferred_record.postfix_message_id = record.postfix_message_id
                deferred_record.delay = record.delay
                deferred_record.delays = record.delays
                deferred_record.dsn = record.dsn
                deferred_record.relay = record.relay
                deferred_record.description = record.description
                deferred_record.log_time = record.log_time
                yield deferred_record

            yield record

        if len(maillog_analysis_faileds) > 0:
            with open(maillog_analysis_failed_file, 'a') as fp:
                fp.write('{}\n'.format('\n'.join(maillog_analysis_faileds)))

    # get analysis function by line
    def __get_analysis_fn(self, line: str) -> typing.Optional[typing.Callable]:
        if line.find('postfix/lmtp[') > -1:
            return None

        # record type
        analysis_fn = None

        # trace qmgr process
        if line.find('postfix/qmgr[') > -1:
            if line.find('from=<') > -1:
                analysis_fn = self.__analysis_with_sender
            elif line.find('removed') > -1:
                analysis_fn = self.__analysis_with_removed

        # trace cleanup process
        if analysis_fn is None and line.find('postfix/cleanup[') > -1:
            if line.find('message-id=<') > -1:
                analysis_fn = self.__analysis_with_message_id

        # send mail
        if analysis_fn is None and line.find('to=<') > -1 and line.find('status=') > -1 and line.find('dsn=') > -1:
            analysis_fn = self.__analysis_with_send_mail

        # skip
        return analysis_fn

    # analysis with sender line
    def __analysis_with_sender(self, line: str, log_time: int = -1, do_summary: typing.Optional[bool] = None) -> typing.Optional[AbstractMailRecord]:
        line = line.strip()

        if log_time < 1:
            log_time = self.__parse_log_time(line)

        if do_summary is None:
            do_summary = self.__do_summary

        m_mail_sender = self.mail_sender_pattern.search(line)

        if m_mail_sender is None:
            return None

        record = MailSender()
        record.postfix_message_id = m_mail_sender.group(1).strip()
        record.sender = m_mail_sender.group(2).strip()
        record.size = int(m_mail_sender.group(3).strip())
        record.log_time = log_time

        if record.sender in self.__ignore_mail_addresses:
            return None

        if do_summary:
            # TODO doing summary...
            pass

        return record

    # analysis with removed line
    def __analysis_with_removed(self, line: str, log_time: int = -1, do_summary: typing.Optional[bool] = None) -> typing.Optional[AbstractMailRecord]:
        line = line.strip()

        if log_time < 1:
            log_time = self.__parse_log_time(line)

        if do_summary is None:
            do_summary = self.__do_summary

        m_mail_removed = self.mail_removed_pattern.search(line)

        if m_mail_removed is None:
            return None

        record = MailRemoved()
        record.postfix_message_id = m_mail_removed.group(1).strip()
        record.log_time = log_time

        if do_summary:
            # TODO doing summary...
            pass

        return record

    # analysis with message-id line
    def __analysis_with_message_id(self, line: str, log_time: int = -1, do_summary: typing.Optional[bool] = None) -> typing.Optional[AbstractMailRecord]:
        line = line.strip()

        if log_time < 1:
            log_time = self.__parse_log_time(line)

        if do_summary is None:
            do_summary = self.__do_summary

        # match message-id
        m_message_id = self.message_id_pattern.search(line)

        if m_message_id is None:
            return None

        # match custom-message-id
        m_custom_message_id = self.custom_message_id_pattern.search(line)

        # mapping message_id to custom_message_id
        if m_custom_message_id is None:
            return None

        record = MailMessageId()
        record.postfix_message_id = m_message_id.group(1).strip()
        record.message_id = m_custom_message_id.group(1).strip()
        record.log_time = log_time

        if do_summary:
            # TODO doing summary...
            pass

        return record

    # analysis with send mail line
    def __analysis_with_send_mail(self, line: str, log_time: int = -1, do_summary: typing.Optional[bool] = None) -> typing.Optional[AbstractMailRecord]:
        line = line.strip()

        if log_time < 1:
            log_time = self.__parse_log_time(line)

        if do_summary is None:
            do_summary = self.__do_summary

        # match message-id
        m_message_id = self.message_id_pattern.search(line)

        if m_message_id is None:
            return None

        # match recipient
        m_recipient = self.recipient_pattern.search(line)

        if m_recipient is None:
            return None

        # match status
        m_status = self.status_pattern.search(line)

        if m_status is None:
            return None

        record = MailSendRecord()
        record.postfix_message_id = m_message_id.group(1).strip()
        record.log_time = log_time
        record.recipient = m_recipient.group(1).strip()
        record.status = m_status.group(1).strip()
        record.delay = 0
        record.delays = ''
        record.dsn = ''
        record.description = ''
        record.mail_provider = ''

        if record.recipient in self.__ignore_mail_addresses:
            return None

        # match relay
        m_relay = self.relay_pattern.search(line)

        if m_relay is not None:
            relay = m_relay.group(1).strip()

            # skip when relay in ignore_relays
            if relay in self.__ignore_relays:
                return None

            record.relay = relay

        # match delay
        m_delay = self.delay_pattern.search(line)

        if m_delay is not None:
            record.delay = float(m_delay.group(1).strip())

        # match delays
        m_delays = self.delays_pattern.search(line)

        if m_delays is not None:
            record.delays = m_delays.group(1).strip()

        # match dsn
        m_dsn = self.dsn_pattern.search(line)

        if m_dsn is not None:
            record.dsn = m_dsn.group(1).strip()

        # match description
        m_description = self.description_pattern.search(line)

        if m_description is not None:
            record.description = m_description.group(1).strip()

        record.mail_provider = self.__get_mail_provider(record.recipient)

        if do_summary:
            if record.status == 'sent' and record.dsn == '2.0.0':
                self.__delivered += 1
            elif record.status == 'bounced':
                self.__bounced += 1

                if record.postfix_message_id not in self.__bounce_details:
                    self.__bounce_details[record.postfix_message_id] = set()

                self.__bounce_details[record.postfix_message_id].add(record.description)
            elif record.status == 'deferred':
                self.__deferred_total += 1

                if record.postfix_message_id not in self.__deferral_details:
                    self.__deferral_details[record.postfix_message_id] = set()
                    self.__deferred += 1

                self.__deferral_details[record.postfix_message_id].add(record.description)

        return record

    # summary
    def summary(self) -> typing.Dict:
        return {
            'delivered': self.__delivered,
            'bounced': self.__bounced,
            'deferred': self.__deferred,
            'deferred_total': self.__deferred_total,
            'bounce_details': self.__bounce_details,
            'deferral_details': self.__deferral_details,
        }


class MaillogEventHandler(pyinotify.ProcessEvent):
    def __init__(self, *args, **kwargs):
        pyinotify.ProcessEvent.__init__(self, *args, **kwargs)
        init_maillog_databases()
        self.__maillog_stat: MaillogStat = MaillogStat(start_time=last_maillog_time(), do_summary=False)
        self.__rename_cookie = None
        self.__analysis_archive = False
        self.__delay: float = 60
        self.__timer: typing.Optional[threading.Timer] = None

    def __register_timer(self):
        if self.__timer is not None:
            return

        self.__timer = threading.Timer(self.__delay, self.__update_maillog)
        self.__timer.start()

        logging.debug('registered timer')

    def __update_maillog(self):
        try:
            logging.debug('update maillog...')

            if self.__analysis_archive:
                try:
                    analysis_and_save_to_database(self.__maillog_stat, last_maillog_time(), maillog_path='{}.1'.format(default_maillog_path))
                except:
                    public.print_error()
                    pass
                self.__analysis_archive = False

            latest_log_time = analysis_and_save_to_database(self.__maillog_stat, last_maillog_time())

            logging.debug('update maillog success, latest_log_time: {}'.format(latest_log_time))
        finally:
            if self.__timer is not None:
                self.__timer.cancel()
                self.__timer = None

    def process_IN_MODIFY(self, event):
        if event.pathname == default_maillog_path:
            self.__register_timer()

    def process_IN_MOVED_FROM(self, event):
        if event.pathname == default_maillog_path:
            self.__rename_cookie = event.cookie

    def process_IN_MOVED_TO(self, event):
        if event.cookie == self.__rename_cookie and event.pathname == '{}.1'.format(default_maillog_path):
            self.__rename_cookie = None
            self.__analysis_archive = True


def maillog_event():
    ev = MaillogEventHandler()
    wm = pyinotify.WatchManager()
    mode = pyinotify.IN_MODIFY | pyinotify.IN_MOVED_FROM | pyinotify.IN_MOVED_TO
    wm.add_watch(os.path.dirname(default_maillog_path), mode, auto_add=True, rec=True)
    notifier = pyinotify.Notifier(wm, ev)
    notifier.loop()


# maillog database help function
def maillog_db_query(table_name, day_date):
    create_table_sql = r'''
-- 邮件从队列中移除记录
create table if not exists `removed` (
	`postfix_message_id` text primary key,
    `log_time` integer not null default (strftime('%s'))
);

-- 索引
create index if not exists `removed_logTime` on `removed` (`log_time`);

-- 邮件MessageID
create table if not exists `message_ids` (
	`postfix_message_id` text primary key,
    `log_time` integer not null default (strftime('%s')),
    `message_id` text not null default ''
);

-- 索引
create index if not exists `messageIds_logTime` on `message_ids` (`log_time`);
create index if not exists `messageIds_messageId` on `message_ids` (`message_id`);

-- 邮件发件人
create table if not exists `senders` (
	`postfix_message_id` text primary key,
    `log_time` integer not null default (strftime('%s')),
    `size` integer not null default 0,
    `sender` text not null default ''
);

-- 索引
create index if not exists `senders_logTime_size_sender` on `senders` (`log_time`, `size`, `sender`);

-- 邮件发送记录（记录唯一，保留最新的发送记录）
create table if not exists `send_mails` (
	`postfix_message_id` text primary key,
    `log_time` integer not null default (strftime('%s')),
    `status` text not null default '',
    `recipient` text not null default '',
    `mail_provider` text not null default '',
    `delay` real not null default 0,
    `delays` text not null default '',
    `dsn` text not null default '',
    `relay` text not null default '',
    `description` text not null default ''
);

-- 索引
create index if not exists `sendMails_logTime_status_recipient` on `send_mails` (`log_time`, `status`, `recipient`);

create index if not exists `sendMails_logTime_status_mailProvider` on `send_mails` (`log_time`, `status`, `mail_provider`);

-- 邮件延迟发送记录
create table if not exists `deferred_mails` (
	`id` integer primary key autoincrement,
    `postfix_message_id` text not null default '',
    `log_time` integer not null default (strftime('%s')),
    `delay` real not null default 0,
    `delays` text not null default '',
    `dsn` text not null default '',
    `relay` text not null default '',
    `description` text not null default ''
);

-- 索引
create index if not exists `deferredMails_postfixMessageId_logTime` on `deferred_mails` (`postfix_message_id`, `log_time`);

-- 邮件打开记录
create table if not exists `opened` (
	`id` integer primary key autoincrement,
    `campaign_id` iteger not null default 0,
    `log_time` integer not null default (strftime('%s')),
    `recipient` text not null default '',
    `postfix_message_id` text not null default '',
    `message_id` text not null default ''
);

-- 索引1
create index if not exists `opened_postfixMessageId_logTime` on `opened` (`postfix_message_id`, `log_time`);

-- 索引2
create index if not exists `opened_campaignId_logTime` on `opened` (`campaign_id`, `log_time`);


-- 邮件点击记录
create table if not exists `clicked` (
	`id` integer primary key autoincrement,
    `campaign_id` iteger not null default 0,
    `log_time` integer not null default (strftime('%s')),
    `recipient` text not null default '',
    `url` text not null default '',
    `postfix_message_id` text not null default '',
    `message_id` text not null default ''
);

-- 索引1
create index if not exists `clicked_postfixMessageId_logTime_url` on `clicked` (`postfix_message_id`, `log_time`, `url`);

-- 索引2
create index if not exists `clicked_campaignId_logTime_url_recipient` on `clicked` (`campaign_id`, `log_time`, `url`, `recipient`);
'''

    db_name = 'maillog/maillog_{}'.format(day_date)

    dir_path = '{}/data/{}'.format(public.get_panel_path(), os.path.dirname(db_name))
    if not os.path.exists(dir_path):
        os.mkdir(dir_path, 0o750)

    with public.S(table_name, db_name) as query:
        query.execute_script('PRAGMA journal_mode = wal;')
        query.execute_script(create_table_sql)

    return public.S(table_name, db_name)


# maillog query helper
def query_maillog_with_time_section(query, start_time: int = -1, end_time: int = -1) -> typing.List:
    if start_time < 1 and end_time < 1:
        return query_maillog_all(query)

    if end_time < 1:
        end_time = int(time.time())

    if end_time < start_time:
        raise ValueError(public.lang('end_time must greater than start_time'))

    ret = []

    snapshot = query.snapshot()

    for i in range(start_time, end_time + 1, 86400):
        day_date = datetime.fromtimestamp(i).strftime('%Y%m%d')

        db_path = '{}/data/maillog/maillog_{}.db'.format(public.get_panel_path(), day_date)

        if not os.path.exists(db_path):
            continue

        with maillog_db_query(None, day_date) as q:
            ret.extend(q.restore_from_snapshot(snapshot).select())

    return ret


# maillog query helper all
def query_maillog_all(query) -> typing.List:
    ret = []

    snapshot = query.snapshot()

    for db_path in glob('{}/data/maillog/maillog_*.db'.format(public.get_panel_path())):

        with maillog_db_query(None, db_path[-11:-3]) as q:
            ret.extend(q.restore_from_snapshot(snapshot).select())

    return ret


# 通过邮件头的message-id查询postfix_message_id
def search_postfix_message_id_by_message_id(message_id: str) -> typing.Optional[str]:
    for db_path in reversed(glob('{}/data/maillog/maillog_*.db'.format(public.get_panel_path()))):
        with maillog_db_query('message_ids', db_path[-11:-3]) as query:
            postfix_message_id = query.where('message_id', message_id).value('postfix_message_id')

            if postfix_message_id is not None:
                return postfix_message_id

    # analysis last 5 minutes maillog
    for record in MaillogStat(start_time=int(time.time()) - 300).analysis():
        if isinstance(record, MailMessageId) and record.message_id == message_id:
            return record.postfix_message_id


# analysis and save to database
def analysis_and_save_to_database(maillog_stat: MaillogStat, start_time: float = -1, end_time: float = -1, auto_update_maillog_time: bool = True, maillog_path: typing.Optional[str] = None) -> float:
    with open(default_latest_log_time_file, 'ab') as fp:
        # lock file
        fcntl.flock(fp.fileno(), fcntl.LOCK_EX)

        insert_datas = {
            'send_mails': {},
            'deferred_mails': {},
            'message_ids': {},
            'senders': {},
            'removed': {},
        }

        latest_log_time = 0

        for record in maillog_stat.analysis(maillog_path, start_time=start_time, end_time=end_time):
            if latest_log_time < record.log_time:
                latest_log_time = record.log_time

            log_day_date = record.log_day_date()
            k = None

            if isinstance(record, MailSender):
                k = 'senders'
            elif isinstance(record, MailSendRecord):
                k = 'send_mails'
            elif isinstance(record, MailMessageId):
                k = 'message_ids'
            elif isinstance(record, MailRemoved):
                k = 'removed'
            elif isinstance(record, MailDeferredRecord):
                k = 'deferred_mails'

            if k is None or k not in insert_datas:
                continue

            if log_day_date not in insert_datas[k]:
                insert_datas[k][log_day_date] = []

            insert_datas[k][log_day_date].append(record.to_dict())

            # save to database
            if len(insert_datas[k][log_day_date]) == 5000:
                with maillog_db_query(k, log_day_date) as query:
                    if k == 'send_mails':
                        query.duplicate({
                            'status': 'case when excluded.log_time > log_time then excluded.status else status end',
                            'delay': 'case when excluded.log_time > log_time then excluded.delay else delay end',
                            'delays': 'case when excluded.log_time > log_time then excluded.delays else delays end',
                            'dsn': 'case when excluded.log_time > log_time then excluded.dsn else dsn end',
                            'relay': 'case when excluded.log_time > log_time then excluded.relay else relay end',
                            'description': 'case when excluded.log_time > log_time then excluded.description else description end',
                            'log_time': 'case when excluded.log_time > log_time then excluded.log_time else log_time end',
                        }).insert_all(insert_datas[k][log_day_date])
                    else:
                        query.insert_all(insert_datas[k][log_day_date], option='ignore')

                insert_datas[k][log_day_date].clear()

                # update last_maillog_time
                if auto_update_maillog_time:
                    last_maillog_time(latest_log_time)

        # save to database
        for k, insert_data_lst in insert_datas.items():
            for log_day_date, insert_data in insert_data_lst.items():
                if len(insert_data) > 0:
                    with maillog_db_query(k, log_day_date) as query:
                        query.insert_all(insert_data, option='ignore')
                    insert_data.clear()

                    # update last_maillog_time
                    if auto_update_maillog_time:
                        last_maillog_time(latest_log_time)

        # update last_maillog_time
        if auto_update_maillog_time:
            last_maillog_time(latest_log_time)

        return latest_log_time


# scan all maillogs to initialize databases
def init_maillog_databases():
    if last_maillog_time() > 0:
        logging.debug('maillog databases is initialized, do not initialize again.')
        return

    start_time = time.time()

    maillog_name = os.path.basename(default_maillog_path)
    exts = ['', '.1', '.2.gz', '.3.gz', '.4.gz']

    for maillog_path in map(lambda x: '/var/log/{}{}'.format(maillog_name, x), exts):
        start_time_n = time.time()

        logging.debug('scanning {}'.format(maillog_path))
        if not os.path.exists(maillog_path):
            continue

        analysis_and_save_to_database(MaillogStat(maillog_path))

        logging.debug('cost time: {}ms'.format(int((time.time() - start_time_n) * 1000)))

    logging.debug('cost time: {}ms'.format(int((time.time() - start_time) * 1000)))


def encrypt(data: typing.Dict) -> str:
    data_json = json.dumps(data, ensure_ascii=True)
    key = public.GetRandomString(16).encode('utf-8')
    iv = public.GetRandomString(16).encode('utf-8')
    aes = AES.new(key, AES.MODE_CBC, iv)
    data_aes = aes.encrypt(public.pkcs7_padding(data_json.encode('utf-8'), 16))
    keyiv = b''
    for i in range(32):
        j = int(i / 2)
        if i % 2 == 0:
            keyiv += key[j:j+1]
        else:
            keyiv += iv[j:j+1]
    data_aes = keyiv[:16] + data_aes + keyiv[16:]
    return base64.urlsafe_b64encode(data_aes).decode('utf-8').strip('=')


def decrypt(data: str) -> typing.Optional[typing.Dict]:
    try:
        data_length = len(data)
        amount_to_pad = 4 - (data_length % 4)
        if amount_to_pad > 0:
            data += '=' * amount_to_pad
        data_aes = base64.urlsafe_b64decode(data.encode('utf-8'))
        keyiv = data_aes[:16] + data_aes[-16:]
        key = b''
        iv = b''
        for i in range(32):
            if i % 2 == 0:
                key += keyiv[i:i+1]
            else:
                iv += keyiv[i:i+1]
        aes = AES.new(key, AES.MODE_CBC, iv)
        data_json = public.pkcs7_unpadding(aes.decrypt(data_aes[16:-16]), 16).decode('utf-8')
        return json.loads(data_json)
    except:
        return None


def campaign_event_handler(enc_str: str):
    data = decrypt(enc_str)

    if data is None:
        return public.lang('invalid data')

    try:
        public.to_dict_obj(data).validate([
            Param('type').Require().String('in', ['open', 'click']),
            Param('campaign_id').Require().Integer('>', 0).Filter(int),
            Param('recipient').Require().Email(),
            Param('message_id').Require(),
            Param('url').Url(),
        ])
    except:
        return public.lang('invalid data -2')

    postfix_message_id = search_postfix_message_id_by_message_id(data['message_id'])

    if postfix_message_id is None:
        postfix_message_id = ''

    today_date = datetime.now().strftime('%Y%m%d')

    if data['type'] == 'open':
        with maillog_db_query('opened', today_date) as query:
            query.insert({
                'campaign_id': data['campaign_id'],
                'log_time': int(time.time()),
                'recipient': data['recipient'],
                'message_id': data['message_id'],
                'postfix_message_id': postfix_message_id,
            })

        img = Image.new('RGB', (1, 1), (0, 0, 0, 0))
        img_bs = io.BytesIO()
        img.save(img_bs, format='PNG')
        img_bs.seek(0)

        return Response(img_bs, mimetype='image/png')

    elif data['type'] == 'click':
        with maillog_db_query('clicked', today_date) as query:
            query.insert({
                'campaign_id': data['campaign_id'],
                'log_time': int(time.time()),
                'recipient': data['recipient'],
                'message_id': data['message_id'],
                'postfix_message_id': postfix_message_id,
                'url': data['url'],
            })

        return redirect(data['url'])

    return public.lang('success')


class MailTracker:
    __href_pattern = re.compile(r'href\s*=\s*"([^"]+)"')

    def __init__(self, mail_html: str, campaign_id: int, message_id: str, recipient: str, base_url: str):
        self.__original_mail_html = mail_html
        self.__modified = False
        self.__mail_html = mail_html
        self.__campaign_id = campaign_id
        self.__message_id = message_id
        self.__recipient = recipient
        self.__base_url = '{}/v2/pmta'.format(base_url.strip('/'))

    def track_links(self):
        self.__mail_html = self.__href_pattern.sub(self.__repl_href, self.__mail_html)
        self.__modified = True

    def __repl_href(self, m) -> str:
        # skip if href is not url
        try:
            url = urlparse(m.group(1))
            if url.scheme == '' or url.netloc == '':
                return m.group(0)
        except:
            return m.group(0)

        return 'href="{}"'.format(self.get_tracking_url(m.group(1)))

    def get_tracking_url(self, url: str) -> str:
        return '{}/{}'.format(self.__base_url, encrypt({
            'type': 'click',
            'campaign_id': self.__campaign_id,
            'recipient': self.__recipient,
            'message_id': self.__message_id,
            'url': url,
        }))

    def append_tracking_pixel(self):
        if self.__mail_html.find('</body>') > -1:
            self.__mail_html = self.__mail_html.replace('</body>', '<img src="{}" style="display:none" />'.format(self.get_tracking_pixel()), 1)
            self.__modified = True
            return

        if self.__mail_html.find('</html>') > -1:
            self.__mail_html = self.__mail_html.replace('</html>', '<img src="{}" style="display:none" /></html>'.format(self.get_tracking_pixel()), 1)
            self.__modified = True
            return

        self.__mail_html += '<img src="{}" style="display:none" />'.format(self.get_tracking_pixel())
        self.__modified = True

    def get_tracking_pixel(self) -> str:
        return '{}/{}'.format(self.__base_url, encrypt({
            'type': 'open',
            'campaign_id': self.__campaign_id,
            'recipient': self.__recipient,
            'message_id': self.__message_id,
        }))

    def is_modified(self) -> bool:
        return self.__modified

    def get_original_html(self) -> str:
        return self.__original_mail_html

    def get_html(self) -> str:
        return self.__mail_html
