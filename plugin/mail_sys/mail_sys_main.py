#!/usr/bin/python
#coding: utf-8

import sys
import os
import json
import re
import traceback
from datetime import datetime
import dns.resolver
import binascii
import base64

if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')

sys.path.append("class/")
import public


class mail_sys_main:
    __setupPath = 'plugin/mail_sys'
    __download_conf_url = public.get_url()

    def check_mail_sys(self, args):
        if os.path.isdir('/www/vmail'):
            return public.returnMsg(True, '邮局系统已经存在，重装之前请先卸载!')
        else:
            return public.returnMsg(False, '之前没有安装过邮局系统，请放心安装!')

    # 安装并配置postfix, dovecot
    def setup_mail_sys(self, args):
        '''
        安装邮局系统主函数
        :param args:
        :return:
        '''
        hostname = args.hostname
        if not self._check_a(hostname):
            return public.returnMsg(False, '检测A记录失败!')
        if not self._check_smtp_port():
            return public.returnMsg(False, '部分云厂商(如：阿里云，腾讯云)默认关闭25端口，需联系厂商开通25端口后才能正常使用邮局服务')

        self._prepare_work(hostname)
        self._setup_postfix()
        self._setup_dovecot()

        return public.returnMsg(True, '安装成功!')

    def _check_smtp_port(self):
        import telnetlib

        host_list = ['mx1.qq.com', 'mx2.qq.com', 'mx3.qq.com']
        for host in host_list:
            try:
                tn = telnetlib.Telnet(host, 25, timeout=1)
                if tn: return True
            except:
                continue
        return False

    def get_a_cache(self, args):
        from BTPanel import session

        if 'hostname' not in args:
            return public.returnMsg(False, '请传入主机域名')
        hostname = args.hostname

        key = '{0}:{1}'.format(hostname, 'A')
        value = session[key] if key in session else ''

        return {'value': value}

    def delete_a_cache(self, args):
        from BTPanel import session

        if 'hostname' not in args:
            return public.returnMsg(False, '请传入主机域名')
        hostname = args.hostname

        key = '{0}:{1}'.format(hostname, 'A')
        value = session.pop(key) if key in session else ''

        return public.returnMsg(True, '删除主机名({})在session中的缓存记录成功'.format(hostname))

    def _check_a(self, hostname):
        '''
        检测主机名是否有A记录
        :param hostname:
        :return:
        '''
        from BTPanel import session
        import urllib2

        url = 'http://pv.sohu.com/cityjson?ie=utf-8'
        opener = urllib2.urlopen(url)
        m_str = opener.read()
        ipaddress = re.search('\d+.\d+.\d+.\d+', m_str).group(0)

        key = '{0}:{1}'.format(hostname, 'A')
        try:
            # value = session[key] if key in session else ''
            value = ''
            if '' == value:
                result = dns.resolver.query(hostname, 'A')
                for i in result.response.answer:
                    for j in i.items:
                        value += str(j).strip()
            if ipaddress in value:
                session[key] = value
                return True
            return False
        except:
            traceback.print_exc()
            return False

    def _clear_work(self):
        '''
        清理之前安装过的痕迹
        :return:
        '''

        shell_str = '''
yum remove postfix3 -y
rm -rf /etc/postfix
rm -rf /etc/postfix.origin

yum remove dovecot -y
rm -rf /etc/dovecot
rm -rf /etc/dovecot.origin

userdel vmail
unalias cp
cp -a /www/vmail /www/vmail.bak
rm -rf /www/vmail

firewall-cmd --remove-port=25/tcp --remove-port=110/tcp --remove-port=143/tcp --permanent
firewall-cmd --remove-port=465/tcp --remove-port=995/tcp --remove-port=993/tcp --remove-port=587/tcp --permanent
firewall-cmd --reload'''
        public.ExecShell(shell_str)

    def _prepare_work(self, hostname):
        '''
        安装前的准备工作
        :return:
        '''
        if 'sendmail' in public.ExecShell('rpm -qa | grep sendmail')[0]:
            os.system('yum remove sendmail -y')

        shell_str = '''
firewall-cmd --add-port=25/tcp --add-port=110/tcp --add-port=143/tcp --permanent
firewall-cmd --add-port=465/tcp --add-port=995/tcp --add-port=993/tcp --add-port=587/tcp --permanent
firewall-cmd --reload

hostnamectl  set-hostname   {hostname}

useradd -r -u 150 -g mail -d /www/vmail -s /sbin/nologin -c "Virtual Mail User" vmail
mkdir -p /www/vmail
chmod -R 770 /www/vmail
chown -R vmail:mail /www/vmail

unalias cp
cp -a /www/vmail/postfixadmin.db /www/vmail/postfixadmin.db.bak
if [ ! -f "/www/vmail/postfixadmin.db" ]; then
    touch /www/vmail/postfixadmin.db
    chown vmail:mail /www/vmail/postfixadmin.db
    chmod 660 /www/vmail/postfixadmin.db
fi'''.format(hostname=hostname)
        public.ExecShell(shell_str)

        # 创建数据表
        sql = '''CREATE TABLE IF NOT EXISTS `domain` (
          `domain` varchar(255) NOT NULL,
          `created` datetime NOT NULL,
          `active` tinyint(1) NOT NULL DEFAULT 1,
          PRIMARY KEY (`domain`));'''
        self.M('').execute(sql, ())

        sql = '''CREATE TABLE IF NOT EXISTS `mailbox` (
          `username` varchar(255) NOT NULL,
          `password` varchar(255) NOT NULL,
          `password_encode` varchar(255) NOT NULL,
          `full_name` varchar(255) NOT NULL,
          `is_admin` tinyint(1) NOT NULL DEFAULT 0,
          `maildir` varchar(255) NOT NULL,
          `quota` bigint(20) NOT NULL DEFAULT 0,
          `local_part` varchar(255) NOT NULL,
          `domain` varchar(255) NOT NULL,
          `created` datetime NOT NULL,
          `modified` datetime NOT NULL,
          `active` tinyint(1) NOT NULL DEFAULT 1,
          PRIMARY KEY (`username`));'''
        self.M('').execute(sql, ())

        sql = '''CREATE TABLE IF NOT EXISTS `alias` (
          `address` varchar(255) NOT NULL,
          `goto` text NOT NULL,
          `domain` varchar(255) NOT NULL,
          `created` datetime NOT NULL,
          `modified` datetime NOT NULL,
          `active` tinyint(1) NOT NULL DEFAULT 1,
          PRIMARY KEY (`address`));'''
        self.M('').execute(sql, ())

        sql = '''CREATE TABLE IF NOT EXISTS `alias_domain` (
          `alias_domain` varchar(255) NOT NULL,
          `target_domain` varchar(255) NOT NULL,
          `created` datetime NOT NULL,
          `modified` datetime NOT NULL,
          `active` tinyint(1) NOT NULL DEFAULT 1,
          PRIMARY KEY (`alias_domain`));'''
        self.M('').execute(sql, ())

    def _setup_postfix(self):
        '''
        安装，配置postfix服务, postfix提供发信功能
        :return:
        '''

        if not os.path.isfile('/etc/yum.repos.d/gf.repo'):
            os.system('rpm -Uhv http://mirror.ghettoforge.org/distributions/gf/gf-release-latest.gf.el7.noarch.rpm')
        if 'postfix' in public.ExecShell('rpm -qa | grep postfix')[0]:
            os.system('yum remove postfix -y')
        if 'postfix3' not in public.ExecShell('rpm -qa | grep postfix3')[0]:
            os.system('yum install -y postfix3 postfix3-sqlite --enablerepo=gf-plus')

        bak_conf_shell = '''
if [ ! -d "/etc/postfix.origin" ]; then
    cp -a /etc/postfix /etc/postfix.origin
fi'''
        public.ExecShell(bak_conf_shell)

        # 修改postfix配置
        edit_postfix_conf_shell = """
postconf -e "myhostname = $(hostname -f)"
postconf -e "inet_interfaces = all"

postconf -e "virtual_mailbox_domains = sqlite:/etc/postfix/sqlite_virtual_domains_maps.cf"
postconf -e "virtual_alias_maps =  sqlite:/etc/postfix/sqlite_virtual_alias_maps.cf, sqlite:/etc/postfix/sqlite_virtual_alias_domain_maps.cf, sqlite:/etc/postfix/sqlite_virtual_alias_domain_catchall_maps.cf"
postconf -e "virtual_mailbox_maps = sqlite:/etc/postfix/sqlite_virtual_mailbox_maps.cf, sqlite:/etc/postfix/sqlite_virtual_alias_domain_mailbox_maps.cf"

postconf -e "smtpd_sasl_type = dovecot"
postconf -e "smtpd_sasl_path = private/auth"
postconf -e "smtpd_sasl_auth_enable = yes"
postconf -e "smtpd_recipient_restrictions = permit_sasl_authenticated, permit_mynetworks, reject_unauth_destination"

postconf -e "smtpd_use_tls = yes"
postconf -e "smtpd_tls_cert_file = /etc/pki/dovecot/certs/dovecot.pem"
postconf -e "smtpd_tls_key_file = /etc/pki/dovecot/private/dovecot.pem"

postconf -e "virtual_transport = lmtp:unix:private/dovecot-lmtp"
"""
        public.ExecShell(edit_postfix_conf_shell)

        download_sql_conf_shell = '''
wget "{download_conf_url}/mail_sys/postfix/master.cf" -O /etc/postfix/master.cf -T 10
wget "{download_conf_url}/mail_sys/postfix/sqlite_virtual_alias_domain_catchall_maps.cf" -O /etc/postfix/sqlite_virtual_alias_domain_catchall_maps.cf -T 10
wget "{download_conf_url}/mail_sys/postfix/sqlite_virtual_alias_domain_mailbox_maps.cf" -O /etc/postfix/sqlite_virtual_alias_domain_mailbox_maps.cf -T 10
wget "{download_conf_url}/mail_sys/postfix/sqlite_virtual_alias_domain_maps.cf" -O /etc/postfix/sqlite_virtual_alias_domain_maps.cf -T 10
wget "{download_conf_url}/mail_sys/postfix/sqlite_virtual_alias_maps.cf" -O /etc/postfix/sqlite_virtual_alias_maps.cf -T 10
wget "{download_conf_url}/mail_sys/postfix/sqlite_virtual_domains_maps.cf" -O /etc/postfix/sqlite_virtual_domains_maps.cf -T 10
wget "{download_conf_url}/mail_sys/postfix/sqlite_virtual_mailbox_maps.cf" -O /etc/postfix/sqlite_virtual_mailbox_maps.cf -T 10
'''.format(download_conf_url=self.__download_conf_url)
        public.ExecShell(download_sql_conf_shell)

        restart_service_shell = '''
systemctl enable postfix
systemctl restart  postfix
'''
        public.ExecShell(restart_service_shell)

    def _setup_dovecot(self):
        '''
        安装，配置dovecot服务, dovecot提供收信功能
        :return:
        '''
        if 'dovecot' not in public.ExecShell('rpm -qa | grep dovecot')[0]:
            public.ExecShell('yum install -y dovecot')

        bak_conf_shell = '''
if [ ! -d "/etc/dovecot.origin" ]; then
    cp -a /etc/dovecot /etc/dovecot.origin
fi'''
        public.ExecShell(bak_conf_shell)

        download_conf_shell = '''
wget "{download_conf_url}/mail_sys/dovecot/dovecot-sql.conf.ext" -O /etc/dovecot/dovecot-sql.conf.ext -T 10
wget "{download_conf_url}/mail_sys/dovecot/10-mail.conf" -O /etc/dovecot/conf.d/10-mail.conf -T 10
wget "{download_conf_url}/mail_sys/dovecot/10-ssl.conf" -O /etc/dovecot/conf.d/10-ssl.conf -T 10
wget "{download_conf_url}/mail_sys/dovecot/10-master.conf" -O /etc/dovecot/conf.d/10-master.conf -T 10
wget "{download_conf_url}/mail_sys/dovecot/10-auth.conf" -O /etc/dovecot/conf.d/10-auth.conf -T 10
'''.format(download_conf_url=self.__download_conf_url)
        public.ExecShell(download_conf_shell)

        restart_service_shell = '''
chown -R vmail:dovecot /etc/dovecot
chmod -R o-rwx /etc/dovecot

systemctl enable dovecot
systemctl restart  dovecot
'''
        public.ExecShell(restart_service_shell)

    def M(self, table_name):
        import db
        sql = db.Sql()
        sql._Sql__DB_FILE = '/www/vmail/postfixadmin.db'
        return sql.table(table_name)

    def get_domains(self, args):
        '''
        域名查询接口
        :param args:
        :return:
        '''
        p = int(args.p) if 'p' in args else 1
        rows = int(args.rows) if 'rows' in args else 12
        callback = args.callback if 'callback' in args else ''

        count = self.M('domain').count()

        #获取分页数据
        page_data = public.get_page(count, p, rows, callback)

        #获取当前页的数据列表
        data_list = self.M('domain').order('created desc').limit(page_data['shift'] + ',' + page_data['row']).field('domain,created,active').select()
        for item in data_list:
            item['mx_status'] = 1 if self._check_mx(item['domain']) else 0
            item['txt_status'] = 1 if self._check_txt(item['domain']) else 0
        #返回数据到前端
        return {'data': data_list, 'page': page_data['page'], 'hostname': public.ExecShell('hostname -f')[0].strip()}

    def _check_mx(self, domain):
        '''
        检测域名是否有mx记录
        :param domain:
        :return:
        '''
        from BTPanel import session

        hostname = public.ExecShell('hostname -f')[0].strip()

        key = '{0}:{1}'.format(domain, 'MX')
        try:
            value = session[key] if key in session else ''
            if '' == value:
                result = dns.resolver.query(domain, 'MX')
                value = str(result[0].exchange).strip('.')
            if hostname == value:
                session[key] = value
                return True
            return False
        except:
            traceback.print_exc()
            return False

    def _check_txt(self, domain):
        '''
        检测域名是否有txt记录
        :param domain:
        :return:
        '''
        from BTPanel import session

        key = '{0}:{1}'.format(domain, 'TXT')
        try:
            value = session[key] if key in session else ''
            if '' == value:
                result = dns.resolver.query(domain, 'TXT')
                for i in result.response.answer:
                    for j in i.items:
                        value += str(j).strip()
            if 'v=spf1' in value:
                session[key] = value
                return True
            return False
        except:
            traceback.print_exc()
            return False

    def get_mx_txt_cache(self, args):
        from BTPanel import session

        if 'domain' not in args:
            return public.returnMsg(False, '请传入域名')
        domain = args.domain

        mx_key = '{0}:{1}'.format(domain, 'MX')
        txt_key = '{0}:{1}'.format(domain, 'TXT')

        mx_value = session[mx_key] if mx_key in session else ''
        txt_value = session[txt_key] if txt_key in session else ''

        return {'mx': mx_value, 'txt': txt_value}

    def delete_mx_txt_cache(self, args):
        from BTPanel import session

        if 'domain' not in args:
            return public.returnMsg(False, '请传入域名')
        domain = args.domain

        mx_key = '{0}:{1}'.format(domain, 'MX')
        txt_key = '{0}:{1}'.format(domain, 'TXT')

        mx_value = session.pop(mx_key) if mx_key in session else ''
        txt_value = session.pop(txt_key) if txt_key in session else ''

        return public.returnMsg(True, '删除域名({})在session中的缓存记录成功'.format(domain))

    def add_domain(self, args):
        '''
        域名增加接口
        :param args:
        :return:
        '''
        if 'domain' not in args:
            return public.returnMsg(False, '请传入域名')
        domain = args.domain

        count = self.M('domain').count()
        if count >= 10:
            return public.returnMsg(False, '域名数量超过上限')

        count = self.M('domain').where('domain=?',(domain,)).count()
        if count > 0:
            return public.returnMsg(False, '该域名已存在')

        cur_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.M('domain').add('domain,created', (domain, cur_time))

        # 在虚拟用户家目录创建对应域名的目录
        os.system('mkdir /www/vmail/{0}'.format(domain))
        os.system('chown -R vmail:mail /www/vmail')
        return public.returnMsg(True, '新增域成功! ({0})'.format(domain))

    def delete_domain(self, args):
        '''
        域名删除接口
        :param args:
        :return:
        '''
        if 'domain' not in args:
            return public.returnMsg(False, '请传入域名')
        domain = args.domain

        # 删除域名记录
        self.M('domain').where('domain=?',(domain,)).delete()
        # 删除域名下的邮箱记录
        self.M('mailbox').where('domain=?',(domain,)).delete()

        # 在虚拟用户家目录删除对应域名的目录
        os.system('rm -rf /www/vmail/{0}'.format(domain))
        return public.returnMsg(True, '删除域成功! ({0})'.format(domain))

    def get_mailboxs(self, args):
        '''
        邮箱用户查询接口
        :param args:
        :return:
        '''
        p = int(args.p) if 'p' in args else 1
        rows = int(args.rows) if 'rows' in args else 12
        callback = args.callback if 'callback' in args else ''
        if 'domain' in args:
            domain = args.domain

            count = self.M('mailbox').where('domain=?',(domain,)).count()

            #获取分页数据
            page_data = public.get_page(count, p, rows, callback)

            #获取当前页的数据列表
            data_list = self.M('mailbox').order('created desc').limit(page_data['shift'] + ',' + page_data['row']).where('domain=?',(domain,))\
                .field('full_name,username,quota,created,modified,active,is_admin').select()

            #返回数据到前端
            return {'data': data_list, 'page': page_data['page']}
        else:
            count = self.M('mailbox').count()

            # 获取分页数据
            page_data = public.get_page(count, p, rows, callback)

            # 获取当前页的数据列表
            data_list = self.M('mailbox').order('created desc').limit(page_data['shift'] + ',' + page_data['row'])\
                .field('full_name,username,quota,created,modified,active,is_admin').select()

            # 返回数据到前端
            return {'data': data_list, 'page': page_data['page']}

    # 加密数据
    def _encode(self, data):
        data = base64.b64encode(data)
        return binascii.hexlify(data)

    # 解密数据
    def _decode(self, data):
        data = binascii.unhexlify(data)
        return base64.b64decode(data)

    # 检测密码强度
    def _check_passwd(self, password):
        return True if re.search("^(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).*$", password) and len(password) >= 8 else False

    def add_mailbox(self, args):
        '''
        新增邮箱用户
        :param args:
        :return:
        '''
        if 'username' not in args:
            return public.returnMsg(False, '请传入账号名')
        if not self._check_passwd(args.password):
            return public.returnMsg(False, '密码强度不够(需要包括大小写字母和数字并且长度不小于8)')
        username = args.username
        is_admin = args.is_admin if 'is_admin' in args else 0

        shell_str = 'doveadm pw -s MD5-CRYPT -p {0}'.format(args.password)
        password_encrypt = public.ExecShell(shell_str)[0][11:].strip()
        password_encode = self._encode(args.password)
        local_part, domain = username.split('@')
        quota = int(args.quota) * 1024 * 1024 * 1024

        count = self.M('mailbox').where('username=?',(username,)).count()
        if count > 0:
            return public.returnMsg(False, '该邮箱地址已存在')

        cur_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.M('mailbox').add('full_name,is_admin,username,password,password_encode,maildir,quota,local_part,domain,created,modified',
                              (args.full_name, is_admin, username, password_encrypt, password_encode, args.username + '/', quota, local_part, domain, cur_time, cur_time))

        # 在虚拟用户家目录创建对应邮箱的目录
        os.system('mkdir /www/vmail/{0}/{1}'.format(domain, local_part))
        os.system('chown -R vmail:mail /www/vmail')
        return public.returnMsg(True, '增加邮箱用户成功! ({0})'.format(username))

    def update_mailbox(self, args):
        '''
        邮箱用户修改接口
        :param args:
        :return:
        '''
        if not self._check_passwd(args.password):
            return public.returnMsg(False, '密码强度不够(需要包括大小写字母和数字并且长度不小于8)')
        quota = int(args.quota) * 1024 * 1024 * 1024
        cur_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if 'password' in args and args.password != '':
            shell_str = 'doveadm pw -s MD5-CRYPT -p {0}'.format(args.password)
            password_encrypt = public.ExecShell(shell_str)[0][11:].strip()
            password_encode = self._encode(args.password)
            self.M('mailbox').where('username=?',(args.username,)).save('password,password_encode,full_name,quota,modified,active,is_admin',
                                                                        (password_encrypt, password_encode, args.full_name, quota, cur_time, args.active, args.is_admin))
        else:
            self.M('mailbox').where('username=?',(args.username,)).save('full_name,quota,modified,active,is_admin',
                                                                        (args.full_name, quota, cur_time, args.active, args.is_admin))
        return public.returnMsg(True, '编辑邮箱用户成功! ({0})'.format(args.username))

    def delete_mailbox(self, args):
        '''
        删除邮箱用户
        :param args:
        :return:
        '''
        if 'username' not in args:
            return public.returnMsg(False, '请传入账号名')
        username = args.username
        local_part, domain = username.split('@')

        self.M('mailbox').where('username=?',(username,)).delete()

        # 在虚拟用户家目录删除对应邮箱的目录
        os.system('rm -rf /www/vmail/{0}/{1}'.format(domain, local_part))
        return public.returnMsg(True, '删除邮箱用户成功! ({0})'.format(username))

    def send_mail(self, args):
        from send_mail import SendMail

        smtp_server = args.smtp_server if 'smtp_server' in args else 'localhost'
        mail_from = args.mail_from
        data = self.M('mailbox').where('username=?', (mail_from,)).field('password_encode').find()
        password = self._decode(data['password_encode'])
        mail_to = json.loads(args.mail_to) if 'mail_to' in args else []
        subject = args.subject
        content = args.content
        subtype = args.subtype if 'subtype' in args else 'plain'
        files = json.loads(args.files) if 'files' in args else []
        if not isinstance(mail_to, list):
            return public.returnMsg(False, '收件人不能解析成列表')
        if len(mail_to) == 0:
            return public.returnMsg(False, '收件人不能为空')

        try:
            send_mail_client = SendMail(mail_from, password, smtp_server)
            send_mail_client.setMailInfo(subject, content, subtype, files)
            send_mail_client.sendMail(mail_to)

            return public.returnMsg(True, '发送邮件成功')
        except Exception as e:
            traceback.print_exc()
            return public.returnMsg(False, '发送邮件失败,错误原因[{0}]'.format(str(e)))

    def _check(self, args):
        if args['fun'] in ['send_mail_http']:
            return True
        else:
            return public.returnMsg(False, '接口不支持公共访问!')

    def send_mail_http(self, args):
        from send_mail import SendMail

        mail_from = args.mail_from
        password = args.password
        mail_to = [item.strip() for item in args.mail_to.split(',')]
        subject = args.subject
        content = args.content
        subtype = args.subtype if 'subtype' in args else 'plain'
        files = json.loads(args.files) if 'files' in args else []

        try:
            send_mail_client = SendMail(mail_from, password, 'localhost')
            send_mail_client.setMailInfo(subject, content, subtype, files)
            send_mail_client.sendMail(mail_to)

            return public.returnMsg(True, '发送邮件成功')
        except Exception as e:
            traceback.print_exc()
            return public.returnMsg(False, '发送邮件失败,错误原因[{0}]'.format(str(e)))

    def receive_mail(self, args):
        from receive_mail import ImapReceiveMail, PopReceiveMail

        username = args.username
        password = args.password
        protocol = args.protocol if 'protocol' in args else 'imap'

        mail_list = list()
        try:
            if protocol == 'imap':
                imap_server = args.imap_server if 'imap_server' in args else 'localhost'
                receive_mail_client = ImapReceiveMail(username, password, imap_server)
            else:
                pop_server = args.pop_server if 'pop_server' in args else 'localhost'
                receive_mail_client = PopReceiveMail(username, password, pop_server)

            for num in receive_mail_client.getAll():
                mailInfo = receive_mail_client.getMailInfo(receive_mail_client.getEmailFormat(num))
                mail_list.append(mailInfo)

            return {'status': True, 'count': len(receive_mail_client.getAll()), 'data': mail_list[::-1]}
        except Exception as e:
            traceback.print_exc()
            return public.returnMsg(False, '接收邮件失败,错误原因[{0}]'.format(str(e)))

    def login(self, args):
        from receive_mail import ImapReceiveMail, PopReceiveMail

        smtp_server = args.smtp_server if 'smtp_server' in args else 'localhost'
        username = args.username
        password = args.password
        protocol = args.protocol if 'protocol' in args else 'imap'

        try:
            if protocol == 'imap':
                imap_server = args.imap_server if 'imap_server' in args else 'localhost'
                ImapReceiveMail(username, password, imap_server)
                return {'status': True, 'msg': '登陆成功', 'data': {'smtp_server': smtp_server, 'username': username, 'password': password, 'protocol': protocol, 'imap_server': imap_server}}
            else:
                pop_server = args.pop_server if 'pop_server' in args else 'localhost'
                PopReceiveMail(username, password, pop_server)
                return {'status': True, 'msg': '登陆成功', 'data': {'smtp_server': smtp_server, 'username': username, 'password': password, 'protocol': protocol, 'pop_server': pop_server}}
        except Exception as e:
            traceback.print_exc()
            return public.returnMsg(False, '登陆失败,错误原因[{0}]'.format(str(e)))

    def get_mails(self, args):
        import email
        from receive_mail import ReceiveMail

        if 'username' not in args:
            return public.returnMsg(False, '请传入账号名')
        username = args.username
        if '@' not in username:
            return public.returnMsg(False, '账号名不合法')
        local_part, domain = username.split('@')

        receive_mail = ReceiveMail()
        mail_list = list()
        try:
            # 读取cur文件夹的邮件
            dir_path = '/www/vmail/{0}/{1}/cur'.format(domain, local_part)
            if os.path.isdir(dir_path):
                for filename in os.listdir(dir_path):
                    file_path = dir_path + '/' + filename
                    fp = open(file_path, 'r')
                    try:
                        message = email.message_from_file(fp)
                        mailInfo = receive_mail.getMailInfo(msg=message)
                        mail_list.append(mailInfo)
                    except:
                        continue

            # 读取new文件夹的邮件
            dir_path = '/www/vmail/{0}/{1}/new'.format(domain, local_part)
            if os.path.isdir(dir_path):
                for filename in os.listdir(dir_path):
                    file_path = dir_path + '/' + filename
                    fp = open(file_path, 'r')
                    try:
                        message = email.message_from_file(fp)
                        mailInfo = receive_mail.getMailInfo(msg=message)
                        mail_list.append(mailInfo)
                    except:
                        continue

            return {'status': True, 'count': len(mail_list), 'data': mail_list[::-1]}
        except Exception as e:
            traceback.print_exc()
            return public.returnMsg(False, '获取邮件失败,错误原因[{0}]'.format(str(e)))
