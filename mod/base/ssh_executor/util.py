import io
import paramiko


def test_ssh_config(host, port, username, password, pkey, pkey_passwd, timeout: int = 10) -> str:
    try:
        ssh = paramiko.SSHClient()
        pkey_obj = None
        if pkey:
            pky_io = io.StringIO(pkey)
            key_cls_list = [paramiko.RSAKey, paramiko.ECDSAKey, paramiko.Ed25519Key]
            if hasattr(paramiko, "DSSKey"):
                key_cls_list.append(paramiko.DSSKey)
            for key_cls in key_cls_list:
                pky_io.seek(0)
                try:
                    pkey_obj = key_cls.from_private_key(pky_io, password=(pkey_passwd if pkey_passwd else None))
                except Exception as e:
                    if "base64 decoding error" in str(e):
                        return "私钥数据错误，请检查是完整复制的私钥信息"
                    elif "Private key file is encrypted" in str(e):
                        return "私钥已加密，但未提供私钥的密码，无法验证私钥信息"
                    elif "Invalid key" in str(e):
                        return "私钥解析错误，请检查私钥的密码是否正确"
                    continue
                else:
                    break
            else:
                return "私钥解析错误, 请确认输入的秘钥格式正确"
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # look_for_keys 一定要是False，排除不必要的私钥尝试导致的错误
        ssh.connect(hostname=host, port=port, username=username, password=(password if password else None),
                    pkey=pkey_obj, look_for_keys=False, auth_timeout=timeout)
        ssh.close()
        return ""
    except Exception as e:
        err_str = str(e)
        auth_str = "{}@{}:{}".format(username, host, port)
        if err_str.find('Authentication timeout') != -1:
            return '认证超时，【{}】错误：{}'.format(auth_str, e)
        if err_str.find('Authentication failed') != -1:
            if pkey:
                return '认证失败，请检查私钥是否正确: ' + auth_str
            return '帐号或密码错误:' + auth_str
        if err_str.find('Bad authentication type; allowed types') != -1:
            return '不支持的身份验证类型: {}'.format(err_str)
        if err_str.find('Connection reset by peer') != -1:
            return '目标服务器主动拒绝连接'
        if err_str.find('Error reading SSH protocol banner') != -1:
            return '协议头响应超时，错误：' + err_str
        return "连接失败：" + err_str