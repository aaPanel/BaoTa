# -*- coding: utf-8 -*-

from qiniu import http
import json

from qiniu.compat import is_py2
from qiniu.compat import is_py3

import hashlib


def urlencode(str):
    if is_py2:
        import urllib2
        return urllib2.quote(str)
    elif is_py3:
        import urllib.parse
        return urllib.parse.quote(str)


class CdnManager(object):
    def __init__(self, auth):
        self.auth = auth
        self.server = 'http://fusion.qiniuapi.com'

    def refresh_urls(self, urls):
        """
        刷新文件列表，文档 http://developer.qiniu.com/article/fusion/api/refresh.html

        Args:
            urls: 待刷新的文件外链列表

        Returns:
            一个dict变量和一个ResponseInfo对象
            参考代码 examples/cdn_manager.py
        """
        return self.refresh_urls_and_dirs(urls, None)

    def refresh_dirs(self, dirs):
        """
        刷新目录，文档 http://developer.qiniu.com/article/fusion/api/refresh.html

        Args:
            urls: 待刷新的目录列表

        Returns:
            一个dict变量和一个ResponseInfo对象
            参考代码 examples/cdn_manager.py
        """
        return self.refresh_urls_and_dirs(None, dirs)

    def refresh_urls_and_dirs(self, urls, dirs):
        """
        刷新文件目录，文档 http://developer.qiniu.com/article/fusion/api/refresh.html

        Args:
           urls: 待刷新的目录列表
           dirs: 待刷新的文件列表

        Returns:
           一个dict变量和一个ResponseInfo对象
           参考代码 examples/cdn_manager.py
       """
        req = {}
        if urls is not None and len(urls) > 0:
            req.update({"urls": urls})
        if dirs is not None and len(dirs) > 0:
            req.update({"dirs": dirs})

        body = json.dumps(req)
        url = '{0}/v2/tune/refresh'.format(self.server)
        return self.__post(url, body)

    def prefetch_urls(self, urls):
        """
        预取文件列表，文档 http://developer.qiniu.com/article/fusion/api/prefetch.html

        Args:
           urls: 待预取的文件外链列表

        Returns:
           一个dict变量和一个ResponseInfo对象
           参考代码 examples/cdn_manager.py
        """
        req = {}
        req.update({"urls": urls})

        body = json.dumps(req)
        url = '{0}/v2/tune/prefetch'.format(self.server)
        return self.__post(url, body)

    def get_bandwidth_data(self, domains, start_date, end_date, granularity):
        """
        查询带宽数据，文档 http://developer.qiniu.com/article/fusion/api/traffic-bandwidth.html

        Args:
           domains:     域名列表
           start_date:  起始日期
           end_date:    结束日期
           granularity: 数据间隔

        Returns:
           一个dict变量和一个ResponseInfo对象
           参考代码 examples/cdn_manager.py
        """
        req = {}
        req.update({"domains": ';'.join(domains)})
        req.update({"startDate": start_date})
        req.update({"endDate": end_date})
        req.update({"granularity": granularity})

        body = json.dumps(req)
        url = '{0}/v2/tune/bandwidth'.format(self.server)
        return self.__post(url, body)

    def get_flux_data(self, domains, start_date, end_date, granularity):
        """
        查询流量数据，文档 http://developer.qiniu.com/article/fusion/api/traffic-bandwidth.html

        Args:
           domains:     域名列表
           start_date:  起始日期
           end_date:    结束日期
           granularity: 数据间隔

        Returns:
           一个dict变量和一个ResponseInfo对象
           参考代码 examples/cdn_manager.py
        """
        req = {}
        req.update({"domains": ';'.join(domains)})
        req.update({"startDate": start_date})
        req.update({"endDate": end_date})
        req.update({"granularity": granularity})

        body = json.dumps(req)
        url = '{0}/v2/tune/flux'.format(self.server)
        return self.__post(url, body)

    def get_log_list_data(self, domains, log_date):
        """
        获取日志下载链接，文档 http://developer.qiniu.com/article/fusion/api/log.html

        Args:
           domains:     域名列表
           log_date:    日志日期

        Returns:
           一个dict变量和一个ResponseInfo对象
           参考代码 examples/cdn_manager.py
        """
        req = {}
        req.update({"domains": ';'.join(domains)})
        req.update({"day": log_date})

        body = json.dumps(req)
        url = '{0}/v2/tune/log/list'.format(self.server)
        return self.__post(url, body)

    def put_httpsconf(self, name, certid, forceHttps=False):
        """
        修改证书，文档 https://developer.qiniu.com/fusion/api/4246/the-domain-name#11

        Args:
           domains:     域名name
           CertID:      证书id，从上传或者获取证书列表里拿到证书id
           ForceHttps:  是否强制https跳转

        Returns:
           {}
        """
        req = {}
        req.update({"certid": certid})
        req.update({"forceHttps": forceHttps})

        body = json.dumps(req)
        url = '{0}/domain/{1}/httpsconf'.format(self.server, name)
        return self.__post(url, body)

    def __post(self, url, data=None):
        headers = {'Content-Type': 'application/json'}
        return http._post_with_auth_and_headers(url, data, self.auth, headers)


class DomainManager(object):
    def __init__(self, auth):
        self.auth = auth
        self.server = 'http://api.qiniu.com'

    def create_domain(self, name, body):
        """
        创建域名，文档 https://developer.qiniu.com/fusion/api/4246/the-domain-name

        Args:
           name:     域名, 如果是泛域名，必须以点号 . 开头
           bosy:     创建域名参数
        Returns:
           {}
        """
        url = '{0}/domain/{1}'.format(self.server, name)
        return self.__post(url, body)

    def get_domain(self, name):
        """
        获取域名信息，文档 https://developer.qiniu.com/fusion/api/4246/the-domain-name

        Args:
           name:     域名, 如果是泛域名，必须以点号 . 开头
        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回dict{}，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/domain/{1}'.format(self.server, name)
        return self.__post(url)

    def put_httpsconf(self, name, certid, forceHttps):
        """
        修改证书，文档 https://developer.qiniu.com/fusion/api/4246/the-domain-name#11

        Args:
           domains:     域名name
           CertID:      证书id，从上传或者获取证书列表里拿到证书id
           ForceHttps:  是否强制https跳转

        Returns:
           {}
        """
        req = {}
        req.update({"certid": certid})
        req.update({"forceHttps": forceHttps})

        body = json.dumps(req)
        url = '{0}/domain/{1}/httpsconf'.format(self.server, name)
        return self.__put(url, body)

    def create_sslcert(self, name, common_name, pri, ca):
        """
        修改证书，文档 https://developer.qiniu.com/fusion/api/4246/the-domain-name#11

        Args:
           name:        证书名称
           common_name: 相关域名
           pri:         证书私钥
           ca:          证书内容
        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回dict{certID: <CertID>}，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息


        """
        req = {}
        req.update({"name": name})
        req.update({"common_name": common_name})
        req.update({"pri": pri})
        req.update({"ca": ca})

        body = json.dumps(req)
        url = '{0}/sslcert'.format(self.server)
        return self.__post(url, body)

    def __post(self, url, data=None):
        headers = {'Content-Type': 'application/json'}
        return http._post_with_auth_and_headers(url, data, self.auth, headers)

    def __put(self, url, data=None):
        headers = {'Content-Type': 'application/json'}
        return http._put_with_auth_and_headers(url, data, self.auth, headers)


def create_timestamp_anti_leech_url(host, file_name, query_string, encrypt_key, deadline):
    """
    创建时间戳防盗链

    Args:
        host:              带访问协议的域名
        file_name:         原始文件名，不需要urlencode
        query_string:      查询参数，不需要urlencode
        encrypt_key:       时间戳防盗链密钥
        deadline:          链接有效期时间戳（以秒为单位）

    Returns:
        带时间戳防盗链鉴权访问链接
    """
    if query_string:
        url_to_sign = '{0}/{1}?{2}'.format(host, urlencode(file_name), query_string)
    else:
        url_to_sign = '{0}/{1}'.format(host, urlencode(file_name))

    path = '/{0}'.format(urlencode(file_name))
    expire_hex = str(hex(deadline))[2:]
    str_to_sign = '{0}{1}{2}'.format(encrypt_key, path, expire_hex).encode()
    sign_str = hashlib.md5(str_to_sign).hexdigest()

    if query_string:
        signed_url = '{0}&sign={1}&t={2}'.format(url_to_sign, sign_str, expire_hex)
    else:
        signed_url = '{0}?sign={1}&t={2}'.format(url_to_sign, sign_str, expire_hex)

    return signed_url
