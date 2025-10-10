# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 x3
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: baozi <baozi@bt.com>
# +-------------------------------------------------------------------

import json
import os
import shutil
import time
import sys
# try:
#     import OpenSSL
# except:
#     os.system('btpip uninstall pyOpenSSL')
#     os.system('btpip install pyOpenSSL==22.1.0')
#     import OpenSSL
from hashlib import md5
from datetime import datetime
from typing import Optional, Tuple, List, Dict

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
        self.check_and_add_ps_column()

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
            "'ps' TEXT DEFAULT '', "  # 新增字段ps，用于存储备份说明
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

    def check_and_add_ps_column(self):
        try:
            public.M('ssl_info').field('ps').select()
        except Exception as e:
            if "no such column: ps" in str(e):
                try:
                    public.M('ssl_info').execute("ALTER TABLE 'ssl_info' ADD 'ps' TEXT DEFAULT ''", ())
                except Exception as e:
                    pass


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



class SSLManger:
    _REFRESH_TIP = "{}/data/ssl_cloud_refresh.tip".format(public.get_panel_path())
    _OTHER_DATA_NAME = ("use_for_panel", "use_for_site",)

    def __init__(self):
        self._local_ssl_info_tool = None

    # 与letsencrypt对接
    @property
    def local_tool(self):
        if self._local_ssl_info_tool is None:
            self._local_ssl_info_tool = _LocalSSLInfoTool()
            return self._local_ssl_info_tool
        return self._local_ssl_info_tool

    # 用于部署
    @classmethod
    def get_cert_for_deploy(cls, ssl_hash: str) -> Dict:
        res = cls.find_ssl_info(ssl_hash=ssl_hash)
        if res is None:
            return public.returnMsg(False, '证书不存在!')
        data = {
            'privkey': public.readFile(res["path"] + '/privkey.pem'),
            'fullchain': public.readFile(res["path"] + '/fullchain.pem')
        }
        if not isinstance(data["privkey"], str) or not isinstance(data["fullchain"], str):
            return public.returnMsg(False, '证书读取错误!')
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

    def get_cert_info_by_hash(self, cert_hash):
        # ssl_db.init_db()
        """通过证书哈希值获取证书ID和备注信息(ps)"""
        record = public.M('ssl_info').where("hash=?", (cert_hash,)).field('id, ps').find()

        # print(record)
        if record:
            # 使用strip()方法删除键名周围的空格
            ps_key = next((key for key in record.keys() if key.strip() == 'ps'), None)
            ps_value = record[ps_key] if ps_key else ""
            return record['id'], ps_value
        else:
            return -1, ""  # 如果没有找到记录，返回空字符串

    @staticmethod
    def strf_date(sdate):
        return time.strftime('%Y-%m-%d', time.strptime(sdate, '%Y%m%d%H%M%S'))

    # 获取证书信息
    @classmethod
    def get_cert_info(cls, cert_filename: str = None, certificate: str = None):
        if cert_filename is not None and os.path.isfile(cert_filename):
            certificate = public.readFile(cert_filename)

        if not isinstance(certificate, str) or not certificate.startswith("-----BEGIN"):
            raise ValueError("证书格式错误")
        
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

    def get_cert_list(self, param: Optional[Tuple[str, List]] = None, force_refresh: bool = False) -> List:
        if self.need_refresh() or force_refresh:
            self._refresh_ssl_info_by_cloud()
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

        format_time_strs = ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S")
        today_time = datetime.today().timestamp()
        for value in res:
            value["dns"] = json.loads(value["dns"])
            value["info"] = json.loads(value["info"])
            value["auth_info"] = json.loads(value["auth_info"])
            value["use_for_site"] = json.loads(value["use_for_site"])
            end_time = None
            for f_str in format_time_strs:
                try:
                    end_time = int(
                        (datetime.strptime(value["not_after"], f_str).timestamp() - today_time) / (60 * 60 * 24)
                    )
                except:
                    continue

            if not end_time:
                end_time = 90

            value['endtime'] = end_time

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
                ssl_db.connection().where("id = ?", (ssl_id["id"], )).update({"cloud_id": -1})

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
    def _remove_ssl_from_local(cls, ssh_hash: str):  # 从本地获取可用证书
        local_path = '/www/server/panel/vhost/ssl'
        if not os.path.exists(local_path):
            return

        for p_name in os.listdir(local_path):
            pem_file = "{}/{}/fullchain.pem".format(local_path, p_name)

            if os.path.isfile(pem_file):
                hash_data = cls.ssl_hash(cert_filename=pem_file)
                if hash_data == ssh_hash:
                    shutil.rmtree("{}/{}".format(local_path, p_name))

    @classmethod
    def add_use_for_site(cls, site_id, ssl_id=None, ssl_hash=None) -> bool:
        return cls.change_use_for_site(site_id, ssl_id, ssl_hash, is_add=True)

    @classmethod
    def remove_use_for_site(cls, site_id, ssl_id=None, ssl_hash=None):
        return cls.change_use_for_site(site_id, ssl_id, ssl_hash, is_add=False)

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
    def remove_cert(self, ssl_id=None, ssl_hash=None, local: bool = False):
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
                    raise ValueError("本地以删除成功， 链接云端失败, 无法删除云端数据")
                raise ValueError("链接云端失败, 无法删除云端数据")

            ssl_db.connection().where("id = ?", (target["id"],)).update({"cloud_id": -1})

        return public.returnMsg(True, "删除成功")

    # 下载证书
    def upload_cert(self, ssl_id=None, ssl_hash=None):
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
                ssl_db.connection().where("id = ?", (target["id"], )).update({"cloud_id": cloud_id})

                return res_data
            else:
                return res_data
        except:
            raise ValueError('链接云端失败')

    def update_ssl_ps(self, ssl_id, ps):
        """更新SSL证书的备份说明"""
        try:
            ssl_db.connection().where("id=?", (ssl_id,)).update({'ps': ps})
            return True, "修改成功"
        except Exception as e:
            return False, "修改失败: {}".format(str(e))

    def get_ssl_ps(self, ssl_id):
        try:

            """获取SSL证书的备份说明"""
            ssl_db.init_db()
            data = ssl_db.connection().where("id=?", (ssl_id,)).field('ps').find()
            if data:
                return True, data['ps']
            else:
                return False, "证书不存在"
        except:
            print(traceback.format_exc())