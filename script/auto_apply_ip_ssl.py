import base64
import binascii
import hashlib
import json
import os
import fcntl
import re
import shutil
import socket
import subprocess
import sys
import time
import datetime
from pathlib import Path

import requests

APACHE_CONF_DIRS = [
    "/www/server/panel/vhost/apache"
]

def is_ipv4(ip):
    '''
        @name 是否是IPV4地址
        @author hwliang
        @param ip<string> IP地址
        @return True/False
    '''
    # 验证基本格式
    if not re.match(r"^\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}$", ip):
        return False

    # 验证每个段是否在合理范围
    try:
        socket.inet_pton(socket.AF_INET, ip)
    except AttributeError:
        try:
            socket.inet_aton(ip)
        except socket.error:
            return False
    except socket.error:
        return False
    return True


def is_ipv6(ip):
    '''
        @name 是否为IPv6地址
        @author hwliang
        @param ip<string> 地址
        @return True/False
    '''
    # 验证基本格式
    if not re.match(r"^[\w:]+$", ip):
        return False

    # 验证IPv6地址
    try:
        socket.inet_pton(socket.AF_INET6, ip)
    except socket.error:
        return False
    return True


def check_ip(ip):
    return is_ipv4(ip) or is_ipv6(ip)

def find_apache_conf_files(keyword):
    """查找 Apache 主配置和 vhost 文件"""
    files = set()
    for base in APACHE_CONF_DIRS:
        base_path = Path(base)
        if not base_path.exists():
            continue
        for f in base_path.rglob("*.conf"):
            with open(f, "r") as file:
                content = file.read()
                # 检查是否包含 ServerName 或 ServerAlias 指令
                if keyword in content:
                    files.add(str(f))
    return list(files)


def insert_location_into_vhost(file_path, keyword, verify_file):
    LOCATION_BLOCK = [
        "    <Location /.well-known/acme-challenge/{}>\n".format(verify_file),
        "        Require all granted\n",
        "        Header set Content-Type \"text/plain\"\n",
        "    </Location>\n",
        "    Alias /.well-known/acme-challenge/{} /tmp/{}\n".format(verify_file, verify_file),
    ]

    path = Path(file_path)
    backup = path.with_suffix(path.suffix + ".bak")
    shutil.copy(path, backup)

    with open(path, "r") as f:
        lines = f.readlines()

    new_lines = []
    in_vhost = False
    hit_vhost = False
    location_exists = False

    for line in lines:
        stripped = line.strip()

        if stripped.lower().startswith("<virtualhost"):
            in_vhost = True
            hit_vhost = False
            location_exists = False

        if in_vhost:
            low = stripped.lower()
            if (low.startswith("servername") or low.startswith("serveralias")) and keyword in stripped:
                hit_vhost = True

            if "<location /.well-known/acme-challenge/>" in low:
                location_exists = True

            if stripped.lower() == "</virtualhost>":
                if hit_vhost and not location_exists:
                    new_lines.extend(LOCATION_BLOCK)
                in_vhost = False

        new_lines.append(line)

    with open(path, "w") as f:
        f.writelines(new_lines)

    return True

def find_nginx_files_by_servername(keyword):
    """通过 nginx -T 找到包含 server_name 的配置文件"""
    result = subprocess.run(
        ["nginx", "-T"],
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        text=True,
        check=True
    )

    files = set()
    current_file = None

    for line in result.stdout.splitlines():
        if line.startswith("# configuration file"):
            current_file = line.split()[-1].rstrip(":")
        if "server_name" in line and keyword in line:
            if current_file:
                files.add(current_file)

    return list(files)

def insert_location_into_server(file_path, keyword, verify_file, verify_content):
    path = Path(file_path)
    backup = path.with_suffix(path.suffix + ".bak")

    shutil.copy(path, backup)

    with open(path, "r") as f:
        lines = f.readlines()

    new_lines = []
    brace_level = 0
    in_server = False
    hit_server = False
    location_exists = False

    LOCATION_BLOCK = [
        "    location = /.well-known/acme-challenge/{} {{\n".format(verify_file),
        "        default_type text/plain;\n",
        "        return 200 \"{}\";\n".format(verify_content),
        "    }\n"
    ]

    for i, line in enumerate(lines):
        stripped = line.strip()

        # server 开始
        if stripped.startswith("server"):
            in_server = True
            hit_server = False
            location_exists = False

        if in_server:
            brace_level += line.count("{")
            brace_level -= line.count("}")

            if "server_name" in line and keyword in line:
                hit_server = True

            if "location /.well-known/acme-challenge/" in line:
                location_exists = True

            # server 结束
            if brace_level == 0:
                if hit_server and not location_exists:
                    new_lines.extend(LOCATION_BLOCK)
                in_server = False

        new_lines.append(line)

    with open(path, "w") as f:
        f.writelines(new_lines)

    return True

class AutoApplyIPSSL:
    # 请求到ACME接口
    def __init__(self):
        self._wait_time = 5
        self._max_check_num = 15
        self._url = 'https://acme-v02.api.letsencrypt.org/directory'
        self._bits = 2048
        self._conf_file_v2 = '/www/server/panel/config/letsencrypt_v2.json'
        self._apis = None
        self._replay_nonce = None
        self._config = self.read_config()


    # 取接口目录
    def get_apis(self):
        if not self._apis:
            # 尝试从配置文件中获取
            api_index = "Production"
            if not 'apis' in self._config:
                self._config['apis'] = {}
            if api_index in self._config['apis']:
                if 'expires' in self._config['apis'][api_index] and 'directory' in self._config['apis'][api_index]:
                    if time.time() < self._config['apis'][api_index]['expires']:
                        self._apis = self._config['apis'][api_index]['directory']
                        return self._apis

            # 尝试从云端获取
            res = requests.get(self._url)
            if not res.status_code in [200, 201]:
                result = res.json()
                if "type" in result:
                    if result['type'] == 'urn:acme:error:serverInternal':
                        raise Exception('服务因维护而关闭或发生内部错误，查看 <a href="https://letsencrypt.status.io/" target="_blank" class="btlink">https://letsencrypt.status.io/</a> 了解更多详细信息。')
                raise Exception(res.content)
            s_body = res.json()
            self._apis = {}
            self._apis['newAccount'] = s_body['newAccount']
            self._apis['newNonce'] = s_body['newNonce']
            self._apis['newOrder'] = s_body['newOrder']
            self._apis['revokeCert'] = s_body['revokeCert']
            self._apis['keyChange'] = s_body['keyChange']

            # 保存到配置文件
            self._config['apis'][api_index] = {}
            self._config['apis'][api_index]['directory'] = self._apis
            self._config['apis'][api_index]['expires'] = time.time() + \
                86400  # 24小时后过期
            self.save_config()
        return self._apis

    def acme_request(self, url, payload):
        headers = {}
        payload = self.stringfy_items(payload)

        if payload == "":
            payload64 = payload
        else:
            payload64 = self.calculate_safe_base64(json.dumps(payload))
        protected = self.get_acme_header(url)
        protected64 = self.calculate_safe_base64(json.dumps(protected))
        signature = self.sign_message(
            message="{0}.{1}".format(protected64, payload64))  # bytes
        signature64 = self.calculate_safe_base64(signature)  # str
        data = json.dumps(
            {"protected": protected64, "payload": payload64,
                "signature": signature64}
        )
        headers.update({"Content-Type": "application/jose+json"})
        response = requests.post(url, data=data.encode("utf8"), headers=headers)
        # 更新随机数
        self.update_replay_nonce(response)
        return response

    # 更新随机数
    def update_replay_nonce(self, res):
        replay_nonce = res.headers.get('Replay-Nonce')
        if replay_nonce:
            self._replay_nonce = replay_nonce

    def stringfy_items(self, payload):
        if isinstance(payload, str):
            return payload

        for k, v in payload.items():
            if isinstance(k, bytes):
                k = k.decode("utf-8")
            if isinstance(v, bytes):
                v = v.decode("utf-8")
            payload[k] = v
        return payload

    # 转为无填充的Base64
    def calculate_safe_base64(self, un_encoded_data):
        if sys.version_info[0] == 3:
            if isinstance(un_encoded_data, str):
                un_encoded_data = un_encoded_data.encode("utf8")
        r = base64.urlsafe_b64encode(un_encoded_data).rstrip(b"=")
        return r.decode("utf8")

    # 获请ACME请求头
    def get_acme_header(self, url):
        header = {"alg": "RS256", "nonce": self.get_nonce(), "url": url}
        if url in [self._apis['newAccount'], 'GET_THUMBPRINT']:
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import serialization
            private_key = serialization.load_pem_private_key(
                self.get_account_key().encode(),
                password=None,
                backend=default_backend(),
            )
            public_key_public_numbers = private_key.public_key().public_numbers()

            exponent = "{0:x}".format(public_key_public_numbers.e)
            exponent = "0{0}".format(exponent) if len(
                exponent) % 2 else exponent
            modulus = "{0:x}".format(public_key_public_numbers.n)
            jwk = {
                "kty": "RSA",
                "e": self.calculate_safe_base64(binascii.unhexlify(exponent)),
                "n": self.calculate_safe_base64(binascii.unhexlify(modulus)),
            }
            header["jwk"] = jwk
        else:
            header["kid"] = self.get_kid()
        return header

    def get_nonce(self, force=False):
        # 如果没有保存上一次的随机数或force=True时则重新获取新的随机数
        if not self._replay_nonce or force:
            response = requests.get(
                self._apis['newNonce'],
            )
            self._replay_nonce = response.headers["Replay-Nonce"]
        return self._replay_nonce

    def analysis_private_key(self, key_pem, password=None):
        """
        解析私钥
        :param key_pem: 私钥内容
        :param password: 私钥密码
        :return: 私钥对象
        """
        try:
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import serialization
            private_key = serialization.load_pem_private_key(
                key_pem.encode(),
                password=password,
                backend=default_backend()
            )
            return private_key
        except:
            return None

    def sign_message(self, message):
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding

        pk = self.analysis_private_key(self.get_account_key())
        return pk.sign(message.encode("utf8"), padding.PKCS1v15(), hashes.SHA256())

    # 获用户取密钥对
    def get_account_key(self):
        if not 'account' in self._config:
            self._config['account'] = {}
        k = "Production"
        if not k in self._config['account']:
            self._config['account'][k] = {}

        if not 'key' in self._config['account'][k]:
            self._config['account'][k]['key'] = self.create_key()
            if type(self._config['account'][k]['key']) == bytes:
                self._config['account'][k]['key'] = self._config['account'][k]['key'].decode()
            self.save_config()
        return self._config['account'][k]['key']

    def create_key(self, key_type='RSA'):
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa, ec, ed25519

        if key_type == 'RSA':
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=self._bits
            )
        elif key_type == 'EC':
            private_key = ec.generate_private_key(ec.SECP256R1())
        elif key_type == 'ED25519':
            private_key = ed25519.Ed25519PrivateKey.generate()
        else:
            raise ValueError(f"Unsupported key type: {key_type}")

        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        return private_key_pem

    def get_kid(self, force=False):
        #如果配置文件中不存在kid或force = True时则重新注册新的acme帐户
        if not 'account' in self._config:
            self._config['account'] = {}
        k = "Production"
        if not k in self._config['account']:
            self._config['account'][k] = {}

        if not 'kid' in self._config['account'][k]:
            self._config['account'][k]['kid'] = self.register()
            self.save_config()
            time.sleep(3)
            self._config = self.read_config()
        return self._config['account'][k]['kid']

    # 读配置文件
    def read_config(self):
        if not os.path.exists(self._conf_file_v2):
            self._config = {'orders': {}, 'account': {}, 'apis': {}, 'email': None}
            self.save_config()
            return self._config
        with open(self._conf_file_v2, 'r') as f:
            fcntl.flock(f, fcntl.LOCK_SH)  # 加锁
            tmp_config = f.read()
            fcntl.flock(f, fcntl.LOCK_UN)  # 解锁
            f.close()
        if not tmp_config:
            return self._config
        try:
            self._config = json.loads(tmp_config)
        except:
            self.save_config()
            return self._config
        return self._config

    # 写配置文件
    def save_config(self):
        fp = open(self._conf_file_v2, 'w+')
        fcntl.flock(fp, fcntl.LOCK_EX)  # 加锁
        fp.write(json.dumps(self._config))
        fcntl.flock(fp, fcntl.LOCK_UN)  # 解锁
        fp.close()
        return True

    # 注册acme帐户
    def register(self, existing=False):
        if not 'email' in self._config:
            self._config['email'] = 'demo@bt.cn'
        if existing:
            payload = {"onlyReturnExisting": True}
        elif self._config['email']:
            payload = {
                "termsOfServiceAgreed": True,
                "contact": ["mailto:{0}".format(self._config['email'])],
            }
        else:
            payload = {"termsOfServiceAgreed": True}

        res = self.acme_request(url=self._apis['newAccount'], payload=payload)

        if res.status_code not in [201, 200, 409]:
            raise Exception("注册ACME帐户失败: {}".format(res.json()))
        kid = res.headers["Location"]
        return kid

    def create_csr(self, ips):
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives import serialization
        import ipaddress


        # 生成私钥
        pk = self.create_key()
        private_key = serialization.load_pem_private_key(pk, password=None)

        # IP证书不需要CN
        csr_builder = x509.CertificateSigningRequestBuilder().subject_name(x509.Name([]))
        # 添加 subjectAltName 扩展
        alt_names = [x509.IPAddress(ipaddress.ip_address(ip)) for ip in ips]


        csr_builder = csr_builder.add_extension(
            x509.SubjectAlternativeName(alt_names),
            critical=False
        )

        # 签署 CSR
        csr = csr_builder.sign(private_key, hashes.SHA256())

        # 返回 CSR (ASN1 格式)
        return csr.public_bytes(serialization.Encoding.DER), pk

    def apply_ip_ssl(self, ips, email, webroot=None, mode=None, path=None):
        print("开始申请Let's Encrypt IP SSL证书...")
        print("获取ACME接口目录...")
        self.get_apis()
        self._config['email'] = email
        print("创建订单...")
        order_data = self.create_order(ips)
        if not order_data:
            raise Exception("创建订单失败！")
        print("订单创建成功")
        print("进行域名验证...")
        try:
            self.get_and_set_authorizations(order_data, webroot, mode, ips)
        except Exception as e:
            raise Exception("域名验证失败！{}".format(e))
        # 完成订单
        print("创建csr...")
        csr, private_key = self.create_csr(ips)
        print("发送csr并完成订单...")
        res = self.acme_request(order_data['finalize'], payload={
            "csr": self.calculate_safe_base64(csr)
        })
        if res.status_code not in [200, 201]:
            raise Exception("完成订单失败！{}".format(res.json()))
        # 获取证书
        print("获取证书...")
        cert_url = res.json().get('certificate')
        if not cert_url:
            raise Exception("获取证书URL失败！")
        cert_res = self.acme_request(cert_url, payload="")
        if cert_res.status_code not in [200, 201]:
            raise Exception("获取证书失败！{}".format(cert_res.json()))
        print("证书获取成功！")
        cert_pem = cert_res.content.decode()
        # 保存证书和私钥
        if not path:
            path = "/www/server/panel/ssl"
        if not os.path.exists(path):
            os.makedirs(path)
        cert_path = os.path.join(path, 'certificate.pem')
        key_path = os.path.join(path, 'privateKey.pem')
        with open(cert_path, 'w') as f:
            f.write(cert_pem)
        with open(key_path, 'w') as f:
            f.write(private_key.decode())
        return cert_path, key_path

    def create_order(self, ips):
        identifiers = []
        for ip in ips:
            identifiers.append({"type": "ip", "value": ip})
        payload = {"identifiers": identifiers, "profile": "shortlived"}
        print("创建订单，域名列表：{}".format(','.join(ips)))
        res = self.acme_request(self._apis['newOrder'], payload)
        if not res.status_code in [201,200]:  # 如果创建失败
            print("创建订单失败，尝试修复错误...")
            e_body = res.json()
            if 'type' in e_body:
                # 如果随机数失效
                if e_body['type'].find('error:badNonce') != -1:
                    print("随机数失效，重新获取随机数后重试...")
                    self.get_nonce(force=True)
                    res = self.acme_request(self._apis['newOrder'], payload)
                # 如果帐户失效
                if e_body['detail'].find('KeyID header contained an invalid account URL') != -1:
                    print("帐户失效，重新注册帐户后重试...")
                    k = "Production"
                    del(self._config['account'][k])
                    self.get_kid()
                    self.get_nonce(force=True)
                    res = self.acme_request(self._apis['newOrder'], payload)
            if not res.status_code in [201,200]:
                print(res.json())
                return {}
        return res.json()

    # UTC时间转时间戳
    def utc_to_time(self, utc_string):
        try:
            utc_string = utc_string.split('.')[0]
            utc_date = datetime.datetime.strptime(
                utc_string, "%Y-%m-%dT%H:%M:%S")
            # 按北京时间返回
            return int(time.mktime(utc_date.timetuple())) + (3600 * 8)
        except:
            return int(time.time() + 86400 * 7)

    def get_keyauthorization(self, token):
        acme_header_jwk_json = json.dumps(
            self.get_acme_header("GET_THUMBPRINT")["jwk"], sort_keys=True, separators=(",", ":")
        )
        acme_thumbprint = self.calculate_safe_base64(
            hashlib.sha256(acme_header_jwk_json.encode("utf8")).digest()
        )
        acme_keyauthorization = "{0}.{1}".format(token, acme_thumbprint)
        base64_of_acme_keyauthorization = self.calculate_safe_base64(
            hashlib.sha256(acme_keyauthorization.encode("utf8")).digest()
        )

        return acme_keyauthorization, base64_of_acme_keyauthorization

    # 获取并设置验证信息
    def get_and_set_authorizations(self, order_data, webroot=None, mode=None, ips=None):
        import os

        if 'authorizations' not in order_data:
            raise Exception("订单数据异常，缺少验证信息！")
        for auth_url in order_data['authorizations']:
            res = self.acme_request(auth_url, payload="")
            if not res.status_code in [200, 201]:
                raise Exception("获取验证信息失败！{}".format(res.json()))
            s_body = res.json()
            if 'status' in s_body:
                if s_body['status'] in ['invalid']:
                    raise Exception("无效订单，此订单当前为验证失败状态!")
                if s_body['status'] in ['valid']:  # 跳过无需验证的域名
                    continue
            for challenge in s_body['challenges']:
                if challenge['type'] == "http-01":
                    break
            if challenge['type'] != "http-01":
                raise Exception("未找到http-01验证方式，无法继续申请证书！")
            # 检查是否需要验证
            check_auth_data = self.check_auth_status(challenge['url'])
            if check_auth_data.json()['status'] == 'invalid':
                raise Exception('域名验证失败，请尝试重新申请!')
            if check_auth_data.json()['status'] == 'valid':
                continue

            acme_keyauthorization, auth_value = self.get_keyauthorization(
                challenge['token'])
            print(challenge)

            if mode:
                if mode == 'standalone':
                    from http.server import HTTPServer, SimpleHTTPRequestHandler
                    import threading
                    import os

                    class ACMERequestHandler(SimpleHTTPRequestHandler):
                        def log_message(self, format, *args):
                            # 屏蔽默认的请求日志输出
                            return

                        def do_GET(self):
                            if self.path == '/.well-known/acme-challenge/{}'.format(challenge['token']):
                                self.send_response(200)
                                self.send_header('Content-type', 'text/plain')
                                self.end_headers()
                                self.wfile.write(acme_keyauthorization.encode())
                            else:
                                self.send_response(404)
                                self.end_headers()

                    server_address = ('', 80)
                    httpd = HTTPServer(server_address, ACMERequestHandler)

                    def start_server():
                        httpd.serve_forever()

                    server_thread = threading.Thread(target=start_server)
                    server_thread.daemon = True
                    server_thread.start()

                    time.sleep(2)  # 等待服务器启动

                    try:
                        # 通知ACME服务器进行验证
                        self.acme_request(challenge['url'], payload={"keyAuthorization": "{0}".format(acme_keyauthorization)})
                        self.check_auth_status(challenge['url'], [
                            'valid', 'invalid'])
                    finally:
                        httpd.shutdown()
                        server_thread.join()
                elif mode == 'nginx':
                    tmp_path = '/www/server/panel/vhost/nginx/tmp_apply_ip_ssl.conf'
                    files = find_nginx_files_by_servername(ips[0])
                    if not files:
                        print("未找到相关Nginx配置文件，尝试创建临时配置文件...")
                        if not os.path.exists('/www/server/panel/vhost/nginx'):
                            raise Exception("未找到Nginx配置文件，且Nginx配置目录不存在！")
                        # 如果没有找到相关配置文件，则创建一个临时配置文件
                        with open(tmp_path, 'w') as f:
                            f.write("""server
{{
    listen 80;
    server_name {0};
    location /.well-known/acme-challenge/{1} {{
        default_type text/plain;
        return 200 "{2}";
    }}
}}
""".format(ips[0], challenge['token'], acme_keyauthorization))
                    try:
                        for file in files:
                            print("修改Nginx配置文件: {}".format(file))
                            insert_location_into_server(file, ips[0], verify_file=challenge['token'], verify_content=acme_keyauthorization)
                        # 重新加载Nginx配置
                        subprocess.run(["nginx", "-t"], check=True)
                        subprocess.run(["nginx", "-s", "reload"], check=True)

                        # 通知ACME服务器进行验证
                        self.acme_request(challenge['url'],
                                          payload={"keyAuthorization": "{0}".format(acme_keyauthorization)})
                        self.check_auth_status(challenge['url'], [
                            'valid', 'invalid'])
                    finally:
                        for file in files:
                            print("恢复Nginx配置文件: {}".format(file))
                            # 恢复备份文件
                            backup_file = file + ".bak"
                            if os.path.exists(backup_file):
                                shutil.move(backup_file, file)
                        if not files:
                            print("删除临时Nginx配置文件...")
                            # 删除临时配置文件
                            os.remove(tmp_path)
                        # 重新加载Nginx配置
                        subprocess.run(["nginx", "-t"], check=True)
                        subprocess.run(["nginx", "-s", "reload"], check=True)

                elif mode == 'apache':
                    tmp_path = '/www/server/panel/vhost/apache/tmp_apply_ip_ssl.conf'
                    files = find_apache_conf_files(ips[0])
                    if not files:
                        print("未找到相关Apache配置文件，尝试创建临时配置文件...")
                        if not os.path.exists('/www/server/panel/vhost/apache'):
                            raise Exception("未找到Apache配置文件，且Apache配置目录不存在！")
                        # 如果没有找到相关配置文件，则创建一个临时配置文件
                        with open(tmp_path, 'w') as f:
                            f.write("""<VirtualHost *:80>
    ServerName {0}
    <Location /.well-known/acme-challenge/{1}>
        Require all granted
        Header set Content-Type "text/plain"
    </Location>
    Alias /.well-known/acme-challenge/{1} /tmp/{1}
</VirtualHost>
""".format(ips[0], challenge['token']))
                    try:
                        for file in files:
                            print("修改Apache配置文件: {}".format(file))
                            insert_location_into_vhost(file, ips[0], verify_file=challenge['token'])
                        # 写入验证文件
                        with open('/tmp/{}'.format(challenge['token']), 'w') as f:
                            f.write(acme_keyauthorization)
                        # 重新加载Apache配置
                        subprocess.run(["/etc/init.d/httpd", "reload"], check=True)

                        # 通知ACME服务器进行验证
                        self.acme_request(challenge['url'],
                                          payload={"keyAuthorization": "{0}".format(acme_keyauthorization)})
                        self.check_auth_status(challenge['url'], [
                            'valid', 'invalid'])
                    finally:
                        for file in files:
                            print("恢复Apache配置文件: {}".format(file))
                            # 恢复备份文件
                            backup_file = file + ".bak"
                            if os.path.exists(backup_file):
                                shutil.move(backup_file, file)
                        if not files:
                            print("删除临时Apache配置文件...")
                            # 删除临时配置文件
                            os.remove(tmp_path)
                        # 重新加载Apache配置
                        subprocess.run(["systemctl", "restart", "httpd"], check=True)
            else:
                # 使用webroot方式验证
                challenge_path = os.path.join(
                    webroot, '.well-known', 'acme-challenge')
                if not os.path.exists(challenge_path):
                    os.makedirs(challenge_path)
                file_path = os.path.join(challenge_path, challenge['token'])
                with open(file_path, 'w') as f:
                    f.write(acme_keyauthorization)

                try:
                    # 通知ACME服务器进行验证
                    self.acme_request(challenge['url'], payload={"keyAuthorization": "{0}".format(acme_keyauthorization)})
                    self.check_auth_status(challenge['url'], [
                        'valid', 'invalid'])
                finally:
                    os.remove(file_path)

    # 检查验证状态
    def check_auth_status(self, url, desired_status=None):
        desired_status = desired_status or ["pending", "valid", "invalid"]
        number_of_checks = 0
        authorization_status = "pending"
        while True:
            print("|-第{}次查询验证结果..".format(number_of_checks + 1))
            if desired_status == ['valid', 'invalid']:
                time.sleep(self._wait_time)
            check_authorization_status_response = self.acme_request(url, "")
            a_auth = check_authorization_status_response.json()
            if not isinstance(a_auth, dict):
                continue
            authorization_status = a_auth["status"]
            number_of_checks += 1
            if authorization_status in desired_status:
                if authorization_status == "invalid":
                    try:
                        if 'error' in a_auth['challenges'][0]:
                            ret_title = a_auth['challenges'][0]['error']['detail']
                        elif 'error' in a_auth['challenges'][1]:
                            ret_title = a_auth['challenges'][1]['error']['detail']
                        elif 'error' in a_auth['challenges'][2]:
                            ret_title = a_auth['challenges'][2]['error']['detail']
                        else:
                            ret_title = str(a_auth)
                    except:
                        ret_title = str(a_auth)
                    raise StopIteration(
                        "{0} >>>> {1}".format(
                            ret_title,
                            json.dumps(a_auth)
                        )
                    )
                break

            if number_of_checks == self._max_check_num:
                raise StopIteration(
                    "错误：已尝试验证{0}次. 最大验证次数为{1}. 验证时间间隔为{2}秒.".format(
                        number_of_checks,
                        self._max_check_num,
                        self._wait_time
                    )
                )
        print("|-验证结果: {}".format(authorization_status))
        return check_authorization_status_response


if __name__ == '__main__':
    import argparse
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='自动申请IP SSL证书脚本')
    parser.add_argument('-ips', type=str, required=True, help='要申请SSL证书的ip地址', dest='ips')
    parser.add_argument('-email', type=str, required=False, help='用于申请SSL证书的邮箱', dest='email')
    parser.add_argument('-w', type=str, help='网站根目录', dest='webroot')
    parser.add_argument('--standalone', help='使用独立模式申请证书', dest='standalone', action='store_true')
    parser.add_argument('--nginx', help='使用nginx模式申请证书', dest='nginx', action='store_true')
    parser.add_argument('--apache', help='使用apache模式申请证书', dest='apache', action='store_true')
    parser.add_argument('-path', type=str, help='证书保存路径', dest='path')
    args = parser.parse_args()

    if not args.standalone and not args.webroot and not args.nginx and not args.apache:
        print("未检测到任何验证模式，将尝试自动选择验证模式！")
        # 自动选择验证模式
        # 判断80端口是否被占用
        use_80 = False
        result = subprocess.run(
            ["lsof", "-i:80"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.stdout:
            result = subprocess.run(
                ["netstat -tuln | grep ':80 '"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True
            )
            if result.stdout:
                use_80 = True
        if use_80:
            print("检测到80端口被占用，尝试使用Nginx或Apache模式进行验证...")
            # 检查是否安装Nginx
            if os.path.exists('/www/server/nginx/sbin/nginx'):
                args.nginx = True
                print("选择Nginx模式进行验证...")
            elif os.path.exists('/www/server/apache/bin/httpd'):
                args.apache = True
                print("选择Apache模式进行验证...")
            else:
                print("[ERROR] 未检测到Nginx或Apache安装，无法使用Nginx或Apache模式进行验证！请释放80端口后重试。")
                exit(1)
        else:
            args.standalone = True
            print("80端口未被占用，选择独立模式进行验证...")

    if not args.email:
        # 使用默认邮箱
        email = "demo@bt.cn"
    else:
        email = args.email

    ips = args.ips.split(',')
    # 先只支持单个IP申请
    if len(ips) > 1 and not args.standalone:
        print("[ERROR] 非独立模式下暂不支持多个IP申请SSL证书！")
        exit(1)
    # 先只支持IPv4
    if not is_ipv4(ips[0]):
        print("[ERROR] 目前仅支持IPv4地址申请SSL证书！")
        exit(1)
    auto_ssl = AutoApplyIPSSL()
    mode = None
    if args.standalone:
        mode = 'standalone'
    elif args.nginx:
        mode = 'nginx'
    elif args.apache:
        mode = 'apache'
    try:
        cert_path, key_path = auto_ssl.apply_ip_ssl(ips, email, webroot=args.webroot, mode=mode, path=args.path)
    except:
        import traceback
        print(f"[ERROR] 证书申请失败！错误信息: {traceback.format_exc()}")
        exit(1)
    exit(0)


