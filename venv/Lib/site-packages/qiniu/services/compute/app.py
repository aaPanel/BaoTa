# -*- coding: utf-8 -*-
from qiniu import http, QiniuMacAuth
from .config import KIRK_HOST
from .qcos_api import QcosClient


class AccountClient(object):
    """客户端入口

    使用账号密钥生成账号客户端，可以进一步：
    1、获取和操作账号数据
    2、获得部署的应用的客户端

    属性：
        auth: 账号管理密钥对，QiniuMacAuth对象
        host: API host，在『内网模式』下使用时，auth=None，会自动使用 apiproxy 服务

    接口：
        get_qcos_client(app_uri)
        create_qcos_client(app_uri)
        get_app_keys(app_uri)
        get_valid_app_auth(app_uri)
        get_account_info()
        get_app_region_products(app_uri)
        get_region_products(region)
        list_regions()
        list_apps()
        create_app(args)
        delete_app(app_uri)

    """

    def __init__(self, auth, host=None):
        self.auth = auth
        self.qcos_clients = {}
        if (auth is None):
            self.host = KIRK_HOST['APPPROXY']
        else:
            self.host = host or KIRK_HOST['APPGLOBAL']
        acc, info = self.get_account_info()
        self.uri = acc.get('name')

    def get_qcos_client(self, app_uri):
        """获得资源管理客户端
        缓存，但不是线程安全的
        """

        client = self.qcos_clients.get(app_uri)
        if (client is None):
            client = self.create_qcos_client(app_uri)
            self.qcos_clients[app_uri] = client

        return client

    def create_qcos_client(self, app_uri):
        """创建资源管理客户端

        """

        if (self.auth is None):
            return QcosClient(None)

        products = self.get_app_region_products(app_uri)
        auth = self.get_valid_app_auth(app_uri)

        if products is None or auth is None:
            return None

        return QcosClient(auth, products.get('api'))

    def get_app_keys(self, app_uri):
        """获得账号下应用的密钥

        列出指定应用的密钥，仅当访问者对指定应用有管理权限时有效：
            用户对创建的应用有管理权限。
            用户对使用的第三方应用没有管理权限，第三方应用的运维方有管理权限。

        Args:
            - app_uri: 应用的完整标识

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回秘钥列表，失败返回None
            - ResponseInfo    请求的Response信息
        """

        url = '{0}/v3/apps/{1}/keys'.format(self.host, app_uri)
        return http._get_with_qiniu_mac(url, None, self.auth)

    def get_valid_app_auth(self, app_uri):
        """获得账号下可用的应用的密钥

        列出指定应用的可用密钥

        Args:
            - app_uri: 应用的完整标识

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回可用秘钥列表，失败返回None
            - ResponseInfo    请求的Response信息
        """

        ret, retInfo = self.get_app_keys(app_uri)

        if ret is None:
            return None

        for k in ret:
            if (k.get('state') == 'enabled'):
                return QiniuMacAuth(k.get('ak'), k.get('sk'))

        return None

    def get_account_info(self):
        """获得当前账号的信息

        查看当前请求方（请求鉴权使用的 AccessKey 的属主）的账号信息。

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回用户信息，失败返回None
            - ResponseInfo    请求的Response信息
        """

        url = '{0}/v3/info'.format(self.host)
        return http._get_with_qiniu_mac(url, None, self.auth)

    def get_app_region_products(self, app_uri):
        """获得指定应用所在区域的产品信息

        Args:
            - app_uri: 应用的完整标识

        Returns:
            返回产品信息列表，若失败则返回None
        """
        apps, retInfo = self.list_apps()
        if apps is None:
            return None

        for app in apps:
            if (app.get('uri') == app_uri):
                return self.get_region_products(app.get('region'))

        return

    def get_region_products(self, region):
        """获得指定区域的产品信息

        Args:
            - region: 区域，如："nq"

        Returns:
            返回该区域的产品信息，若失败则返回None
        """

        regions, retInfo = self.list_regions()
        if regions is None:
            return None

        for r in regions:
            if r.get('name') == region:
                return r.get('products')

    def list_regions(self):
        """获得账号可见的区域的信息

        列出当前用户所有可使用的区域。

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回区域列表，失败返回None
            - ResponseInfo    请求的Response信息
        """

        url = '{0}/v3/regions'.format(self.host)
        return http._get_with_qiniu_mac(url, None, self.auth)

    def list_apps(self):
        """获得当前账号的应用列表

        列出所属应用为当前请求方的应用列表。

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回应用列表，失败返回None
            - ResponseInfo    请求的Response信息
        """

        url = '{0}/v3/apps'.format(self.host)
        return http._get_with_qiniu_mac(url, None, self.auth)

    def create_app(self, args):
        """创建应用

        在指定区域创建一个新应用，所属应用为当前请求方。

        Args:
            - args: 请求参数(json)，参考 http://kirk-docs.qiniu.com/apidocs/

        Returns:
            - result        成功返回所创建的应用信息，若失败则返回None
            - ResponseInfo  请求的Response信息
        """

        url = '{0}/v3/apps'.format(self.host)
        return http._post_with_qiniu_mac(url, args, self.auth)

    def delete_app(self, app_uri):
        """删除应用

        删除指定标识的应用，当前请求方对该应用应有删除权限。

        Args:
            - app_uri: 应用的完整标识

        Returns:
            - result        成功返回空dict{}，若失败则返回None
            - ResponseInfo  请求的Response信息
        """

        url = '{0}/v3/apps/{1}'.format(self.host, app_uri)
        return http._delete_with_qiniu_mac(url, None, self.auth)
