
import os, sys,time

os.chdir('/www/server/panel/')
sys.path.insert(0, "class/")
sys.path.insert(0, "/www/server/panel/")
import public

__isFirewalld=False
__isUfw=False

if os.path.exists('/usr/sbin/firewalld') and os.path.exists('/usr/bin/yum'):
    __isFirewalld = True
if os.path.exists('/usr/sbin/ufw') and os.path.exists('/usr/bin/apt-get'):
    __isUfw = True

def check_ipset_exist(ipset_name):
    cmd = "ipset list {}|grep Name".format(ipset_name)
    res,err = public.ExecShell(cmd)
    if err!= "":
        return False
    return True


def firewalld_process_zone_file(zone_path, rule_dict, zone_name):
    """
    处理zone文件（public.xml或trusted.xml），删除匹配的规则。

    参数:
        zone_path (str): zone文件路径
        rule_dict (dict): 规则字典
        zone_name (str): Zone名称（'public'或'trusted'）
    """
    if not os.path.exists(zone_path):
        return
    import xml.etree.ElementTree as ET
    tree = ET.parse(zone_path)
    root = tree.getroot()
    # 处理<rule>标签
    for rule in root.findall('rule'):
        source = rule.find('source')
        if source is not None:
            ip = source.get('address')
            action = None
            if rule.find('accept') is not None:
                action = 'ACCEPT'
            elif rule.find('drop') is not None:
                action = 'DROP'
            if (ip in rule_dict and
                    rule_dict[ip]['Chain'].upper() == 'INPUT' and
                    rule_dict[ip]['Zone'] == zone_name and
                    rule_dict[ip]['Strategy'].upper() == action.upper()):
                root.remove(rule)
    if zone_name == 'trusted':
        for source in root.findall('source'):
            ip = source.get('address')
            if (ip in rule_dict and
                    rule_dict[ip]['Chain'].upper() == 'INPUT' and
                    rule_dict[ip]['Zone'] == 'trusted' and
                    rule_dict[ip]['Strategy'].upper() == 'ACCEPT'):
                root.remove(source)
    tree.write(zone_path)

def firewalld_process_direct_file(direct_path, rule_dict):
    """
    处理direct.xml文件，删除匹配的OUTPUT规则。
    参数:
        direct_path (str): direct.xml文件路径
        rule_dict (dict): 规则字典
    """
    if not os.path.exists(direct_path):
        return
    import xml.etree.ElementTree as ET
    tree = ET.parse(direct_path)
    root = tree.getroot()
    for rule in root.findall('rule'):
        if rule.get('chain') == 'OUTPUT':
            rule_text = rule.text.strip()
            if rule_text.startswith('-d '):
                parts = rule_text.split()
                ip = parts[1]
                action = parts[-1]
                if (ip in rule_dict and
                        rule_dict[ip]['Chain'].upper() == 'OUTPUT' and
                        rule_dict[ip]['Strategy'].upper() == action.upper()):
                    root.remove(rule)
    tree.write(direct_path)

def firewalld_batch_remove_ip_rule(rule_dict):
    direct_path = '/etc/firewalld/direct.xml'
    public_path = '/etc/firewalld/zones/public.xml'
    trusted_path = '/etc/firewalld/zones/trusted.xml'
    import shutil

    if os.path.exists(public_path):
        shutil.copyfile(public_path, public_path + '.bak')
        firewalld_process_zone_file(public_path, rule_dict, 'public')
    if os.path.exists(trusted_path):
        shutil.copyfile(trusted_path, trusted_path + '.bak')
        firewalld_process_zone_file(trusted_path, rule_dict, 'trusted')
    if os.path.exists(direct_path):
        shutil.copyfile(direct_path, direct_path + '.bak')
        firewalld_process_direct_file(direct_path, rule_dict)

def ufw_batch_remove_ip_rule(rule_dict):
    """
    UFW批量删除规则
    """
    ufw_config = '/etc/ufw/user.rules'
    import shutil
    shutil.copy(ufw_config, ufw_config+".bak"+public.format_date())

    lines = public.readFile(ufw_config)
    lines = lines.splitlines()
    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        if line.startswith('### tuple ###'):
            parts = line.split()
            action = parts[3]  # deny 或 allow
            direction = parts[-1]  # in 或 out
            ip = parts[-2]  # IP 地址

            if ip == '0.0.0.0/0':
                new_lines.extend(lines[i:i + 3])  # 保留这三行
                i += 3
                continue

            chain = 'INPUT' if direction == 'in' else 'OUTPUT' if direction == 'out' else ""
            strategy = 'DROP' if action == 'deny' else 'ACCEPT' if action == 'allow' else ""

            if (ip in rule_dict and
                    chain.upper() == rule_dict[ip]['Chain'].upper() and
                    strategy.upper() == rule_dict[ip]['Strategy'].upper()):
                # 如果匹配，跳过这三行（即删除）
                i += 3
            else:
                # 如果不匹配，保留这三行
                new_lines.extend(lines[i:i + 3])
                i += 3
        else:
            # 如果不是规则的开始行，直接保留
            new_lines.append(lines[i])
            i += 1
    with open(ufw_config, 'w') as file:
        file.writelines(line if line.endswith('\n') else line + '\n' for line in new_lines)

#9.5.0-9.6.0
def upgrade_iprule(commodel):
    list_address = commodel.firewall.list_address()
    if len(list_address)==0:
        return

    rule_dict = {}
    print("-* 正在迁移IP规则数据...")
    for item in list_address:
        print("迁移IP规则:{}".format(item))
        commodel.iptables.set_chain_rich_ip(item, 'add', item['Chain'])
        rule_dict[item['Address']] = {
            "Address": item['Address'],
            "Family": item['Family'],
            "Strategy": item['Strategy'],
            "Zone": item.get('Zone'),
            "Chain": item['Chain']
        }

    if __isFirewalld:
        firewalld_batch_remove_ip_rule(rule_dict)
    elif __isUfw:
        ufw_batch_remove_ip_rule(rule_dict)
    else:
        return
    commodel.firewall.reload()
    public.ExecShell("systemctl reload BT-FirewallServices")
    print("-* IP规则数据迁移完成...")
#9.5.0-9.6.0
def upgrade_countrys(commodel):
    country_list = public.M('firewall_country').select()
    if len(country_list)==0:
        return

    from safeModel.firewallModel import main as firewallModel
    firewallmodel = firewallModel()

    print("-* 正在迁移地区规则数据...")
    for country in country_list:
        ports = country['ports']
        brief = country['brief']
        types = country['types']

        print("迁移地区规则:{}".format(brief))
        if __isUfw or not __isFirewalld:
            if not ports:
                public.ExecShell('iptables -D INPUT -m set --match-set ' + brief + ' src -j ' + types.upper())
            else:
                public.ExecShell('iptables -D INPUT -m set --match-set ' + brief + ' src -p tcp --destination-port ' + ports + ' -j ' + types.upper())
        else:
            if not ports:
                o,e = public.ExecShell("firewall-cmd --permanent --direct --remove-rule ipv4 filter INPUT 0 -m set --match-set {} src -j {}".format(brief, types.upper()))
                if e!= '':
                    public.ExecShell('firewall-cmd --permanent --remove-rich-rule=\'rule source ipset="{}" {}\''.format(brief, types.upper()))
            else:
                o,e = public.ExecShell('firewall-cmd --permanent --direct --remove-rule ipv4 filter INPUT 0 -m set --match-set {} src -p tcp --dport {} -j {}'.format(brief, ports, types.upper()))
                if e != '':
                    public.ExecShell('firewall-cmd --permanent --remove-rich-rule=\'rule source ipset="' + brief + '" port port="' + ports + '" protocol=tcp ' + types.upper() + '\'')

    commodel.firewall.reload()
    for country in country_list:
        ports = country['ports']
        brief = country['brief']
        types = country['types']

        print("迁移地区规则:{}".format(brief))
        o,e = public.ExecShell("ipset destroy " + brief)
        if e != '':
            public.ExecShell("firewall-cmd --permanent --delete-ipset="+brief)

        tmp_file = "/tmp/firewall_{}.txt".format(brief)
        if os.path.exists(tmp_file): #9.5.0之后
            command = '''grep -q "in_bt_country" {filename} || awk '{{print "add in_bt_country_" $2, $3}}' {filename} > {filename}.tmp && mv {filename}.tmp {filename}'''.format(filename=tmp_file)
            public.ExecShell(command)

            _ipset = "in_bt_country_" + brief
            public.ExecShell('ipset create {} hash:net maxelem 1000000; ipset restore -f {}'.format(_ipset, tmp_file))

            if ports:
                public.ExecShell('iptables -I IN_BT_Country -m set --match-set {} src -p tcp --destination-port {} -j {}'.format(_ipset, ports, types.upper()))
            else:
                public.ExecShell('iptables -I IN_BT_Country -m set --match-set {} src -j {}'.format(_ipset, types.upper()))

            public.ExecShell("systemctl reload BT-FirewallServices")
        else:  #9.5.0之前
            public.M("firewall_country").where("id=?", (country['id'],)).delete()
            get_tmp = public.dict_obj()
            get_tmp.country = country['country']
            get_tmp.types = country['types']
            get_tmp.ports = country['ports']
            get_tmp.choose = "all"
            get_tmp.is_update = True
            res = firewallmodel.create_countrys(get_tmp)
            if res['status'] == False:
                print("迁移地区规则失败:{}".format(res['msg']))
    print("-* 地区规则数据迁移完成...")
#9.5.0-9.6.0
def upgrade_malicious_ip():
    pl_path = "/www/server/panel/config/firewalld_malicious_ip.pl"
    if not os.path.exists(pl_path):
        return

    if not check_ipset_exist("malicious_ipset"):
        return

    print("-* 正在迁移恶意IP封禁数据...")
    # 移除旧规则
    if __isUfw or not __isFirewalld:
        public.ExecShell('rm -rf /var/log/FIREWALL-ACCESS-LOG*')
        public.ExecShell('rm -rf /etc/rsyslog.d/firewall-access-log.conf')
        public.ExecShell('rm -rf /etc/logrotate.d/firewall-access-log')
        public.ExecShell('iptables -D INPUT -m conntrack --ctstate NEW -j LOG --log-prefix "FIREWALL-ACCESS: " --log-level 4')
        public.ExecShell('iptables -D INPUT -j IP-DAILY-LOG')
        public.ExecShell('iptables -D IP-DAILY-LOG -m recent --name DAILY_IPS --rcheck --seconds 86400 -j RETURN')
        public.ExecShell('iptables -D IP-DAILY-LOG -m recent --name DAILY_IPS --set -j LOG --log-prefix "DAILY-IP: " --log-level 4')
        public.ExecShell('iptables -D IP-DAILY-LOG -j RETURN')
        public.ExecShell('iptables -X IP-DAILY-LOG')
        public.ExecShell("iptables -D INPUT -m set --match-set malicious_ipset src -j DROP")
    else:
        public.ExecShell("firewall-cmd --permanent --direct --remove-rule ipv4 filter INPUT 1 -m conntrack --ctstate NEW -j LOG --log-prefix 'FIREWALL-ACCESS: ' --log-level 4")
        public.ExecShell("firewall-cmd --permanent --direct --remove-rule ipv4 filter INPUT 2 -j IP-DAILY-LOG")
        public.ExecShell("firewall-cmd --permanent --direct --remove-rule ipv4 filter IP-DAILY-LOG 0 -m recent --name DAILY_IPS --rcheck --seconds 86400 -j RETURN")
        public.ExecShell("firewall-cmd --permanent --direct --remove-rule ipv4 filter IP-DAILY-LOG 1 -m recent --name DAILY_IPS --set -j LOG --log-prefix 'DAILY-IP: ' --log-level 4")
        public.ExecShell("firewall-cmd --permanent --direct --remove-rule ipv4 filter IP-DAILY-LOG 2 -j RETURN")
        public.ExecShell("firewall-cmd --permanent --direct --remove-chain ipv4 filter IP-DAILY-LOG")
        public.ExecShell("firewall-cmd --permanent --direct --remove-rule ipv4 filter INPUT 0 -m set --match-set malicious_ipset src -j DROP")
    commodel.firewall.reload()
    public.ExecShell("ipset destroy malicious_ipset")

    read = public.readFile(pl_path)
    if read.strip() == "open":
        tmp_file = "/tmp/firewall_malicious_ip.txt"
        command = '''grep -q "in_bt" {filename} || awk '{{print "add in_bt_" $2, $3 ,"timeout", 86400}}' {filename} > {filename}.tmp && mv {filename}.tmp {filename}'''.format(filename=tmp_file)
        public.ExecShell(command)
        public.ExecShell("sh /www/server/panel/script/open_malicious_ip.sh")
        public.ExecShell("ipset restore -f {}".format(tmp_file))
    public.ExecShell("systemctl reload BT-FirewallServices")
    print("-* 恶意IP封禁数据迁移完成...")

def upgrade_port_forward(commodel):
    """
    升级端口转发规则
    """
    port_forward_list = commodel.firewall.list_port_forward()
    print("-* 正在迁移端口转发规则数据...")
    for port_forward in port_forward_list:
        print("迁移端口转发规则:{}".format(port_forward))
        info = {
            "Family": "ipv4",
            "Protocol": port_forward["Protocol"],
            "S_Address": port_forward['S_Address'],
            "S_Port": port_forward['S_Port'],
            "T_Address": port_forward['T_Address'],
            "T_Port": port_forward['T_Port'],
        }
        commodel.firewall.port_forward(info,"remove")
        commodel.iptables.port_forward(info,"add")
    public.ExecShell("systemctl reload BT-FirewallServices")
    commodel.firewall.reload()
    print("-* 端口转发规则数据迁移完成...")

if __name__ == '__main__':
    from firewallModel.comModel import main as comModel
    commodel = comModel()

    upgrade_iprule(commodel)
    upgrade_countrys(commodel)
    upgrade_malicious_ip()
    upgrade_port_forward(commodel)
    # for i in range(100):
    #     time.sleep(0.1)
    #     print("正在执行...")
    print("程序运行结束...")
