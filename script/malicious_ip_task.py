# coding: utf-8
import os, sys, time, re, json

os.chdir('/www/server/panel/')
sys.path.insert(0, "class/")
sys.path.insert(0, "/www/server/panel/")

import public
import requests

__isFirewalld = False
__isUfw = False

if os.path.exists('/usr/sbin/firewalld') and os.path.exists('/usr/bin/yum'):
    __isFirewalld = True
if os.path.exists('/usr/sbin/ufw') and os.path.exists('/usr/bin/apt-get'):
    __isUfw = True

def get_malicious_ip(page = 1):
    """
    从官网获取恶意IP情报库
    :param get:
    :return:
    """
    page_size = 10000

    userinfo = public.get_user_info()
    url = "https://www.bt.cn/api/bt_waf/get_system_malicious?x_bt_token=SksBSpWhJE7oVRixKCAZVEsN3QDnfQBU&page={}&size={}&uid={}&serverid={}&access_key={}".format(page,page_size,userinfo['uid'], userinfo['serverid'], userinfo['access_key'])
    res = requests.get(url).json()

    if res["success"]:
        total = res["res"]["total"] #数据总量
        ip_list = set(res["res"]["list"].keys())
        #处理是否下一页
        if total > page_size*page:
            page += 1
            return ip_list | get_malicious_ip(page)
        return ip_list
    else:
        print("每天最多只能同步五次恶意IP库~",res["res"])
        return set()

def clean_log():
    public.ExecShell("echo -n > /var/log/IP-DAILY-LOG.log")

def get_ban_time():
    """
    获取封禁时间
    """
    ban_time = 1
    firewall_config = public.readFile("/www/server/panel/config/firewall_config.json")
    if firewall_config:
        firewall_config = json.loads(firewall_config)
        ban_time = firewall_config.get("maliciousip_ban_time")
        if ban_time is None:
            ban_time = 1
    ban_time = int(ban_time)*86400
    return ban_time

def process_access_ip(malicious_ip_list):
    """
    处理iptables日志文件，获取IP访问情况 与情报库对比
    """
    ban_ip_list = set()
    logs = public.readFile("/var/log/IP-DAILY-LOG.log")
    if not logs:
        print("日志还未产生 稍等系统日志产生后再次运行")
        return ban_ip_list

    logs = logs.split("\n")
    for log in logs:
        if not log: continue
        try:
            pattern = r"SRC=(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
            match = re.search(pattern, log)
            if match:
                access_ip = match.group(1).strip()
            else:
                continue
        except:
            continue
        if access_ip in malicious_ip_list:
            ban_ip_list.add(access_ip)
    return ban_ip_list

def reload_firewall():
    """
    重载防火墙
    """
    if __isUfw or not __isFirewalld:
        public.ExecShell('/usr/sbin/ufw reload')
    else:
        public.ExecShell("firewall-cmd --reload")

def clean_iptables(ban_time):
    """
    清理过期ip
    """
    nowtime = time.time()
    malicious_ip_list = public.M('firewall_malicious_ip').select()
    for ip in malicious_ip_list:
        addtime = time.mktime(time.strptime(ip['addtime'], '%Y-%m-%d %X'))
        if nowtime - addtime > ban_time:
            public.M('firewall_malicious_ip').where('id=?', (ip['id'],)).delete()
            public.ExecShell('ipset del in_bt_malicious_ipset {}'.format(ip['address']))

def process_iptables(ban_ip_list):
    """
    通过iptables封禁恶意IP
    :param ban_ip_list:
    :return:
    """
    ban_time = get_ban_time()
    print("IP封禁时间(s)：",ban_time)
    if ban_time != 0:
        clean_iptables(ban_time)

    firewall_malicious_path = "/tmp/firewall_malicious_ip.txt"
    tmp_file = open(firewall_malicious_path, 'w')
    _string = ""
    for ip in ban_ip_list:
        _string = _string + "add {} {} timeout {}\n".format("in_bt_malicious_ipset", ip,ban_time)
    tmp_file.write(_string)
    tmp_file.close()

    public.ExecShell('ipset restore -f {}'.format(firewall_malicious_path))

    reload_firewall()
    add_time = time.strftime('%Y-%m-%d %X', time.localtime())
    for ip in ban_ip_list:
        public.M('firewall_malicious_ip').add('address,brief,addtime',(ip, "", add_time))

if __name__ == '__main__':
    print("===自动封禁恶意IP运行开始===")
    malicious_ip_list = get_malicious_ip()
    print("从官网同步恶意IP总量：",len(malicious_ip_list))
    malicious_access_ip = process_access_ip(malicious_ip_list)
    print("本次运行封禁恶意IP数量:",len(malicious_access_ip))
    process_iptables(malicious_access_ip)
    clean_log()
    print("===自动封禁恶意IP运行结束===")