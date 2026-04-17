#coding: utf-8
import json
import os,sys,time
from json import loads
os.chdir('/www/server/panel/')
sys.path.insert(0,"class/")
sys.path.insert(0,"/www/server/panel")
import setPanelLets, public
# lets_info = public.readFile("/www/server/panel/ssl/lets.info")
cert_info = public.get_cert_data("/www/server/panel/ssl/certificate.pem")
# if lets_info:
#     lets_info = loads(lets_info)
#     res = setPanelLets.setPanelLets().check_cert_update(lets_info['domain'])
#     if res and res['status'] and res['msg'] == '1':
#         strTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))
#         public.writeFile("/tmp/panelSSL.pl","{} Panel certificate updated successfully\n".format(strTime),"a+")
#         public.writeFile('/www/server/panel/data/reload.pl',"1")
#         exit(0)
if cert_info and cert_info['issuer'] in ["R10", "Let's Encrypt", "R8", "R11", "R5", "R3"] or cert_info.get('issuer_O', "") == "Let's Encrypt":
    # 计算有效总天数
    total_days = (time.mktime(time.strptime(cert_info['notAfter'], "%Y-%m-%d")) - time.mktime(time.strptime(cert_info['notBefore'], "%Y-%m-%d"))) / 86400
    # 剩余天数是否小于总天数的1/3
    if cert_info["endtime"] > total_days / 3:
        print("当前证书还有{}天过期跳过续签".format(cert_info['endtime']))
        exit(1)

    domain = public.ReadFile('/www/server/panel/data/domain.conf')
    if domain:
        domain = domain.strip()
        res = setPanelLets.setPanelLets().check_cert_update(domain)
        if res['status'] and res['msg'] == '1':
            strTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))
            public.writeFile("/tmp/panelSSL.pl", "{} Panel certificate updated successfully\n".format(strTime), "a+")
            public.writeFile('/www/server/panel/data/reload.pl', "1")
            exit(0)
    else:
        # 仅当证书是Let's Encrypt颁发且没有绑定域名时，尝试使用IP申请
        if len(cert_info['dns']) > 1:
            print("当前仅支持单个IP申请")
            exit(1)
        ip = cert_info['dns'][0]
        # 判断证书夹内是否有到期时间大于当前证书且未过期的let's encrypt证书
        import panelSSL
        pssl = panelSSL.panelSSL()
        ssl_list = pssl.get_cert_list(public.to_dict_obj({}))
        today = time.strftime("%Y-%m-%d", time.localtime())
        for ssl in ssl_list:
            info = ssl["info"]
            if info['issuer'] in ["R10", "Let's Encrypt", "R8", "R11", "R5", "R3"] or info.get("issuer_O", "") == "Let's Encrypt":
                if ssl['dns'] == [ip] and ssl['not_after'] > today and ssl['not_after'] > cert_info['notAfter']:
                    print("已存在有效的IP证书，无需重复申请")
                    cert_pem = public.readFile(ssl['path'] + '/fullchain.pem')
                    key_pem = public.readFile(ssl['path'] + '/privkey.pem')
                    if cert_pem and key_pem:
                        print("替换证书")
                        public.writeFile('/www/server/panel/ssl/certificate.pem', cert_pem)
                        public.writeFile('/www/server/panel/ssl/privateKey.pem', key_pem)
                        public.writeFile('/www/server/panel/data/reload.pl', "1")
                        exit(0)
        print("尝试使用IP申请新的证书")
        import subprocess
        with open("/tmp/auto_apply_ip_ssl.log", "w") as stdout:
            # 执行脚本
            result = subprocess.run(
                [
                    "/www/server/panel/pyenv/bin/python3",
                    "-u",
                    "/www/server/panel/script/auto_apply_ip_ssl.py",
                    "-ips", ip,
                    "-path", "/www/server/panel/ssl/",
                ],
                stdout=stdout,
                stderr=stdout,
                text=True
            )
        if result.returncode == 0:
            strTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))
            public.writeFile("/tmp/panelSSL.pl", "{} Panel certificate updated successfully\n".format(strTime), "a+")
            public.writeFile('/www/server/panel/data/reload.pl', "1")
            exit(0)
        else:
            print("证书申请失败，请查看日志：/tmp/auto_apply_ip_ssl.log")
            # 申请失败，替换为默认证书

            def get_ipaddress():
                '''
                    @name 获取本机IP地址
                    @author hwliang<2020-11-24>
                    @return list
                '''
                ipa_tmp = \
                public.ExecShell("ip a |grep inet|grep -v inet6|grep -v 127.0.0.1|awk '{print $2}'|sed 's#/[0-9]*##g'")[
                    0].strip()
                iplist = ipa_tmp.split('\n')
                return iplist

            def get_host_all():
                local_ip = ['127.0.0.1', '::1', 'localhost']
                ip_list = []
                bind_ip = get_ipaddress()

                for ip in bind_ip:
                    ip = ip.strip()
                    if ip in local_ip: continue
                    if ip in ip_list: continue
                    ip_list.append(ip)
                net_ip = public.httpGet("https://api.bt.cn/api/getipaddress")

                if net_ip:
                    net_ip = net_ip.strip()
                    if not net_ip in ip_list:
                        ip_list.append(net_ip)
                if len(ip_list) > 1:
                    ip_list = [ip_list[-1], ip_list[0]]

                print(ip_list)
                return ip_list

            # 自签证书
            def CreateSSL():
                import base64
                userInfo = public.get_user_info()
                if not userInfo:
                    userInfo['uid'] = 0
                    userInfo['access_key'] = 'B' * 32
                domains = get_host_all()
                pdata = {
                    "action": "get_domain_cert",
                    "company": "宝塔面板",
                    "domain": ','.join(domains),
                    "uid": userInfo['uid'],
                    "access_key": userInfo['access_key'],
                    "panel": 1
                }
                cert_api = 'https://api.bt.cn/bt_cert'
                res = public.httpPost(cert_api, {'data': json.dumps(pdata)})


                try:
                    result = json.loads(res)
                    if 'status' in result:
                        if result['status']:
                            public.writeFile('/www/server/panel/ssl/certificate.pem', result['cert'])
                            public.writeFile('/www/server/panel/ssl/privateKey.pem', result['key'])
                            public.writeFile('/www/server/panel/ssl/baota_root.pfx', base64.b64decode(result['pfx']), 'wb+')
                            public.writeFile('/www/server/panel/ssl/root_password.pl', result['password'])
                            public.writeFile('/www/server/panel/data/ssl.pl', 'True')
                            public.ExecShell("/etc/init.d/bt reload")
                            print('1')
                            return True
                except:
                    print('error:{}'.format(res))
                print('0')
                return False

            CreateSSL()
            exit(1)