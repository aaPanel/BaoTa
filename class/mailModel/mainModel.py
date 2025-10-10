#!/usr/bin/python
# coding: utf-8
# +-------------------------------------------------------------------
# | aaPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: wzjie <wzj@aapanel.com>
# | Author: zhwen <zhw@aapanel.com>
# +-------------------------------------------------------------------

# +--------------------------------------------------------------------
# |   宝塔邮局
# +--------------------------------------------------------------------

import binascii, base64, re, json, os, sys, time, shutil, socket, io, math
from genericpath import isfile
from datetime import datetime, timedelta, timezone
import requests
import psutil
import pytz
from flask import request
from mailModel.base import Base

try:
    from BTPanel import cache
except:
    import cachelib

    cache = cachelib.SimpleCache()
import traceback

if sys.version_info[0] == 3:
    from importlib import reload

if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')

sys.path.append('/www/server/panel')

sys.path.append("class/")

from mod.base import public_aap as public

import mailModel.server_init as msi

try:
    import dns.resolver
except:
    if os.path.exists('/www/server/panel/pyenv'):
        public.ExecShell('/www/server/panel/pyenv/bin/pip install dnspython')
    else:
        public.ExecShell('pip install dnspython')
    import dns.resolver

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.encoders import encode_base64
from email.utils import COMMASPACE, formatdate, formataddr, make_msgid
from email.header import Header


try:
    import jwt
except:
    public.ExecShell('btpip install pyjwt')
    import jwt


# from mail_send_bulk import SendMailBulk



class SendMail:
    '''
    发件类
    '''
    __setupPath = '/www/server/panel/plugin/mail_sys'
    _session_conf = __setupPath + '/session.json'

    def __init__(self, username, password, server, port=25, usettls=False):
        self._session = self._get_session()
        self.mailUser = username
        self.mailPassword = password
        self.smtpServer = server
        self.smtpPort = port
        self.mailServer = smtplib.SMTP(self.smtpServer, self.smtpPort)
        if usettls:
            self.mailServer.starttls()
        self.mailServer.ehlo()
        self.mailServer.login(self.mailUser, self.mailPassword)
        self.msg = MIMEMultipart()
        self.mailbox_list = [
            'gmail.com',
            'googlemail.com',
            'hotmail.com',
            'outlook.com',
            'yahoo.com',
            'protonmail.com',
            'zoho.com',
            'icloud.com',
        ]

    def __del__(self):
        self.mailServer.close()

    # 更新到初始的无内容无主题状态
    def update_init(self, name):
        self.msg = MIMEMultipart()
        sender = formataddr((name, self.mailUser))
        self.msg['From'] = sender
        self.msg['Date'] = formatdate(localtime=True)

    def nwe_msg(self, msgid):
        msg = MIMEMultipart()
        msg['Subject'] = self.msg['Subject']
        msg['From'] = self.msg['From']
        msg['Date'] = self.msg['Date']
        msg['Message-ID'] = msgid

        # unsubscribe_mailto = 'mailto:lotk1@moyumao.top'
        # unsubscribe_url = 'https://bbb.moyumao.top/mailUnsubscribe?action=Unsubscribe&jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6Ijk3NzkzNTUwMUBxcS5jb20iLCJleHAiOjE3MzI2MTcyNTB9.aXDSxtem1eAvcjYIlgkVr0I0CGNmPlcq4yAx5eEYHTI'
        # # self.msg.add_header('List-Unsubscribe', f'<{unsubscribe_url}>, <{unsubscribe_mailto}>')
        # msg['List-Unsubscribe'] = f'<{unsubscribe_mailto}>, <{unsubscribe_url}>'

        msg.set_payload(self.msg.get_payload())

        return msg

    def _get_session(self):
        session = public.readFile(self._session_conf)
        if session:
            session = json.loads(session)
        else:
            session = {}
        return session

    def setMailInfo(self, name, subject, text, attachmentFilePaths):

        self.msg['Subject'] = subject
        sender = formataddr((name, self.mailUser))
        self.msg['From'] = sender
        self.msg['Date'] = formatdate(localtime=True)

        self.msg.attach(MIMEText(text, 'html', _charset="utf-8"))
        for attachmentFilePath in attachmentFilePaths:
            self.msg.attach(self.addAttachmentFromFile(attachmentFilePath))

    def setMailInfo_one(self, name):
        sender = formataddr((name, self.mailUser))
        self.msg['From'] = sender
        self.msg['Date'] = formatdate(localtime=True)

    # 用于有退订内容时循环发送 每次重新传如邮件内容
    def setMailInfo_two(self, subject, text, attachmentFilePaths):
        # self.msg = MIMEMultipart()
        self.msg['Subject'] = subject
        self.msg.attach(MIMEText(text, 'html', _charset="utf-8"))
        for attachmentFilePath in attachmentFilePaths:
            self.msg.attach(self.addAttachmentFromFile(attachmentFilePath))

    # 添加附件从网络数据流
    def addAttachment(self, filename, filedata):
        part = MIMEBase('application', "octet-stream")
        part.set_payload(filedata)
        encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % str(Header(filename, 'utf8')))
        self.msg.attach(part)

    # 添加附件从本地文件路径
    def addAttachmentFromFile(self, attachmentFilePath):
        part = MIMEBase('application', "octet-stream")
        part.set_payload(open(attachmentFilePath, "rb").read())
        encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % str(Header(attachmentFilePath, 'utf8')))
        return part

    # 统计发送 收件人
    def count_receiveUsers(self, receiveUsers):

        data = {
            'gmail': 0,
            'outlook': 0,
            'yahoo.com': 0,
            'icloud.com': 0,
            'other': 0,
        }

        for i in receiveUsers:
            _, domain = i.lower().split('@')
            domain_key = domain if domain in self.mailbox_list else 'other'

            if domain_key in ['gmail.com', 'googlemail.com']:
                domain_key = 'gmail'
            if domain_key in ['hotmail.com', 'outlook.com']:
                domain_key = 'outlook'
            # 累计数量  收件人不属于指定域名 不限制发送数量
            if domain_key != 'other':
                data[domain_key] += 1

        # 获取已有的
        count_sent = '/www/server/panel/plugin/mail_sys/count_sent_domain.json'
        if not os.path.exists(count_sent):
            data_d = {
                'gmail': 0,
                'outlook': 0,
                'yahoo.com': 0,
                'icloud.com': 0,
                'other': 0,
            }
        else:
            try:
                data_d = public.readFile(count_sent)
                data_d = json.loads(data_d)
                # 如果有 data_d 将data_d['outher'] 改为data_d['other']
                if 'outher' in data_d:
                    data_d['other'] = data_d.pop('outher')
            except:

                data_d = {
                    'gmail': 0,
                    'outlook': 0,
                    'yahoo.com': 0,
                    'icloud.com': 0,
                    'other': 0,
                }

        result = {}
        # 累计
        for key in data.keys():
            result[key] = data[key] + data_d[key]
        # 更新文件
        public.writeFile(count_sent, json.dumps(result))

        is_ok = True
        # 判断额度  单个发送
        for key, value in result.items():
            if key == 'other':
                continue

            if value > 5000:
                is_ok = False

        return is_ok

    # 查看单个收件人是否在限额内
    def count_receiveUsers_one(self, receiveUsers):

        data = {
            'gmail': 0,
            'outlook': 0,
            'yahoo.com': 0,
            'icloud.com': 0,
            'other': 0,
        }
        receiveUser = receiveUsers[0]
        _, domain = receiveUser.lower().split('@')
        domain_key = domain if domain in self.mailbox_list else 'other'

        if domain_key in ['gmail.com', 'googlemail.com']:
            domain_key = 'gmail'
        if domain_key in ['hotmail.com', 'outlook.com']:
            domain_key = 'outlook'

        # 累计数量  收件人不属于指定域名 不限制发送数量
        if domain_key != 'other':
            data[domain_key] += 1

        # 获取已有的
        count_sent = '/www/server/panel/plugin/mail_sys/count_sent_domain.json'
        if not os.path.exists(count_sent):
            data_d = {
                'gmail': 0,
                'outlook': 0,
                'yahoo.com': 0,
                'icloud.com': 0,
                'other': 0,
            }
        else:
            try:
                data_d = public.readFile(count_sent)
                data_d = json.loads(data_d)
                # 如果有 data_d 将data_d['outher'] 改为data_d['other']
                if 'outher' in data_d:
                    data_d['other'] = data_d.pop('outher')
            except:

                data_d = {
                    'gmail': 0,
                    'outlook': 0,
                    'yahoo.com': 0,
                    'icloud.com': 0,
                    'other': 0,
                }

        result = {}
        # 累计
        for key in data.keys():
            result[key] = data[key] + data_d[key]
        # # 更新文件
        # public.writeFile(count_sent, json.dumps(result))

        is_ok = True
        # 判断额度  单个发送
        for key, value in result.items():
            if key == 'other':
                continue
            # 超过限额发送失败 不用更新数量
            if value > 5000:
                is_ok = False
                return is_ok
        # 未超过限额 更新文件
        public.writeFile(count_sent, json.dumps(result))
        return is_ok

    def sendMail(self, receiveUsers, domain, is_record, msgid=None):

        # 统计发送 收件人, 判断是否有发送额度  未设置ptr不阻拦发送
        try:
            key = '{0}:{1}'.format(domain, 'PTR')
            isptr = self._session[key]['status']
            if not isptr:
                # 查看额度
                if not self.count_receiveUsers_one(receiveUsers):
                    return public.returnMsg(False, '超过发送限制，请联系IP提供商进行PTR记录')
        except:
            pass

        if msgid:
            msgid = msgid
        else:
            msgid = make_msgid()
        # 将列表用逗号拼接成字符串
        msg = self.nwe_msg(msgid)
        msg['To'] = COMMASPACE.join(receiveUsers)

        try:
            try:
                result = self.mailServer.sendmail(self.mailUser, receiveUsers, msg.as_string())

            except Exception as e:
                public.print_log(public.get_error_info())
                return public.returnMsg(False, '发送邮件失败,错误原因[{0}]'.format(str(e)))

            # 记录
            if is_record:
                # 保存邮件到发件箱
                local_part, domain = self.mailUser.split('@')
                dir_path = '/www/vmail/{0}/{1}/.Sent/cur'.format(domain, local_part)
                if not os.path.isdir(dir_path):
                    os.makedirs(dir_path)
                file_name = public.GetRandomString(36)
                if file_name in [item.split(':')[0] for item in os.listdir(dir_path)]:
                    file_name = public.GetRandomString(54)
                public.writeFile(os.path.join(dir_path, file_name), msg.as_string())
                self.set_owner_and_group(os.path.join(dir_path, file_name), 'vmail', 'mail')

            # 不删除收件人 收件人会在邮件里一直累加
            del self.msg['To']
            del msg['To']
            del msg['Message-ID']
            return public.returnMsg(True, "发送邮件成功")
        except Exception as e:
            public.print_log(public.get_error_info())
            return public.returnMsg(False, '发送邮件失败,错误原因[{0}]'.format(str(e)))

    def parse_queue_id(self, receiveUsers):
        # receiveUsers = [receiveUsers]
        try:
            # 获取邮件队列信息
            output, err = public.ExecShell('mailq')

            pattern = re.compile(
                r'(?P<queue_id>\S+)\*?\s+\d+\s+\w{3}\s\w{3}\s+\d+\s+\d+:\d+:\d+\s+\S+\s*[\s\S]*?\n\s+' + re.escape(
                    receiveUsers[0]))
            # 搜索匹配的队列ID
            match = pattern.search(output)

            if match:
                # 提取匹配到的队列ID并去掉星号
                queue_id = match.group('queue_id').rstrip('*')

                return queue_id
            else:

                return None

        except Exception as e:
            public.print_log(public.get_error_info())
            return None

    def set_owner_and_group(self, path, user, group):
        '''
        检测目录所有者和组 并更改
        :param path: 目录或文件   user: 用户, group: 组
        :return:
        '''
        import os
        import pwd
        import grp
        try:
            # 获取当前文件或目录的所有者和组
            stat_info = os.stat(path)
            current_uid = stat_info.st_uid
            current_gid = stat_info.st_gid

            # 检查当前所有者和组是否为 vmail:mail
            vmail_uid = pwd.getpwnam(user).pw_uid
            mail_gid = grp.getgrnam(group).gr_gid
            if current_uid == vmail_uid and current_gid == mail_gid:
                return
            # 设置文件或目录的所有者和组
            os.chown(path, vmail_uid, mail_gid)
            # print(f"Ownership of {path} changed to {user}:{group}.")
        # except FileNotFoundError:
        #     print(f"Directory or file {path} not found.")
        # except Exception as e:
        #     print(f"Error occurred: {e}")
        except:
            pass

    def _get_pubilc_ip(self):

        try:
            # url = 'http://pv.sohu.com/cityjson?ie=utf-8'
            url = 'https://ifconfig.me/ip'
            opener = requests.get(url)
            m_str = opener.text
            ip_address = re.search(r'\d+.\d+.\d+.\d+', m_str).group(0)
            c_ip = public.check_ip(ip_address)
            if not c_ip:
                a, e = public.ExecShell("curl ifconfig.me")
                return a
            return ip_address
        except:
            filename = '/www/server/panel/data/iplist.txt'
            ip_address = public.readFile(filename).strip()
            if public.check_ip(ip_address):
                return ip_address
            else:
                return None

    def _get_all_ip(self):
        # import psutil
        public_ip = self._get_pubilc_ip()
        net_info = psutil.net_if_addrs()
        addr = []
        for i in net_info.values():
            addr.append(i[0].address)
        locataddr = public.readFile('/www/server/panel/data/iplist.txt')
        if not locataddr:
            locataddr = ""
        ip_address = locataddr.strip()
        if ip_address not in addr:
            addr.append(ip_address)
        if public_ip not in addr:
            addr.append(public_ip)
        return addr

    def check_ptr_domain(self, domain):
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
                    # public.print_log("ip 转RTR记录查询 -- {}".format(ip_address))
                    # public.print_log("RTR 记录查询地址 -- {}".format(reverse_domain))
                    result = resolver.query(reverse_domain, 'PTR')
                    found_ptr_record = True

                    break
                # except dns.resolver.NoAnswer:
                except:
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

    def _ipv6_to_ptr(self, ipv6_address):

        parts = ipv6_address.split(':')
        normalized_parts = [part.zfill(4) for part in parts]
        # 去掉冒号
        normalized_address = ''.join(normalized_parts)
        # 反转字符串
        reversed_address = normalized_address[::-1]
        # 加上点号
        ptr_address_parts = list(reversed_address)
        ptr_address = '.'.join(ptr_address_parts)
        ptr_address += '.ip6.arpa'
        # public.print_log("ptr_address  ^--{}".format(ptr_address))

        return ptr_address


class main(Base):
    __setupPath = '/www/server/panel/plugin/mail_sys'
    _session_conf = __setupPath + '/session.json'
    _forward_conf = __setupPath + '/forward.json'
    _save_conf = __setupPath + '/save_day.json'
    postfix_main_cf = "/etc/postfix/main.cf"
    # 收件人黑名单
    postfix_recipient_blacklist = '/etc/postfix/blacklist'
    _check_time = 86400
    _check_time2 = 60
    # 退订用到的 域名/ip 端口
    unsubscribe_path = __setupPath + "/setinfo.json"

    def __init__(self):
        # 数据库文件与名称
        self.db_files = {
            'postfixadmin': '/www/vmail/postfixadmin.db',
            'postfixmaillog': '/www/vmail/postfixmaillog.db',
            'mail_unsubscribe': '/www/vmail/mail_unsubscribe.db',
            'abnormal_recipient': '/www/vmail/abnormal_recipient.db'
        }
        # self.sys_v = system.system().GetSystemVersion().replace(' ', '').lower()
        self.sys_v = self.get_linux_distribution().lower()
        self._session = self._get_session()
        self.in_bulk_path = '/www/server/panel/data/mail/in_bulk'
        self.blacklist_tips = '/www/server/panel/plugin/mail_sys/data/blacklist_tips'
        self.blacklist_alarm_switch = '/www/server/panel/plugin/mail_sys/data/blacklist_alarm_switch'
        if not os.path.exists(self.in_bulk_path):
            os.makedirs(self.in_bulk_path)

        if not os.path.exists("{}/content".format(self.in_bulk_path)):
            os.mkdir("{}/content".format(self.in_bulk_path))

        # self.back_log_path = '/www/server/panel/data/mail/back_log'
        # if not os.path.exists(self.back_log_path):
        #     os.mkdir(self.back_log_path)

        # 检查域名表字段是否完整  日志表创建
        self.check_domain_column()

        # 检查pflogsumm安装
        self.is_pflogsumm = self.is_pflogsumm_installed()
        # 更新roundcube ssl状态
        self._roundcube_ssl_status()
        # 处理冗余的cron任务
        self.remove_old_cron()

        # self.task_cut_maillog()

        # # 初始化增加黑名单文件
        # if not os.path.exists(self.postfix_recipient_blacklist):
        #     public.writeFile(self.postfix_recipient_blacklist, '')
        #     # 生成db文件
        #     shell_str = 'postmap /etc/postfix/blacklist'
        #     public.ExecShell(shell_str)

        # 删除配置项(黑名单为空时)
        # self.check_black()

        self.maillog_path = '/var/log/maillog'
        if "ubuntu" in public.get_linux_distribution().lower():
            self.maillog_path = '/var/log/mail.log'

        # 给群发任务错误详情表增加唯一索引和时间字段
        self.update_task_count_table()
        # ---------------优化退订逻辑---------------
        # 黑名单列表同步到退订数据库  新安装的跳过
        self._sync_blacklist_to_unsubscribe_db()

    # 旧task_count表 迁移数据 增加索引约束
    def update_task_count_table(self):
        path = '/www/server/panel/data/update_mail_task_count_table.pl'
        if os.path.exists(path):
            return

        if not os.path.exists('/www/vmail/postfixadmin.db'):
            public.writeFile(path, '')
            return

        # 旧数据数量
        with self.M("task_count") as obj:
            total = obj.count()

        if not total:  # 无数据跳过
            public.writeFile(path, '')
            return

        try:

            # 1. Create a new table with the unique constraint
            create_table_sql = '''
            CREATE TABLE IF NOT EXISTS `task_count_new` (
              `id` INTEGER PRIMARY KEY AUTOINCREMENT,
              `task_id` INTEGER NOT NULL,
              `recipient` varchar(320) NOT NULL,
              `delay` varchar(320) NOT NULL,
              `delays` varchar(320) NOT NULL,
              `dsn` varchar(320) NOT NULL,
              `relay` text NOT NULL,
              `domain` varchar(320) NOT NULL,
              `status` varchar(255) NOT NULL,
              `err_info` text NOT NULL,
              `created` INTEGER NOT NULL DEFAULT 0,
              UNIQUE (`task_id`, `recipient`)  -- 联合唯一约束
            );
            '''

            rename_table_sql1 = '''
            ALTER TABLE `task_count` RENAME TO `task_count_bak`;
            '''
            # 4. Rename the new table to the old table's name
            rename_table_sql2 = '''
            ALTER TABLE `task_count_new` RENAME TO `task_count`;
            '''

            # 创建新表
            with self.M("") as obj:
                obj.execute(create_table_sql)

            # 查旧数据
            with self.M("task_count") as obj:
                alldata = obj.field('task_id,recipient,delay,delays,dsn,relay,domain,status,err_info').select()

            # 复制到新表
            with public.S("task_count_new", "/www/vmail/postfixadmin.db") as obj:
                aa = obj.insert_all(alldata, option='IGNORE')
                # public.print_log("更新数据表 task_count --{}".format(aa))
            # 改名
            with self.M("") as obj:
                # task_count 改名 task_count_bak
                obj.execute(rename_table_sql1)
                # task_count_new 改名 task_count
                obj.execute(rename_table_sql2)

            # error: You can only execute one statement at a time
            public.writeFile(path, '')
        except:
            public.print_log(public.get_error_info())

    def check_black(self):
        try:
            with open(self.postfix_recipient_blacklist, 'r') as file:
                emails = file.read().splitlines()
        except Exception as e:
            emails = []

        if not emails:
            # 黑名单为空 关闭
            st = self.recipient_blacklist_open(False)
            if st:
                public.ExecShell('systemctl reload postfix')

    def login_roundcube(self, args):
        '''
        一键登录 roundcube webmail
        :param args: rc_user账号  rc_pass密码
        :return: url
        '''
        if not hasattr(args, 'rc_user') or args.get('rc_user/s', "") == "":
            return self.self.return_msg(public.returnMsg(False, '参数 rc_user 错误'))
        if not hasattr(args, 'rc_pass') or args.get('rc_pass/s', "") == "":
            return self.return_msg(public.returnMsg(False, '参数 rc_pass 错误'))

        rc_user = args.rc_user
        rc_pass = args.rc_pass

        # 检查账户是否存在
        with self.M("mailbox") as obj:
            un = obj.where('username=?', rc_user).count()
        if un <= 0:
            return self.return_msg(public.returnMsg(False, '用户不存在'))

        # data = self.M('mailbox').where('username=?', mail_from).field('password_encode,full_name').find()
        # password = self._decode(data['password_encode'])
        # 获取部署信息
        info = self.get_roundcube_status(None)['data']
        if not info['status']:
            return self.self.return_msg(public.returnMsg(False, '请先安装roundcube'))

        site_name = info['site_name']
        token = public.GetRandomString(16)
        # 生成文件
        login_name = public.GetRandomString(5) + '.php'
        roundcube_path = '/www/wwwroot/' + site_name + '/'
        file = roundcube_path + login_name
        # 读取文件 并替换指定字符
        tmp_file = "/www/server/panel/class/mailModel/roundcube_autologin.php"
        if not os.path.exists(tmp_file):
            return self.return_msg(public.returnMsg(False, '缺少必要文件'))
        data_info = public.readFile(tmp_file)
        # 替换关键词
        data_info = data_info.replace('__WEBMAIL_ROUNDCUBE_RANDOM_TOKEN__', token)
        data_info = data_info.replace('__WEBMAIL_ROUNDCUBE_USERNAME__', rc_user)
        data_info = data_info.replace('__WEBMAIL_ROUNDCUBE_PASSWORD__', rc_pass)
        data_info = data_info.replace('__WEBMAIL_ROUNDCUBE_LOGINPHP_PATH__', file)
        # 重新写入
        public.writeFile(file, data_info)
        url = "{}/{}?_aap_token={}".format(site_name, login_name, token)
        return self.return_msg(url)

        # from BTPanel import redirect
        # return redirect(url)

    # 获取全部域名
    def get_domain_name(self, args):
        with self.M("domain") as obj:
            data_list = obj.order('created desc').field("domain").select()

        # data_list = self.M('domain').order('created desc').field("domain").select()
        data_list = [i['domain'] for i in data_list]
        return self.return_msg(data_list)

    def get_mailbox(self, args):
        if "domain" in args and args.domain:
            data = self.M('mailbox').where('domain=?', args.domain).field('username').select()
        else:
            data = self.M('mailbox').field('username').select()
        return self.return_msg(data)

    def get_domainip(self, args):
        '''
        查询域名和ip 用于安装 webmail
        :param args:
        :return:
        '''
        with self.M("domain") as obj:
            data_list = obj.field('domain,a_record').select()
        # data_list = self.M('domain').field('domain,a_record').select()
        public.print_log(data_list)
        all_list = []
        # 获取域名指向的ip
        for i in data_list:
            ip = self._session['{}:A'.format(i['a_record'])]['value']
            all_list.append(ip)
            all_list.append(i['domain'])
        domainip = list(set(all_list))
        return self.return_msg(domainip)

    #
    def _pflogsumm_data_treating(self, output, timezone=None):

        '''
         分析命令执行后的数据
        :param args: output  命令返回内容
        :param args: timezone 时区 默认为系统时区  为'utc'时 使用0时区 提交数据需要
        :return:  data  list
        '''

        import public.PluginLoader as plugin_loader
        bulk = plugin_loader.get_module('{}/plugin/mail_sys/mail_send_bulk.py'.format(public.get_panel_path()))
        SendMailBulk = bulk.SendMailBulk
        try:
            return SendMailBulk()._pflogsumm_data_treating(output, timezone)
        except Exception as ex:
            public.print_log(public.get_error_info())
            return []

    # 判断安装 并安装
    def is_pflogsumm_installed(self):
        if os.path.exists('/usr/sbin/pflogsumm'):
            return True
        else:
            return False

    # 获取pflogsumm统计
    # pflogsumm /var/log/mail.log > mail_report.txt
    # pflogsumm -d yesterday /var/log/mail.log > mail_report.txt
    # pflogsumm -d today /var/log/mail.log > mail_report.txt
    def get_today_count(self, args):  # 增加历史记录  昨日 每天统计昨天的数据到数据库
        if not self.is_pflogsumm:
            errinfo = ""
            if not os.path.exists('/usr/sbin/pflogsumm'):
                if self.sys_v == 'centos7':
                    errinfo = 'yum install postfix-pflogsumm -y'
                elif self.sys_v == 'centos8':
                    errinfo = 'yum install postfix-pflogsumm -y'
                elif self.sys_v == 'ubuntu':
                    errinfo = 'apt install pflogsumm -y'

            return self.return_msg(public.returnMsg(False, '请先运行[{}]安装pflogsumm'.format(errinfo)))

        else:
            self.is_pflogsumm = True

        # 取缓存
        cache_key = 'mail_sys:get_today_count'
        cache = public.cache_get(cache_key)
        if cache:
            return self.return_msg(cache)

        output, err = public.ExecShell(
            'pflogsumm -d today --verbose-msg-detail --zero-fill --iso-date-time --rej-add-from {}'.format(self.maillog_path))
        data = self._pflogsumm_data_treating(output)

        public.cache_set(cache_key, data, 30)
        # 更新昨日数据到数据库
        public.run_thread(self.get_yesterday_count)

        # 检查定时任务创建
        self.task_cut_maillog()
        return self.return_msg(data)

    def get_monthly_quota_statistics(self, args):
        # 获取本月发件数与补充包信息
        data = {
            "sent": 0,  # 当月发送
            "free_quota": 0,  # 当月额度
            "pack_use": 0,  # 补充包已使用
            "pack_total": 0,  # 补充包总额度
            "packages": [],  # 补充包
            "available": 0,  # 补充包可用
        }
        try:
            import public.PluginLoader as plugin_loader
            bulk = plugin_loader.get_module('{}/plugin/mail_sys/mail_send_bulk.py'.format(public.get_panel_path()))
            SendMailBulk = bulk.SendMailBulk

            m_sent = SendMailBulk()._get_month_senduse()
            pack = SendMailBulk()._get_user_pack_quota()
            free_quota = SendMailBulk()._get_user_free_quota()

            data = {
                "sent": m_sent,  # 当月发送
                "free_quota": free_quota,  # 当月额度
                "pack_use": pack['used'],  # 补充包已使用
                "pack_total": pack['total'],  # 补充包总额度
                "packages": pack['packages'],
                "available": pack['available'],
            }
        except:
            public.print_log(public.get_error_info())

        return self.return_msg(data)

    # 获取昨天的邮件统计 计入数据库并提交
    def get_yesterday_count(self):

        import public.PluginLoader as plugin_loader
        bulk = plugin_loader.get_module('{}/plugin/mail_sys/mail_send_bulk.py'.format(public.get_panel_path()))
        SendMailBulk = bulk.SendMailBulk
        try:
            return SendMailBulk().get_yesterday_count()
        except Exception as ex:
            public.print_log(public.get_error_info())
            return {}

    # 获取本月发件数
    def get_month_senduse(self):
        # 接口缓存15s
        dnum = self.get_data_month_count(None)
        pnum = self.get_pflogsumm_month_count(None)
        # todo 获取提交数据 每天获取一次 缓存
        cnum = 0
        senduse = dnum if dnum >= pnum else pnum
        # 统计到本月发件小于线上  有问题
        if senduse < cnum:

            return cnum
        else:
            return senduse

    # 数据库 获取本月发件数
    def get_data_month_count(self, args):
        '''
         数据库 获取本月发件数
        :param args: int
        :return:
        '''

        import public.PluginLoader as plugin_loader
        bulk = plugin_loader.get_module('{}/plugin/mail_sys/mail_send_bulk.py'.format(public.get_panel_path()))
        SendMailBulk = bulk.SendMailBulk
        try:

            return SendMailBulk().get_data_month_count(args)
        except Exception as ex:
            public.print_log(public.get_error_info())
            return {}

    # 命令 获取本月发件数
    def get_pflogsumm_month_count(self, args):
        '''
         命令 获取本月发件数
        :param args: int
        :return:
        '''

        import public.PluginLoader as plugin_loader
        bulk = plugin_loader.get_module('{}/plugin/mail_sys/mail_send_bulk.py'.format(public.get_panel_path()))
        SendMailBulk = bulk.SendMailBulk
        try:

            return SendMailBulk().get_pflogsumm_month_count(args)
        except Exception as ex:
            public.print_log(public.get_error_info())
            return {}

    # 获取历史数据 -- 首页发件统计  传参  时间戳范围    一个详细列表 一个统计 暂未对接
    def get_data_month_list(self, args):
        # 		"received": 0,  //接收
        # 		"delivered": 0,  //发送
        # 		"forwarded": 0,  // 转发
        # 		"deferred": 5,   //延迟
        # 		"bounced": 3,   // 退回
        # 		"rejected": 0,  // 拒绝

        # 取缓存
        # cache_key = 'mail_sys:get_data_month_list'
        # cache = public.cache_get(cache_key)
        #
        # if cache:
        #     return cache

        # # 获取当前时间戳
        # timestamp_now = int(time.time())
        # strat = timestamp_now-86400*7
        # end = timestamp_now

        strat = int(args.strat)
        end = int(args.end)

        try:
            # 发送+退回+拒绝
            total_fields = "sum(received) as received, sum(delivered) as delivered, sum(deferred) as deferred, sum(bounced) as bounced, sum(rejected) as rejected, sum(delivered+bounced+rejected) as sentall"
            with self.M("log_analysis") as obj:
                query = obj.field(total_fields).where('time between ? and ?', (strat, end)).find()
                query2 = obj.where('time between ? and ?', (strat, end)).order('time desc').select()

            # sentall = query['sentall']

            # public.cache_set(cache_key, sentall, 15)
            data = {
                "hourly_stats": query2,
                "stats_dict": query,
            }
            return data
        except:
            public.print_log(public.get_error_info())

    def get_postconf(self):
        if os.path.exists("/usr/sbin/postconf"):
            return "/usr/sbin/postconf"
        elif os.path.exists("/sbin/postconf"):
            return "/sbin/postconf"
        else:
            return "postconf"

    def get_linux_distribution(self):
        distribution = 'ubuntu'
        redhat_file = '/etc/redhat-release'
        if os.path.exists(redhat_file):
            try:
                tmp = public.readFile(redhat_file).split()[3][0]
                distribution = 'centos{}'.format(tmp)
            except:
                distribution = 'centos7'
        elif not os.path.exists('/usr/bin/apt-get'):
            distribution = 'centos7'
        return distribution

    def check_mail_sys(self, args):
        if os.path.exists('/etc/postfix/sqlite_virtual_domains_maps.cf'):
            public.ExecShell('{} -e "message_size_limit = 102400000"'.format(self.get_postconf()))
            # 修改postfix mydestination配置项
            result = public.readFile(self.postfix_main_cf)
            if not result:
                return self.return_msg(public.returnMsg(False, "找不到postfix配置文件"))
            result = re.search(r"\n*mydestination\s*=(.+)", result)
            if not result:
                return self.return_msg(public.returnMsg(False,
                                        "postfix配置文件中找不到mydestination配置项"))
            result = result.group(1)
            if 'localhost' in result or '$myhostname' in result or '$mydomain' in result:
                public.ExecShell('{} -e "mydestination =" && systemctl restart postfix'.format(self.get_postconf()))
            # 修改dovecot配置
            dovecot_conf = public.readFile("/etc/dovecot/dovecot.conf")
            if not dovecot_conf or not re.search(r"\n*protocol\s*imap",
                                                 dovecot_conf):
                return self.return_msg(public.returnMsg(False, '配置dovecot失败'))
            # 修复之前版本未安装opendkim的问题
            # if not (os.path.exists("/usr/sbin/opendkim") and os.path.exists("/etc/opendkim.conf") and os.path.exists("/etc/opendkim")):
            #     if not self.setup_opendkim():
            #         return public.returnMsg(False, 'Failed to configure opendkim 1')

            return self.return_msg(public.returnMsg(True, '邮局系统已经存在，重装之前请先卸载!'))
        else:
            return self.return_msg(public.returnMsg(False, '之前没有安装过邮局系统，请放心安装!'))

    def check_mail_env(self, args):
        return self.return_msg(msi.mail_server_init().check_env())

    def change_to_rspamd(self, args):
        msi.change_to_rspamd().main()
        return self.return_msg(public.returnMsg(True, "设置成功"))

    def install_rspamd(self, args):
        a, e = public.ExecShell("bash {}/install.sh rspamd".format(
            self.__setupPath))
        return self.return_msg(public.returnMsg(True, "安装成功"))

    # 安装并配置postfix, dovecot
    def setup_mail_sys(self, args):
        '''
        安装邮局系统主函数
        :param args:
        :return:
        '''
        res = msi.mail_server_init().setup_mail_sys(args)
        # 关闭黑名单
        self.check_black()
        # 安装时添加cut_maillog任务
        self.task_cut_maillog()
        return self.return_msg(res)

    # 检测多个 SMTP 服务器的 25 端口是否可用
    def _check_smtp_port(self):
        import telnetlib

        host_list = ['mx1.qq.com', 'mx2.qq.com', 'mx3.qq.com', 'smtp.gmail.com']
        for host in host_list:
            try:
                tn = telnetlib.Telnet(host, 25, timeout=5)
                if tn: return True
            except:
                continue
        return False

    # 获取公网ip
    def _get_pubilc_ip(self):

        try:
            # url = 'http://pv.sohu.com/cityjson?ie=utf-8'
            url = 'https://ifconfig.me/ip'
            opener = requests.get(url)
            m_str = opener.text
            ip_address = re.search(r'\d+.\d+.\d+.\d+', m_str).group(0)
            c_ip = public.check_ip(ip_address)
            if not c_ip:
                a, e = public.ExecShell("curl ifconfig.me")
                return a
            return ip_address
        except:
            filename = '/www/server/panel/data/iplist.txt'
            ip_address = public.readFile(filename).strip()
            if public.check_ip(ip_address):
                return ip_address
            else:
                return None

    def _check_a(self, hostname):
        '''
        检测主机名是否有A记录
        :param hostname:
        :return:
        '''
        ipaddress = self._get_all_ip()
        if not ipaddress: return False
        key = '{0}:{1}'.format(hostname, 'A')
        now = int(time.time())
        value = ""
        error_ip = ""
        try:
            if key in self._session and self._session[key]["status"] != 0:
                v_time = now - int(self._session[key]["v_time"])
                if v_time < self._check_time:
                    value = self._session[key]["value"]
            if not value:
                # result = model.resolver.query(hostname, 'A')
                resolver = dns.resolver.Resolver()
                resolver.timeout = 5
                resolver.lifetime = 10
                try:
                    result = resolver.query(hostname, 'A')
                except:
                    result = resolver.resolve(hostname, 'A')
                for i in result.response.answer:
                    for j in i.items:
                        error_ip = j
                        if str(j).strip() in ipaddress:
                            value = str(j).strip()
            if value:
                self._session[key] = {
                    "status": 1,
                    "v_time": now,
                    "value": value
                }
                return True
            if str(type(error_ip)).find("dns.rdtypes.IN.A") != -1:
                self._session[key] = {
                    "status": 0,
                    "v_time": now,
                    "value": error_ip.to_text()
                }
            else:
                self._session[key] = {
                    "status": 0,
                    "v_time": now,
                    "value": error_ip
                }
            return False
        except:
            public.print_log(public.get_error_info())
            self._session[key] = {"status": 0, "v_time": now, "value": value}
            return False

    def repair_postfix(self, args=None):
        if self.sys_v == 'centos7':
            msi.mail_server_init().install_postfix_on_centos7()
        elif self.sys_v == 'centos8':
            msi.mail_server_init().install_postfix_on_centos8()
        elif self.sys_v == 'ubuntu':
            msi.mail_server_init().install_postfix_on_ubuntu()
        return self.return_msg(msi.mail_server_init().conf_postfix())

    def repair_dovecot(self, args=None):
        status = False
        if os.path.exists('/etc/dovecot/conf.d/10-ssl.conf'):
            if os.path.exists('/tmp/10-ssl.conf_aap_bak'):
                os.remove('/tmp/10-ssl.conf_aap_bak')
            shutil.move('/etc/dovecot/conf.d/10-ssl.conf', '/tmp/10-ssl.conf_aap_bak')
        if self.sys_v == 'centos7':
            if msi.mail_server_init().install_dovecot_on_centos7():
                status = True
        elif self.sys_v == 'centos8':
            msi.mail_server_init().install_postfix_on_centos8()
            status = True
        elif self.sys_v == 'ubuntu':
            msi.mail_server_init().install_dovecot_on_ubuntu()
            status = True
        if os.path.exists('/tmp/10-ssl.conf_aap_bak') and os.path.exists('/etc/dovecot/conf.d'):
            if os.path.exists("/etc/dovecot/conf.d/10-ssl.conf"):
                os.remove('/etc/dovecot/conf.d/10-ssl.conf')
            shutil.move('/tmp/10-ssl.conf_aap_bak',
                        '/etc/dovecot/conf.d/10-ssl.conf')
        return self.return_msg(public.returnMsg(status,
                                "修复{}！".format("成功" if status else "失败")))

    # 修复服务配置文件不全的问题
    def repair_service_conf(self, args=None):
        service_name = args.service
        if service_name.lower() not in ['postfix', 'dovecot', 'rspamd']:
            return self.return_msg(public.returnMsg(False, '服务名不正确'))
        if service_name == 'postfix':
            self.repair_postfix()
        elif service_name == 'dovecot':
            self.repair_dovecot()
        elif service_name == 'rspamd':
            msi.mail_server_init().setup_rspamd()
        return self.return_msg(public.returnMsg(True, '修复成功'))

    # 获取服务状态
    def get_service_status(self, args=None):
        data = {}
        data['change_rspamd'] = True if "smtpd_milters = inet:127.0.0.1:11332" not in public.readFile(
            "/etc/postfix/main.cf") else False
        data['postfix'] = public.process_exists('master', '/usr/libexec/postfix/master')
        data['dovecot'] = public.process_exists('dovecot', '/usr/sbin/dovecot')
        data['rspamd'] = public.process_exists('rspamd', '/usr/bin/rspamd')
        data['opendkim'] = public.process_exists('opendkim', '/usr/sbin/opendkim')
        if "ubuntu" in self.sys_v:
            data['postfix'] = public.process_exists('master', '/usr/lib/postfix/sbin/master')

        # if "amazon" in self.sys_v:  # /usr/sbin/postfix  /usr/libexec/postfix/master
        if not data['postfix']:
            data['postfix'] = public.process_exists('master', '/usr/sbin/postfix') or public.process_exists('master',
                                                                                                            '/usr/lib/postfix/sbin/master') or public.process_exists(
                'master', '/usr/libexec/postfix/master')

        data['recipient_blacklist'] = self._recipient_blacklist_status()
        # data['alarm_black_switch'] = self._get_alarm_black_switch()
        return self.return_msg(data)

    def get_mail_log(self, args):
        path = '/var/log/maillog'
        if "ubuntu" in self.sys_v:
            path = '/var/log/mail.log'
        if not os.path.exists(path): return {'log': '文件不存在'}
        text = public.GetNumLines(path, 500)
        return self.return_msg({'log': text})

    # postfixadmin.db 初始默认数据库
    def M(self, table_name):
        import db
        sql = db.Sql()
        sql._Sql__DB_FILE = '/www/vmail/postfixadmin.db'
        sql._Sql__encrypt_keys = []
        return sql.table(table_name)

    # 合并重复代码块
    def MD(self, table_name, db_key):
        if db_key not in self.db_files:
            raise ValueError(f"未知的数据库键: {db_key}")
        import db
        sql = db.Sql()
        sql._Sql__DB_FILE = self.db_files[db_key]
        sql._Sql__encrypt_keys = []
        return sql.table(table_name)

    def flush_domain_record(self, args):
        '''
        手动刷新域名记录
        domain all/specify.com
        :param args:
        :return:
        '''
        if args.domain == 'all':
            data_list = self.M('domain').order('created desc').field('domain,a_record,created,active').select()
            # cache_key_template = "{}_checkBlacklist"
            for item in data_list:
                try:
                    if os.path.exists("/usr/bin/rspamd"):
                        self.set_rspamd_dkim_key(item['domain'])
                    if os.path.exists("/usr/sbin/opendkim"):
                        self._gen_dkim_key(item['domain'])

                    # 清空当前域名的黑名单检测记录
                    # cache_key = cache_key_template.format(item['domain'])
                    # cache.delete(cache_key)
                except:
                    return self.return_msg(public.returnMsg(False, '请检查Rspamd服务器是否已经启动！'))
                self._gevent_jobs(item['domain'], item['a_record'])
        else:
            try:
                if os.path.exists("/usr/bin/rspamd"):
                    self.set_rspamd_dkim_key(args.domain)
                if os.path.exists("/usr/sbin/opendkim"):
                    self._gen_dkim_key(args.domain)
            except:
                return self.return_msg(public.returnMsg(False, '请检查Rspamd服务器是否已经启动！'))
            try:
                self._gevent_jobs(args.domain, None)  # 不需要验证A记录
            except:
                public.print_log('error:{}'.format(str(public.get_error_info())))
        try:
            public.writeFile(self._session_conf, json.dumps(self._session))
            return self.return_msg(public.returnMsg(True, '刷新成功！'))
        except:
            return self.return_msg(public.returnMsg(False, '刷新失败！'))

    def get_record_in_cache(self, item):
        try:
            item['mx_status'] = self._session['{0}:{1}'.format(item['domain'], 'MX')]["status"]
            item['spf_status'] = self._session['{0}:{1}'.format(item['domain'], 'TXT')]["status"]
            item['dkim_status'] = self._session['{0}:{1}'.format("default._domainkey." + item['domain'], 'TXT')][
                "status"]
            item['dmarc_status'] = self._session['{0}:{1}'.format("_dmarc." + item['domain'], 'TXT')]["status"]
            item['a_status'] = self._session['{0}:{1}'.format(item['a_record'], 'A')]["status"]
            if self._session['{0}:{1}'.format(item['domain'], 'PTR')]:
                item['ptr_status'] = self._session['{0}:{1}'.format(item['domain'], 'PTR')]["status"]
        except:
            public.print_log(item)
            self._gevent_jobs(item['domain'], item['a_record'])
            self.get_record_in_cache(item)
        return item

    def get_domains(self, args):
        '''
        域名查询接口
        :param args:
        :return:
        '''
        from mailModel import multipleipModel
        from sslModel.base import sslBase

        multipleipModel_main = multipleipModel.main()

        p = int(args.p) if 'p' in args else 1
        rows = int(args.size) if 'size' in args else 10
        callback = args.callback if 'callback' in args else ''
        count = self.M('domain').count()
        # 0 退出
        if count == 0:
            return self.return_msg(public.returnMsg(True, {'data': [],
                                           'page': "<div><span class='Pcurrent'>1</span><span class='Pcount'>Total 0</span></div>"}))

        # 获取分页数据
        page_data = public.get_page(count, p=p, rows=rows, callback=callback)

        data_list = self.M('domain').order('created desc').limit(page_data['shift'] + ',' + page_data['row']).select()
        if isinstance(data_list, str):
            return public.returnMsg(False, data_list)
        domain_ip = None
        path = '/www/server/panel/plugin/mail_sys/domain_ip.json'
        if os.path.exists(path):
            domain_ip = public.readFile(path)
            try:
                domain_ip = json.loads(domain_ip)
            except:
                pass

        blcheck_count = f'/www/server/panel/plugin/mail_sys/data/blcheck.json'  # 统计各个域名黑名单情况

        if os.path.exists(blcheck_count):
            blcheck_ = public.readFile(blcheck_count)
            try:
                blcheck_ = json.loads(blcheck_)
            except:
                pass
        else:
            blcheck_ = {}

        for item in data_list:
            try:
                if os.path.exists("/usr/bin/rspamd"):
                    self.set_rspamd_dkim_key(item['domain'])
                if os.path.exists("/usr/sbin/opendkim"):
                    self._gen_dkim_key(item['domain'])
            except:
                public.print_log(public.get_error_info())
                return self.return_msg(public.returnMsg(False, '请检查rspamd服务状态是否正常'))
            if not os.path.exists(self._session_conf):
                self._gevent_jobs(item['domain'], item['a_record'])
                item = self.get_record_in_cache(item)
            else:
                item = self.get_record_in_cache(item)
            item['dkim_value'] = self._get_dkim_value(item['domain'])
            item['dmarc_value'] = 'v=DMARC1;p=quarantine;rua=mailto:admin@{0}'.format(item['domain'])
            item['mx_record'] = item['a_record']
            item['ssl_status'] = self._get_multiple_certificate_domain_status(item['domain'])
            item['catch_all'], item['catch_type'], item['email'] = self._get_catchall_status(item['domain'])
            item['ssl_info'] = self.get_ssl_info(item['domain'])

            # # CatchALL
            # item['email'] = self._get_domain_forward(item['domain'])
            if domain_ip:
                item['ip_address'] = domain_ip[item['domain']] if domain_ip.get(item['domain'], None) else {"ipv4": [],
                                                                                                            "ipv6": []}
            else:
                item['ip_address'] = {"ipv4": [], "ipv6": []}

            # 新增域名黑名单检查
            item['domain_check_log'] = f"/www/server/panel/plugin/mail_sys/data/{item['a_record']}_blcheck.txt"
            item['domain_black_count'] = blcheck_.get(item['a_record'], {})
            item['dns_id'] = 0
            item['dns_name'] = ''

            # 新增dns_id和dns_name
            dns_data = public.M('ssl_domains').where("domain=?", (item['domain'],)).find()
            if dns_data:
                dns_dic = sslBase().get_dns_data(None).get(dns_data['dns_id'], {})
                if dns_dic:
                    item['dns_id'] = dns_data['dns_id']
                    item['dns_name'] = dns_dic['dns_name']
            bind = "@" + item['domain']
            ip_tags = multipleipModel_main.get_tag_bind(bind=bind)
            now_tag = ip_tags[0] if ip_tags else ''
            _tags = multipleipModel_main.get_ip_tags_api(args)
            ip_dic = {i['tag']: i['ip'] for i in _tags['data']}
            ip_rotate_conf = multipleipModel_main.get_ip_rotate_conf()
            ip_rotate = ip_rotate_conf.get(item['domain'])
            item['ip_tag'] = []
            item['ip_rotate'] = {"status": False}

            if now_tag:
                item['ip_tag'] = [{"tag": now_tag, "ip": ip_dic.get(now_tag, ''), "status": True}]

            if ip_rotate:
                item['ip_rotate'] = ip_rotate
                for ip_tag in ip_rotate["tags"]:
                    if ip_tag == now_tag:
                        continue
                    item['ip_tag'].append({
                        "tag": ip_tag,
                        "ip": ip_dic.get(ip_tag, ''),
                        "status": False
                    })
            else:
                item['ip_rotate'] = {"status": False}

        public.writeFile(self._session_conf, json.dumps(self._session))
        # 返回数据到前端
        return self.return_msg(public.returnMsg(True, {
            'data': data_list,
            'page': page_data['page']
        }))

    def _get_domain_forward(self, domain):
        address = '@' + domain.strip()
        result = self.M('alias').where('domain=? AND (address=? or address=?) AND active = 1', (domain, address, '%'+address)).getField('goto')
        if not result:
            return ''
        return result

    def _gevent_jobs(self, domain, a_record):
        from gevent import monkey
        monkey.patch_all()
        import gevent
        gevent.joinall([
            gevent.spawn(self._check_mx, domain),
            gevent.spawn(self._check_spf, domain),
            gevent.spawn(self._check_dkim, domain),
            gevent.spawn(self._check_dmarc, domain),
            gevent.spawn(self._check_a, a_record),
            # 新增ptr检查
            gevent.spawn(self._check_ptr, domain),
        ])
        return True

    def _build_dkim_sign_content(self, domain, dkim_path):
        dkim_signing_conf = """#{domain}_DKIM_BEGIN
  {domain} {{
    selectors [
     {{
       path: "{dkim_path}/default.private";
       selector: "default"
     }}
   ]
 }}
#{domain}_DKIM_END
""".format(domain=domain, dkim_path=dkim_path)
        return dkim_signing_conf

    def _dkim_sign(self, domain, dkim_sign_content):
        res = self.check_domain_in_rspamd_dkim_conf(domain)
        if not res:
            return False
        sign_domain = '#BT_DOMAIN_DKIM_BEGIN{}#BT_DOMAIN_DKIM_END'.format(
            res['sign_domain'].group(1) + dkim_sign_content)
        sign_conf = re.sub(res['rep'], sign_domain, res['sign_conf'])
        public.writeFile(res['sign_path'], sign_conf)
        return True

    def check_domain_in_rspamd_dkim_conf(self, domain):
        sign_path = '/etc/rspamd/local.d/dkim_signing.conf'
        sign_conf = public.readFile(sign_path)
        if not sign_conf:
            public.writeFile(sign_conf, "#BT_DOMAIN_DKIM_BEGIN\n#BT_DOMAIN_DKIM_END")
            sign_conf = """
domain {
#BT_DOMAIN_DKIM_BEGIN
#BT_DOMAIN_DKIM_END
}
            """
        rep = '#BT_DOMAIN_DKIM_BEGIN((.|\n)+)#BT_DOMAIN_DKIM_END'
        sign_domain = re.search(rep, sign_conf)
        if not sign_domain:
            return False
        if domain in sign_domain.group(1):
            return False
        return {"rep": rep, "sign_domain": sign_domain, 'sign_conf': sign_conf, 'sign_path': sign_path}

    def set_rspamd_dkim_key(self, domain):
        dkim_path = '/www/server/dkim/{}'.format(domain)
        if not dkim_path:
            os.makedirs(dkim_path)
        if not os.path.exists('{}/default.pub'.format(dkim_path)):
            dkim_shell = """
    mkdir -p {dkim_path}
    rspamadm dkim_keygen -s 'default' -b 1024 -d {domain} -k /www/server/dkim/{domain}/default.private > /www/server/dkim/{domain}/default.pub
    chmod 755 -R /www/server/dkim/{domain}
    """.format(dkim_path=dkim_path, domain=domain)
            public.ExecShell(dkim_shell)
        dkim_sign_content = self._build_dkim_sign_content(domain, dkim_path)
        if self._dkim_sign(domain, dkim_sign_content):
            public.ExecShell('systemctl reload rspamd')
        return True

    def _gen_dkim_key(self, domain):
        if not os.path.exists('/usr/share/perl5/vendor_perl/Getopt/Long.pm'):
            os.makedirs('/usr/share/perl5/vendor_perl/Getopt')
            public.ExecShell(
                'wget -O /usr/share/perl5/vendor_perl/Getopt/Long.pm {}/install/plugin/mail_sys/Long.pm -T 10'
                .format(public.get_url()))
        if not os.path.exists('/etc/opendkim/keys/{0}/default.private'.format(domain)):
            dkim_shell = '''
mkdir /etc/opendkim/keys/{domain}
opendkim-genkey -D /etc/opendkim/keys/{domain}/ -d {domain} -s default -b 1024
chown -R opendkim:opendkim /etc/opendkim/
systemctl restart  opendkim'''.format(domain=domain)
            keytable = "default._domainkey.{domain} {domain}:default:/etc/opendkim/keys/{domain}/default.private".format(
                domain=domain)
            sigingtable = "*@{domain} default._domainkey.{domain}".format(domain=domain)
            keytable_conf = public.readFile("/etc/opendkim/KeyTable")
            sigingtable_conf = public.readFile("/etc/opendkim/SigningTable")
            if keytable_conf:
                if keytable not in keytable_conf:
                    keytable_conf = keytable_conf + keytable + "\n"
                    public.writeFile("/etc/opendkim/KeyTable", keytable_conf)
            if sigingtable_conf:
                if sigingtable not in sigingtable_conf:
                    sigingtable_conf = sigingtable_conf + sigingtable + "\n"
                    public.writeFile("/etc/opendkim/SigningTable", sigingtable_conf)
            public.ExecShell(dkim_shell)

    def _get_dkim_value(self, domain):
        '''
        解析/etc/opendkim/keys/domain/default.txt得到域名要设置的dkim记录值
        :param domain:
        :return:
        '''
        if not os.path.exists("/www/server/dkim/{}".format(domain)):
            os.makedirs("/www/server/dkim/{}".format(domain))
        rspamd_pub_file = '/www/server/dkim/{}/default.pub'.format(domain)
        opendkim_pub_file = '/etc/opendkim/keys/{0}/default.txt'.format(domain)
        if os.path.exists(opendkim_pub_file) and not os.path.exists(rspamd_pub_file):
            opendkim_pub = public.readFile(opendkim_pub_file)
            public.writeFile(rspamd_pub_file, opendkim_pub)

            rspamd_pri_file = '/www/server/dkim/{}/default.private'.format(domain)
            opendkim_pri_file = '/etc/opendkim/keys/{}/default.private'.format(domain)
            opendkim_pri = public.readFile(opendkim_pri_file)
            public.writeFile(rspamd_pri_file, opendkim_pri)

        if not os.path.exists(rspamd_pub_file): return ''
        file_body = public.readFile(rspamd_pub_file).replace(' ', '').replace('\n', '').split('"')
        value = file_body[1] + file_body[3]
        return value

    def _get_session(self):
        session = public.readFile(self._session_conf)
        if session:
            session = json.loads(session)
        else:
            session = {}
        return session

    def _check_mx(self, domain):
        '''
        检测域名是否有mx记录
        :param domain:
        :return:
        '''
        a_record = self.M('domain').where('domain=?', domain).field('a_record').find()['a_record']
        key = '{0}:{1}'.format(domain, 'MX')
        now = int(time.time())
        try:
            value = ""
            if key in self._session and self._session[key]["status"] != 0:
                v_time = now - int(self._session[key]["v_time"])
                if v_time < self._check_time:
                    value = self._session[key]["value"]
            if '' == value:
                resolver = dns.resolver.Resolver()
                resolver.timeout = 5
                resolver.lifetime = 10
                try:
                    result = resolver.query(domain, 'MX')
                except:
                    result = resolver.resolve(domain, 'MX')
                value = str(result[0].exchange).strip('.')
            if not a_record:
                a_record = value
                self.M('domain').where('domain=?', domain).save('a_record', (a_record,))
            if value == a_record:
                self._session[key] = {"status": 1, "v_time": now, "value": value}
                return True
            self._session[key] = {"status": 0, "v_time": now, "value": value}
            return False
        except:
            public.print_log(public.get_error_info())
            self._session[key] = {"status": 0, "v_time": now,
                                  "value": "None of DNS query names exist:{}".format(domain)}
            return False

    def _check_spf(self, domain):
        '''
        检测域名是否有spf记录
        :param domain:
        :return:
        '''
        key = '{0}:{1}'.format(domain, 'TXT')
        now = int(time.time())
        try:
            value = ""
            if key in self._session and self._session[key]["status"] != 0:
                v_time = now - int(self._session[key]["v_time"])
                if v_time < self._check_time:
                    value = self._session[key]["value"]
            if '' == value:
                resolver = dns.resolver.Resolver()
                resolver.timeout = 5
                resolver.lifetime = 10
                try:
                    result = resolver.query(domain, 'TXT')
                except:
                    result = resolver.resolve(domain, 'TXT')
                for i in result.response.answer:
                    for j in i.items:
                        value += str(j).strip()
            if 'v=spf1' in value.lower():
                self._session[key] = {"status": 1, "v_time": now, "value": value}
                return True
            self._session[key] = {"status": 0, "v_time": now, "value": value}
            return False
        except:
            public.print_log(public.get_error_info())

            self._session[key] = {"status": 0, "v_time": now, "value": "None of DNS query spf exist:{}".format(domain)}
            return False

    def _check_dkim(self, domain):
        '''
        检测域名是否有dkim记录
        :param domain:
        :return:
        '''
        origin_domain = domain
        domain = 'default._domainkey.{0}'.format(domain)
        key = '{0}:{1}'.format(domain, 'TXT')
        now = int(time.time())
        try:
            value = ""
            if key in self._session and self._session[key]["status"] != 0:
                v_time = now - int(self._session[key]["v_time"])
                if v_time < self._check_time:
                    value = self._session[key]["value"]
            if '' == value:
                # result = model.resolver.query(domain, 'TXT')
                resolver = dns.resolver.Resolver()
                resolver.timeout = 5
                resolver.lifetime = 10
                try:
                    result = resolver.query(domain, 'TXT')
                except:
                    result = resolver.resolve(domain, 'TXT')
                for i in result.response.answer:
                    for j in i.items:
                        value += str(j).strip()
            new_v = self._get_dkim_value(origin_domain)
            if new_v and new_v in value:
                self._session[key] = {"status": 1, "v_time": now, "value": value}
                return True
            self._session[key] = {"status": 0, "v_time": now, "value": value}
            return False
        except:
            public.print_log(public.get_error_info())
            self._session[key] = {"status": 0, "v_time": now,
                                  "value": "None of DNS query names exist:{}".format(domain)}
            return False

    def _check_dmarc(self, domain):
        '''
        检测域名是否有dmarc记录
        :param domain:
        :return:
        '''
        domain = '_dmarc.{0}'.format(domain)
        key = '{0}:{1}'.format(domain, 'TXT')
        now = int(time.time())
        try:
            value = ""
            if key in self._session and self._session[key]["status"] != 0:
                v_time = now - int(self._session[key]["v_time"])
                if v_time < self._check_time:
                    value = self._session[key]["value"]
            if '' == value:
                # result = model.resolver.query(domain, 'TXT')
                resolver = dns.resolver.Resolver()
                resolver.timeout = 5
                resolver.lifetime = 10
                try:
                    result = resolver.query(domain, 'TXT')
                except:
                    result = resolver.resolve(domain, 'TXT')
                for i in result.response.answer:
                    for j in i.items:
                        value += str(j).strip()
            if 'v=dmarc1' in value.lower():
                self._session[key] = {"status": 1, "v_time": now, "value": value}
                return True
            self._session[key] = {"status": 0, "v_time": now, "value": value}
            return False
        except:
            public.print_log(public.get_error_info())
            self._session[key] = {"status": 0, "v_time": now,
                                  "value": "None of DNS query names exist:{}".format(domain)}
            return False

    def _check_ptr(self, domain):
        '''
        检测IP地址是否有PTR记录
        :param ip_address: IP地址字符串
        :return: bool
        '''

        ip_addresses = self._get_all_ip()
        ip_addresses = [ip for ip in ip_addresses if ip != '127.0.0.1']
        # ip可能有多个  使用域名拼接
        key = '{0}:{1}'.format(domain, 'PTR')

        now = int(time.time())

        try:
            value = ""
            if key in self._session and self._session[key]["status"] != 0:
                v_time = now - int(self._session[key]["v_time"])
                if v_time < self._check_time2:
                    value = self._session[key]["value"]
                    keys = self._session[key]["keys"]
                    values = self._session[key]["values"]

            if value == "":
                found_ptr_record = False
                result = None
                ptr_addr = None
                for ip_address in ip_addresses:
                    if ':' in ip_address:  # IPv6
                        reverse_domain = self._ipv6_to_ptr(ip_address)
                    else:  # IPv4
                        reverse_domain = '.'.join(reversed(ip_address.split('.'))) + '.in-addr.arpa'

                    resolver = dns.resolver.Resolver()
                    resolver.timeout = 1
                    resolver.lifetime = 3
                    try:
                        # public.print_log("ip 转RTR记录查询 -- {}".format(ip_address))
                        # public.print_log("RTR 记录查询地址 -- {}".format(reverse_domain))
                        result = resolver.query(reverse_domain, 'PTR')
                        found_ptr_record = True
                        ptr_addr = reverse_domain
                        # public.print_log('找到, 退出')
                        break
                    except:
                        continue
                # 有记录
                if found_ptr_record:
                    values = [str(rdata.target).rstrip('.') for rdata in result]
                    # public.print_log('有记录  {}'.format(values))
                    for i in values:
                        # public.print_log('对比  记录--- {}   传入域名--{}'.format(i, domain))
                        if i.endswith(domain):
                            self._session[key] = {"status": 1, "v_time": now, "value": i, "key": ptr_addr,
                                                  "values": values}
                            return True
                        else:
                            continue
                    self._session[key] = {"status": 0, "v_time": now,
                                          "value": "No matching PTR record:{}".format(values), "key": ptr_addr,
                                          "values": values}
                    return False
                else:
                    self._session[key] = {"status": 0, "v_time": now,
                                          "value": "None of DNS query PTR exist:{}".format(domain), "key": ptr_addr,
                                          "values": []}
                    return False
            if domain in value.lower() or value.lower().endswith(domain):
                self._session[key] = {"status": 1, "v_time": now, "value": value, "key": keys, "values": values}
                return True

        except:
            public.print_log(public.get_error_info())

            self._session[key] = {"status": 0, "v_time": now, "value": "None of DNS query PTR exist:{}".format(domain)}
            return False

    def _ipv6_to_ptr(self, ipv6_address):
        parts = ipv6_address.split(':')
        normalized_parts = [part.zfill(4) for part in parts]
        # 去掉冒号
        normalized_address = ''.join(normalized_parts)
        # 反转字符串
        reversed_address = normalized_address[::-1]
        # 加上点号
        ptr_address_parts = list(reversed_address)
        ptr_address = '.'.join(ptr_address_parts)
        ptr_address += '.ip6.arpa'
        # public.print_log("ptr_address  ^--{}".format(ptr_address))

        return ptr_address

    def get_mx_txt_cache(self, args):
        session = self._get_session()
        if 'domain' not in args:
            return self.return_msg(public.returnMsg(False, '请传入域名'))
        domain = args.domain

        mx_key = '{0}:{1}'.format(domain, 'MX')
        spf_key = '{0}:{1}'.format(domain, 'TXT')
        dkim_key = '{0}:{1}'.format('default._domainkey.{0}'.format(domain), 'TXT')
        dmarc_key = '{0}:{1}'.format('_dmarc.{0}'.format(domain), 'TXT')

        mx_value = session[mx_key] if mx_key in session else ''
        spf_value = session[spf_key] if spf_key in session else ''
        dkim_value = session[dkim_key] if dkim_key in session else ''
        dmarc_value = session[dmarc_key] if dmarc_key in session else ''

        return self.return_msg({
            'mx': mx_value,
            'spf': spf_value,
            'dkim': dkim_value,
            'dmarc': dmarc_value
        })

    def delete_mx_txt_cache(self, args):
        session = self._get_session()
        if 'domain' not in args:
            return self.return_msg(public.returnMsg(False, '请传入域名'))
        domain = args.domain

        mx_key = '{0}:{1}'.format(domain, 'MX')
        spf_key = '{0}:{1}'.format(domain, 'TXT')
        dkim_key = '{0}:{1}'.format('default._domainkey.{0}'.format(domain), 'TXT')
        dmarc_key = '{0}:{1}'.format('_dmarc.{0}'.format(domain), 'TXT')

        if mx_key in session: del (session[mx_key])
        if spf_key in session: del (session[spf_key])
        if dkim_key in session: del (session[dkim_key])
        if dmarc_key in session: del (session[dmarc_key])
        public.writeFile(self._session_conf, json.dumps(session))

        return self.return_msg(public.returnMsg(True,
                                '刷新域名({})在session中的缓存记录成功'.format(domain)))

    def add_domain(self, args):
        '''
        域名增加接口
        :param args:
        :return:
        '''
        if 'domain' not in args:
            return self.return_msg(public.returnMsg(False, '请传入域名'))
        domain = args.domain
        a_record = args.a_record
        if not a_record.endswith(domain):
            return self.return_msg(public.returnMsg(False, 'A记录 [{}] 不属于该域名'.format(a_record)))
        if not self._check_a(a_record):
            return self.return_msg(public.returnMsg(
                False, 'A记录解析失败 <br>域名：{}<br>IP  ：{}'.format(
                    a_record, self._session['{}:A'.format(a_record)]['value'])))

        if self.M('domain').where('domain=?', domain).count() > 0:
            return self.return_msg(public.returnMsg(False, '该域名已存在'))

        cur_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            self.M('domain').add('domain,a_record,created', (domain, a_record, cur_time))
        except:
            return self.return_msg(public.returnMsg(
                False, '邮局没有初始化成功！<br>'
                       '请尝试重新初始化,<br>'
                       '如果以下端口没访问将无法初始化 <br>port 25 [outbound direction]<br> '
                       '你可以尝试执行以下命令测试端口是否开启:<br><br> [ telnet gmail-smtp-in.l.google.com 25 ] <br> '
            ))
        errip = []
        # 增加域名的ip地址记录
        if 'ips' in args:
            data = {domain: {"ipv4": [], "ipv6": []}}
            ips = args.ips  # ips = '1.1.1.1;2.2.2.2;3.3.3.3'  或 ips = '1.1.1.1'
            # 根据 ; 拆分成列表
            ip_list = ips.split(';')
            # 循环列表
            for ip in ip_list:
                if public.is_ipv4(ip):
                    data[domain]["ipv4"].append(ip)
                elif public.is_ipv6(ip):
                    data[domain]["ipv6"].append(ip)
                else:
                    errip.append(ip)

            # 记录域名的ip address    /www/server/panel/plugin/mail_sys/domain_ip.json
            path = '/www/server/panel/plugin/mail_sys/domain_ip.json'

            if not os.path.exists(path):
                public.writeFile(path, json.dumps(data))
            else:
                rdata = public.readFile(path)
                try:
                    rdata = json.loads(rdata)
                except:
                    pass
                rdata.update(data)
                public.writeFile(path, json.dumps(rdata))
        # 绑定dns-api
        dns_id = 0
        if "dns_id" in args:
            dns_id = args.dns_id
        # 获取根域名
        from sslModel.base import sslBase
        root_domain, _, _ = sslBase().extract_zone(domain)
        # 判断是否存在该域名
        dns_data = public.M('ssl_domains').where("domain=?", (root_domain,)).find()
        if not dns_data:
            public.M('ssl_domains').add('domain,dns_id,type_id,endtime,ps', (domain, dns_id, 0, 0, ''))
        # 自动解析
        if 'auto_create_record' in args and args.auto_create_record:
            self.auto_create_dns_record(args)

        # 在虚拟用户家目录创建对应域名的目录
        if not os.path.exists('/www/vmail/{0}'.format(domain)):
            os.makedirs('/www/vmail/{0}'.format(domain))
        public.ExecShell('chown -R vmail:mail /www/vmail/{0}'.format(domain))
        if len(errip) > 0:
            return self.return_msg(public.returnMsg(True, '新增域名[{}]成功! ip err:{}'.format(domain, errip)))
        return self.return_msg(public.returnMsg(True, '新增域名[{0}]成功!'.format(domain)))

    def edit_domain_record(self, args):
        if 'domain' not in args:
            return public.returnMsg(False, '请输入域名')
        domain = args.domain
        a_record = args.a_record
        if self.M('domain').where('domain=?', domain).count() == 0:
            return self.return_msg(public.returnMsg(False, '该域名不存在'))
        self.M('domain').where('domain=?', domain).save('a_record', (a_record,))
        return self.return_msg(public.returnMsg(True, '修改域名[{0}]A记录成功!'.format(domain)))

    def delete_domain(self, args):
        '''
        域名删除接口
        :param args:
        :return:
        '''
        if 'domain' not in args:
            return self.return_msg(public.returnMsg(False, '请传入域名'))
        domain = args.domain

        # 删除域名记录
        domain_info = self.M('domain').where('domain=?', (domain,)).find()
        self.M('domain').where('domain=?', (domain,)).delete()

        # 删除域名下的邮箱记录
        self.M('mailbox').where('domain=?', (domain,)).delete()
        self.delete_mx_txt_cache(args)

        # 删除caheAll
        self._deledte_catchall(domain)

        # 删除域名黑名单检测日志
        domain_check_log = f'/www/server/panel/plugin/mail_sys/data/{domain_info["a_record"]}_blcheck.txt'
        if os.path.exists(domain_check_log):
            os.remove(domain_check_log)
        from mailModel import multipleipModel
        multipleipModel_main = multipleipModel.main()
        bind = "@{}".format(domain)
        multipleipModel_main.del_bind_ip_tag(bind)
        multipleipModel_main.del_ip_rotate_conf(bind)

        # 在虚拟用户家目录删除对应域名的目录
        public.ExecShell('rm -rf /www/vmail/{0}'.format(domain))
        public.ExecShell('systemctl restart postfix')
        return self.return_msg(public.returnMsg(True, '删除域成功! ({0})'.format(domain)))

    def create_mail_box(self, user, passwd):
        try:
            import imaplib
            conn = imaplib.IMAP4(port=143, host='127.0.0.1')
            conn.login(user, passwd)
            conn.select('Junk')
            conn.select('Trash')
            conn.select('Drafts')
            conn.logout()
            conn.close()
            return True
        except:
            return False

    def get_mailboxs1(self, args):
        '''
        邮箱用户查询接口
        :param args:
        :return:
        '''
        p = int(args.p) if 'p' in args else 1
        rows = int(args.size) if 'size' in args else 12
        callback = args.callback if 'callback' in args else ''
        if 'domain' in args and args.domain != "":
            domain = args.domain
            count = self.M('mailbox').where('domain=?', domain).count()
            # 获取分页数据
            page_data = public.get_page(count, p, rows, callback)
            # 获取当前页的数据列表
            data_list = self.M('mailbox').order('created desc').limit(
                page_data['shift'] + ',' + page_data['row']).where('domain=?', domain).field(
                'full_name,username,quota,created,modified,active,is_admin,password_encode,domain').select()
            mx = self._check_mx_domain(domain)
            for i in data_list:
                i['password'] = self._decode(i['password_encode'])
                del i['password_encode']
                i['mx'] = mx
            # 返回数据到前端
            return self.return_msg({'data': data_list, 'page': page_data['page']})
        else:
            count = self.M('mailbox').count()
            # 获取分页数据
            page_data = public.get_page(count, p, rows, callback)
            # 获取域名  以及域名对应mx记录
            domains_mx = {}
            domains = self.get_domain_name(None)["data"]
            for i in domains:
                mx = self._check_mx_domain(i)
                domains_mx[i] = mx

            # 获取当前页的数据列表
            data_list = self.M('mailbox').order('created desc').limit(
                page_data['shift'] + ',' + page_data['row']).field(
                'full_name,username,quota,created,modified,active,is_admin,password_encode,domain').select()
            for i in data_list:
                try:
                    i['password'] = self._decode(i['password_encode'])
                    del i['password_encode']
                    # 获取mx记录
                    i['mx'] = domains_mx[i['domain']]
                except:
                    pass

            # 返回数据到前端
            return self.return_msg({'data': data_list, 'page': page_data['page']})

    def get_mailboxs(self, args):
        '''
        邮箱用户查询接口
        :param args:
        :return:
        '''
        p = int(args.p) if 'p' in args else 1
        rows = int(args.size) if 'size' in args else 12
        callback = args.callback if 'callback' in args else ''
        if "search" in args and args.search != "":
            where_str = "username LIKE ?"
            where_args = (f"%{args.search.strip()}%",)
        else:
            where_str = ""
            where_args = ()
        if 'domain' in args and args.domain != "":
            domain = args.domain
            if where_str and where_args:
                where_str = "domain=? AND username LIKE?"
                where_args = (domain, f"%{args.search.strip()}%")
            else:
                where_str = "domain=?"
                where_args = (domain,)
            with self.M('mailbox') as obj_mailbox:
                count = obj_mailbox.where(where_str, where_args).count()
            # 获取分页数据
            page_data = public.get_page(count, p, rows, callback)
            # 获取当前页的数据列表
            with self.M('mailbox') as obj_mailbox:
                data_list = obj_mailbox.order('created desc').limit(
                    page_data['shift'] + ',' + page_data['row']).where(where_str, where_args).field(
                    'full_name,username,quota,created,modified,active,is_admin,password_encode,domain'
                ).select()
            mx = self._check_mx_domain(domain)
            for i in data_list:
                i['password'] = self._decode(i['password_encode'])
                del i['password_encode']
                i['mx'] = mx
            # 返回数据到前端
            return self.return_msg({'data': data_list, 'page': page_data['page']})
        else:
            with self.M('mailbox') as obj_mailbox:
                count = obj_mailbox.where(where_str, where_args).count()
            # 获取分页数据
            page_data = public.get_page(count, p, rows, callback)
            # 获取域名  以及域名对应mx记录
            domains_mx = {}
            domains = self.get_domain_name(None)["data"]
            for i in domains:
                mx = self._check_mx_domain(i)
                domains_mx[i] = mx
            # 获取当前页的数据列表
            with self.M('mailbox') as obj_mailbox:
                data_list = obj_mailbox.order('created desc').limit(
                    page_data['shift'] + ',' + page_data['row']).field(
                    'full_name,username,quota,created,modified,active,is_admin,password_encode,domain'
                ).where(where_str, where_args).select()
            for i in data_list:
                try:
                    i['password'] = self._decode(i['password_encode'])
                    del i['password_encode']
                    # 获取mx记录
                    i['mx'] = domains_mx[i['domain']]
                except:
                    pass

            # 返回数据到前端
            return self.return_msg({'data': data_list, 'page': page_data['page']})

    def _check_mx_domain(self, domain):
        '''
        查询域名的mx
        :param args:
        :return:
        '''
        key = '{0}:{1}'.format(domain, 'MX')
        session = public.readFile('/www/server/panel/plugin/mail_sys/session.json')
        if session:
            session = json.loads(session)
        else:
            return ''

        if session[key]['status']:
            mx = session[key]['value']
            return mx
        return ''

    def get_all_user(self, args):
        if 'domain' in args:
            data_list = self.M('mailbox').where('domain=? AND active=?', (args.domain, 1)).field(
                'full_name,username,quota,created,modified,active,is_admin,domain').select()
        else:
            data_list = self.M('mailbox').where('active=?', 1).field(
                'full_name,username,quota,created,modified,active,is_admin,domain').select()
        return self.return_msg(data_list)

    # 加密数据
    def _encode(self, data):
        str2 = data.strip()
        if sys.version_info[0] == 2:
            b64_data = base64.b64encode(str2)
        else:
            b64_data = base64.b64encode(str2.encode('utf-8'))
        return binascii.hexlify(b64_data).decode()

    # 解密数据
    def _decode(self, data):
        b64_data = binascii.unhexlify(data.strip())
        return base64.b64decode(b64_data).decode()

    # 检测密码强度
    def _check_passwd(self, password):
        return True if re.search(r"^(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).*$", password) and len(password) >= 8 else False

    def _check_email_address(self, email_address):
        return True if re.match(r"^\w+([.-]?\w+)*@.*", email_address) else False

    # 生成MD5-CRYPT模式加密的密码
    def _generate_crypt_passwd(self, password):
        if sys.version_info[0] == 2:
            shell_str = 'doveadm pw -s MD5-CRYPT -p {0}'.format(password)
            return public.ExecShell(shell_str)[0][11:].strip()
        else:
            import crypt
            return crypt.crypt(password, crypt.mksalt(crypt.METHOD_MD5))

    # 批量创建邮箱
    def __create_mail_box_mulitiple(self, info, args):
        create_successfully = {}
        create_failed = {}
        # status = False
        for data in info:
            if not data:
                continue
            try:
                args.quota = '{} {}'.format(data['quota'], data['unit'])
                args.username = data['username']
                args.password = data['password']
                args.full_name = data['full_name']
                args.is_admin = 0
                result = self.add_mailbox(args)
                if result['status']:
                    create_successfully[data['username']] = result['msg']
                    continue
                # create_successfully[data['username']] = create_other
                create_failed[data['username']] = result['msg']
            except:
                create_failed[data['username']] = "create error"
        # if not create_failed:
        #     status = True
        return {'status': True, 'msg': "Create the mailbox [ {} ] successfully".format(','.join(create_successfully)),
                'error': create_failed,
                'success': create_successfully}

    # 批量创建邮箱 todo 后期改 S() insertall
    def add_mailbox_multiple(self, args):
        '''
            @name 批量创建网站
            @author zhwen<2020-11-26>
            @param create_type txt  txt格式为 “Name|Address|Password|MailBox space|GB” 每个网站一行
                                                 "support|support|Password|5|GB"
            @param content     "["support|support|Password|5|GB"]"
        '''
        key = ['full_name', 'username', 'password', 'quota', 'unit']
        info = [dict(zip(key, i)) for i in
                [i.strip().split('|') for i in json.loads(args.content)]]
        if not info:
            return self.return_msg(public.returnMsg(False, '参数为空，密码强度不足（需要包含大小写字母和数字，长度不小于8）'))
        res = self.__create_mail_box_mulitiple(info, args)
        # # 批量创建完毕后
        # os.system('chown -R vmail:mail /www/vmail')
        return self.return_msg(res)

    def add_mailbox(self, args):
        '''
        新增邮箱用户
        :param args:
        :return:
        '''
        if 'username' not in args:
            return self.return_msg(public.returnMsg(False, '请传入账号名'))
        if not self._check_passwd(args.password):
            return self.return_msg(public.returnMsg(False, '密码强度不够(需要包括大小写字母和数字并且长度不小于8)'))
        username = args.username
        # if not self._check_email_address(username):
        #     return public.returnMsg(False, public.lang('Email address format is incorrect'))
        if not username.islower():
            return self.return_msg(public.returnMsg(False, '邮箱地址不能有大写字母！'))
        is_admin = args.is_admin if 'is_admin' in args else 0

        active = 1
        if 'active' in args and args.active == "0":
            active = 0
        local_part, domain = username.split('@')
        # 检查邮箱数量  查看数量限制
        with self.M('mailbox') as obj_mailbox:
            user_count = obj_mailbox.where('domain=?', (domain,)).count()
            count = obj_mailbox.where('username=?', (username,)).count()

        if count > 0:
            return self.return_msg(public.returnMsg(False, '邮箱已存在'))

        with self.M('domain') as obj_domain:
            domaincount = obj_domain.where('domain=?', (domain,)).getField("mailboxes")

        if user_count + 1 > domaincount:
            return self.return_msg(public.returnMsg(False, '{}的邮箱数量已达上限{}'.format(domain,
                                                                           domaincount)))

        password_encrypt = self._generate_crypt_passwd(args.password)
        password_encode = self._encode(args.password)

        domain_list = self.get_domain_name(None)["data"]
        if domain not in domain_list:
            return self.return_msg(public.returnMsg(False, '域名列表不存在域名{}'.format(domain)))
        num, unit = args.quota.split()
        if unit == 'GB':
            quota = float(num) * 1024 * 1024 * 1024
        else:
            quota = float(num) * 1024 * 1024

        cur_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        is_insert = True
        while is_insert:
            try:
                with self.M('mailbox') as obj_mailbox:
                    res = obj_mailbox.add(
                        'full_name,is_admin,username,password,password_encode,maildir,quota,local_part,domain,created,modified,active',
                        (args.full_name, is_admin, username, password_encrypt, password_encode, args.username + '/',
                         quota,
                         local_part, domain, cur_time, cur_time, active))
                if isinstance(res, str):
                    if 'error' in res:
                        # public.print_log("添加失败--{}".format(res))
                        continue

                is_insert = False
                # public.print_log("添加邮箱--{}".format(args.full_name))
            except:
                time.sleep(0.01)
                continue

        # 在虚拟用户家目录创建对应邮箱的目录
        user_path = '/www/vmail/{0}/{1}'.format(domain, local_part)
        os.makedirs(user_path)
        os.makedirs(user_path + '/tmp')
        os.makedirs(user_path + '/new')
        os.makedirs(user_path + '/cur')

        # 增加发送目录
        dir_path = '/www/vmail/{0}/{1}/.Sent/cur'.format(domain, local_part)
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)

        os.system('chown -R vmail:mail /www/vmail/{0}/{1}'.format(domain, local_part))
        # 检查登录效果 暂未处理
        # self.create_mail_box(username, args.password)

        return self.return_msg(public.returnMsg(True, '增加邮箱用户[{0}]成功!'.format(username)))

    def update_mailbox(self, args):
        '''
        邮箱用户修改接口
        :param args:
        :return:
        '''
        num, unit = args.quota.split()
        if unit == 'GB':
            quota = float(num) * 1024 * 1024 * 1024
        else:
            quota = float(num) * 1024 * 1024
        cur_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if 'password' in args and args.password != '':
            if not self._check_passwd(args.password):
                return public.returnMsg(False, '密码强度不够(需要包括大小写字母和数字并且长度不小于8)')
            # shell_str = 'doveadm pw -s MD5-CRYPT -p {0}'.format(args.password)
            # password_encrypt = public.ExecShell(shell_str)[0][11:].strip()
            password_encrypt = self._generate_crypt_passwd(args.password)
            password_encode = self._encode(args.password)
            self.M('mailbox').where('username=?', args.username).save(
                'password,password_encode,full_name,quota,modified,active,is_admin',
                (password_encrypt, password_encode, args.full_name, quota, cur_time, args.active, args.is_admin))
        else:
            self.M('mailbox').where('username=?', args.username).save('full_name,quota,modified,active,is_admin', (
                args.full_name, quota, cur_time, args.active, args.is_admin))
        return self.return_msg(public.returnMsg(True, '编辑邮箱用户成功! ({0})'.format(args.username)))

    def delete_mailbox(self, args):
        '''
        删除邮箱用户
        :param args:
        :return:
        '''
        if 'username' not in args:
            return self.return_msg(public.returnMsg(False, '请传入账号名'))
        username = args.username
        local_part, domain = username.split('@')
        res = self.M('mailbox').where('username=?', username).count()
        if not res:
            return self.return_msg(public.returnMsg(False, "删除失败!"))
        self.M('mailbox').where('username=?', username).delete()

        # 在虚拟用户家目录删除对应邮箱的目录
        if os.path.exists('/www/vmail/{0}/{1}'.format(domain, local_part)):
            public.ExecShell('rm -rf /www/vmail/{0}/{1}'.format(domain, local_part))
        return self.return_msg(public.returnMsg(True, '删除邮箱用户成功! ({0})'.format(username)))

    def send_mail(self, args):
        # 获取服务状态
        service_status = self.get_service_status(args)["data"]
        if not service_status['postfix']:
            return self.return_msg(public.returnMsg(False, '无法发送邮件, 错误原因: 部分服务未启动,请查看服务状态'))
        if not self._check_smtp_port():
            return self.return_msg(public.returnMsg(
                False, '部分云厂商(如：阿里云，腾讯云)默认关闭25端口，需联系厂商开通25端口后才能正常使用邮局服务'))

        # smtp_server: localhost
        # mail_from: lotk777 @ kern123.top  发件人
        # mail_to: ["977935501@qq.com"]   收件人列表
        # subject: 测试发送                 主题
        # content: < h3 >...                内容

        # 查询发件人
        mail_from = args.mail_from
        data = self.M('mailbox').where('username=?', mail_from).field('password_encode,full_name').find()
        password = self._decode(data['password_encode'])
        # 收件人 反序列成列表
        mail_to = json.loads(args.mail_to) if 'mail_to' in args else []

        # for mail_address in mail_to:
        #     # 邮件合法性
        #     if not self._check_email_address(mail_address):
        #         return public.returnMsg(False,
        #                                 public.lang('Failed to send mail, error reason: Incoming address format is incorrect'))
        subject = args.subject
        content = args.content

        # #增加订阅链接  测试----------------------
        #
        # # 生成邮箱jwt
        # mail_jwt = self.generate_jwt(mail_to[0])
        # # 获取公网ip
        # ip = public.readFile("/www/server/panel/data/iplist.txt")
        # # public.print_log("获取公网ip -- {}".format(ip))
        #
        # port = public.readFile('/www/server/panel/data/port.pl')
        # ssl_staus = public.readFile('/www/server/panel/data/ssl.pl')
        # if ssl_staus:
        #     ssl = 'https'
        # else:
        #     ssl = 'http'

        # if subtype.lower() == 'html':
        content = '<html>' + content + '</html>'

        # 附件?
        files = json.loads(args.files) if 'files' in args else []
        # 收件人判断
        if not isinstance(mail_to, list):
            return self.return_msg(public.returnMsg(False, '收件人不能解析成列表'))
        if len(mail_to) == 0:
            return self.return_msg(public.returnMsg(False, '收件人不能为空'))

        try:

            # 登录
            send_mail_client = SendMail(mail_from, password, 'localhost')
            # public.print_log("--------------------登录信息000 ---{}--({})".format(mail_from, password))
            # 用户名full_name
            send_mail_client.setMailInfo(data['full_name'], subject, content, files)
            # 收件人列表  此处记录调用次数
            _, domain = mail_from.split('@')
            result = send_mail_client.sendMail(mail_to, domain, 1)
            return self.return_msg(result)
        except Exception as e:
            public.print_log(public.get_error_info())
            return self.return_msg(public.returnMsg(False, '发送邮件失败,错误原因[{0}]'.format(str(e))))

    # 发送测试  -- 含退订
    def send_mail_test(self, args):
        # 获取服务状态
        service_status = self.get_service_status(args)["data"]
        if not service_status['postfix']:
            return self.return_msg(public.returnMsg(False, '无法发送邮件，错误原因：某些服务未启动，请检查服务状态'))
        # 检测多个 SMTP 服务器的 25 端口是否可用
        if not self._check_smtp_port():
            return self.return_msg(public.returnMsg(False, '一些云供应商（如阿里云、腾讯云）默认关闭端口25，您需要联系供应商打开端口25，然后才能正常使用邮局服务'))

        # try:
        #     from plugin.mail_sys.mail_send_bulk import SendMailBulk
        # except:
        #     import public.PluginLoader as plugin_loader
        #     bulk = plugin_loader.get_module('{}/plugin/mail_sys/mail_send_bulk.py'.format(public.get_panel_path()))
        #     SendMailBulk = bulk.SendMailBulk
        from mailModel.bulkModel import main as SendMailBulk

        return self.return_msg(SendMailBulk().send_mail_test(args))

    def _check(self, args):
        if args['fun'] in ['send_mail_http']:
            return self.return_msg(True)
        else:
            return self.return_msg(public.returnMsg(False, '接口不支持公共访问!'))

    def send_mail_http(self, args):
        service_status = self.get_service_status(args)["data"]
        if not service_status['postfix']:
            return self.return_msg(public.returnMsg(False, '无法发送邮件, 错误原因: 部分服务未启动,请查看服务状态'))
        if not self._check_smtp_port():
            return self.return_msg(public.returnMsg(
                False, '部分云厂商(如：阿里云，腾讯云)默认关闭25端口，需联系厂商开通25端口后才能正常使用邮局服务'))

        mail_from = args.mail_from
        password = args.password
        mail_to = [item.strip() for item in args.mail_to.split(',')]
        # for mail_address in mail_to:
        #     if not self._check_email_address(mail_address):
        #         return public.returnMsg(False,
        #                                 public.lang('Failed to send mail, error reason: Incoming address format is incorrect'))
        subject = args.subject
        content = args.content

        content = '<html>' + content + '</html>'
        files = json.loads(args.files) if 'files' in args else []

        try:
            data = self.M('mailbox').where('username=?', mail_from).field('full_name').find()
            send_mail_client = SendMail(mail_from, password, 'localhost')
            send_mail_client.setMailInfo(data['full_name'], subject, content, files)
            _, domain = mail_from.split('@')
            result = send_mail_client.sendMail(mail_to, domain, 1)
            return self.return_msg(result)
        except Exception as e:
            public.print_log(public.get_error_info())
            return self.return_msg(public.returnMsg(False, '发送邮件失败,错误原因[{0}]'.format(str(e))))

    # 获取文件编码类型
    def get_encoding(self, file):
        import chardet

        try:
            # 二进制方式读取，获取字节数据，检测类型
            with open(file, 'rb') as f:
                data = f.read()
                return chardet.detect(data)['encoding']
        except:
            return 'ascii'

    def get_mails(self, args):
        import email
        from mailModel import receive_mail
        reload(receive_mail)

        if 'username' not in args:
            return self.return_msg(public.returnMsg(False, '请传入账号名'))
        username = args.username
        if '@' not in username:
            return self.return_msg(public.returnMsg(False, '账号名不合法'))
        local_part, domain = username.split('@')
        if 'p' not in args:
            args.p = 1
        if 'p=' in args.p:
            args.p = args.p.replace('p=', '')

        receive_mail_client = receive_mail.ReceiveMail()
        mail_list = []
        try:
            dir_path = '/www/vmail/{0}/{1}/cur'.format(domain, local_part)
            if os.path.isdir(dir_path):
                # 先将new文件夹的邮件移动到cur文件夹
                new_path = '/www/vmail/{0}/{1}/new'.format(domain, local_part)
                if os.path.isdir(new_path):
                    for file in os.listdir(new_path):
                        src = os.path.join(new_path, file)
                        dst = os.path.join(dir_path, file)
                        shutil.move(src, dst)
                files = []
                for fname in os.listdir(dir_path):
                    mail_file = os.path.join(dir_path, fname)
                    if not os.path.exists(mail_file): continue
                    f_info = {}
                    f_info['name'] = fname
                    f_info['mtime'] = os.path.getmtime(mail_file)
                    # save_day = self.get_save_day(None)['message']
                    save_day = self.get_save_day(None)['data']
                    if save_day > 0:
                        deltime = int(time.time()) - save_day * 86400
                        if int(f_info['mtime']) < deltime:
                            os.remove(mail_file)
                            continue
                    files.append(f_info)
                files = sorted(files, key=lambda x: x['mtime'], reverse=True)
                page_data = public.get_page(len(files), int(args.p), 10)
                # public.print_log("page_data['page']----- {}".format(page_data['page']))
                # import re
                pattern = r"href='(?:/v2)?/plugin.*?\?p=(\d+)'"
                # 使用re.sub进行替换
                page_data['page'] = re.sub(pattern, r"href='\1'", page_data['page'])

                shift = int(page_data['shift'])
                row = int(page_data['row'])
                files = files[shift:shift + row]
                for d in files:
                    mail_file = os.path.join(dir_path, d['name'])
                    try:
                        mailInfo = receive_mail_client.getMailInfo(public.readFile(mail_file))
                        mailInfo['path'] = mail_file
                        mailInfo['text'] = public.readFile(mail_file)
                        mail_list.append(mailInfo)
                    except:
                        public.writeFile(
                            "{}/error.log".format(self.__setupPath),
                            public.get_error_info())
                        continue
                return self.return_msg({
                    'status':
                        True,
                    'data':
                        mail_list,
                    'page':
                        page_data['page'].replace(
                            '/plugin?action=a&name=mail_sys&s=get_mails&p=', '')
                })
            else:
                page_data = public.get_page(0, int(args.p), 10)
                return self.return_msg({
                    'status':
                        True,
                    'data':
                        mail_list,
                    'page':
                        page_data['page']
                })
        except Exception as e:
            print(public.get_error_info())
            return self.return_msg(public.returnMsg(False, '获取邮件失败,错误原因[{0}]'.format(str(e))))

    def delete_mail(self, args):
        path = args.path
        if not os.path.exists(path):
            return self.return_msg(public.returnMsg(False, '邮件路径不存在'))
        os.remove(path)
        return self.return_msg(public.returnMsg(True, '删除邮件成功'))

    def get_config(self, args):
        from files import files

        if args.service == 'postfix':
            args.path = '/etc/postfix/main.cf'
        elif args.service == 'dovecot':
            args.path = '/etc/dovecot/dovecot.conf'
        elif args.service == 'rspamd':
            args.path = '/etc/rspamd/rspamd.conf'
        elif args.service == 'opendkim':
            args.path = '/etc/opendkim.conf'
        else:
            return self.return_msg(public.returnMsg(False, '服务名不正确'))

        return self.return_msg(files().GetFileBody(args))

    def save_config(self, args):
        from files import files

        if args.service == 'postfix':
            args.path = '/etc/postfix/main.cf'
        elif args.service == 'dovecot':
            args.path = '/etc/dovecot/dovecot.conf'
        elif args.service == 'rspamd':
            args.path = '/etc/rspamd/rspamd.conf'
        elif args.service == 'opendkim':
            args.path = '/etc/opendkim.conf'
        else:
            return self.return_msg(public.returnMsg(False, '服务名不正确'))
        args.encoding = 'utf-8'

        result = files().SaveFileBody(args)
        if result['status']:
            if args.service == 'postfix':
                public.ExecShell('systemctl reload postfix')
            elif args.service == 'dovecot':
                public.ExecShell('systemctl reload dovecot')
            elif args.service == 'rspamd':
                public.ExecShell('systemctl reload rspamd')
            elif args.service == 'opendkim':
                public.ExecShell('systemctl reload opendkim')
        return self.return_msg(result)

    def service_admin(self, args):
        service_name = args.service
        if service_name.lower() not in [
                'postfix', 'dovecot', 'rspamd', 'opendkim'
        ]:
            return self.return_msg(public.returnMsg(False, '服务名不正确'))
        type = args.type
        if type.lower() not in ['start', 'stop', 'restart', 'reload']:
            return self.return_msg(public.returnMsg(False, '操作不正确'))

        exec_str = 'systemctl {0} {1}'.format(type, service_name)
        if type == 'reload':
            if service_name == 'postfix':
                exec_str = '/usr/sbin/postfix reload'
            elif service_name == 'dovecot':
                exec_str = '/usr/bin/doveadm reload'
            elif service_name == 'rspamd':
                exec_str = 'systemctl reload rspamd'
            elif service_name == 'opendkim':
                exec_str = 'systemctl reload opendkim'
        if service_name == 'opendkim' and type in ('start', 'restart'):
            exec_str = '''
sed -i "s#/var/run/opendkim/opendkim.pid#/run/opendkim/opendkim.pid#" /etc/opendkim.conf
sed -i "s#/var/run/opendkim/opendkim.pid#/run/opendkim/opendkim.pid#" /etc/sysconfig/opendkim
sed -i "s#/var/run/opendkim/opendkim.pid#/run/opendkim/opendkim.pid#" /usr/lib/systemd/system/opendkim.service
systemctl daemon-reload
systemctl enable opendkim
systemctl restart opendkim
'''

        public.ExecShell(exec_str)
        return self.return_msg(public.returnMsg(True,
                                '{0}执行{1}操作成功'.format(service_name, type)))

    # 获取收件箱 增加域名筛选
    def get_sent_mails(self, args):
        import email
        from mailModel import receive_mail
        reload(receive_mail)

        if 'username' not in args:
            return self.return_msg(public.returnMsg(False, '请传入账号名'))
        username = args.username
        if '@' not in username:
            return self.return_msg(public.returnMsg(False, '账号名不合法'))
        local_part, domain = username.split('@')
        if 'p' not in args:
            args.p = 1
        if 'p=' in args.p:
            args.p = args.p.replace('p=', '')

        receive_mail_client = receive_mail.ReceiveMail()
        mail_list = []
        try:
            # 读取发件箱cur文件夹的邮件
            dir_path = '/www/vmail/{0}/{1}/.Sent/cur'.format(domain, local_part)
            if os.path.isdir(dir_path):
                files = []
                for fname in os.listdir(dir_path):
                    mail_file = os.path.join(dir_path, fname)
                    if not os.path.exists(mail_file): continue
                    f_info = {}
                    f_info['name'] = fname
                    f_info['mtime'] = os.path.getmtime(mail_file)
                    save_day = self.get_save_day(None)["data"]
                    if save_day > 0:
                        deltime = int(time.time()) - save_day * 86400
                        if int(f_info['mtime']) < deltime:
                            os.remove(mail_file)
                            continue
                    files.append(f_info)
                files = sorted(files, key=lambda x: x['mtime'], reverse=True)
                page_data = public.get_page(len(files), int(args.p), 10)
                # 替换掉 href标签里的多余信息 只保留页码
                # pattern =r"href='(/v2)?/plugin.*?\?p=(\d+)'"
                pattern = r"href='(?:/v2)?/plugin.*?\?p=(\d+)'"
                # 使用re.sub进行替换
                page_data['page'] = re.sub(pattern, r"href='\1'", page_data['page'])
                shift = int(page_data['shift'])
                row = int(page_data['row'])
                files = files[shift:shift + row]
                for d in files:
                    mail_file = os.path.join(dir_path, d['name'])
                    fp = open(mail_file, 'r')
                    try:
                        message = email.message_from_file(fp)
                        mailInfo = receive_mail_client.getMailInfo(public.readFile(mail_file))
                        mailInfo['path'] = mail_file
                        mail_list.append(mailInfo)
                    except:
                        public.print_log(public.get_error_info())
                        continue
                return self.return_msg({
                    'status':
                        True,
                    'data':
                        mail_list,
                    'page':
                        page_data['page']
                })
            else:
                page_data = public.get_page(0, int(args.p), 10)
                return self.return_msg({
                    'status':
                        True,
                    'data':
                        mail_list,
                    'page':
                        page_data['page']
                })
        except Exception as e:
            public.print_log(public.get_error_info())
            return self.return_msg(public.returnMsg(False,
                                    '获取已发送邮件失败,错误原因[{0}]'.format(str(e))))

    # 设置postfix ssl
    def set_postfix_ssl(self, csrpath, keypath, act):
        main_file = self.postfix_main_cf
        master_file = "/etc/postfix/master.cf"
        main_conf = public.readFile(main_file)
        master_conf = public.readFile(master_file)
        if act == "0":
            csrpath = "/etc/pki/dovecot/certs/dovecot.pem"
            keypath = "/etc/pki/dovecot/private/dovecot.pem"
            master_rep = r"\n*\s*-o\s+smtpd_tls_auth_only=yes"
            master_str = "\n#  -o smtpd_tls_auth_only=yes"
            master_rep1 = r"\n*\s*-o\s+smtpd_tls_wrappermode=yes"
            master_str1 = "\n#  -o smtpd_tls_wrappermode=yes"
        else:
            master_rep = r"\n*#\s*-o\s+smtpd_tls_auth_only=yes"
            master_str = "\n  -o smtpd_tls_auth_only=yes"
            master_rep1 = r"\n*#\s*-o\s+smtpd_tls_wrappermode=yes"
            master_str1 = "\n  -o smtpd_tls_wrappermode=yes"

        for i in [[main_conf, main_file], [master_conf, master_file]]:
            if not i[0]:
                return public.returnMsg(False,
                                        "找不到postfix配置文件 {}".format(i[1]))
        main_rep = r"smtpd_tls_cert_file\s*=\s*.+"
        main_conf = re.sub(main_rep, "smtpd_tls_cert_file = {}".format(csrpath), main_conf)
        main_rep = r"smtpd_tls_key_file\s*=\s*.+"
        main_conf = re.sub(main_rep, "smtpd_tls_key_file = {}".format(keypath), main_conf)
        public.writeFile(main_file, main_conf)
        # master_rep = "#\s*-o\s+smtpd_tls_auth_only=yes"
        master_conf = re.sub(master_rep, master_str, master_conf)
        master_conf = re.sub(master_rep1, master_str1, master_conf)
        public.writeFile(master_file, master_conf)

    def get_dovecot_version(self, args=None):
        data = public.ExecShell("dpkg -l|grep dovecot-core|awk -F':' '{print $2}'")[0]
        if os.path.exists('/etc/redhat-release'):
            data = public.ExecShell('rpm -qa | grep dovecot | grep -v pigeonhole')[0].split('-')[1]
        return self.return_msg(data)

    def set_dovecot_ssl(self, csrpath, keypath, act):
        dovecot_version = self.get_dovecot_version()['data']
        ssl_file = "/etc/dovecot/conf.d/10-ssl.conf"
        ssl_conf = public.readFile(ssl_file)
        if not ssl_conf:
            return public.returnMsg(False,
                                    "找不到dovecot配置文件 {}".format(ssl_file))
        if act == "0":
            csrpath = "/etc/pki/dovecot/certs/dovecot.pem"
            keypath = "/etc/pki/dovecot/private/dovecot.pem"
        ssl_rep = r"ssl_cert\s*=\s*<.+"
        ssl_conf = re.sub(ssl_rep, "ssl_cert = <{}".format(csrpath), ssl_conf)
        ssl_rep = r"ssl_key\s*=\s*<.+"
        ssl_conf = re.sub(ssl_rep, "ssl_key = <{}".format(keypath), ssl_conf)
        if dovecot_version.startswith('2.3'):
            if act == '1':
                if not os.path.exists('/etc/dovecot/dh.pem') or os.path.getsize('/etc/dovecot/dh.pem') < 300:
                    public.ExecShell('openssl dhparam 2048 > /etc/dovecot/dh.pem')
                ssl_conf = ssl_conf + "\nssl_dh = </etc/dovecot/dh.pem"
            else:
                ssl_conf = re.sub(r'\nssl_dh = </etc/dovecot/dh.pem', '', ssl_conf)
                os.remove('/etc/dovecot/dh.pem')
        public.writeFile(ssl_file, ssl_conf)

    # 设置ssl  弃用
    def set_ssl(self, args):
        path = '{}/cert/'.format(self.__setupPath)
        csrpath = path + "fullchain.pem"
        keypath = path + "privkey.pem"
        backup_cert = '/tmp/backup_cert_mail_sys'
        if hasattr(args, "act") and args.act == "1":
            if args.key.find('KEY') == -1:
                return self.return_msg(public.returnMsg(False, '私钥错误，请检查!'))
            if args.csr.find('CERTIFICATE') == -1:
                return self.return_msg(public.returnMsg(False, '证书错误，请检查!'))
            public.writeFile('/tmp/mail_cert.pl', str(args.csr))
            if not public.CheckCert('/tmp/mail_cert.pl'):
                return self.return_msg(public.returnMsg(False, '证书错误，请以pem格式粘贴正确的证书!'))
            if os.path.exists(backup_cert): shutil.rmtree(backup_cert)
            if os.path.exists(path): shutil.move(path, backup_cert)
            if os.path.exists(path): shutil.rmtree(path)

            os.makedirs(path)
            public.writeFile(keypath, args.key)
            public.writeFile(csrpath, args.csr)
        else:
            if os.path.exists(csrpath):
                os.remove(csrpath)
            if os.path.exists(keypath):
                os.remove(keypath)

        # 写入配置文件
        p_result = self.set_postfix_ssl(csrpath, keypath, args.act)
        if p_result: return self.return_msg(p_result)
        d_result = self.set_dovecot_ssl(csrpath, keypath, args.act)
        if d_result: return self.return_msg(d_result)

        import time
        for i in ["dovecot", "postfix"]:
            args.service = i
            args.type = "restart"
            self.service_admin(args)
            time.sleep(1)
        # 清理备份证书
        if os.path.exists(backup_cert): shutil.rmtree(backup_cert)
        return public.returnMsg(True, '设置成功')

    # 获取ssl状态   弃用
    def get_ssl_status(self, args):
        path = '{0}/cert/'.format(self.__setupPath)
        csrpath = path + "fullchain.pem"
        keypath = path + "privkey.pem"
        if not (os.path.exists(csrpath) and os.path.exists(keypath)):
            return self.return_msg(False)
        main_file = self.postfix_main_cf
        main_conf = public.readFile(main_file)
        master_file = "/etc/postfix/master"
        master_conf = public.readFile(master_file)
        dovecot_ssl_file = "/etc/dovecot/conf.d/10-ssl.conf"
        dovecot_ssl_conf = public.readFile(dovecot_ssl_file)
        if main_conf:
            if csrpath not in main_conf and keypath not in main_conf:
                return self.return_msg(False)
        if master_conf:
            rep = r"\n*\s*-o\s+smtpd_sasl_auth_enable\s*=\s*yes"
            if not re.search(rep, master_conf):
                return self.return_msg(False)
        if dovecot_ssl_conf:
            if csrpath not in main_conf and keypath not in main_conf:
                return self.return_msg(False)
        return self.return_msg(True)

    # 获取可以监听的IP
    def _get_all_ip(self):
        # import psutil

        public_ip = self._get_pubilc_ip()
        net_info = psutil.net_if_addrs()
        addr = []
        for i in net_info.values():
            addr.append(i[0].address)
        locataddr = public.readFile('/www/server/panel/data/iplist.txt')
        if not locataddr:
            locataddr = ""
        ip_address = locataddr.strip()
        if ip_address not in addr:
            addr.append(ip_address)
        if public_ip not in addr:
            addr.append(public_ip)
        return addr

    def get_bcc(self, args):
        forward = public.readFile(self._forward_conf)
        if forward:
            forward = json.loads(forward)
        else:
            forward = {"recipient": [], "sender": []}
        # 如果没有 active 字段, 则增加 "active":1
        if forward['recipient']:
            for d in forward['recipient']:
                d.setdefault('active', 1)
        if forward['sender']:
            for d in forward['sender']:
                d.setdefault('active', 1)
        return self.return_msg(forward)

    # 设置邮件秘抄
    def set_mail_bcc(self, args):
        """
        type            sender/recipien
        user            domain_name/email_address
        forward_user    email_address
        domain          domain
        active          active  0/1   默认1 开启
        :param args:
        :return:
        """
        # 增加 active 默认1
        if not hasattr(args, 'active') or args.get('active/d', 1) == 1:
            args.active = 1
        else:
            args.active = 0
        # if not hasattr(args, 'domain') or args.get('domain/s', '') == '':
        #     args.domain = args.user.strip().split('@')[1]
        args.domain = args.user.strip().split('@')[1]
        data = self.get_bcc(args)['data']
        for d in data[args.type]:
            if args.user == d["user"] and args.forward_user == d[
                    "forward_user"]:
                return self.return_msg(public.returnMsg(False, "已存在"))

        # 启用的状态下才能加入密抄
        if args.active:
            rep = r"^(?=^.{3,255}$)[a-zA-Z0-9\_\-][a-zA-Z0-9\_\-]{0,62}(\.[a-zA-Z0-9\_\-][a-zA-Z0-9\_\-]{0,62})+$"
            if re.search(rep, args.user):
                content = "\n@{} {}".format(args.user, args.forward_user)
            else:
                content = "\n{} {}".format(args.user, args.forward_user)
            # 密抄文件
            bcc_file = "/etc/postfix/{}_bcc".format(args.type)
            public.writeFile(bcc_file, content, "a+")

        # 增加启停开关
        data[args.type].append(
            {"domain": args.domain, "user": args.user, "forward_user": args.forward_user, "active": args.active})

        public.writeFile(self._forward_conf, json.dumps(data))
        for i in ["/etc/postfix/sender_bcc", "/etc/postfix/recipient_bcc"]:
            if not os.path.exists(i):
                public.writeFile(i, "")
        # bcc_conf = '\nrecipient_bcc_maps = hash:/etc/postfix/recipient_bcc\nsender_bcc_maps = hash:/etc/postfix/sender_bcc\n'
        # public.writeFile(self.postfix_main_cf, bcc_conf, 'a+')

        bcc_conf = ''
        if not self.check_postfix_bcc('recipient_bcc_maps'):
            bcc_conf += 'recipient_bcc_maps = hash:/etc/postfix/recipient_bcc\n'
        if not self.check_postfix_bcc('sender_bcc_maps'):
            bcc_conf += 'sender_bcc_maps = hash:/etc/postfix/sender_bcc\n'
        if bcc_conf:
            public.writeFile(self.postfix_main_cf, '\n'+bcc_conf, 'a+')

        shell_str = '''
postmap /etc/postfix/recipient_bcc
postmap /etc/postfix/sender_bcc
systemctl reload postfix
'''
        public.ExecShell(shell_str)
        return self.return_msg(public.returnMsg(True, "设置成功"))

    def check_postfix_bcc(self, act):
        try:
            res = public.ExecShell('postconf {}'.format(act))
            if '=' in res[0] and res[0].split('=')[1].strip():
                return True
            else:
                return False
        except:
            return False

    # 删除邮件秘送
    def del_bcc(self, args):
        data = self.get_bcc(args)['data']
        bcc_file = "/etc/postfix/{}_bcc".format(args.type)
        # 密抄配置
        conf = public.readFile(bcc_file)
        n = 0
        rep = r"\n*{}\s+{}".format(args.user, args.forward_user)
        for d in data[args.type]:
            if args.user == d["user"] and args.forward_user == d["forward_user"]:
                del (data[args.type][n])
                public.writeFile(self._forward_conf, json.dumps(data))
                conf = re.sub(rep, '', conf)
                public.writeFile(bcc_file, conf)
                public.ExecShell(
                    'postmap {} && systemctl reload postfix'.format(bcc_file))
                return self.return_msg(public.returnMsg(True, '删除成功'))
            n += 1
        return self.return_msg(public.returnMsg(True, '删除失败'))

    # 修改邮件密送 -- 删除 添加
    def update_bcc(self, args):
        self.del_bcc(args)
        args.type = args.type_new
        args.forward_user = args.forward_user_new
        args.active = args.active_new
        self.set_mail_bcc(args)
        return self.return_msg(public.returnMsg(True, '修改成功'))

    # 设置邮件中继
    def set_smtp_relay(self, args):
        """
            username: mailgun的用户名
            passwd: mailgun的密码
            smtphost: smtp地址
            port: smtp端口
        """
        username = args.username
        passwd = args.passwd
        smtphost = args.smtphost
        port = args.port
        add_paramater = """
#BEGIN_POSTFIX_RELAY
relayhost = [{smtphost}]:{port}
smtp_sasl_auth_enable = yes
smtp_sasl_password_maps = static:{username}:{passwd}
smtp_sasl_security_options = noanonymous
#END_POSTFIX_RELAY
""".format(smtphost=smtphost, port=port, username=username, passwd=passwd)
        if self.get_smtp_status(args)['status']:
            return self.return_msg(public.returnMsg(False, "smtp中继配置已经存在"))
        public.writeFile(self.postfix_main_cf, add_paramater, 'a+')
        return self.return_msg(public.returnMsg(True, "设置邮件中继成功"))

    # 获取中继信息
    def get_smtp_status(self, args):
        conf = public.readFile(self.postfix_main_cf)
        if not conf:
            return self.return_msg(public.returnMsg(False, "没有找到中继配置信息"))
        if "BEGIN_POSTFIX_RELAY" in conf:
            host_port_reg = r"relayhost\s*=\s*\[([\.\w]+)\]:(\d+)"
            tmp = re.search(host_port_reg, conf)
            host = port = user = passwd = ""
            if tmp:
                host = tmp.groups(1)[0]
                port = tmp.groups(2)[1]
            user_passwd_reg = r"smtp_sasl_password_maps\s*=\s*static:(.*?):(.*)"
            tmp = re.search(user_passwd_reg, conf)
            if tmp:
                user = tmp.groups(1)[0]
                passwd = tmp.groups(2)[1]
            return self.return_msg(public.returnMsg(True, {
                "host": host,
                "port": port,
                "user": user,
                "passwd": passwd
            }))
        return self.return_msg(public.returnMsg(False, "没有找到中继配置信息"))

    # 取消中继
    def cancel_smtp_relay(self, args):
        conf = public.readFile(self.postfix_main_cf)
        reg = r"\n#BEGIN_POSTFIX_RELAY(.|\n)+#END_POSTFIX_RELAY\n"
        tmp = re.search(reg, conf)
        if not tmp:
            return self.return_msg(public.returnMsg(False, "smtp中继配置不存在"))
        conf = re.sub(reg, "", conf)
        public.writeFile(self.postfix_main_cf, conf)
        return self.return_msg(public.returnMsg(True, "取消邮件中继成功"))

    # 获取反垃圾服务监听ip和端口
    def _get_anti_server_ip_port(self, get):
        conf = public.readFile('/etc/amavisd/amavisd.conf')
        if not os.path.exists('/etc/redhat-release'):
            conf = public.readFile('/etc/amavis/conf.d/20-debian_defaults')
        reg = r'\n\${}\s*=\s*[\'\"]?(.*?)[\'\"]?;'
        spam_server_ip_reg = reg.format('inet_socket_bind')
        spam_server_port_reg = reg.format('inet_socket_port')
        spam_server_ip = re.search(spam_server_ip_reg, conf)
        if spam_server_ip:
            spam_server_ip = spam_server_ip.groups(1)[0]
        else:
            spam_server_ip = '127.0.0.1'
        spam_server_port = re.search(spam_server_port_reg, conf)
        if spam_server_port:
            spam_server_port = spam_server_port.groups(1)[0]
        else:
            spam_server_port = '10024'
        return self.return_msg({
            'spam_server_port': spam_server_port,
            'spam_server_ip': spam_server_ip
        })

    # 设置postfix main配置支持反垃圾
    def _set_main_cf_anti_spam(self, args):
        conf = public.readFile(self.postfix_main_cf)
        anti_spam_conf = """
##BT-ANTISPAM-BEGIN
content_filter=amavisfeed:[{}]:{}
##BT-ANTISPAM-END
"""
        if 'amavisfeed' in conf:
            return
        if args.spam_server_ip == 'localhost':
            spam_server_info = self._get_anti_server_ip_port(get=None)
            anti_spam_conf = anti_spam_conf.format(spam_server_info['spam_server_ip'],
                                                   spam_server_info['spam_server_port'])
            public.writeFile(self.postfix_main_cf, conf + anti_spam_conf)
        else:
            anti_spam_conf = anti_spam_conf.format(args.spam_server_ip, args.spam_server_port)
            public.writeFile(self.postfix_main_cf, conf + anti_spam_conf)

    # 设置postfix master配置支持反垃圾
    def _set_master_cf_anti_spam(self):
        master_file = '/etc/postfix/master.cf'
        conf = public.readFile(master_file)
        if re.search('##BT-ANTISPAM-BEGIN', conf):
            return
        anti_conf = """
##BT-ANTISPAM-BEGIN
amavisfeed unix -   -   n   -   2    smtp
 -o smtp_data_done_timeout=1000
 -o smtp_send_xforward_command=yes
 -o disable_dns_lookups=yes
 -o max_use=20
127.0.0.1:10025 inet n -   n   -   -    smtpd
 -o content_filter=
 -o smtpd_delay_reject=no
 -o smtpd_client_restrictions=permit_mynetworks,reject
 -o smtpd_helo_restrictions=
 -o smtpd_sender_restrictions=
 -o smtpd_recipient_restrictions=permit_mynetworks,reject
 -o smtpd_data_restrictions=reject_unauth_pipelining
 -o smtpd_end_of_data_restrictions=
 -o smtpd_restriction_classes=
 -o mynetworks=127.0.0.0/8,192.168.0.0/16
 -o smtpd_error_sleep_time=0
 -o smtpd_soft_error_limit=1001
 -o smtpd_hard_error_limit=1000
 -o smtpd_client_connection_count_limit=0
 -o smtpd_client_connection_rate_limit=0
 -o receive_override_options=no_header_body_checks,no_unknown_recipient_checks,no_milters
 -o local_header_rewrite_clients=
##BT-ANTISPAM-END
 """
        public.writeFile(master_file, conf + anti_conf)

    def _set_dovecot_cf_anti_spam(self):
        '''
        设置dovecot配置支持反垃圾
        :return:
        '''
        # 判断dovecot-sieve是否安装成功
        if os.path.exists('/etc/dovecot/conf.d/90-sieve.conf'):
            download_conf_shell = '''
wget "{download_conf_url}/mail_sys/dovecot/dovecot.conf" -O /etc/dovecot/dovecot.conf -T 10
wget "{download_conf_url}/mail_sys/dovecot/15-lda.conf" -O /etc/dovecot/conf.d/15-lda.conf -T 10
wget "{download_conf_url}/mail_sys/dovecot/20-lmtp.conf" -O /etc/dovecot/conf.d/20-lmtp.conf -T 10
wget "{download_conf_url}/mail_sys/dovecot/90-plugin.conf" -O /etc/dovecot/conf.d/90-plugin.conf -T 10
wget "{download_conf_url}/mail_sys/dovecot/90-sieve.conf" -O /etc/dovecot/conf.d/90-sieve.conf -T 10
    '''.format(download_conf_url=public.get_url())
            public.ExecShell(download_conf_shell)
            if not os.path.exists('/etc/dovecot/sieve'):
                os.makedirs('/etc/dovecot/sieve')
            default_sieve = '''require "fileinto";
if header :contains "X-Spam-Flag" "YES" {
    fileinto "Junk";
}'''
            public.writeFile('/etc/dovecot/sieve/default.sieve', default_sieve)
            public.ExecShell('chown -R vmail:dovecot /etc/dovecot')

    # 开启反垃圾
    def turn_on_anti_spam(self, args):
        if args.spam_server_ip != 'localhost':
            return self.return_msg(public.returnMsg(False, '目前还不支持远程扫描，正在测试该功能'))
        if args.spam_server_ip == 'localhost' and not os.path.exists(
                '/www/server/panel/plugin/anti_spam'):
            return self.return_msg(public.returnMsg(False, '请先安装[反垃圾邮件网关]插件,并将要监听的域名添加到配置里面'))
        self._set_main_cf_anti_spam(args)
        self._set_master_cf_anti_spam()
        self._set_dovecot_cf_anti_spam()
        public.ExecShell('/usr/sbin/postfix reload')
        public.ExecShell('systemctl restart dovecot')
        public.ExecShell('systemctl restart spamassassin')
        return self.return_msg(public.returnMsg(True, '开启成功'))

    # # 关闭反垃圾
    def turn_off_anti_spam(self, args):
        # 清理master配置
        master_file = '/etc/postfix/master.cf'
        conf = public.readFile(master_file)
        reg = "\n##BT-ANTISPAM-BEGIN(.|\n)+##BT-ANTISPAM-END\n"
        conf = re.sub(reg, '', conf)
        public.writeFile(master_file, conf)
        # 清理main配置
        conf = public.readFile(self.postfix_main_cf)
        conf = re.sub(reg, '', conf)
        public.writeFile(self.postfix_main_cf, conf)
        public.ExecShell('/usr/sbin/postfix reload')
        return self.return_msg(public.returnMsg(True, '关闭成功'))

    # 获取反垃圾开启状态
    def get_anti_spam_status(self, args):
        conf = public.readFile(self.postfix_main_cf)
        if re.search('##BT-ANTISPAM-BEGIN', conf):
            return self.return_msg(True)
        return self.return_msg(False)

    # 获取数据备份任务是否存在的状态
    def get_backup_task_status(self, get):
        c_id = public.M('crontab').where('name=?',
                                         u'[勿删]堡塔邮局-数据备份任务').getField('id')
        if not c_id: return self.return_msg(public.returnMsg(False, '定时任务不存在!'))
        data = public.M('crontab').where('name=?', u'[勿删]堡塔邮局-数据备份任务').find()
        return self.return_msg(public.returnMsg(True, data))

    # 打开数据备份任务
    def open_backup_task(self, get):
        import crontab
        p = crontab.crontab()

        c_id = public.M('crontab').where('name=?',
                                         u'[勿删]堡塔邮局-数据备份任务').getField('id')
        if c_id:
            data = {}
            data['id'] = c_id
            data['name'] = u'[勿删]堡塔邮局-数据备份任务'
            data['type'] = get.type
            data['where1'] = get.where1 if 'where1' in get else ''
            data['sBody'] = ''
            data['backupTo'] = get.backupTo if 'backupTo' in get else 'localhost'
            data['sType'] = 'path'
            data['hour'] = get.hour if 'hour' in get else ''
            data['minute'] = get.minute if 'minute' in get else ''
            data['week'] = get.week if 'week' in get else ''
            data['sName'] = '/www/vmail/'
            data['urladdress'] = ''
            data['save'] = get.save
            p.modify_crond(data)
            return self.return_msg(public.returnMsg(True, '编辑成功!'))
        else:
            data = {}
            data['name'] = u'[勿删]堡塔邮局-数据备份任务'
            data['type'] = get.type
            data['where1'] = get.where1 if 'where1' in get else ''
            data['sBody'] = ''
            data['backupTo'] = get.backupTo if 'backupTo' in get else 'localhost'
            data['sType'] = 'path'
            data['hour'] = get.hour if 'hour' in get else ''
            data['minute'] = get.minute if 'minute' in get else ''
            data['week'] = get.week if 'week' in get else ''
            data['sName'] = '/www/vmail/'
            data['urladdress'] = ''
            data['save'] = get.save
            p.AddCrontab(data)
            return self.return_msg(public.returnMsg(True, '设置成功!'))

    # 关闭数据备份任务
    def close_backup_task(self, get):
        import crontab

        p = crontab.crontab()
        c_id = public.M('crontab').where('name=?',
                                         u'[勿删]堡塔邮局-数据备份任务').getField('id')
        if not c_id: return self.return_msg(public.returnMsg(False, '定时任务不存在!'))
        args = {"id": c_id}
        p.DelCrontab(args)
        return self.return_msg(public.returnMsg(True, '关闭成功!'))

    # 获取已安装云存储插件列表
    def get_cloud_storage_list(self, get):
        data = []
        tmp = public.readFile('data/libList.conf')
        libs = json.loads(tmp)
        for lib in libs:
            if 'opt' not in lib: continue
            filename = 'plugin/{}'.format(lib['opt'])
            if not os.path.exists(filename): continue
            data.append({'name': lib['name'], 'value': lib['opt']})
        return self.return_msg(data)

    # 获取本地备份文件列表
    def get_backup_file_list(self, get):
        dir_path = get.path.strip()
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, 384)
        dir_path_vmail = os.path.join(dir_path, 'vmail')
        files = []
        for file_name in os.listdir(dir_path):
            if not file_name.startswith('path_vmail'): continue
            file_path = os.path.join(dir_path, file_name)
            if not os.path.exists(file_path): continue
            f_info = {}
            f_info['name'] = file_name
            f_info['mtime'] = os.path.getmtime(file_path)
            files.append(f_info)
        if os.path.exists(dir_path_vmail):
            for file_name in os.listdir(dir_path_vmail):
                if not file_name.startswith('path_vmail'): continue
                file_path = os.path.join(dir_path_vmail, file_name)
                if not os.path.exists(file_path): continue
                f_info = {}
                f_info['name'] = 'vmail/'+ file_name
                f_info['mtime'] = os.path.getmtime(file_path)
                files.append(f_info)
        files = sorted(files, key=lambda x: x['mtime'], reverse=True)
        return self.return_msg(files)

    def get_backup_path(self, get):
        path = public.M('config').where("id=?", (1,)).getField('backup_path')
        path = os.path.join(path, 'path')
        return self.return_msg(os.path.join(path, 'vmail'))

    # 数据恢复
    def restore(self, get):
        file_path = get.file_path.strip()
        if not os.path.exists(file_path):
            return self.return_msg(public.returnMsg(False, '文件不存在'))
        # 检测当前文件是否是正确的备份文件 /.../path_vmail_20240614_095728.tar.gz
        # 以 path_vmail开头  并且是 .tar.gz 结尾
        file_name = os.path.basename(file_path)
        if file_name.startswith('path_vmail') and file_name.endswith('.tar.gz'):
            cmd = 'cd {} && tar -xzvf {} 2>&1'.format('/www', file_path)
            print(cmd)
            public.ExecShell(cmd)
            return self.return_msg(public.returnMsg(True, '恢复数据完成'))
        else:
            return self.return_msg(public.returnMsg(False, '这不是有效的备份文件!,文件名应该以"path_vmail"开头，以".tar.gz"结尾'))

    # 设置收件箱和发件箱邮件保存的天数
    def set_save_day(self, get):
        # 更新缓存
        # from BTPanel import cache
        skey = "mail_save_day"
        cache.set(skey, get.save_day, 86400)

        public.writeFile(self._save_conf, get.save_day)
        return self.return_msg(public.returnMsg(True, '设置成功'))

    # 获取收件箱和发件箱邮件保存的天数
    def get_save_day(self, get):
        # from BTPanel import cache
        skey = "mail_save_day"
        cache_day = cache.get(skey)
        if cache_day:
            return self.return_msg(int(cache_day))
        if not os.path.exists(self._save_conf):
            return self.return_msg(0)
        save_day = int(public.readFile(self._save_conf))
        cache.set(skey, save_day, 86400)
        return self.return_msg(save_day)

    def _get_old_certificate_path(self, conf):
        # 以前设置的获取证书路径
        cert_file_reg = r'#smtpd_tls_cert_file\s*=\s*(.*)'
        cert_key_reg = r'#smtpd_tls_key_file\s*=\s*(.*)'
        cert_tmp = re.search(cert_file_reg, conf)
        if cert_tmp:
            cert_file = cert_tmp.groups(1)[0]
            cert_key = re.search(cert_key_reg, conf).groups(1)[0]
        else:
            cert_key = '/etc/pki/dovecot/private/dovecot.pem'
            cert_file = '/etc/pki/dovecot/certs/dovecot.pem'
        return {'cert_key': cert_key, 'cert_file': cert_file}

    def _set_new_certificate_conf(self, conf, cert_file, cert_key):
        """添加新的证书配置,支持多域名不同证书"""
        # 确保SNI映射配置存在
        sni_reg = r'\ntls_server_sni_maps\s*=(.*)'
        if not re.search(sni_reg, conf):
            conf += '\ntls_server_sni_maps = hash:/etc/postfix/vmail_ssl.map\n'

        # 确保使用单独的smtpd_tls_cert_file和smtpd_tls_key_file配置
        # 这些只作为默认证书,当SNI无法匹配时使用
        cert_reg = r'\nsmtpd_tls_cert_file\s*=(.*)'
        key_reg = r'\nsmtpd_tls_key_file\s*=(.*)'

        if re.search(cert_reg, conf):
            conf = re.sub(cert_reg, '\nsmtpd_tls_cert_file = {}'.format(cert_file), conf)
        else:
            conf += '\nsmtpd_tls_cert_file = {}'.format(cert_file)

        if re.search(key_reg, conf):
            conf = re.sub(key_reg, '\nsmtpd_tls_key_file = {}'.format(cert_key), conf)
        else:
            conf += '\nsmtpd_tls_key_file = {}'.format(cert_key)

        # 移除可能存在的chain_files配置,因为它会覆盖SNI
        chain_reg = r'\nsmtpd_tls_chain_files\s*=(.*)'
        if re.search(chain_reg, conf):
            conf = re.sub(chain_reg, '', conf)

        return conf

    def _set_vmail_certificate(self, args, arecord, cert_file, cert_key):
        """设置证书给某个A记录和域名，完善SNI映射"""
        domain = args.domain
        if args.act == 'add':
            vmail_ssl_map = '/etc/postfix/vmail_ssl.map'
            # 读取现有映射文件
            map_content = ""
            if os.path.isfile(vmail_ssl_map):
                map_content = public.readFile(vmail_ssl_map)
                if map_content is None:
                    map_content = ""

            # 构建域名到证书的映射行
            domain_map_line = '{} {} {}\n'.format(domain, cert_key, cert_file)
            arecord_map_line = '{} {} {}\n'.format(arecord, cert_key, cert_file)

            # 如果该域名已存在映射，则更新它
            if re.search(r'^{}.*$'.format(domain), map_content, re.M):
                map_content = re.sub(r'^{}.*$'.format(domain), domain_map_line.strip(), map_content, flags=re.M)
            else:
                map_content += domain_map_line

            # 如果该A记录已存在映射，则更新它
            if re.search(r'^{}.*$'.format(arecord), map_content, re.M):
                map_content = re.sub(r'^{}.*$'.format(arecord), arecord_map_line.strip(), map_content, flags=re.M)
            else:
                map_content += arecord_map_line

            # 写入映射文件
            public.writeFile(vmail_ssl_map, map_content)
            os.system('postmap -F hash:{}'.format(vmail_ssl_map))
        else:
            # 删除操作
            vmail_ssl_map = '/etc/postfix/vmail_ssl.map'
            if os.path.exists(vmail_ssl_map):
                map_content = public.readFile(vmail_ssl_map)
                if map_content:
                    # 移除该域名和A记录的映射行
                    map_content = re.sub(r'^{}.*$\n?'.format(domain), '', map_content, flags=re.M)
                    map_content = re.sub(r'^{}.*$\n?'.format(arecord), '', map_content, flags=re.M)
                    public.writeFile(vmail_ssl_map, map_content)
                    os.system('postmap -F hash:{}'.format(vmail_ssl_map))

    def _set_dovecot_cert_global(self, cert_file, cert_key, conf):
        default_cert_key = r'ssl_key\s*=\s*<\s*/etc/pki/dovecot/private/dovecot.pem'
        default_cert_file = r'ssl_cert\s*=\s*<\s*/etc/pki/dovecot/certs/dovecot.pem'
        if not re.search(default_cert_file, conf):
            return conf
        conf = re.sub(default_cert_file, "ssl_cert = <{}".format(cert_file), conf)
        conf = re.sub(default_cert_key, "ssl_key = <{}".format(cert_key), conf)
        return conf

    # 修改dovecot的ssl配置
    def _set_dovecot_certificate(self, args, a_record, cert_file, cert_key):
        dovecot_version = self.get_dovecot_version()['data']
        ssl_file = "/etc/dovecot/conf.d/10-ssl.conf"
        ssl_conf = public.readFile(ssl_file)
        if not ssl_conf:
            return public.returnMsg(False,
                                    "找不到dovecot配置文件 {}".format(ssl_file))
        # 2.3版本的dovecot要加上ssl_dh配置
        if dovecot_version.startswith('2.3'):
            if args.act == 'add':
                if not os.path.exists('/etc/dovecot/dh.pem') or os.path.getsize('/etc/dovecot/dh.pem') < 300:
                    public.ExecShell('openssl dhparam 2048 > /etc/dovecot/dh.pem')
                if 'ssl_dh = </etc/dovecot/dh.pem' not in ssl_conf:
                    ssl_conf = ssl_conf + "\nssl_dh = </etc/dovecot/dh.pem"
        # 将自签证书替换为用户设置的证书
        reg_cert = r'local_name\s+{}'.format(a_record)
        if args.act == 'add' and not re.search(reg_cert, ssl_conf):
            ssl_conf = self._set_dovecot_cert_global(cert_file, cert_key, ssl_conf)
            domain_ssl_conf = """
#DOMAIN_SSL_BEGIN_%s
local_name %s {
    ssl_cert = < %s
    ssl_key = < %s
}
#DOMAIN_SSL_END_%s""" % (a_record, a_record, cert_file, cert_key, a_record)
            reg = r'ssl\s*=\s*yes'
            ssl_conf = re.sub(reg, 'ssl = yes' + domain_ssl_conf, ssl_conf)
        if args.act == 'delete':
            reg = '#DOMAIN_SSL_BEGIN_{a}(.|\n)+#DOMAIN_SSL_END_{a}\n'.format(a=a_record)
            ssl_conf = re.sub(reg, '', ssl_conf)

        public.writeFile(ssl_file, ssl_conf)
        public.ExecShell('systemctl restart dovecot')

    def _verify_certificate(self, args, path, csrpath, keypath):
        # 验证并写入证书
        # path = '{}/cert/{}/'.format(self.__setupPath, args.domain)
        # csrpath = path + "fullchain.pem"
        # keypath = path + "privkey.pem"
        backup_cert = '/tmp/backup_cert_mail_sys'
        if hasattr(args, "act") and args.act == "add":
            if args.key.find('KEY') == -1:
                return public.returnMsg(False, '私钥错误，请检查!')
            if args.csr.find('CERTIFICATE') == -1:
                return public.returnMsg(False, '证书错误，请检查!')
            public.writeFile('/tmp/mail_cert.pl', str(args.csr))
            if not public.CheckCert('/tmp/mail_cert.pl'):
                return public.returnMsg(False, '证书错误，请以pem格式粘贴正确的证书!')
            if os.path.exists(backup_cert): shutil.rmtree(backup_cert)
            if os.path.exists(path): shutil.move(path, backup_cert)
            if os.path.exists(path): shutil.rmtree(path)
            os.makedirs(path)
            public.writeFile(keypath, args.key)
            os.chown(keypath, 0, 0)
            os.chmod(keypath, 0o600)
            public.writeFile(csrpath, args.csr)
            os.chown(csrpath, 0, 0)
            os.chmod(csrpath, 0o600)
        # else:
        #     if os.path.exists(csrpath):
        #         public.ExecShell('rm -rf {}'.format(path))

    def _check_postfix_conf(self):
        result = public.process_exists('master', '/usr/libexec/postfix/master')
        if "ubuntu" in self.sys_v:
            result = public.process_exists('master', '/usr/lib/postfix/sbin/master')
        return result

    def _get_ubuntu_version(self):
        return public.readFile('/etc/issue').strip().split("\n")[0].replace('\\n', '').replace(r'\l',
                                                                                               '').strip().lower()

    def _modify_old_ssl_perameter(self, conf):
        if not os.path.exists('/etc/postfix/vmail_ssl.map'):
            # 注释以前的证书设置
            if '#smtpd_tls_cert_file' not in conf:
                conf = conf.replace('smtpd_tls_cert_file', '#smtpd_tls_cert_file')
                conf = conf.replace('smtpd_tls_key_file', '#smtpd_tls_key_file')
            # 以前设置的获取证书路径
            old_cert_info = self._get_old_certificate_path(conf)
            # 设置新的证书配置和默认TLS配置
            if 'tls_server_sni_maps' not in conf:
                conf = self._set_new_certificate_conf(conf, old_cert_info['cert_file'], old_cert_info['cert_key'])
        public.writeFile(self.postfix_main_cf, conf)

    def _fix_default_cert(self, conf, cert_file, cert_key):
        reg = r'smtpd_tls_chain_files\s*=(.*)'
        tmp = re.search(reg, conf)
        if not tmp:
            return conf
        tmp = tmp.groups()[0]
        if len(tmp) < 5 or 'dovecot.pem' in conf:
            conf = self._set_new_certificate_conf(conf, cert_file, cert_key)
        return conf

    def _set_master_ssl(self):
        master_file = "/etc/postfix/master.cf"
        master_conf = public.readFile(master_file)
        master_rep = r"\n*#\s*-o\s+smtpd_tls_auth_only=yes"
        master_str = "\n  -o smtpd_tls_auth_only=yes"
        master_rep1 = r"\n*#\s*-o\s+smtpd_tls_wrappermode=yes"
        master_str1 = "\n  -o smtpd_tls_wrappermode=yes"
        master_conf = re.sub(master_rep, master_str, master_conf)
        master_conf = re.sub(master_rep1, master_str1, master_conf)
        public.writeFile(master_file, master_conf)

    def set_mail_certificate_multiple(self, args):
        '''
        :param args: domain 要设置证书的域名
        :param args: csr
        :param args: key
        :param args: act add/delete
        :return:
        '''
        #         if not os.path.exists('/etc/redhat-release') and 'debian gnu/linux 10' not in self._get_ubuntu_version():
        #             if 'ubuntu 2' not in self._get_ubuntu_version():
        #                 if args.act == 'add':
        #                     args.act = "1"
        #                 else:
        #                     args.act = "0"
        #                 pstr = """
        # {postconf} -e "smtpd_tls_cert_file = /etc/pki/dovecot/certs/dovecot.pem"
        # {postconf} -e "smtpd_tls_key_file = /etc/pki/dovecot/private/dovecot.pem"
        #     """.format(postconf=self.get_postconf())
        #                 public.ExecShell(pstr)
        #                 return self.set_ssl(args)
        conf = public.readFile(self.postfix_main_cf)
        domain = args.domain
        cert_path = '/www/server/panel/plugin/mail_sys/cert/{}'.format(domain)
        cert_file = "{}/fullchain.pem".format(cert_path)
        cert_key = "{}/privkey.pem".format(cert_path)
        if not os.path.exists(cert_path):
            os.makedirs(cert_path)
        # 备份配置文件
        self.back_file(self.postfix_main_cf)
        # 在main注释smtpd_tls_cert_file，smtpd_tls_key_file参数
        # 添加smtpd_tls_chain_files和tls_server_sni_maps，3.4+支持
        conf = self._fix_default_cert(conf, cert_file, cert_key)
        self._modify_old_ssl_perameter(conf)
        # 修改master.cf开启tls/ssl
        self._set_master_ssl()
        # 获取域名的A记录
        arecord = self.M('domain').where('domain=?', domain).field('a_record').find()['a_record']
        if arecord == '':
            return self.return_msg(public.returnMsg(False, '所设置的域名不存在'))
        # 验证域名证书是否有效
        if args.csr != '':
            verify_result = self._verify_certificate(args, cert_path, cert_file, cert_key)
            if verify_result:
                return self.return_msg(verify_result)
        # 将证书配置到vmail_ssl.map
        self._set_vmail_certificate(args, arecord, cert_file, cert_key)
        self._set_dovecot_certificate(args, arecord, cert_file, cert_key)
        # if args.act == 'delete':
        #     pem = "{}/cert/{}/fullchain.pem".format(self.__setupPath,domain)
        #     key = "{}/cert/{}/privkey.pem".format(self.__setupPath,domain)
        #     if os.path.exists(pem):
        #         os.remove(pem)
        #     if os.path.exists(key):
        #         os.remove(key)
        public.ExecShell('postmap -F hash:/etc/postfix/vmail_ssl.map && systemctl restart postfix')
        if not self._check_postfix_conf():
            self.restore_file(self.postfix_main_cf)
            return self.return_msg(public.returnMsg(False, '设置失败，恢复配置文件'))
        return self.return_msg(public.returnMsg(True, '设置成功'))

    # # 取证书内容 兼容老版本  弃用
    # def get_multiple_certificate(self, domain):
    #     """
    #         @name 获取某个域名的证书内容
    #         @author zhwen<zhw@aapanel.com>
    #         @param domain 需要获取的域名
    #     """
    #     # domain = args.domain
    #     path = '{}/cert/{}/'.format(self.__setupPath, domain)
    #     if not os.path.exists('/etc/redhat-release') and 'debian gnu/linux 10' not in self._get_ubuntu_version():
    #         if 'ubuntu 2' not in self._get_ubuntu_version():
    #             path = '/www/server/panel/plugin/mail_sys/cert/'
    #     csrpath = path + "fullchain.pem"
    #     keypath = path + "privkey.pem"
    #     if not os.path.exists(csrpath):
    #         return {'csr': '', 'key': ''}
    #         # return public.returnMsg(False, 'SSL has not been set up for this domain')
    #     csr = public.readFile(csrpath)
    #     key = public.readFile(keypath)
    #     data = {'csr': csr, 'key': key}
    #     return data

    # 检查ssl状态
    def _get_multiple_certificate_domain_status(self, domain):
        path = '/www/server/panel/plugin/mail_sys/cert/{}/fullchain.pem'.format(domain)
        ssl_conf = public.readFile('/etc/postfix/vmail_ssl.map')
        # if not os.path.exists('/etc/redhat-release') and 'debian gnu/linux 10' not in self._get_ubuntu_version():
        #     if 'ubuntu 2' not in self._get_ubuntu_version():
        #         path = '/www/server/panel/plugin/mail_sys/cert/fullchain.pem'
        if not os.path.exists(path):
            return False
        if not ssl_conf or domain not in ssl_conf:
            return False
        return True

    # 备份配置文件
    def back_file(self, file, act=None):
        """
            @name 备份配置文件
            @author zhwen<zhw@bt.cn>
            @param file 需要备份的文件
            @param act 如果存在，则备份一份作为默认配置
        """
        file_type = "_bak"
        if act:
            file_type = "_def"
        public.ExecShell("/usr/bin/cp -p {0} {1}".format(
            file, file + file_type))

    # 还原配置文件
    def restore_file(self, file, act=None):
        """
            @name 还原配置文件
            @author zhwen<zhw@bt.cn>
            @param file 需要还原的文件
            @param act 如果存在，则还原默认配置
        """
        file_type = "_bak"
        if act:
            file_type = "_def"
        public.ExecShell("/usr/bin/cp -p {1} {0}".format(
            file, file + file_type))

    def enable_catchall(self, args):
        """
        设置邮局捕获所有/不存在的用户并转发到指定邮箱
        @param args.domain: 需要捕获的域名
        @param args.email: 转发到的邮箱
        @param args.catch_type: 捕获类型 all/none 全部/不存在的用户 默认none
        @return:
        """
        if not self.check_main_forward_conf():
            return self.return_msg(public.returnMsg(False, 'main.cf配置失败'))

        domain = '@' + args.domain.strip()
        email = args.email.strip()

        self._deledte_catchall(args.domain)
        create_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        if email:
            if args.catch_type == 'all':
                domain = '%' + domain
            self.M('alias').add('address,goto,domain,created,modified,active',
                                (domain, email, args.domain.strip(), create_time, create_time, '1'))
        return self.return_msg(public.returnMsg(True, '设置成功'))
    def _add_enable_catchall(self, args):
        """
        设置邮局捕获所有/不存在的用户并转发到指定邮箱
        @param args.domain: 需要捕获的域名
        @param args.email: 转发到的邮箱
        @param args.catch_type: 捕获类型 all/none 全部/不存在的用户 默认none
        @return:
        """
        domain = '@' + args.domain.strip()
        email = args.email.strip()
        catch_type = args.catch_type
        if catch_type == 'all':
            domain = '%' + domain

        create_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.M('alias').add('address,goto,domain,created,modified,active',
                            (domain, email, args.domain.strip(), create_time, create_time, '1'))
        self.check_main_forward_conf()
        return True

    def check_main_forward_conf(self):
        """
        检查main.cf配置文件中的virtual_alias_maps配置
        @return:
        """
        conf = public.readFile(self.postfix_main_cf)
        if not conf:
            return False
        virtual_alias_maps = 'virtual_alias_maps = sqlite:/etc/postfix/sqlite_virtual_alias_maps.cf, sqlite:/etc/postfix/sqlite_virtual_alias_domain_maps.cf, sqlite:/etc/postfix/sqlite_virtual_alias_domain_catchall_maps.cf,sqlite:/etc/postfix/bt_catchnone_maps.cf'
        if virtual_alias_maps in conf:
            return True
        else:
            try:
                if 'virtual_alias_maps' in conf:
                    conf = re.sub(r'virtual_alias_maps\s*=.*', virtual_alias_maps, conf)
                else:
                    conf += '\n'+virtual_alias_maps+'\n'
                public.writeFile(self.postfix_main_cf, conf)
                public.ExecShell('systemctl restart postfix')
                return True
            except:
                public.print_log(public.get_error_info())
                return False

    def _get_catchall_status(self, domain):
        """
        获取某个域名下的catchall开启状态和类型
        @param domain:
        @return:
        """
        conf = public.readFile(self.postfix_main_cf)
        if not conf:
            return False, '', ''
        domain = '@' + domain.strip()
        result = self.M('alias').where('(address=? or address=?) and active=1', (domain, "%"+domain)).select()
        if result:
            goto = ''
            for i in result:
                goto = i['goto']
                if '%' in i['address']:
                    return True, 'all', goto
            return True, 'none', goto
        return False, '', ''

    def get_junk_mails(self, args):
        '''
        获取垃圾邮件列表
        :param args:
        :return:
        '''
        import email
        from mailModel import receive_mail
        reload(receive_mail)

        if 'username' not in args:
            return self.return_msg(public.returnMsg(False, '请传入账号名'))
        username = args.username
        if '@' not in username:
            return self.return_msg(public.returnMsg(False, '账号名不合法'))
        local_part, domain = username.split('@')
        if 'p' not in args:
            args.p = 1
        if 'p=' in args.p:
            args.p = args.p.replace('p=', '')

        receive_mail_client = receive_mail.ReceiveMail()
        mail_list = []
        try:
            dir_path = '/www/vmail/{0}/{1}/.Junk/cur'.format(domain, local_part)
            if os.path.isdir(dir_path):
                # 先将new文件夹的邮件移动到cur文件夹
                new_path = '/www/vmail/{0}/{1}/.Junk/new'.format(domain, local_part)
                if os.path.isdir(new_path):
                    for file in os.listdir(new_path):
                        src = os.path.join(new_path, file)
                        dst = os.path.join(dir_path, file)
                        shutil.move(src, dst)
                files = []
                for fname in os.listdir(dir_path):
                    mail_file = os.path.join(dir_path, fname)
                    if not os.path.exists(mail_file): continue
                    f_info = {}
                    f_info['name'] = fname
                    f_info['mtime'] = os.path.getmtime(mail_file)
                    save_day = self.get_save_day(None)['data']
                    if save_day > 0:
                        deltime = int(time.time()) - save_day * 86400
                        if int(f_info['mtime']) < deltime:
                            os.remove(mail_file)
                            continue
                    files.append(f_info)
                files = sorted(files, key=lambda x: x['mtime'], reverse=True)
                page_data = public.get_page(len(files), int(args.p), 10)
                # 替换掉 href标签里的多余信息 只保留页码
                # pattern =r"href='(/v2)?/plugin.*?\?p=(\d+)'"
                pattern = r"href='(?:/v2)?/plugin.*?\?p=(\d+)'"
                # 使用re.sub进行替换
                page_data['page'] = re.sub(pattern, r"href='\1'", page_data['page'])
                shift = int(page_data['shift'])
                row = int(page_data['row'])
                files = files[shift:shift + row]
                for d in files:
                    mail_file = os.path.join(dir_path, d['name'])
                    try:
                        mailInfo = receive_mail_client.getMailInfo(public.readFile(mail_file))
                        mailInfo['path'] = mail_file
                        mail_list.append(mailInfo)
                    except:
                        public.print_log(public.get_error_info())
                        continue
                return self.return_msg({
                    'status':
                        True,
                    'data':
                        mail_list,
                    'page':
                        page_data['page']
                })
            else:
                page_data = public.get_page(0, int(args.p), 10)
                return self.return_msg({
                    'status':
                        True,
                    'data':
                        mail_list,
                    'page':
                        page_data['page']
                })
        except Exception as e:
            print(public.get_error_info())
            return self.return_msg(public.returnMsg(False, '获取失败,错误原因[{0}]'.format(str(e))))

    def move_to_junk(self, get):
        '''
        将收件箱的邮件标记为垃圾邮件
        :param get:
        :return:
        '''
        if 'username' not in get:
            return self.return_msg(public.returnMsg(False, '请传入账号名'))
        username = get.username
        if '@' not in username:
            return self.return_msg(public.returnMsg(False, '账号名不合法'))
        local_part, domain = username.split('@')

        src = get.path.strip()

        if not os.path.exists('/www/vmail/{0}/{1}/.Junk'.format(domain, local_part)):
            data = self.M('mailbox').where('username=?', username).field('password_encode,full_name').find()
            password = self._decode(data['password_encode'])
            self.create_mail_box(username, password)
        if not os.path.exists(src):
            return self.return_msg(public.returnMsg(False, '邮件路径不存在'))
        dir_path = '/www/vmail/{0}/{1}/.Junk/cur'.format(domain, local_part)
        dst = os.path.join(dir_path, os.path.basename(src))
        shutil.move(src, dst)
        return self.return_msg(public.returnMsg(True, '标记成功'))

    def move_out_junk(self, get):
        '''
        将垃圾箱的邮件移动到收件箱
        :param get:
        :return:
        '''
        if 'username' not in get:
            return self.return_msg(public.returnMsg(False, '请传入账号名'))
        username = get.username
        if '@' not in username:
            return self.return_msg(public.returnMsg(False, '账号名不合法'))
        local_part, domain = username.split('@')

        src = get.path.strip()
        if not os.path.exists(src):
            return self.return_msg(public.returnMsg(False, '邮件路径不存在'))
        dir_path = '/www/vmail/{0}/{1}/cur'.format(domain, local_part)
        dst = os.path.join(dir_path, os.path.basename(src))
        shutil.move(src, dst)
        return self.return_msg(public.returnMsg(True, '操作成功'))

    # 获取SSL证书时间到期时间
    def get_ssl_info(self, domain):

        try:
            import data
            fullchain_file = '/www/server/panel/plugin/mail_sys/cert/{}/fullchain.pem'.format(domain)
            privkey_file = '/www/server/panel/plugin/mail_sys/cert/{}/privkey.pem'.format(domain)
            if not os.path.exists(fullchain_file) or not os.path.exists(privkey_file):
                return {'dns': [domain]}
            os.chown(fullchain_file, 0, 0)
            os.chmod(fullchain_file, 0o600)
            os.chown(privkey_file, 0, 0)
            os.chmod(privkey_file, 0o600)

            ssl_info = data.data().get_cert_end(fullchain_file)
            if not ssl_info:
                return {'dns': [domain]}
            ssl_info['src'] = public.readFile(fullchain_file)
            ssl_info['key'] = public.readFile(privkey_file)
            ssl_info['endtime'] = int(
                int(time.mktime(time.strptime(ssl_info['notAfter'], "%Y-%m-%d")) - time.time()) / 86400)
            return ssl_info
        except Exception as ex:
            public.print_log(public.get_error_info())
            return {'dns': [domain]}

    # 仅支持dns申请
    # 申请证书
    def apply_cert(self, args):
        """
        domains 邮箱域名 ['example.com']
        auth_to CloudFlareDns|email|token 当auth_to 为 dns时是需要手动添加解析
        auto_wildcard = 1
        auth_type = dns
        :param args:
        :return:
        """
        import acme_v2
        domains = json.loads(args.domains)
        apply_cert_module = acme_v2.acme_v2()
        apply_cert = apply_cert_module.apply_cert(domains, 'dns', args.auth_to, auto_wildcard=1)
        return self.return_msg(apply_cert)

    # 手动验证dns
    def apply_cert_manual(self, args):
        """
        index
        :param args:
        :return:
        """
        import acme_v2
        apply_cert_module = acme_v2.acme_v2()
        return self.return_msg(apply_cert_module.apply_cert([], 'dns', 'dns', index=args.index))

    def check_rspamd_route(self, args):
        panel_init = public.readFile("/www/server/panel/BTPanel/__init__.py")
        if "proxy_rspamd_requests" in panel_init:
            return self.return_msg(public.returnMsg(True, ""))
        return self.return_msg(public.returnMsg(False, ""))

    @staticmethod
    def change_hostname(args):
        hostname = args.hostname
        rep_domain = r"^(?=^.{3,255}$)[a-zA-Z0-9\_\-][a-zA-Z0-9\_\-]{0,62}(\.[a-zA-Z0-9\_\-][a-zA-Z0-9\_\-]{0,62})+$"
        if not re.search(rep_domain, hostname):
            return self.return_msg(public.returnMsg(False, "请输入完整域名，例如 mail.bt.com),"))
        public.ExecShell('hostnamectl set-hostname --static {}'.format(hostname))
        h = socket.gethostname()
        if h == hostname:
            return self.return_msg(public.returnMsg(True, "设置成功！"))
        return self.return_msg(public.returnMsg(False, "设置失败！"))

    def check_init_result(self, args):
        """
        检查安装结果：
        服务状态
        配置文件完整性
        :return:
        """
        result = dict()
        result['missing_file'] = self.check_confile_completeness()
        result['service_status'] = self.get_service_status()
        return self.return_msg(result)

    def check_confile_completeness(self):
        file_list = public.readFile("{}/services_file.txt".format(self.__setupPath))
        if not file_list:
            return ["%s/services_file.txt|{download_conf_url}/mail_sys" % self.__setupPath]
        file_list = [i for i in file_list.split()]
        missing_files = []
        for file in file_list:
            tmp = public.readFile(file.split('|')[0])
            if not tmp:
                missing_files.append(file)
        return missing_files

    @staticmethod
    def get_init_log(args=None):
        """
        获取初始化日志
        :param args:
        :return:
        """
        logfile = '/tmp/mail_init.log'
        return self.return_msg(public.returnMsg(True, public.GetNumLines(logfile, 50)))

    @staticmethod
    def check_smtp_port(args):
        """
        检查服务器能否连接其他服务的25端口
        :param args:
        :return:
        """
        domain = args.domain
        rep_domain = r"^(?=^.{3,255}$)[a-zA-Z0-9\_\-][a-zA-Z0-9\_\-]{0,62}(\.[a-zA-Z0-9\_\-][a-zA-Z0-9\_\-]{0,62})+$"
        if not re.search(rep_domain, domain):
            return self.return_msg(public.returnMsg(False, "请输入完整域名，例如 smtp.qq.com)"))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((domain, 25))
        if result == 0:
            return self.return_msg(public.returnMsg(True, "25端口通信正常"))
        return self.return_msg(public.returnMsg(False, "25端口通信失败，请联系你的主机提供商进行放行"))

    def download_file(self, args):
        filename = args.filename
        tmp = filename.split('|')
        local_file = tmp[0]
        remote_file = tmp[1].format(download_conf_url="http://node.aapanel.com")
        data = public.readFile("/www/server/panel/plugin/mail_sys/services_file.txt")
        if not data:
            return self.return_msg(public.returnMsg(False, "Get source file error!"))
        if remote_file not in data or local_file not in data:
            return self.return_msg(public.returnMsg(False, "There is no such file!"))
        public.ExecShell(
            "wget {remote_file} -O {local_file} -T 10 --no-check-certificate".format(remote_file=remote_file,
                                                                                     local_file=local_file))
        return self.return_msg(public.returnMsg(True, "重新下载成功！"))

    # 邮局-定期，一键检查域名是否被列入垃圾域名    一键检测  刷新检测    定时任务

    # 获取域名是否被列入垃圾域名
    def check_domains_blacklist(self):
        '''
        获取域名是否被列入垃圾域名
        :param
        :return:  dict
        domains_info = {
            'kern123.top':{
                "is_blacklist": False,  # 无黑名单记录
                "blacklist": [],
            },
            'moyumao.top': {
                "is_blacklist": True,   # 有黑名单记录
                "blacklist": ['dnsbl.sorbs.net'],
            },
         }
        '''

        data_list = self.M('domain').order('created desc').field('domain').select()
        domain_list = [item['domain'] for item in data_list]
        domains_info = {}
        cache_key_template = "{}_checkBlacklist"

        for domain in domain_list:
            cache_key = cache_key_template.format(domain)
            cached_result = cache.get(cache_key)
            if cached_result is None:
                cached_result = {"is_blacklist": False, "blacklist": []}
                blacklist_info = self._check_spam_blacklist(domain)
                cached_result.update(blacklist_info)
                cache.set(cache_key, cached_result, 86400)
            domains_info[domain] = cached_result

        return domains_info

    def check_domain_blacklist(self, domain):
        '''
        获取域名是否被列入垃圾域名
        :param
        :return:  dict
        domain_info = {
                "is_blacklist": False,  # 无黑名单记录
                "blacklist": [],
            }
        '''

        cache_key = "{}_checkBlacklist".format(domain)
        cached_result = cache.get(cache_key)
        # 如果缓存中没有结果，进行查询并设置缓存
        if cached_result is None:
            cached_result = self._check_spam_blacklist(domain)
            cache.set(cache_key, cached_result, 86400)
        return cached_result

    # 检测邮箱域名是否被列入垃圾域名(无变化缓存1天  刷新检测重新检测内容)
    def _check_spam_blacklist(self, domain):
        # 常见的DNSBL服务列表，可以根据需要添加更多
        blacklist_services = [
            "zen.spamhaus.org",
            "bl.spamcop.net",
            "dnsbl.sorbs.net",
            "multi.surbl.org",
            "bl.spamcop.net",
            "http.dnsbl.sorbs.net",
            "misc.dnsbl.sorbs.net",
            "socks.dnsbl.sorbs.net",
            "web.dnsbl.sorbs.net",
            "rbl.spamlab.com",
            "cbl.anti - spam.org.cn",
            "httpbl.abuse.ch",
            "virbl.bit.nl",
            "dsn.rfc - ignorant.org",
            "opm.tornevall.org",
            "multi.surbl.org",
            "relays.mail - abuse.org",
            "rbl - plus.mail - abuse.org",
            "rbl.interserver.net",
            "dul.dnsbl.sorbs.net",
            "smtp.dnsbl.sorbs.net",
            "spam.dnsbl.sorbs.net",
            "zombie.dnsbl.sorbs.net",
            "drone.abuse.ch",
            "rbl.suresupport.com",
            "spamguard.leadmon.net",
            "netblock.pedantic.org",
            "blackholes.mail - abuse.org",
            "dnsbl.dronebl.org",
            "query.senderbase.org",
            "csi.cloudmark.com",
            "0spam - killlist.fusionzero.com",
            "0spam.fusionzero.com",
            "access.redhawk.org",
            "all.rbl.jp",
            "all.spam - rbl.fr",
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
            "blackholes.five - ten - sg.com",
            "blacklist.sci.kun.nl",
            "blacklist.woody.ch",
            "bogons.cymru.com",
            "bsb.empty.us",
            "bsb.spamlookup.net",
            "cart00ney.surriel.com",
            "cbl.abuseat.org",
            "cbl.anti - spam.org.cn",
            "cblless.anti - spam.org.cn",
            "cblplus.anti - spam.org.cn",
            "cdl.anti - spam.org.cn",
            "cidr.bl.mcafee.com",
            "combined.rbl.msrbl.net",
            "db.wpbl.info",
            "dev.null.dk",
            "dialups.visi.com",
            "dnsbl - 0.uceprotect.net",
            "dnsbl - 1.uceprotect.net",
            "dnsbl - 2.uceprotect.net",
            "dnsbl - 3.uceprotect.net",
            "dnsbl.anticaptcha.net",
            "dnsbl.aspnet.hu",
            "dnsbl.inps.de",
            "dnsbl.justspam.org",
            "dnsbl.kempt.net",
            "dnsbl.madavi.de",
            "dnsbl.rizon.net",
            "dnsbl.rv - soft.info",
            "dnsbl.rymsho.ru",
            "dnsbl.sorbs.net",
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
            "mail - abuse.blacklist.jippg.org",
            "netbl.spameatingmonkey.net",
            "netscan.rbl.blockedservers.com",
            "no - more - funn.moensted.dk",
            "noptr.spamrats.com",
            "orvedb.aupads.org",
            "pbl.spamhaus.org",
            "phishing.rbl.msrbl.net",
            "pofon.foobar.hu",
            "psbl.surriel.com",
            "rbl.abuse.ro",
            "rbl.blockedservers.com",
            "rbl.dns - servicios.com",
            "rbl.efnet.org",
            "rbl.efnetrbl.org",
            "rbl.iprange.net",
            "rbl.schulte.org",
            "rbl.talkactive.net",
            "rbl2.triumf.ca",
            "rsbl.aupads.org",
            "sbl - xbl.spamhaus.org",
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
        is_blacklist = False
        blacklist = []
        for service in blacklist_services:
            try:
                # 构造DNS查询，A记录通常用来表示域名是否在黑名单中
                query_domain = domain + "." + service
                response = dns.resolver.resolve(query_domain, "A")

                # 如果有响应，说明域名在黑名单中
                if response:
                    is_blacklist = True
                    blacklist.append(service)

            except Exception as e:
                pass
                # print(f"查询 {service} 时发生错误: {e}")

        data = {
            "is_blacklist": is_blacklist,
            "blacklist": blacklist,
        }

        return data

    # 获取监控任务状态
    def get_service_monitor_status(self, get):
        c_id = public.M('crontab').where('name=?', u'[勿删] 邮局服务监控').getField('id')
        if not c_id: return self.return_msg(public.returnMsg(False, '任务不存在!'))
        data = public.M('crontab').where('name=?', u'[勿删] 邮局服务监控').find()
        return self.return_msg(public.returnMsg(True, data))

    # 创建监控任务
    def create_service_monitor_task(self, get):
        import crontab
        p = crontab.crontab()

        try:

            c_id = public.M('crontab').where('name=?', u'[勿删] 邮局服务监控').getField('id')
            if c_id:
                data = {}
                data['id'] = c_id
                data['name'] = u'[勿删] 邮局服务监控'
                # data['type'] = get.type
                # data['where1'] = get.where1 if 'where1' in get else ''
                data['type'] = 'minute-n'
                data['where1'] = '1'
                data['sBody'] = 'btpython /www/server/panel/class/mailModel/script/monitor_script.py'
                data['backupTo'] = ''
                data['sType'] = 'toShell'
                # data['hour'] = get.hour if 'hour' in get else ''
                # data['minute'] = get.minute if 'minute' in get else ''
                # data['week'] = get.week if 'week' in get else ''
                data['hour'] = ''
                data['minute'] = ''
                data['week'] = ''
                data['sName'] = ''
                data['urladdress'] = ''
                data['save'] = ''
                p.modify_crond(data)
                return self.return_msg(public.returnMsg(True, '编辑成功!'))
            else:
                data = {}
                data['name'] = u'[勿删] 邮局服务监控'
                # data['type'] = get.type
                # data['where1'] = get.where1 if 'where1' in get else ''
                data['type'] = 'minute-n'
                data['where1'] = '1'
                data['sBody'] = 'btpython /www/server/panel/class/mailModel/script/monitor_script.py'
                data['backupTo'] = ''
                data['sType'] = 'toShell'
                # data['hour'] = get.hour if 'hour' in get else ''
                # data['minute'] = get.minute if 'minute' in get else ''
                # data['week'] = get.week if 'week' in get else ''
                data['hour'] = ''
                data['minute'] = ''
                data['week'] = ''
                data['sName'] = ''
                data['urladdress'] = ''
                data['save'] = ''
                p.AddCrontab(data)
                return self.return_msg(public.returnMsg(True, '设置成功!'))
        except Exception as e:
            public.print_log(public.get_error_info())

    # 打开服务状态监测任务 弃用
    def open_service_monitor_task(self, get):
        import crontab
        p = crontab.crontab()

        try:

            c_id = public.M('crontab').where('name=?', u'[勿删] 邮局服务监控').getField('id')
            if c_id:
                data = {}
                data['id'] = c_id
                data['name'] = u'[勿删] 邮局服务监控'
                # data['type'] = get.type
                # data['where1'] = get.where1 if 'where1' in get else ''
                data['type'] = 'minute-n'
                data['where1'] = '1'
                data['sBody'] = 'btpython /www/server/panel/class/mailModel/script/monitor_script.py'
                data['backupTo'] = ''
                data['sType'] = 'toShell'
                # data['hour'] = get.hour if 'hour' in get else ''
                # data['minute'] = get.minute if 'minute' in get else ''
                # data['week'] = get.week if 'week' in get else ''
                data['hour'] = ''
                data['minute'] = ''
                data['week'] = ''
                data['sName'] = ''
                data['urladdress'] = ''
                data['save'] = ''
                p.modify_crond(data)
                return public.returnMsg(True, public.lang('修改成功!'))
            else:
                data = {}
                data['name'] = u'[勿删] 邮局服务监控'
                # data['type'] = get.type
                # data['where1'] = get.where1 if 'where1' in get else ''
                data['type'] = 'minute-n'
                data['where1'] = '1'
                data['sBody'] = 'btpython /www/server/panel/class/mailModel/script/monitor_script.py'
                data['backupTo'] = ''
                data['sType'] = 'toShell'
                # data['hour'] = get.hour if 'hour' in get else ''
                # data['minute'] = get.minute if 'minute' in get else ''
                # data['week'] = get.week if 'week' in get else ''
                data['hour'] = ''
                data['minute'] = ''
                data['week'] = ''
                data['sName'] = ''
                data['urladdress'] = ''
                data['save'] = ''
                p.AddCrontab(data)
                return public.returnMsg(True, public.lang('设置成功!'))
        except Exception as e:
            public.print_log(public.get_error_info())

    # 关闭服务状态监控任务 弃用
    def close_service_monitor_task(self, get):
        import crontab

        p = crontab.crontab()
        c_id = public.M('crontab').where('name=?', u'[勿删] 邮局服务监控').getField('id')
        if not c_id: return self.return_msg(public.returnMsg(False, '任务不存在!'))
        args = {"id": c_id}
        p.DelCrontab(args)
        return self.return_msg(public.returnMsg(True, '关闭成功!'))

    # 导出用户
    def export_users(self, get):

        rule_path = '/www/server/panel/data/mail/'
        if not os.path.exists(rule_path):
            os.makedirs(rule_path, exist_ok=True)

        file_name = "All_users_{}".format(int(time.time()))
        # domain = get.get('domain/s', '')
        query = self.M('mailbox').order('created desc').field(
            'full_name,is_admin,username,password,password_encode,maildir,quota,local_part,domain')

        if hasattr(get, 'domain') and get.get('domain/s', '') != '':
            domain = get.get('domain/s', '')
            # 导出某域名
            file_name = "{}_users_{}".format(domain, int(time.time()))
            query = self.M('mailbox').where('domain=?', domain).order('created desc').field(
                'full_name,is_admin,username,password,password_encode,maildir,quota,local_part,domain')

        data_list = query.select()

        if not data_list:
            return self.return_msg(public.returnMsg(False, '没有用户可以导出'))

        file_path = "{}{}.json".format(rule_path, file_name)
        public.writeFile(file_path, public.GetJson(data_list))

        return self.return_msg(public.returnMsg(True, file_path))

    # 导入用户
    def import_users(self, get):

        get.file = get.get('file/s', '')

        if not get.file:
            return self.return_msg(public.returnMsg(False, '文件不能为空'))

        if not os.path.exists(get.file):
            return self.return_msg(self.return_msg(public.returnMsg(False, '文件不存在')))

        try:
            data = public.readFile(get.file)
            data = json.loads(data)
            data.reverse()
        except:
            return self.return_msg(public.returnMsg(False, '文件内容有误或格式不正确'))
        # public.print_log("获取文件---{}".format(data))

        create_successfully = {}
        create_failed = {}

        args = public.dict_obj()
        for item in data:

            if not item:
                continue
            if not item['username'] or not item['password']:
                continue

            try:
                # 添加用户 筛选掉域名不一致的  空密码的  添加 调用批量添加 可筛选出域名不存在  账号名已存在的账号
                args.full_name = item['full_name']
                args.is_admin = item['is_admin']
                args.username = item['username']
                args.password_encrypt = item['password']  # 处理后的
                args.password_encode = item['password_encode']
                args.maildir = item['maildir']
                args.quota = item['quota']
                args.local_part = item['local_part']
                args.domain = item['domain']
                result = self._add_mailbox2(args)
                if result['status']:
                    create_successfully[item['username']] = result['msg']
                    continue
                create_failed[item['username']] = result['msg']
            except Exception as ex:
                public.print_log(traceback.format_exc())
                create_failed[item['username']] = "create error {}".format(ex)

        return self.return_msg({'status': True, 'msg': "导入邮箱[{}]成功".format(','.join(create_successfully)),
                'error': create_failed,
                'success': create_successfully})

    # 添加导入的用户
    def _add_mailbox2(self, args):
        '''
        新增邮箱用户  取消存储空间字节转换   取消密码加密(存的就是加密的)
        :param args:
        :return:
        '''

        username = args.username
        # if not self._check_email_address(username):
        #     return public.returnMsg(False, public.lang('Email address format is incorrect'))
        if not username.islower():
            return public.returnMsg(False, '电子邮件地址不能有大写字母!')
        is_admin = args.is_admin if 'is_admin' in args else 0

        local_part, domain = username.split('@')
        # 检查邮箱数量  查看数量限制
        user_count = self.M('mailbox').where('domain=?', (args.domain,)).count()
        domaincount = self.M('domain').where('domain=?', (args.domain,)).getField("mailboxes")
        if user_count + 1 > domaincount:
            return public.returnMsg(False,'{}的邮箱数量已达到限制{}'.format(args.domain, domaincount))

        domain_list = [item['domain'] for item in self.M('domain').field('domain').select()]
        if domain not in domain_list:
            return public.returnMsg(False, '不存在该域名 {}'.format(domain))

        count = self.M('mailbox').where('username=?', (username,)).count()
        if count > 0:
            return public.returnMsg(False, 'EMAIL_EXIST')

        cur_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.M('mailbox').add(
            'full_name,is_admin,username,password,password_encode,maildir,quota,local_part,domain,created,modified',
            (args.full_name, is_admin, username, args.password_encrypt, args.password_encode, args.username + '/',
             args.quota,
             local_part, args.domain, cur_time, cur_time))

        # 在虚拟用户家目录创建对应邮箱的目录
        user_path = '/www/vmail/{0}/{1}'.format(domain, local_part)
        os.makedirs(user_path)
        os.makedirs(user_path + '/tmp')
        os.makedirs(user_path + '/new')
        os.makedirs(user_path + '/cur')
        public.ExecShell('chown -R vmail:mail /www/vmail/{0}/{1}'.format(domain, local_part))
        # 此处密码需要先解密
        password = self._decode(args.password_encode)
        self.create_mail_box(username, password)
        return public.returnMsg(True, "成功添加用户 {}".format(username))

    def check_field_exists(self, db_obj, table_name, field_name):
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
        except:
            pass
        return False

    # 检查字段是否存在 不存在创建
    def check_domain_column(self, ):
        """
        @name 检查数据库表或字段是否完整
        """
        with self.M("domain") as obj:
            if not self.check_field_exists(obj, "domain", "a_record"):
                obj.execute('ALTER TABLE `domain` ADD COLUMN `a_record` Text default "";')

            if not self.check_field_exists(obj, "domain", "mailboxes"):
                obj.execute('ALTER TABLE `domain` ADD COLUMN `mailboxes` INT DEFAULT 50;')

            if not self.check_field_exists(obj, "domain", "mailbox_quota"):
                obj.execute('ALTER TABLE `domain` ADD COLUMN `mailbox_quota` BIGINT(20) NOT NULL DEFAULT 5368709120;')

            if not self.check_field_exists(obj, "domain", "quota"):
                obj.execute('ALTER TABLE `domain` ADD COLUMN `quota` BIGINT(20) NOT NULL DEFAULT 10737418240;')

            if not self.check_field_exists(obj, "domain", "rate_limit"):
                obj.execute('ALTER TABLE `domain` ADD COLUMN `rate_limit` INT DEFAULT 12;')

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
          `created` INTEGER NOT NULL,
          `modified` INTEGER NOT NULL,
          `active` tinyint(1) NOT NULL DEFAULT 0    --  预留字段
          );'''
        with self.M("") as obj:
            obj.execute(sql2, ())
            # self.M('').execute(sql2, ())

        # 判断存在 /www/vmail目录后再操作 避免新安装的失败
        if os.path.exists('/www/vmail'):
            sql = '''CREATE TABLE IF NOT EXISTS `mail_errlog` (
              `id` INTEGER  PRIMARY KEY AUTOINCREMENT,
              `created` INTEGER NOT NULL,            -- 收件人
              `recipient` varchar(320) NOT NULL,            -- 收件人
              `delay` varchar(320) NOT NULL,            -- 延时
              `delays` varchar(320) NOT NULL,            -- 各阶段延时
              `dsn` varchar(320) NOT NULL,            -- dsn
              `relay` text NOT NULL,                    -- 中继服务器
              `domain` varchar(320) NOT NULL,               -- 域名
              `status` varchar(255) NOT NULL,               -- 错误状态
              `err_info` text NOT NULL,                   -- 错误详情
              UNIQUE(created, recipient)
              );'''

            with self.MD("", "postfixmaillog") as obj2:
                obj2.execute(sql, ())

            # 退订表   退订时间和退订邮箱联合唯一   /www/vmail/mail_unsubscribe.db
            sql = '''CREATE TABLE IF NOT EXISTS `mail_unsubscribe` (
              `id` INTEGER  PRIMARY KEY AUTOINCREMENT,
              `created` INTEGER NOT NULL,
              `recipient` varchar(320) NOT NULL,            -- 收件人
              `etype`  INTEGER NOT NULL DEFAULT 1,           -- 邮件类型id
              `active` tinyint(1) NOT NULL DEFAULT 0,    --  0 取消订阅      1订阅
              `task_id` INTEGER  DEFAULT 0,       -- 群发任务 id  (退订有关联id  订阅没有)
              UNIQUE(etype, recipient)
              );'''

            with self.MD("", "mail_unsubscribe") as obj3:
                aa = obj3.execute(sql, ())
                #  public.print_log("初始化退订表 --{}".format(aa))

            # 异常用户表
            sql = '''CREATE TABLE IF NOT EXISTS `abnormal_recipient` (
            `id` INTEGER  PRIMARY KEY AUTOINCREMENT,
            `created` INTEGER NOT NULL,               -- 邮件时间 时间戳
            `recipient` varchar(320) NOT NULL,        -- 收件人
            `count` INTEGER NOT NULL,                 -- 次数
            `status` varchar(255) NOT NULL,           -- 状态
            `task_name` varchar(255) NOT NULL,      -- 任务名
            UNIQUE(recipient)
            );'''

            with self.MD("", "abnormal_recipient") as obj4:
                obj4.execute(sql, ())

        # 邮件日志分析统计表  接收 received, 发送 delivered, 延迟 deferred, 退回 bounced, 拒绝 rejected
        sql = '''CREATE TABLE IF NOT EXISTS `log_analysis` (
          `id` INTEGER  PRIMARY KEY AUTOINCREMENT,
          `received` INTEGER NOT NULL DEFAULT 0,        -- 接收
          `delivered` INTEGER NOT NULL DEFAULT 0,       -- 发送
          `deferred` INTEGER NOT NULL DEFAULT 0,        -- 延迟
          `bounced` INTEGER NOT NULL DEFAULT 0,         -- 退回
          `rejected` INTEGER NOT NULL DEFAULT 0,        -- 拒绝
          `time` INTEGER NOT NULL,                    -- 时间  每小时时间戳
           UNIQUE(`time`)    
          );'''
        with self.M("") as obj:
            obj.execute(sql, ())

        # 邮件类型表不存在时创建并插入一条数据
        mail_type_table_str = self.M('sqlite_master').where('type=? AND name=?', ('table', 'mail_type')).find()
        if not mail_type_table_str:
            # 邮件类型表  欢迎邮件 营销邮件
            sql = '''CREATE TABLE IF NOT EXISTS `mail_type` (
              `id` INTEGER  PRIMARY KEY AUTOINCREMENT,
              `mail_type` varchar(320) NOT NULL,            -- 邮件类型
              `created` INTEGER NOT NULL,
              `active` tinyint(1) NOT NULL DEFAULT 0    --  预留字段
              );'''
            with self.M("") as obj:
                obj.execute(sql, ())

            # 插入一条类型
            sql_insert = ''' INSERT INTO `mail_type`(`mail_type`, `created`) VALUES ('Default',  strftime('%s', 'now'));'''
            with self.M("") as obj:
                obj.execute(sql_insert, ())

    def _convert_quota_to_bytes(self, quota):
        num, unit = quota.split()
        if unit == 'GB':
            quota = float(num) * 1024 * 1024 * 1024
        else:
            quota = float(num) * 1024 * 1024
        return quota

    # 新 添加域名
    def add_domain_new(self, args):
        '''
        域名增加接口
        :param args:
        :return:
        '''
        if 'domain' not in args:
            return self.return_msg(public.returnMsg(False, 'DOMAIN_NAME'))
        domain = args.domain
        a_record = args.a_record
        # if not a_record.endswith(domain):
        #     return self.return_msg(public.returnMsg(False, 'A记录 [{}] 不属于这个域名'.format(a_record)))
        # if not self._check_a(a_record):
        #     return self.return_msg(public.returnMsg(False, 'A记录解析错误 <br>域名: {}<br>IP: {}'
        #                             .format(a_record, self._session['{}:A'.format(a_record)]['value'])))

        if self.M('domain').where('domain=?', domain).count() > 0:
            return self.return_msg(public.returnMsg(False, '域名已存在'))
        # 邮箱数  邮箱空间   域名空间   每秒几封 全数字类型
        if not hasattr(args, 'mailboxes') or args.get('mailboxes/d', 0) == 0:
            args.mailboxes = 50
        if not hasattr(args, 'mailbox_quota') or args.get('mailbox_quota/s', "") == "":
            args.mailbox_quota = "5 GB"
        if not hasattr(args, 'quota') or args.get('quota/s', "") == "":
            args.quota = "10 GB"
        if not hasattr(args, 'rate_limit') or args.get('rate_limit/d', 0) == 0:
            args.rate_limit = 12

        mailboxes = args.mailboxes
        rate_limit = args.rate_limit
        mailbox_quota = self._convert_quota_to_bytes(args.mailbox_quota)
        quota = self._convert_quota_to_bytes(args.quota)

        # 通过 添加
        cur_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            self.M('domain').add('domain,a_record,mailboxes,mailbox_quota,quota,rate_limit,created',
                                 (domain, a_record, mailboxes, mailbox_quota, quota, rate_limit, cur_time))
        except:
            return self.return_msg(public.returnMsg(False, '邮件服务器初始化失败。请重新打开插件以进行初始化<br>'
                                           '如果服务器没有打开25 端口（出站方向），将无法完成初始化。<br>'
                                           '您可以在终端中运行以下命令检查端口是否打开：<br><br>[ telnet gmail-smtp-in.l.google.com 25 ]'))

        errip = []
        # 增加域名的ip地址记录
        if 'ips' in args:
            data = {domain: {"ipv4": [], "ipv6": []}}
            ips = args.ips  # ips = '1.1.1.1;2.2.2.2;3.3.3.3'  或 ips = '1.1.1.1'
            # 根据 ; 拆分成列表
            ip_list = ips.split(';')
            # 循环列表
            for ip in ip_list:
                if public.is_ipv4(ip):
                    data[domain]["ipv4"].append(ip)
                elif public.is_ipv6(ip):
                    data[domain]["ipv6"].append(ip)
                else:
                    errip.append(ip)

            # 记录域名的ip address    /www/server/panel/plugin/mail_sys/domain_ip.json
            path = '/www/server/panel/plugin/mail_sys/domain_ip.json'

            if not os.path.exists(path):
                public.writeFile(path, json.dumps(data))
            else:
                rdata = public.readFile(path)
                try:
                    rdata = json.loads(rdata)
                except:
                    pass
                rdata.update(data)
                public.writeFile(path, json.dumps(rdata))
        # 增加 catchAll
        if hasattr(args, 'email') and args.get('email/s', "") != "":
            self._add_enable_catchall(args)
        # 在虚拟用户家目录创建对应域名的目录
        if not os.path.exists('/www/vmail/{0}'.format(domain)):
            os.makedirs('/www/vmail/{0}'.format(domain))
        public.ExecShell('chown -R vmail:mail /www/vmail/{0}'.format(domain))

        # 绑定dns-api
        dns_id = 0
        if "dns_id" in args:
            dns_id = args.dns_id
        # 获取根域名
        from sslModel.base import sslBase
        root_domain, _, _ = sslBase().extract_zone(domain)
        # 判断是否存在该域名
        dns_data = public.M('ssl_domains').where("domain=?", (root_domain,)).find()
        if not dns_data:
            public.M('ssl_domains').add('domain,dns_id,type_id,endtime,ps', (domain, dns_id, 0, 0, ''))
        # 自动解析
        if 'auto_create_record' in args and args.auto_create_record:
            self.auto_create_dns_record(args)
        if 'ip_tag' in args and args.ip_tag:
            from mailModel import multipleipModel
            ip_tags = args.ip_tag.split(',')
            bind = "@{}".format(domain)
            multipleipModel.main().add_bind_ip_tag(ip_tags[0], bind)
            if len(ip_tags) > 1:
                multipleipModel.set_ip_rotate_conf(domain, ip_tags, 10, True)

        if len(errip) > 0:
            return self.return_msg(public.returnMsg(True, '域名[{}]添加成功! ip err:{}'.format(domain, errip)))
        return self.return_msg(public.returnMsg(True, '域名[{0}]添加成功!'.format(domain)))

    def update_domain(self, args):
        '''
        域名编辑接口
        :param args:
        :return:
        '''
        if 'domain' not in args:
            return self.return_msg(public.returnMsg(False, 'DOMAIN_NAME'))

        domain = args.domain
        if self.M('domain').where('domain=?', domain).count() == 0:
            return self.return_msg(public.returnMsg(False, '域名不存在'))

        if not hasattr(args, 'rate_limit') or args.get('rate_limit/d', 0) == 0:
            args.rate_limit = 12
        if not hasattr(args, 'mailboxes') or args.get('mailboxes/d', 0) == 0:
            args.mailboxes = 50
        if not hasattr(args, 'mailbox_quota') or args.get('mailbox_quota/s', "") == "":
            args.mailbox_quota = "5 GB"
        if not hasattr(args, 'quota') or args.get('quota/s', "") == "":
            args.quota = "10 GB"

        rate_limit = args.rate_limit
        mailboxes = args.mailboxes
        mailbox_quota = self._convert_quota_to_bytes(args.mailbox_quota)
        quota = self._convert_quota_to_bytes(args.quota)

        try:
            data = {
                "mailboxes": mailboxes,
                "mailbox_quota": mailbox_quota,
                "quota": quota,
                "rate_limit": rate_limit,
            }
            self.M('domain').where('domain=?', domain).update(data)
        except Exception as ex:
            public.print_log(public.get_error_info())

        # 修改cacheall  开启 先删再加   关闭 加
        if hasattr(args, 'email'):
            email_old = self._get_domain_forward(domain)
            if args.get('email/s', "") == "":
                self.enable_catchall(args)
            else:
                if email_old != args.email:
                    self.enable_catchall(args)

        # 绑定dns-api
        dns_id = 0
        if "dns_id" in args:
            dns_id = args.dns_id
        # 获取根域名
        from sslModel.base import sslBase
        root_domain, _, _ = sslBase().extract_zone(domain)
        # 判断是否存在该域名
        dns_data = public.M('ssl_domains').where("domain=?", (root_domain,)).find()
        if not dns_data:
            public.M('ssl_domains').add('domain,dns_id,type_id,endtime,ps', (domain, dns_id, 0, 0, ''))
        else:
            public.M('ssl_domains').where("domain=?", (root_domain,)).update({'dns_id': dns_id})
        # 自动解析
        if 'auto_create_record' in args and args.auto_create_record:
            self.auto_create_dns_record(args)
        if 'ip_tag' in args:
            from mailModel import multipleipModel
            ip_tags = args.ip_tag.split(',')
            bind = "@{}".format(domain)
            multipleipModel_main = multipleipModel.main()
            multipleipModel_main.edit_bind_ip_tag(ip_tags[0], bind)
            if len(ip_tags) > 1:
                multipleipModel_main.set_ip_rotate_conf(domain, ip_tags)
            else:
                if not ip_tags[0]: ip_tags = []
                multipleipModel_main.set_ip_rotate_conf(domain, ip_tags, status=False)

        return self.return_msg(public.returnMsg(True, '修改域名[{}]成功!'.format(domain)))

    # 删除转发
    def _deledte_catchall(self, domain):
        '''
        删除邮件被转发
        :param args:
        :return:
        '''
        domain = '@' + domain.strip()
        self.M('alias').where('address=? or address=?', (domain, '%'+domain)).delete()

    # 定时分析记录日志到数据库 弃用
    def _mail_logs_task(self, args):

        import crontab
        p = crontab.crontab()
        try:
            c_id = public.M('crontab').where('name=?', u'[勿删] 邮件日志').getField('id')

            if not c_id:
                data = {}
                data['name'] = u'[勿删] 邮件日志'
                data['type'] = 'minute-n'
                data['where1'] = '10'
                data['sBody'] = 'btpython /www/server/panel/class/mailModel/script/mail_logs.py'
                data['backupTo'] = ''
                data['sType'] = 'toShell'
                data['hour'] = ''
                data['minute'] = ''
                data['week'] = ''
                data['sName'] = ''
                data['urladdress'] = ''
                data['save'] = ''
                p.AddCrontab(data)
                return self.return_msg(public.returnMsg(True, '设置成功!'))
        except Exception as e:
            public.print_log(public.get_error_info())

    # 获取最新日志详情   弃用
    def mail_log_list(self, args):
        # self._mail_logs_task(None)
        p = int(args.p) if 'p' in args else 1
        rows = int(args.size) if 'size' in args else 10
        callback = args.callback if 'callback' in args else ''
        try:
            count = self.M('email_log').count()
            # 获取分页数据
            page_data = public.get_page(count, p, rows, callback)
            pattern = r"href='(?:/v2)?/plugin.*?\?p=(\d+)'"
            # 使用re.sub进行替换
            page_data['page'] = re.sub(pattern, r"href='\1'", page_data['page'])
            # 获取当前页的数据列表
            data_list = self.M('email_log').order('created desc').limit(
                page_data['shift'] + ',' + page_data['row']).select()
            # 返回数据到前端
            return self.return_msg({'data': data_list, 'page': page_data['page']})
        except Exception as ex:
            public.print_log(public.get_error_info())

    # 投递结果
    # 基于邮件标签的统计数据，及时关注邮件投递结果。
    # 发送情况
    # 邮件群发时可查看邮件请求量、发送成功量、失败量、无效地址量和到达率等统计数据。

    # 增加收件人/群组表 临时用
    # def add_tables(self):
    #     # 新增免费邮箱表
    #     sql = '''CREATE TABLE IF NOT EXISTS `public_mailbox` (
    #       `id` INTEGER  PRIMARY KEY AUTOINCREMENT,
    #       `domain` varchar(255) NOT NULL,
    #       `ps` varchar(255) NULL,
    #       `maxnum` MEDIUMINT NOT NULL DEFAULT 5000, -- 对应每日最多发送量
    #       `active` tinyint(1) NOT NULL DEFAULT 1
    #       );'''
    #     self.M('').execute(sql, ())
    #
    #     # 增加默认数据
    #     sql = '''INSERT INTO `spider_list`(`domain`, `maxnum`, `active`) VALUES
    #        ('gmail.com', 5000, 1),
    #        ('hotmail.com', 5000, 1), --
    #        ('outlook.com', 5000, 1), -- 与 hotmail.com合并累计5000
    #        ('yahoo.com', 5000, 1),
    #        ('protonmail.com', 5000, 1),
    #        ('zoho.com', 5000, 1),
    #        ('icloud.com', 5000, 1);'''
    #     self.M('').execute(sql, ())
    #
    #     # 新增收件人分组表   群组最大邮箱数限制?
    #     sql = '''CREATE TABLE IF NOT EXISTS `recipient_group` (
    #       `id` INTEGER  PRIMARY KEY AUTOINCREMENT,
    #       `group` varchar(255) NOT NULL,
    #       `ps` varchar(255) NULL,
    #       `created` datetime NOT NULL,
    #       `modified` datetime NOT NULL,
    #       `active` tinyint(1) NOT NULL DEFAULT 1  -- 可以禁用分组或取消禁用
    #       );'''
    #     self.M('').execute(sql, ())
    #
    #     # 新增收件人表  收件人可以有多个群组?  表数据比较多
    #     sql = '''CREATE TABLE IF NOT EXISTS `recipient` (
    #       `email` varchar(320) NOT NULL,
    #       `group` int NOT NULL,         -- 所属群组 群组id
    #       `mailbox` int NOT NULL DEFAULT 0,  -- 关联免费邮箱  无查到就是0
    #       `ps` varchar(255) NULL,         -- 可以为空
    #       `created` datetime NOT NULL,
    #       `modified` datetime NOT NULL,
    #       `active` tinyint(1) NOT NULL DEFAULT 1,  -- 邮件接收失败后改为0  无效地址  发邮件时可选只发送有效地址
    #       PRIMARY KEY (`email`));'''
    #     self.M('').execute(sql, ())
    #
    #     return 1

    # 添加 roundcube  添加成功后记录路由  修复 只检测nginx服务的问题
    def add_roundcube(self, args):
        public.set_module_logs('mailModel', 'add_roundcube', 1)
        is_ok = self.get_roundcube_status(None)
        if isinstance(is_ok, dict) and is_ok['status']:
            return self.return_msg(public.returnMsg(False, "roundcube已存在"))

        if not os.path.exists('/usr/bin/mysql'):
            return self.return_msg(public.returnMsg(False, '没有检测到MySQL服务!请先安装MySQL'))
        # 检测mysql是否安装
        from panelModel.publicModel import main
        get1 = public.dict_obj()
        get1.name = 'mysql'
        mysqlinfo = main().get_soft_status(get1)
        public.print_log("mysqlinfo--{}".format(mysqlinfo))
        if not mysqlinfo['status']:
            public.print_log(mysqlinfo['status'])
            if not mysqlinfo['setup'] or not mysqlinfo['status']:
                return self.return_msg(public.returnMsg(False, '没有检测到MySQL服务!请先安装MySQL'))

        # 查看当前web服务
        webserver = public.GetWebServer()
        if webserver == 'nginx':
            # 检测 nginx
            if not os.path.exists('/etc/init.d/nginx'):
                return self.return_msg(public.returnMsg(False, '没有检测到nginx服务!请先安装nginx'))
            get2 = public.dict_obj()
            get2.name = 'nginx'
            mysqlinfo = main().get_soft_status(get2)
        if not mysqlinfo['status']:
            if not mysqlinfo['setup'] or not mysqlinfo['status']:
                return self.return_msg(public.returnMsg(False, '没有检测到nginx服务!请先安装nginx'))

        args.dname = 'roundcube'
        if not hasattr(args, 'site_name') or args.get('site_name/s', "") == "":

            return self.return_msg(public.returnMsg(False, '参数错误 site_name'))
        if not hasattr(args, 'php_version') or args.get('php_version/s', "") == "":
            return self.return_msg(public.returnMsg(False, '参数错误 php_version'))
        site_name = args.site_name
        php_version = args.php_version

        # 先添加网站 数据库
        from panelSite import panelSite
        # from common import to_dict_obj
        ps = site_name.replace('.', '_').replace('-', '_')
        data = panelSite().AddSite(public.to_dict_obj({
            'webname': json.dumps({
                'domain': site_name,
                'domainlist': [],
                'count': 0,
            }),
            'type': 'PHP',
            'version': php_version,
            'port': '80',
            'path': '/www/wwwroot/' + site_name,
            'sql': 'MySQL',
            'datauser': 'sql_' + ps,
            'datapassword': public.GetRandomString(16).lower(),
            'codeing': 'utf8mb4',
            'ps': ps,
            'set_ssl': 0,
            'force_ssl': 0,
            'ftp': False,
        }))
        # The site you tried to add already exists
        public.print_log(data)
        if not data.get('status', True):
            return self.return_msg(data)

        deployment = self.SetupPackage_roundcube(args)
        if not deployment['status']:
            return self.return_msg(deployment)

        tistamp = int(time.time())
        # 将网址和创建时间写入文件
        roundcube_info = {
            "status": True,
            "id": data['siteId'],
            "site_name": site_name,
            "php_version": php_version,
            "ssl_status": False,
            # "ssl_info": self.get_ssl_info(site_name),
            "timestimp": tistamp,
        }
        path = "/www/server/panel/plugin/mail_sys/roundcube.json"
        public.writeFile(path, json.dumps(roundcube_info))
        return self.return_msg(public.returnMsg(True, '安装成功'))

    def SetupPackage_roundcube(self, get):
        import plugin_deployment
        sysObject = plugin_deployment.plugin_deployment()

        name = get.dname
        site_name = get.site_name
        php_version = get.php_version
        # 取基础信息
        find = public.M('sites').where('name=?', (site_name,)).field('id,path').find()
        path = find['path']

        pinfo = {
            "username": "",
            "ps": "免费开源的邮件客户端程序",
            "php": "56,70,71,72,73,74,80",
            "run": "",
            "name": "roundcube",
            "title": "Roundcube",
            "type": 6,
            "chmod": "",
            "ext": "pathinfo,exif",
            "version": "1.5.0",
            "install": "",
            # "download": "{Download}/roundcubemail.zip",
            # "download": "{}/install/plugin/mail_sys/roundcubemail.zip".format(public.get_url()),
            "download": "https://node.aapanel.com/install/package/roundcubemail.zip",
            # "download": "http://127.0.0.1/roundcube.zip",
            "password": "",
            "config": "/config/config.inc.php",
            "md5": "785660db6540692b5c0eb240b41816e9"
        }

        # 检查本地包
        sysObject.WriteLogs(
            json.dumps({'name': public.GetMsg("VERIFYING_PACKAGE"), 'total': 0, 'used': 0, 'pre': 0, 'speed': 0}))
        # 安装包
        packageZip = 'plugin/mail_sys/' + name + '.zip'
        isDownload = False
        if os.path.exists(packageZip):
            md5str = sysObject.GetFileMd5(packageZip)
            if md5str != pinfo['md5']:
                isDownload = True
        else:
            isDownload = True

        # 删除多余文件
        rm_file = path + '/index.html'
        if os.path.exists(rm_file): os.remove(rm_file)

        # 下载文件
        if isDownload:
            sysObject.WriteLogs(
                json.dumps({'name': public.GetMsg("DOWNLOAD"), 'total': 0, 'used': 0, 'pre': 0, 'speed': 0}))
            sysObject.DownloadFile(pinfo['download'], packageZip)

        if not os.path.exists(packageZip):
            return public.returnMsg(False, "DOWNLOAD_FILE_FAIL")

        sysObject.WriteLogs(json.dumps({'name': public.GetMsg("UNPACKING"), 'total': 0, 'used': 0, 'pre': 0, 'speed': 0}))
        public.ExecShell('unzip -o ' + packageZip + ' -d ' + path + '/')

        # 设置权限
        sysObject.WriteLogs(
            json.dumps({'name': public.GetMsg("SET_PERMISSION"), 'total': 0, 'used': 0, 'pre': 0, 'speed': 0}))
        public.ExecShell('chmod -R 755 ' + path)
        public.ExecShell('chown -R www.www ' + path)

        if pinfo['chmod'] != "":
            access = pinfo['chmod'].split(',')
            for chm in access:
                tmp = chm.split('|')
                if len(tmp) != 2: continue;
                public.ExecShell('chmod -R ' + tmp[0] + ' ' + path + '/' + tmp[1])

        # 执行额外shell进行依赖安装
        sysObject.WriteLogs(
            json.dumps({'name': public.GetMsg("EXECUTE_EXTRA_SHELL"), 'total': 0, 'used': 0, 'pre': 0, 'speed': 0}))
        if os.path.exists(path + '/install.sh'):
            public.ExecShell('cd ' + path + ' && bash ' + 'install.sh')
            public.ExecShell('rm -f ' + path + '/install.sh')

        # 是否执行Composer
        if os.path.exists(path + '/composer.json'):
            sysObject.WriteLogs(json.dumps({'name': 'Execute Composer', 'total': 0, 'used': 0, 'pre': 0, 'speed': 0}))
            if not os.path.exists(path + '/composer.lock'):
                execPHP = '/www/server/php/' + php_version + '/bin/php'
                if execPHP:
                    if public.get_url().find('125.88'):
                        public.ExecShell(
                            'cd ' + path + ' && ' + execPHP + ' /usr/bin/composer config repo.packagist composer https://packagist.phpcomposer.com')
                    import panelSite
                    phpini = '/www/server/php/' + php_version + '/etc/php.ini'
                    phpiniConf = public.readFile(phpini)
                    phpiniConf = phpiniConf.replace('proc_open,proc_get_status,', '')
                    public.writeFile(phpini, phpiniConf)
                    public.ExecShell(
                        'nohup cd ' + path + ' && ' + execPHP + ' /usr/bin/composer install -vvv > /tmp/composer.log 2>&1 &')

        # 写伪静态
        sysObject.WriteLogs(
            json.dumps({'name': public.GetMsg("SET_URL_REWRITE"), 'total': 0, 'used': 0, 'pre': 0, 'speed': 0}))
        swfile = path + '/nginx.rewrite'
        if os.path.exists(swfile):
            rewriteConf = public.readFile(swfile)
            dwfile = sysObject.__panelPath + '/vhost/rewrite/' + site_name + '.conf'
            public.writeFile(dwfile, rewriteConf)

        # 删除伪静态文件
        public.ExecShell("rm -f " + path + '/*.rewrite')

        # 设置运行目录
        sysObject.WriteLogs(json.dumps({'name': public.GetMsg("SET_RUN_DIR"), 'total': 0, 'used': 0, 'pre': 0, 'speed': 0}))
        if pinfo['run'] != '/':
            import panelSite
            from plugin_deployment import obj
            siteObj = panelSite.panelSite()
            mobj = obj()
            mobj.id = find['id']
            mobj.runPath = pinfo['run']
            # return find['id']
            siteObj.SetSiteRunPath(mobj)

        # 导入数据
        sysObject.WriteLogs(json.dumps({'name': public.GetMsg("IMPORT_DB"), 'total': 0, 'used': 0, 'pre': 0, 'speed': 0}))

        if os.path.exists(path + '/import.sql'):
            databaseInfo = public.M('databases').where('pid=?', (find['id'],)).field('username,password').find()
            if databaseInfo:
                public.ExecShell('/www/server/mysql/bin/mysql -u' + databaseInfo['username'] + ' -p' + databaseInfo[
                    'password'] + ' ' + databaseInfo['username'] + ' < ' + path + '/import.sql')

                public.ExecShell('rm -f ' + path + '/import.sql')
                # /www/wwwroot/moyumao.top + '/' + /config/config.inc.php

                siteConfigFile = path + '/' + pinfo['config']
                if os.path.exists(siteConfigFile):

                    siteConfig = public.readFile(siteConfigFile)
                    siteConfig = siteConfig.replace('BT_DB_USERNAME', databaseInfo['username'])
                    siteConfig = siteConfig.replace('BT_DB_PASSWORD', databaseInfo['password'])
                    siteConfig = siteConfig.replace('BT_DB_NAME', databaseInfo['username'])
                    # public.print_log("写入数据库文件  ---{}".format(siteConfigFile))
                    public.writeFile(siteConfigFile, siteConfig)


        public.serviceReload()
        sysObject.depTotal(name)
        sysObject.WriteLogs(
            json.dumps({'name': public.GetMsg("READY_DEPLOY"), 'total': 0, 'used': 0, 'pre': 0, 'speed': 0}))

        return public.returnMsg(True, pinfo)

    # 检查ssl
    def _get_roundcube_ssl(self, site_name):
        from data import data
        has_ssl = data().get_site_ssl_info(site_name)
        if has_ssl != -1:
            return True
        else:
            return False

    # 查看是否有 roundcube
    def get_roundcube_status(self, args):

        # 版本 "5.1"
        # versions = public.get_plugin_info("mail_sys")['versions']
        # if versions < "6.0":
        #     return self.return_msg(public.returnMsg(False, '请在应用商定将宝塔邮局升级到6.0或更高版本'))

        path = "/www/server/panel/plugin/mail_sys/roundcube.json"
        if os.path.exists(path):
            data = public.readFile(path)
            public_data = {}
            if data != '':
                public_data = json.loads(data)

            return self.return_msg(public_data)
        else:
            return self.return_msg({"status": False})

    # 初始化时更新ssl状态
    def _roundcube_ssl_status(self):
        path = "/www/server/panel/plugin/mail_sys/roundcube.json"

        if os.path.exists(path):
            data = public.readFile(path)
            # public_data = {}
            if data != '':
                public_data = json.loads(data)

                site_name = public_data['site_name']
                # 更新 public_data 的ssl_status
                # public.print_log("更新ssl状态 ---{}".format(public_data['ssl_status']))
                public_data['ssl_status'] = True if self._get_multiple_certificate_domain_status(
                    site_name) or self._get_roundcube_ssl(site_name) else False
                public.writeFile(path, json.dumps(public_data))

    def get_domain(self, args):
        '''
        查询网站
        :param args:
        :return:
        '''

        data_list = public.M('sites').field('id,name,path').select()
        return self.return_msg(data_list)

    # 添加已有网站到部署信息里
    def add_roundcube_info(self, args):
        if not hasattr(args, 'id') or args.get('id/d', 0) == 0:
            return self.return_msg(public.returnMsg(False, '参数错误 id'))
        if not hasattr(args, 'site_name') or args.get('site_name/s', "") == "":
            return self.return_msg(public.returnMsg(False, '参数错误 site_name'))
        if not hasattr(args, 'path') or args.get('path/s', "") == "":
            return self.return_msg(public.returnMsg(False, '参数错误 path'))

        id = args.get('id/d', 0)
        name = args.get('site_name/s', "")
        path = args.get('path/s', "")
        # /www/wwwroot/webmail.moyumao.top /composer.json
        if path.endswith('/'):
            path = path.rstrip('/')
        cmp_path = path + '/composer.json'
        if not os.path.exists(cmp_path):
            return self.return_msg(public.returnMsg(False, '此站点未部署roundcube'))
        info = json.loads(public.readFile(cmp_path))
        # roundcube
        if info['name'].find("roundcube") == -1:
            return self.return_msg(public.returnMsg(False, '此站点未部署roundcube'))

        tistamp = int(time.time())
        # 将网址和创建时间写入文件
        roundcube_info = {
            "status": True,
            "id": id,
            "site_name": name,
            "php_version": None,
            "ssl_status": self._get_multiple_certificate_domain_status(name),
            "timestimp": tistamp,
        }
        path = "/www/server/panel/plugin/mail_sys/roundcube.json"
        public.writeFile(path, json.dumps(roundcube_info))
        return self.return_msg(public.returnMsg(True, '添加成功'))


    def uninstall_roundcube(self, args):

        if not hasattr(args, 'site_name') or args.get('site_name/s', "") == "":
            return self.return_msg(public.returnMsg(False, '参数 site_name 错误'))
        if not hasattr(args, 'id') or args.get('id/s', "") == "":
            return self.return_msg(public.returnMsg(False, '参数 id 错误'))
        if not hasattr(args, 'force') or args.get('force/d', 0) == 0:
            args.force = 0
        site_name = args.site_name
        id = args.id
        force = args.force
        from panelSite import panelSite
        if force:
            data = panelSite().DeleteSite(public.to_dict_obj({
                'id': id,
                'webname': site_name,
                'ftp': '1',
                'path': '1',
                'database': '1',
            }))
        else:
            data = panelSite().DeleteSite(public.to_dict_obj({
                'id': id,
                'webname': site_name,
            }))
        path = "/www/server/panel/plugin/mail_sys/roundcube.json"
        if os.path.exists(path):
            os.remove(path)
        return self.return_msg(data)

    # 开关 在用
    def recipient_blacklist_open(self, status):
        # 开启 Ture,  关闭 False
        result = public.readFile(self.postfix_main_cf)
        # 没有配置
        if not result:
            return False
        match = re.search(r"smtpd_recipient_restrictions\s*=\s*(.+)", result)
        if not match:
            return False

        if status:
            new_restrictions = 'check_recipient_access hash:/etc/postfix/blacklist,permit_sasl_authenticated, permit_mynetworks, reject_unauth_destination'
            updated_config = re.sub(
                r"smtpd_recipient_restrictions\s*=\s*(.+)",
                f"smtpd_recipient_restrictions = {new_restrictions}",
                result
            )
            public.writeFile(self.postfix_main_cf, updated_config)
        else:
            new_restrictions = 'permit_sasl_authenticated, permit_mynetworks, reject_unauth_destination'
            updated_config = re.sub(
                r"smtpd_recipient_restrictions\s*=\s*(.+)",
                f"smtpd_recipient_restrictions = {new_restrictions}",
                result
            )
            public.writeFile(self.postfix_main_cf, updated_config)
        return True

    # 黑名单状态
    def _recipient_blacklist_status(self):
        # 查看配置是否有黑名单限制
        result = public.readFile(self.postfix_main_cf)

        match = re.search(r"smtpd_recipient_restrictions\s*=\s*(.+)", result)
        if not match:
            return False

        restrictions = match.group(1)
        if 'check_recipient_access hash:/etc/postfix/blacklist' not in restrictions:
            return False
        else:
            return True

    # 收件人黑名单
    def recipient_blacklist(self, args):
        keyword = args.get('keyword/s', '')

        if not keyword or keyword == '':
            keyword = None

        # 判断是否开启黑名单
        if not self._recipient_blacklist_status():
            # return public.returnMsg(False, 'Blacklist is not open')
            return self.return_msg(public.returnMsg(True, []))


        # 黑名单文件是否存在
        if not os.path.exists(self.postfix_recipient_blacklist):
            public.writeFile(self.postfix_recipient_blacklist, '')
            public.ExecShell('postmap /etc/postfix/blacklist')

        try:
            with open(self.postfix_recipient_blacklist, 'r') as file:
                emails = file.read().splitlines()
        except Exception as e:
            emails = []

        # 去掉  REJECT
        if emails:
            emails = [email.split()[0] for email in emails]
        else:
            # 黑名单为空 关闭
            st = self.recipient_blacklist_open(False)
            if st:
                public.ExecShell('systemctl reload postfix')
            return self.return_msg(public.returnMsg(True, []))

        # 模糊查询匹配的邮箱
        if keyword:
            emails = [email for email in emails if re.search(keyword, email)]

        return self.return_msg(public.returnMsg(True, emails))

    # 添加收件人黑名单
    def add_recipient_blacklist(self, args):
        # 收件人列表  一行一个
        if not os.path.exists(self.postfix_recipient_blacklist):
            public.writeFile(self.postfix_recipient_blacklist, '')

        emails_to_add = args.emails_to_add if 'emails_to_add' in args else []
        try:
            emails_to_add = json.loads(args.emails_to_add)
        except:
            pass

        try:

            if not emails_to_add:
                return self.return_msg(public.returnMsg(False, '参数错误emails_to_add'))

            # 构造要追加的行的集合
            add_set = {f"{email} REJECT\n" for email in emails_to_add}

            try:
                # 读取现有文件内容
                with open(self.postfix_recipient_blacklist, 'r') as file:
                    existing_lines = set(file.readlines())

                # 获取待追加但不重复的邮箱
                new_lines = add_set - existing_lines

                # 将新的行追加到文件
                if new_lines:
                    with open(self.postfix_recipient_blacklist, 'a') as file:
                        file.writelines(new_lines)

            except Exception as e:
                return self.return_msg(public.returnMsg(False, e))

            # 未开启黑名单配置 先开启
            if not self._recipient_blacklist_status():
                # 开启
                self.recipient_blacklist_open(True)

            shell_str = '''
            postmap /etc/postfix/blacklist
            systemctl reload postfix
            '''
            public.ExecShell(shell_str)
        except:
            public.print_log(public.get_error_info())

        return self.return_msg(public.returnMsg(True, '成功添加黑名单'))

    # 删除收件人黑名单
    def del_recipient_blacklist(self, args):
        try:
            emails_to_remove = json.loads(args.emails_to_remove) if 'emails_to_remove' in args else []

            if not emails_to_remove:
                return self.return_msg(public.returnMsg(False, '参数错误 emails_to_remove'))

            remove_set = {f"{email} REJECT\n" for email in emails_to_remove}

            try:
                # 读取现有文件内容
                with open(self.postfix_recipient_blacklist, 'r') as file:
                    lines = file.readlines()

                # 写回不在删除集合中的行
                with open(self.postfix_recipient_blacklist, 'w') as file:
                    for line in lines:
                        if line not in remove_set:
                            file.write(line)

            except Exception as e:
                return self.return_msg(public.returnMsg(False, e))

            # 检测黑名单是否为空  为空关闭黑名单
            # if not os.path.exists(self.postfix_recipient_blacklist):
            #     public.writeFile(self.postfix_recipient_blacklist, '')
            filedata = public.readFile(self.postfix_recipient_blacklist)
            if not filedata or filedata == '':
                self.recipient_blacklist_open(False)

            shell_str = '''
            postmap /etc/postfix/blacklist
            systemctl reload postfix
            '''
            public.ExecShell(shell_str)
        except:
            public.print_log(public.get_error_info())
        return self.return_msg(public.returnMsg(True, '黑名单删除成功'))

    # 导出收件人黑名单
    def export_recipient_blacklist(self, args):

        # 黑名单文件存在
        if not os.path.exists(self.postfix_recipient_blacklist):
            return self.return_msg(public.returnMsg(False, '没有黑名单文件'))

        try:
            with open(self.postfix_recipient_blacklist, 'r') as file:
                emails = file.read().splitlines()
        except Exception as e:
            emails = []

        # 去掉  REJECT
        if emails != []:
            emails = [email.split()[0] for email in emails]
        else:
            return self.return_msg(public.returnMsg(False, '没有黑名单可以导出'))
        file_name = 'recipient_blacklist'
        rule_path = '/www/server/panel/data/mail/'
        file_path = "{}{}.json".format(rule_path, file_name)
        public.writeFile(file_path, public.GetJson(emails))
        return self.return_msg(public.returnMsg(True, file_path))

    # 导入收件人黑名单
    def import_recipient_blacklist(self, args):
        try:
            file = args.get('file/s', '')

            if not file:
                return self.return_msg(public.returnMsg(False, '文件不能为空'))

            if not os.path.exists(file):
                return self.return_msg(public.returnMsg(False, '文件不存在'))

            try:
                data = public.readFile(file)
                data = json.loads(data)
            except Exception as e:
                return self.return_msg(public.returnMsg(False, '文件内容异常或格式错误: {}'.format(e)))
            args.emails_to_add = data
            self.add_recipient_blacklist(args)
            return self.return_msg(public.returnMsg(True, '成功导入黑名单'))
        except:
            public.print_log(public.get_error_info())

    # ---------------------------------------------- 退订管理(新) -----------------------------

    # 获取异常邮件列表  status筛选  search查询
    def get_abnormal_recipient(self, args):

        p = int(args.p) if 'p' in args else 1
        rows = int(args.size) if 'size' in args else 12
        data_list = []

        if "search" in args and args.search != "":
            where_str = "recipient LIKE ? OR task_name LIKE ?"
            where_args = (f"%{args.search.strip()}%", f"%{args.search.strip()}%")
        else:
            where_str = "id!=?"
            where_args = (0,)

        if 'status' in args and args.status != "":
            status = args.status
            if where_str and where_args:
                where_str = "status=? AND (recipient LIKE? OR task_name LIKE ?)"

                where_args = (status, f"%{args.search.strip()}%", f"%{args.search.strip()}%")
            else:
                where_str = "status=?"
                where_args = (status,)

            with public.S("abnormal_recipient", "/www/vmail/abnormal_recipient") as obj:
                count = obj.where(where_str, where_args).select()
                data_list = obj.order('created', 'DESC').limit(rows, (p - 1) * rows).where(where_str,
                                                                                           where_args).select()

            for i in data_list:
                if i['status'] == 'bounced':
                    i['state'] = 1
                else:
                    i['state'] = 1 if i['count'] >= 3 else 0

            return self.return_msg({'data': data_list, 'total': len(count)})

        else:
            with public.S("abnormal_recipient", "/www/vmail/abnormal_recipient") as obj:
                count = obj.where(where_str, where_args).select()
                data_list = obj.order('created', 'DESC').limit(rows, (p - 1) * rows).where(where_str,
                                                                                           where_args).select()

            for i in data_list:
                if i['status'] == 'bounced':
                    i['state'] = 1
                else:
                    i['state'] = 1 if i['count'] >= 3 else 0
            # 返回数据到前端
            return self.return_msg({'data': data_list, 'total': len(count)})

    def get_abnormal_status(self, args):
        with public.S("abnormal_recipient", "/www/vmail/abnormal_recipient") as obj:
            count = obj.group('status').field('status').select()
        return self.return_msg(count)

    # 删除数据  批量删  单独删
    def del_abnormal_recipient(self, args):
        try:
            # delnum = 0
            if "ids" in args and args.ids != "":
                ids_list = args.ids.split(',')
                ids_list = [int(id_str) for id_str in ids_list]
                with public.S("abnormal_recipient", "/www/vmail/abnormal_recipient.db") as obj:
                    nums = obj.where_in('id', ids_list).column('id')
                    if len(nums) > 0:
                        obj.where_in('id', ids_list).delete()
            return self.return_msg(public.returnMsg(True, public.lang('删除成功')))
        except Exception as e:
            return self.return_msg(public.returnMsg(False, public.lang('错误: {}', e)))

    # 清空数据
    def clear_abnormal_recipient(self, args):
        try:

            if "status" in args and args.status != "":
                status = args.status
            else:
                status = 'all'

            if status == 'all':  # 全部删除
                with public.S("abnormal_recipient", "/www/vmail/abnormal_recipient.db") as obj:
                    obj.delete()
            else:
                with public.S("abnormal_recipient", "/www/vmail/abnormal_recipient.db") as obj:
                    nums = obj.where('status', status).delete()
                    public.print_log('清空 {}个'.format(nums))
            return self.return_msg(public.returnMsg(True, public.lang('清空 {} 成功', status)))
        except Exception as e:
            return self.return_msg(public.returnMsg(False, public.lang('错误: {}', e)))

    def _sync_blacklist_to_unsubscribe_db(self):
        # 黑名单列表同步到退订数据库
        # 获取黑名单  构造数据    批量插入数据库  判断数量  关闭黑名单
        if not os.path.exists('/www/vmail'):
            return
        # 判断同步标记
        path = '/www/server/panel/data/mail_sync_black_to_unsubscribe_db.pl'
        if os.path.exists(path):
            return

        recipient_blacklist = []
        if not self._recipient_blacklist_status() or not os.path.exists(self.postfix_recipient_blacklist):
            # if not os.path.exists(self.postfix_recipient_blacklist):
            recipient_blacklist = []
        else:

            try:
                with open(self.postfix_recipient_blacklist, 'r') as file:
                    emails = file.read().splitlines()
            except Exception as e:
                emails = []
            # 去掉  REJECT
            if emails:
                recipient_blacklist = [email.split()[0] for email in emails]

        # 存在黑名单 处理
        if recipient_blacklist:
            created = int(time.time())
            insert_data = []
            for recipient in recipient_blacklist:
                insert_data.append({
                    "created": created,
                    "recipient": recipient,
                    "etype": 0,
                })

            # 邮件类型和收件人唯一 不会重复插入
            with public.S("mail_unsubscribe", "/www/vmail/mail_unsubscribe.db") as obj:
                aa = obj.insert_all(insert_data, option='IGNORE')
            # public.print_log("黑名单列表同步到退订数据库  --{}".format(aa))
        # if aa != len(recipient_blacklist):
        # public.print_log("000黑名单同步不正常  插入--{}   原始--{}".format(aa, len(recipient_blacklist)))

        # 关闭黑名单
        st = self.recipient_blacklist_open(False)
        if st:
            public.ExecShell('systemctl reload postfix')

        # 添加处理标记
        public.writeFile(path, 1)

    # 修改后群发专用退订管理 todo 增加必传 active
    def get_unsubscribe_list(self, args):
        '''
        获取退订用户列表
        :param args: etype  邮件类型id
        :param args: search  搜索  收件人
        :param args: active  类型  0退订  1订阅
        :return:
        '''
        p = int(args.p) if 'p' in args else 1
        rows = int(args.size) if 'size' in args else 12
        active = args.active if 'active' in args else 0

        if "search" in args and args.search != "":
            where_str = "recipient LIKE ? AND active=?"
            where_args = (f"%{args.search.strip()}%", active)
        else:
            # 避免空条件报错
            where_str = "active=?"
            where_args = (active,)

        # 获取邮件类型
        typelist = self.get_mail_type_list(None)
        typelist = {str(item["id"]): item["mail_type"] for item in typelist}

        if 'etype' in args and args.etype != "":
            etype = int(args.etype)
            if where_str and where_args:
                where_str = "etype=? AND recipient LIKE? AND active=?"
                where_args = (etype, f"%{args.search.strip()}%", active)
            else:
                where_str = "etype=? AND active=?"
                where_args = (etype, active)

            with public.S("mail_unsubscribe", '/www/vmail/mail_unsubscribe.db') as obj:
                query = obj.where(where_str, where_args).group('recipient')
                count = query.select()
                data_list = obj.order('created', 'DESC').limit(rows, (p - 1) * rows).where(where_str, where_args).group(
                    'recipient').select()
                for i in data_list:
                    i['mail_type'] = []
                    etypes = obj.where('active', active).where('recipient', i['recipient']).field('etype').select()
                    # public.print_log(f'类型  {etypes}')
                    for j in etypes:
                        if typelist.get(str(j['etype']), None):
                            i['mail_type'].append({str(j['etype']): typelist[str(str(j['etype']))]})
                        else:
                            ...

            return self.return_msg({'data': data_list, 'total': len(count)})

        else:
            with public.S("mail_unsubscribe", '/www/vmail/mail_unsubscribe.db') as obj:
                count = obj.where(where_str, where_args).group('recipient').select()

                data_list = obj.order('created', 'DESC').limit(rows, (p - 1) * rows).where(where_str, where_args).group(
                    'recipient').select()
                for i in data_list:
                    i['mail_type'] = []
                    etypes = obj.where('active', active).where('recipient', i['recipient']).field('etype').select()
                    # public.print_log(f'类型  {etypes}')
                    for j in etypes:
                        if typelist.get(str(j['etype']), None):
                            i['mail_type'].append({str(j['etype']): typelist[str(str(j['etype']))]})
                        else:
                            ...
            return self.return_msg({'data': data_list, 'total': len(count)})

    def get_contacts_list(self, args):
        '''
        获取联系人列表 趋势图展示
        :param args: active  类型  0退订  1订阅
        :return:
        '''

        from datetime import datetime
        from collections import defaultdict

        active = args.active if 'active' in args else 0

        with public.S("mail_unsubscribe", '/www/vmail/mail_unsubscribe.db') as obj:
            query = obj.where('active', active).order('created', 'DESC').select()

        # 用于存储每个月的统计数据
        monthly_data = defaultdict(lambda: {'count': 0, 'month': ''})

        # 遍历数据，统计每个月的退订/订阅数量
        for record in query:
            created_timestamp = record['created']
            created_date = datetime.utcfromtimestamp(created_timestamp)
            year_month = created_date.strftime('%Y-%m')  # 获取年月，格式 '2024-12'
            monthly_data[year_month]['count'] += 1
            monthly_data[year_month]['month'] = year_month

        # 获取最新的月份
        if monthly_data:
            last_month = max(monthly_data.keys())
            last_month_date = datetime.strptime(last_month, '%Y-%m')
            # 确保结果数据包含过去12个月的数据
            result = self.complete_monthly_data(list(monthly_data.values()), last_month_date)

            return self.return_msg(result)
        else:
            return self.return_msg([])

    def complete_monthly_data(self, data, last_month_date):
        """ 补全12个月数据 """
        from datetime import datetime
        from collections import defaultdict
        from dateutil.relativedelta import relativedelta
        # 获取从 last_month_date 向前推12个月的数据
        months_list = []
        for i in range(12):
            # 使用 relativedelta 来往回推 i 个月
            month_date = last_month_date - relativedelta(months=i)  # 按月往回推
            months_list.append(month_date.strftime('%Y-%m'))  # 获取年月，格式 '2024-12'

        # 将原始数据存入一个字典，按月分组
        data_dict = {entry['month']: entry['count'] for entry in data}

        # 补全数据，若某个月没有数据，设置 count 为 0
        completed_data = []
        for month in months_list[::-1]:  # 倒序遍历，确保从最早的月份到最新的月份
            if month in data_dict:
                completed_data.append({'month': month, 'count': data_dict[month]})
            else:
                completed_data.append({'month': month, 'count': 0})

        return completed_data

    def edit_type_unsubscribe_list(self, args):
        """切换联系人的列表类型"""
        etypes_list = []
        recipients_list = []

        if "active" not in args or args.active == "":
            return self.return_msg(public.returnMsg(False, public.lang('缺少参数: active')))
        active = int(args.active)

        # 需要修改的类型
        if "etypes" in args and args.etypes != "":
            etypes_list = args.etypes.split(',')

        # 需要操作的 联系人
        if "recipients" in args and args.recipients != "":
            recipients_list = args.recipients.split(',')
        created = int(time.time())
        try:
            insert_data_alletype = []
            with public.S("mail_unsubscribe", "/www/vmail/mail_unsubscribe.db") as obj:
                # 删除已经存在的退订或订阅
                aa = obj.where('active', active).where_in('recipient', recipients_list).delete()

                for etype in etypes_list:
                    insert_data = []
                    for recipients in recipients_list:
                        insert_data.append({
                            'created': created,
                            'recipient': recipients,
                            'etype': int(etype),
                            'active': active,
                        })

                    insert_data_alletype += insert_data

                num = obj.insert_all(insert_data_alletype, option='IGNORE')

        except Exception as e:
            return self.return_msg(public.returnMsg(False, public.lang('错误: {}', e)))
        return self.return_msg(public.returnMsg(True, public.lang('类型修改成功')))

    def update_subscription_state(self, args):
        """切换订阅退订状态"""
        try:
            if "active" not in args or args.active == "":
                return public.returnMsg(False, public.lang('Missing parameter: active'))
            if "recipient" not in args or args.recipient == "":
                return public.returnMsg(False, public.lang('Missing parameter: recipient'))
            active = int(args.active)
            recipient = args.recipient
            with public.S("mail_unsubscribe", "/www/vmail/mail_unsubscribe.db") as obj:
                obj.where('recipient', recipient).update({'active': active})
        except Exception as e:
            return self.return_msg(public.returnMsg(False, public.lang('错误: {}', e)))
        return self.return_msg(public.returnMsg(True, public.lang('修改成功')))

    # 删除 批量删除
    def del_unsubscribe_list(self, args):
        try:
            if "active" not in args or args.active == "":
                return self.return_msg(public.returnMsg(False, public.lang('缺少参数: active')))
            active = int(args.active)
            if "ids" in args and args.ids != "":
                ids_list = args.ids.split(',')
                ids_list = [int(id_str) for id_str in ids_list]
                with public.S("mail_unsubscribe", "/www/vmail/mail_unsubscribe.db") as obj:
                    nums = obj.where('active', active).where_in('id', ids_list).column('id')
                    if len(nums) > 0:
                        delnum = obj.where('active', active).where_in('id', ids_list).delete()
        except Exception as e:
            return self.return_msg(public.returnMsg(False, public.lang('错误: {}', e)))
        return self.return_msg(public.returnMsg(True, public.lang('删除成功')))

    # 添加  测试用
    def add_unsubscribe1(self, args):
        # 使用默认邮件类型
        email = args.email
        etype = int(args.etype)

        try:

            for i in range(9):
                created = int(time.time())
                email = f"tet{i}@qq.cpm"
                insert = {
                    'created': created,
                    'recipient': email,
                    'etype': 8,
                }

                with self.MD("mail_unsubscribe", "mail_unsubscribe") as obj:
                    obj.insert(insert)
            return self.return_msg(True)
        except Exception as e:
            return self.return_msg(False)

    # todo  增加 active
    def add_unsubscribe(self, args):
        # 使用默认邮件类型
        email = args.emails
        etype = int(args.etype)
        emaillist = email.splitlines()
        active = int(args.active)

        try:
            insert_data = []
            for i in emaillist:
                created = int(time.time())
                email = i
                insert_data.append({
                    'created': created,
                    'recipient': email,
                    'etype': etype,
                    'active': active,
                })
            with public.S("mail_unsubscribe", '/www/vmail/mail_unsubscribe.db') as obj:
                num = obj.insert_all(insert_data, option='IGNORE')
                # num = obj.insert_all(insert_data)
            return self.return_msg(public.returnMsg(True, public.lang('添加成功', num)))

        except Exception as e:
            return self.return_msg(public.returnMsg(False, public.lang('添加失败 {}', e)))

    def get_mail_type_list(self, args):
        '''
        获取邮件类型列表
        :param args:
        :return:
        '''

        # 获取当前页的数据列表
        with self.M('mail_type') as obj:
            data_list = obj.order('created desc').select()

        return data_list

    def get_mail_type_info_list(self, args):
        '''
        获取邮件类型列表
        :param args: search  搜索
        :return:
        '''

        if "search" in args and args.search != "":
            where_str = "mail_type LIKE ?"
            where_args = (f"%{args.search.strip()}%")
        else:
            # 避免空条件报错
            where_str = "id!=?"
            where_args = (0,)
        p = int(args.p) if 'p' in args else 1
        rows = int(args.size) if 'size' in args else 10
        # 获取当前页的数据列表
        with self.M('mail_type') as obj:
            count = obj.order('created desc').where(where_str, where_args).count()
            data_list = obj.order('created desc').where(where_str, where_args).limit(rows, (p - 1) * rows).select()

        with public.S("mail_unsubscribe", '/www/vmail/mail_unsubscribe.db') as obj:
            etypes = obj.where('active', 1).group('etype').field('etype', 'count(*) as `cnt`').select()
            unetypes = obj.where('active', 0).group('etype').field('etype', 'count(*) as `cnt`').select()
        # public.print_log(f'etypes  111 {etypes}')
        etype_cnt = {}
        unetype_cnt = {}
        for i in etypes:
            etype_cnt[str(i['etype'])] = i['cnt']
        for i in unetypes:
            unetype_cnt[str(i['etype'])] = i['cnt']
        # import public.PluginLoader as plugin_loader
        # bulk = plugin_loader.get_module('{}/plugin/mail_sys/mail_send_bulk.py'.format(public.get_panel_path()))
        # SendMailBulk = bulk.SendMailBulk
        from mailModel.bulkModel import main as SendMailBulk

        url = SendMailBulk().get_unsubscribe_url()

        for i in data_list:
            i['subscribe_url'] = f"{url}/mailUnsubscribe?action=Subscribe&etype={i['id']}"
            i['subscribers'] = etype_cnt.get(str(i['id']), 0)
            i['unsubscribers'] = unetype_cnt.get(str(i['id']), 0)

        return self.return_msg({'data': data_list, 'total': count})

    # 删除邮件类型
    def del_mail_type_list(self, args):
        # 1 Default分类不能删    分类下有退订邮箱的不能删
        delnum = 0
        ids_err = 0
        if "ids" in args and args.ids != "":
            ids_list = args.ids.split(',')
            ids_list = [int(id_str) for id_str in ids_list if id_str != '1']
            ids_ok = []
            with self.MD("mail_unsubscribe", "mail_unsubscribe") as obj:
                for etype_id in ids_list:
                    count = obj.where('etype=?', etype_id).count()
                    if count > 0:
                        ids_err += 1
                    else:
                        ids_ok.append(etype_id)

            with public.S("mail_type", "/www/vmail/postfixadmin.db") as obj:
                nums = obj.where_in('id', ids_ok).column('id')
                if len(nums) > 0:
                    delnum = obj.where_in('id', ids_ok).delete()
        if delnum == 0 and ids_err == 0:
            return self.return_msg(public.returnMsg(False, public.lang('默认类型不能删除')))
        if ids_err > 0:
            return self.return_msg(public.returnMsg(True,
                                    public.lang('成功删除{}种类型,有{}种类型正在使用不能删除',
                                                delnum, ids_err)))
        return self.return_msg(public.returnMsg(True, public.lang('删除成功')))

    # 修改邮件类型
    def edit_mail_type(self, args):
        id = int(args.id)
        mail_type = args.mail_type

        if id == 1:
            return self.return_msg(public.returnMsg(False, public.lang('默认类型不能修改')))

        try:
            with self.M('mail_type') as obj:
                info = obj.where('id=?', id).update({"mail_type": mail_type})
            # return public.returnMsg(True, info)
            return self.return_msg(public.returnMsg(True, public.lang('修改成功')))
        except Exception as e:
            return self.return_msg(public.returnMsg(False, public.lang('错误: {}', e)))

    # 添加邮件类型
    def add_mail_type(self, args):
        mail_type = args.mail_type
        try:
            created = int(time.time())
            insert = {
                'created': created,
                'mail_type': mail_type,
            }

            with self.M('mail_type') as obj:
                exit = obj.where('mail_type =?', (mail_type,)).count()
                if exit:
                    return self.return_msg(public.returnMsg(False, public.lang('类型已存在')))
                obj.insert(insert)
            return self.return_msg(public.returnMsg(True, public.lang('添加成功')))
        except Exception as e:
            return self.return_msg(public.returnMsg(False, public.lang('添加失败 {}', e)))

    # 查看指定邮件类型
    def get_mail_type(self, args):
        id = args.id
        try:
            with self.M('mail_type') as obj:
                info = obj.where('id=?', id).find()
            return self.return_msg(public.returnMsg(True, info))
        except Exception as e:
            return self.return_msg(public.returnMsg(False, public.lang('错误: {}', e)))

    # 导出退订 (待定)
    def export_unsubscribe_list(self, args):
        # 数据库 存在数据 导出 格式{'0':[],'1':[],}
        ...

    # 导入退订 (匹配类型  如果没有类型的纯列表 使用默认类型) 兼容旧导出文件(待定)
    def import_unsubscribe_list(self, args):
        ...

    # ----------------------------------------------  批量发件 --------------------------------
    # 生成批量发件任务的数据库    兼容(如果查不到数据库 就从原始数据库中查
    # def Ms(self, table_name, db_path):
    #     import db
    #     sql = db.Sql()
    #     sql._Sql__DB_FILE = db_path
    #     sql._Sql__encrypt_keys = []
    #     return sql.table(table_name)
    def tables2(self, get):

        # 删除表
        # sql = '''DROP TABLE IF EXISTS `temp_email`;'''
        # self.M('').execute(sql, ())
        # sql = '''DROP TABLE IF EXISTS `email_task`;'''
        # self.M('').execute(sql, ())
        # sql = '''DROP TABLE IF EXISTS `task_count`;'''
        # self.M('').execute(sql, ())
        # sql = '''DROP TABLE IF EXISTS `mail_unsubscribe`;'''
        # self.M3('').execute(sql, ())
        # sql = '''DROP TABLE IF EXISTS `abnormal_recipient`;'''
        # with self.Ms('', '/www/vmail/abnormal_recipient.db') as obj:
        #     obj.execute(sql, ())
        ...

    def get_task_list(self, args):
        '''
        任务列表
        :param args:
        :return:
        '''
        # if not self.__check_auth():
        #     return self.return_msg(public.returnMsg(False, "此功能限企业版用户使用"))
        import PluginLoader
        args.model_index = 'mail'
        try:
            res = PluginLoader.module_run("bulk", "get_task_list", args)
            return self.return_msg(res)
        except Exception as ex:
            public.print_log(public.get_error_info())
            return self.return_msg({})

    # 查看任务是否要执行 定时任务调用 不改返回
    def check_task_status(self, args):
        '''
        执行发送邮件的定时任务
        :param
        :return:
        '''

        import PluginLoader
        args.model_index = 'mail'
        # 获取服务状态
        service_status = self.get_service_status(None)['data']
        if not service_status['postfix']:
            return self.return_msg(False)
        # 检测多个 SMTP 服务器的 25 端口是否可用
        if not self._check_smtp_port():
            return self.return_msg(False)

        try:
            res = PluginLoader.module_run("bulk", "check_task_status", args)
            return self.return_msg(res)
        except Exception as ex:
            public.print_log(public.get_error_info())
            return self.return_msg({})

    #  定时任务调用 不改返回
    def check_task_finish(self, args):
        '''
        发送完毕后处理发送失败的日志
        :param
        :return:
        '''

        import PluginLoader
        args.model_index = 'mail'
        try:
            res = PluginLoader.module_run("bulk", "check_task_finish", args)
            return self.return_msg(res)
        except Exception as ex:
            public.print_log(public.get_error_info())
            return self.return_msg({})

    def processing_recipient(self, args):
        '''
        导入收件人
        :param  file
        :return:
        '''

        import PluginLoader
        args.model_index = 'mail'

        try:
            res = PluginLoader.module_run("bulk", "processing_recipient", args)
            return self.return_msg(res)
        except Exception as ex:
            public.print_log(public.get_error_info())
            return self.return_msg({})

    def get_recipient_data(self, args):
        '''
        获取发送预计完成时间
        :param  file
        :return:
        '''

        import PluginLoader
        args.model_index = 'mail'
        try:
            res = PluginLoader.module_run("bulk", "get_recipient_data", args)
            return self.return_msg(res)
        except Exception as ex:
            public.print_log(public.get_error_info())
            return self.return_msg({})

    def add_task(self, args):
        '''
        添加批量发送任务
        :param args:
        :return:
        '''
        # if not self.__check_auth():
        #     return self.return_msg(public.returnMsg(False, "此功能限企业版用户使用"))
        import PluginLoader
        args.model_index = 'mail'
        try:
            res = PluginLoader.module_run("bulk", "add_task", args)
            return self.return_msg(res)
        except Exception as ex:
            public.print_log(public.get_error_info())
            return self.return_msg({})

    def pause_task(self, args):
        '''
        暂停发送任务   判断状态为执行中的可以暂停   task_process 1
        :param args: task_id 任务id;   pause 1暂停 0 重启
        :return:
        '''

        import PluginLoader
        args.model_index = 'mail'
        try:
            res = PluginLoader.module_run("bulk", "pause_task", args)
            return self.return_msg(res)
        except Exception as ex:
            public.print_log(public.get_error_info())
            return self.return_msg({})

    def delete_task(self, args):
        '''
        删除任务
        :param args: task_id 任务id
        :return:
        '''

        import PluginLoader
        args.model_index = 'mail'
        try:
            res = PluginLoader.module_run("bulk", "delete_task", args)
            return self.return_msg(res)
        except Exception as ex:
            public.print_log(public.get_error_info())
            return self.return_msg({})

    def get_log_rank(self, args):
        '''
        获取错误排行
        :param args: task_id 任务id
        :return:
        '''

        import PluginLoader
        args.model_index = 'mail'
        try:
            res = PluginLoader.module_run("bulk", "get_log_rank", args)
            return self.return_msg(res)
        except Exception as ex:
            public.print_log(public.get_error_info())
            return self.return_msg({})

    def get_log_list(self, args):
        '''
        获取错误详情
        :param args: task_id 任务id
        :return:
        '''
        import PluginLoader
        args.model_index = 'mail'
        try:
            res = PluginLoader.module_run("bulk", "get_log_list", args)
            return self.return_msg(res)
        except Exception as ex:
            public.print_log(public.get_error_info())
            return self.return_msg({})

    # 查看群发邮件的邮件内容/邮件路径
    def get_task_email_content(self, args):

        if 'id' in args and args.id != '':
            id = int(args.id)
        else:
            return public.returnMsg(False, public.lang('id必传'))

        email_info = self.M('temp_email').where('id=?', id).find()
        if not email_info:
            return public.returnMsg(False, public.lang('模板不存在'))

        content_path = email_info['content']
        render_path = email_info['render']
        type = email_info['type']
        if os.path.exists(content_path):
            content = public.readFile(content_path)
            # try:
            #     content = json.loads(content)
            # except:
            #     pass
        else:
            content = '{}文件不存在'.format(content_path)

        if type:
            if os.path.exists(render_path):
                render = public.readFile(render_path)
                # try:
                #     content = json.loads(render)
                # except:
                #     pass
            else:
                render = '{}文件不存在'.format(render_path)
        else:
            render = ''

        data = {
            'name': email_info['name'],
            'type': email_info['type'],
            'content_path': content_path,
            'content': content,
            'render_path': render_path,
            'render': render,
        }
        return self.return_msg(data)

    # 查看任务配置 传任务id
    def get_task_find(self, args):

        if 'id' in args and args.id != '':
            id = int(args.id)
        else:
            return public.returnMsg(False, public.lang('id必传'))
        # id = 17
        task_info = self.M('email_task').where('id=?', id).find()
        if not isinstance(task_info, dict):
            return public.returnMsg(False, task_info)
        email_info = self.M('temp_email').where('id=?', task_info['temp_id']).find()

        data = {
            "task_info": task_info,
            "email_info": email_info,
        }

        return self.return_msg(data)

    def update_task(self, args):
        '''
        修改发送任务
        :param args:
        :return:
        '''
        # if not self.__check_auth():
        #     return public.returnMsg(False, public.lang("Sorry. This feature is professional member only."))
        import public.PluginLoader as plugin_loader
        bulk = plugin_loader.get_module('{}/plugin/mail_sys/mail_send_bulk.py'.format(public.get_panel_path()))
        SendMailBulk = bulk.SendMailBulk
        try:
            return SendMailBulk().update_task(args)
        except Exception as ex:
            public.print_log(public.get_error_info())
            return {}

    # 获取当天日志详情
    def get_data_info(self, args):
        now = datetime.now()

        # 将时间调整为当天的开始时间（零点）
        today_start = datetime(now.year, now.month, now.day)

        # 将当天的开始时间转换为时间戳
        start = int(today_start.timestamp())
        end = start + 86400
        # 取缓存
        cache_key = 'mail_sys:get_day_errlog_{}'.format(start)
        cache = public.cache_get(cache_key)
        if cache:
            return self.return_msg(cache)
        try:

            with self.MD("mail_errlog", "postfixmaillog") as obj2:
                # query1 = obj2.order('created desc').where('created >? AND created<?', (start, end)).count()
                query = obj2.order('created desc').where('created >? AND created<?', (start, end)).select()


        except:
            public.print_log(public.get_error_info())

        # 缓存
        public.cache_set(cache_key, query, 30 * 60)

        return self.return_msg(query)

    # 弃用
    def _get_errlist(self, timestamp):
        '''
        获取错误详情
        :return:
        '''

        start = int(timestamp)
        end = int(timestamp) + 3599
        # 当前小时以后的不获取   3点半   3-4点v  4-5x
        current_time = int(time.time())
        if current_time < start:
            return []

        # 取缓存
        cache_key = 'mail_sys:get_errlog_{}'.format(timestamp)
        cache = public.cache_get(cache_key)
        if cache:
            return cache
        try:
            with self.MD("mail_errlog", "postfixmaillog") as obj2:
                query = obj2.order('created desc').where('created >? AND created<?', (start, end)).select()
        except:
            public.print_log(public.get_error_info())

        # 缓存
        if current_time > end:
            public.cache_set(cache_key, query, 60 * 60 * 24)
        else:
            public.cache_set(cache_key, query, 30 * 60)

        return query

    def task_cut_maillog(self):
        cmd = '''
        if pgrep -f "cut_maillog.py" > /dev/null
        then
            echo "The task [Cut_maillog] is executing"
            exit 1;
        else
            btpython /www/server/panel/class/mailModel/script/cut_maillog.py
        fi
        '''

        import crontab
        p = crontab.crontab()
        try:
            c_id = public.M('crontab').where('name=?', u'[勿删] 切割邮件日志').getField('id')
            if not c_id:
                data = {}
                data['name'] = u'[勿删] 切割邮件日志'
                data['type'] = 'hour-n'
                data['where1'] = '1'
                data['sBody'] = 'btpython /www/server/panel/class/mailModel/script/cut_maillog.py'
                data['backupTo'] = ''
                data['sType'] = 'toShell'
                data['hour'] = ''
                data['minute'] = '0'
                data['week'] = ''
                data['sName'] = ''
                data['urladdress'] = ''
                data['save'] = ''
                p.AddCrontab(data)
                return public.returnMsg(True, '设置成功!')
            # else:
            #     Cut_maillog = public.M('crontab').where('id=?', c_id).find()
            #     if Cut_maillog['sBody'].find("pgrep -x") == -1:
            #         public.M('crontab').where('id=?', c_id).delete()
        except Exception as e:
            public.print_log(public.get_error_info())

    # 设置邮件取消订阅所用到的域名端口号
    def set_unsubscribe_info(self, args):
        path_info = {}
        if os.path.exists(self.unsubscribe_path):
            path_info = json.loads(public.readFile(self.unsubscribe_path))

        if 'url' in args and args.url != '':
            # 检查访问是否成功
            url = args.url
            td = "{}/mailUnsubscribe".format(url)

            try:
                testdata = public.httpGet(td)
                public.print_log(testdata)
                try:
                    testdata = json.loads(testdata)
                except:
                    pass
                if isinstance(testdata, dict):
                    # public.print_log(testdata['status'])
                    # public.print_log(testdata)

                    if testdata['status'] == 0:

                        path_info['url'] = url
                    else:
                        return self.return_msg(public.returnMsg(False, public.lang(
                            '当前url无法访问，请正确设置反向代理!')))
                else:
                    return self.return_msg(public.returnMsg(False, public.lang(
                        '当前url无法访问，请正确设置反向代理!!')))
            except Exception as e:
                return self.return_msg(public.returnMsg(False, e))
        public.writeFile(self.unsubscribe_path, json.dumps(path_info))
        # public.set_module_logs('mailModel', 'set_unsubscribe_info', 1)

        return self.return_msg(public.returnMsg(True, public.lang('设置成功!')))

    # 查看
    def get_unsubscribe_info(self, args):
        # 面板默认
        ssl_staus = public.readFile('/www/server/panel/data/ssl.pl')
        if ssl_staus:
            ssl = 'https'
        else:
            ssl = 'http'

        ip = public.readFile("/www/server/panel/data/iplist.txt")
        port = public.readFile('/www/server/panel/data/port.pl')
        panel_url = "{}://{}:{}".format(ssl, ip, port)

        if os.path.exists(self.unsubscribe_path):
            path_info = json.loads(public.readFile(self.unsubscribe_path))
            url = path_info.get('url', '')
        else:
            url = ''

        data = {
            "url": url,
            "panel_url": panel_url
        }

        return self.return_msg(public.returnMsg(True, data))

    # 删除
    def del_unsubscribe_info(self, args):
        if os.path.exists(self.unsubscribe_path):
            os.remove(self.unsubscribe_path)

        return self.return_msg(public.returnMsg(True, public.lang('删除成功')))

    def __check_auth(self):
        # 检测是否为专业pro版
        from plugin_auth_v2 import Plugin as Plugin
        plugin_obj = Plugin(False)
        plugin_list = plugin_obj.get_plugin_list()
        # 检测是否为专业永久版
        import PluginLoader
        self.__IS_PRO_MEMBER = PluginLoader.get_auth_state() > 0
        return int(plugin_list["pro"]) > time.time() or self.__IS_PRO_MEMBER

    def modify_domain_quota(self, args):
        if not hasattr(args, "path"):  # /www/vmail/kern123.top
            return self.return_msg(public.returnMsg(False, "缺少参数！path"))
        if not hasattr(args, "quota_type"):  # mail
            return self.return_msg(public.returnMsg(False, "缺少参数！quota_type"))
        if not hasattr(args, "quota_storage"):
            return self.return_msg(public.returnMsg(False, "缺少参数！quota_storage"))

        quota_type = args.quota_type
        if not isinstance(args.quota_storage, dict):
            return self.return_msg(public.returnMsg(False, "参数错误！ quota_storage"))
        path = args.path
        path = str(path).rstrip("/")
        if not os.path.exists(path):
            return self.return_msg(public.returnMsg(False, "指定目录不存在"))
        if os.path.isfile(path):
            return self.return_msg(public.returnMsg(False, "这不是一个有效的目录!"))
        if os.path.islink(path):
            return self.return_msg(public.return_message(False, "指定的目录是软链接!"))
        if not os.path.isdir(path):
            return self.return_msg(public.returnMsg(False, "这不是一个有效的目录！"))

        return self.return_msg(self.modify_path_quota(args))

        ...

    def modify_path_quota(self, args):
        # {"path":"/www/wwwroot/aa.dd.com","quota_type":"site",
        # "quota_push":{"module":"","status":false,"size":0,"push_count":0},
        # "quota_storage":{"size":1000}}
        # if not hasattr(args, "path"):  # /www/vmail/kern123.top
        #     return public.return_message(-1, 0, "missing parameter!path")
        # if not hasattr(args, "quota_type"): # mail
        #     return public.return_message(-1, 0, "missing parameter!quota_type")
        # # if not hasattr(args, "quota_push"):
        # #     return public.return_message(-1, 0, "missing parameter!quota_push")
        # if not hasattr(args, "quota_storage"):
        #     return public.return_message(-1, 0, "missing parameter!quota_storage")
        #
        # quota_type = args.quota_type
        # # if not isinstance(args.quota_push, dict):
        # #     return public.return_message(-1, 0, "parameter error! quota_push")
        # if not isinstance(args.quota_storage, dict):
        #     return public.return_message(-1, 0,
        #                                  "parameter error! quota_storage")
        # # if quota_type not in ["site", "ftp", "path"]:
        # #     return public.return_message(-1, 0, "parameter error!quota_type")
        # # if args.quota_push.get("status", False) is True:
        # #     args.quota_push["module"] = args.quota_push.get("module",
        # #                                                     "").strip(",")
        # #     if not args.quota_push["module"]:
        # #         return public.return_message(
        # #             -1, 0, "Please select a push message channel!")
        # path = args.path
        # path = str(path).rstrip("/")
        # public.print_log('path-- {}'.formar(path))
        # if not os.path.exists(path):
        #     return public.return_message(
        #         -1, 0, "The specified directory does not exist")
        # if os.path.isfile(path):
        #     return public.return_message(-1, 0,
        #                                  "this is not a valid directory!")
        # if os.path.islink(path):
        #     return public.return_message(
        #         -1, 0, "The specified directory is a soft link!")
        # if not os.path.isdir(path):
        #     return public.return_message(-1, 0,
        #                                  "this is not a valid directory!")
        path = args.path
        path = str(path).rstrip("/")
        quota_type = args.quota_type
        quota_dict = self.__get_quota_list()

        if quota_dict.get(path) is not None:
            # if quota_dict[path]["quota_type"] == "database":
            #     return public.return_message(
            #         -1, 0, "The path has been set with database quota!")
            quota = quota_dict[path]
            quota["quota_push"]["size"] = int(args.quota_push.get("size", 0))
            quota["quota_push"]["interval"] = int(
                args.quota_push.get("interval", 600))
            quota["quota_push"]["module"] = args.quota_push["module"]
            quota["quota_push"]["push_count"] = int(
                args.quota_push.get("push_count", 3))
            quota["quota_push"]["status"] = args.quota_push.get(
                "status", False)
            quota["quota_storage"]["size"] = int(
                args.quota_storage.get("size", 0))
        else:
            quota = {
                "id": self.__get_quota_id(quota_dict),
                "quota_type": quota_type,
                "quota_push": {
                    "size": int(args.quota_push.get("size", 0)),
                    "interval": int(args.quota_push.get("interval", 600)),
                    "module": args.quota_push.get("module", ""),
                    "push_count": int(args.quota_push.get("push_count", 3)),
                    "status": args.quota_push.get("status", False),
                },
                "quota_storage": {
                    "size": int(args.quota_storage.get("size", 0)),
                },
            }

        if quota["quota_storage"]["size"] > 0:
            disk = self.__get_path_dev_mountpoint(path)
            if disk is None:
                return self.return_msg(public.returnMsg(
                    False,
                    "指定目录所在的分区不是 XFS 分区，且不支持目录配额！"
                ))

            if "prjquota" not in disk["opts"]:
                msg = '<div class="ftp-verify-disk">指定的 xfs 分区未启用目录配额。请在挂载该分区时添加 `prjquota` 参数。 <p>/etc/fstab 示例文件配置：</p><pre>{device} {mountpoint} xfs defaults,prjquota 0 0</pre><p>注意：配置后，需要重新挂载分区或重启服务器以使配置生效。</p></div>'.format(
                    device=disk["device"], mountpoint=disk["mountpoint"])
                return self.return_msg(public.returnMsg(False, msg))

            if args.quota_storage.get("size", 0) * 1024 * 1024 > disk["free"]:
                return self.return_msg(public.returnMsg(
                    False,
                    "指定磁盘的可用配额容量不足!"
                ))

            res = public.ExecShell(
                "xfs_quota -x -c 'project -s -p {path} {quota_id}'".format(
                    path=path, quota_id=quota["id"]))
            if res[1]:
                return self.return_msg(public.returnMsg(
                    False, "配额设置错误!{}".format(res[1])))
            res = public.ExecShell(
                "xfs_quota -x -c 'limit -p bhard={size}m {quota_id}' {mountpoint}"
                .format(size=quota["quota_storage"]["size"],
                        quota_id=quota["id"],
                        mountpoint=disk["mountpoint"]))
            if res[1]:
                return self.return_msg(public.returnMsg(
                    False, "配额设置错误!{}".format(res[1])))

        self.__set_push(quota)

        quota_dict[path] = quota
        public.WriteLog(
            "配额",
            "设置目录[{path}]的配额限制为: {size}MB".format(
                path=path, size=quota["quota_storage"]["size"]))
        public.writeFile(self.__SETTINGS_FILE, json.dumps(quota_dict))
        return self.return_msg(public.returnMsg(True, "修改成功"))

    # 处理计划任务重复
    def remove_old_cron(self):
        # 没初始化跳过
        if not os.path.exists('/www/vmail'):
            return
        # 判断删掉标记 如果不存在 就删掉就任务
        path = '/www/server/panel/data/remove_old_mail_cron.pl'
        if os.path.exists(path):
            return
        # 判断已经存在任务
        c_id = public.M('crontab').where('name=?', u'[勿删] 切割邮件日志').getField('id')
        if not c_id:
            return
        target_list = ['cut_maillog.py', 'send_bulk_script.py', 'mail_error_logs.py']
        cron_jobs = public.ExecShell("crontab -l")
        # 要删除的旧任务
        script_path_list = []
        if cron_jobs:
            # 提取cron任务中的所有脚本路径
            script_paths = self.find_script_paths(cron_jobs)

            # 查找每个脚本文件是否包含目标字符串
            for script_path in script_paths:
                if self.search_in_file(script_path, target_list):
                    script_path_list.append(script_path)

        import crontab
        p = crontab.crontab()
        try:
            # 删除多余任务
            for echo_path in script_path_list:
                echo = echo_path.split('/')[-1]

                p.remove_for_crond(echo)
                if os.path.exists(echo_path): os.remove(echo_path)
                sfile = echo_path + '.log'
                if os.path.exists(sfile): os.remove(sfile)
        except:
            pass
        try:
            # 删除
            c_id = public.M('crontab').where('name=?', u'[勿删] 检查发送结果').getField('id')
            if c_id:
                a = p.DelCrontab({"id": c_id})

            s_id = public.M('crontab').where('name=?', u'[勿删] 群发邮件任务').getField('id')
            if s_id:
                b = p.DelCrontab({"id": s_id})
                # public.print_log("b --{}".format(b))
            m_id = public.M('crontab').where('name=?', u'[勿删] 切割邮件日志').getField('id')
            if m_id:
                c = p.DelCrontab({"id": m_id})
                # public.print_log("c --{}".format(c))
        except:
            public.print_log(public.get_error_info())

        # 记录删除标记
        public.writeFile(path, "")
        return

    def search_in_file(self, file_path, target_list):
        """检查脚本文件中是否包含目标字符串"""
        if not os.path.exists(file_path):
            return False
        if not os.path.isfile(file_path):  # 检查是否是文件
            return False
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        for target in target_list:
            if target in content:
                return True
        return False

    def find_script_paths(self, cron_jobs):
        """从cron任务中提取出所有的脚本路径"""
        script_paths = []
        lines = cron_jobs[0].split("\n")

        path_pattern = re.compile(r'(/\S+)(?=\s*(?:>>|\s*$))')
        for line in lines:
            if not line:
                continue
            match = path_pattern.search(line)
            if match:
                script_paths.append(match.group(1))

        return script_paths

    def _get_user_quota(self, ):
        '''

        :return:
        '''
        import public.PluginLoader as plugin_loader
        bulk = plugin_loader.get_module('{}/plugin/mail_sys/mail_send_bulk.py'.format(public.get_panel_path()))
        SendMailBulk = bulk.SendMailBulk
        try:
            return SendMailBulk()._get_user_quota()
        except Exception as ex:
            public.print_log(public.get_error_info())
            return {}

    def import_contacts(self, args):
        '''
        导入收件人到联系人列表
        :param  file        str (收件人文件名)
        :param  etypes      str (联系人类型  多个逗号隔开)  多选分类  每个分类都导入
        :param  active      int (0 退订    1订阅)  暂不使用,默认订阅类型
        :return:
        '''
        import public.PluginLoader as plugin_loader
        bulk = plugin_loader.get_module('{}/plugin/mail_sys/mail_send_bulk.py'.format(public.get_panel_path()))
        SendMailBulk = bulk.SendMailBulk
        try:
            return SendMailBulk().import_contacts(args)
        except Exception as ex:
            public.print_log(public.get_error_info())
            return {}

    def import_contacts_etypes(self, args):
        '''
        导入收件人到联系人列表
        :param  file        str (收件人文件名)
        :param  etypes      str (联系人类型  多个逗号隔开)  多选分类  每个分类都导入
        :param  active      int (0 退订    1订阅)  暂不使用,默认订阅类型
        :return:
        '''
        import public.PluginLoader as plugin_loader
        bulk = plugin_loader.get_module('{}/plugin/mail_sys/mail_send_bulk.py'.format(public.get_panel_path()))
        SendMailBulk = bulk.SendMailBulk
        try:
            return SendMailBulk().import_contacts_etypes(args)
        except Exception as ex:
            public.print_log(public.get_error_info())
            return {}

    def get_email_temp_list(self, args):
        '''
        邮件模版列表
        :param
        :return:
        '''
        import mod.base.public_aap.PluginLoader as plugin_loader
        bulk = plugin_loader.get_module('{}/plugin/mail_sys/mail_send_bulk.py'.format(public.get_panel_path()))
        SendMailBulk = bulk.SendMailBulk
        try:
            return SendMailBulk().get_email_temp_list(args)
        except Exception as ex:
            public.print_log(public.get_error_info())
            return {}

    def get_email_temp_render(self, args):
        '''
        邮件模版列表
        :param
        :return:
        '''
        import public.PluginLoader as plugin_loader
        bulk = plugin_loader.get_module('{}/plugin/mail_sys/mail_send_bulk.py'.format(public.get_panel_path()))
        SendMailBulk = bulk.SendMailBulk
        try:
            return SendMailBulk().get_email_temp_render(args)
        except Exception as ex:
            public.print_log(public.get_error_info())
            return {}

    def get_email_temp(self, args):
        '''
        邮件模版列表
        :param
        :return:
        '''
        import public.PluginLoader as plugin_loader
        bulk = plugin_loader.get_module('{}/plugin/mail_sys/mail_send_bulk.py'.format(public.get_panel_path()))
        SendMailBulk = bulk.SendMailBulk
        try:
            return SendMailBulk().get_email_temp(args)
        except Exception as ex:
            public.print_log(public.get_error_info())
            return {}

    def add_email_temp(self, args):
        '''
        邮件模版列表
        :param
        :return:
        '''
        import public.PluginLoader as plugin_loader
        bulk = plugin_loader.get_module('{}/plugin/mail_sys/mail_send_bulk.py'.format(public.get_panel_path()))
        SendMailBulk = bulk.SendMailBulk
        try:
            return SendMailBulk().add_email_temp(args)
        except Exception as ex:
            public.print_log(public.get_error_info())
            return {}

    def del_email_temp(self, args):
        '''
        邮件模版列表
        :param
        :return:
        '''
        import public.PluginLoader as plugin_loader
        bulk = plugin_loader.get_module('{}/plugin/mail_sys/mail_send_bulk.py'.format(public.get_panel_path()))
        SendMailBulk = bulk.SendMailBulk
        try:
            return SendMailBulk().del_email_temp(args)
        except Exception as ex:
            public.print_log(public.get_error_info())
            return {}

    def edit_email_temp(self, args):
        '''
        邮件模版列表
        :param
        :return:
        '''
        import public.PluginLoader as plugin_loader
        bulk = plugin_loader.get_module('{}/plugin/mail_sys/mail_send_bulk.py'.format(public.get_panel_path()))
        SendMailBulk = bulk.SendMailBulk
        try:
            return SendMailBulk().edit_email_temp(args)
        except Exception as ex:
            public.print_log(public.get_error_info())
            return {}

    # 检测域名是否在黑名单
    def check_blacklists(self, args):
        '''
        邮件模版列表
        :param
        :return:
        '''
        import public.PluginLoader as plugin_loader
        bulk = plugin_loader.get_module('{}/plugin/mail_sys/mail_send_bulk.py'.format(public.get_panel_path()))
        SendMailBulk = bulk.SendMailBulk
        try:
            return SendMailBulk().check_blacklists(args)
        except Exception as ex:
            public.print_log(public.get_error_info())
            return {}

    # 设置忽略提示
    def Blacklist_tips(self, args):
        '''
        操作黑名单提示横幅
        :param operation  (-1 忽略   >0 已处理)
        :return:
        '''
        path = self.blacklist_tips
        operation = str(args.operation)

        # 测试用
        if operation == '0':
            if os.path.exists(path):
                # public.print_log('删除标记')
                os.remove(path)
                return self.return_msg(public.returnMsg(True, public.lang("操作成功")))

        if operation == '-1':
            oper = -1
        else:
            oper = int(time.time())
        public.writeFile(path, str(oper))
        return self.return_msg(public.returnMsg(True, public.lang("操作成功")))

    # 获取忽略提示设置
    def get_blacklist_tips(self, args):
        '''
        获取操作黑名单提示横幅处理状态 -1 忽略  0 未操作   >0 已处理
        :param
        :return:
        '''
        path = self.blacklist_tips
        if os.path.exists(path):
            data = public.readFile(path)
            if not data:
                data = 0
        else:
            data = 0

        blcheck_count = f'/www/server/panel/plugin/mail_sys/data/blcheck.json'  # 统计各个域名黑名单情况

        if os.path.exists(blcheck_count):
            blcheck_ = public.readFile(blcheck_count)
            try:
                blcheck_ = json.loads(blcheck_)
            except:
                pass
            count = sum(info["blacklisted"] for info in blcheck_.values())
        else:
            count = 0

        res = {
            'status': data,
            'count': count,
        }

        return self.return_msg(res)

    def _get_alarm_black_switch(self):
        '''
        获取自动检测黑名单告警开关
        :param
        :return:
        '''

        # endtime = public.get_pd()[1]
        # curtime = int(time.time())
        # if endtime != 0 and endtime < curtime:
        #     # 无专业版或永久版
        #     return False
        # else:
        path = self.blacklist_alarm_switch
        if os.path.exists(path):
            return False
        else:
            return True

    def set_alarm_black_switch(self, args):
        '''
        设置自动检测黑名单告警开关
        :param  type str     'black'
        :return:
        '''
        operation = str(args.operation)

        # endtime = public.get_pd()[1]
        # curtime = int(time.time())
        # if endtime != 0 and endtime < curtime:
        #     return public.returnMsg(False, public.lang('This feature is exclusive to the Pro version'))

        # 检查文件(存在关)
        path = self.blacklist_alarm_switch
        if operation == '1':
            if os.path.exists(path):
                os.remove(path)
        # 关
        else:
            public.writeFile(path, '1')

        public.set_module_logs('mailModel', 'set_alarm_black_switch', 1)
        return self.return_msg(public.returnMsg(True, public.lang("操作成功")))

    def get_alarm_send(self, args):
        '''
        获取服务掉线监控告警任务
        :param
        :return:
        '''
        import public.PluginLoader as plugin_loader
        bulk = plugin_loader.get_module('{}/plugin/mail_sys/mail_send_bulk.py'.format(public.get_panel_path()))
        SendMailBulk = bulk.SendMailBulk
        try:
            return SendMailBulk().get_alarm_send(args)
        except Exception as ex:
            public.print_log(public.get_error_info())
            return {}

    # 导出模版
    def export_email_template(self, args):
        '''
        导出邮件模版
        :param
        :return:
        '''
        import public.PluginLoader as plugin_loader
        bulk = plugin_loader.get_module('{}/plugin/mail_sys/mail_send_bulk.py'.format(public.get_panel_path()))
        SendMailBulk = bulk.SendMailBulk
        try:
            return SendMailBulk().export_email_template(args)
        except Exception as ex:
            public.print_log(public.get_error_info())
            return {}

    # 导入模版
    def import_email_template(self, args):
        '''
        导入邮件模版
        :param
        :return:
        '''
        import public.PluginLoader as plugin_loader
        bulk = plugin_loader.get_module('{}/plugin/mail_sys/mail_send_bulk.py'.format(public.get_panel_path()))
        SendMailBulk = bulk.SendMailBulk
        try:
            return SendMailBulk().import_email_template(args)
        except Exception as ex:
            public.print_log(public.get_error_info())
            return {}

    def read_blacklist_scan_log(self, args):
        '''
        读取黑名单扫描日志
        :param
        :return:
        '''

        if not os.path.exists(args.path):
            return public.return_message(-1, 0, public.lang("配置文件不存在"))
        if os.path.isdir(args.path):
            return public.return_message(-1, 0, public.lang("验证文件写入失败: {}"))

        import files
        f = files.files()
        public.set_module_logs('mailModel', 'read_blacklist_scan_log', 1)
        return self.return_msg(f.GetFileBody(args))

    def get_contact_number(self, args):
        '''
        获取多个分组下的收件人数量
        :param   str  etypes  分组类型   1,3,4
        :return: int  数量
        '''
        if not hasattr(args, 'etypes') or args.get('etypes', '') == '':
            return self.return_msg(0)
        else:
            etypes = args.etypes

        etype_list = etypes.split(',')

        with public.S("mail_unsubscribe", '/www/vmail/mail_unsubscribe.db') as obj:
            email_list = obj.where_in('etype', etype_list).where('active', 1).select()
        emails = [i['recipient'] for i in email_list]
        # 不同组有相同邮件 去重
        count = len(list(set(emails)))

        return self.return_msg(count)

    def auto_create_dns_record(self, args):
        """
        自动创建域名的dns记录
        @param args:
        @return:
        """
        try:
            # item['dkim_value'] = self._get_dkim_value(item['domain'])
            # item['dmarc_value'] = 'v=DMARC1;p=quarantine;rua=mailto:admin@{0}'.format(item['domain'])
            # item['mx_record'] = item['a_record']

            # # 清除缓存
            # self.delete_mx_txt_cache(args)
            # 查看记录是否存在
            item = self.get_record_in_cache(args.__dict__)
            from sslModel import dataModel
            dataModel.main()
            result = []
            if item['mx_status'] != 1:
                try:
                    dataModel.main().add_dns_value_by_domain(args.domain, args.a_record, "MX")
                    result.append({"name": "MX", "status": 1, "msg": "添加成功"})
                except Exception as e:
                    result.append({"name": "MX", "status": 0, "msg": str(e)})
            if item['spf_status'] != 1:
                try:
                    dataModel.main().add_dns_value_by_domain(args.domain, "v=spf1 a mx ~all", "TXT")
                    result.append({"name": "SPF", "status": 1, "msg": "添加成功"})
                except Exception as e:
                    result.append({"name": "SPF", "status": 0, "msg": str(e)})
            if item['dkim_status'] != 1:
                try:
                    dataModel.main().add_dns_value_by_domain("default._domainkey."+args.domain, self._get_dkim_value(args.domain).strip(), "TXT")
                    result.append({"name": "DKIM", "status": 1, "msg": "添加成功"})
                except Exception as e:
                    result.append({"name": "DKIM", "status": 0, "msg": str(e)})
            if item['dmarc_status'] != 1:
                try:
                    dataModel.main().add_dns_value_by_domain("_dmarc."+args.domain, 'v=DMARC1;p=quarantine;rua=mailto:admin@{0}'.format(args.domain), "TXT")
                    result.append({"name": "DMARC", "status": 1, "msg": "添加成功"})
                except Exception as e:
                    result.append({"name": "DMARC", "status": 0, "msg": str(e)})
            if item['a_status'] != 1:
                try:
                    dataModel.main().add_dns_value_by_domain(args.a_record, public.get_server_ip(), "A")
                    result.append({"name": "A", "status": 1, "msg": "添加成功"})
                except Exception as e:
                    result.append({"name": "A", "status": 0, "msg": str(e)})
            result = {"data": result}
            return self.return_msg(public.returnMsg(True, result))
        except Exception as e:
            public.print_log(public.get_error_info())
            return self.return_msg(public.returnMsg(False, '自动创建域名DNS记录失败! {}'.format(e)))

    # 打开数据备份任务
    def open_auto_ssl_task(self, get):
        import crontab
        import random
        p = crontab.crontab()

        try:

            c_id = public.M('crontab').where('name=?', u'[勿删] 堡塔邮局-证书自动续签').getField('id')
            if c_id:
                data = {}
                data['id'] = c_id
                data['name'] = u'[勿删] 堡塔邮局-证书自动续签'
                data['type'] = 'day'
                data['where1'] = '1'
                data['sBody'] = '/www/server/panel/pyenv/bin/python3 -u /www/server/panel/class/mailModel/script/auto_renew_letssl.py'
                data['backupTo'] = ''
                data['sType'] = 'toShell'
                data['hour'] = random.randint(0, 23)
                data['minute'] = random.randint(0, 59)
                data['week'] = ''
                data['sName'] = ''
                data['urladdress'] = ''
                data['save'] = ''
                p.modify_crond(data)
                return self.return_msg(public.returnMsg(True, '编辑成功!'))
            else:
                data = {}
                data['name'] = u'[勿删] 堡塔邮局-证书自动续签'
                data['type'] = 'day'
                data['where1'] = '1'
                data['sBody'] = '/www/server/panel/pyenv/bin/python3 -u /www/server/panel/class/mailModel/script/auto_renew_letssl.py'
                data['backupTo'] = ''
                data['sType'] = 'toShell'
                data['hour'] = random.randint(0, 23)
                data['minute'] = random.randint(0, 59)
                data['week'] = ''
                data['sName'] = ''
                data['urladdress'] = ''
                data['save'] = ''
                p.AddCrontab(data)
                return self.return_msg(public.returnMsg(True, '设置成功!'))
        except Exception as e:
            public.print_log(public.get_error_info())

    # 关闭数据备份任务
    def close_auto_ssl_task(self, get):
        import crontab

        p = crontab.crontab()
        c_id = public.M('crontab').where('name=?', u'[勿删] 堡塔邮局-证书自动续签').getField('id')
        if not c_id: return self.return_msg(public.returnMsg(False, '定时任务不存在!'))
        args = {"id": c_id}
        p.DelCrontab(args)
        return self.return_msg(public.returnMsg(True, '关闭成功!'))

    def get_auto_ssl_task_status(self, get):
        import crontab

        p = crontab.crontab()
        c_id = public.M('crontab').where('name=?', u'[勿删] 堡塔邮局-证书自动续签').getField('id')
        if not c_id: return self.return_msg(public.returnMsg(False, '定时任务不存在!'))
        args = {"id": c_id}
        status = p.GetCrontab(args)
        if status:
            return self.return_msg(public.returnMsg(True, '定时任务已开启!'))
        else:
            return self.return_msg(public.returnMsg(False, '定时任务已关闭!'))


    def overview_api(self, get):
        import importlib
        module = importlib.import_module("mailModel.power_mta.actions")
        query = request.args
        if not query.get("action"):
            return public.returnMsg(False, "参数错误")
        action = query['action']
        get = public.to_dict_obj(vars(get))
        method = getattr(module, action)
        return method(get)

    def set_cert_from_local(self, args):
        from sslModel import certModel
        data = certModel.main().get_cert_content(args)
        if not data['status']:
            return data
        args.key = data['content']['key']
        args.csr = data['content']['cert']
        args.act = 'add'
        return self.set_mail_certificate_multiple(args)

    def get_task_unsubscribe_list(self,args):
        """ 获取营销任务 退订详情列表 """
        p = int(args.p) if 'p' in args else 1
        rows = int(args.size) if 'size' in args else 12

        task_id = args.get('task_id', '')
        if not task_id:
            return public.return_message(-1, 0, public.lang("The required id parameter is missing"))
        with public.S("mail_unsubscribe", '/www/vmail/mail_unsubscribe.db') as obj:
            count = obj.where('task_id', task_id).select()
            # 获取不重复数据
            data1 = obj.order('created', 'DESC').where('active', 0).limit(rows, (p - 1) * rows).where('task_id', task_id).group('recipient').select()
            # 获取最新时间
            data2 = obj.order('created', 'DESC').where('active', 0).limit(rows, (p - 1) * rows).where('task_id', task_id).select()
            result = {}

            data = data1 + data2
            # 遍历合并后的数据
            for entry in data:
                recipient = entry['recipient']
                created = entry['created']

                # 如果该 recipient 不在结果中，或者当前的 created 更大，则更新
                if recipient not in result or created > result[recipient]['created']:
                    result[recipient] = entry

            # 将结果转换为列表
            data = list(result.values())

        return {'data': data, 'total': len(count)}
