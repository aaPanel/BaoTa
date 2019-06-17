# -*- coding: utf-8 -*-

import imaplib
import poplib
import email
import traceback
import sys

reload(sys)
sys.setdefaultencoding('utf8')


class ReceiveMail(object):

    # 返回接收邮件的时间
    def getTime(self, msg):
        deContent = email.Header.decode_header(msg['date'])[0]
        if deContent[1] is not None:
            return unicode(deContent[0], deContent[1])
        return deContent[0]

    # 返回发送者的信息
    def getSenderInfo(self, msg):
        name = email.Utils.parseaddr(msg["from"])[0]
        deName = email.Header.decode_header(name)[0]
        if deName[1] is not None:
            name = unicode(deName[0], deName[1])
        address = email.Utils.parseaddr(msg["from"])[1]
        return address

    # 返回接受者的信息
    def getReceiverInfo(self, msg):
        to_list = msg["to"].split(', ')
        to_str_list = list()
        for to_addr in to_list:
            name = email.Utils.parseaddr(to_addr)[0]
            deName = email.Header.decode_header(name)[0]
            if deName[1] is not None:
                name = unicode(deName[0], deName[1])
            address = email.Utils.parseaddr(to_addr)[1]
            to_str_list.append('{0} <{1}>'.format(name, address).strip())
        return ';'.join(to_str_list)

    # 返回邮件的主题
    def getSubjectContent(self, msg):
        deContent = email.Header.decode_header(msg['subject'])[0]
        if deContent[1] is not None:
            return unicode(deContent[0], deContent[1])
        return deContent[0]

    def parse_attachment(self, message_part):
        '''
        判断是否有附件，并解析
        '''
        content_disposition = message_part.get("Content-Disposition", None)
        if content_disposition:
            dispositions = content_disposition.strip().split(";")
            if bool(content_disposition and dispositions[0].lower() == "attachment"):

                file_data = message_part.get_payload(decode=True)
                attachment = dict()
                attachment["content_type"] = message_part.get_content_type()
                attachment["size"] = len(file_data)
                deName = email.Header.decode_header(message_part.get_filename())[0]
                name = deName[0]
                if deName[1] is not None:
                    name = unicode(deName[0], deName[1])
                attachment["name"] = name
                # attachment["data"] = file_data
                # 保存附件
                # fileobject = open(name, "wb")
                # fileobject.write(file_data)
                # fileobject.close()
                return attachment
        return None

    # 编码处理
    def guess_charset(self, msg):
        charset = msg.get_charset()
        if charset is None:
            content_type = msg.get('Content-Type', '').lower()
            if 'charset' in content_type:
                charset = content_type.split('charset=')[1].strip()
                return charset
        return charset

    def getMailInfo(self, msg):
        '''
        返回邮件的解析后信息部分
        返回列表包含(主题，纯文本正文部分，html的正文部分，发件人，收件人，附件列表)
        '''
        # msg = self.getEmailFormat(num)
        attachments = []
        body = ''
        html = ''
        for part in msg.walk():
            attachment = self.parse_attachment(part)
            if attachment:
                attachments.append(attachment)
            elif part.get_content_type() == "text/plain":
                content = part.get_payload(decode=True)
                charset = self.guess_charset(part)
                if charset: content = content.decode(charset)
                body += content
            elif part.get_content_type() == "text/html":
                content = part.get_payload(decode=True)
                charset = self.guess_charset(part)
                if charset: content = content.decode(charset)
                html += content

        return {'time': self.getTime(msg),
                'subject': self.getSubjectContent(msg),
                'body': body,
                'html': html,
                'from': self.getSenderInfo(msg),
                'to': self.getReceiverInfo(msg),
                'attachments': attachments}


class ImapReceiveMail(ReceiveMail):

    def __init__(self, username, password, server, is_ssl=False):
        if is_ssl:
            self.mail = imaplib.IMAP4_SSL(server)
        else:
            self.mail = imaplib.IMAP4(server)
        self.mail.login(username, password)
        self.select("INBOX")

    # 返回所有文件夹
    def showFolders(self):
        return self.mail.list()

    # 选择收件箱
    def select(self, selector):
        return self.mail.select(selector)

    # 搜索邮件
    def search(self, charset, *criteria):
        try:
            return self.mail.search(charset, *criteria)
        except :
            self.select("INBOX")
            return self.mail.search(charset, *criteria)

    # 返回所有未读的邮件列表
    def getUnread(self):
        return self.search(None, "Unseen")

    # 返回所有邮件列表
    def getAll(self):
        return self.search(None, "All")[1][0].split()

    # 以RFC822协议格式返回邮件详情的email对象
    def getEmailFormat(self, num):
        data = self.mail.fetch(num, 'RFC822')
        if data[0] == 'OK':
            return email.message_from_string(data[1][0][1])
        else:
            return "fetch error"

    # 返回邮件的UID号，UID号是唯一标识邮件的一个号码
    def getEmailUid(self, num):
        data = self.mail.fetch(num, 'UID')
        if data[0] == 'OK':
            return data[1][0].split()[2].rstrip(')')
        else:
            return "get uid error"


class PopReceiveMail(ReceiveMail):

    def __init__(self, username, password, server, is_ssl=False):
        if is_ssl:
            self.mail = poplib.POP3_SSL(server)
        else:
            self.mail = poplib.POP3(server)
        self.mail.user(username)
        self.mail.pass_(password)

    def getAll(self):
        return range(1, self.mail.stat()[0] + 1)

    def getEmailFormat(self, num):
        response, message, octets = self.mail.retr(num)
        if 'OK' in response:
            return email.message_from_string('\n'.join(message))
        else:
            return "get email error"

    def getEmailUid(self, num):
        response, _, uid = self.mail.uidl(num).split()
        if 'OK' in response:
            return uid
        else:
            return "get uid error"
