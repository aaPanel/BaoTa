import os, sys, time, dns

os.chdir('/www/server/panel')
sys.path.append('class/')
import public
try:
    import dns.resolver
except:
    if os.path.exists('/www/server/panel/pyenv'):
        public.ExecShell('/www/server/panel/pyenv/bin/pip install dnspython')
    else:
        public.ExecShell('pip install dnspython')
    import dns.resolver


def cron_shell():
    from safeModel import firewallModel
    firewallobj = firewallModel.main()
    conf = public.M('firewall_domain').select()
    domain_name_dict = {}
    old_a_ip_dict = {}
    #整理所有的域名规则
    for ii in conf:
        domain_name = ii['domain'].split('|')[0]
        if domain_name not in domain_name_dict.keys():
            domain_name_dict[domain_name] = []
            old_a_ip_dict[domain_name] = []
        domain_name_dict[domain_name].append(ii)
        old_a_ip_dict[domain_name].append(ii['address'])
    is_reload = False
    # print(domain_name_dict)
    for i3 in domain_name_dict.keys():
        a_ip = firewallobj.get_a_ip(i3)
        # a_ip = firewallobj.check_a_ip(a_ip)
        if a_ip and len(a_ip) < 2 and public.is_domain(a_ip[0]):
            # return 111
            a_ip = [firewallobj.check_a_ip(a_ip[0])]
        # 当域名解析IP为空，跳过
        if not a_ip: continue
        #域名解析IP数量
        a_ip_num = len(a_ip)
        old_num = len(domain_name_dict[i3])
        #取交集
        intersection_list = list(set(old_a_ip_dict[i3]).intersection(a_ip))
        # print(a_ip)
        #取a_ip中不在old_a_ip_dict[i3]中的IP
        a_ip_difference = list(set(a_ip).difference(old_a_ip_dict[i3]))
        #取old_a_ip_dict[i3]中不在a_ip中的IP
        i3_difference = list(set(old_a_ip_dict[i3]).difference(a_ip))
        #当域名解析IP比原来减少时
        if a_ip_num < old_num:
            pass
        #当域名解析IP比原来增加时
        elif a_ip_num > old_num:
            pass
        #当域名解析IP数量不变时
        else:
            #当交集为空时，说明域名全部解析IP发生变化
            if not intersection_list:
                for i4 in domain_name_dict[i3]:
                    # if i4['address'] not in intersection_list:
                    is_reload = True
                    args = public.dict_obj()
                    args.id = i4['sid']
                    args.domain = i4['domain']
                    #取A记录中不在交集中的IP
                    for i7 in a_ip:
                        if i7 not in intersection_list:
                            args.address = i7
                            a_ip.remove(i7)
                            break
                    if args.domain.split('|')[1] != args.address:
                        args.domain = args.domain.split(
                            '|')[0] + '|' + args.address
                    args.types = i4['types']
                    args.brief = i4['brief']
                    args.sid = i4['id']
                    #修改端口规则
                    # {"id":7,"sid":0,"protocol":"tcp","ports":"39000-40000","choose":"all","address":"","domain":"","types":"accept","brief":"测试","source":""}
                    if i4['port']:
                        args.protocol = i4['protocol']
                        args.ports = i4['port']
                        args.choose = 'point'
                        args.source = args.address
                        firewallobj.modify_rules(args)
                    else:
                        #修改IP规则
                        #{"id":34,"sid":0,"address":"192.168.66.32","types":"accept","brief":"测试","choose":"address"}
                        firewallobj.modify_ip_rules(args)
                    #更新域名解析IP
                    if i4['address'] and i4['address'] != args.address:
                        public.M('firewall_domain').where(
                            "id=?", (i4['id'], )).save('address',
                                                       (args.address, ))
            #当交集不为空且交集不等于原IP时，说明域名部分解析IP发生变化
            elif intersection_list and intersection_list != old_a_ip_dict[i3]:
                for i5 in domain_name_dict[i3]:
                    if i5['address'] not in intersection_list:
                        is_reload = True
                        args = public.dict_obj()
                        args.id = i5['sid']
                        args.domain = i5['domain']
                        if args.domain.split('|')[1] != args.address:
                            args.domain = args.domain.split(
                                '|')[0] + '|' + args.address
                        #取A记录中不在交集中的IP
                        for i6 in a_ip:
                            if i6 not in intersection_list:
                                args.address = i6
                                a_ip.remove(i6)
                                break
                        # args.address = a_ip[0]
                        args.types = i5['types']
                        args.brief = i5['brief']
                        args.sid = i5['id']
                        #修改端口规则
                        # {"id":7,"sid":0,"protocol":"tcp","ports":"39000-40000","choose":"all","address":"","domain":"","types":"accept","brief":"测试","source":""}
                        if i5['port']:
                            args.protocol = i5['protocol']
                            args.ports = i5['port']
                            args.choose = 'point'
                            args.source = args.address
                            firewallobj.modify_rules(args)
                        else:
                            #修改IP规则
                            #{"id":34,"sid":0,"address":"192.168.66.32","types":"accept","brief":"测试","choose":"address"}
                            firewallobj.modify_ip_rules(args)
                        #更新域名解析IP
                        if i5['address'] and i5['address'] != args.address:
                            public.M('firewall_domain').where(
                                "id=?",
                                (i4['id'], )).save('address', (args.address, ))

    if is_reload: firewallobj.FirewallReload()


cron_shell()
