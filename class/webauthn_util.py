import os.path
import sys
import secrets
import json
from typing import Union, Optional, List, Dict, Tuple
from flask import Flask, request, jsonify, session, Response
try:
    import asn1crypto, cbor2
except:
    pass
    # os.system("{} -m pip install asn1crypto==1.5.1 cbor2==5.4.6".format(sys.executable))

from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
    options_to_json,
    base64url_to_bytes,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    AuthenticatorAttestationResponse,
    UserVerificationRequirement,
    RegistrationCredential,
    AuthenticationCredential,
    ResidentKeyRequirement,
    AttestationConveyancePreference,
    AuthenticatorAttachment,
    PublicKeyCredentialDescriptor,
    PublicKeyCredentialType,
    AuthenticatorTransport,
    AuthenticatorAssertionResponse,
)
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
from webauthn.helpers.cose import COSEAlgorithmIdentifier
from urllib.parse import urlparse

try:
    from BTPanel import cache
except:
    cache = dict()

import db
import public


class WebAuthn:
    fake=False
    _OP_TIMEOUT = 5 * 60 * 1000  # 操作5分钟超时, 单位毫秒（ms）
    _TIMEOUT = 5 * 60 # 缓存5分钟超时, 单位秒（s）
    _GLOBAL_STATUS_FILE = "data/passkey_auth.pl"

    def __init__(self):
        self._DB: "db.Sql" = self.create_table()

    @classmethod
    def is_enabled(cls) -> bool:
        return os.path.isfile(cls._GLOBAL_STATUS_FILE)

    @classmethod
    def enable_passkey(cls) ->  bool:
        if cls.is_enabled():
            return True
        try:
            with open(cls._GLOBAL_STATUS_FILE, "w") as f:
                f.write("1")
            return True
        except Exception:
            return False

    @classmethod
    def disable_passkey(cls) -> bool:
        if not cls.is_enabled():
            return True
        try:
            os.remove(cls._GLOBAL_STATUS_FILE)
        except Exception:
            return False
        return True


    @staticmethod
    def create_table() -> "db.Sql":
        import sqlite3
        panel_path = "/www/server/panel"
        _SQL = """
               CREATE TABLE IF NOT EXISTS `webauthn`
               (
                   `id`             INTEGER PRIMARY KEY AUTOINCREMENT,
                   `origin`         TEXT    NOT NULL,
                   `domain`         TEXT    NOT NULL,
                   `name`           TEXT    NOT NULL,
                   `uid`            INTEGER NOT NULL,
                   `challenge_data` TEXT    NOT NULL,
                   `status`         INTEGER NOT NULL DEFAULT 1, -- 状态，1为正常，0为禁用
                   `created_at`     INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
               );
               CREATE INDEX IF NOT EXISTS `idx_webauthn_origin` ON `webauthn` (`origin`);
               CREATE INDEX IF NOT EXISTS `idx_webauthn_domain` ON `webauthn` (`domain`); \
               """

        try:
            with sqlite3.connect("{}/data/db/webauthn.db".format(panel_path)) as conn:
                conn.executescript(_SQL)
                conn.commit()
        except Exception as e:
            import traceback
            print(traceback.format_exc(), flush=True)

        res_db = db.Sql()
        res_db._Sql__DB_FILE = "{}/data/db/webauthn.db".format(panel_path)
        return res_db

    # 生成注册选项
    def register_options(self, name: str, origin: str) -> Union[str, Response]:
        if session.get("tmp_login", None):
            return "临时授权登录无法操作登录信息"
        sess_uid = session.get("uid", None)
        if not sess_uid or not isinstance(sess_uid, int) or not sess_uid > 0:
            return "登录校验失败，请确保是正常登录使用，而非临时授权登录"
        public.set_module_logs("passkey_create_options", "passkey_create_options")
        try:
            u_p = urlparse(origin)
            origin = "{}://{}".format(u_p.scheme, u_p.netloc)
            domain = u_p.hostname
        except:
            return "无效的域名"

        if not name or not domain:
            return "名称 和 域名信息不能为空"

        # 查重
        if self._DB.table("webauthn").where("origin = ? AND uid = ? AND name = ?", (origin, sess_uid, name)).find():
            return "该用户登录凭证已存在"

        name_id = secrets.token_bytes(32)
        options = generate_registration_options(
            rp_id=domain,
            rp_name="BtPanelPasskey",
            user_id=name_id,
            user_name=name,
            user_display_name=name,
            authenticator_selection=AuthenticatorSelectionCriteria(
                user_verification=UserVerificationRequirement.PREFERRED,  # 允许用户验证（PIN/生物识别）
                resident_key=ResidentKeyRequirement.PREFERRED,  # 支持常驻密钥
                authenticator_attachment=AuthenticatorAttachment.PLATFORM  # 优先使用平台认证器（Windows Hello）
            ),
            attestation=AttestationConveyancePreference.NONE,
            exclude_credentials=[],
            timeout=self._OP_TIMEOUT,
        )
        challenge = options.challenge

        # 转换为JSON字符串并解析，获取前端使用的base64url格式的挑战值
        json_str = options_to_json(options)

        # 解析JSON字符串为字典再返回
        result = json.loads(json_str)
        frontend_challenge = result.get('challenge')

        # 存储base64url格式的挑战值，因为前端会返回这种格式
        cache_key = f'webauthn_challenge_{frontend_challenge}'
        cache.set(cache_key, {
            'username': name,
            'user_id': name_id.hex(),
            'sess_uid': sess_uid,
            'display_name': name,
            'domain': domain,
            'origin': origin,
            'type': 'registration',
            'challenge_bytes': challenge.hex()  # 同时存储原始字节用于验证
        })

        return jsonify(result)

    # 验证注册信息
    def verify_registration(self, credential: dict, challenge: str) -> Union[str, Response]:
        if session.get("tmp_login", None):
            return "临时授权登录无法操作登录信息"
        challenge = challenge.strip('"')
        challenge_data = cache.get(f'webauthn_challenge_{challenge}')
        if not challenge_data:
            return "没有查询到对应的验证信息"
        if not challenge_data['type'] == 'registration':
            return "该验证信息不是注册信息"

        # 解码前端传来的base64url数据
        credential_id = credential['id']
        raw_id = base64url_to_bytes(credential['rawId'])
        client_data_json = base64url_to_bytes(credential['response']['clientDataJSON'])
        attestation_object = base64url_to_bytes(credential['response']['attestationObject'])

        # 构造认证器响应
        auth_response = AuthenticatorAttestationResponse(
            client_data_json=client_data_json,
            attestation_object=attestation_object
        )

        # 构造注册凭证
        registration_credential = RegistrationCredential(
            id=credential_id,
            raw_id=raw_id,
            response=auth_response
        )

        try:
            # 验证注册响应
            verification = verify_registration_response(
                credential=registration_credential,
                expected_challenge=base64url_to_bytes(challenge),
                expected_rp_id=challenge_data["domain"],
                expected_origin=challenge_data["origin"],
            )
        except Exception as e:
            return "验证失败，凭证信息无效"

        # 存储用户信息
        username = challenge_data['username']
        need_auto_start=False
        if self._DB.table("webauthn").count() == 0:
            need_auto_start = True

        self._DB.table("webauthn").insert({
            "origin": challenge_data["origin"],
            "domain": challenge_data["domain"],
            "status": True,
            "name": username,
            "uid": challenge_data['sess_uid'],
            "challenge_data": json.dumps({
                'user_id': challenge_data['user_id'],
                'display_name': challenge_data['display_name'],
                'credential_id': verification.credential_id.hex(),
                'public_key': verification.credential_public_key.hex(),
                'sign_count': verification.sign_count,
                'domain': challenge_data['domain'],
                'uid': challenge_data['sess_uid'],
                'origin': challenge_data['origin'],
                # 'created_at': verification.credential_id.hex()  # 简化处理
            }),
        })
        public.set_module_logs("passkey_create_finished", "passkey_create_finished")

        # 清理挑战
        cache.delete(f'webauthn_challenge_{challenge}')
        if need_auto_start:
            self.enable_passkey()

        return public.returnMsg(True, "添加成功")

    # 生成登录选项
    ## username 可以传递用户表的用户名， 也可以是登录凭证名称
    def login_options(self, origin: str, username: Optional[str] = None) -> Union[str, Response]:
        try:
            u_p = urlparse(origin)
            origin = "{}://{}".format(u_p.scheme, u_p.netloc)
            domain = u_p.hostname
        except:
            return "无效的域名"

        if username and isinstance(username, str):
            username = username.strip()
        if username:
            user_data_list = self._DB.table("webauthn").where("origin = ? AND name = ? AND status = ?", (origin, username, True)).select()
            if not user_data_list:
                try:
                    target_uid = None
                    last_login_token = session.get("last_login_token")
                    user_info_list = public.M('users').where().field('id,username,salt').select()
                    for user_info in user_info_list:
                        u_name = user_info['username']
                        if len(username) == 32 and public.md5(public.md5(u_name + last_login_token)) == username:
                            target_uid = user_info['id']
                        elif len(username) <32 and username == u_name:
                            target_uid = user_info['id']
                        if target_uid:
                            break
                except:
                    return "无效的用户名"

                # 继续使用用户id去查找
                user_data_list = self._DB.table("webauthn").where("origin = ? AND uid = ? AND status = ?", (origin, target_uid, True)).select()
        else:
            user_data_list = self._DB.table("webauthn").where("origin = ? AND status = ?", (origin, True)).select()
        allow_user = []
        for user_data in user_data_list:
            challenge_data = json.loads(user_data['challenge_data'])
            credential_id_bytes = bytes.fromhex(challenge_data['credential_id'])
            allow_user.append({
                'id': credential_id_bytes,
                'username': user_data["name"],
                'user': challenge_data
            })
        if not allow_user:
            return "没有找到可以用凭证，无法快速登录"

        options = generate_authentication_options(
            rp_id=domain,
            allow_credentials=[
                PublicKeyCredentialDescriptor(
                    id=cred['id'],
                    type=PublicKeyCredentialType.PUBLIC_KEY,
                    transports=[AuthenticatorTransport.INTERNAL, AuthenticatorTransport.HYBRID]
                )
                for cred in allow_user
            ],
            user_verification=UserVerificationRequirement.PREFERRED,
            timeout=self._OP_TIMEOUT,
        )

        json_str = options_to_json(options)
        result = json.loads(json_str)
        frontend_challenge = result.get('challenge')

        cache.set(f'webauthn_challenge_{frontend_challenge}', {
            'type': 'discover_authentication',
            'credentials': {cred['username']: cred['user'] for cred in allow_user}
        }, self._TIMEOUT)
        public.set_module_logs("passkey_login_options", "passkey_login_options")

        return jsonify(result)


    # 验证登录信息
    def authentication_options(self, credential: dict, challenge: str) -> Union[str, Tuple[int, str]]:
        if not credential or not challenge:
            return '缺少必要参数'
        challenge = challenge.strip('"')
        challenge_data = cache.get(f'webauthn_challenge_{challenge}')
        if not challenge_data:
            return "Invalid challenge"
        #获取完之后立马清理掉缓存
        cache.delete(f'webauthn_challenge_{challenge}')
        auth_type = None
        if challenge_data:
            auth_type = challenge_data.get('type')

        if not challenge_data or auth_type != 'discover_authentication':
            return "验证数据无效"

        credential_id = credential.get('id')
        if not credential_id:
            return '缺少凭证ID'

        # 从存储的凭证信息中查找对应的用户
        credentials_map = challenge_data.get('credentials', {})
        found_user = None
        found_username = None
        found_credential_id = None

        for uname, user_data in credentials_map.items():
            stored_credential_id = user_data.get('credential_id', None)
            if not stored_credential_id:
                continue
            stored_credential_id_md5 = public.md5(bytes_to_base64url(bytes.fromhex(stored_credential_id)))
            if stored_credential_id_md5 == credential_id:
                found_username = uname
                found_user = user_data
                found_credential_id = stored_credential_id
                break

        if not found_username or not found_user:
            return '无法识别用户'

        # 解码前端传来的base64url数据
        credential_id = bytes_to_base64url(bytes.fromhex(found_credential_id))
        raw_id = base64url_to_bytes(credential['rawId'])
        client_data_json = base64url_to_bytes(credential['response']['clientDataJSON'])
        authenticator_data = base64url_to_bytes(credential['response']['authenticatorData'])
        signature = base64url_to_bytes(credential['response']['signature'])
        user_handle = base64url_to_bytes(credential['response']['userHandle']) if credential['response'].get(
            'userHandle') else None

        # 构造认证器断言响应
        auth_response = AuthenticatorAssertionResponse(
            client_data_json=client_data_json,
            authenticator_data=authenticator_data,
            signature=signature,
            user_handle=user_handle
        )

        # 构造认证凭证
        authentication_credential = AuthenticationCredential(
            id=credential_id,
            raw_id=raw_id,
            response=auth_response
        )

        # 将十六进制挑战值转换为字节
        expected_challenge_bytes = base64url_to_bytes(challenge)
        verification = verify_authentication_response(
            credential=authentication_credential,
            expected_challenge=expected_challenge_bytes,
            expected_rp_id=found_user["domain"],
            expected_origin=found_user["origin"],
            credential_public_key=bytes.fromhex(found_user['public_key']),
            credential_current_sign_count=found_user['sign_count'],
            require_user_verification=False,
        )
        public.set_module_logs("passkey_login", "passkey_login")

        # 更新签名计数
        found_user['sign_count'] = verification.new_sign_count
        self._DB.table("webauthn").where("origin = ? AND name = ?", (found_user["origin"], found_username)).update({
            "challenge_data": json.dumps(found_user)
        })
        # 返回实际的用户ID
        return found_user['uid'], found_username

    def query_users(self, keyword: str = None, page: int = 1, page_size: int = 10) -> Tuple[List[Dict], int, bool]:
        limit_str = "{}, {}".format(page_size * page - page_size, page_size)
        if keyword:
            where="name LIKE ? OR origin LIKE ?"
            param = ("%{}%".format(keyword), "%{}%".format(keyword))
            users = self._DB.table("webauthn").where(where, param).limit(limit_str).select()
            count = self._DB.table("webauthn").where(where, param).count()
        else:
            users = self._DB.table("webauthn").limit(limit_str).select()
            count = self._DB.table("webauthn").count()

        user_name_data = public.M("users").field("id, name").select()
        user_name_map = {user_name["id"]: user_name["name"] for user_name in user_name_data}

        res_list = []
        for user in users:
            user_name = user_name_map.get(user["uid"], "-")
            sign_count = json.loads(user["challenge_data"])["sign_count"]
            res_list.append({
                "id": user["id"],
                "name": user["name"],
                "uid": user["uid"],
                "username": user_name,
                "origin": user["origin"],
                "status": bool(user["status"]),
                "created_at": user["created_at"],
                "sign_count": sign_count,
            })

        return res_list, count, self.is_enabled()


    def set_user_satus(self, pass_id: int, status: bool) -> Optional[str]:
        if not isinstance(status, bool):
            return "参数错误，请传入布尔值"
        if not isinstance(pass_id, int):
            return "参数错误，请传入必要id"
        if not self._DB.table("webauthn").where("id = ?", pass_id).find():
            return "找不到该凭证信息"
        self._DB.table("webauthn").where("id = ?", pass_id).update({"status": status})
        return

    def remove_pass(self, pass_id: int) -> Optional[str]:
        if not isinstance(pass_id, int):
            return "参数错误，请传入必要id"
        if not self._DB.table("webauthn").where("id = ?", pass_id).find():
            return "找不到该凭证信息"
        self._DB.table("webauthn").where("id = ?", pass_id).delete()
        return
