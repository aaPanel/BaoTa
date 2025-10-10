# -*- coding: utf-8 -*-
# 批量发邮件

import re, json, os, sys, time, socket, requests, glob,shutil
import subprocess
import dns.resolver
import argparse
import zipfile

# import datetime

sys.path.append("class/")
from mod.base import public_aap as public

# from public.hook_import import hook_import
# hook_import()

# from public.authorization import only_pro_members

if sys.version_info[0] == 3:
    from importlib import reload

try:
    from dateutil.parser import parse
except:
    public.ExecShell("btpip install python-dateutil==2.9.0.post0")
    from dateutil.parser import parse

try:
    import dns.resolver
except:
    if os.path.exists('/www/server/panel/pyenv'):
        public.ExecShell('/www/server/panel/pyenv/bin/pip install dnspython')
    else:
        public.ExecShell('pip install dnspython')
    import dns.resolver
from mailModel.base import Base
from mailModel.mainModel import SendMail
import math
try:
    import jwt
except:
    public.ExecShell('btpip install pyjwt')
    import jwt
from datetime import datetime, timedelta
from email.utils import make_msgid

class main(Base):

    postfix_main_cf = "/etc/postfix/main.cf"
    domain_restrictions = '/etc/postfix/sender_black'
    plugin_data = f'/www/server/panel/plugin/mail_sys/data'  # 插件数据目录
    blcheck_count = f'/www/server/panel/plugin/mail_sys/data/blcheck.json'  # 统计各个域名黑名单情况
    CONF_DNS_TRIES = 2
    CONF_DNS_DURATION = 6
    CONF_BLACKLISTS = [
            "bl.spamcop.net",
            "dnsbl.sorbs.net",
            "multi.surbl.org",
            "http.dnsbl.sorbs.net",
            "misc.dnsbl.sorbs.net",
            "socks.dnsbl.sorbs.net",
            "web.dnsbl.sorbs.net",
            "rbl.spamlab.com",
            "cbl.anti-spam.org.cn",
            "httpbl.abuse.ch",
            "virbl.bit.nl",
            "dsn.rfc-ignorant.org",
            "opm.tornevall.org",
            "multi.surbl.org",
            "relays.mail-abuse.org",
            "rbl-plus.mail-abuse.org",
            "rbl.interserver.net",
            "dul.dnsbl.sorbs.net",
            "smtp.dnsbl.sorbs.net",
            "spam.dnsbl.sorbs.net",
            "zombie.dnsbl.sorbs.net",
            "drone.abuse.ch",
            "rbl.suresupport.com",
            "spamguard.leadmon.net",
            "netblock.pedantic.org",
            "blackholes.mail-abuse.org",
            "dnsbl.dronebl.org",
            "query.senderbase.org",
            "csi.cloudmark.com",
            "0spam-killlist.fusionzero.com",
            "access.redhawk.org",
            "all.rbl.jp",
            "all.spam-rbl.fr",
            "all.spamrats.com",
            "aspews.ext.sorbs.net",
            "b.barracudacentral.org",
            "backscatter.spameatingmonkey.net",
            "badnets.spameatingmonkey.net",
            "bb.barracudacentral.org",
            "bl.drmx.org",
            "bl.konstant.no",
            "bl.nszones.com",
            "bl.spamcannibal.org",
            "bl.spameatingmonkey.net",
            "bl.spamstinks.com",
            "black.junkemailfilter.com",
            "blackholes.five-ten-sg.com",
            "blacklist.sci.kun.nl",
            "blacklist.woody.ch",
            "bogons.cymru.com",
            "bsb.empty.us",
            "bsb.spamlookup.net",
            "cart00ney.surriel.com",
            "cbl.abuseat.org",
            "cbl.anti-spam.org.cn",
            "cblless.anti-spam.org.cn",
            "cblplus.anti-spam.org.cn",
            "cdl.anti-spam.org.cn",
            "cidr.bl.mcafee.com",
            "combined.rbl.msrbl.net",
            "db.wpbl.info",
            "dev.null.dk",
            "dialups.visi.com",
            "dnsbl-0.uceprotect.net",
            "dnsbl-1.uceprotect.net",
            "dnsbl-2.uceprotect.net",
            "dnsbl-3.uceprotect.net",
            "dnsbl.anticaptcha.net",
            "dnsbl.aspnet.hu",
            "dnsbl.inps.de",
            "dnsbl.justspam.org",
            "dnsbl.kempt.net",
            "dnsbl.madavi.de",
            "dnsbl.rizon.net",
            "dnsbl.rv-soft.info",
            "dnsbl.rymsho.ru",
            "dnsbl.zapbl.net",
            "dnsrbl.swinog.ch",
            "dul.pacifier.net",
            "dyn.nszones.com",
            "dyna.spamrats.com",
            "fnrbl.fast.net",
            "fresh.spameatingmonkey.net",
            "hostkarma.junkemailfilter.com",
            "images.rbl.msrbl.net",
            "ips.backscatterer.org",
            "ix.dnsbl.manitu.net",
            "korea.services.net",
            "l2.bbfh.ext.sorbs.net",
            "l3.bbfh.ext.sorbs.net",
            "l4.bbfh.ext.sorbs.net",
            "list.bbfh.org",
            "list.blogspambl.com",
            "mail-abuse.blacklist.jippg.org",
            "netbl.spameatingmonkey.net",
            "netscan.rbl.blockedservers.com",
            "no-more-funn.moensted.dk",
            "noptr.spamrats.com",
            "orvedb.aupads.org",
            "pbl.spamhaus.org",
            "phishing.rbl.msrbl.net",
            "pofon.foobar.hu",
            "psbl.surriel.com",
            "rbl.abuse.ro",
            "rbl.blockedservers.com",
            "rbl.dns-servicios.com",
            "rbl.efnet.org",
            "rbl.efnetrbl.org",
            "rbl.iprange.net",
            "rbl.schulte.org",
            "rbl.talkactive.net",
            "rbl2.triumf.ca",
            "rsbl.aupads.org",
            "sbl-xbl.spamhaus.org",
            "sbl.nszones.com",
            "sbl.spamhaus.org",
            "short.rbl.jp",
            "spam.dnsbl.anonmails.de",
            "spam.pedantic.org",
            "spam.rbl.blockedservers.com",
            "spam.rbl.msrbl.net",
            "spam.spamrats.com",
            "spamrbl.imp.ch",
            "spamsources.fabel.dk",
            "st.technovision.dk",
            "tor.dan.me.uk",
            "tor.dnsbl.sectoor.de",
            "tor.efnet.org",
            "torexit.dan.me.uk",
            "truncate.gbudb.net",
            "ubl.unsubscore.com",
            "uribl.spameatingmonkey.net",
            "urired.spameatingmonkey.net",
            "virbl.dnsbl.bit.nl",
            "virus.rbl.jp",
            "virus.rbl.msrbl.net",
            "vote.drbl.caravan.ru",
            "vote.drbl.gremlin.ru",
            "web.rbl.msrbl.net",
            "work.drbl.caravan.ru",
            "work.drbl.gremlin.ru",
            "wormrbl.imp.ch",
            "xbl.spamhaus.org",
            "zen.spamhaus.org",
        ]
    # 正则表达式
    REGEX_IP = r'^\b(?:\d{1,3}\.){3}\d{1,3}\b$'
    def __init__(self):
        super().__init__()
        self.in_bulk_path = '/www/server/panel/data/mail/in_bulk'
        if not os.path.exists(self.in_bulk_path):
            os.mkdir(self.in_bulk_path)
        # 邮局日志
        self.maillog_path = '/var/log/maillog'
        if "ubuntu" in public.get_linux_distribution().lower():
            self.maillog_path = '/var/log/mail.log'
        # 群发任务  收件人发送记录
        self.sent_recipient_path = '/www/server/panel/data/mail/in_bulk/recipient/sent_recipient'
        if not os.path.exists(self.sent_recipient_path):
            os.makedirs(self.sent_recipient_path)
        # 群发 收件人数量记录 取消记录
        # self.recipient_count_path = '/www/server/panel/data/mail/in_bulk/recipient/recipient_count'
        # 数据库文件与名称
        self.db_files = {
            'postfixadmin': '/www/vmail/postfixadmin.db',
            'postfixmaillog': '/www/vmail/postfixmaillog.db',
            'mail_unsubscribe': '/www/vmail/mail_unsubscribe.db',
            'abnormal_recipient': '/www/vmail/abnormal_recipient.db'
        }
        if os.path.exists('/www/vmail/'):
            self.check_table_column()
            # 检查昨日提交
            self.get_yesterday_count()

        # 域名已经进了黑名单  关闭黑名单
        self.restored_domain_send()
        self.check_new_unsubscribe()

    def restored_domain_send(self):
        restored_domain = '/www/server/panel/plugin/mail_sys/data/restored_domain_send.pl'
        if os.path.exists(restored_domain):
            return
        if self._check_sender_domain_restrictions():
            self._domain_restrictions_switch(False)
        # 添加标记
        public.writeFile(restored_domain, '1')

    def check_field_exists(self,db_obj,table_name, field_name):
        """
        @name 检查表字段是否存在
        @param db_obj 数据库对象
        @param table_name 表名
        @param field_name 要检查的字段
        """
        try:
            res = db_obj.query("PRAGMA table_info({})".format(table_name))
            for val in res:
                if field_name == val[1]:
                    return True
        except:pass
        return False

    def check_table_column(self,):
        """
        @name 检查数据库表或字段是否完整
        """
        # 新增3个表  批量发件用
        # 邮件模版表
        sql1 = '''CREATE TABLE IF NOT EXISTS `temp_email` (
          `id` INTEGER  PRIMARY KEY AUTOINCREMENT,        
          `name` varchar(255) NULL,         -- 邮件名 有模版时为模版名
          `type` tinyint(1) NOT NULL DEFAULT 1,  -- 拖拽生成1    上传0
          `content` text NOT NULL,          -- 邮件正文 路径
          `render` text NOT NULL,   -- html渲染数据
          `created` INTEGER NOT NULL,  
          `modified` INTEGER NOT NULL,
          `is_temp` tinyint(1) NOT NULL DEFAULT 0  -- 是否是模版
          );'''
        with self.M("") as obj:
            obj.execute(sql1, ())


        # 任务表
        sql2 = '''CREATE TABLE IF NOT EXISTS `email_task` (
          `id` INTEGER  PRIMARY KEY AUTOINCREMENT,    
          `task_name` varchar(255) NOT NULL,        -- 任务名
          `addresser` varchar(320) NOT NULL,        -- 发件人
          `recipient_count` int NOT NULL,           -- 收件人数量
          `task_process` tinyint NOT NULL,     -- 任务进程  0待执行   1执行中  2 已完成
          `pause` tinyint NOT NULL,      -- 暂停状态  1 暂停中     0 未暂停     执行中的任务才能暂停
          `temp_id` INTEGER NOT NULL,          -- 邮件对应id
          `is_record` INTEGER NOT NULL DEFAULT 0,        -- 是否记录到发件箱
          `unsubscribe` INTEGER NOT NULL DEFAULT 0,      -- 是否增加退订按钮   0 没有   1 增加退订按钮
          `threads` INTEGER NOT NULL DEFAULT 0,          -- 线程数量 控制发送线程数 0时自动控制线程   0~10
          `etypes` varchar(320) NOT NULL DEFAULT '1',          -- 邮件类型id 默认为1  多个
          `created` INTEGER NOT NULL,
          `modified` INTEGER NOT NULL,
          `remark` text,           -- 备注
          `start_time` INTEGER NOT NULL DEFAULT 0,            -- 任务开始时间
          `subject` text NULL,          -- 邮件主题   改task存  可空
          `full_name` varchar(255),  -- 新发件人名    改task存  可空
          `recipient` text NOT NULL,        -- 收件人路径 改task存
          `active` tinyint(1) NOT NULL DEFAULT 0    --  预留字段
          );'''
        with self.M("") as obj:
            obj.execute(sql2, ())


        # 发送详情表 现改为独立数据库

        sql3 = '''CREATE TABLE IF NOT EXISTS `task_count` (
          `id` INTEGER  PRIMARY KEY AUTOINCREMENT,    
          `task_id` INTEGER NOT NULL,                   -- 所属任务编号
          `recipient` varchar(320) NOT NULL,            -- 收件人
          `delay` varchar(320) NOT NULL,            -- 延时
          `delays` varchar(320) NOT NULL,            -- 各阶段延时
          `dsn` varchar(320) NOT NULL,            -- dsn
          `relay` text NOT NULL,            -- 中继服务器
          `domain` varchar(320) NOT NULL,               -- 域名
          `status` varchar(255) NOT NULL,               -- 错误状态
          `err_info` text NOT NULL,                      -- 错误详情
          `created` INTEGER NOT NULL DEFAULT 0 
          );'''
        with self.M("") as obj:
            obj.execute(sql3, ())

        # 邮件模版增加渲染数据地址
        with self.M("temp_email") as obj:
            if not self.check_field_exists(obj, "temp_email", "render"):
                obj.execute('ALTER TABLE `temp_email` ADD COLUMN `render` text NOT NULL DEFAULT "";')
            if not self.check_field_exists(obj, "temp_email", "type"):
                obj.execute('ALTER TABLE `temp_email` ADD COLUMN `type` tinyint(1) NOT NULL DEFAULT 1;')
            # 删除模版表字段
            with self.M("temp_email") as obj:
                if self.check_field_exists(obj, "temp_email", "addresser"):
                    obj.execute('ALTER TABLE `temp_email` DROP COLUMN `addresser`;')
                if self.check_field_exists(obj, "temp_email", "recipient"):
                    obj.execute('ALTER TABLE `temp_email` DROP COLUMN `recipient`;')
                if self.check_field_exists(obj, "temp_email", "subject"):
                    obj.execute('ALTER TABLE `temp_email` DROP COLUMN `subject`;')
                if self.check_field_exists(obj, "temp_email", "subtype"):
                    obj.execute('ALTER TABLE `temp_email` DROP COLUMN `subtype`;')
        # 群发任务表
        with self.M("email_task") as obj:
            if not self.check_field_exists(obj, "email_task", "unsubscribe"):
                obj.execute('ALTER TABLE `email_task` ADD COLUMN `unsubscribe` INTEGER NOT NULL DEFAULT 0;')

            if not self.check_field_exists(obj, "email_task", "threads"):
                obj.execute('ALTER TABLE `email_task` ADD COLUMN `threads` INTEGER NOT NULL DEFAULT 0;')
            # 邮件类型
            # if not self.check_field_exists(obj, "email_task", "etype"):
            #     obj.execute('ALTER TABLE `email_task` ADD COLUMN `etype` INTEGER NOT NULL DEFAULT 1;')
            # 群发开始时间
            if not self.check_field_exists(obj, "email_task", "start_time"):
                obj.execute('ALTER TABLE `email_task` ADD COLUMN `start_time` INTEGER NOT NULL DEFAULT 0;')
            if not self.check_field_exists(obj, "email_task", "remark"):
                obj.execute('ALTER TABLE `email_task` ADD COLUMN `remark` text;')

            # if self.check_field_exists(obj, "email_task", "etypes"):
            #     obj.execute('ALTER TABLE `email_task` DROP COLUMN `etypes`;')

            # 邮件类型  多个  1,2,3
            if not self.check_field_exists(obj, "email_task", "etypes"):
                obj.execute('ALTER TABLE `email_task` ADD COLUMN `etypes` varchar(320) NOT NULL DEFAULT "1";')

            if not self.check_field_exists(obj, "email_task", "subject"):
                obj.execute('ALTER TABLE `email_task` ADD COLUMN `subject` text;')

            if not self.check_field_exists(obj, "email_task", "full_name"):
                obj.execute('ALTER TABLE `email_task` ADD COLUMN `full_name` varchar(255) DEFAULT "";')


            if not self.check_field_exists(obj, "email_task", "recipient"):
                obj.execute('ALTER TABLE `email_task` ADD COLUMN `recipient` text NOT NULL DEFAULT "";')

            # if not self.check_field_exists(obj, "email_task", "track_open"):
            #     obj.execute('ALTER TABLE `email_task` ADD COLUMN `track_open` INTEGER NOT NULL DEFAULT 0;')
            #
            # if not self.check_field_exists(obj, "email_task", "track_click"):
            #     obj.execute('ALTER TABLE `email_task` ADD COLUMN `track_click` INTEGER NOT NULL DEFAULT 0;')

        with self.M("task_count") as obj:
            if not self.check_field_exists(obj, "task_count", "created"):
                obj.execute('ALTER TABLE `task_count` ADD COLUMN `created` INTEGER NOT NULL DEFAULT 0;')

        # 退订表增加任务id  退订可关联id
        with self.MD("mail_unsubscribe", "mail_unsubscribe") as obj:
            if not self.check_field_exists(obj, "mail_unsubscribe", "task_id"):
                obj.execute('ALTER TABLE `mail_unsubscribe` ADD COLUMN `task_id` INTEGER  DEFAULT 0;')
    def MD(self, table_name, db_key):
        if db_key not in self.db_files:
            raise ValueError(f"Unknown database key: {db_key}")
        import db
        sql = db.Sql()
        sql._Sql__DB_FILE = self.db_files[db_key]
        sql._Sql__encrypt_keys = []
        return sql.table(table_name)

    # 任务完成后才会新建任务
    def check_task_status(self, args):
        '''
        执行发送邮件的定时任务
        :param
        :return:
        '''
        try:
            print("|-Prepare to execute the send task")
            # public.print_log("执行发送任务")
            # task_process  0待执行   1执行中  2 已完成
            with self.M("email_task") as obj:
                exits_task = obj.where('task_process =? and pause =?', (1, 0)).count()
                process0_task = obj.where('task_process =? and pause =?', (0, 0)).select()

            if exits_task:  # 存在执行中的任务  跳过
                # public.print_log("|-已有任务正在发送中 ")
                print("|-An existing task is being sent ")
                return False
            if not process0_task:  # 不存在待执行的 跳过
                # public.print_log("|-没有需要执行的任务 ")
                print("|-There are no tasks to execute")
                return False
            # public.print_log(f" 发件状态0  未暂停 -- {process0_task}")
            cur_time = int(time.time())
            send_task_ok = []   # 满足执行时间的任务
            for i in process0_task:
                # public.print_log(f" 发件{i['start_time']}  当前{cur_time} ")
                if i['start_time'] <= cur_time:
                    send_task_ok.append(i)

            # 存在且发件时间最近的 先发送
            if send_task_ok:
                if len(send_task_ok) == 1:
                    task_info = send_task_ok[0]
                else:
                    task_info = min(send_task_ok, key=lambda x: x['start_time'])
            else:
                # public.print_log("|-没有到达发件时间的任务 ")
                print("|-No task has reached its dispatch time")
                return False



            # task_info = self.M('email_task').order('created desc').find()


            start_mark = '/www/server/panel/plugin/mail_sys/start_Task.pl'  # 无ptr记录每日发件数
            SendTaskId = '/www/server/panel/plugin/mail_sys/SendTaskid.pl'
            _, domain_ = task_info['addresser'].split('@')
            # todo ptr临时改1
            is_ptr = self._check_ptr_domain(domain_)
            # is_ptr = 1

            # 查看任务是否已开始
            if os.path.exists(start_mark):
                # 新的一天
                # public.print_log("|-执行一天后 {}".format(int(public.readFile(start_mark)) + 86400))
                if int(public.readFile(start_mark)) + 86400 < cur_time:
                    # public.print_log("|-时间未超出 清掉当天配额")
                    # 重置时间
                    public.writeFile(start_mark, str(cur_time))
                    # 清空统计
                    count_sent = '/www/server/panel/plugin/mail_sys/count_sent_domain.json'
                    os.remove(count_sent)
                # 当天 已经开始过 如果超额 跳过
                else:
                    # 无ptr记录 当天没有发件机会 跳过
                    if not is_ptr:
                        # 判断是否有配额
                        # 查看当前domain已发送数量
                        count_sent = '/www/server/panel/plugin/mail_sys/count_sent_domain.json'
                        count = 0
                        if os.path.exists(count_sent):
                            data = public.readFile(count_sent)
                            data = json.loads(data)
                            count = sum(domain_data for domain_data in data.values())
                        # public.print_log(" 查看当前domain是否有发送额度--{}".format(count))
                        # 无发送额度
                        if count > 5000:
                            print("|-The execution quota for the day has been used up")
                            # public.print_log("|-The execution quota for the day has been used up")
                            return False

                public.writeFile(SendTaskId, str(task_info['id']))
            else:
                timestamp = str(int(time.time()))
                public.writeFile(start_mark, timestamp)
                # 记录当前处理的任务id
                public.writeFile(SendTaskId, str(task_info['id']))
                # public.print_log("|-记录文件处理id  {}".format(task_info['id']))

            # 邮件相关内容
            email_info = self.M('temp_email').where('id=?', task_info['temp_id']).find()
            content_path = email_info['content']

            recipient_path = task_info['recipient']
            addresser = task_info['addresser']
            subject = task_info.get('subject', '')
            # 优先使用用户新建的名字
            full_name = task_info.get('full_name', '')

            try:
                content_detail = public.readFile(content_path)
                content_detail = json.loads(content_detail)
            except:
                # 直接上传的文件不用
                content_detail = public.readFile(content_path)

            task_id = task_info['id']
            unsubscribe = task_info['unsubscribe']

            threads = task_info['threads']
            etypes = task_info['etypes']

            # 收件人
            recipient_analysis = {}
            try:
                data = public.readFile(recipient_path)
                recipient_analysis = json.loads(data)
            except:
                print(public.get_error_info())
                public.print_log(public.get_error_info())
                # return public.returnMsg(False, 'Abnormal or malformed file contents')

            # 发件人
            data = self.M('mailbox').where('username=?', addresser).field('password_encode,full_name').find()
            password = self._decode(data['password_encode'])
            # public.print_log("批量发件1  用户信息  {}--({})".format(addresser, password))
            if not full_name:
                full_name = data['full_name']

            other_today = {
                'gmail.com': {"count": 0, "info": []},
                'googlemail.com': {"count": 0, "info": []},
                'hotmail.com': {"count": 0, "info": []},
                'outlook.com': {"count": 0, "info": []},
                'yahoo.com': {"count": 0, "info": []},
                'icloud.com': {"count": 0, "info": []},
                'other': {"count": 0, "info": []},
            }
            # 批量发件的内容是否要保存到发件箱  0不保存  1保存
            is_record = task_info['is_record']
            # # 查询群发任务的邮件类型 todo 改多类型
            # with self.M('mail_type') as obj:
            #     mail_type = obj.where('id=?', etype_id).getField('mail_type')
            # public.print_log("|-准备执行的任务 id   {} ".format(str(task_info['id'])))
            args1 = public.dict_obj()
            args1.addresser = addresser
            args1.password = password
            args1.full_name = full_name
            args1.subject = subject
            args1.content_detail = content_detail
            args1.is_record = is_record
            args1.unsubscribe = unsubscribe
            args1.task_id = task_id
            args1.etypes = etypes

            # 记录所有线程
            p_list = []
            if not is_ptr:
                # public.print_log("无ptr_________________________________")
                # 今日能发送的
                send_today = {
                    'gmail.com': {"count": 0, "info": []},
                    'googlemail.com': {"count": 0, "info": []},
                    'hotmail.com': {"count": 0, "info": []},
                    'outlook.com': {"count": 0, "info": []},
                    'yahoo.com': {"count": 0, "info": []},
                    'icloud.com': {"count": 0, "info": []},
                    'other': {"count": 0, "info": []},
                }
                # 循环调用发件
                for domain, details in recipient_analysis.items():
                    today_count = 0
                    # 查看当前domain已发送数量
                    count = self._get_count_limit(domain)
                    # public.print_log(" 查看当前domain是否有发送额度--{}".format(count))
                    # 无发送额度
                    if count > 5000:
                        # 记录未发送状态 第二天发送
                        today_count = 0
                    # 需要发送的+已发送>额度
                    elif details['count'] + count > 5000:
                        # 当日可发送数量  额度-已发送  5-3=2   有3
                        today_count = 5000 - count
                    else:
                        today_count = 5000

                    if today_count != 0:
                        if details['count'] < today_count:
                            send_today[domain] = details
                            other_today[domain] = {"count": 0, "info": []}
                        else:
                            send_today[domain] = {"count": len(details[:today_count]),
                                                  "info": details[:today_count]}  # 取前n个元素
                            other_today[domain] = {"count": len(details[today_count:]), "info": details[today_count:]}
                    else:
                        send_today[domain] = {"count": 0, "info": []}
                        other_today[domain] = details

                # public.print_log("批量发件1  准备发件 无ptr--{}".format(send_today))
                try:
                    import random
                    listall = []
                    for domain, detail in send_today.items():
                        listall += detail['info']
                    if len(listall) == 0:
                        # public.print_log("准备发件2 空 退出_")
                        with self.M("email_task") as obj:
                            obj.where('id=?', task_info['id']).update({'task_process': 2})
                        return
                    random.shuffle(listall)
                    # public.print_log(" 无ptr 循环发送--{}".format(len(listall))
                    # 更新今天发送后的
                    public.writeFile(recipient_path, json.dumps(other_today))
                    # 无ptr 默认线程1

                    args1.listall = listall
                    args1.threads = 1
                    # p1_list = self.send_emails_split(listall, addresser, password, full_name, subject, content_detail, is_record, unsubscribe, 1, task_id, etypes)
                    p1_list = self.send_emails_split(args1)
                    p_list.extend(p1_list)
                except Exception as ex:
                    print(public.get_error_info())
                    public.print_log(public.get_error_info())
                    # public.print_log("Send in installments - error: {}".format(ex))
                    # 删除开始标志
                    if os.path.exists(start_mark):
                        os.remove(start_mark)
                    print("|-Installment delivery failed - error: {}".format(ex))
                    # public.print_log("|-分期失败 - error: {}".format(ex))
                    return False

            else:
                # public.print_log("准备发件2  全部发送  ____________________________________________")
                # 准备发件 任务状态改为执行中  有ptr记录可以一次发完
                with self.M("email_task") as obj:
                    obj.where('id=?', task_info['id']).update({'task_process': 1})
                try:
                    import random
                    listall = []
                    for domain, detail in recipient_analysis.items():
                        listall += detail['info']
                    if len(listall) == 0:
                        # public.print_log("准备发件2 空 退出_")
                        with self.M("email_task") as obj:
                            obj.where('id=?', task_info['id']).update({'task_process': 2})

                        return
                    # 打乱每个列表
                    random.shuffle(listall)

                    # 清空收件人记录
                    public.writeFile(recipient_path, json.dumps(other_today))

                    args1.listall = listall
                    args1.threads = int(threads)

                    # p1_list = self.send_emails_split(listall, addresser, password, full_name, subject, content_detail, is_record, unsubscribe, int(threads), task_id, etypes)
                    p1_list = self.send_emails_split(args1)
                    p_list.extend(p1_list)

                except Exception as ex:
                    print(public.get_error_info())
                    public.print_log(public.get_error_info())
                    # public.print_log("Send - error: {}".format(ex))
                    # 删除开始标志
                    if os.path.exists(start_mark):
                        os.remove(start_mark)
                    # 执行中修改为待执行
                    with self.M("email_task") as obj:
                        obj.where('id=?', task_info['id']).update({'task_process': 0})

                    print("|-Failed to send - error: {}".format(ex))
                    # public.print_log("Failed to send - error: {}".format(ex))
                    return False

            # public.print_log("等线程 {}".format(p_list))
            # 等线程结束
            for p in p_list:
                p.join()


            other_todays = {}
            try:
                data = public.readFile(recipient_path)
                other_todays = json.loads(data)
            except:
                print(public.get_error_info())
                public.print_log(public.get_error_info())

            if all(value['count'] == 0 for value in other_todays.values()):
                # 任务状态改已完成
                with self.M("email_task") as obj:
                    obj.where('id=?', task_info['id']).update({'task_process': 2})
                # public.print_log("发完了 收工")
            else:
                # 执行中修改为待执行
                with self.M("email_task") as obj:
                    obj.where('id=?', task_info['id']).update({'task_process': 0})
                # public.print_log("没发完 99999 {}".format(other_todays))
            return public.returnMsg(True, '已完成发送任务')
        except:
            print(public.get_error_info())
            public.print_log(public.get_error_info())

    # 大批量邮件拆分发送  订阅 分线程
    # def send_emails_split(self, listall, addresser, password, full_name, subject, content_detail, is_record, unsubscribe, threads, task_id, etypes):
    def send_emails_split(self, args):
        # info = detail["info"]
        task_id = args.task_id
        listall = args.listall
        unsubscribe = args.unsubscribe
        threads = args.threads
        addresser = args.addresser
        password = args.password
        full_name = args.full_name
        subject = args.subject
        content_detail = args.content_detail
        is_record = args.is_record
        etypes = args.etypes
        # public.print_log("|-准备执行的任务 id   {} ".format(task_id))
        total_recipients = len(listall)
        if total_recipients > 10000:
            max_batches = int(threads)
            if max_batches == 0:
                # 根据数量定  大于50000  5线程    否则3线程
                if total_recipients > 50000:
                    max_batches = 5
                else:
                    max_batches = 3
        else:
            # 1w以内单线程
            max_batches = 1

        # # 订阅 线程翻倍
        # if unsubscribe:
        #     max_batches = max_batches*2

        # 计算每个线程要发送的数量
        batch_size = math.ceil(total_recipients / max_batches)

        # num_batches = math.ceil(total_recipients / batch_size)
        # public.print_log("batch_size--每个线程要发{}, num_batches--线程数{}".format(batch_size,num_batches))
        p_all = []

        for i in range(max_batches):
            start_idx = i * batch_size
            end_idx = min(total_recipients, (i + 1) * batch_size)
            batch_recipients = listall[start_idx:end_idx]
            # public.print_log("分批发 线程--{}".format(len(batch_recipients)))
            # 用线程发邮件
            recipients = {"count": len(batch_recipients), "info": batch_recipients}
            args.recipients = recipients
            # 判断订阅
            if unsubscribe:
                # 如果是订阅 线程翻倍

                p = self.run_thread(self._send_email_all_unsubscribe, (recipients, addresser, password, full_name, subject, content_detail, is_record, task_id, etypes))
                # p = self.run_thread(self._send_email_all_unsubscribe, args)
            else:

                p = self.run_thread(self._send_email_all, (recipients, addresser, password, full_name, subject, content_detail, is_record, task_id))
                # p = self.run_thread(self._send_email_all, args)

            p_all.append(p)

        return p_all

    def run_thread(self, fun, args=(), daemon=False):
        '''
            @name 使用线程执行指定方法
            @author hwliang<2020-10-27>
            @param fun {def} 函数对像
            @param args {tuple} 参数元组
            @param daemon {bool} 是否守护线程
            @return 线程
        '''
        import threading
        p = threading.Thread(target=fun, args=args)
        p.setDaemon(daemon)
        p.start()
        return p

    # 只根据上次时间和当前时间筛选日志  无上次时间 取开始时间
    def check_task_finish(self, args=None):
        '''
        发送完毕后 处理发送日志 定时任务
        :param
        :return:
        '''
        # 如果不存在处理中的任务 只有待执行和已结束(任务发完 没新任务)  考虑已结束任务的时间 距离当前十分钟以上 不处理

        # public.print_log("进入处理日志")
        LastTaskId = '/www/server/panel/plugin/mail_sys/LastTaskid.pl'
        SendTaskId = '/www/server/panel/plugin/mail_sys/SendTaskid.pl'
        if not os.path.exists(SendTaskId):
            print("|- There are no tasks to work on")
            # public.print_log("|-没有需要处理日志的任务 ")
            return False

        # 正在发送的任务id
        task_id = int(public.readFile(SendTaskId))
        cur_time = int(time.time())
        with self.M("email_task") as obj:
            exits_task = obj.where('task_process !=?', (0,)).select()   # 状态不是待执行的任务
            process1_task = obj.where('task_process =?', (1,)).count()   # 执行中的数量

            if not process1_task:  # 没有执行中的  都是未执行或执行完的
                if not obj.where('task_process !=?', (2,)).count():  # 没有待执行或执行中  删掉额度占用
                    path = '/www/server/panel/plugin/mail_sys/data/quota_occupation.json'
                    if os.path.exists(path):
                        os.remove(path)

                # 最后一个已完成的任务
                last_task = obj.order('created desc').where('task_process =?', (2,)).find()
                if cur_time-600 > last_task['created']:
                    if os.path.exists(LastTaskId):
                        os.remove(LastTaskId)
                    # public.print_log("|-最近一次已完成的任务也在十分钟前了 ")
                    print("|-There are no tasks to handle 1")
                    return False

        if not exits_task:  # 没有1,2  执行中或已完毕
            # public.print_log("|-没有执行中或已结束的任务(无日志处理)")
            print("|-There are no tasks to handle 2")
            return False
        ids = [i['id'] for i in exits_task]


        # 记录上次执行id  如果上次!= 这次  先执行上次  执行完毕更新为这次的id
        task_switch = False  # 是否处于新旧任务切换时
        if os.path.exists(LastTaskId):
            last_id = int(public.readFile(LastTaskId))
            if task_id != last_id:
                task_switch = True
                # 更新为当前正在执行的任务
                # public.print_log("写入LastTaskId 1  {}".format(task_id))
                public.writeFile(LastTaskId, str(task_id))
                # 最后处理一次上次任务 收尾
                task_id = last_id
        else:
            # 记录此次处理id
            # public.print_log("写入LastTaskId 2  {}".format(task_id))
            public.writeFile(LastTaskId, str(task_id))



        if task_id not in ids:
            # public.print_log("|-记录的id不在处理范围内(日志处理)")
            public.print_log("|-The id is not in the scope of processing")
            return False
        with self.M("email_task") as obj:
            # public.print_log(" 日志查库 id  {}".format(task_id))
            task_info = obj.where('id =?', (task_id,)).find()

        # 没有任务 可去
        if not task_info:
            print("|-There are currently no tasks")
            # public.print_log("任务id没查到")
            return False

        # task_id = task_info['id']
        # 错误日志路径
        error_log = "/www/server/panel/data/mail/in_bulk/errlog/task_{}.log".format(task_id)


        # 分析日志并记录
        self._mail_error_log(error_log, task_id)
        print("|-Logging completion")
        # 更新上次记录时间
        # public.writeFile(last_time, str(last_timestamp))

        # public.print_log("日志task_info   {}".format(task_info))
        # 任务已结束 或 上次处理id与正在发送的任务不一致   最后一次扫描
        if task_info['task_process'] == 2 or task_switch:
            # 更新处理标记

            # # 删标记  任务开始标记 删掉后不处理日志  删除容易出问题
            # if os.path.exists(SendTaskId):
            #     os.remove(SendTaskId)

            # # 删除任务占用的额度
            # self.del_quota_occupation(str(task_id))

            # 记录异常邮箱
            self.run_thread(self.handle_abnormal_recipient, (task_id,))

        print("|-The processing tag has been removed")
        # public.print_log("|- 分析完")
        return True

    def handle_abnormal_recipient(self, task_id):

        database_path = f'/www/vmail/bulk/task_{task_id}.db'
        # 本次任务的异常邮箱
        with public.S("task_count", database_path) as obj:
            # errlist = obj.where('code !=? OR status !=?', (250, 'sent')).select()
            errlist = obj.where('status !=?', ('sent',)).select()

        # 获取任务名
        with self.M('email_task') as obj:
            task_info = obj.where('id=?', task_id).field('temp_id,created,subject,created,remark').find()


        task_name = task_info.get('subject', '') + '_' + task_info.get('remark', '') + '_' + str(task_info['created'])
        # 有失败
        if errlist:
            err_recipient = [i['recipient'] for i in errlist]
            exist_recipient = []
            # 存在就更新
            with public.S("abnormal_recipient", '/www/vmail/abnormal_recipient.db') as obj1:
                existlist = obj1.where_in('recipient', err_recipient).select()
                # 更新
                if existlist:
                    exist_recipient = [i['recipient'] for i in existlist]
                    for i in existlist:
                        obj1.where('id=?', i['id']).update({'count': i['count'] + 1})

                # 插入  存在-更新 = 新增 插入增加  status, task_name
                insert_data = []
                for i in errlist:
                    if i['recipient'] not in exist_recipient:
                        insert_data.append({
                            "created": int(time.time()),
                            "recipient": i['recipient'],
                            "status": i['status'],
                            "task_name": task_name,
                            "count": 1,
                        })
                if insert_data:
                    aa = obj1.insert_all(insert_data, option='IGNORE')



    def _read_recipient_file(self,file_path):
        """读取收件人文件 兼容json和普通类型"""

        if file_path.endswith('.json'):
            try:
                emails = json.loads(public.readFile(file_path))
                return emails, None
            except Exception as e:
                return None, f'从文件读取json内容失败: {e}'
        else:
            try:
                with open(file_path, 'r') as file:
                    emails = file.read().splitlines()
                return emails, None
            except Exception as e:
                return None, f'从文件读取文本内容失败: {e}'

    # 导入收件人 todo 弃用 (改v2 )   改联系人导入
    def processing_recipient(self, args):
        '''
        导入收件人
        :param  file   etype(邮件类型   用于筛选退订用户)
        :return:
        '''
        args.file = args.get('file/s', '')

        if not os.path.exists("{}/recipient".format(self.in_bulk_path)):
            os.mkdir("{}/recipient".format(self.in_bulk_path))
        file_path = "{}/recipient/{}".format(self.in_bulk_path, args.file)

        if not args.file:
            return public.returnMsg(False, '参数错误')

        if not os.path.exists(file_path):
            return public.returnMsg(False, '文件不存在')
        emails = []
        # 判断file_path 文件格式  txt  json  txt: 一行一个   json:["1","2",...]
        try:
            emails, err = self._read_recipient_file(file_path)
            # public.print_log("获取文件内容 ---{}    type:{}".format(emails, type(emails)))
            if err:
                return public.returnMsg(False, err)
            # 去除空内容
            emails = list(map(lambda x: x.strip(),filter(lambda x: x != "", emails)))

            # 找出重复的邮箱
            from collections import Counter
            email_counts = Counter(emails)
            duplicates = [email for email, count in email_counts.items() if count > 1]
            # public.print_log("重复-- {}".format(duplicates))

            # 去除重复项
            emails = list(set(emails))
        except Exception as e:
            public.print_log(public.get_error_info())
            return public.returnMsg(False, e)
        # public.print_log("获取文件内容 55---{}".format(emails))

        # recipient_analysis = {
            # 'gmail.com': {"count": 0, "info": []},
            # 'googlemail.com': {"count": 0, "info": []},
            #
            # 'hotmail.com': {"count": 0, "info": []},
            # 'outlook.com': {"count": 0, "info": []},
            #
            # 'yahoo.com': {"count": 0, "info": []},
            #
            # 'icloud.com': {"count": 0, "info": []},
            #
            # 'other': {"count": 0, "info": []},

            # 'protonmail.com': {"count": 0, "info": []},
            # 'zoho.com': {"count": 0, "info": []},

        # }
        recipient_analysis = {}

        verify_results = {"success": {}, "failed": {}}


        # 跳过配置黑名单里的邮箱
        # blacklist = self.recipient_blacklist()
        with self.MD("mail_unsubscribe", "mail_unsubscribe") as obj:
            mail_unsubscribe = obj.where('etype=?', 0).select()
        blacklist = [i['recipient'] for i in mail_unsubscribe]
        blacklist_count = 0
        for email in emails:
            # validation_result = self._check_email_address(email)
            # if not validation_result:
            #     verify_results["failed"][email] = 'Email address format is incorrect'
            #     continue
            # if any(char.isupper() for char in email):
            #     verify_results["failed"][email] = 'Email address cannot have uppercase letters!'
            #     continue
            # 跳过黑名单
            if blacklist:
                if email in blacklist:
                    # public.print_log("跳过黑名单 --{}".format(email))
                    blacklist_count += 1
                    continue
            # # 类型退订 todo 暂时没
            # if unemail_list:
            #     if email in unemail_list:
            #         public.print_log("跳过类型黑名单 --{}".format(email))
            #         blacklist_count += 1
            #         continue

            local_part, domain = email.lower().split('@')
            # domain_key = domain if domain in recipient_analysis else 'other'
            domain_key = domain
            if not recipient_analysis.get(domain_key):
                recipient_analysis[domain_key] = {"count": 0, "info": []}
            recipient_analysis[domain_key]["info"].append(email)
            recipient_analysis[domain_key]["count"] += 1
            verify_results["success"][email] = "Common post office" if domain != 'other' else "Other domains"

        # 处理后的数据写入新文件
        recipient_path = "{}/recipient/verify_{}".format(self.in_bulk_path, args.file)

        public.writeFile(recipient_path, public.GetJson(recipient_analysis))

        return public.returnMsg(True,
                                public.lang('导入成功, 跳过 {}取消订阅用户,重复的邮件地址:{}',blacklist_count, len(duplicates)))

    # 获取收件人处理数据 添加时展示 todo 后期弃用
    def get_recipient_data(self, args):
        '''
        获取发送预计完成时间
        :param  file
        :return:
        '''
        if not args.file:
            return public.returnMsg(False, '参数错误')
        recipient_path = "{}/recipient/verify_{}".format(self.in_bulk_path, args.file)
        try:
            data = public.readFile(recipient_path)
            recipient_analysis = json.loads(data)
        except Exception as e:
            public.print_log(public.get_error_info())
            return public.returnMsg(False, '文件内容异常或格式错误: {}'.format(e))

        return public.returnMsg(True, recipient_analysis)

    # 添加批量发送任务  需要生成邮件id  任务id  创建任务统计  已增加新字段 线程和退订
    def add_task(self, args):
        '''
        添加批量发送任务
        :param args:
        :return:
        '''

        # 判断参数传递
        # 必传  addresser  subject content      任务 :  task_name  addresser   task_process(立即执行 1   稍后执行 0)
        # 选传  is_temp 是否是模版  file_content= '邮件正文(1)' 邮件内容上传名称  file_recipient='收件人11' 收件人上传名称
        # 指定邮件内容上传到 /www/server/panel/data/mail/in_bulk/content/
        # 指定收件人上传到 /www/server/panel/data/mail/in_bulk/recipient/
        # 新增 退订按钮
        # 新增 线程数

        try:
            if not hasattr(args, 'addresser') or args.get('addresser/s', '') == '':
                return public.returnMsg(False, public.lang('参数错误：addresser'))

            if not hasattr(args, 'task_name') or args.get('task_name/s', '') == '':
                return public.returnMsg(False, public.lang('参数错误：task_name'))
            task_name = args.get('task_name/s', '')
            # 新增群发邮件类型
            if not hasattr(args, 'etypes') or args.get('etypes', '') == '':
                etypes = '1'
            else:
                etypes = args.etypes

            etype_list = etypes.split(',')
            # 判断  etype 必须要有数据
            with public.S("mail_unsubscribe", '/www/vmail/mail_unsubscribe.db') as obj:
                count = obj.where_in('etype', etype_list).where('active', 1).count()
            if not count:
                return public.returnMsg(False, public.lang('所选联系人列表为空'))

            # 邮件模板
            if not hasattr(args, 'temp_id') or args.get('temp_id/d', 0) == 0:
                return public.returnMsg(False, '参数错误: temp_id')
            temp_id = args.temp_id


            # 收件人路径(上传后处理的文件)
            namemd5 = public.md5(task_name)
            # 校验后的文件就是  /{md5任务名}_verify_{原始文件名}  todo  改 {md5任务名}_verify_{邮件类型(联系人的分类)}
            recipient_path = "{}/recipient/{}_verify_{}".format(self.in_bulk_path, namemd5, etypes)
            # 处理收件人列表
            recipient_count, black_num, abnormal_num = self.processing_recipient_v2(recipient_path, etype_list)
            if recipient_count == 0:
                return public.returnMsg(False, public.lang('没有符合条件的收件人, 黑名单 {} 异常邮箱 {}', black_num, abnormal_num))

            # # 用户剩余额度
            # user_quota = self._get_user_quota()
            # # 占用额度
            # occupied = self.get_quota_occupation()['occupation']
            # if user_quota == 0:
            #     # 当前无发件额度 请购买补充包 或等待下月刷新
            #     return public.returnMsg(False, public.lang('There is no sending quota, please purchase the refill pack or wait for refresh next month'))
            #
            # if user_quota - occupied < recipient_count:
            #     # usable = recipient_count - (user_quota + occupied)
            #     # 剩余额度{} 未完成任务占用额度{} 任务发送需要额度{}, 请购买补充包
            #     return public.returnMsg(False, public.lang('The remaining amount {} the amount occupied by the unfinished task {} the amount needed for the task to be sent {}, please purchase the supplementary package', user_quota,occupied, recipient_count))

            # 是否记录到发件箱
            if not hasattr(args, 'is_record') or args.get('is_record/d', 0) == 0:
                is_record = 0
            else:
                is_record = 1
            # 是否增加退订 unsubscribe
            if not hasattr(args, 'unsubscribe') or args.get('unsubscribe/d', 0) == 0:
                unsubscribe = 0
            else:
                unsubscribe = 1
            # 线程数
            if not hasattr(args, 'threads') or args.get('threads/d', 0) == 0:
                threads = 0
            else:
                threads = int(args.threads)
                if threads > 10:
                    return public.returnMsg(False, '线程数不能超过10')


            # 任务开始时间
            if not hasattr(args, 'start_time'):
                start_time = int(time.time())
            else:
                start_time = int(args.start_time)

            # # 是否立即执行?  1 暂停中     0 未暂停  默认不暂停
            # if not hasattr(args, 'pause') or args.get('pause/d', 0) == 0:
            #     pause = 0
            # else:
            #     pause = 1
            pause = 0  # 默认都执行

            # 新增字段
            if not hasattr(args, 'full_name') or args.get('full_name', '') == '':
                full_name = ''
            else:
                full_name = args.get('full_name', '')
            # 备注
            remark = args.get('remark', '')
            addresser = args.get('addresser/s', '')
            subject = args.get('subject/s', '')
            task_process = args.get('task_process', 0)  # 是否立即执行


            # 发件人检测
            data = self.M('mailbox').where('username=?', addresser).find()
            if not data:
                return public.returnMsg(False, '邮件地址不存在')

            # 清标记
            self.init_send()
            # 添加邮件表
            timestamp = int(time.time())
            task_id = 0

            try:

                # 添加任务表
                task_id = self.M('email_task').add(
                    'task_name,addresser,recipient_count,task_process,pause,temp_id,is_record,unsubscribe,threads,created,modified,start_time,remark,etypes,recipient,subject,full_name',
                    (task_name, addresser, recipient_count, task_process, pause, temp_id, is_record, unsubscribe, threads,
                     timestamp, timestamp, start_time, remark, etypes, recipient_path, subject,full_name))


                # 记录发送失败日志
                error_log = "/www/server/panel/data/mail/in_bulk/errlog/task_{}.log".format(task_id)
                if not os.path.exists(error_log):
                    public.WriteFile(error_log, '')

                # 添加执行的定时任务
                self._task_mail_send1()
                self._task_mail_send2()
                # 写入额度占用
                # self.add_quota_occupation(str(task_id), recipient_count)
                # 建立数据库
                self.create_task_database(task_id)
                # 统计调用
                public.set_module_logs('mailModel', 'add_task', 1,)
                public.set_module_logs('mailModel', 'bulk_emails', recipient_count)
                return public.returnMsg(True, '任务添加成功')
            except Exception as e:
                public.print_log(public.get_error_info())
                # 删除已创建的任务
                # self.M('temp_email').where('id=?', temp_id).delete()
                self.M('email_task').where('id=?', task_id).delete()
                # 删除独立数据库
                database_path = f'/www/vmail/bulk/task_{task_id}.db'
                if os.path.exists(database_path):
                    os.remove(database_path)
                return public.returnMsg(False, '任务添加失败: [{0}]'.format(str(e)))
        except Exception as e:
            public.print_log(public.get_error_info())

    # 发送测试  -- 含退订
    # @only_pro_members
    def send_mail_test(self, args):
        # 获取正文
        if not hasattr(args, 'temp_id') or args.get('temp_id/d', 0) == 0:
            return public.returnMsg(False, '参数错误: temp_id')
        temp_id = args.get('temp_id', 0)

        email_info = self.M('temp_email').where('id=?', temp_id).find()
        if not email_info:
            return public.returnMsg(False, public.lang('模板不存在'))

        content_path = email_info['content']

        if os.path.exists(content_path):
            content = public.readFile(content_path)

        else:
            return public.returnMsg(False, public.lang('{}文件不存在', content_path))

        subject = args.get('subject', '')
        # unsubscribe = args.get('unsubscribe', 0)

        # 查询发件人
        mail_from = args.mail_from
        data = self.M('mailbox').where('username=?', mail_from).field('password_encode,full_name').find()
        password = self._decode(data['password_encode'])
        mail_to = args.mail_to.split(',')

        _, domain = mail_from.split('@')
        # if unsubscribe:
        #
        #     import public.PluginLoader as plugin_loader
        #     bulk = plugin_loader.get_module('{}/plugin/mail_sys/mail_send_bulk.py'.format(public.get_panel_path()))
        #     SendMailBulk = bulk.SendMailBulk
        #
        #     url = SendMailBulk().get_unsubscribe_url()
        #     send_mail_client = SendMail(mail_from, password, 'localhost')
        #
        #     # url = self.get_unsubscribe_url()
        #     for user in mail_to:
        #         if len(user) == 0:
        #             # print("收件人为0 退出 1435")
        #             continue
        #         user_ = [user]
        #         # 生成message-id
        #         # msgid = make_msgid()
        #         # 更改发件内容  重新发送
        #         # 生成邮箱jwt
        #         # mail_jwt = self.generate_jwt(user, etypes, task_id)
        #         mail_jwt = SendMailBulk().generate_jwt(user, etypes, task_id)
        #         # 将邮件内容重点退订链接替换为指定内容  todo  __UNSUBSCRIBE_URL__
        #         url1 = "{}/mailUnsubscribe?action=Unsubscribe&jwt={}".format(url, mail_jwt)
        #         # 替换
        #         content = content.replace('__UNSUBSCRIBE_URL__', url1)
        #         # 测试  通过后删掉
        #         public.writeFile('/www/server/panel/plugin/mail_sys/data/tiaaaa.txt', content)
        #         public.print_log('正文已替换333')
        #
        #         try:
        #             send_mail_client.setMailInfo_two(subject, content, [])
        #
        #             st = send_mail_client.sendMail(user_, domain, 0)
        #
        #             if not st:
        #                 # 重新建立连接
        #                 send_mail_client = SendMail(mail_from, password, 'localhost')
        #                 send_mail_client.setMailInfo_one(data['full_name'])
        #             else:
        #                 # 重置msg对象
        #                 send_mail_client.update_init(data['full_name'])
        #         except Exception as e:
        #             public.print_log(public.get_error_info())
        #     return public.returnMsg(True, public.lang('Sent over'))
        # else:
        # 附件?
        files = json.loads(args.files) if 'files' in args else []
        # 收件人判断
        if not isinstance(mail_to, list):
            return public.returnMsg(False, '收件人不是list')
        if len(mail_to) == 0:
            return public.returnMsg(False, '收件人不能为空')

        try:

            # 登录
            send_mail_client = SendMail(mail_from, password, 'localhost')
            # public.print_log("--------------------登录信息000 ---{}--({})".format(mail_from, password))
            # 用户名full_name
            send_mail_client.setMailInfo(data['full_name'], subject, content, files)
            # 收件人列表  此处记录调用次数
            _, domain = mail_from.split('@')
            result = send_mail_client.sendMail(mail_to, domain, 1)
            return result
        except Exception as e:
            public.print_log(public.get_error_info())
            return public.returnMsg(False, public.lang('发送失败, 错误原因 [{0}]', str(e)))

    def import_contacts(self, args):
        '''
        导入收件人到联系人列表
        :param  file        str (收件人文件名)
        :param  etypes      str (联系人类型  多个逗号隔开)  多选分类  每个分类都导入
        :param  active      int (0 退订    1订阅)  暂不使用,默认订阅类型
        :return:
        '''
        file = args.get('file/s', '')
        # etypes = args.get('etypes/s', '')

        if not file:
            return public.returnMsg(False, public.lang('参数错误'))

        if not hasattr(args, 'mail_type'):
            return public.returnMsg(False, public.lang('参数错误: mail_type'))

        created = int(time.time())
        insert = {
            'created': created,
            'mail_type': args.mail_type,
        }

        with self.M('mail_type') as obj:
            exit = obj.where('mail_type =?',(args.mail_type,)).count()
            if exit:
                return public.returnMsg(False, public.lang('这种类型已经存在'))
            etype = obj.insert(insert)

        if not os.path.exists("{}/recipient".format(self.in_bulk_path)):
            os.mkdir("{}/recipient".format(self.in_bulk_path))
        file_path = "{}/recipient/{}".format(self.in_bulk_path, file)
        if not os.path.exists(file_path):
            return public.returnMsg(False, public.lang('文件不存在'))


        # 判断file_path 文件格式  txt  json  txt: 一行一个   json:["1","2",...]
        try:
            emails, err = self._read_recipient_file(file_path)
            if err:
                return public.returnMsg(False, err)
            # 去除空内容
            emails = list(map(lambda x: x.strip(),filter(lambda x: x != "", emails)))

            # 找出重复的邮箱
            from collections import Counter
            email_counts = Counter(emails)
            duplicates = [email for email, count in email_counts.items() if count > 1]

            # 去除重复项
            emails = list(set(emails))
        except Exception as e:
            public.print_log(public.get_error_info())
            return public.returnMsg(False, e)

        import_info = []

        # 先导入订阅   已存在退订的改为订阅  已有订阅跳过  不存在的订阅新增
        # 没个分类都执行一遍

        etype = int(etype)

        with public.S("mail_unsubscribe", '/www/vmail/mail_unsubscribe.db') as obj:
            # 已存在退订
            unsubscribe_list = obj.where_in('recipient', emails).where('etype', etype).where('active', 0).select()
            # 已存在的订阅
            subscribe_list = obj.where_in('recipient', emails).where('etype', etype).where('active', 1).select()

            unsubscribes = [i['recipient'] for i in unsubscribe_list]
            subscribes = [i['recipient'] for i in subscribe_list]
            import itertools
            merged_list = list(itertools.chain(unsubscribes, subscribes))

            # 退订改订阅
            unup_num = obj.where_in('recipient', unsubscribes).update({"active": 1})

            # 不存在的新增
            add_emails = [i for i in emails if i not in merged_list]
            insert_data = []

            for i in add_emails:
                insert_info = {
                    'created': created,
                    'recipient': i,
                    'etype': etype,
                    'active': 1,        # 订阅
                    'task_id': 0,
                }
                insert_data.append(insert_info)
            add_num = obj.insert_all(insert_data, option='IGNORE')
            import_info.append({
                    "etype": etype,                     # 操作分类id
                    "mail_type": args.mail_type,     # 操作分类
                    "unup_num": unup_num,               # 退订改订阅
                    "add_num": add_num,                 # 订阅新增
                })
        data = {
            "duplicates": duplicates,
            "import_info": import_info,
        }
        # return public.returnMsg(True, data)
        # public.set_module_logs('mailModel', 'import_contacts', 1)
        return public.returnMsg(True, public.lang('成功添加邮箱{}个, 失败{}个, 重复邮箱{}个',add_num,unup_num,len(duplicates)))


    def import_contacts_etypes(self, args):
        '''
        导入收件人到联系人列表
        :param  file        str (收件人文件名)
        :param  etypes      str (联系人类型  多个逗号隔开)  多选分类  每个分类都导入
        :param  active      int (0 退订    1订阅)  暂不使用,默认订阅类型
        :return:
        '''
        file = args.get('file/s', '')
        etypes = args.get('etypes/s', '')

        if not file:
            return public.returnMsg(False, public.lang('参数错误：file'))
        if not etypes:
            return public.returnMsg(False, public.lang('参数错误：etypes'))

        if not os.path.exists("{}/recipient".format(self.in_bulk_path)):
            os.mkdir("{}/recipient".format(self.in_bulk_path))
        file_path = "{}/recipient/{}".format(self.in_bulk_path, file)
        # /www/server/panel/data/mail/in_bulk/recipient/
        if not os.path.exists(file_path):
            return public.returnMsg(False, public.lang('文件不存在'))

        etype_list = etypes.split(",")

        # 判断file_path 文件格式  txt  json  txt: 一行一个   json:["1","2",...]
        try:
            emails, err = self._read_recipient_file(file_path)
            if err:
                return public.returnMsg(False, err)
            # 去除空内容
            emails = list(map(lambda x: x.strip(),filter(lambda x: x != "", emails)))

            # 找出重复的邮箱
            from collections import Counter
            email_counts = Counter(emails)
            duplicates = [email for email, count in email_counts.items() if count > 1]

            # 去除重复项
            emails = list(set(emails))
        except Exception as e:
            public.print_log(public.get_error_info())
            return public.returnMsg(False, e)

        with self.M('mail_type') as obj:
            data_list = obj.select()
        types = {str(item["id"]): item["mail_type"] for item in data_list}
        import_info = []

        # 先导入订阅   已存在退订的改为订阅  已有订阅跳过  不存在的订阅新增
        # 没个分类都执行一遍
        for etype in etype_list:
            etype = int(etype)
            if not types.get(str(etype), None):
                continue

            with public.S("mail_unsubscribe", '/www/vmail/mail_unsubscribe.db') as obj:
                # 已存在退订
                # unsubscribe_list = obj.where_in('recipient', emails).where('etype', etype).where('active', 0).select()
                # 已存在的订阅
                # subscribe_list = obj.where_in('recipient', emails).where('etype', etype).where('active', 1).select()

                # unsubscribes = [i['recipient'] for i in unsubscribe_list]
                # subscribes = [i['recipient'] for i in subscribe_list]
                # import itertools
                # merged_list = list(itertools.chain(unsubscribes, subscribes))

                # 退订改订阅
                # unup_num = obj.where_in('recipient', unsubscribes).update({"active": 1})
                unup_num = 0

                # 不存在的新增
                # add_emails = [i for i in emails if i not in merged_list]
                insert_data = []
                created = int(time.time())
                for i in emails:
                    insert_info = {
                        'created': created,
                        'recipient': i,
                        'etype': etype,
                        'active': 1,        # 订阅
                        'task_id': 0,
                    }
                    insert_data.append(insert_info)
                add_num = obj.insert_all(insert_data, option='IGNORE')
                import_info.append({
                        "etype": etype,                     # 操作分类id
                        "mail_type": types[str(etype)],     # 操作分类
                        "unup_num": unup_num,               # 退订改订阅
                        "add_num": add_num,                 # 订阅新增
                    })
        data = {
            "duplicates":duplicates,
            "import_info":import_info,
        }
        # return public.returnMsg(True, data)
        # public.set_module_logs('mailModel', 'import_contacts_etypes', 1)
        return public.returnMsg(True, public.lang('成功添加邮箱{}个, 失败{}个, 重复邮箱{}个',add_num,unup_num,len(duplicates)))

    # 二次处理收件人文件  剔除0类型  剔除针对类型 剔除异常邮箱
    def processing_recipient_v2(self, recipient_path, etype_list):
        '''
        导入收件人 (收件人写入文件时去重)

        :param  str   recipient_path 处理后的收件人文件路径
        :param  int   etype_list(邮件类型   [1,2,3])
        :return:  int,int,int   收件人数量 ,黑名单数量,异常邮箱数量
        '''

        # 判断file_path 文件格式  txt  json  txt: 一行一个   json:["1","2",...]
        try:
            with public.S("mail_unsubscribe", '/www/vmail/mail_unsubscribe.db') as obj:
                email_list = obj.where_in('etype', etype_list).where('active', 1).select()
            emails = [i['recipient'] for i in email_list]
            # 不同组有相同邮件 去重
            emails = list(set(emails))
        except Exception as e:
            public.print_log(public.get_error_info())
            return public.returnMsg(False, e)

        recipient_analysis = {
            'gmail.com': {"count": 0, "info": []},
            'googlemail.com': {"count": 0, "info": []},

            'hotmail.com': {"count": 0, "info": []},
            'outlook.com': {"count": 0, "info": []},

            'yahoo.com': {"count": 0, "info": []},

            'icloud.com': {"count": 0, "info": []},

            'other': {"count": 0, "info": []},
        }

        verify_results = {"success": {}, "failed": {}}

        # 数据库查询邮件类型对应的黑名单
        blacklist = []
        # 增加黑名单
        etype_list.append(0)
        # 在   active=0 退订     etype_list 退订类型    etype=0 黑名单
        with public.S("mail_unsubscribe", '/www/vmail/mail_unsubscribe.db') as obj:
            unemails = obj.where_in('etype', etype_list).where('active', 0).select()

        if unemails:
            blacklist = [i['recipient'] for i in unemails]
        abnormal_recipient = self.get_abnormal_recipient()

        blacklist_count = 0
        abnormal_count = 0
        for email in emails:
            # 跳过黑名单
            if blacklist:
                if email in blacklist:
                    # public.print_log("跳过黑名单 --{}".format(email))
                    blacklist_count += 1
                    continue
            # 跳过异常邮箱    todo 测试时隐藏
            if abnormal_recipient:
                if email in abnormal_recipient:
                    # public.print_log("跳过异常 --{}".format(email))
                    abnormal_count += 1
                    continue
            local_part, domain = email.lower().split('@')
            domain_key = domain if domain in recipient_analysis else 'other'
            recipient_analysis[domain_key]["info"].append(email)
            recipient_analysis[domain_key]["count"] += 1
            verify_results["success"][email] = "Common post office" if domain != 'other' else "Other domains"

        # 处理后的数据写入新文件
        public.writeFile(recipient_path, public.GetJson(recipient_analysis))

        # 累计recipient_analysis所有count数量
        total_count = sum(domain_data["count"] for domain_data in recipient_analysis.values())

        return total_count, blacklist_count,abnormal_count

    # 暂停批量发送任务
    def pause_task(self, args):
        '''
        暂停发送任务   判断状态为执行中的可以暂停   task_process 1
        :param args: task_id 任务id;   pause 1暂停 0 重启
        :return:
        '''

        if not hasattr(args, 'task_id') or args.get('task_id/d', 0) == 0:
            return public.returnMsg(False, '参数错误')
        if not hasattr(args, 'pause'):
            return public.returnMsg(False, '参数错误')
        task_info = self.M('email_task').where('id=?', args.task_id).find()
        pause = int(args.pause)
        if pause == 1 and task_info['task_process'] != 1:
            return public.returnMsg(False, '只能暂停执行中的任务')

        self.M('email_task').where('id=?', args.task_id).update({'pause': pause})
        info = {
            "1": "暂停",
            # "0": "Restart"
            "0": "发送"
        }
        return public.returnMsg(True, '{}成功'.format(info[args.pause]))

    # 任务列表
    def get_task_list(self, args):
        '''
        任务列表
        :param args:
        :return:
        '''

        p = int(args.p) if 'p' in args else 1
        rows = int(args.size) if 'size' in args else 10
        callback = args.callback if 'callback' in args else ''
        count = self.M('email_task').count()
        page_data = public.get_page(count, p=p, rows=rows, callback=callback)

        try:
            task_list = self.M('email_task').order('created desc').limit(
                page_data['shift'] + ',' + page_data['row']).select()
            email_list = self.M('temp_email').order('created desc').select()
            if not task_list:
                return public.returnMsg(True, {'data': [], 'page': page_data['page']})
            email_dict = {item['id']: item for item in email_list}

            # 新增邮件类型信息
            with self.M('mail_type') as obj:
                data_list = obj.select()
            types = {str(item["id"]): item["mail_type"] for item in data_list}
            # 加入0类型的邮件  完全退订 Unsubscribe all
            types['0'] = "Unsubscribe all"
            for task in task_list:
                temp_id = task['temp_id']
                task_id = task['id']
                # 获取错误数量 新数据库
                database_path = f'/www/vmail/bulk/task_{task_id}.db'
                if os.path.exists(database_path):
                    with public.S("task_count", database_path) as obj:
                        count = obj.where('status !=?', 'sent').count()

                else:
                    recipients = self.M('task_count').where('task_id=?', task_id).select()
                    unique_recipients = set(r['recipient'] for r in recipients)  # 使用集合去重
                    count = len(unique_recipients)

                task['count'] = {"error_count": count}
                # 更新 email_info
                if temp_id in email_dict:
                    task['email_info'] = email_dict[temp_id]

                # 获取任务邮件类型
                etype_list = task['etypes'].split(",")
                etype_info = []
                for i in etype_list:
                    if types.get(str(i), None):
                        # etype_info.append({"id": i, "mail_type": types[str(i)]})
                        etype_info.append({str(i): types[str(i)]})
                task['mail_type'] = etype_info

                # 获取发件进度
                if task['task_process'] == 2:
                    task['progress'] = 100
                    task['delivered'] = task['recipient_count']
                else:
                    sentcount = self.get_send_progress(task_id)
                    if sentcount > task['recipient_count']:
                        sentcount = task['recipient_count']

                    task['progress'] = round(sentcount / task['recipient_count'] * 100, 2) if task['recipient_count'] > 0 else 0
                    task['delivered'] = sentcount

                # 记录发送失败日志
                task['error_log'] = "/www/server/panel/data/mail/in_bulk/errlog/task_{}.log".format(task_id)
                if not os.path.exists("/www/server/panel/data/mail/in_bulk/errlog/task_{}.log".format(task_id)):
                    task['error_log'] = "/www/server/panel/data/mail/in_bulk/errlog/{}_{}.log".format(task['task_name'],task_id)
                sent_recipient_path = f"{self.sent_recipient_path}/toRecipient_{task_id}.log"
                task['sent_recipient_file'] = sent_recipient_path
                if not os.path.exists(task['error_log']):
                    public.WriteFile(task['error_log'], '')
            return public.returnMsg(True, {'data': task_list, 'page': page_data['page']})

        except Exception as e:
            public.print_log(public.get_error_info())

    def get_task_all(self, args):
        '''
        获取全部群发任务
        :param args:
        :return:
        '''

        try:
            task_list = self.M('email_task').order('created desc').field('id,task_name,subject,created').select()

            return public.returnMsg(True, task_list)

        except Exception as e:
            public.print_log(public.get_error_info())



    # 删除任务
    def delete_task(self, args):
        '''
        删除任务
        :param args: task_id 任务id
        :return:
        '''
        if not hasattr(args, 'task_id') or args.get('task_id/d', 0) == 0:
            return public.returnMsg(False, '参数错误')
        task_info = self.M('email_task').where('id=?', args.task_id).find()

        # 删除错误日志
        error_log = "/www/server/panel/data/mail/in_bulk/errlog/task_{}.log".format(task_info['id'])
        if os.path.exists(error_log):
            os.remove(error_log)
        # 兼容旧日志文件
        error_log1 = "/www/server/panel/data/mail/in_bulk/errlog/{}_{}.log".format(task_info['task_name'], task_info['id'])
        if os.path.exists(error_log1):
            os.remove(error_log1)
        try:
            self.M('email_task').where('id=?', task_info['id']).delete()
            self.M('task_count').where('task_id=?', task_info['id']).delete()

        except:
            public.print_log(public.get_error_info())
        # 删除标记
        start_mark = '/www/server/panel/plugin/mail_sys/start_Task.pl'
        start_send = '/www/server/panel/plugin/mail_sys/start_Send.pl'
        if os.path.exists(start_mark):
            os.remove(start_mark)
        if os.path.exists(start_send):
            os.remove(start_send)

        # 删除额度占用
        # self.del_quota_occupation(str(task_info['id']))
        # 删除群发任务数据库
        database_path = f'/www/vmail/bulk/task_{args.task_id}.db'
        if os.path.exists(database_path):
            os.remove(database_path)

        return public.returnMsg(True, '删除成功')

    # 获取错误数据分析
    def get_log_rank(self, args):
        '''
        获取错误排行
        :param args:
                task_id 任务id
                type     类型 domain 域名排行    status 错误类型排行
        :return:
        '''

        if not hasattr(args, 'type'):
            return public.returnMsg(False, '参数错误')

        types = args.type
        if types == "domain":
            field = "domain"
        else:
            field = "status"

        # 先检查是否有专属数据库  task_id
        task_id = args.task_id
        database_path = f'/www/vmail/bulk/task_{task_id}.db'
        if os.path.exists(database_path):
            with public.S("task_count", database_path) as obj:
                rank_list = obj.group(field).field(field, 'count(*) as `count`').where('status !=?', 'sent').select()
        else:

            try:
                query = '''
                SELECT {group_by_field}, COUNT(*) as count
                FROM task_count
                WHERE task_id = ?
                GROUP BY {group_by_field}
                ORDER BY count DESC
                LIMIT 10;
                '''.format(group_by_field=field)

                params = (args.task_id,)
                # 执行查询
                results = self.M('task_count').query(query, params)
                # params = (args.task_id,)
                # results = self.M('task_count').query(query, params)
                rank_list = []
                for value, count in results:
                    # rank_list.append({
                    #     field:count
                    # })
                    rank_list.append({
                        field: value,
                        "count": count,
                    })
            except:
                rank_list = []

        return public.returnMsg(True, rank_list)

    def get_log_list(self, args):
        '''
        获取错误详情
        :param args: task_id 任务id
        :return:
        '''
        if not hasattr(args, 'task_id') or args.get('task_id/d', 0) == 0:
            return public.returnMsg(False, '参数错误')

        p = int(args.page) if 'page' in args else 1
        rows = int(args.size) if 'size' in args else 10
        # callback = args.callback if 'callback' in args else ''

        if not hasattr(args, 'type'):
            return public.returnMsg(False, '参数错误')
        if not hasattr(args, 'value'):
            return public.returnMsg(False, '参数错误')

        types = args.type
        value = args.value
        if types == "domain":
            fields = "domain=?"
        else:
            fields = "status=?"

        # 先检查是否有专属数据库  task_id
        task_id = args.task_id
        database_path = f'/www/vmail/bulk/task_{task_id}.db'
        if os.path.exists(database_path):
            with public.S("task_count", database_path) as obj:
                count = obj.where(fields, value).where('status !=?', 'sent').count()
                error_list = obj.where(fields, value).where('status !=?', 'sent').limit(rows, (p - 1) * rows).select()
            page_data = public.get_page(count, p=p, rows=rows, callback='')
            pattern = r"href='(/v2)?/plugin.*?\?p=(\d+)'"
            page_data['page'] = re.sub(pattern, r"href='\1'", page_data['page'])

        else:
            # 查询原来数据库
            wheres = 'task_id=? and ' + fields
            count = self.M('task_count').where(wheres, (args.task_id, value)).count()

            page_data = public.get_page(count, p=p, rows=rows, callback='')

            # 替换掉 href标签里的多余信息 只保留页码
            pattern = r"href='(/v2)?/plugin.*?\?p=(\d+)'"
            # 使用re.sub进行替换
            page_data['page'] = re.sub(pattern, r"href='\1'", page_data['page'])

            try:
                query = self.M('task_count').where(wheres, (args.task_id, value))
                error_list = query.limit(page_data['shift'] + ',' + page_data['row']).select()
            except:
                error_list = []
        return public.returnMsg(True, {'data': error_list, 'page': page_data['page']})

    def _get_ptr_record(self):

        public_ip = self._get_pubilc_ip()
        if not public_ip:
            return False
        try:
            # 执行反向DNS查询
            result = socket.gethostbyaddr(public_ip)
            if result:
                if result[0]:
                    return True
            return False
        except socket.herror:
            return False

    def _task_mail_send1(self, ):

        # 查看是否有任务 没有结束 是否有执行中的任务 有 看执行状态
        # 查看任务是否已经开始执行  开始.pl -- 检查有没有结束 结束标记.pl
        # 没有开始标志 记录开始 开始.pl 去执行   执行  判断数量  分批次 延时执行

        cmd = '''
        if pgrep -f "send_bulk_script.py" > /dev/null
        then
            echo "The task [Sending bulk emails] is executing"
            exit 1;
        else
            btpython /www/server/panel/class/mailModel/script/send_bulk_script.py
        fi
        '''

        import crontab
        p = crontab.crontab()
        try:
            c_id = public.M('crontab').where('name=?', u'[勿删] 群发邮件任务').getField('id')
            if not c_id:
                data = {}
                data['name'] = u'[勿删] 群发邮件任务'
                data['type'] = 'minute-n'
                data['where1'] = '1'
                # data['sBody'] = 'btpython /www/server/panel/plugin/mail_sys/script/send_bulk_script.py'
                data['sBody'] = cmd
                data['backupTo'] = ''
                data['sType'] = 'toShell'
                data['hour'] = ''
                data['minute'] = ''
                data['week'] = ''
                data['sName'] = ''
                data['urladdress'] = ''
                data['save'] = ''
                p.AddCrontab(data)
                return public.returnMsg(True, '设置成功!')
        except Exception as e:
            public.print_log(public.get_error_info())

    # 检查有没有执行完毕  执行完毕 记录时间 修改状态 分析日志 更改统计 添加结束标记 删掉开始标记
    def _task_mail_send2(self, ):

        cmd = '''
        if pgrep -f "mail_error_logs.py" > /dev/null
        then
            echo "The task [Checking the sent results] is executing"
            exit 1;
        else
            btpython /www/server/panel/class/mailModel/script/mail_error_logs.py
        fi
        '''
        import crontab
        p = crontab.crontab()
        try:
            c_id = public.M('crontab').where('name=?', u'[勿删] 检查发送结果').getField('id')
            if not c_id:
                data = {}
                data['name'] = u'[勿删] 检查发送结果'
                data['type'] = 'minute-n'
                data['where1'] = '1'
                data['sBody'] = cmd
                data['backupTo'] = ''
                data['sType'] = 'toShell'
                data['hour'] = ''
                data['minute'] = ''
                data['week'] = ''
                data['sName'] = ''
                data['urladdress'] = ''
                data['save'] = ''
                p.AddCrontab(data)
                return public.returnMsg(True, '设置成功!')
        except Exception as e:
            public.print_log(public.get_error_info())

    # 无订阅发送
    def _send_email_all(self, recipients, addresser, password, full_name, subject, content_detail, is_record, task_id):

        if recipients['count'] == 0:
            # public.print_log("无邮件退出")
            return
        # 登录
        send_mail_client = SendMail(addresser, password, 'localhost')
        # 邮件内容
        send_mail_client.setMailInfo(full_name, subject, content_detail, [])

        _, domain = addresser.split('@')
        sent_recipients_path = f"{self.sent_recipient_path}/toRecipient_{task_id}.log"
        sent_msgid_path = f"{self.sent_recipient_path}/msgid_{task_id}.log"
        mail_to = recipients['info']

        orig_content = content_detail
        proxy_url = self.get_unsubscribe_url()

        for user in mail_to:
            if len(user) == 0:
                continue

            content_detail = orig_content

            user_ = [user]
            # 生成message-id
            msgid = make_msgid()

            try:
                from power_mta.maillog_stat import MailTracker
                mail_tracker = MailTracker(content_detail, task_id, msgid.strip('<>'), user, proxy_url)
                mail_tracker.track_links()
                mail_tracker.append_tracking_pixel()
                content_detail = mail_tracker.get_html()
            except:
                pass

            st = send_mail_client.sendMail(user_, domain, is_record, msgid)
            if not st:
                # 重新登录
                send_mail_client = SendMail(addresser, password, 'localhost')

                # 重新传入邮件内容
                send_mail_client.setMailInfo(full_name, subject, content_detail, [])

            # 记录已发件的收件人
            public.AppendFile(sent_recipients_path, user + '\n')
            public.AppendFile(sent_msgid_path, msgid + '\n')


    def get_unsubscribe_url(self,):
        # 获取退订链接
        path = "/www/server/panel/plugin/mail_sys/setinfo.json"
        url = None

        # 检查用户设置的反代url
        if os.path.exists(path):
            try:
                path_info = json.loads(public.readFile(path))
                if path_info.get('url'):  # 如果url存在且不为空
                    url = path_info['url']
            except json.JSONDecodeError:
                # 如果读取json时发生错误，可以记录日志或者返回默认值
                pass

        # 如果没有设置url，使用默认的url
        if not url:
            ssl_status = public.readFile('/www/server/panel/data/ssl.pl')
            ssl = 'https' if ssl_status else 'http'

            ip = public.readFile("/www/server/panel/data/iplist.txt")
            port = public.readFile('/www/server/panel/data/port.pl')

            # 如果ip或port不存在，应该处理异常情况
            if ip and port:
                url = f"{ssl}://{ip}:{port}"

        return url

    #  正文需要增加退订按钮 发送方式
    def _send_email_all_unsubscribe(self, recipients, addresser, password, full_name, subject, content_detail, is_record, task_id, etypes):

        if recipients['count'] == 0:
            # public.print_log("无邮件退出")
            return

        # 先查看有没有设置ip端口  未设置使用用户设置的
        url = self.get_unsubscribe_url()

        # 登录
        send_mail_client = SendMail(addresser, password, 'localhost')
        # 邮件内容(原本位置)
        # send_mail_client.setMailInfo(full_name, subject, None, [])
        # 此处传递邮件发件人 主题
        send_mail_client.setMailInfo_one(full_name)

        _, domain = addresser.split('@')
        mail_to = recipients['info']
        # 每个线程单独开一个文件记录已发送 避免文件操作异常
        # 改为任务名
        # public.print_log("|-准备执行的任务 id 记录   {} ".format(task_id))
        sent_recipients_path = f"{self.sent_recipient_path}/toRecipient_{task_id}.log"
        sent_msgid_path = f"{self.sent_recipient_path}/msgid_{task_id}.log"
        # print("订阅发送msgid文件   sent_msgid_path-- {}".format(sent_msgid_path))

        orig_content = content_detail

        try:
            for user in mail_to:
                if len(user) == 0:
                    # print("收件人为0 退出 1435")
                    continue

                content_detail = orig_content

                user_ = [user]

                # 生成message-id
                msgid = make_msgid()

                # 追踪邮件
                try:
                    from power_mta.maillog_stat import MailTracker
                    mail_tracker = MailTracker(content_detail, task_id, msgid.strip('<>'), user, url)
                    mail_tracker.track_links()
                    mail_tracker.append_tracking_pixel()
                    content_detail = mail_tracker.get_html()
                except:
                    pass

                # 更改发件内容  重新发送
                # 生成邮箱jwt
                mail_jwt = self.generate_jwt(user, etypes, task_id)

                # 将邮件内容重点退订链接替换为指定内容  todo  __UNSUBSCRIBE_URL__
                url1 = "{}/mailUnsubscribe?action=Unsubscribe&jwt={}".format(url, mail_jwt)

                # 替换
                new_content = content_detail.replace('__UNSUBSCRIBE_URL__', url1)

                # 此处传入邮件正文 邮件正文用过就删
                send_mail_client.setMailInfo_two(subject, new_content, [])

                st = send_mail_client.sendMail(user_, domain, is_record, msgid)

                if not st:
                    # 重新建立连接
                    send_mail_client = SendMail(addresser, password, 'localhost')
                    send_mail_client.setMailInfo_one(full_name)
                else:
                    # 重置msg对象
                    send_mail_client.update_init(full_name)

                # 记录已发件的收件人 message-id
                public.AppendFile(sent_recipients_path, user + '\n')
                public.AppendFile(sent_msgid_path, msgid + '\n')
        except:
            print(public.get_error_info())
            public.print_log(public.get_error_info())

    # 获取某个域名已经发送的数量
    def _get_count_limit(self, domain):
        key = domain

        if domain in ['gmail.com', 'googlemail.com']:
            key = 'gmail'
        if domain in ['hotmail.com', 'outlook.com']:
            key = 'outlook'

        # 获取已有的  每日凌晨1点清空
        count_sent = '/www/server/panel/plugin/mail_sys/count_sent_domain.json'
        if not os.path.exists(count_sent):
            data = {
                'gmail': 0,
                'outlook': 0,
                'yahoo.com': 0,
                'icloud.com': 0,
                'other': 0,
            }
        else:
            try:
                data = public.readFile(count_sent)
                data = json.loads(data)
            except:
                data = {
                    'gmail': 0,
                    'outlook': 0,
                    'yahoo.com': 0,
                    'icloud.com': 0,
                    'other': 0,
                }

        return data[key]

    def _mail_error_log_back(self, start, end, error_log, task_id):
        # public.print_log("取日志中----")
        try:

            log_data = public.readFile(self.maillog_path)

            # 正则表达式模式匹配投递结果信息
            status_pattern = r"\bstatus=([a-zA-Z0-9]+)\b"

            output_file1 = "/www/server/panel/data/mail/in_bulk/errlog"
            # output_file = "/www/server/panel/data/mail/in_bulk/errlog/task_err.log"
            if not os.path.isdir(output_file1):
                os.makedirs(output_file1)

            # 先清空
            with open(error_log, 'w') as f:
                pass

            seen_recipients = set()

            with open(error_log, 'a') as f:
                # 循环处理日志数据
                for line in log_data.splitlines():
                    err_one = {
                        "task_id": task_id,
                        "recipient": "",
                        "delay": "",
                        "delays": "",
                        "dsn": "",
                        "relay": "",
                        "domain": "",
                        "status": "",
                        "err_info": "",
                    }

                    try:

                        try:
                            # 尝试解析ISO 8601格式的时间戳
                            log_time = parse(line[:31])  # 取前31个字符 2024-07-12T08:32:04.211578+00:00
                            # 根据系统时区偏移时间

                        except ValueError:
                            # 如果ISO 8601格式解析失败，尝试解析另一种格式
                            timestamp_str = line[:15]  # 取前15个字符 Jul 12 16:37:12
                            try:
                                current_year = datetime.now().year
                                # 拼接年份
                                timestamp_str = f"{timestamp_str} {current_year}"
                                log_time = datetime.strptime(timestamp_str, '%b %d %H:%M:%S %Y')
                            except ValueError:
                                # public.print_log("报错 提取当前时间  当前:{} ".format(log_time))

                                # 记录为当前时间
                                log_time = datetime.now()

                        # log_time = log_time.timestamp()
                        log_time = int(log_time.timestamp())
                        # public.print_log("比较:  结束:{}  当前:{}  开始:{}".format(end, log_time, start))

                        if end >= log_time >= start:
                            match = re.search(status_pattern, line)
                            if match and (match.group(1) != "sent"):
                                # public.print_log("进入记录判断")
                                # 收件人邮箱
                                match1 = re.search(r'to=<([^>]+)>', line)
                                if match1:
                                    recipient = match1.group(1)
                                # 递送状态
                                match2 = re.search(r'status=([^ ]+)', line)
                                if match2:
                                    status = match2.group(1)
                                # 失败详情  (括号里的是失败详情)
                                match3 = re.search(r'\((.*?)\)', line)
                                if match3:
                                    err_info = match3.group(1)
                                # 总延时
                                match4 = re.search(r'delay=(\d+(\.\d+)?)', line)
                                if match4:
                                    delay = match4.group(1)
                                # 各阶段延时
                                match5 = re.search(r'delays=([\d./*]+)', line)
                                if match5:
                                    delays = match5.group(1)
                                # dsn
                                match6 = re.search(r'dsn=([\d.]+)', line)
                                if match6:
                                    dsn = match6.group(1)
                                # 中继服务器
                                match7 = re.search(r'relay=(.*?)(?=,| )', line)
                                if match7:
                                    relay = match7.group(1)

                                name, domain = recipient.split('@')
                                if name == 'postmaster':
                                    continue

                                else:
                                    # 记录详情 # 记录当前失败邮箱  失败原因  根据邮箱去重
                                    # err_one = {}
                                    err_one['recipient'] = recipient
                                    err_one['domain'] = domain
                                    err_one['status'] = status
                                    err_one['delay'] = delay
                                    err_one['delays'] = delays
                                    err_one['dsn'] = dsn
                                    err_one['relay'] = relay
                                    err_one['err_info'] = err_info
                                    if recipient not in seen_recipients:
                                        seen_recipients.add(recipient)
                                        f.write(line + '\n')
                                        self.M('task_count').insert(err_one)

                    except ValueError:
                        print(public.get_error_info())
                        public.print_log(public.get_error_info())
                        pass
            return True
        except Exception as e:
            print(public.get_error_info())
            public.print_log(public.get_error_info())
            return False

    # 获取群发任务的message_ids
    def get_message_ids_from_task_file(self, task_id):
        """获取群发任务的message_ids"""

        message_ids = set()
        task_file_path = f"{self.sent_recipient_path}/msgid_{task_id}.log"
        # task_file_path = f"{self.sent_recipient_path}/{task_name}_msgid.log"
        if os.path.exists(task_file_path):
            data = public.readFile(task_file_path)
            for line in data.splitlines():
                msgid = line.strip()
                msgid = msgid.strip('<>')
                # 去掉msgid两边的<> <173224082931.4191130.12787570563193919720@mail.aapanel.store>
                message_ids.add(msgid)
        # else:
        #     public.print_log("文件不存在{}  ".format(task_file_path))
        message_ids = list(message_ids)
        return message_ids

    def parse_log_time(self, line):
        """日志时间转普通时间戳"""
        try:
            # First try ISO format
            if line[:4].isdigit():
                return int(parse(line[:31]).timestamp())

            # Then try standard format
            current_year = datetime.now().year
            timestamp_str = f"{line[:15]} {current_year}"
            return int(datetime.strptime(timestamp_str, '%b %d %H:%M:%S %Y').timestamp())
        except:
            return int(datetime.now().timestamp())


    def _mail_error_log(self,error_log, task_id):
        """分析日志并记录到群发独立数据库"""
        database_path = f'/www/vmail/bulk/task_{task_id}.db'

        try:

            output_file1 = "/www/server/panel/data/mail/in_bulk/errlog"
            if not os.path.isdir(output_file1):
                os.makedirs(output_file1)

            seen_recipients = set()

            # 获取任务message_ids
            message_ids = self.get_message_ids_from_task_file(task_id)
            if not message_ids:
                print('Message id is empty, skip')
                # public.print_log('Message id is empty, skip')
                return
            # public.print_log('Message id  获取 {}'.format(message_ids))
            # 日期格式 Nov 19 兼容 如果日期是1~9时  数字前自动多加一个空格
            today_ = datetime.now()
            today = today_.strftime('%b ') + (str(today_.day).rjust(2) if today_.day < 10 else str(today_.day))
            today0 = datetime.now().strftime('%b %-d')

            # 日期格式 2024-11-20
            full_date = today_.strftime('%Y-%m-%d')

            # 取出当天的日志
            cmd = f"grep -E '({full_date}|{today})' {self.maillog_path} > /tmp/recent_mass_posting.log"
            if today0 != today:
                cmd = f"grep -E '({full_date}|{today}|{today0})' {self.maillog_path} > /tmp/recent_mass_posting.log"

            public.ExecShell(cmd)

            # self.get_tdlog(full_date,today )
            # 使用当天日志筛选
            log_data = public.readFile('/tmp/recent_mass_posting.log')

            try:
                # 队列id 与 message-id
                queue_id_to_message_id = {}
                # 队列id 与 详情
                queue_id_to_status_info = {}
                # 队列id 与 匹配到的收件信息条
                queue_id_to_line = {}

                # 取到的messageid
                aamsh = []

                # 预编译
                message_id_pattern = re.compile(r'message-id=<([^>]+)>')
                queue_id_pattern = re.compile(r'postfix/\S+\[\d+\]: (\w+):')
                status_pattern = re.compile(r'status=([^ ]+)')
                recipient_pattern = re.compile(r'to=<([^>]+)>')
                status_code_pattern = re.compile(r'\b(\d+)\s(\d+\.\d+\.\d+)\b')

                delay_pattern = re.compile(r'delay=(\d+(\.\d+)?)')
                delays_pattern = re.compile(r'delays=([\d./*]+)')
                dsn_pattern = re.compile(r'dsn=([\d.]+)')
                relay_pattern = re.compile(r'relay=(.*?)(?=,| )')
                err_info_pattern = re.compile(r'\((.*?)\)')

                for line in log_data.splitlines():
                    log_time = self.parse_log_time(line)

                    message_id_match = message_id_pattern.search(line)
                    # 取队列id
                    if message_id_match:
                        message_id = message_id_match.group(1)
                        aamsh.append(message_id)
                        if message_id in message_ids:
                            queue_id_match = queue_id_pattern.search(line)
                            if queue_id_match:
                                queue_id = queue_id_match.group(1)
                                queue_id_to_message_id[queue_id] = message_id

                    # 收件状态消息条
                    status_match = status_pattern.search(line)
                    recipient_match = recipient_pattern.search(line)
                    if status_match and recipient_match:

                        if 'postmaster@' in recipient_match.group(1):
                            # public.print_log("跳过 - postmaster@")
                            continue
                        queue_id_match = queue_id_pattern.search(line)
                        if queue_id_match:
                            queue_id = queue_id_match.group(1)
                            # 统计队列id-- 状态信息

                            queue_id_to_status_info[queue_id] = {
                                'recipient': recipient_match.group(1),
                                'status': status_match.group(1),
                                'delay': delay_pattern.search(line).group(1) if delay_pattern.search(line) else '',
                                'delays': delays_pattern.search(line).group(1) if delays_pattern.search(line) else '',
                                'dsn': dsn_pattern.search(line).group(1) if dsn_pattern.search(line) else '',
                                'relay': relay_pattern.search(line).group(1) if relay_pattern.search(line) else '',
                                'err_info': err_info_pattern.search(line).group(1) if err_info_pattern.search(
                                    line) else '',
                                'created': log_time,
                            }


                            status_code_match = status_code_pattern.search(queue_id_to_status_info[queue_id]['err_info'])

                            if status_code_match:
                                status_code = status_code_match.group(1)
                            else:
                                status_code = 101  # 如果找不到状态码,默认设置为 101

                            queue_id_to_status_info[queue_id]['code'] = int(status_code)

                            queue_id_to_line[queue_id] = line

            except Exception as e:
                print(public.get_error_info())
                public.print_log(public.get_error_info())

                return False

            # 将过滤后的日志写入error_log和database
            insert_data = []
            with open(error_log, 'a') as f:
                for queue_id, message_id in queue_id_to_message_id.items():
                    if queue_id in queue_id_to_status_info:
                        status_info = queue_id_to_status_info[queue_id]
                        # if 'postmaster@' in status_info['recipient']:
                        #     continue

                        if status_info['recipient'] in seen_recipients:
                            continue

                        seen_recipients.add(status_info['recipient'])
                        # 日志记录文件
                        if queue_id_to_line[queue_id]:
                            f.write(f"{queue_id_to_line[queue_id]}\n")

                        # if status_info['status'] != 'sent':  # 取消限制
                        err_data = {
                            'recipient': status_info['recipient'],
                            'domain': status_info['recipient'].split('@')[1],
                            'status': status_info['status'],
                            'delay': status_info['delay'],
                            'delays': status_info['delays'],
                            'dsn': status_info['dsn'],
                            'relay': status_info['relay'],
                            'err_info': status_info['err_info'],
                            'created': status_info['created'],
                            'queue_id': queue_id,
                            'message_id': message_id,
                            'code': status_info['code'],
                        }
                        insert_data.append(err_data)

                    if len(insert_data) >= 5000:
                        with public.S("task_count", database_path) as obj:
                            aa = obj.insert_all(insert_data, option='IGNORE')

                            insert_data = []

                if len(insert_data) > 0:

                    with public.S("task_count", database_path) as obj:
                        aa = obj.insert_all(insert_data, option='IGNORE')
            return True
        except Exception as e:
            print(public.get_error_info())
            public.print_log(public.get_error_info())

            return False

    def _check_ptr_domain(self, domain):
        '''
        检测IP地址是否有PTR记录
        :param ip_address: IP地址字符串
        :return: bool
        '''

        try:
            ip_addresses = self._get_all_ip()
            ip_addresses = [ip for ip in ip_addresses if ip != '127.0.0.1']

            found_ptr_record = False
            result = None
            for ip_address in ip_addresses:
                if ':' in ip_address:  # IPv6
                    reverse_domain = self._ipv6_to_ptr(ip_address)
                else:  # IPv4
                    reverse_domain = '.'.join(reversed(ip_address.split('.'))) + '.in-addr.arpa'

                resolver = dns.resolver.Resolver()
                resolver.timeout = 5
                resolver.lifetime = 10

                try:
                    result = resolver.query(reverse_domain, 'PTR')
                    found_ptr_record = True

                    break
                except dns.resolver.NoAnswer:
                    continue
            # 有记录
            if found_ptr_record:
                values = [str(rdata.target).rstrip('.') for rdata in result]

                for i in values:
                    if i.endswith(domain):
                        return True
                    else:
                        continue
                return False
            return False

        except Exception as e:
            public.print_log(public.get_error_info())
            return False

    def check_ptr_domain(self, domain):
        '''
        查询域名和ip 用于安装webmail
        :param args:
        :return:
        '''
        key = '{0}:{1}'.format(domain, 'PTR')
        session = public.readFile('/www/server/panel/plugin/mail_sys/session.json')
        if session:
            session = json.loads(session)
        else:
            session = {}
        isptr = session[key]['status']
        return isptr

    def get_SECRET_KEY(self):
        path = '/www/server/panel/data/mail/jwt-secret.txt'
        if not os.path.exists(path):
            secretKey = public.GetRandomString(64)
            public.writeFile(path, secretKey)
        secretKey = public.readFile(path)
        return secretKey

    def generate_jwt(self, email, etypes, task_id):
        # 传入邮箱   邮件类型id 邮件类内容
        SECRET_KEY = self.get_SECRET_KEY()
        payload = {
            'email': email,
            # 'etypename': mail_type,
            'etype': etypes,
            'task_id': task_id,
            'exp': datetime.utcnow() + timedelta(days=7)  # 7天过期
        }

        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        return token

    def update_task(self, args):
        # todo 邮件信息改获取id

        try:
            # 传入任务id
            if not hasattr(args, 'id') or args.get('id/d', 0) == 0:
                return public.returnMsg(False, public.lang('参数错误: id'))
            task_old = self.M('email_task').where('id=?', args.get('id/d', 0)).find()
            if not isinstance(task_old, dict):
                return public.returnMsg(False, public.lang('Task does not exist'))
            if not hasattr(args, 'temp_id') or args.get('temp_id/d', 0) == 0:
                return public.returnMsg(False, public.lang('参数错误: temp_id'))
            temp_id = args.temp_id

            if not hasattr(args, 'addresser') or args.get('addresser/s', '') == '':
                return public.returnMsg(False, public.lang('参数错误: addresser'))
            if not hasattr(args, 'task_name') or args.get('task_name/s', '') == '':
                return public.returnMsg(False, public.lang('参数错误: task_name'))

            task_name = args.get('task_name', '')

            # 新增群发邮件类型   传id
            if not hasattr(args, 'etypes') or args.get('etypes', '') == '':
                etypes = '1'
            else:
                etypes = args.etypes

            etype_list = etypes.split(',')

            # 判断  etype 必须要有数据
            with public.S("mail_unsubscribe", '/www/vmail/mail_unsubscribe.db') as obj:
                count = obj.where_in('etype', etype_list).where('active', 1).count()
            if not count:
                return public.returnMsg(False, 'The selected contact list is empty')
            namemd5 = public.md5(task_name)
            # 收件人路径(上传后处理的文件)
            # 校验后的文件就是  /{md5任务名}_verify_{原始文件名}
            recipient_path = "{}/recipient/{}_verify_{}".format(self.in_bulk_path, namemd5, etypes)
            # 处理收件人列表
            recipient_count, black_num, abnormal_num = self.processing_recipient_v2(recipient_path, etype_list)

            # # 用户剩余额度
            # user_quota = self._get_user_quota()
            # # 占用额度
            # occupied = self.get_quota_occupation()['occupation']
            # if user_quota == 0:
            #     return public.returnMsg(False, public.lang('There is no sending quota, please purchase the refill pack or wait for refresh next month'))
            #
            # if user_quota - occupied < recipient_count:
            #     # usable = recipient_count - (user_quota + occupied)
            #
            #     return public.returnMsg(False, public.lang('The remaining amount {} the amount occupied by the unfinished task {} the amount needed for the task to be sent {}, please purchase the supplementary package', user_quota,occupied, recipient_count))

            addresser = args.get('addresser', '')
            old_task_id = args.get('id', 0)  # 旧任务的id

            # 是否记录到发件箱
            is_record = args.get('is_record/d', 0)
            is_record = 1 if is_record else 0

            # 是否增加退订 unsubscribe   0 1
            unsubscribe = args.get('unsubscribe/d', 0)
            unsubscribe = 1 if unsubscribe else 0

            # 线程数
            threads = args.get('threads/d', 0)
            threads = int(threads) if threads else 0

            # 是否立即执行?  1 暂停中     0 未暂停  默认不暂停
            if not hasattr(args, 'pause') or args.get('pause/d', 0) == 0:
                pause = 0
            else:
                pause = 1
            # 新增字段
            if not hasattr(args, 'full_name') or args.get('full_name', '') == '':
                full_name = ''
            else:
                full_name = args.get('full_name', '')
            # 备注
            remark = args.get('remark', '')

            # 邮件主题 可为空
            subject = args.get('subject', '')

            # 任务开始时间
            if not hasattr(args, 'start_time') or args.get('start_time/d', 0) == 0:
                start_time = int(time.time())
            else:
                start_time = int(args.start_time)

            task_process = 0  # 是否立即执行

            self.init_send()
            # 二次导入文件

            # 删除旧任务 旧数据库
            args1 = public.dict_obj()
            args1.task_id = old_task_id
            dfg = self.delete_task(args1)


            # 添加邮件表
            timestamp = int(time.time())
            task_id = 0
            try:
                # 添加任务表
                task_id = self.M('email_task').add(
                    'task_name,addresser,recipient_count,task_process,pause,temp_id,is_record,unsubscribe,threads,created,modified,start_time,remark,etypes,recipient,subject,full_name',
                    (task_name, addresser, recipient_count, task_process, pause, temp_id, is_record, unsubscribe, threads,
                     timestamp, timestamp, start_time, remark, etypes, recipient_path, subject,full_name))

                # 记录发送失败日志
                error_log = "/www/server/panel/data/mail/in_bulk/errlog/task_{}.log".format(task_id)
                if not os.path.exists(error_log):
                    public.WriteFile(error_log, '')
                # 生成新数据库
                self.create_task_database(task_id)
                # 添加执行的定时任务
                self._task_mail_send1()
                self._task_mail_send2()
                # # 写入额度占用
                # self.add_quota_occupation(str(task_id), recipient_count)


                return public.returnMsg(True, public.lang('任务添加成功'))
            except Exception as e:
                public.print_log(public.get_error_info())
                # 删除已创建的任务
                # self.M('temp_email').where('id=?', temp_id).delete()
                self.M('email_task').where('id=?', task_id).delete()
                return public.returnMsg(False, public.lang('任务添加失败: [{}]', str(e)))


        except Exception as e:

            public.print_log(public.get_error_info())

    # 一些操作 为了发件顺利
    def init_send(self):
        # # 更新配置让黑名单生效
        # shell_str = 'systemctl reload postfix'
        # public.ExecShell(shell_str)

        # 添加前清除之前任务标记
        start_mark = '/www/server/panel/plugin/mail_sys/start_Task.pl'
        start_send = '/www/server/panel/plugin/mail_sys/start_Send.pl'
        # end_mark = '/www/server/panel/plugin/mail_sys/end_Task.pl'
        if os.path.exists(start_mark):
            os.remove(start_mark)
        if os.path.exists(start_send):
            os.remove(start_send)
        # if os.path.exists(end_mark):
        #     os.remove(end_mark)

        # SendTaskId = '/www/server/panel/plugin/mail_sys/SendTaskid.pl'
        # if os.path.exists(SendTaskId):
        #     os.remove(SendTaskId)

    # 导入收件人后跳过黑名单
    def recipient_blacklist(self):

        # 判断是否开启黑名单
        if not self._recipient_blacklist_status():
            # return public.returnMsg(False, 'Blacklist is not open')
            return []

        postfix_recipient_blacklist = '/etc/postfix/blacklist'
        # 黑名单文件是否存在
        if not os.path.exists(postfix_recipient_blacklist):
            return []

        try:
            with open(postfix_recipient_blacklist, 'r') as file:
                emails = file.read().splitlines()
        except Exception as e:
            return []

        # 去掉  REJECT
        if emails:
            emails = [email.split()[0] for email in emails]
        else:
            return []

        return emails

    def _recipient_blacklist_status(self):
        # 查看配置是否有黑名单限制
        postfix_main_cf = "/etc/postfix/main.cf"
        result = public.readFile(postfix_main_cf)

        match = re.search(r"smtpd_recipient_restrictions\s*=\s*(.+)", result)
        if not match:
            return False
        restrictions = match.group(1)
        if 'check_recipient_access hash:/etc/postfix/blacklist' not in restrictions:
            return False
        else:
            return True

    def _get_user_free_quota(self):
        """获取当月免费额度   免费版2w 专业版12w"""
        endtime = public.get_pd()[1]
        curtime = int(time.time())

        quota = 20000
        # 专业版未过期
        if endtime == 0 or endtime > curtime:
            quota = 120000
        # todo 测试提交 先降低免费额度
        # quota = 1500
        return quota

    def _get_user_pack_quota(self):
        """获取补充包信息"""
        data = {
            'total': 0,
            'used': 0,
            'available': 0,
            'packages': [],
        }

        from panelPlugin import panelPlugin
        pp = panelPlugin()
        a = public.to_dict_obj({})
        # a.focre = 1

        try:
            softList = pp.get_soft_list(a)
        except:
            softList = {}

        # expansions['mail']    total  used   'available': 0, 'packages': []
        if softList.get('expansions', None):
            mail = softList['expansions']['mail']

            data['total'] = mail.get('total', 0)
            data['used'] = mail.get('used', 0)
            data['available'] = mail.get('available', 0)
            data['packages'] = mail.get('packages', [])

        return data

    # 获取用户当前额度
    def _get_user_quota(self):
        """用户当月可用额度  免费剩余+付费包剩余"""
        # 本月免费
        quota = self._get_user_free_quota()

        # 本月发送
        senduse = self._get_month_senduse()

        # 补充包
        pack = self._get_user_pack_quota()

        # 计算补充包剩余用量
        # packnum = pack['total']-pack['used'] if pack['total'] > pack['used'] else 0
        packnum = pack['available']
        free = quota-senduse if quota > senduse else 0

        user_quota = free + packnum


        # # 额度为0  检查  开-> 关闭   关->不动
        # if user_quota == 0:
        #     public.print_log('check_mail_quota_failed: quota: {} senduse: {} pack: {}'.format(quota, senduse, pack))
        #     self.add_domain_restrictions()
        # else:
        #     # 关闭限制
        # if self._check_sender_domain_restrictions():
        #     self._domain_restrictions_switch(False)

        return user_quota

    # 获取本月发件数   分开计算 避免被修改
    def _get_month_senduse(self):
        """获取本月发件数   本地和线上比较取最大   本地改数据库+当天"""
        # 两种方式获取本月发件数
        dnum = self.get_data_month_count(None)
        todaynum = self.get_today_sendnum()

        pack = self._get_user_pack_quota()  # 补充包使用信息
        quota = self._get_user_free_quota()  # 当月免费额度
        pack_use = pack['used']  # 获取到的线上补充包使用量
        cnum = 0
        if pack_use > 0:
            cnum = pack_use + quota

        senduse = dnum + todaynum

        # 统计到本月发件小于线上  有问题
        if senduse < cnum:
            return cnum
        else:
            return senduse

    def get_today_sendnum(self):

        # 有缓存 跳过
        cache_key = 'mail_sys:get_today_sendnum'
        cache = public.cache_get(cache_key)

        if cache:
            return cache
        output, err = public.ExecShell(
            f'pflogsumm -d today --verbose-msg-detail --zero-fill --iso-date-time --rej-add-from {self.maillog_path}')

        # 数据库本地时间
        data = self._pflogsumm_data_treating(output)

        # 日志存入数据库
        all = 0
        if data.get('stats_dict', None):
            all = data['stats_dict'].get('delivered', 0)

        # 缓存86400s  缓存1小时 每隔一小时检查下有没有补充完
        public.cache_set(cache_key, all, 15)
        return all

    def get_yesterday_count(self):
        """ 昨日数据插入概览统计表 """

        # 有缓存 跳过
        cache_key = 'mail_sys:get_yesterday_count'
        cache = public.cache_get(cache_key)

        if cache:
            return

        # 查询数据库是否有记录 有 跳过
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_midnight = datetime(yesterday.year, yesterday.month, yesterday.day)
        yesterday_0 = int(time.mktime(yesterday_midnight.timetuple()))
        yesterday_24 = yesterday_0 + 86400

        with self.M("log_analysis") as obj:
            query = obj.where('time >=? and time <?', (yesterday_0, yesterday_24)).count()
        # 记录完整才能跳过
        if query == 24:
            # public.print_log("昨天已记录")
            return


        output, err = public.ExecShell(
            f'pflogsumm -d yesterday --verbose-msg-detail --zero-fill --iso-date-time --rej-add-from {self.maillog_path}')

        # 数据库本地时间
        data = self._pflogsumm_data_treating(output, day='yesterday')

        # public.print_log(f"昨天要添加--{data['hourly_stats']}")
        # 日志存入数据库
        if data.get('hourly_stats', None) and len(data['hourly_stats']) == 24:
            # a = {'time': 1733846400, 'received': 0, 'delivered': 0, 'deferred': 194, 'bounced': 0, 'rejected': 0}


            try:
                with public.S("log_analysis", "/www/vmail/postfixadmin.db") as obj:
                    aa = obj.insert_all(data['hourly_stats'], option='IGNORE')
            except:
                public.print_log(public.get_error_info())

        # # 提交昨日
        # msg = self.upload_yesterday_email_usage(output)
        # if msg:
        #     public.print_log(f"upload: {msg}")
        # 缓存86400s  缓存1小时 每隔一小时检查下有没有补充完
        public.cache_set(cache_key, 1, 3600)
        return

    def upload_yesterday_email_usage(self, output):
        """ 上传补充包使用量 """

        # 判断本月发件额度是否用完 没用完不上传
        # 本月免费
        quota = self._get_user_free_quota()
        # 本月发送
        senduse = self._get_month_senduse()
        # 免费>发件数  不提交
        upload = False if quota > senduse else True
        if not upload:
            # public.print_log("免费额度未用完,暂不提交")
            return False

        #  转为utc时间
        data = self._pflogsumm_data_treating(output, timezone='utc')

        if not isinstance(data['hourly_stats'], list):
            # public.print_log("数据获取有误1")
            return False
        data = data['hourly_stats']
        if len(data) != 24:
            # public.print_log("数据获取有误2")
            return False

        # todo  上传今日发件量
        submat_data = []
        for i in data:
            all = i['delivered']
            if all == 0:
                continue
            submat_data.append({
                "day_time_utc": i['time'],
                "used": all
            })
        if not submat_data:
            # public.print_log("昨天没有数据")
            return False

        import panelAuth
        import requests
        from BTPanel import session
        cloudUrl = '{}/api/panel/submit_expand_pack_used'.format(public.OfficialApiBase())
        pdata = panelAuth.panelAuth().create_serverid(None)
        url_headers = {}
        if 'token' in pdata:
            url_headers = {"authorization": "bt {}".format(pdata['token'])}

        pdata['environment_info'] = json.dumps(public.fetch_env_info())
        pdata['data'] = submat_data
        pdata['expand_pack_type'] = "mail"

        listTmp = requests.post(cloudUrl, json=pdata, headers=url_headers)
        ret = listTmp.json()

        if not ret['success']:
            print(f"|-{ret['res']}")
            return ret['res']
        else:
            # 刷新授权状态 更新数据
            public.load_soft_list()
            public.refresh_pd()

    # 数据库 获取本月发件数
    def get_data_month_count(self, args):
        """数据库 获取本月发件数"""
        # 		"received": 0,  //接收
        # 		"delivered": 0,  //发送
        # 		"forwarded": 0,  // 转发
        # 		"deferred": 5,   //延迟
        # 		"bounced": 3,   // 退回
        # 		"rejected": 0,  // 拒绝

        # 取缓存
        cache_key = 'mail_sys:get_data_month_count'
        cache = public.cache_get(cache_key)

        if cache:
            return cache


        # 获取 本月月初0点时间戳
        now = datetime.now()
        first_day_of_month = datetime(now.year, now.month, 1)
        timestamp_first_day = int(time.mktime(first_day_of_month.timetuple()))

        # 获取当前时间戳
        timestamp_now = int(time.time())
        try:
            # 发送+退回+拒绝
            total_fields = "sum(received) as received, sum(delivered) as delivered, sum(deferred) as deferred, sum(bounced) as bounced, sum(rejected) as rejected, sum(delivered+bounced+rejected) as sentall"
            query = self.M('log_analysis').field(total_fields).where('time between ? and ?',
                                                                     (timestamp_first_day, timestamp_now)).find()

            if isinstance(query, str):
                # public.print_log("本月发件数据有误-- {}".format(query))
                return 0

            sentall = query['sentall']

            public.cache_set(cache_key, sentall, 15)
            return sentall
        except:
            public.print_log(public.get_error_info())
            return 0

    # 命令 获取本月发件数
    def get_pflogsumm_month_count(self, args):
        """命令 获取本月发件数"""
        # 取缓存
        cache_key = 'mail_sys:get_pflogsumm_month_count'
        cache = public.cache_get(cache_key)

        if cache:
            return cache
        log_data = public.readFile(self.maillog_path)
        if not log_data:
            # public.print_log("日志文件为空或无法读取")
            return 0

        # 获取当前月份
        current_time = time.localtime()
        current_year = time.strftime("%Y", current_time)
        current_month_num = time.strftime("%m", current_time)  # 数字格式月份，如 "11"
        current_month_abbr = time.strftime("%b", current_time)  # 字母格式月份，如 "Nov"

        # 获取日志的第一行，判断日志格式
        first_line = log_data.splitlines()[0] if log_data else None

        if first_line is None:
            # public.print_log("日志文件为空")
            return 0

        try:

            # 判断第一行是数字格式还是字母格式
            if first_line[:2].isdigit():
                # 数字开头 "2024-11-12T..." 格式的日志
                date = f"{current_year}-{current_month_num}"
                public.ExecShell(f'grep "{date}" {self.maillog_path} > /tmp/mail_filtered.log')
            else:
                # 字母开头 "Jul 12 16:37:12" 格式的日志
                public.ExecShell(f'grep "{current_month_abbr}" {self.maillog_path} > /tmp/mail_filtered.log')

            output, err = public.ExecShell('pflogsumm /tmp/mail_filtered.log')
            # public.print_log("00 output  {}".format(output))
            # 处理命令后返回的输出

            res = self.parse_pflogsumm_grand_totals(output)

            stats_dict = res['stats_dict']
            # public.print_log(f"当月统计-- {stats_dict}")

            sentall = stats_dict.get('delivered', 0) + stats_dict.get('bounced', 0) + stats_dict.get('rejected', 0)

            public.cache_set(cache_key, sentall, 15)
            return sentall

        except Exception as e:
            public.print_log(f"get_pflogsumm_month_count: {e}")

    # 处理命令返回数据
    def   _pflogsumm_data_treating(self, output, timezone=None, day='today'):
        """ 处理命令返回数据 -- 当天/昨天"""
        stats_dict = {}

        # 使用正则表达式来匹配和提取关键信息
        patterns = [
            r'(\d+)\s+received',
            r'(\d+)\s+delivered',
            r'(\d+)\s+forwarded',
            r'(\d+)\s+deferred\s+\((\d+)\s+deferrals\)',
            r'(\d+)\s+bounced',
            r'(\d+)\s+rejected\s+\((\d+)%\)',
            r'(\d+)\s+reject\s+warnings',
            r'(\d+)\s+held',
            r'(\d+)\s+discarded\s+\((\d+)%\)',
            r'(\d+)\s+bytes\s+received',
            r'(\d+)k\s+bytes\s+delivered',
            r'(\d+)\s+senders',
            r'(\d+)\s+sending\s+hosts/domains',
            r'(\d+)\s+recipients',
            r'(\d+)\s+recipient\s+hosts/domains'
        ]

        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                # 将找到的数字转换为整数并存入字典
                stats_dict[pattern] = int(match.group(1))

        friendly_names = {
            r'(\d+)\s+received': 'received',
            r'(\d+)\s+delivered': 'delivered',
            r'(\d+)\s+forwarded': 'forwarded',
            r'(\d+)\s+deferred\s+\((\d+)\s+deferrals\)': 'deferred',
            r'(\d+)\s+bounced': 'bounced',
            r'(\d+)\s+rejected\s+\((\d+)%\)': 'rejected',
            r'(\d+)\s+reject\s+warnings': 'reject_warnings',
            r'(\d+)\s+held': 'held',
            r'(\d+)\s+discarded\s+\((\d+)%\)': 'discarded',
            r'(\d+)\s+bytes\s+received': 'bytes_received',
            r'(\d+)k\s+bytes\s+delivered': 'bytes_delivered_kilo',
            r'(\d+)\s+senders': 'senders',
            r'(\d+)\s+sending\s+hosts/domains': 'sending_hosts_domains',
            r'(\d+)\s+recipients': 'recipients',
            r'(\d+)\s+recipient\s+hosts/domains': 'recipient_hosts_domains'
        }

        stats_dict = {friendly_names[key]: value for key, value in stats_dict.items() if key in friendly_names}
        keys_to_remove = [
            "reject_warnings",
            "held",
            "discarded",
            "bytes_received",
            "senders",
            "sending_hosts_domains",
            "recipients",
            "recipient_hosts_domains"
        ]

        for key in keys_to_remove:
            stats_dict.pop(key, None)

        # 使用正则表达式来匹配并捕获每个小时的统计数据
        pattern = r'(\d{2}:\d{2}-\d{2}:\d{2})\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)'
        hourly_stats_list = []
        matches = re.findall(pattern, output)

        # 遍历所有匹配的结果并构建嵌套字典
        for match in matches:
            hour = match[0]
            received = int(match[1])
            delivered = int(match[2])
            deferred = int(match[3])
            bounced = int(match[4])
            rejected = int(match[5])
            # utc 时间 用于提交

            if timezone == 'utc':
                hourly_stats_obj = {
                    "time": self._str_to_tstp_utc(hour),
                    'received': received,
                    'delivered': delivered,
                    'deferred': deferred,
                    'bounced': bounced,
                    'rejected': rejected,
                }
            else:  # 系统时间
                hourly_stats_obj = {
                    "time": self._str_to_tstp(hour),
                    'received': received,
                    'delivered': delivered,
                    'deferred': deferred,
                    'bounced': bounced,
                    'rejected': rejected,
                }
            if day == 'yesterday':
                hourly_stats_obj['time'] = hourly_stats_obj['time']-86400

            hourly_stats_list.append(hourly_stats_obj)


        data = {
            "hourly_stats": hourly_stats_list,
            "stats_dict": stats_dict,
        }
        return data

    def parse_pflogsumm_grand_totals(self, output):
        """ 处理命令返回数据 """
        stats_dict = {}

        patterns = [
            r'(\d+)\s+received',
            r'(\d+)\s+delivered',
            r'(\d+)\s+forwarded',
            r'(\d+)\s+deferred\s+\((\d+)\s+deferrals\)',
            r'(\d+)\s+bounced',
            r'(\d+)\s+rejected\s+\((\d+)%\)',
            r'(\d+)\s+reject\s+warnings',
            r'(\d+)\s+held',
            r'(\d+)\s+discarded\s+\((\d+)%\)',
            r'(\d+)\s+bytes\s+received',
            r'(\d+)k\s+bytes\s+delivered',
            r'(\d+)\s+senders',
            r'(\d+)\s+sending\s+hosts/domains',
            r'(\d+)\s+recipients',
            r'(\d+)\s+recipient\s+hosts/domains'
        ]

        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                stats_dict[pattern] = int(match.group(1))
                # public.print_log(f"match-- {match}")
        friendly_names = {
            r'(\d+)\s+received': 'received',
            r'(\d+)\s+delivered': 'delivered',
            r'(\d+)\s+forwarded': 'forwarded',
            r'(\d+)\s+deferred\s+\((\d+)\s+deferrals\)': 'deferred',
            r'(\d+)\s+bounced': 'bounced',
            r'(\d+)\s+rejected\s+\((\d+)%\)': 'rejected',
            r'(\d+)\s+reject\s+warnings': 'reject_warnings',
            r'(\d+)\s+held': 'held',
            r'(\d+)\s+discarded\s+\((\d+)%\)': 'discarded',
            r'(\d+)\s+bytes\s+received': 'bytes_received',
            r'(\d+)k\s+bytes\s+delivered': 'bytes_delivered_kilo',
            r'(\d+)\s+senders': 'senders',
            r'(\d+)\s+sending\s+hosts/domains': 'sending_hosts_domains',
            r'(\d+)\s+recipients': 'recipients',
            r'(\d+)\s+recipient\s+hosts/domains': 'recipient_hosts_domains'
        }

        stats_dict = {friendly_names[key]: value for key, value in stats_dict.items() if key in friendly_names}
        # public.print_log(f"当月统计-- {stats_dict}")
        data = {"stats_dict": stats_dict}
        return data
    # 获取系统时间与utc的差值
    def _get_asd(self):
        """获取系统时间与utc的差值"""
        # 系统时间戳
        current_local_time = datetime.now()
        current_local_timestamp = int(current_local_time.timestamp())

        # 获取当前 UTC 时间的时间戳
        current_utc_time = datetime.utcnow()
        current_utc_timestamp = int(current_utc_time.timestamp())

        # 计算时区差值（秒）
        timezone_offset = current_local_timestamp - current_utc_timestamp

        if timezone_offset > 0:  # 东时区   需要减
            return timezone_offset, True
        else:  # 西时区
            return abs(timezone_offset), False

    def _str_to_tstp_utc(self, start_time):
        """00:00-01:00改为utc时间戳"""
        # start_time :  00:00-01:00
        current_date = datetime.now().date()
        start_time = start_time.split('-')[0]
        # 将当前日期和开始时间合并
        combined_datetime_str = f"{current_date} {start_time}"
        combined_datetime = datetime.strptime(combined_datetime_str,
                                              "%Y-%m-%d %H:%M")  # combined_datetime: 2024-11-18 23:00:00

        unix_timestamp = int(combined_datetime.timestamp())
        h, e = self._get_asd()
        if e:
            unix_timestamp = unix_timestamp - h
        else:

            unix_timestamp = unix_timestamp + h
        return unix_timestamp

    def _str_to_tstp(self, start_time):
        """00:00-01:00改为时间戳"""
        # start_time :  00:00-01:00
        current_date = datetime.now().date()
        start_time = start_time.split('-')[0]
        # 将当前日期和开始时间合并
        combined_datetime_str = f"{current_date} {start_time}"
        combined_datetime = datetime.strptime(combined_datetime_str, "%Y-%m-%d %H:%M")
        # combined_datetime: 2024-11-18 23:00:00
        unix_timestamp = int(combined_datetime.timestamp())
        return unix_timestamp

    # 统计额度占用
    # {"任务名":数量, "任务名":数量, }
    def get_quota_occupation(self):
        '''
         统计额度占用
        :param args:
        :return:
        '''
        # 额度占用文件
        path = '/www/server/panel/plugin/mail_sys/data/quota_occupation.json'

        if os.path.exists(path):
            data = public.readFile(path)
            try:
                data = json.loads(data)
            except:
                pass
        else:
            data = {}
        occupation = 0
        if data:
            occupation = sum(data.values())
        res = {
            "occupation": occupation,
            "info": data
        }
        return res

    # 新增
    def add_quota_occupation(self, task_id, occupation):
        '''
         新增 任务占用额度
        :param args: task_id str  任务id
        :param args: occupation int  占用数量
        :return:
        '''

        # 额度占用文件
        path = '/www/server/panel/plugin/mail_sys/data/quota_occupation.json'
        data = {}
        if os.path.exists(path):
            data = public.readFile(path)
            try:
                data = json.loads(data)
            except:
                pass
        data[task_id] = int(occupation)
        public.writeFile(path, public.GetJson(data))

        return True

    # 删除  (任务完成   任务删除 需要调用)
    def del_quota_occupation(self, task_id):
        '''
         删除指定任务占用的额度
        :param args: task_id str   任务id
        :return: bool
        '''
        # 额度占用文件
        path = '/www/server/panel/plugin/mail_sys/data/quota_occupation.json'

        if os.path.exists(path):
            data = public.readFile(path)
            try:
                data = json.loads(data)
            except:
                pass
            # 删除指定键值对
            if task_id in data:
                del data[task_id]  # 删除字典中对应的键值对
            else:
                return False
        else:
            return False

        public.writeFile(path, public.GetJson(data))

        return True

    # 生成批量发件任务的数据库    兼容(如果查不到数据库 就从原始数据库中查
    def Ms(self, table_name, db_path):
        import db
        sql = db.Sql()
        sql._Sql__DB_FILE = db_path
        sql._Sql__encrypt_keys = []
        return sql.table(table_name)

    def create_task_database(self, taskid):
        """生成群发任务的数据库"""
        db_dir = '/www/vmail/bulk'
        db_path = f'{db_dir}/task_{taskid}.db'
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
            os.system('chown -R vmail:mail /www/vmail/bulk')
        # 建表
        # 全量统计  message_id与收件人联合唯一
        sql = '''CREATE TABLE IF NOT EXISTS `task_count` (
          `id` INTEGER  PRIMARY KEY AUTOINCREMENT,
          `queue_id` varchar(320)  NOT NULL,             -- 邮件队列id
          `message_id` TEXT NOT NULL,          -- 邮件 message_id
          `created` INTEGER NOT NULL,               -- 邮件时间 时间戳
          `recipient` varchar(320) NOT NULL,        -- 收件人
          `delay` varchar(320) NOT NULL,            -- 延时
          `delays` varchar(320) NOT NULL,           -- 各阶段延时
          `dsn` varchar(320) NOT NULL,              -- dsn
          `relay` text NOT NULL,                    -- 中继服务器
          `domain` varchar(320) NOT NULL,             -- 域名
          `status` varchar(255) NOT NULL,             -- 状态
          `code` INTEGER,                           -- 状态码   250   5xx  101
          `err_info` text NOT NULL,                   -- 详情
          UNIQUE(message_id,recipient)
          );'''

        with self.Ms("", db_path) as obj:
            aa = obj.execute(sql, ())


    def get_abnormal_recipient(self):  # 拒绝 + 延迟3
        """获取异常邮件  拒绝状态 + 延迟3次"""
        abnormal_list = []
        with public.S("abnormal_recipient", '/www/vmail/abnormal_recipient.db') as obj1:
            abnormal = obj1.where('count >=? OR status =?', (3, 'bounced')).select()
        if abnormal:
            abnormal_list = [i['recipient'] for i in abnormal]
        return abnormal_list

    # 获取发件进度
    def get_send_progress(self, task_id):
        """
        获取邮件发送进度。

        :param task_id: 任务id
        :return: 发送进度（百分比）
        """
        database_path = f'/www/vmail/bulk/task_{task_id}.db'
        with public.S("task_count", database_path) as obj:
            total_sent = obj.count()
        return total_sent

    # 检查域名限制状态
    def _check_sender_domain_restrictions(self):
        """ 是否限制域名发件  False未限制  True限制"""
        # 查看配置是否有黑名单限制
        result = public.readFile(self.postfix_main_cf)

        match = re.search(r"smtpd_sender_restrictions\s*=\s*(.+)", result)
        if not match:
            return False

        restrictions = match.group(1)
        if 'check_sender_access hash:/etc/postfix/sender_black' not in restrictions:
            return False
        else:
            return True

    # 开关 在用  smtpd_sender_restrictions
    def _domain_restrictions_switch(self, status):
        """ 域名限制 开关  开启 Ture, 关闭 False"""
        # 开启 Ture,  关闭 False
        try:
            # 读取现有的 Postfix 主配置文件内容
            result = public.readFile(self.postfix_main_cf)
            if not result:
                return False

            # 定义黑名单条目
            blacklist_entry_parts = ['check_sender_access', 'hash:/etc/postfix/sender_black']
            blacklist_entry_str = ' '.join(blacklist_entry_parts)

            # 查找现有的 smtpd_sender_restrictions 配置
            match = re.search(r"smtpd_sender_restrictions\s*=\s*(.+)", result, re.IGNORECASE)

            if status:
                # 如果选择开启，并且没有找到 smtpd_sender_restrictions，则添加新的配置项
                if not match:
                    updated_config = f"{result}\nsmtpd_sender_restrictions = {blacklist_entry_str}\n"
                    public.writeFile(self.postfix_main_cf, updated_config)
                    # public.print_log("新增 smtpd_sender_restrictions 并启用黑名单检查")
                else:
                    current_restrictions = match.group(1).split()
                    # 如果未包含黑名单检查条目，则添加
                    if not all(part in current_restrictions for part in blacklist_entry_parts):
                        current_restrictions.extend(blacklist_entry_parts)
                        updated_config = re.sub(
                            r"smtpd_sender_restrictions\s*=.*",
                            f"smtpd_sender_restrictions = {' '.join(current_restrictions)}",
                            result,
                            flags=re.IGNORECASE
                        )
                        public.writeFile(self.postfix_main_cf, updated_config)
                        # public.print_log("已存在的 smtpd_sender_restrictions 中添加黑名单检查")

            else:
                # 关闭
                if match:
                    current_restrictions = match.group(1).split()
                    # 移除黑名单检查条目
                    if all(part in current_restrictions for part in blacklist_entry_parts):
                        for part in blacklist_entry_parts:
                            while part in current_restrictions:
                                current_restrictions.remove(part)

                        # 如果移除后没有其他限制条件，则删除整个 smtpd_sender_restrictions 行
                        if not current_restrictions:
                            updated_config = re.sub(
                                r"smtpd_sender_restrictions\s*=.*\n?", "", result, flags=re.IGNORECASE
                            )

                        else:
                            updated_config = re.sub(
                                r"smtpd_sender_restrictions\s*=.*",
                                f"smtpd_sender_restrictions = {' '.join(current_restrictions)}",
                                result,
                                flags=re.IGNORECASE
                            )

                        public.writeFile(self.postfix_main_cf, updated_config)
                    else:
                        ...
                        # public.print_log("移除黑名单检查条目失败：条目不存在")
                else:
                    ...
                    # public.print_log("尝试关闭黑名单检查，但 smtpd_sender_restrictions 未配置")

            # 重载配置
            shell_str = '''
            postmap /etc/postfix/sender_black
            systemctl reload postfix
            '''
            public.ExecShell(shell_str)

            return True
        except Exception as e:
            print(f"Error managing recipient blacklist: {e}")
            return False

    # 添加域名黑名单
    def add_domain_restrictions(self, ):
        """ 域名加入黑名单 """

        if not os.path.exists(self.domain_restrictions):
            public.writeFile(self.domain_restrictions, '')

        try:
            # 获取域名
            domains = self.get_domain_name()

            # 构造要追加的行的集合
            add_set = {f"{domain} REJECT\n" for domain in domains}
            try:
                formatted_string = ''.join(add_set)
                aa = public.writeFile(self.domain_restrictions, formatted_string)

            except Exception as e:
                return public.returnMsg(False, e)

            # 开启域名限制
            if not self._check_sender_domain_restrictions():
                self._domain_restrictions_switch(True)

            shell_str = '''
            postmap /etc/postfix/sender_black
            systemctl reload postfix
            '''
            public.ExecShell(shell_str)

        except:
            public.print_log(public.get_error_info())

        return

    def get_domain_name(self):
        with self.M("domain") as obj:
            data_list = obj.order('created desc').field("domain").select()
        data_list = [i['domain'] for i in data_list]
        return data_list


    def get_email_temp_list(self, args):
        '''
        邮件模版列表
        :param args:
        :return:
        '''

        p = int(args.p) if 'p' in args else 1
        rows = int(args.size) if 'size' in args else 12

        if "search" in args and args.search != "":
            where_str = "name LIKE ? AND is_temp =?"
            where_args = (f"%{args.search.strip()}%", 1)
        else:
            # 避免空条件报错
            where_str = "is_temp =?"
            where_args = (1,)

        with public.S("temp_email", '/www/vmail/postfixadmin.db') as obj:
            count = obj.where(where_str, where_args).select()
            data_list = obj.order('created', 'DESC').limit(rows, (p - 1) * rows).where(where_str, where_args).select()

            return {'data': data_list, 'total': len(count)}

    def get_email_temp_render(self, args):
        '''
        所有邮件模版 渲染数据
        :param args:
        :return:
        '''
        cache_key = 'mail_sys:get_email_temp_render'
        cache = public.cache_get(cache_key)
        if cache:
            return cache

        with public.S("temp_email", '/www/vmail/postfixadmin.db') as obj:
            temp = obj.where('is_temp', 1).field('id,type,render').select()
        for t in temp:
            if t['type']:
                render_data = ''
                if os.path.exists(t['render']):
                    render_data = public.readFile(t['render'])

                t['render_data'] = render_data
        public.cache_set(cache_key, data, 120)
        return temp
    def get_email_temp(self, args):
        '''
        邮件模版列表 无分页
        :param args:
        :return:
        '''

        with public.S("temp_email", '/www/vmail/postfixadmin.db') as obj:
            data_list = obj.order('created', 'DESC').where('is_temp =?', (1,)).field('id,name').select()
        return data_list



    def add_email_temp(self, args):
        '''
        新增邮件模版
        :param args:
        :return:
        '''

        if not hasattr(args, 'temp_name'):
            return public.returnMsg(False, public.lang('参数错误: temp_name'))
        if not hasattr(args, 'type'):
            return public.returnMsg(False, public.lang('参数错误: type'))

        temp_type = int(args.type)
        name = args.temp_name
        timestimp = int(time.time())

        path = "{}/content".format(self.in_bulk_path)

        # 时间戳+名称+随机数  生成md5
        content_s = name+'content'+str(timestimp)+public.GetRandomString(5)
        render_s = name+'render'+str(timestimp)+public.GetRandomString(5)

        content_name = public.md5(content_s)
        render_name = public.md5(render_s)
        content_path = "{}/{}".format(path, content_name)
        render_path = "{}/{}".format(path, render_name)

        content = """<table width="500px" style="margin: 0px auto;"><tr><td><div style="background-color: transparent; padding: 0px;"><table style="width: 100%;"><tr><td style="width: 100%;"></td></tr></table></div></td></tr><tr><td><div style="background-color: transparent; padding: 0px;"><table style="width: 100%;"><tr><td style="width: 100%; text-align: center; padding: 10px;"><div style="text-align: center; padding: 10px;"><div style="border-top: 1px solid rgb(187, 187, 187); width: 100%; display: inline-block; line-height: 1px; height: 0px; vertical-align: middle;"></div></div><a href="__UNSUBSCRIBE_URL__" target="_blank" style="padding: 10px 20px; border-radius: 4px; width: auto; line-height: 120%; color: rgb(162, 162, 162); display: inline-block; background-color: rgb(255, 255, 255); font-size: 13px; text-align: center; font-weight: normal;">Unsubscribe</a></td></tr></table></div></td></tr></table>"""
        render = """{"version":1.3,"columns_source":["32792fd2c7","8d15a39e2d"],"column_map":{"32792fd2c7":{"type":"columns","name":"列","key":"32792fd2c7","children":["707a7e2997"]},"8d15a39e2d":{"type":"columns","name":"列","key":"8d15a39e2d","children":["a6d1c0b77c"]}},"cell_map":{"707a7e2997":{"width":"100%","key":"707a7e2997","children":[]},"a6d1c0b77c":{"width":"100%","key":"a6d1c0b77c","children":["8d5aa67a11","7c5406af20"]}},"cell_style_map":{"707a7e2997":{"style":{"background":"transparent","textAlign":"center","padding":{"more":false,"all":"10","top":"","right":"","bottom":"","left":""},"border":{"more":false,"all":"0px","top":"","right":"","bottom":"","left":""}}},"a6d1c0b77c":{"style":{"background":"transparent","textAlign":"center","padding":{"more":false,"all":"10","top":"","right":"","bottom":"","left":""},"border":{"more":false,"all":"0px","top":"","right":"","bottom":"","left":""}}}},"column_row_style_map":{"32792fd2c7":{"style":{"backgroundColor":"transparent","padding":{"more":false,"all":"0px","top":"","right":"","bottom":"","left":""}}},"8d15a39e2d":{"style":{"backgroundColor":"transparent","padding":{"more":false,"all":"0px","top":"","right":"","bottom":"","left":""}}}},"comp_style_map":{"7c5406af20":{"style":{"border":{"more":false,"all":"","top":"","right":"","bottom":"","left":""},"padding":{"more":true,"all":"","top":"10px","left":"20px","right":"20px","bottom":"10px"},"borderRadius":{"more":false,"all":"4px","top":"","left":"","right":"","bottom":""},"width":"auto","lineHeight":"120%","color":"#A2A2A2FF","display":"inline-block","backgroundColor":"#FFFFFFFF","FontWeight":"normal","fontSize":"13px","textAlign":"center","LetterSpacing":"0px","fontWeight":"normal"},"general":{"textAlign":"center","padding":{"more":false,"all":"10px","top":"4px","left":"10px","right":"10px","bottom":"10px"}},"info":{"href":"__UNSUBSCRIBE_URL__","target":"_blank"},"content":"Unsubscribe"},"8d5aa67a11":{"style":{"borderTop":"1px solid #bbbbbb","width":"100%","display":"inline-block","lineHeight":"1px","height":"0px","verticalAlign":"middle"},"general":{"textAlign":"center","padding":{"more":false,"all":"10px","top":"","left":"","right":"","bottom":""}},"info":{}}},"compOptions":{},"comp_map":{"7c5406af20":{"key":"7c5406af20","type":"button"},"8d5aa67a11":{"key":"8d5aa67a11","type":"divider"}}}"""
        public.writeFile(content_path, content)
        public.writeFile(render_path, render)


        # public.writeFile(content_path, '')
        # public.writeFile(render_path, '')
        insert_data = {
            "name": name,
            "content": content_path,
            "created": timestimp,
            "modified": timestimp,
            "render": render_path,
            "is_temp": 1,
            "type": temp_type
        }
        try:
            with public.S("temp_email", '/www/vmail/postfixadmin.db') as obj:
                tmp_id = obj.insert(insert_data)
        except:
            public.print_log(public.get_error_info())

        insert_data['id'] = tmp_id
        res = {
            "result": public.lang("Added successfully"),
            "data": insert_data,
        }

        # 清获取渲染数据接口的缓存
        public.cache_remove('mail_sys:get_email_temp_render')
        public.set_module_logs('mailModel', 'add_email_temp', 1)
        return public.returnMsg(True, res)


    def del_email_temp(self, args):
        '''
        删除邮件模版
        :param args:
        :return:
        '''
        tmp_id = args.id
        with public.S("temp_email", '/www/vmail/postfixadmin.db') as obj:
            obj.where_in('id', tmp_id.split(',')).delete()
        # 清获取渲染数据接口的缓存
        public.cache_remove('mail_sys:get_email_temp_render')
        public.set_module_logs('mailModel', 'del_email_temp', 1)
        return public.returnMsg(True,public.lang("删除成功"))

    def edit_email_temp(self, args):
        '''
        编辑邮件模版
        :param args:
        :return:
        '''

        if not hasattr(args, 'id'):
            return public.returnMsg(False, public.lang('参数错误: id'))
        tmp_id = args.id
        timestimp = int(time.time())

        if not hasattr(args, 'content'):
            args.content = None

        if not hasattr(args, 'upload_path'):
            args.upload_path = None
        if not hasattr(args, 'render'):
            args.render = ''
        if not hasattr(args, 'temp_name'):
            args.temp_name = None

        # 改名  改数据库   改内容  改文件
        name = args.temp_name
        content = args.content
        render = args.render
        upload_path = args.upload_path
        if upload_path:
            if os.path.exists(args.upload_path):
                content = public.readFile(args.upload_path)
        # 拖拽1 上传0
        temp_type = 1 if render else 0
        with public.S("temp_email", '/www/vmail/postfixadmin.db') as obj:
            tmail = obj.where('id', tmp_id).find()

            if name:
                update_data = {
                    "name": name,
                    "modified": timestimp,
                    "type": temp_type,
                }
            else:
                update_data = {
                    "modified": timestimp,
                    "type": temp_type,
                }
            obj.where('id', tmp_id).update(update_data)

        if content:
            # 更文件
            content_path = tmail['content']
            render_path = tmail['render']
            public.writeFile(content_path, content)
            public.writeFile(render_path, render)

        # 清获取渲染数据接口的缓存
        public.cache_remove('mail_sys:get_email_temp_render')
        public.set_module_logs('mailModel', 'edit_email_temp', 1)
        return public.returnMsg(True, public.lang("Edit success"))


    def resolve_dns(self, domain, dns_servers=None, record_type='A'):
        if re.match(self.REGEX_IP, domain):
            # public.print_log(f"退出 {domain_or_ip}")
            return domain
        else:
            resolver = dns.resolver.Resolver()
            if dns_servers:
                resolver.nameservers = dns_servers
            for i in range(self.CONF_DNS_TRIES):
                try:

                    response = resolver.resolve(domain, record_type, lifetime=self.CONF_DNS_DURATION)
                    result = str(response.rrset[0])
                    return result
                except (dns.resolver.NXDOMAIN, dns.resolver.YXDOMAIN, dns.resolver.Timeout, dns.resolver.NoAnswer) as e:
                    # public.print_log(f"Attempt {i+1}/{self.CONF_DNS_TRIES}: Error resolving {domain}: {e}")
                    if i < self.CONF_DNS_TRIES - 1:
                        time.sleep(1)  # 等待1秒后重试
                        continue
                    else:
                        # public.print_log(f"Error resolving {domain}: {e}")
                        return None
                except Exception as e:
                    public.print_log(public.get_error_info())
                    public.print_log(f"Unexpected error resolving {domain}: {e}")
                    return None


    def check_blacklists(self, args):
        """
        检查给定的域名或IP地址是否被列入黑名单
        """

        # endtime = public.get_pd()[1]
        # curtime = int(time.time())

        # 专业版过期
        # if endtime != 0 and endtime < curtime:
        #     return public.returnMsg(False, public.lang('This feature is exclusive to the Pro version'))

        # domain = args.domain
        if not hasattr(args, 'a_record'):
            return public.returnMsg(False, public.lang('参数错误: a_record'))

        # 改a记录检查
        domain = args.a_record

        dns_servers = ['8.8.8.8', '1.1.1.1']

        blacklist_file = None

        # 后续改文件管理黑名单列表
        if blacklist_file:
            with open(blacklist_file, 'r') as f:
                self.CONF_BLACKLISTS.extend(f.read().splitlines())

        ip = self.resolve_dns(domain, dns_servers)
        if not ip:
            # public.print_log(f"Error: No DNS record found for {domain}  ip:{ip}")

            return public.returnMsg(False, public.lang('Error: 没有找到对应的DNS记录 {} ', domain))
        if ip == '127.0.0.1':
            ip = public.GetLocalIp()

        self.run_thread(self._check_blacklists, (ip, domain,dns_servers))
        public.set_module_logs('mailModel', 'check_blacklists', 1)

        return public.returnMsg(True, public.lang('检查需要两分钟，请耐心等待'))


    def _check_blacklists(self, ip, domain, dns_servers):
        '''
         域名黑名单检测 + 告警
        :param args: ip str  域名
        :param args: blcheck_info dict  黑名单检测统计
        :return:
        '''

        # 反转IP地址
        reversed_ip = '.'.join(reversed(ip.split('.')))

        blacklisted = 0  # 黑名单
        invalid = 0  # 无效
        passed = 0  # 通过验证

        black_list = []

        # 记录域名检查日志  检测日志  检测时间(文件最近更新时间) 检测结果 记录文件{域名:{检测结果},域名:{检测结果}}
        domain_check_log = f'/www/server/panel/plugin/mail_sys/data/{domain}_blcheck.txt'
        # 清空历史记录
        public.writeFile(domain_check_log, '')

        # is_over = False
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        check_log = f'{date}:  Start checking... '
        public.AppendFile(domain_check_log, check_log + '\n')

        for blacklist in self.CONF_BLACKLISTS:
            times = int(time.time())
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            test_domain = f"{reversed_ip}.{blacklist}"
            #public.print_log(f' ip {ip} ,  检测{test_domain}')
            result = self.resolve_dns(test_domain, dns_servers)
            # print(f"检查结果 {result}")
            if not result:
                check_log = f'{date}: {blacklist} -----------------------------  √'
                public.AppendFile(domain_check_log, check_log + '\n')

                passed += 1
            elif result.startswith('127.'):
                if result == '127.255.255.254':
                    passed += 1
                    check_log = f'{date}: {blacklist} -----------------------------  √ ({result})'
                    public.AppendFile(domain_check_log, check_log + '\n')
                else:
                    # public.print_log(f"检查到黑名单: {test_domain}  结果:{result}")
                    check_log = f'{date}: {blacklist} ----------------------------- x   blacklisted ({result})'
                    public.AppendFile(domain_check_log, check_log + '\n')
                    blacklisted += 1
                    black_list.append({"blacklist": blacklist, "time": times})
            else:
                # print(f"无效黑 ({result})")
                check_log = f'{date}: {blacklist} ----------------------------- Invalid'
                public.AppendFile(domain_check_log, check_log + '\n')
                invalid += 1

        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        check_log = f'---------------------------------------------------------------------------------------  \n' \
                    f'Results for {domain}: \n' \
                    f'Ip: {ip} \n' \
                    f'Tested: {len(self.CONF_BLACKLISTS)} \n' \
                    f'Passed: {passed} \n' \
                    f'Invalid: {invalid} \n' \
                    f'Blacklisted: {blacklisted} \n' \
                    f'---------------------------------------------------------------------------------------   \n' \
                    f'{date}:  Check finished'

        public.AppendFile(domain_check_log, check_log)


        data = {
            "time": int(time.time()),
            "results": domain,
            "ip": ip,
            "tested": len(self.CONF_BLACKLISTS),
            "passed": passed,
            "invalid": invalid,
            "blacklisted": blacklisted,
            "black_list": black_list
        }

        # 更新检查内容
        self.add_blacklist(domain, data)

        # 有黑名单,检查告警并推送
        if blacklisted > 0:
            args = public.dict_obj()
            args.keyword = 'mail_domain_black'
            send_task = self.get_alarm_send(args)
            if send_task and send_task.get('status', False):
                black_lists = [i['blacklist'] for i in black_list]

                body = [f">Send content: Your IP [{ip}] is on the email blacklist.", f">Results for {domain}.",
                        f">Blacklisted: {black_lists}."]

                # 推送告警信息
                args.body = body
                args.domain = domain
                self.send_mail_data(args)

        return data


    def add_blacklist(self, domain, blcheck_info):
        '''
         记录域名黑名单检测内容
        :param args: domain str  域名
        :param args: blcheck_info dict  黑名单检测统计
        :return:
        '''

        path = self.blcheck_count
        data = {}
        if os.path.exists(path):
            data = public.readFile(path)
            try:
                data = json.loads(data)
            except:
                pass
        data[domain] = blcheck_info
        public.writeFile(path, public.GetJson(data))

        return True

    # todo 定时任务调用
    def check_domain_blacklist_corn(self):
        '''
        执行检查域名黑明定的定时任务
        :param
        :return:
        '''
        # 循环域名  每个域名检查完   域名数量小于8 等待3小时  大于8  24/域名数量 *3600
        # 每个循环里  判断黑名单存在 检测是否要告警

        # 关闭告警 跳过
        blacklist_alarm_switch = '/www/server/panel/plugin/mail_sys/data/blacklist_alarm_switch'
        if os.path.exists(blacklist_alarm_switch):
            return

        endtime = public.get_pd()[1]
        curtime = int(time.time())

        # 专业版过期
        if endtime != 0 and endtime < curtime:
            print("|-This feature is exclusive to the Pro version")
            return
        domain_list = self.M('domain').order('created desc').field('a_record,domain').select()
        if not domain_list:
            print("|-The domain is empty, skip")
            return

        # # 后续改文件管理黑名单列表
        # blacklist_file = None
        # if blacklist_file:
        #     with open(blacklist_file, 'r') as f:
        #         self.CONF_BLACKLISTS.extend(f.read().splitlines())

        interval_time = 3*3600
        if len(domain_list) > 8:
            interval_time = int((24 / len(domain_list)) * 3600)

        for i in domain_list:
            # 改a记录检查
            domain = i['a_record']
            dns_servers = None

            ip = self.resolve_dns(domain, dns_servers)
            if not ip:
                # public.print_log(f"Error: No DNS record found for {domain}  ip:{ip}")
                print(f"|-Error: No DNS record found for {domain}")
                continue

            data = self._check_blacklists(ip, domain, dns_servers)
            # 等待间隔 todo
            time.sleep(interval_time)

        return

    def send_mail_data(self, args):

        body = args.body

        keyword = args.keyword
        push_data = {}
        if keyword == 'mail_domain_black':
           domain = args.domain
           push_data = {
               "domain": domain,
               "msg_list": body
           }
        if keyword == 'mail_server_status':
            push_data = {
                "msg_list": body
            }

        try:
            import sys
            if "/www/server/panel" not in sys.path:
                sys.path.insert(0, "/www/server/panel")

            from mod.base.push_mod import push_by_task_keyword
            res = push_by_task_keyword(keyword, keyword, push_data=push_data)
            if res:
                return
        except:
            pass



    # 查看邮局服务告警
    def get_alarm_send(self, args):
        # 服务掉线 mail_server_status   黑名单 mail_domain_black
        keyword = args.keyword
        task_file_path = '/www/server/panel/data/mod_push_data/task.json'
        sender_file_path = '/www/server/panel/data/mod_push_data/sender.json'
        task_data = {}

        try:
            with open(task_file_path, 'r') as file:
                tasks = json.load(file)

            # 读取发送者配置文件
            with open(sender_file_path, 'r') as file:
                senders = json.load(file)
            sender_dict = {sender['id']: sender for sender in senders}

            # 查找特定的告警任务
            for task in tasks:
                if task.get('keyword') == keyword:
                    task_data = task
                    sender_types = set()  # 使用集合来保证类型的唯一性

                    # 对应sender的ID，获取sender_type，并保证唯一性
                    for sender_id in task.get('sender', []):
                        if sender_id in sender_dict:
                            sender_types.add(sender_dict[sender_id]['sender_type'])

                    # 将唯一的通道类型列表转回列表格式，添加到告警数据中
                    task_data['channels'] = list(sender_types)
                    break

        except Exception as e:
            return False
        if task_data:
            return task_data
        else:
            return False


    # 导出模版
    def export_email_template(self, args):
        if not hasattr(args, 'ids'):
            return public.returnMsg(False, public.lang('参数错误: ids'))
        ids_list = args.ids.split(',')
        ids_list = [int(id_str) for id_str in ids_list]
        with public.S("temp_email", '/www/vmail/postfixadmin.db') as obj:
            temps = obj.where_in('id', ids_list).select()

        # 获取当前模版文件信息
        # 生成文件  并压缩
        current_time = datetime.now()
        timestamp = current_time.strftime("%Y%m%d%H%M%S")
        template_p = f"t_{timestamp}"
        # 生成模板压缩包 临时下载目录
        download_dir = f"/tmp/export_{template_p}"
        os.makedirs(download_dir)

        for i in temps:
            rdm = public.GetRandomString(5)
            download_tmpdir = f'{download_dir}/{template_p}_{rdm}'

            info = {'type': i['type'], 'name': i['name']}
            content_path = i['content']
            render_path = i['render']

            content_new = os.path.join(download_tmpdir, 'content')
            render_new = os.path.join(download_tmpdir, 'render')
            template_info = os.path.join(download_tmpdir, 'template_info.json')
            if not os.path.exists(os.path.dirname(content_new)):
                os.makedirs(os.path.dirname(content_new))
            if not os.path.exists(os.path.dirname(render_new)):
                os.makedirs(os.path.dirname(render_new))

            if os.path.isfile(content_path):
                shutil.copy2(content_path, content_new)
            if os.path.isfile(render_path):
                shutil.copy2(render_path, render_new)

            public.writeFile(template_info, json.dumps(info))
        # 压缩包
        zip_path = f"{download_dir}.zip"
        # 创建ZIP文件
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 添加整个文件夹及其内容
            for root, dirs, files in os.walk(download_dir):
                for file in files:
                    full_file_path = os.path.join(root, file)
                    arcname = os.path.relpath(full_file_path, download_dir)
                    zipf.write(full_file_path, arcname)

        # 清理临时文件夹
        shutil.rmtree(download_dir)

        return public.returnMsg(True, zip_path)

    # 导入模版
    def import_email_template(self, args):
        upload_dir = args.path
        # upload_dir = '/tmp/export_t_20250109162548.zip'

        # 压缩包上传目录
        if not os.path.exists(upload_dir):
            return public.returnMsg(False, public.lang('The file {} does not exist',upload_dir))

        # 解压到
        upload_path = '/tmp/upload_mail_template'
        if os.path.exists(upload_path):
            shutil.rmtree(upload_path)

        public.ExecShell('unzip -o "' + upload_dir + '" -d ' + upload_path + '/')

        insert_data = []
        for p_name in os.listdir(upload_path):
            tmppath = os.path.join(upload_path, p_name)

            cur_tmpinfo = {}

            # 处理每一个模版
            for p_name in os.listdir(tmppath):
                cur_file = os.path.join(tmppath, p_name)

                if not os.path.exists(cur_file):
                    continue

                if p_name == 'content':
                    cur_tmpinfo['content_data'] = public.readFile(cur_file)
                if p_name == 'render':
                    cur_tmpinfo['render_data'] = public.readFile(cur_file)

                if p_name == 'template_info.json':
                    info = json.loads(public.readFile(cur_file))
                    cur_tmpinfo['name'] = info['name']
                    cur_tmpinfo['type'] = int(info.get('type', 0))

                path = "{}/content".format(self.in_bulk_path)

                # 时间戳+名称+随机数  生成md5
                timestimp = int(time.time())
                content_s = cur_tmpinfo['name'] + 'content' + str(timestimp) + public.GetRandomString(5)
                render_s = cur_tmpinfo['name'] + 'render' + str(timestimp) + public.GetRandomString(5)

                content_name = public.md5(content_s)
                render_name = public.md5(render_s)
                cur_tmpinfo['content_path'] = "{}/{}".format(path, content_name)
                cur_tmpinfo['render_path'] = "{}/{}".format(path, render_name)
                cur_tmpinfo['timestimp'] = timestimp

            data = {
                "name": cur_tmpinfo['name'],
                "content": cur_tmpinfo['content_path'],
                "created": cur_tmpinfo['timestimp'],
                "modified": cur_tmpinfo['timestimp'],
                "render": cur_tmpinfo['render_path'],
                "is_temp": 1,
                "type": cur_tmpinfo['type']
            }
            insert_data.append(data)

            public.writeFile(cur_tmpinfo['content_path'], cur_tmpinfo['content_data'])
            public.writeFile(cur_tmpinfo['render_path'], cur_tmpinfo['render_data'])
        try:
            with public.S("temp_email", '/www/vmail/postfixadmin.db') as obj:
                add_num = obj.insert_all(insert_data, option='IGNORE')
        except:
            public.print_log(public.get_error_info())

        return public.returnMsg(True, public.lang('Import successfully!'))

    # 通过分组查询邮箱地址列表
    def retrieve_email_address_from_groups(self, args: public.dict_obj):
        pass


    # 判断是否更新退订方式 是否缺少静态文件 /www/server/panel/BTPanel/templates/default/unsubscribe.html
    def check_new_unsubscribe(self, ):
        """ 检查退订页面是否拉取"""
        # 没初始化跳过
        if not os.path.exists('/www/vmail'):
            return
        # # 判断删掉标记 如果不存在 就删掉就任务
        # path = '/www/server/panel/data/mailsys_check_new_unsubscribe.pl'
        # if os.path.exists(path):
        #     return

        unsubscribe_path = '/www/server/panel/BTPanel/templates/default/unsubscribe.html'
        if os.path.exists(unsubscribe_path):
            return
        else:
            # 拉取文件
            public.downloadFile('https://node.aapanel.com/mail_sys/unsubscribe.html', unsubscribe_path)

        # # 记录标记
        # public.writeFile(path, "")

