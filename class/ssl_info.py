import os,sys,re,time,subprocess

panelPath = '/www/server/panel/'
os.chdir(panelPath)

sys.path.insert(0, panelPath + "class/")
import public
from datetime import date, datetime

is_openssl = True
try:
    import OpenSSL
except:
    is_openssl = False

class ssl_info:

    def __init__(self) -> None:
        pass


    def create_key(self,bits=2048):
        """
        @name 创建RSA密钥
        @param bits 密钥长度
        """
        if is_openssl:

            key = OpenSSL.crypto.PKey()
            key.generate_key(OpenSSL.crypto.TYPE_RSA, bits)
            private_key = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, key)
            return private_key
        else:
            tmp_pk_file = "/tmp/private_key_{}.pem".format(int(time.time()))
            cmd = ["openssl", "genpkey", "-algorithm", "RSA", "-out", tmp_pk_file, "-pkeyopt", f"rsa_keygen_bits:{bits}"]
            subprocess.run(cmd, check=True)
            with open(tmp_pk_file, "r") as f:
                private_key = f.read()
            try:
                os.remove("private_key.pem")
            except:
                pass
            return private_key

    def load_ssl_info_by_data(self, pem_data: str):
        if not isinstance(pem_data, (str, bytes)):
            return None

        if is_openssl:
            return self.__get_cert_info(pem_data)
        else:
            result = {}
            pem_file = "/tmp/fullchain_{}.pem".format(int(time.time()))
            public.writeFile(pem_file, pem_data)
            res = public.ExecShell("openssl x509 -in {} -noout -text".format(pem_file))[0]
            issuer_match = re.search(r"Issuer: (.*)", res)
            if issuer_match:
                data = {}
                issuer = issuer_match.group(1)
                for key,val in re.findall(r"(\w+)\s*=([^,]+)", issuer):
                    data[key] = val.strip()

                result["issuer"] = data['CN']
                if "CN" in data:
                    s = data['CN'].encode().decode('unicode_escape')
                    result["issuer"] = bytes(s, 'latin1').decode('utf-8')
                result["issuer_O"] = data['O']
                if "O" in data:
                    s = data['O'].encode().decode('unicode_escape')
                    result["issuer_O"] = bytes(s, 'latin1').decode('utf-8')

            validity_match = re.search(r"Not After\s*:\s*(.*)", res)
            if validity_match:
                not_after = validity_match.group(1)
                dt_after = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
                result['notAfter'] = dt_after.strftime("%Y-%m-%d %H:%M:%S")
                result['endtime'] = (dt_after - datetime.now()).days
            else:
                result['endtime'] = 0

            validity_match = re.search(r"Not Before\s*:\s*(.*)", res)
            if validity_match:
                not_befoer = validity_match.group(1)
                dt_befoer = datetime.strptime(not_befoer, "%b %d %H:%M:%S %Y %Z")
                result['notBefore'] = dt_befoer.strftime("%Y-%m-%d %H:%M:%S")

            subject_match = re.search(r"Subject: (.*)", res)
            if subject_match:
                subject = subject_match.group(1)
                for key,val in re.findall(r"(\w+)\s*=([^,]+)", subject):
                    if key == 'CN':
                        s = val.encode().decode('unicode_escape')
                        result["subject"] = bytes(s, 'latin1').decode('utf-8').strip()
            # 取可选名称
            result['dns'] = []
            dns_match = re.findall(r"DNS:([^\s,]+)", res)
            for dns in dns_match:
                result['dns'].append(dns)
            if os.path.exists(pem_file):
                os.remove(pem_file)
            return result

    def load_ssl_info(self,pem_file):
        """
        @name 获取证书详情
        """
        if not os.path.exists(pem_file):
            return None

        pem_data = public.readFile(pem_file)
        if not pem_data:
            return None
        return self.load_ssl_info_by_data(pem_data)

    def __get_cert_info(self,pem_data):
        """
        @name 通过python的openssl模块获取证书信息
        @param pem_data 证书内容
        """
        result = {}
        try:
            x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, pem_data)
        except:   # 证书格式可能是错的，就没有办法读取证书内容
            return None

        issuer = x509.get_issuer()
        result['issuer'] = ''
        if hasattr(issuer, 'CN'):
            result['issuer'] = issuer.CN
        if not result['issuer']:
            is_key = [b'0', '0']
            issue_comp = issuer.get_components()
            if len(issue_comp) == 1:
                is_key = [b'CN', 'CN']
            for iss in issue_comp:
                if iss[0] in is_key:
                    result['issuer'] = iss[1].decode()
                    break
        if hasattr(issuer, 'O'):
            result['issuer_O'] = issuer.O
        # 取到期时间
        result['notAfter'] = self.strf_date(
            bytes.decode(x509.get_notAfter())[:-1])
        # 取申请时间
        result['notBefore'] = self.strf_date(
            bytes.decode(x509.get_notBefore())[:-1])
        # 取可选名称
        result['dns'] = []
        for i in range(x509.get_extension_count()):
            s_name = x509.get_extension(i)
            if s_name.get_short_name() in [b'subjectAltName', 'subjectAltName']:
                s_dns = str(s_name).split(',')
                for d in s_dns:
                    result['dns'].append(d.split(':')[1])
        subject = x509.get_subject().get_components()
        # 取主要认证名称
        if len(subject) == 1:
            result['subject'] = subject[0][1].decode()
        else:
            if not result['dns']:
                for sub in subject:
                    if sub[0] == b'CN':
                        result['subject'] = sub[1].decode()
                        break
                if 'subject' in result:
                    result['dns'].append(result['subject'])
            else:
                result['subject'] = result['dns'][0]
        result['endtime'] = int(int(time.mktime(time.strptime(result['notAfter'], "%Y-%m-%d")) - time.time()) / 86400)
        return result

       # 转换时间
    def strf_date(self, sdate):
        return time.strftime('%Y-%m-%d', time.strptime(sdate, '%Y%m%d%H%M%S'))

    #转换时间
    def strfToTime(self,sdate):
        import time
        return time.strftime('%Y-%m-%d',time.strptime(sdate,'%b %d %H:%M:%S %Y %Z'))


    def dump_pkcs12_new(self, key_pem=None, cert_pem=None, ca_pem=None, friendly_name=""):
        try:
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import serialization
            from cryptography.x509 import load_pem_x509_certificate
            private_key = self.analysis_private_key(key_pem)
            cert = self.analysis_certificate(cert_pem)
            if not private_key or not cert:
                return None
            # 加载CA证书
            cas = None
            if ca_pem:
                cas = [load_pem_x509_certificate(ca_pem.encode(), default_backend())]
            # 将证书和私钥组合成PKCS12格式的文件
            from cryptography.hazmat.primitives.serialization.pkcs12 import serialize_key_and_certificates
            p12 = serialize_key_and_certificates(
                name=friendly_name.encode() if friendly_name else None,
                key=private_key,
                cert=cert,
                encryption_algorithm=serialization.NoEncryption(),
                cas=cas
            )
            return p12
        except:
            return None

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

    def analysis_certificate(self, cert_pem):
        """
        解析证书
        :param cert_pem: 证书内容
        :return: 有效返回True，无效返回False
        """
        try:
            from cryptography.hazmat.backends import default_backend
            from cryptography.x509 import load_pem_x509_certificate
            cert = load_pem_x509_certificate(cert_pem.encode(), default_backend())
            return cert
        except Exception as e:
            public.print_log(public.get_error_info())
            return None

    def verify_certificate_and_key_match(self, key_pem, cert_pem, password=None):
        """
        验证证书和私钥是否匹配(通过签名验证)
        :param key_pem: 私钥内容
        :param cert_pem: 证书内容
        :param password: 私钥密码
        :return: 验证成功返回True，失败返回False
        """
        try:
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import padding, ec
            message = b"test message"
            private_key = self.analysis_private_key(key_pem, password)
            cert = self.analysis_certificate(cert_pem)
            if not private_key:
                return False, "密钥错误，请检查是否为正确的PEM格式私钥"
            if not cert:
                return False, "证书错误，请检查是否为正确的PEM格式证书"

            # 使用私钥对消息进行签名
            if isinstance(private_key, ec.EllipticCurvePrivateKey):
                # ECC 私钥使用 ECDSA 签名（2个参数）
                signature = private_key.sign(
                    message,
                    ec.ECDSA(hashes.SHA256())
                )
            else:
                # RSA 私钥使用 PKCS1v15 签名（3个参数）
                signature = private_key.sign(
                    message,
                    padding.PKCS1v15(),
                    hashes.SHA256()
                )

            # 使用证书中的公钥验证签名
            public_key = cert.public_key()

            try:
                if isinstance(public_key, ec.EllipticCurvePublicKey):
                    public_key.verify(
                        signature,
                        message,
                        ec.ECDSA(hashes.SHA256())
                    )
                else:
                    public_key.verify(
                        signature,
                        message,
                        padding.PKCS1v15(),
                        hashes.SHA256()
                    )
                return True, "验证成功"
            except Exception as e:
                return False, "密钥和证书不匹配。"
        except Exception as e:
            public.print_log(public.get_error_info())
            return True, str(e)

    # TODO 待完善,先不检测
    def verify_certificate_chain(self, cert_pem):
        """
        验证证书链是否完整
        :param cert_pem: 证书链内容
        :return: 验证成功返回True，失败返回False
        """
        return True, ""
        try:
            from cryptography.hazmat.primitives.asymmetric import padding, ec
            cert_chain = [(i+"-----END CERTIFICATE-----").strip() for i in cert_pem.strip().split("-----END CERTIFICATE-----") if i]

            for i in range(len(cert_chain) - 1):
                cert = self.analysis_certificate(cert_chain[i])

                issuer_cert = self.analysis_certificate(cert_chain[i + 1])

                # 验证当前证书的签名是否由上一级签发
                try:
                    issuer_public_key = issuer_cert.public_key()
                    # 检查 issuer_public_key 是否为 ECC 公钥或 RSA 公钥
                    if isinstance(issuer_public_key, ec.EllipticCurvePublicKey):
                        # 使用 ECDSA 验证 ECC 证书签名
                        issuer_public_key.verify(
                            cert.signature,
                            cert.tbs_certificate_bytes,
                            ec.ECDSA(cert.signature_hash_algorithm),
                        )
                    else:
                        # 使用 PKCS1v15 验证 RSA 证书签名
                        issuer_public_key.verify(
                            cert.signature,
                            cert.tbs_certificate_bytes,
                            padding.PKCS1v15(),
                            cert.signature_hash_algorithm,
                        )
                except Exception as e:
                    return False, "证书链验证失败，请检查证书链是否完整。"
            return True, "证书链验证成功。"
        except Exception as e:
            public.print_log(public.get_error_info())
            return True, str(e)

#class ssl:








