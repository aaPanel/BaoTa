# -*- coding: utf-8 -*-
from qiniu import http, Auth
import json


class RtcServer(object):
    """
    直播连麦管理类
    主要涉及了直播连麦管理及操作接口的实现，具体的接口规格可以参考官方文档 https://developer.qiniu.com
    Attributes:
        auth: 账号管理密钥对，Auth对象

    """

    def __init__(self, auth):
        self.auth = auth
        self.host = 'http://rtc.qiniuapi.com'

    def create_app(self, data):
        return self.__post(self.host + '/v3/apps', data)

    def get_app(self, app_id=None):
        if app_id:
            return self.__get(self.host + '/v3/apps/%s' % app_id)
        else:
            return self.__get(self.host + '/v3/apps')

    def delete_app(self, app_id):
        return self.__delete(self.host + '/v3/apps/%s' % app_id)

    def update_app(self, app_id, data):
        return self.__post(self.host + '/v3/apps/%s' % app_id, data)

    def list_user(self, app_id, room_name):
        return self.__get(self.host + '/v3/apps/%s/rooms/%s/users' % (app_id, room_name))

    def kick_user(self, app_id, room_name, user_id):
        return self.__delete(self.host + '/v3/apps/%s/rooms/%s/users/%s' % (app_id, room_name, user_id))

    def list_active_rooms(self, app_id, room_name_prefix=None):
        if room_name_prefix:
            return self.__get(self.host + '/v3/apps/%s/rooms?prefix=%s' % (app_id, room_name_prefix))
        else:
            return self.__get(self.host + '/v3/apps/%s/rooms' % app_id)

    def __post(self, url, data=None):
        return http._post_with_qiniu_mac(url, data, self.auth)

    def __get(self, url, params=None):
        return http._get_with_qiniu_mac(url, params, self.auth)

    def __delete(self, url, params=None):
        return http._delete_with_qiniu_mac(url, params, self.auth)


def get_room_token(access_key, secret_key, room_access):
    auth = Auth(access_key, secret_key)
    room_access_str = json.dumps(room_access)
    room_token = auth.token_with_data(room_access_str)
    return room_token
