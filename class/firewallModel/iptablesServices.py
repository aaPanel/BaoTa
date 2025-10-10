import subprocess
import sys

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
import public
from firewallModel.app.appBase import Base

class IptablesServices(Base):
    def __init__(self):
        pass

    def set_chain_rich_ip(self, info, operation, chain):
        '''
            @name 添加/删除指定链的复杂ip规则
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            if "Address" in info and info["Address"] == "":
                return self._result(False, "设置规则失败:{}".format("IP地址不能为空"))
            if "Address" in info and public.is_ipv6(info['Address']):
                return self._result(False, "设置规则失败:{}".format("不支持的IPV6地址"))

            if "Timeout" not in info or info["Timeout"] == "":
                info["Timeout"] = 0

            if chain == "INPUT":
                chain = 'in'
            else:
                chain = 'out'

            if operation == "add":
                exec_cmd = "ipset add {}_bt_user_{}_ipset {} timeout {}".format(chain,info["Strategy"],info["Address"],info["Timeout"])
            else:
                exec_cmd = "ipset del {}_bt_user_{}_ipset {}".format( chain, info["Strategy"], info["Address"])

            stdout, stderr = public.ExecShell(exec_cmd)
            if stderr:
                return self._result(False, "设置规则失败:{}".format(stderr))

            return self._result(True, "设置规则成功")
        except Exception as e:
            return self._result(False, "设置规则失败:{}".format(str(e)))

    def rich_rules(self,info, operation, chain):
        '''
            @name
            @author csj <2025/3/12 上午9:28>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if "Priority" in info and not "Port" in info:
            return self.set_chain_rich_ip(info, operation, chain)
        else:
            pass
            # 端口类型暂时不用新版
            # return self.set_chain_rich_port(info, operation, "INPUT")

    # 2024/4/29 下午4:01 获取指定链的数据
    def get_chain_data(self, chain):
        '''
            @name 获取指定链的数据
            @author wzz <2024/4/29 下午4:01>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return [
                       {
                          "Family": "ipv4",
                          "Address": "192.168.1.190",
                          "Strategy": "accept",
                          "Chain": "INPUT",
                          "Timeout": timeout
                       }
                    ]
        '''
        if chain == "INPUT":
            ipset_chain = "in"
        elif chain == "OUTPUT":
            ipset_chain = "out"
        else:
            return []

        rules = []
        try:
            for strategy in ["accept", "drop"]:
                ipset_cmd = "ipset list {}_bt_user_{}_ipset | awk '/[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+/ && /timeout/ {{print $1, $3}}'".format(ipset_chain, strategy)

                stdout, stderr = public.ExecShell(ipset_cmd)
                iplist = stdout.split("\n")

                for line in iplist:
                    if line == "": continue
                    address = line.strip().split(" ")[0]
                    timeout = line.strip().split(" ")[1]
                    rule = {
                        "Family": "ipv4",
                        "Address": address,
                        "Strategy": strategy,
                        "Chain": chain,
                        "Timeout": timeout
                    }
                    rules.append(rule)
            return rules
        except Exception as e:
            return ""

    def list_address(self,chains:list = ["INPUT","OUTPUT"]):
        """
        获取指定链的ipset列表
        :param chains: 链列表 ["INPUT","OUTPUT"]
        """
        result = []
        for chain in chains:
            result = result + self.get_chain_data(chain)
        return result

    def parse_rules(self, stdout):
        '''
            @name 解析规则列表输出，返回规则列表字典
            @author wzz <2024/3/19 下午 3:53>
                字段含义:
                    "number": 规则编号，对应规则在链中的顺序。
                    "chain": 规则所属的链的名称。
                    "pkts": 规则匹配的数据包数量。
                    "bytes": 规则匹配的数据包字节数。
                    "target": 规则的目标动作，表示数据包匹配到该规则后应该执行的操作。
                    "prot": 规则适用的协议类型。
                    "opt": 规则的选项，包括规则中使用的匹配条件或特定选项。
                    "in": 规则匹配的数据包的输入接口。
                    "out": 规则匹配的数据包的输出接口。
                    "source": 规则匹配的数据包的源地址。
                    "destination": 规则匹配的数据包的目标地址。
                    "options": 规则的其他选项或说明，通常是规则中的注释或附加信息。

                protocol(port协议头中数字对应的协议类型):
                    0: 表示所有协议
                    1: ICMP（Internet 控制消息协议）
                    6: TCP（传输控制协议）
                    17: UDP（用户数据报协议）
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        lines = stdout.strip().split('\n')
        rules = []
        current_chain = None
        for line in lines:
            if line.startswith("Chain"):
                current_chain = line.split()[1]
            elif (line.startswith("target") or line.strip() == "" or "source" in line or
                  "Warning: iptables-legacy tables present" in line):
                # 过滤表头,空行,警告
                continue
            else:
                rule_info = line.split()
                rule = {
                    "number": rule_info[0],
                    "chain": current_chain,
                    "pkts": rule_info[1],
                    "bytes": rule_info[2],
                    "target": rule_info[3],
                    "prot": rule_info[4],
                    "opt": rule_info[5],
                    "in": rule_info[6],
                    "out": rule_info[7],
                    "source": rule_info[8],
                    "destination": rule_info[9],
                    "options": " ".join(rule_info[10:]).strip()
                }
                rules.append(rule)
        return rules

    def list_rules(self, parm):
        '''
            @name 列出指定表的指定链的规则
            @author wzz <2024/3/19 下午 3:02>
            @param
            @return
        '''
        try:
            stdout = subprocess.check_output(
                ['iptables', '-t', parm['table'], '-L', parm['chain_name'], '-nv', '--line-numbers'],
                stderr=subprocess.STDOUT, universal_newlines=True
            )
            return self.parse_rules(stdout)
        except Exception as e:
            return []

    def list_port_forward(self):
        '''
            @name 调用list_rules获取所有nat表中的PREROUTING链的规则(端口转发规则),并分析成字典返回
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            port_forward_rules = self.list_rules({"table": "nat", "chain_name": "FORWARD_BT"})
            rules = []
            for rule in port_forward_rules:
                rule_item={
                    "type": "port_forward",
                    "number": rule["number"],
                    "S_Address": rule["source"],
                    "S_Port": "",
                    "T_Address": "",
                    "T_Port": "",
                    "Protocol": "TCP"
                }

                options = rule["options"].split(' ')
                if rule["target"] == "DNAT": # 外部转发 有IP
                    rule_item["S_Port"] = options[1].split("dpt:")[1]
                    rule_item["T_Address"] = options[2].split("to:")[1].split(":")[0]
                    rule_item["T_Port"] = options[2].split("to:")[1].split(":")[1]
                elif rule["target"] == "REDIRECT": # 内部转发无IP
                    rule_item["S_Port"] = options[1].split("dpt:")[1]
                    rule_item["T_Address"] = "127.0.0.1"
                    rule_item["T_Port"] = options[-1]
                else:
                    continue

                if rule["prot"] == "6" or rule["prot"] == "tcp":
                    rule_item["Protocol"] = "TCP"
                elif rule["prot"] == "17" or rule["prot"] == "udp":
                    rule_item["Protocol"] = "UDP"

                rules.append(rule_item)
            return rules
        except Exception as e:
            return []

    def port_forward(self,info,operation):
        """
        设置端口转发规则
        :param info: 规则信息
        :param operation: 操作类型 add/del
        """
        to_addr = info["T_Address"]

        if operation == "add":
            operation = "A"
        else:
            operation = "D"

        is_lo = False
        if to_addr == "" or to_addr == "0.0.0.0" or to_addr == "127.0.0.1" or to_addr=="0.0.0.0/0":
            is_lo = True

        if is_lo :
            # iptables -t nat -A FORWARD_BT -p tcp --dport 3330 -j REDIRECT --to-port 7777
            exec_cmd = "iptables -t nat -{operation} FORWARD_BT -p {proto} --dport {sport} -j REDIRECT --to-port {tport}".format(
                operation=operation,proto=info["Protocol"],sport=info["S_Port"],tport=info["T_Port"])
        else:
            # "iptables -t nat -A FORWARD_BT -p tcp --dport 3331 -j DNAT --to-destination 192.168.69.135:7777"
            exec_cmd = "iptables -t nat -{operation} FORWARD_BT -p {proto} --dport {sport} -j DNAT --to-destination {taddr}:{tport}".format(
                operation=operation,proto=info["Protocol"],addr=info["S_Address"],sport=info["S_Port"],taddr=to_addr,tport=info["T_Port"])
        # public.print_log(exec_cmd)
        stdout, stderr = public.ExecShell(exec_cmd)
        if stderr:
            return self._result(False, "设置规则失败:{}".format(stderr))
        public.ExecShell("systemctl reload BT-FirewallServices")
        return self._result(True, "设置规则成功")