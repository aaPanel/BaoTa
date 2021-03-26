# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: wzj <wzj@bt.cn>
# +-------------------------------------------------------------------
import sys
import os
import json
import pwd
import socket
import paramiko
from io import StringIO

os.chdir('/www/server/panel')
sys.path.insert(0, 'class/')
import public


class ssh_client:
    server_path = 'class/colony/ssh_servers/'
    _address = None
    _port = None
    _ssh_user = None
    _password = None
    _pkey = None
    _term = None
    _sftp = None

    def __init__(self, address, port, ssh_user, password=None, pkey=None):
        self._address = address
        self._port = int(port)
        self._ssh_user = ssh_user
        self._password = password
        self._pkey = pkey

    # 连接SSH
    def connect_ssh(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 262144)
        sock.connect((self._address, self._port))
        transport = paramiko.Transport(sock)
        transport.start_client()
        # 如果有pkey使用RSA私钥登录
        if self._pkey:
            # 将RSA私钥转换为io对象，然后生成rsa_key对象
            p_file = StringIO(self._pkey.strip())
            pkey = paramiko.RSAKey.from_private_key(p_file)
            transport.auth_publickey(username=self._ssh_user, key=pkey)
        else:
            transport.auth_password(username=self._ssh_user, password=self._password)
        self._term = paramiko.SSHClient()
        self._term._transport = transport

    # 连接sftp
    def connect_sftp(self):
        if not self._term:
            self.connect_ssh()
        if not self._sftp:
            self._sftp = self._term.open_sftp()

    # 创建目录
    def mkdir(self, path):
        try:
            self._sftp.mkdir(path)
        except Exception as ex:
            if str(ex).find('No such file') != -1:
                self.exec_shell("mkdir -p {}".format(path))
        return True

    # 设置文件权限
    def chmod(self, path, mode):
        self._sftp.chmod(path, int(str(mode), 8))
        return True

    # 设置所有者
    def chown(self, path, user=None, uid=None, gid=None):
        if user:
            uid, gid = self.get_uid(user)
        self._sftp.chown(path, uid, gid)
        return True

    # 上传文件
    def upload_file(self, sfile, dfile, is_dir=False):
        self.connect_sftp()
        if not is_dir and not os.path.isdir(sfile):
            self.mkdir(os.path.dirname(dfile))
            return self._sftp.put(sfile, dfile)

        file_list = self.get_local_files(sfile)
        if not file_list: return False
        self.mkdir(dfile)
        # 上传文件
        for f in file_list['FILES']:
            f_info = f.split(';')
            s_file = os.path.join(sfile, f_info[0])
            d_file = os.path.join(dfile, f_info[0])
            print("正在上传文件:{}".format(d_file))
            self._sftp.put(s_file, d_file)
            self.chmod(d_file, f_info[3])
            self.chown(d_file, f_info[4])

        # 递归上传目录
        for d in file_list['DIR']:
            d_info = d.split(';')
            s_file = os.path.join(sfile, d_info[0])
            d_file = os.path.join(dfile, d_info[0])
            self.mkdir(d_file)
            self.chmod(d_file, d_info[3])
            self.chown(d_file, d_info[4])
            self.upload_file(s_file, d_file, True)
        return True

    # 获本地取文件列表
    def get_local_files(self, path):
        result = {"FILES": [], 'DIR': [], 'PATH': path}
        for f in os.listdir(path):
            if f in ['lost+found']: continue
            filename = os.path.join(path, f)
            f_stat = os.stat(filename)
            mode = oct(f_stat.st_mode)
            user = pwd.getpwuid(f_stat.st_uid).pw_name
            f_tmp = r"{};{};{};{};{};{}".format(f, f_stat.st_size, int(f_stat.st_mtime), mode[-3:], user, mode)
            if mode[:-3] in ['0040', '0o40', '040']:
                result['DIR'].append(f_tmp)
            else:
                result['FILES'].append(f_tmp)
        return result

    # 获取用户列表
    def get_ulist(self):
        user_info_file = self.server_path + '{}/users.json'.format(self._address)
        u_list = {}
        if not os.path.exists(user_info_file):
            self.connect_sftp()
            p_file = self.server_path + '{}/passwd'.format(self._address)
            self.download_file('/etc/passwd', p_file)
            u_data = public.readFile(p_file)
            if u_data:
                for i in u_data.split("\n"):
                    u_tmp = i.split(':')
                    if len(u_tmp) > 3:
                        u_list[u_tmp[2]] = u_tmp
                if u_list:
                    public.writeFile(user_info_file, json.dumps(u_list))
        if not u_list:
            u_list = json.loads(public.readFile(user_info_file))
        return u_list

    # 取用户名
    def get_user(self, uid):
        uid = str(uid)
        u_list = self.get_ulist()
        if uid not in u_list.keys(): return uid
        return u_list[uid][0]

    # 取uid,gid
    def get_uid(self, user):
        u_list = self.get_ulist()
        for i in u_list.keys():
            if u_list[i][0] == user:
                return int(u_list[i][2]), int(u_list[i][3])
        return 0, 0

    # 取文件列表
    def get_files(self, path):
        result = {"FILES": [], 'DIR': [], 'PATH': path}
        self.connect_sftp()
        tmp_files = self._sftp.listdir_attr(path)

        for f in tmp_files:
            if f.filename in ['lost+found']: continue
            mode = oct(f.st_mode)
            f_tmp = r"{};{};{};{};{};{}".format(f.filename, f.st_size, int(f.st_mtime), mode[-3:], self.get_user(f.st_uid), mode)
            if mode[:-3] in ['0040', '0o40', '040']:
                result['DIR'].append(f_tmp)
            else:
                result['FILES'].append(f_tmp)
        return result

    # 删除文件
    def remove_file(self, filename):
        if not filename: return False
        if filename in ['/', './', '/*']: return False
        if filename.find('*') != -1: return False
        try:
            self._sftp.remove(filename)
        except:
            try:
                self._sftp.rmdir(filename)
            except:
                self.exec_shell("rm -rf " + filename)
        return True

    # 下载文件
    def download_file(self, filename, save_file, is_dir=False):
        self.connect_sftp()

        # 如果是文件
        if not is_dir:
            s_path = os.path.dirname(save_file)
            if not os.path.exists(s_path):
                os.makedirs(s_path)
            return self._sftp.get(filename, save_file)

        if not os.path.exists(save_file):
            os.makedirs(save_file)
        # 获取文件列表
        file_list = self.get_files(filename)
        if not file_list: return False
        # 下载文件
        for f in file_list['FILES']:
            f_info = f.split(';')
            s_file = os.path.join(filename, f_info[0])
            d_file = os.path.join(save_file, f_info[0])
            print("正在下载文件:{}".format(d_file))
            self._sftp.get(s_file, d_file)
            public.set_mode(d_file, f_info[3])
            public.set_own(d_file, f_info[4])

        # 递归下载目录
        for d in file_list['DIR']:
            d_info = d.split(';')
            s_file = os.path.join(filename, d_info[0])
            d_file = os.path.join(save_file, d_info[0])
            if not os.path.exists(d_file):
                os.makedirs(d_file)
            public.set_mode(d_file, d_info[3])
            public.set_own(d_file, d_info[4])
            self.download_file(s_file, d_file, True)

        return True

    # 文件重命名
    def rename(self, sfile, dfile):
        try:
            self._sftp.rename(sfile, dfile)
        except:
            return False
        return True

    # 执行命令
    def exec_shell(self, shell_str, get_pty=False, bufsize=-1, callback=None):
        stdin, stdout, stderr = self._term.exec_command(
            shell_str, 
            get_pty=get_pty, 
            bufsize=bufsize)
        
        if callback:
            stdout_iter = iter(stdout.readline, '')
            for out in stdout_iter:
                if out: callback(out.strip())
        return stdout.read().decode(), stderr.read().decode()

    # 关闭
    def __del__(self):
        if self._sftp:
            self._sftp.close()
        if self._term:
            self._term.close()


if __name__ == '__main__':
    p = ssh_client(address='192.168.1.180', port=22, ssh_user='root', password='www.bt.cn')
    p.connect_ssh()
    print(p.exec_shell('df -h')[0])
    # print(p.get_files('/www'))
    # print(p.get_ulist())
    # print(p.get_user(0))
    # print(p.download_file('/www/wwwroot/w4.hao.com', '/www/test/w4', True))
    # print(p.get_local_files('/www'))
    # print(p.upload_file('/www/wwwroot/w4.hao.com', '/www/www11212/213132/w4_upload', True))
