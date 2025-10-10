import json
import os
import sys
import shutil
import time
# import OpenSSL
import re
from hashlib import md5
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict, Union, Callable

from mod.base import json_response
from .util import webserver, check_server_config, write_file, read_file, GET_CLASS, service_reload

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
import public
import db
from panelAes import AesCryptPy3


SSL_SAVE_PATH = "{}/vhost/ssl_saved".format(public.get_panel_path())


class _SSLDatabase:

    def __init__(self):
        db_path = "{}/data/db".format(public.get_panel_path())
        if not os.path.exists(db_path):
            os.makedirs(db_path, 0o600)
        self.db_file = '{}/data/db/ssl_data.db'.format(public.get_panel_path())
        if not os.path.exists(self.db_file):
            self.init_db()
        if not os.path.exists(SSL_SAVE_PATH):
            os.makedirs(SSL_SAVE_PATH, 0o600)

    def init_db(self):
        tmp_db = db.Sql()
        setattr(tmp_db, "_Sql__DB_FILE", self.db_file)

        create_sql_str = (
            "CREATE TABLE IF NOT EXISTS 'ssl_info' ("
            "'id' INTEGER PRIMARY KEY AUTOINCREMENT, "
            "'hash' TEXT NOT NULL UNIQUE, "
            "'path' TEXT NOT NULL, "
            "'dns' TEXT NOT NULL, "
            "'subject' TEXT NOT NULL, "
            "'info' TEXT NOT NULL DEFAULT '', "
            "'cloud_id' INTEGER NOT NULL DEFAULT -1, "
            "'not_after' TEXT NOT NULL, "
            "'use_for_panel' INTEGER NOT NULL DEFAULT 0, "
            "'use_for_site' TEXT NOT NULL DEFAULT '[]', "
            "'auth_info' TEXT NOT NULL DEFAULT '{}', "
            "'create_time' INTEGER NOT NULL DEFAULT (strftime('%s'))"
            ");"
        )
        res = tmp_db.execute(create_sql_str)
        if isinstance(res, str) and res.startswith("error"):
            public.WriteLog("SSL管理", "建表ssl_info失败")
            return

        index_sql_str = "CREATE INDEX IF NOT EXISTS 'hash_index' ON 'ssl_info' ('hash');"

        res = tmp_db.execute(index_sql_str)
        if isinstance(res, str) and res.startswith("error"):
            public.WriteLog("SSL管理", "为ssl_info建立索引hash_index失败")
            return
        tmp_db.close()

    def connection(self):
        tmp_db = db.Sql()
        setattr(tmp_db, "_Sql__DB_FILE", self.db_file)
        tmp_db.table("ssl_info")
        return tmp_db


ssl_db = _SSLDatabase()


class _LocalSSLInfoTool:

    def __init__(self):
        self._letsencrypt = self.get_letsencrypt_conf()

    @staticmethod
    def get_letsencrypt_conf():
        conf_file = "{}/config/letsencrypt_v2.json".format(public.get_panel_path())
        if not os.path.exists(conf_file):
            conf_file = "{}/config/letsencrypt.json".format(public.get_panel_path())
        if not os.path.exists(conf_file):
            return None
        tmp_config = public.readFile(conf_file)
        try:
            orders = json.loads(tmp_config)["orders"]
        except (json.JSONDecodeError, KeyError):
            return None
        return orders

    def get_auth(self, domains):
        if self._letsencrypt is None:
            return None

        for _, data in self._letsencrypt.items():
            if 'save_path' not in data:
                continue
            for d in data['domains']:
                if d in domains:
                    return {
                        "auth_type": data.get('auth_type'),
                        "auth_to": data.get('auth_to')
                    }


class RealSSLManger:
    _REFRESH_TIP = "{}/data/ssl_cloud_refresh.tip".format(public.get_panel_path())
    _OTHER_DATA_NAME = ("use_for_panel", "use_for_site",)

    def __init__(self, conf_prefix=""):
        self._local_ssl_info_tool = None
        self._vhost_path = "/www/server/panel/vhost"
        self.conf_prefix = conf_prefix
        self._tls_v3 = None
        self._is_nginx_http3 = None

    # 与letsencrypt对接
    @property
    def local_tool(self):
        if self._local_ssl_info_tool is None:
            self._local_ssl_info_tool = _LocalSSLInfoTool()
            return self._local_ssl_info_tool
        return self._local_ssl_info_tool

    # 用于部署
    @classmethod
    def get_cert_for_deploy(cls, ssl_data: dict) -> Union[Dict, str]:
        data = {
            'privkey': public.readFile(ssl_data["path"] + '/privkey.pem'),
            'fullchain': public.readFile(ssl_data["path"] + '/fullchain.pem')
        }
        if not isinstance(data["privkey"], str) or not isinstance(data["fullchain"], str):
            return '证书读取错误!'
        return data

    # 是否刷新
    @classmethod
    def need_refresh(cls):
        now = int(time.time())
        if not os.path.isfile(cls._REFRESH_TIP):
            public.writeFile(cls._REFRESH_TIP, str(now))
            return True
        last_time = int(public.readFile(cls._REFRESH_TIP))
        if last_time + 60 * 60 * 4 < now:
            public.writeFile(cls._REFRESH_TIP, str(now))
            return True
        return False

    # 获取hash指纹
    @staticmethod
    def ssl_hash(cert_filename: str = None, certificate: str = None, ignore_errors: bool = False) -> Optional[str]:
        if cert_filename is not None and os.path.isfile(cert_filename):
            certificate = public.readFile(cert_filename)

        if not isinstance(certificate, str) or not certificate.startswith("-----BEGIN"):
            if ignore_errors:
                return None
            raise ValueError("证书格式错误")

        md5_obj = md5()
        md5_obj.update(certificate.encode("utf-8"))
        return md5_obj.hexdigest()

    @staticmethod
    def strf_date(sdate):
        return time.strftime('%Y-%m-%d', time.strptime(sdate, '%Y%m%d%H%M%S'))

    # 获取证书信息
    @classmethod
    def get_cert_info(cls, cert_filename: str = None, certificate: str = None):
        if cert_filename is not None and os.path.isfile(cert_filename):
            certificate = public.readFile(cert_filename)

        if "/www/server/panel/class" not in sys.path:
            sys.path.insert(0, "/www/server/panel/class")
        import ssl_info
        return ssl_info.ssl_info().load_ssl_info_by_data(certificate)

        # try:
        #     result = {
        #         "issuer": '',
        #         "dns": [],
        #     }
        #     x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, certificate.encode("utf-8"))
        #     # 取产品名称
        #     issuer = x509.get_issuer()
        #     result['issuer'] = ''
        #     if hasattr(issuer, 'CN'):
        #         result['issuer'] = issuer.CN
        #     if not result['issuer']:
        #         is_key = [b'0', '0']
        #         issue_comp = issuer.get_components()
        #         if len(issue_comp) == 1:
        #             is_key = [b'CN', 'CN']
        #         for iss in issue_comp:
        #             if iss[0] in is_key:
        #                 result['issuer'] = iss[1].decode()
        #                 break
        #     if not result['issuer']:
        #         if hasattr(issuer, 'O'):
        #             result['issuer'] = issuer.O
        #     # 取到期时间
        #     result['notAfter'] = cls.strf_date(x509.get_notAfter().decode("utf-8")[:-1])
        #     # 取申请时间
        #     result['notBefore'] = cls.strf_date(x509.get_notBefore().decode("utf-8")[:-1])
        #     # 取可选名称
        #     for i in range(x509.get_extension_count()):
        #         s_name = x509.get_extension(i)
        #         if s_name.get_short_name() in [b'subjectAltName', 'subjectAltName']:
        #             s_dns = str(s_name).split(',')
        #             for d in s_dns:
        #                 result['dns'].append(d.split(':')[1])
        #     subject = x509.get_subject().get_components()
        #     # 取主要认证名称
        #     if len(subject) == 1:
        #         result['subject'] = subject[0][1].decode()
        #     else:
        #         if not result['dns']:
        #             for sub in subject:
        #                 if sub[0] == b'CN':
        #                     result['subject'] = sub[1].decode()
        #                     break
        #             if 'subject' in result:
        #                 result['dns'].append(result['subject'])
        #         else:
        #             result['subject'] = result['dns'][0]
        #     return result
        # except:
        #     return None

    # 通过文件名称检查并保存
    def save_by_file(self, cert_filename, private_key_filename, cloud_id=None, other_data: Optional[Dict] = None):
        if not os.path.isfile(cert_filename) or not os.path.isfile(private_key_filename):
            raise ValueError("不存在的证书")

        certificate = public.readFile(cert_filename)
        private_key = public.readFile(private_key_filename)
        if not isinstance(certificate, str) or not isinstance(private_key, str):
            raise ValueError("证书格式错误")
        return self.save_by_data(certificate, private_key, cloud_id=cloud_id)

    # 通过证书内容检查并保存
    def save_by_data(self, certificate: str,
                     private_key: str,
                     cloud_id: Optional[int] = None,
                     other_data: Optional[Dict] = None) -> Dict:

        if not certificate.startswith("-----BEGIN") or not private_key.startswith("-----BEGIN"):
            raise ValueError("证书格式检查错误")

        if cloud_id is None:
            cloud_id = -1

        hash_data = self.ssl_hash(certificate=certificate)
        db_data = self.get_ssl_info_by_hash(hash_data)
        if db_data is not None:  # 已经保存过的
            # 检查 cloud_id 与 保存的 cloud_id 不同时，更新cloud_id
            if db_data['cloud_id'] != cloud_id and cloud_id != -1:
                ssl_db.connection().where("id = ?", (db_data["id"],)).update({"cloud_id": cloud_id})
                db_data['cloud_id'] = cloud_id
            db_data["dns"] = json.loads(db_data["dns"])
            db_data["info"] = json.loads(db_data["info"])
            db_data["auth_info"] = json.loads(db_data["auth_info"])
            db_data["use_for_site"] = json.loads(db_data["use_for_site"])
            return db_data
        info = self.get_cert_info(certificate=certificate)
        if info is None:
            raise ValueError("证书信息解析错误")

        auth_info = self.local_tool.get_auth(info['dns'])
        if auth_info is None:
            auth_info = {}

        pdata = {
            "hash": hash_data,
            "path": "{}/{}".format(SSL_SAVE_PATH, hash_data),
            "dns": json.dumps(info['dns']),
            "subject": info['subject'],
            "info": json.dumps(info),
            "cloud_id": cloud_id,
            "not_after": info["notAfter"],
            "auth_info": json.dumps(auth_info)
        }

        if other_data:
            for key, other_data in other_data.items():
                if key in self._OTHER_DATA_NAME:
                    pdata[key] = other_data

        res_id = ssl_db.connection().insert(pdata)
        if isinstance(res_id, str) and res_id.startswith("error"):
            raise ValueError("数据库写入错误：" + res_id)

        pdata["id"] = res_id
        if not os.path.exists(pdata["path"]):
            os.makedirs(pdata["path"], 0o600)

        public.writeFile("{}/privkey.pem".format(pdata["path"]), private_key)
        public.writeFile("{}/fullchain.pem".format(pdata["path"]), certificate)
        public.writeFile("{}/info.json".format(pdata["path"]), pdata["info"])

        pdata["info"] = info
        return pdata

    # 通过hash指纹获取ssl信息
    @staticmethod
    def get_ssl_info_by_hash(hash_data: str) -> Optional[dict]:
        data = ssl_db.connection().where("hash = ?", (hash_data,)).find()
        if isinstance(data, str):
            raise ValueError("数据库查询错误：" + data)
        if len(data) == 0:
            return None
        return data

    @staticmethod
    def _get_cbc_key_and_iv(with_uer_info=True):
        uer_info_file = "{}/data/userInfo.json".format(public.get_panel_path())
        try:
            user_info = json.loads(public.readFile(uer_info_file))
            uid = user_info["uid"]
        except (json.JSONDecodeError, KeyError):
            return None, None, None

        md5_obj = md5()
        md5_obj.update(str(uid).encode('utf8'))
        bytes_data = md5_obj.hexdigest()

        key = ''
        iv = ''
        for i in range(len(bytes_data)):
            if i % 2 == 0:
                iv += bytes_data[i]
            else:
                key += bytes_data[i]

        if with_uer_info:
            return key, iv, user_info

        return key, iv, None

    def get_cert_list(self,
                      param: Optional[Tuple[str, List]] = None,
                      force_refresh: bool = False,
                      local_refresh: bool = False) -> List:
        if self.need_refresh() or force_refresh:
            self._refresh_ssl_info_by_cloud()
            self._get_ssl_by_local_data()
        elif local_refresh:
            self._get_ssl_by_local_data()

        return self._get_cert_list(param)

    # 获取证书列表
    @classmethod
    def _get_cert_list(cls, param: Optional[Tuple[str, List]]) -> List:
        db_conn = ssl_db.connection()
        if param is not None and len(param) == 2 and isinstance(param[0], str) and isinstance(param[1], (tuple, list)):
            db_conn.where(param[0], param[1])
        res = db_conn.select()
        if isinstance(res, str):
            raise ValueError("数据库查询错误：" + res)

        for value in res:
            value["dns"] = json.loads(value["dns"])
            value["info"] = json.loads(value["info"])
            value["auth_info"] = json.loads(value["auth_info"])
            value["use_for_site"] = json.loads(value["use_for_site"])
            value['endtime'] = int((datetime.strptime(value['not_after'], "%Y-%m-%d").timestamp()
                                    - datetime.today().timestamp()) / (60 * 60 * 24))

        res.sort(key=lambda x: x["not_after"], reverse=True)

        return res

    # 从云端收集证书
    def _refresh_ssl_info_by_cloud(self):
        key, iv, user_info = self._get_cbc_key_and_iv(with_uer_info=True)
        if key is None or iv is None:
            raise ValueError('面板未登录，无法链接云端!')

        AES = AesCryptPy3(key, "CBC", iv, char_set="utf8")

        # 对接云端
        url = "https://www.bt.cn/api/Cert_cloud_deploy/get_cert_list"
        try:
            res_text = public.httpPost(url, {
                "uid": user_info["uid"],
                "access_key": user_info["access_key"],
                "serverid": user_info["serverid"],
            })
            res_data = json.loads(res_text)
            if res_data["status"] is False:
                raise ValueError("获取云端数据失败")

            res_list = res_data['data']
        except:
            raise ValueError("链接云端失败")

        change_set = set()
        for data in res_list:
            try:
                privateKey = AES.aes_decrypt(data["privateKey"])
                certificate = AES.aes_decrypt(data["certificate"])
                cloud_id = data["id"]
                change_data = self.save_by_data(certificate, privateKey, cloud_id)
                change_set.add(change_data.get("id"))
            except:
                pass

        all_ids = ssl_db.connection().field("id").select()
        for ssl_id in all_ids:
            if ssl_id["id"] not in change_set:
                ssl_db.connection().where("id = ?", (ssl_id["id"],)).update({"cloud_id": -1})

    # 从本地收集证书
    def _get_ssl_by_local_data(self):  # 从本地获取可用证书
        local_paths = ['/www/server/panel/vhost/cert', '/www/server/panel/vhost/ssl']
        for path in local_paths:
            if not os.path.exists(path):
                continue
            for p_name in os.listdir(path):
                pem_file = "{}/{}/fullchain.pem".format(path, p_name)
                key_file = "{}/{}/privkey.pem".format(path, p_name)
                if os.path.isfile(pem_file) and os.path.isfile(key_file):
                    try:
                        self.save_by_file(pem_file, key_file)
                    except:
                        pass

        panel_pem_file = "/www/server/panel/ssl/fullchain.pem"
        panel_key_file = "/www/server/panel/ssl/privkey.pem"
        if os.path.isfile(panel_pem_file) and os.path.isfile(panel_key_file):
            try:
                self.save_by_file(panel_pem_file, panel_key_file, other_data={"use_for_panel": 1})
            except:
                pass

    # 从源储存位置删除
    @classmethod
    def _remove_ssl_from_local(cls, ssh_hash: str):
        local_path = '/www/server/panel/vhost/ssl'
        if not os.path.exists(local_path):
            return

        for p_name in os.listdir(local_path):
            pem_file = "{}/{}/fullchain.pem".format(local_path, p_name)

            if os.path.isfile(pem_file):
                hash_data = cls.ssl_hash(cert_filename=pem_file)
                if hash_data == ssh_hash:
                    shutil.rmtree("{}/{}".format(local_path, p_name))

    # 查询证书
    @staticmethod
    def find_ssl_info(ssl_id=None, ssl_hash=None) -> Optional[dict]:
        tmp_conn = ssl_db.connection()
        if ssl_id is None and ssl_hash is None:
            raise ValueError("没有参数信息")
        if ssl_id is not None:
            tmp_conn.where("id = ?", (ssl_id,))
        else:
            tmp_conn.where("hash = ?", (ssl_hash,))

        target = tmp_conn.find()
        if isinstance(target, str) and target.startswith("error"):
            raise ValueError("数据库查询错误：" + target)

        if not bool(target):
            return None

        target["auth_info"] = json.loads(target["auth_info"])
        target["use_for_site"] = json.loads(target["use_for_site"])
        target["dns"] = json.loads(target["dns"])
        target["info"] = json.loads(target["info"])
        target['endtime'] = int((datetime.strptime(target['not_after'], "%Y-%m-%d").timestamp()
                                 - datetime.today().timestamp()) / (60 * 60 * 24))
        return target

    @classmethod
    def add_use_for_site(cls, site_id, ssl_id=None, ssl_hash=None) -> bool:
        return cls.change_use_for_site(site_id, ssl_id, ssl_hash, is_add=True)

    @classmethod
    def remove_use_for_site(cls, site_id, ssl_id=None, ssl_hash=None):
        return cls.change_use_for_site(site_id, ssl_id, ssl_hash, is_add=False)

    @classmethod
    def change_use_for_site(cls, site_id, ssl_id=None, ssl_hash=None, is_add=True):
        target = cls.find_ssl_info(ssl_id=ssl_id, ssl_hash=ssl_hash)
        if not target:
            return False
        try:
            site_ids = json.loads(target["use_for_site"])
        except:
            site_ids = []

        if site_id in site_ids and is_add is False:
            site_ids.remove(site_id)
            up_res = ssl_db.connection().where("id = ?", (target["id"],)).update({"use_for_site": json.dumps(site_ids)})
            if isinstance(up_res, str) and up_res.startswith("error"):
                raise ValueError("数据库查询错误：" + up_res)

        if site_id not in site_ids and is_add is True:
            site_ids.append(site_id)
            up_res = ssl_db.connection().where("id = ?", (target["id"],)).update({"use_for_site": json.dumps(site_ids)})
            if isinstance(up_res, str) and up_res.startswith("error"):
                raise ValueError("数据库查询错误：" + up_res)

        return True

    def get_all_site_ssl(self):
        all_sites = public.M("sites").select()
        self.clear_use_for_site()
        if isinstance(all_sites, str) and all_sites.startswith("error"):
            raise ValueError(all_sites)
        for site in all_sites:
            prefix = "" if site["project_type"] == "PHP" else site["project_type"].lower() + "_"
            tmp = self._get_site_ssl_info(site["name"], prefix=prefix)
            if tmp is None:
                continue

            hash_data = self.ssl_hash(cert_filename=tmp[0])
            self.add_use_for_site(site["id"], ssl_hash=hash_data)

    @staticmethod
    def clear_use_for_site():
        ssl_db.connection().update({"use_for_site": "[]"})

    @staticmethod
    def _get_site_ssl_info(site_name, prefix='') -> Optional[Tuple[str, str]]:
        path = os.path.join('/www/server/panel/vhost/cert/', site_name)

        pem_file = os.path.join(path, "fullchain.pem")
        key_file = os.path.join(path, "privkey.pem")
        if not os.path.isfile(pem_file) or not os.path.isfile(key_file):
            path = os.path.join('/etc/letsencrypt/live/', site_name)
            pem_file = os.path.join(path, "fullchain.pem")
            key_file = os.path.join(path, "privkey.pem")
            if not os.path.isfile(pem_file) or not os.path.isfile(key_file):
                return None

        webserver = public.get_webserver()
        if webserver == "nginx":
            conf_file = "{}/vhost/nginx/{}{}.conf".format(public.get_panel_path(), prefix, site_name)
        elif webserver == "apache":
            conf_file = "{}/vhost/apache/{}{}.conf".format(public.get_panel_path(), prefix, site_name)
        else:
            conf_file = "{}/vhost/openlitespeed/detail/{}.conf".format(public.get_panel_path(), site_name)

        conf = public.readFile(conf_file)
        if not conf:
            return None

        if public.get_webserver() == 'nginx':
            keyText = 'ssl_certificate'
        elif public.get_webserver() == 'apache':
            keyText = 'SSLCertificateFile'
        else:
            keyText = 'openlitespeed/detail/ssl'

        if conf.find(keyText) == -1:
            return None

        return pem_file, key_file

    # 删除证书
    def remove_cert(self, ssl_id=None, ssl_hash=None, local: bool = False) -> Dict:
        _, _, user_info = self._get_cbc_key_and_iv(with_uer_info=True)
        if user_info is None:
            raise ValueError('面板未登录，无法上传云端!')

        target = self.find_ssl_info(ssl_id=ssl_id, ssl_hash=ssl_hash)
        if not target:
            raise ValueError('没有指定的证书')

        if local:
            shutil.rmtree(target["path"])
            self._remove_ssl_from_local(target["hash"])  # 把ssl下的也删除
            ssl_db.connection().delete(id=target["id"])

        if target["cloud_id"] != -1:
            url = "https://www.bt.cn/api/Cert_cloud_deploy/del_cert"
            try:
                res_text = public.httpPost(url, {
                    "cert_id": target["cloud_id"],
                    "hashVal": target["hash"],
                    "uid": user_info["uid"],
                    "access_key": user_info["access_key"],
                    "serverid": user_info["serverid"],
                })
                res_data = json.loads(res_text)
                if res_data["status"] is False:
                    return res_data
            except:
                if local:
                    raise ValueError("本地以删除成功, 链接云端失败, 无法删除云端数据")
                raise ValueError("链接云端失败, 无法删除云端数据")

            if not local:
                ssl_db.connection().where("id = ?", (target["id"],)).update({"cloud_id": -1})

        return public.returnMsg(True, "删除成功")

    def mutil_remove_cert(self, ssl_id_list: List[int], local: bool = False):
        result = []
        for i in ssl_id_list:
            try:
                ssl_id = int(i)
            except:
                result.append({"status": False, "msg": "id信息解析错误"})
                continue
            res = self.remove_cert(ssl_id=ssl_id, local=local)
            result.append(res)
        return result

    # 下载证书
    def upload_cert(self, ssl_id=None, ssl_hash=None) -> Dict:
        key, iv, user_info = self._get_cbc_key_and_iv()
        if key is None or iv is None:
            raise ValueError(False, '面板未登录，无法上传云端!')

        target = self.find_ssl_info(ssl_id=ssl_id, ssl_hash=ssl_hash)
        if not target:
            raise ValueError("没有指定的证书信息")

        data = {
            'privateKey': public.readFile(target["path"] + '/privkey.pem'),
            'certificate': public.readFile(target["path"] + '/fullchain.pem'),
            "encryptWay": "AES-128-CBC",
            "hashVal": target['hash'],
            "uid": user_info["uid"],
            "access_key": user_info["access_key"],
            "serverid": user_info["serverid"],
        }
        if data["privateKey"] is False or data["certificate"] is False:
            raise ValueError('证书文件读取错误')

        AES = AesCryptPy3(key, "CBC", iv, char_set="utf8")
        data["privateKey"] = AES.aes_encrypt(data["privateKey"])
        data["certificate"] = AES.aes_encrypt(data["certificate"])
        # 对接云端
        url = "https://www.bt.cn/api/Cert_cloud_deploy/cloud_deploy"

        try:
            res_text = public.httpPost(url, data)
            res_data = json.loads(res_text)
            if res_data["status"] is True:
                cloud_id = int(res_data["data"].get("id"))
                ssl_db.connection().where("id = ?", (target["id"],)).update({"cloud_id": cloud_id})

                return res_data
            else:
                return res_data
        except:
            raise ValueError('链接云端失败')

    # ssl_hash 证书储存记录的唯一值
    def set_site_ssl_conf(self, site_name: str, ssl_data: dict, mutil=False) -> Optional[str]:
        privkey = ssl_data["privkey"]
        fullchain = ssl_data["fullchain"]
        path = '/www/server/panel/vhost/cert/' + site_name
        if not os.path.exists(path):
            os.makedirs(path)

        csrpath = path + "/fullchain.pem"
        keypath = path + "/privkey.pem"

        # 清理旧的证书链
        remove_list = [keypath, csrpath, path + "/certOrderId", path + "/README"]
        for i in remove_list:
            if os.path.exists(i):
                os.remove(i)
        public.ExecShell('rm -rf ' + path + '-00*')
        public.ExecShell('rm -rf /etc/letsencrypt/archive/' + site_name)
        public.ExecShell('rm -rf /etc/letsencrypt/archive/' + site_name + '-00*')
        public.ExecShell('rm -f /etc/letsencrypt/renewal/' + site_name + '.conf')
        public.ExecShell('rm -f /etc/letsencrypt/renewal/' + site_name + '-00*.conf')

        public.writeFile(keypath, privkey)
        public.writeFile(csrpath, fullchain)
        error_msg = self._set_ssl_conf_to_nginx(site_name, mutil)
        if error_msg is not None and webserver() == "nginx":
            return error_msg
        error_msg = self._set_ssl_conf_to_apache(site_name, mutil)
        if error_msg is not None and webserver() == "apache":
            return error_msg

    # http3是否可用
    def is_nginx_http3(self):
        """判断nginx是否可以使用http3"""
        if getattr(self, "_is_nginx_http3", None) is None:
            _is_nginx_http3 = public.ExecShell("nginx -V 2>&1| grep 'http_v3_module'")[0] != ''
            setattr(self, "_is_nginx_http3", _is_nginx_http3)
        return self._is_nginx_http3

    # 在防火墙放行443
    @staticmethod
    def open_firewall_443() -> None:
        import firewalls
        get = GET_CLASS()
        get.port = '443'
        get.ps = 'HTTPS'
        firewalls.firewalls().AddAcceptPort(get)

    # 在nginx配置文件中设置ssl信息
    def _set_ssl_conf_to_nginx(self, site_name, mutil=False) -> Optional[str]:
        # Nginx配置
        file = '{}/nginx/{}{}.conf'.format(self._vhost_path, self.conf_prefix, site_name)
        ng_conf = read_file(file)
        if not ng_conf:
            return "配置文件丢失，配置失败"

        http3_header = ""
        if self.is_nginx_http3():
            http3_header = '''\n    add_header Alt-Svc 'quic=":443"; h3=":443"; h3-29=":443"; h3-27=":443";h3-25=":443"; h3-T050=":443"; h3-Q050=":443";h3-Q049=":443";h3-Q048=":443"; h3-Q046=":443"; h3-Q043=":443"';'''

        if ng_conf.find('ssl_certificate') == -1:
            sslStr = """#error_page 404/404.html;
    ssl_certificate    /www/server/panel/vhost/cert/%s/fullchain.pem;
    ssl_certificate_key    /www/server/panel/vhost/cert/%s/privkey.pem;
    ssl_protocols %s;
    ssl_ciphers EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    add_header Strict-Transport-Security "max-age=31536000";%s
    error_page 497  https://$host$request_uri;""" % (
                site_name, site_name, self._get_tls_protocol(is_apache=False), http3_header
            )

            new_ng_conf = ng_conf.replace('#error_page 404/404.html;', sslStr)
            # 添加端口
            from .domain_tool import NginxDomainTool
            new_ng_conf = NginxDomainTool.nginx_add_port_by_config(new_ng_conf, "443", is_http3=self.is_nginx_http3())
            write_file(file, new_ng_conf)
            if webserver() == "nginx" and check_server_config() is not None:
                return "配置失败"
            if webserver() == "nginx" and not mutil:
                service_reload()
                self.open_firewall_443()

    # 在apache配置文件中设置ssl信息
    def _set_ssl_conf_to_apache(self, site_name, mutil=False) -> Optional[str]:
        ap_file = '{}/apache/{}{}.conf'.format(self._vhost_path, self.conf_prefix, site_name)
        ap_conf = read_file(ap_file)
        if not ap_conf:
            return "配置文件丢失，配置失败"

        tmp_template_res = re.search(r"<VirtualHost(.|\n)*?</VirtualHost>", ap_conf)
        if not tmp_template_res:
            return "配置文件丢失，配置失败"
        else:
            tmp_template = tmp_template_res.group()

        rep_template_with_ports = re.compile(r"<VirtualHost +.*:(?P<port>\d+)+\s*>(.|\n)*?</VirtualHost>")
        target_vhost = None
        for tmp in rep_template_with_ports.finditer(ap_conf):
            if tmp.group("port") == "443":
                target_vhost = tmp.group()

        if target_vhost and (target_vhost.find("SSLEngine On") or target_vhost.find("SSLCertificateFile")):
            return
        if not target_vhost:
            rep_ports = re.compile(r"<VirtualHost +.*:(?P<port>\d+)+\s*>")
            target_vhost = rep_ports.sub("<VirtualHost *:443>", tmp_template, 1)

        # 添加SSL配置
        ssl_conf = """    
    #SSL
    SSLEngine On
    SSLCertificateFile /www/server/panel/vhost/cert/%s/fullchain.pem
    SSLCertificateKeyFile /www/server/panel/vhost/cert/%s/privkey.pem
    SSLCipherSuite EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5:ALL:!ADH:!EXPORT56:RC4+RSA:+HIGH:+MEDIUM:+LOW:+SSLv2:+EXP:+eNULL
    SSLProtocol All -SSLv2 -SSLv3 %s
    SSLHonorCipherOrder On
    """ % (site_name, site_name, self._get_tls_protocol(is_apache=True))

        rep_list = [
            (re.compile(r"#DENY FILES"), True),
            (re.compile(r"CustomLog[^\n]*\n"), False),
        ]

        # 使用正则匹配确定插入位置
        def set_by_rep_idx(tmp_rep: re.Pattern, use_start: bool) -> Optional[str]:
            tmp_res = tmp_rep.search(target_vhost)
            if not tmp_res:
                return None
            if use_start:
                new_conf = target_vhost[:tmp_res.start()] + ssl_conf + tmp_res.group() + target_vhost[tmp_res.end():]
            else:
                new_conf = target_vhost[:tmp_res.start()] + tmp_res.group() + ssl_conf + target_vhost[tmp_res.end():]
            return new_conf

        ssl_vhost = None
        for r, s in rep_list:
            ssl_vhost = set_by_rep_idx(r, s)
            if ssl_vhost is not None:
                break

        if ssl_vhost is None:
            return "无法定位SSL配置文件位置，配置失败"

        write_file(ap_file, ap_conf + "\n" + ssl_vhost)
        # 添加端口
        from .domain_tool import ApacheDomainTool
        ApacheDomainTool.apache_add_ports("443")
        web_server = webserver()
        if web_server == "apache" and check_server_config() is not None:
            write_file(ap_file, ap_conf)
            return "配置失败"

        if web_server == "apache" and not mutil:
            service_reload()
            self.open_firewall_443()

    def close_site_ssl_conf(self, site_name) -> Optional[str]:
        error_msg = self._close_ssl_conf_to_nginx(site_name)
        if error_msg is not None and webserver() == "nginx":
            return error_msg
        error_msg = self._close_ssl_conf_to_apache(site_name)
        if error_msg is not None and webserver() == "apache":
            return error_msg
        service_reload()
        return None

    def _close_ssl_conf_to_nginx(self, site_name) -> Optional[str]:
        file = '{}/nginx/{}{}.conf'.format(self._vhost_path, self.conf_prefix, site_name)
        ng_conf = read_file(file)
        if not ng_conf:
            return "配置文件丢失，配置失败"
        rep_list = (
            re.compile(r"\n\s*#HTTP_TO_HTTPS_START(.|\n){1,300}#HTTP_TO_HTTPS_END"),  # 关闭 强制https
            re.compile(r"\s*ssl_(certificate|certificate_key|protocols|"
                       r"ciphers|prefer_server_ciphers|session_cache|session_timeout)[^;]*;"),  # 关闭 强制https
            re.compile(r"\s*add_header\s+(Strict-Transport-Security|Alt-Svc)[^;]*;"),  # 关闭 https 请求头配置
            re.compile(r"\s*error_page\s+497\s+[^;]*;"),
            re.compile(r"\s+listen\s+(\[::]:)?443.*;"),  # 关闭端口监听
        )
        new_conf = ng_conf
        for rep in rep_list:
            new_conf = rep.sub("", new_conf)

        write_file(file, new_conf)

    def _close_ssl_conf_to_apache(self, site_name) -> Optional[str]:
        file = '{}/apache/{}{}.conf'.format(self._vhost_path, self.conf_prefix, site_name)
        ap_conf = read_file(file)
        if not ap_conf:
            return "配置文件丢失，配置失败"
        rep_list = (
            re.compile(r"\n\s*#HTTP_TO_HTTPS_START(.|\n){1,300}#HTTP_TO_HTTPS_END"),
            re.compile(r"\n<VirtualHost\s+\*:443\s*>(.|\n)*</VirtualHost>"),
        )
        new_conf = ap_conf
        for rep in rep_list:
            new_conf = rep.sub("", new_conf)

        write_file(file, new_conf)

    def _get_tls_protocol(self, is_apache=False):
        """获取使用的协议
        @author baozi <202-04-18>
        @param:
        @return
        """
        protocols = {
            "TLSv1": False,
            "TLSv1.1": True,
            "TLSv1.2": True,
            "TLSv1.3": False,
        }
        tls1_3 = self.get_tls13()
        file_path = public.get_panel_path() + "/data/ssl_protocol.json"
        if os.path.exists(file_path):
            data = public.readFile(file_path)
            if data is not False:
                protocols = json.loads(data)
                if protocols["TLSv1.3"] and tls1_3 == "":
                    protocols["TLSv1.3"] = False
                if is_apache is False:
                    return " ".join([p for p, v in protocols.items() if v is True])
                else:
                    return " ".join(["-" + p for p, v in protocols.items() if v is False])
        else:
            if tls1_3 != "":
                protocols["TLSv1.3"] = True
            if is_apache is False:
                return " ".join([p for p, v in protocols.items() if v is True])
            else:
                return " ".join(["-" + p for p, v in protocols.items() if v is False])

    # 获取TLS1.3标记
    def get_tls13(self):
        if self._tls_v3 is not None:
            return self._tls_v3
        nginx_bin = '/www/server/nginx/sbin/nginx'
        nginx_v = public.ExecShell(nginx_bin + ' -V 2>&1')[0]
        nginx_v_re = re.search(r"nginx/(?P<ng_ver>\d\.\d+).+OpenSSL\s+(?P<ssl_ver>\d\.\d+)", nginx_v)
        if nginx_v_re:
            ng_ver = nginx_v_re.group("ng_ver")
            ssl_ver = nginx_v_re.group("ssl_ver")
            if float(ng_ver) >= 1.15 and float(ssl_ver) >= 1.1:
                self._tls_v3 = 'TLSv1.3'
        else:
            can_ng_ver = re.search(r'nginx/1\.(1[5-9]|2\d)', nginx_v)
            openssl_v = public.ExecShell(nginx_bin + ' -V 2>&1|grep OpenSSL')[0].find('OpenSSL 1.1.') != -1
            if can_ng_ver and openssl_v:
                self._tls_v3 = 'TLSv1.3'

        if self._tls_v3 is None:
            self._tls_v3 = ''
        return self._tls_v3

    # HttpToHttps
    def set_http_to_https(self, site_name: str):
        # Nginx配置
        file = '{}/nginx/{}{}.conf'.format(self._vhost_path, self.conf_prefix, site_name)
        conf = read_file(file)
        if conf:
            if conf.find('ssl_certificate') == -1:
                return public.returnMsg(False, '当前未开启SSL')
            to_str = """#error_page 404/404.html;
    #HTTP_TO_HTTPS_START
    if ($server_port !~ 443){
        rewrite ^(/.*)$ https://$host$1 permanent;
    }
    #HTTP_TO_HTTPS_END
"""
            conf = conf.replace('#error_page 404/404.html;', to_str)
            write_file(file, conf)

        file = '{}/apache/{}{}.conf'.format(self._vhost_path, self.conf_prefix, site_name)
        conf = public.readFile(file)
        if conf:
            to_str = '''
    #HTTP_TO_HTTPS_START
    <IfModule mod_rewrite.c>
        RewriteEngine on
        RewriteCond %{SERVER_PORT} !^443$
        RewriteRule (.*) https://%{SERVER_NAME}$1 [L,R=301]
    </IfModule>
    #HTTP_TO_HTTPS_END
    SSLEngine On'''
            conf = re.sub('SSLEngine On', to_str, conf, 1)
            public.writeFile(file, conf)

        service_reload()

    # CloseToHttps
    def close_to_https(self, site_name):
        file = '{}/nginx/{}{}.conf'.format(self._vhost_path, self.conf_prefix, site_name)
        conf = public.readFile(file)
        if conf:
            rep_https = re.compile(r"(#HTTP_TO_HTTPS_START\s*)?if\s+\(\s*\$server_port\s+!~\s+443\s*\)"
                                   r"[^{]*\{[^}]*}\s*(#HTTP_TO_HTTPS_END\s*)?")
            new_conf = rep_https.sub('', conf)
            write_file(file, new_conf)

        file = '{}/apache/{}{}.conf'.format(self._vhost_path, self.conf_prefix, site_name)
        conf = public.readFile(file)
        if conf:
            rep_https = re.compile("\n\s*#HTTP_TO_HTTPS_START(.|\n){1,300}#HTTP_TO_HTTPS_END")
            new_conf = rep_https.sub('', conf)
            write_file(file, new_conf)

        service_reload()

    # 是否有跳转到https
    def is_to_https(self, site_name) -> bool:
        file = '{}/nginx/{}{}.conf'.format(self._vhost_path, self.conf_prefix, site_name)
        conf = public.readFile(file)
        if conf:
            if conf.find('HTTP_TO_HTTPS_START') != -1:
                return True
            if conf.find('$server_port !~ 443') != -1:
                return True
        return False

    def get_site_ssl_info(self, site_name: str) -> Optional[dict]:
        try:
            w_s = webserver()
            if w_s == 'nginx':
                conf_file = '{}/nginx/{}{}.conf'.format(self._vhost_path, self.conf_prefix, site_name)
            elif w_s == "apach":
                conf_file = '{}/apache/{}{}.conf'.format(self._vhost_path, self.conf_prefix, site_name)
            else:
                return None

            if not os.path.exists(conf_file):
                return None

            s_conf = public.readFile(conf_file)
            if not s_conf:
                return None
            if w_s == "apach":
                s_tmp = re.findall(r"SSLCertificateFile\s+(.+\.pem)", s_conf)
                if not s_tmp:
                    return None
                ssl_file = s_tmp[0]
            else:
                s_tmp = re.findall(r"ssl_certificate\s+(.+\.pem);", s_conf)
                if not s_tmp:
                    return None
                ssl_file = s_tmp[0]

            ssl_info = self.get_cert_info(cert_filename=ssl_file)
            if not ssl_info:
                return None
            ssl_info['endtime'] = int(
                int(time.mktime(time.strptime(ssl_info['notAfter'], "%Y-%m-%d")) - time.time()) / 86400)
            return ssl_info
        except:
            return None


class SSLManager:

    def __init__(self, conf_prefix: str = ""):
        self.conf_prefix = conf_prefix

    def set_site_ssl_conf(self, get):
        ssl_id = None
        ssl_hash = None
        try:
            if "ssl_id" in get:
                ssl_id = int(get.ssl_id)
            if "ssl_hash" in get:
                ssl_hash = get.ssl_hash.strip()
            site_name = get.site_name.strip()
        except (ValueError, AttributeError, KeyError):
            return public.ReturnMsg(False, "参数错误")
        ssl_mgr = RealSSLManger(self.conf_prefix)
        try:
            info = ssl_mgr.find_ssl_info(ssl_id=ssl_id, ssl_hash=ssl_hash)
            if not info:
                return json_response(status=False, msg="未查询到证书信息")
            ssl_data = ssl_mgr.get_cert_for_deploy(info)
            if isinstance(ssl_data, str):
                return json_response(status=False, msg=ssl_data)
        except ValueError as e:
            return json_response(status=False, msg=str(e))

        err_msg = ssl_mgr.set_site_ssl_conf(site_name=site_name, ssl_data=ssl_data)
        if err_msg:
            return json_response(status=False, msg=err_msg)
        return json_response(status=True, msg="部署成功")

    def mutil_set_site_ssl_conf(self, get):
        ssl_id = None
        ssl_hash = None
        try:
            if "ssl_id" in get:
                ssl_id = int(get.ssl_id)
            if "ssl_hash" in get:
                ssl_hash = get.ssl_hash.strip()
            site_names = json.loads(get.site_names.strip())
        except (ValueError, AttributeError, KeyError, json.JSONDecodeError):
            return public.ReturnMsg(False, "参数错误")
        ssl_mgr = RealSSLManger(self.conf_prefix)
        try:
            info = ssl_mgr.find_ssl_info(ssl_id=ssl_id, ssl_hash=ssl_hash)
            if not info:
                return json_response(status=False, msg="未查询到证书信息")
            ssl_data = ssl_mgr.get_cert_for_deploy(info)
            if isinstance(ssl_data, str):
                return json_response(status=False, msg=ssl_data)
        except ValueError as e:
            return json_response(status=False, msg=str(e))

        result = {
            "total": len(site_names),
            "success": 0,
            "failed": 0,
            "success_list": [],
            "failed_list": [],
            "failed_msg": []
        }
        for i in site_names:
            err_msg = ssl_mgr.set_site_ssl_conf(site_name=i, ssl_data=ssl_data)
            if err_msg:
                result["failed"] += 1
                result["failed_list"].append(i)
                result["failed_msg"].append(err_msg)
            else:
                result["success"] += 1
                result["success_list"].append(i)

        return json_response(status=True, data=result)

    def close_site_ssl_conf(self, get):
        try:
            site_name = get.site_name.strip()
        except (ValueError, AttributeError, KeyError):
            return public.ReturnMsg(False, "参数错误")

        ssl_mgr = RealSSLManger(self.conf_prefix)
        try:
            err_msg = ssl_mgr.close_site_ssl_conf(site_name)
            if err_msg:
                return json_response(status=False, msg=err_msg)
            return json_response(status=True, msg="关闭成功")
        except Exception as e:
            return json_response(status=False, msg=str(e))

    def upload_cert_to_cloud(self, get):
        ssl_id = None
        ssl_hash = None
        try:
            if "ssl_id" in get:
                ssl_id = int(get.ssl_id)
            if "ssl_hash" in get:
                ssl_hash = get.ssl_hash.strip()
        except (ValueError, AttributeError, KeyError):
            return public.ReturnMsg(False, "参数错误")
        try:
            data = RealSSLManger(self.conf_prefix).upload_cert(ssl_id, ssl_hash)
            return json_response(status=True, data=data)
        except ValueError as e:
            return json_response(status=False, msg=str(e))
        except Exception as e:
            return json_response(status=False, msg="操作错误：" + str(e))

    def remove_cloud_cert(self, get):
        ssl_id = None
        ssl_hash = None
        local = False
        try:
            if "ssl_id" in get:
                ssl_id = int(get.ssl_id)
            if "ssl_hash" in get:
                ssl_hash = get.ssl_hash.strip()

            if "local" in get and get.local.strip() in ("1", 1, True, "true"):
                local = True

        except (ValueError, AttributeError, KeyError):
            return public.ReturnMsg(False, "参数错误")
        try:
            data = RealSSLManger(self.conf_prefix).remove_cert(ssl_id, ssl_hash, local=local)
            return json_response(status=data.get("status", True), msg=data.get("msg", ""), data=data)
        except ValueError as e:
            return json_response(status=False, msg=str(e))
        except Exception as e:
            return json_response(status=False, msg="操作错误：" + str(e))

    def mutil_remove_cloud_cert(self, get):
        local = False
        try:
            ssl_id_list = json.loads(get.ssl_id_list.strip())
            if "local" in get and get.local.strip() in ("1", 1, True, "true"):
                local = True

        except (ValueError, AttributeError, KeyError):
            return public.ReturnMsg(False, "参数错误")
        try:
            data = RealSSLManger(self.conf_prefix).mutil_remove_cert(ssl_id_list, local=local)
            return json_response(status=True, data=data)
        except ValueError as e:
            return json_response(status=False, msg=str(e))
        except Exception as e:
            return json_response(status=False, msg="操作错误：" + str(e))

    # 未使用
    def refresh_cert_list(self, get=None):
        try:
            data = RealSSLManger(self.conf_prefix).get_cert_list(force_refresh=True)
            return json_response(status=True, data=data)
        except ValueError as e:
            return json_response(status=False, msg=str(e))
        except Exception as e:
            return json_response(status=False, msg="操作错误：" + str(e))

    def get_cert_info(self, get):
        ssl_id = None
        ssl_hash = None
        try:
            if "ssl_id" in get:
                ssl_id = int(get.ssl_id)
            if "ssl_hash" in get:
                ssl_hash = get.ssl_hash.strip()
        except (ValueError, AttributeError, KeyError):
            return public.ReturnMsg(False, "参数错误")
        try:
            ssl_mager = RealSSLManger(self.conf_prefix)
            target = ssl_mager.find_ssl_info(ssl_id, ssl_hash)
            if target is None:
                return json_response(status=False, msg="未获取到证书信息")
            data = ssl_mager.get_cert_for_deploy(target)
            if isinstance(data, dict):
                target.update(data)
                return json_response(status=True, data=target)
            else:
                return json_response(status=False, msg=data)
        except ValueError as e:
            return json_response(status=False, msg=str(e))
        except Exception as e:
            return json_response(status=False, msg="操作错误：" + str(e))

    def get_site_ssl_info(self, get):
        try:
            site_name = get.site_name.strip()
        except (ValueError, AttributeError, KeyError):
            return json_response(False, "参数错误")
        ssl_info = RealSSLManger(self.conf_prefix).get_site_ssl_info(site_name)
        if ssl_info is None:
            return json_response(status=False, msg="未获取到证书信息")
        else:
            return json_response(status=True, data=ssl_info)

    def get_cert_list(self, get):
        """
        search_limit 0 -> 所有证书
        search_limit 1 -> 没有过期的证书
        search_limit 2 -> 有效期小于等于15天的证书 但未过期
        search_limit 3 -> 过期的证书
        search_limit 4 -> 过期时间1年以上的证书
        """
        search_name = None
        search_limit = 0
        force_refresh = False

        try:
            if "search_name" in get:
                search_name = get.search_name.strip()
            if "search_limit" in get:
                search_limit = int(get.search_limit.strip())
            if "force_refresh" in get and get.force_refresh.strip() in ("1", 1, "True", True):
                force_refresh = True

        except (ValueError, AttributeError, KeyError):
            return json_response(status=False, msg="参数错误")

        param = None
        if search_name is not None:
            param = ['subject LIKE ?', ["%{}%".format(search_name)]]

        now = datetime.now()
        filter_func: Callable[[dict, ], bool] = lambda x: True
        if search_limit == 1:
            date = now.strftime("%Y-%m-%d")
            filter_func: Callable[[dict, ], bool] = lambda x: x["not_after"] >= date
        elif search_limit == 2:
            date1 = now.strftime("%Y-%m-%d")
            date2 = (now + timedelta(days=15)).strftime("%Y-%m-%d")
            filter_func: Callable[[dict, ], bool] = lambda x: date1 <= x["not_after"] <= date2
        elif search_limit == 3:
            date = now.strftime("%Y-%m-%d")
            filter_func: Callable[[dict, ], bool] = lambda x: x["not_after"] < date
        elif search_limit == 4:
            date = (now + timedelta(days=366)).strftime("%Y-%m-%d")
            filter_func: Callable[[dict, ], bool] = lambda x: x["not_after"] > date
        try:
            res_list = RealSSLManger(self.conf_prefix).get_cert_list(param=param, force_refresh=force_refresh)
            res_list = list(filter(filter_func, res_list))
            res_list.sort(key=lambda x: x["not_after"])
            return json_response(status=True, data=res_list)
        except ValueError as e:
            return json_response(False, str(e))
        except Exception as e:
            return json_response(False, "操作错误：" + str(e))

    @staticmethod
    def set_ssl_protocol(get):
        """ 设置全局TLS版本
        @author baozi <202-04-18>
        @param:
        @return
        """
        protocols = {
            "TLSv1": False,
            "TLSv1.1": False,
            "TLSv1.2": False,
            "TLSv1.3": False,
        }
        if "use_protocols" in get:
            use_protocols = getattr(get, "use_protocols", [])
            if isinstance(use_protocols, list):
                for protocol in use_protocols:
                    if protocol in protocols:
                        protocols[protocol] = True
            elif isinstance(use_protocols, str):
                for protocol in use_protocols.split(","):
                    if protocol in protocols:
                        protocols[protocol] = True
            else:
                protocols["TLSv1.1"] = True
                protocols["TLSv1.2"] = True
                protocols["TLSv1.3"] = True

        else:
            protocols["TLSv1.1"] = True
            protocols["TLSv1.2"] = True
            protocols["TLSv1.3"] = True

        public.print_log(protocols)
        public.WriteFile(public.get_panel_path() + "/data/ssl_protocol.json", json.dumps(protocols))
        return public.returnMsg(True, 'SET_SUCCESS')

    @staticmethod
    def get_ssl_protocol(get=None):
        """ 获取全局TLS版本
        @author baozi <202-04-18>
        @param:
        @return
        """
        protocols = {
            "TLSv1": False,
            "TLSv1.1": True,
            "TLSv1.2": True,
            "TLSv1.3": False,
        }
        file_path = public.get_panel_path() + "/data/ssl_protocol.json"
        if os.path.exists(file_path):
            data = public.readFile(file_path)
            if data is not False:
                protocols = json.loads(data)
                return protocols

        return protocols
