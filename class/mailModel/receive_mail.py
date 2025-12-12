# -*- coding: utf-8 -*-

import imaplib
import poplib
import email
import sys
import re
try:
    from HTMLParser import HTMLParser
except:
    from html.parser import HTMLParser

if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
else:
    from email.header import decode_header
    from email.utils import parsedate_tz, mktime_tz, parseaddr

sys.path.append("class/")
import public


class XssHtml(HTMLParser):
    allow_tags = ['a', 'img', 'br', 'strong', 'b', 'code', 'pre',
                  'p', 'div', 'em', 'span', 'h1', 'h2', 'h3', 'h4',
                  'h5', 'h6', 'blockquote', 'ul', 'ol', 'tr', 'th', 'td',
                  'hr', 'li', 'u', 'embed', 's', 'table', 'thead', 'tbody',
                  'caption', 'small', 'q', 'sup', 'sub']
    common_attrs = ["style", "class", "name"]
    nonend_tags = ["img", "hr", "br", "embed"]
    tags_own_attrs = {
        "img": ["src", "width", "height", "alt", "align"],
        "a": ["href", "target", "rel", "title"],
        "embed": ["src", "width", "height", "type", "allowfullscreen", "loop", "play", "wmode", "menu"],
        "table": ["border", "cellpadding", "cellspacing"],
    }

    _regex_url = re.compile(r'^(http|https|ftp)://.*', re.I | re.S)
    _regex_style_1 = re.compile(r'(\\|&#|/\*|\*/)', re.I)
    _regex_style_2 = re.compile(r'e.*x.*p.*r.*e.*s.*s.*i.*o.*n', re.I | re.S)

    def __init__(self, allows=[]):
        HTMLParser.__init__(self)
        self.allow_tags = allows if allows else self.allow_tags
        self.result = []
        self.start = []
        self.data = []

    def getHtml(self):
        """
        Get the safe html code
        """
        for i in range(0, len(self.result)):
            self.data.append(self.result[i])
        return ''.join(self.data)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_starttag(self, tag, attrs):
        if tag not in self.allow_tags:
            return
        end_diagonal = ' /' if tag in self.nonend_tags else ''
        if not end_diagonal:
            self.start.append(tag)
        attdict = {}
        for attr in attrs:
            attdict[attr[0]] = attr[1]

        attdict = self._wash_attr(attdict, tag)
        if hasattr(self, "node_%s" % tag):
            attdict = getattr(self, "node_%s" % tag)(attdict)
        else:
            attdict = self.node_default(attdict)

        attrs = []
        for (key, value) in attdict.items():
            attrs.append('%s="%s"' % (key, self._htmlspecialchars(value)))
        attrs = (' ' + ' '.join(attrs)) if attrs else ''
        self.result.append('<' + tag + attrs + end_diagonal + '>')

    def handle_endtag(self, tag):
        if self.start and tag == self.start[len(self.start) - 1]:
            self.result.append('</' + tag + '>')
            self.start.pop()

    def handle_data(self, data):
        self.result.append(self._htmlspecialchars(data))

    def handle_entityref(self, name):
        if name.isalpha():
            self.result.append("&%s;" % name)

    def handle_charref(self, name):
        if name.isdigit():
            self.result.append("&#%s;" % name)

    def node_default(self, attrs):
        attrs = self._common_attr(attrs)
        return attrs

    def node_a(self, attrs):
        attrs = self._common_attr(attrs)
        attrs = self._get_link(attrs, "href")
        attrs = self._set_attr_default(attrs, "target", "_blank")
        attrs = self._limit_attr(attrs, {
            "target": ["_blank", "_self"]
        })
        return attrs

    def node_embed(self, attrs):
        attrs = self._common_attr(attrs)
        attrs = self._get_link(attrs, "src")
        attrs = self._limit_attr(attrs, {
            "type": ["application/x-shockwave-flash"],
            "wmode": ["transparent", "window", "opaque"],
            "play": ["true", "false"],
            "loop": ["true", "false"],
            "menu": ["true", "false"],
            "allowfullscreen": ["true", "false"]
        })
        attrs["allowscriptaccess"] = "never"
        attrs["allownetworking"] = "none"
        return attrs

    def _true_url(self, url):
        if self._regex_url.match(url):
            return url
        else:
            return "http://%s" % url

    def _true_style(self, style):
        if style:
            style = self._regex_style_1.sub('_', style)
            style = self._regex_style_2.sub('_', style)
        return style

    def _get_style(self, attrs):
        if "style" in attrs:
            attrs["style"] = self._true_style(attrs.get("style"))
        return attrs

    def _get_link(self, attrs, name):
        if name in attrs:
            attrs[name] = self._true_url(attrs[name])
        return attrs

    def _wash_attr(self, attrs, tag):
        if tag in self.tags_own_attrs:
            other = self.tags_own_attrs.get(tag)
        else:
            other = []

        _attrs = {}
        if attrs:
            for (key, value) in attrs.items():
                if key in self.common_attrs + other:
                    _attrs[key] = value
        return _attrs

    def _common_attr(self, attrs):
        attrs = self._get_style(attrs)
        return attrs

    def _set_attr_default(self, attrs, name, default=''):
        if name not in attrs:
            attrs[name] = default
        return attrs

    def _limit_attr(self, attrs, limit={}):
        for (key, value) in limit.items():
            if key in attrs and attrs[key] not in value:
                del attrs[key]
        return attrs

    def _htmlspecialchars(self, html):
        return html.replace("<", "&lt;")\
            .replace(">", "&gt;")\
            .replace('"', "&quot;")\
            .replace("'", "&#039;")


class ReceiveMail(object):

    def xss_encode(self, text):
        parser = XssHtml()
        parser.feed(text)
        parser.close()
        return parser.getHtml()

    # 返回接收邮件的时间
    def getTime(self, msg):
        if not msg['date']: return 0
        if sys.version_info[0] == 2:
            deContent = email.Header.decode_header(msg['date'])[0]
        else:
            deContent = decode_header(msg['date'])[0]
        if deContent[1] is not None:
            if sys.version_info[0] == 2:
                date_str = unicode(deContent[0], deContent[1])
            else:
                date_str = str(deContent[0], deContent[1])
        else:
            date_str = deContent[0]
        if sys.version_info[0] == 2:
            date_tuple = email.Utils.parsedate_tz(date_str)
            time_stamp = email.Utils.mktime_tz(date_tuple)
        else:
            date_tuple = parsedate_tz(date_str)
            time_stamp = mktime_tz(date_tuple)
        return time_stamp

    # 返回发送者的信息
    def getSenderInfo(self, msg):
        if sys.version_info[0] == 2:
            address = email.Utils.parseaddr(msg["from"])[1]
            name = email.Utils.parseaddr(msg["from"])[0]
            deName = email.Header.decode_header(name)
        else:
            address = parseaddr(msg["from"])[1]
            name = parseaddr(msg["from"])[0]
            deName = decode_header(name)
        s = ""
        for content in deName:
            if type(content[0]) == str:
                s += content[0]
                continue
            if content[1] is not None:
                s += content[0].decode(content[1])
            else:
                s += content[0].decode('utf-8')
        name = s.strip()
        return '{0} <{1}>'.format(name, address).strip()

    # 返回接受者的信息
    def getReceiverInfo(self, msg):
        to_list = msg["to"].split(', ')
        to_str_list = list()
        for to_addr in to_list:
            if sys.version_info[0] == 2:
                address = email.Utils.parseaddr(to_addr)[1]
                name = email.Utils.parseaddr(to_addr)[0]
                deName = email.Header.decode_header(name)[0]
            else:
                address = parseaddr(to_addr)[1]
                name = parseaddr(to_addr)[0]
                deName = decode_header(name)[0]
            if deName[1] is not None:
                if sys.version_info[0] == 2:
                    name = unicode(deName[0], deName[1])
                else:
                    name = str(deName[0], deName[1])
            to_str_list.append('{0} <{1}>'.format(name, address).strip())
        return ';'.join(to_str_list)

    # 返回邮件的主题
    def getSubjectContent(self, msg):
        if not msg['subject']:
            return ''
        if sys.version_info[0] == 2:
            deContent = email.Header.decode_header(msg['subject'])
        else:
            deContent = decode_header(msg['subject'])
        s = ""
        for content in deContent:
            if type(content[0]) == str:
                s += content[0]
                continue
            if content[1] is not None:
                s += content[0].decode(content[1])
            else:
                s += content[0].decode('utf-8')
        return s.strip()

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
                if sys.version_info[0] == 2:
                    deName = email.Header.decode_header(message_part.get_filename())[0]
                else:
                    deName = decode_header(message_part.get_filename())[0]
                name = deName[0]
                if deName[1] is not None:
                    if sys.version_info[0] == 2:
                        name = unicode(deName[0], deName[1])
                    else:
                        name = str(deName[0], deName[1])
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
                if ';' in charset:
                    charset = charset.split(';')[0]
                return charset
        return charset

    def getMailInfo(self, msg):
        from email import policy
        from email.parser import BytesParser
        from email.utils import parsedate_to_datetime
        import time
        import base64

        msg = BytesParser(policy=policy.default).parsebytes(msg.encode('utf-8'))

        # 解析时间，并转换为时间戳
        date_str = msg["date"]
        if date_str:
            dt = parsedate_to_datetime(date_str)
            timestamp = int(time.mktime(dt.timetuple()))
        else:
            timestamp = None

        headers = {
            "from": msg["from"],
            "to": msg["to"],
            "subject": msg["subject"],
            "time": timestamp,
        }

        # 解析邮件正文
        body = {"body": "", "html": ""}
        if msg.is_multipart():
            for part in msg.iter_parts():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                if part.get_content_maintype() == "multipart" and part.get_content_subtype() == "alternative":
                    # 遍历 alternative 的子部分
                    for subpart in part.iter_parts():
                        sub_type = subpart.get_content_type()
                        if sub_type == "text/html":
                            body["html"] = subpart.get_content()
                        elif sub_type == "text/plain" and not body["html"]:
                            body["body"] = subpart.get_content()
                    continue

                # 解析正文
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    body["body"] = part.get_content()
                elif content_type == "text/html" and "attachment" not in content_disposition:
                    body["html"] = part.get_content()

                # 解析附件
                elif "attachment" in content_disposition:
                    filename = part.get_filename()
                    content = part.get_payload(decode=True)
                    body.setdefault("attachments", []).append({"filename": filename, "content": base64.b64encode(content).decode("utf-8")})
        else:
            # 非 multipart 邮件的处理
            content_type = msg.get_content_type()
            if content_type == "text/plain":
                body["body"] = msg.get_content()
            elif content_type == "text/html":
                body["html"] = msg.get_content()

        headers.update(body)

        return headers


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
