import json
import os
import re
import sys
import time

from mailModel.base import Base
sys.path.append("class/")
import public
class main(Base):
    def __init__(self):
        super().__init__()
        self.sender_transport = public.readFile('/etc/postfix/sender_transport')
        self.master_conf = public.readFile('/etc/postfix/master.cf')

    def check_main_conf(self):
        """
        检查主配置文件
        @return:
        """
        # 读取主配置文件 main.cf
        main_conf = public.readFile('/etc/postfix/main.cf')

        if not main_conf:
            return public.returnMsg(False, '未找到主配置文件main.cf')
        conf = "sender_dependent_default_transport_maps = hash:/etc/postfix/sender_transport"
        if not conf in main_conf:
            main_conf += '\n' + conf + '\n'
            public.writeFile('/etc/postfix/main.cf', main_conf)
        return public.returnMsg(True, '')

    def advance_create_ip_tag(self, net_interface):
        """
        预生成IP标签
        @param net_interface:
        @return:
        """
        tags = []
        if net_interface['status']:
            for k, v in net_interface['data'].items():
                for i in v:
                    tags.append({
                            'tag': "smtp"+str(len(tags)+1),
                            'ip': i['addr'],
                            'helo': "",
                            'syslog': "postfix-smtp"+str(len(tags)+1),
                            'binds': [],
                            'preference': "" if i["type"] =="IPv4" else "ipv6"
                        })
                    self.add_ip_tag_conf("smtp"+str(len(tags)), i['addr'], "", "postfix-smtp"+str(len(tags)), "4"if i["type"] =="IPv4" else "6", [])

        public.writeFile('/etc/postfix/master.cf', self.master_conf)
        public.ExecShell('postfix reload')
        return tags

    def get_ip_tags_api(self, get):
        """
        获取IP标签
        @param get:
        @return:
        """

        if not self.master_conf:
            return public.returnMsg(False, '未找到主配置文件master.cf')
        check_main_conf = self.check_main_conf()
        if not check_main_conf['status']:
            return check_main_conf
        pattern = re.compile(r"""
        ^(\S+)  # 匹配 SMTP 名称
        \s+unix\s+-\s+-\s+n\s+-\s+-\s+smtp  # 匹配 "unix - - n - - smtp"
        (?=.*(?:\n\s+-o\s+smtp_bind_address=([\d.]+)|\n\s+-o\s+smtp_bind_address6=([a-fA-F0-9:]+)))  # 至少包含 IPv4 或 IPv6
        (?:\n\s+-o\s+smtp_bind_address=([\d.]+))?  # 解析 IPv4 地址
        (?:\n\s+-o\s+smtp_bind_address6=([a-fA-F0-9:]+))?  # 解析 IPv6 地址
        (?:\n\s+-o\s+smtp_helo_name=([^\s]+))?  # 解析 HELO 名称（可选）
        (?:\n\s+-o\s+syslog_name=([^\s]+))?  # 解析 syslog 名称（可选）
        (?:\n\s+-o\s+smtp_address_preference=([^\s]+))?  # smtp_address_preference 可选
        """, re.MULTILINE | re.VERBOSE)
        matches = pattern.findall(self.master_conf)
        tags = []
        ip_dict = {}
        net_interface = self.get_net_interface(get)
        if net_interface['status']:
            for k, v in net_interface['data'].items():
                for i in v:
                    ip_dict[i['addr']] = i['public_ip']
        for match in matches:
            tag = {
                'tag': match[0],
                'ip': ip_dict.get(match[1] if match[1] else match[2]) or "",
                'helo': match[5],
                'syslog': match[6],
                'binds': self.get_tag_bind(match[0]),
                'preference': match[7]
            }
            tags.append(tag)
        # if not tags:
        #     tags = self.advance_create_ip_tag(net_interface)

        return {"status": True, "msg": "获取成功", "data": tags}

    def add_ip_tag_conf(self, tag, ip, helo, syslog, ipv, binds):
        """
        添加IP标签
        @param tag:
        @param ip:
        @param helo:
        @param syslog:
        @param ipv:
        @param binds:
        @return:
        """
        if tag in self.master_conf:
            return {"status": False, "msg": "标签已存在", "bind_success": []}
        if len(tag) > 10:
            return {"status": False, "msg": "标签长度不能大于10", "bind_success": []}
        if not re.match(r"^[a-zA-Z0-9_]+$", tag):
            return {"status": False, "msg": "标签只能包含字母、数字和下划线", "bind_success": []}

        extends = ""
        if helo:
            extends += "\n    -o smtp_helo_name={}".format(helo)
        if syslog:
            extends += "\n    -o syslog_name={}".format(syslog)

        if ipv == "6":
            conf = """
# =======设置IP标签 {tag} begin=======
{tag}     unix  -       -       n       -       -       smtp
    -o smtp_bind_address6={ip}{extends}
    -o smtp_address_preference=ipv6
# =======设置IP标签 {tag} end=======
"""
        else:
            conf = """
# =======设置IP标签 {tag} begin=======
{tag}     unix  -       -       n       -       -       smtp
    -o smtp_bind_address={ip}{extends}
# =======设置IP标签 {tag} end=======
"""
        conf = conf.format(tag=tag, ip=ip, extends=extends)
        bind_success = self.bind_ip_tag_conf(tag, binds)
        self.master_conf += conf
        # return {"status": True, "msg": "添加成功", "bind_success": bind_success}
        return {"status": True, "msg": "添加成功"}

    def add_ip_tag_api(self, get):
        """
        添加IP标签
        @param get:
        @return:
        """
        if not self.master_conf:
            return public.returnMsg(False, '未找到主配置文件master.cf')
        check_main_conf = self.check_main_conf()
        if not check_main_conf['status']:
            return check_main_conf
        result = self.add_ip_tag_conf(get.tag, get.ip, get.helo, get.syslog, get.ipv, get.binds.split(',') if get.binds else [])
        # public.writeFile('/etc/postfix/sender_transport', self.sender_transport)
        public.writeFile('/etc/postfix/master.cf', self.master_conf)
        # public.ExecShell('postmap /etc/postfix/sender_transport')
        public.ExecShell('postfix reload')
        return result

    def multi_add_ip_tag_api(self, get):
        """
        批量添加IP标签
        @param get:
        @return:
        """
        if not self.master_conf:
            return public.returnMsg(False, '未找到主配置文件master.cf')
        check_main_conf = self.check_main_conf()
        if not check_main_conf['status']:
            return check_main_conf
        data = get.data
        success = []
        for i in data:
            result = self.add_ip_tag_conf(i["tag"], i["ip"], i["helo"], i["syslog"], i["ipv"], i["binds"])
            success.append(result)
        public.writeFile('/etc/postfix/sender_transport', self.sender_transport)
        public.writeFile('/etc/postfix/master.cf', self.master_conf)
        public.ExecShell('postmap /etc/postfix/sender_transport')
        public.ExecShell('postfix reload')
        return {"status": True, "msg": "添加成功", "success": success}

    def del_ip_tag_conf(self, tags):
        """
        删除IP标签
        @param tags:
        @return:
        """
        tags = tags.split(',')
        for tag in tags:
            # 构建正则匹配配置块的模式，删除标签对应的配置段
            pattern = re.compile("""
# =======设置IP标签\s+{tag}\s+begin=======[\s\S]*?# =======设置IP标签\s+{tag}\s+end=======
""".format(tag=re.escape(tag)))
            # 使用正则替换删除配置段
            self.master_conf = re.sub(pattern, '', self.master_conf)
            self.bind_ip_tag_conf(tag, [])
        return {"status": True, "msg": "删除成功"}

    def del_ip_tag_api(self, get):
        """
        删除IP标签
        @param get:
        @return:
        """
        if not self.master_conf:
            return public.returnMsg(False, '未找到主配置文件master.cf')
        check_main_conf = self.check_main_conf()
        if not check_main_conf['status']:
            return check_main_conf
        result = self.del_ip_tag_conf(get.tags)
        public.writeFile('/etc/postfix/sender_transport', self.sender_transport)
        public.writeFile('/etc/postfix/master.cf', self.master_conf)
        public.ExecShell('postmap /etc/postfix/sender_transport')
        public.ExecShell('postfix reload')
        return result

    def edit_ip_tag_api(self, get):
        """
        编辑IP标签
        @param get:
        @return:
        """
        if not self.master_conf:
            return public.returnMsg(False, '未找到主配置文件master.cf')
        check_main_conf = self.check_main_conf()
        if not check_main_conf['status']:
            return check_main_conf
        # 删除配置段
        self.del_ip_tag_conf(get.tag)
        # 添加配置段
        result = self.add_ip_tag_conf(get.tag, get.ip, get.helo, get.syslog, get.ipv, get.binds.split(',') if get.binds else [])
        # for i in result['bind_success']:
        #     if not i['status']:
        #         return {"status": False, "msg": "编辑失败:{}".format(i['msg']), "bind_success": []}
        result['msg'] = '编辑成功'
        public.writeFile('/etc/postfix/sender_transport', self.sender_transport)
        public.writeFile('/etc/postfix/master.cf', self.master_conf)
        public.ExecShell('postmap /etc/postfix/sender_transport')
        public.ExecShell('postfix reload')
        return result

    def get_net_interface(self, get):
        """
        获取所有真实网卡的IP地址信息
        @param get:
        @return: 格式化后的真实网卡IP信息
        """
        if "refresh" not in get or not get.refresh:
            try:
                result = json.loads(public.readFile('/www/server/panel/config/net_interfaces.json'))
                return {"status": True, "msg": "获取成功", "data": result}
            except:
                pass

        import psutil
        import socket

        # 获取所有网卡
        net_interfaces = psutil.net_if_addrs()

        # 格式化输出，只保留真实网卡的真实IP
        result = {}
        for interface, addresses in net_interfaces.items():
            # 跳过虚拟网卡
            if interface.startswith(('lo', 'docker', 'veth', 'br-', 'tun', 'tap', 'virb')):
                continue
            public.print_log(interface)

            ip_info = []
            for addr in addresses:
                if addr.family == socket.AF_INET:  # IPv4
                    p_ip = public.ExecShell("curl --interface {} https://www.bt.cn/api/getIpAddress --connect-timeout 3 -m 3".format(addr.address))
                    if not p_ip[0]:
                        p_ip = addr.address

                    ip_info.append({
                        "type": "IPv4",
                        "addr": addr.address,
                        "public_ip": p_ip[0],
                        "netmask": addr.netmask
                    })
                elif addr.family == socket.AF_INET6:  # IPv6
                    # 跳过链路本地地址
                    if addr.address.startswith('fe80::'):
                        continue
                    p_ip = public.ExecShell("curl -6 --interface {} https://www.bt.cn/api/getIpAddress --connect-timeout 3 -m 3".format(addr.address))
                    if not p_ip[0]:
                        p_ip = addr.address

                    ip_info.append({
                        "type": "IPv6",
                        "addr": addr.address,
                        "public_ip": p_ip[0],
                        "netmask": addr.netmask
                    })
            # 只添加有IP信息的网卡
            if ip_info:
                result[interface] = ip_info
        public.writeFile('/www/server/panel/config/net_interfaces.json', json.dumps(result))

        return {"status": True, "msg": "获取成功", "data": result}

    def bind_ip_tag_conf(self, tag, binds):
        """
        绑定标签
        @param tag:
        @param binds:
        @return:
        """
        if not self.sender_transport:
            self.sender_transport = ""
        else:
            pattern = re.compile(".*?[\s\S]{}:".format(tag))
            # 使用正则替换删除配置段
            self.sender_transport = re.sub(pattern, '', self.sender_transport).strip()
        success = []
        for bind in binds:
            pattern = re.findall("{bind}[\s\S](.*?):".format(bind=re.escape(bind)), self.sender_transport)
            if pattern:
                success.append({"bind": bind, "status": False, "msg": "{}已绑定:{}".format(bind, pattern[0])})
                continue
            self.sender_transport += "\n{bind} {tag}:".format(bind=bind, tag=tag)
            success.append({"bind": bind, "status": True, "msg": "添加成功"})
        return success

    def add_bind_ip_tag(self, tag, bind):
        """
        添加标签绑定
        @param tag:
        @param bind:
        @return:
        """
        tag_data = self.get_ip_tags_api(public.dict_obj())
        if not tag_data['status']:
            return tag_data
        tags = [i['tag'] for i in tag_data['data']]
        if tag not in tags:
            return public.returnMsg(False, '标签不存在')
        result = self.add_bind_ip_tag_conf(tag, bind)
        public.writeFile('/etc/postfix/sender_transport', self.sender_transport)
        public.ExecShell('postmap /etc/postfix/sender_transport')
        public.ExecShell('postfix reload')
        return result

    def add_bind_ip_tag_conf(self, tag, bind):
        """
        添加标签绑定
        @param tag:
        @param bind:
        @return:
        """
        if not self.sender_transport:
            self.sender_transport = ""
        else:
            pattern = re.findall("{bind}[\s\S](.*?):".format(bind=re.escape(bind)), self.sender_transport)
            if pattern:
                return {"bind": bind, "status": False, "msg": "{}已绑定:{}".format(bind, pattern[0])}
        self.sender_transport += "\n{bind} {tag}:".format(bind=bind, tag=tag)
        return {"bind": bind, "status": True, "msg": "添加成功"}

    def del_bind_ip_tag(self, bind):
        """
        删除标签绑定
        @param tag:
        @param bind:
        @return:
        """
        check_main_conf = self.check_main_conf()
        if not check_main_conf['status']:
            return check_main_conf
        result = self.del_bind_ip_tag_conf(bind)
        public.writeFile('/etc/postfix/sender_transport', self.sender_transport)
        public.ExecShell('postmap /etc/postfix/sender_transport')
        public.ExecShell('postfix reload')
        return result

    def del_bind_ip_tag_conf(self, bind):
        """
        删除标签绑定
        @param tag:
        @param bind:
        @return:
        """
        if not self.sender_transport:
            self.sender_transport = ""
        else:
            pattern = re.compile("{}[\s\S](.*?):".format(re.escape(bind)))
            # 使用正则替换删除配置段
            self.sender_transport = re.sub(pattern, '', self.sender_transport).strip()
        return {"bind": bind, "status": True, "msg": "删除成功"}

    def edit_bind_ip_tag(self, tag, bind):
        """
        编辑标签绑定
        @param tag:
        @param bind:
        @return:
        """
        tag_data = self.get_ip_tags_api(public.dict_obj())
        if not tag_data['status']:
            return tag_data
        # 删除配置段
        self.del_bind_ip_tag_conf(bind)
        if tag:
            tags = [i['tag'] for i in tag_data['data']]
            if tag not in tags:
                return public.returnMsg(False, '标签不存在')
            # 添加配置段
            result = self.add_bind_ip_tag_conf(tag, bind)
            result['msg'] = '编辑成功'
        else:
            result = {"status": True, "msg": "编辑成功"}
        public.writeFile('/etc/postfix/sender_transport', self.sender_transport)
        public.ExecShell('postmap /etc/postfix/sender_transport')
        public.ExecShell('postfix reload')
        return result

    def get_tag_bind(self, tag=None, bind=None):
        """
        获取标签绑定的域名或者邮箱
        @param tag:
        @param bind:
        @return:
        """
        if self.sender_transport is False:
            return []
        if not tag:
            tag = "(.*?)"
            bind = re.escape(bind)
        else:
            tag = re.escape(tag)
            bind = "(.*?)"
        pattern = re.findall("{bind}[\s\S]{tag}:".format(tag=tag, bind=bind), self.sender_transport)
        return pattern

    def tag_get_domain_list(self, get):
        """
        获取当前标签可绑定的域名列表
        @param tag:
        @return:
        """
        domains = self.M('domain').field('domain').select()
        if 'tag' not in get or not get.tag:
            return ["@"+i['domain'] for i in domains]
        can_bind_domains = []
        for domain in domains:
            bind = "@"+domain['domain']
            ip_tag = self.get_tag_bind(bind=bind)
            public.print_log(ip_tag)
            if ip_tag and ip_tag[0] != get.tag:
                continue
            can_bind_domains.append(bind)
        return can_bind_domains

    def get_ip_rotate_conf(self):
        """
        获取IP轮换状态
        @param bind:
        @return:
        """
        path = "/www/server/panel/config/mail_ip_rotate.json"
        try:
            data = json.loads(public.readFile(path))
        except:
            data = {}
        return data

    def set_ip_rotate(self, get):
        """
        设置IP轮换状态
        @param bind:
        @param status:
        @return:
        """
        self.check_ip_rotate_task_status()
        tags = get.tags.split(',')
        if len(tags) < 2:
            return public.returnMsg(False, '标签数量不能小于2')
        # data = self.get_ip_rotate_conf()
        bind = get.bind
        status = True if get.status == "1" else False
        cycle = int(get.cycle)
        return self.set_ip_rotate_conf(bind, tags, cycle, status)

    def set_ip_rotate_conf(self, bind, tags=None, cycle=None, status=None):
        data = self.get_ip_rotate_conf()
        data[bind] = {
            "tags": tags,
            "last_time": time.time()
        }
        if status is not None:
            data[bind]['status'] = status
        if cycle is not None:
            data[bind]['cycle'] = cycle
        public.writeFile("/www/server/panel/config/mail_ip_rotate.json", json.dumps(data))
        return public.returnMsg(True, '设置成功')

    def del_ip_rotate_conf(self, bind):
        """
        删除IP轮换状态
        @param bind:
        @return:
        """
        data = self.get_ip_rotate_conf()
        if bind in data:
            del data[bind]
            public.writeFile("/www/server/panel/config/mail_ip_rotate.json", json.dumps(data))
        return public.returnMsg(True, '删除成功')

    def ip_rotate(self, get=None):
        """
        IP多点切换
        @return:
        """
        data = self.get_ip_rotate_conf()
        now = time.time()

        for domain, value in data.items():
            bind = "@"+domain.strip()
            print("======================{}开始========================".format(bind))
            if not value['status']:
                print("当前IP轮换状态为关闭，跳过")
                continue
            if now - value['last_time'] < value['cycle']*60:
                print("当前IP轮换周期未到，跳过")
                continue
            tags = value['tags']
            now_tag = self.get_tag_bind(bind=bind)
            if not now_tag:
                tag = tags[0]
                print("当前标签不在轮换列表中，取列表中的第一个标签【{}】".format(tag))
            else:
                if now_tag[0] == tags[-1]:
                    tag = tags[0]
                    print("当前标签轮换列表的末尾，取列表中的第一个标签【{}】".format(tag))
                else:
                    tag = tags[(tags.index(now_tag[0]) + 1)]
                    print("切换到下一个标签【{}】".format(tag))
            print("======================{}结束========================".format(bind))
            self.edit_bind_ip_tag(tag, bind)
            data[domain]['last_time'] = now
        public.writeFile("/www/server/panel/config/mail_ip_rotate.json", json.dumps(data))
        return public.returnMsg(True, '切换成功')

    def check_ip_rotate_task_status(self):
        """
        检查任务状态
        @param args:
        @return:
        """
        import crontab
        p = crontab.crontab()
        try:
            c_id = public.M('crontab').where('name=?', u'[勿删] 邮局发邮件IP轮换').getField('id')

            if not c_id:
                data = {}
                data['name'] = u'[勿删] 邮局发邮件IP轮换'
                data['type'] = 'minute-n'
                data['where1'] = '1'
                data['sBody'] = 'btpython /www/server/panel/class/mailModel/script/multi_ip_rotate.py'
                data['backupTo'] = ''
                data['sType'] = 'toShell'
                data['hour'] = ''
                data['minute'] = '1'
                data['week'] = ''
                data['sName'] = ''
                data['urladdress'] = ''
                data['save'] = ''
                p.AddCrontab(data)
                return self.return_msg(public.returnMsg(True, '设置成功!'))
        except Exception as e:
            public.print_log(public.get_error_info())

def _before():
    """
    初始化
    """
    _main = main()
    try:
        tags =_main.get_ip_tags_api(public.dict_obj())
        if not tags['status'] or not tags['data']:
            net_interface = _main.get_net_interface(public.to_dict_obj({"refresh": False}))
            if not net_interface:
                net_interface = _main.get_net_interface(public.to_dict_obj({"refresh": True}))
            _main.advance_create_ip_tag(net_interface)
    except:
        public.print_log(public.get_error_info())
    finally:
        if _main.sender_transport is False:
            public.writeFile("/etc/postfix/sender_transport", "")
        if not os.path.exists("/etc/postfix/sender_transport.db"):
            public.ExecShell('postmap /etc/postfix/sender_transport')
_before()
del _before
