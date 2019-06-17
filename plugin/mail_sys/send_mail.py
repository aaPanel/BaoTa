#!/usr/bin/python
# -*- coding: utf-8 -*-

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.encoders import encode_base64
from email.utils import COMMASPACE, formatdate
from email.header import Header

import time


class SendMail(object):

    def __init__(self, username, password, server, port=25, usettls=False):
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

    def __del__(self):
        self.mailServer.close()

    def setMailInfo(self, subject, text, text_type, attachmentFilePaths):
        self.msg['From'] = self.mailUser
        self.msg['Date'] = formatdate(localtime=True)
        self.msg['Subject'] = subject

        self.msg.attach(MIMEText(text, text_type, _charset="utf-8"))
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

    def sendMail(self, receiveUsers):
        self.msg['To'] = COMMASPACE.join(receiveUsers)

        if not receiveUsers:
            print("没有收件人, 请先设置邮件基本信息")
            return False
        self.mailServer.sendmail(self.mailUser, receiveUsers, self.msg.as_string())
        print('Sent email to %s' % self.msg['To'])
        return True
