#自签证书脚本 hezhihong
import sys,os
os.chdir('/www/server/panel/')
sys.path.insert(0,"class/")
sys.path.insert(0,"class_v2/")
import public,json
class CreateSSLMain:
    cert_file="/www/server/vhost_virtual/data/cert/vhost.crt"
    key_file="/www/server/vhost_virtual/data/cert/vhost.key"
    def get_ipaddress(self):
        '''
            @name 获取本机IP地址
            @author hwliang<2020-11-24>
            @return list
        '''
        ipa_tmp = public.ExecShell("ip a |grep inet|grep -v inet6|grep -v 127.0.0.1|awk '{print $2}'|sed 's#/[0-9]*##g'")[0].strip()
        iplist = ipa_tmp.split('\n')
        return iplist

    def get_host_all(self):
        local_ip = ['127.0.0.1','::1','localhost']
        ip_list = []
        bind_ip = self.get_ipaddress()

        for ip in bind_ip:
            ip = ip.strip()
            if ip in local_ip: continue
            if ip in ip_list: continue
            ip_list.append(ip)
        net_ip = public.httpGet("https://ifconfig.me/ip")

        if net_ip:
            net_ip = net_ip.strip()
            if not net_ip in ip_list:
                ip_list.append(net_ip)
        if len(ip_list) > 1:
            ip_list = [ip_list[-1],ip_list[0]]
        return ip_list

    #自签证书
    def CreateSSL(self):
        if os.path.exists(self.cert_file) and os.path.exists(self.key_file): return True
        import base64
        userInfo = public.get_user_info()

        if not userInfo:
            userInfo['uid'] = 0
            userInfo['access_key'] = 'B' * 32

        if 'access_key' not in userInfo or not userInfo['access_key']:
            userInfo['access_key'] = 'B' * 32

        domains = self.get_host_all()
        pdata = {
            "action":"get_domain_cert",
            "company":"aapanel.com",
            "domain":','.join(domains),
            "uid":userInfo['uid'],
            "access_key":userInfo['access_key'],
            "panel":1
        }
        cert_api = 'https://api.aapanel.com/aapanel_cert'
        result = json.loads(public.httpPost(cert_api,{'data': json.dumps(pdata)}))
        if 'status' in result:
            if result['status']:
                public.writeFile(self.cert_file,result['cert'])
                public.writeFile(self.key_file,result['key'])
                public.writeFile('/www/server/vhost_virtual/data/cert/baota_root.pfx',base64.b64decode(result['pfx']),'wb+')
                public.writeFile('/www/server/vhost_virtual/data/cert/root_password.pl',result['password'])
                print('1')
                return True
        print('0')
        return False


if __name__ == '__main__':
    ssl = CreateSSLMain()
    ssl.CreateSSL()
