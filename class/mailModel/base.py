# coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aapanel(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------

# ------------------------------
# 邮局 - 底层基类
# ------------------------------

import binascii, base64, re, json, os, sys, time, io
import psutil
if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
import public

class Base:

    def __init__(self):
        pass

    def M(self, table_name):
        import db
        sql = db.Sql()
        sql._Sql__DB_FILE = '/www/vmail/postfixadmin.db'
        sql._Sql__encrypt_keys = []
        return sql.table(table_name)


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

    # 获取公网ip
    def _get_pubilc_ip(self):
        import requests

        try:
            #url = 'http://pv.sohu.com/cityjson?ie=utf-8'
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

    # 检查邮箱合法性
    def _check_email_address(self, email_address):
        return True if re.match(r"^\w+([.-]?\w+)*@.*", email_address) else False
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
    def _ipv6_to_ptr(self,ipv6_address):

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

    def returnResult(self, status=True, msg="OK", data=None, timestamp=None, code=0, args=None):
        '''
        通用响应对象
        @param code: 0:成功 1:失败 2:警告 ...
        @param status:
        @param msg: 只传msg,不传需要前端处理的数据
        @param data: 只传需要前端处理的数据
        @param timestamp: 秒级时间戳
        @return:

        使用示例：
        成功：return dp.returnResult(data=data)
        失败：return dp.returnResult(code=1, status=False, msg="获取失败!", data=[])
        失败：return dp.returnResult(code=1, status=False, msg="获取失败!")
        警告：return dp.returnResult(code=2, status=False, msg="警告，xxxxxxxxxxx!")
        ...
        '''
        import time
        if timestamp is None:
            timestamp = int(time.time())

        try:
            log_message = json.loads(
                public.ReadFile('BTPanel/static/language/' + public.GetLanguage() + '/public.json'))
            keys = log_message.keys()
        except:
            log_message = {}
            keys = []

        if type(msg) == str:
            if msg in keys:
                msg = log_message[msg]
                for i in range(len(args)):
                    rep = '{' + str(i + 1) + '}'
                    msg = msg.replace(rep, args[i])

        return {
            "code": code,
            "status": status,
            "msg": msg,
            "data": data,
            "timestamp": timestamp
        }

    def return_msg(self, result):
        if not isinstance(result, dict):
            return self.returnResult(True, "", result, time.time(), 0, )
        status = result.get('status', True)
        msg = result.get('msg', '')
        data = result
        timestamp = result.get('timestamp', time.time())
        code = 0 if status else 1
        return self.returnResult(status, msg, data, timestamp, code, )
        # return {'status': result.get('status', False), 'message': result, 'timestamp': time.time()}
        # return result