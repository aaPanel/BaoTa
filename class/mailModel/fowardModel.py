import json
import re
import sys
import time

from mailModel.base import Base
sys.path.append("class/")
import public

class main(Base):
    def __init__(self):
        pass

    def check_main_conf(self, get=None):
        """
        检查主配置文件
        @return:
        """
        main_conf = public.readFile("/etc/postfix/main.cf")
        if not main_conf:
            return {"status": False, "msg": "主配置文件不存在"}
        conf = "virtual_alias_maps = sqlite:/etc/postfix/sqlite_virtual_alias_new_maps.cf, sqlite:/etc/postfix/sqlite_virtual_alias_domain_new_maps.cf, sqlite:/etc/postfix/sqlite_virtual_alias_domain_catchall_new_maps.cf, sqlite:/etc/postfix/bt_catchnone_maps.cf"
        if conf not in main_conf:
            public.print_log("主配置文件检查不通过，开始修改")
            main_conf = re.sub(r'virtual_alias_maps\s*=.*', conf, main_conf)
            public.writeFile("/etc/postfix/main.cf", main_conf)
        return {"status": True, "msg": "主配置文件检查完成"}

    def check_maps_conf(self, get=None):
        """
        检查maps配置文件
        @return:
        """
        if public.FileMd5("/etc/postfix/sqlite_virtual_alias_new_maps.cf") != "11ea7f20ced0b1b5cfff7aa8bb818600":
            public.print_log("开始下载maps配置文件")
            public.ExecShell(
                'wget -O /etc/postfix/sqlite_virtual_alias_new_maps.cf {}/mail_sys/postfix/sqlite_virtual_alias_new_maps.cf -T 10'.format(
                    public.get_url()))
        if public.FileMd5("/etc/postfix/sqlite_virtual_alias_domain_new_maps.cf") != "523b9217adfb715b1e0badd874e30904":
            public.print_log("开始下载maps配置文件")
            public.ExecShell(
                'wget -O /etc/postfix/sqlite_virtual_alias_domain_new_maps.cf {}/mail_sys/postfix/sqlite_virtual_alias_domain_new_maps.cf -T 10'.format(
                    public.get_url()))
        if public.FileMd5("/etc/postfix/sqlite_virtual_alias_domain_catchall_new_maps.cf") != "a6c4368fef0b6c27be690f354e970344":
            public.print_log("开始下载maps配置文件")
            public.ExecShell(
                'wget -O /etc/postfix/sqlite_virtual_alias_domain_catchall_new_maps.cf {}/mail_sys/postfix/sqlite_virtual_alias_domain_catchall_new_maps.cf -T 10'.format(
                    public.get_url()))
        if public.FileMd5("/etc/postfix/bt_catchnone_maps.cf") != "d41d9d8159ada493f1278ab737e1c47c":
            public.print_log("开始下载maps配置文件")
            public.ExecShell(
                'wget -O /etc/postfix/bt_catchnone_maps.cf {}/mail_sys/postfix/bt_catchnone_maps.cf -T 10'.format(
                    public.get_url()))
        return {"status": True, "msg": "maps配置文件检查完成"}

    def get_mail_forward(self, get):
        """
        获取邮件转发
        @param get:
        @return:
        """
        dtype = "0"
        if "dtype" in get:
            dtype = get.dtype
        if dtype == "1":
            data = self.M("alias_domain").field('alias_domain as address,alias_domain as domain,alias_domain as forwarder,target_domain as goto,created,modified,active').order('created desc').select()
        else:
            data = self.M("alias").order('created desc').select()
            for i in data:
                user = i["address"].split("@")[0]
                if not user:
                    i["rule"] = "none"
                    i["rule_str"] = ""
                    i["forwarder"] = "[不存在的邮箱]"
                else:
                    if user == "%":
                        i["rule"] = "all"
                        i["rule_str"] = ""
                        i["forwarder"] = "[全部邮箱]"
                    elif user[0] == "%" and user[-1] == "%":
                        i["rule"] = "contain"
                        i["rule_str"] = user[1:-1]
                        i["forwarder"] = "包含[{}]的邮箱".format(user[1:-1])
                    elif user[0] == "%":
                        i["rule"] = "suffix"
                        i["rule_str"] = user[1:]
                        i["forwarder"] = "以[{}]结尾的邮箱".format(user[1:])
                    elif user[-1] == "%":
                        i["rule"] = "prefix"
                        i["rule_str"] = user[:-1]
                        i["forwarder"] = "以[{}]开头的邮箱".format(user[:-1])
                    else:
                        i["rule"] = ""
                        i["rule_str"] = ""
                        i["forwarder"] = i["address"]
                i["goto"] = i["goto"].replace(",", "\n")
        return {"status": True, "msg": "", "data": data}

    def add_forward(self, get):
        """
        添加邮件转发
        @param get:
        @return:
        """
        modified_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        if get.forward_type == "1":
            if self.M("alias_domain").where("alias_domain=?", (get.domain,)).count() > 0:
                return {"status": False, "msg": "域名【{}】转发规则已存在".format(get.domain)}
            self.M("alias_domain").add("alias_domain,target_domain,created,modified,active",
                                       (get.domain, get.receiver, modified_time, modified_time, int(get.status)))
        else:
            if "rule"not in get or not get.rule:
                if not get.rule_str:
                    return {"status": False, "msg": "被转发邮箱不能为空", "bind_success": []}
                address = get.rule_str
            elif get.rule in ("all","none") :
                if get.rule == "all":
                    address = "%@"+get.domain
                    if self.M("alias").where("address=?", ("@"+get.domain,)).count() > 0:
                        return {"status": False, "msg": "同一域名，捕获全部邮箱转发和捕获不存在的邮箱转发不能同时存在"}
                else:
                    address = "@"+get.domain
                    if self.M("alias").where("address=?", ("%@"+get.domain,)).count() > 0:
                        return {"status": False, "msg": "同一域名，捕获全部邮箱转发和捕获不存在的邮箱转发不能同时存在"}
            elif get.rule in ("contain","suffix","prefix"):
                if len(get.rule_str) > 10:
                    return {"status": False, "msg": "规则内容长度不能大于10", "bind_success": []}
                if not re.match(r"^[a-zA-Z0-9_]+$", get.rule_str):
                    return {"status": False, "msg": "规则内容只能包含字母、数字和下划线", "bind_success": []}
                if get.rule == "contain":
                    address = "%"+get.rule_str+"%@"+get.domain
                elif get.rule == "suffix":
                    address = "%"+get.rule_str+"@"+get.domain
                else:
                    address = get.rule_str+"%@"+get.domain
            else:
                return {"status": False, "msg": "规则错误"}
            if self.M("alias").where("address=?", (address,)).count() > 0:
                return {"status": False, "msg": "此规则已存在，请勿重复添加"}
            receiver = get.receiver.strip().replace("\n", ",")

            self.M("alias").add("address,goto,domain,created,modified,active",
                                (address, receiver, get.domain, modified_time, modified_time, int(get.status)))
        return {"status": True, "msg": "添加成功"}

    def edit_forward(self, get):
        """
        编辑邮件转发
        @param get:
        @return:
        """
        modified_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        if get.forward_type == "1":
            self.M("alias_domain").where("alias_domain=?", (get.address,)).update(
                {"target_domain": get.receiver, "modified": modified_time, "active": int(get.status)})
        else:
            receiver = get.receiver.strip().replace("\n", ",")
            self.M("alias").where("address=?", (get.address,)).update(
                {"goto": receiver, "modified": modified_time, "active": int(get.status)})
        return {"status": True, "msg": "修改成功"}

    def del_forward(self, get):
        """
        删除邮件转发
        @param get:
        @return:
        """
        address = get.address.split(",")
        if get.forward_type == "1":
            self.M("alias_domain").where("alias_domain in ('{}')".format("','".join(address)), ()).delete()
        else:
            self.M("alias").where("address in ('{}')".format("','".join(address)), ()).delete()
        return {"status": True, "msg": "删除成功"}

def _conf():
    try:
        main().check_main_conf()
        main().check_maps_conf()
        public.ExecShell("postfix reload")
    except:
        public.print_log(public.get_error_info())
_conf()
del _conf






