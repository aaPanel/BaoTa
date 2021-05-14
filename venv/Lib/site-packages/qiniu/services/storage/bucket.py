# -*- coding: utf-8 -*-

from qiniu import config
from qiniu import http
from qiniu.utils import urlsafe_base64_encode, entry


class BucketManager(object):
    """空间管理类

    主要涉及了空间资源管理及批量操作接口的实现，具体的接口规格可以参考：
    http://developer.qiniu.com/docs/v6/api/reference/rs/

    Attributes:
        auth: 账号管理密钥对，Auth对象
    """

    def __init__(self, auth, zone=None):
        self.auth = auth
        if (zone is None):
            self.zone = config.get_default('default_zone')
        else:
            self.zone = zone

    def list(self, bucket, prefix=None, marker=None, limit=None, delimiter=None):
        """前缀查询:

        1. 首次请求 marker = None
        2. 无论 err 值如何，均应该先看 ret.get('items') 是否有内容
        3. 如果后续没有更多数据，err 返回 EOF，marker 返回 None（但不通过该特征来判断是否结束）
        具体规格参考:
        http://developer.qiniu.com/docs/v6/api/reference/rs/list.html

        Args:
            bucket:     空间名
            prefix:     列举前缀
            marker:     列举标识符
            limit:      单次列举个数限制
            delimiter:  指定目录分隔符

        Returns:
            一个dict变量，类似 {"hash": "<Hash string>", "key": "<Key string>"}
            一个ResponseInfo对象
            一个EOF信息。
        """
        options = {
            'bucket': bucket,
        }
        if marker is not None:
            options['marker'] = marker
        if limit is not None:
            options['limit'] = limit
        if prefix is not None:
            options['prefix'] = prefix
        if delimiter is not None:
            options['delimiter'] = delimiter

        url = '{0}/list'.format(config.get_default('default_rsf_host'))
        ret, info = self.__get(url, options)

        eof = False
        if ret and not ret.get('marker'):
            eof = True

        return ret, eof, info

    def stat(self, bucket, key):
        """获取文件信息:

        获取资源的元信息，但不返回文件内容，具体规格参考：
        https://developer.qiniu.com/kodo/api/1308/stat

        Args:
            bucket: 待获取信息资源所在的空间
            key:    待获取资源的文件名

        Returns:
            一个dict变量，类似：
                {
                    "fsize":        5122935,
                    "hash":         "ljfockr0lOil_bZfyaI2ZY78HWoH",
                    "mimeType":     "application/octet-stream",
                    "putTime":      13603956734587420
                    "type":         0
                }
            一个ResponseInfo对象
        """
        resource = entry(bucket, key)
        return self.__rs_do('stat', resource)

    def delete(self, bucket, key):
        """删除文件:

        删除指定资源，具体规格参考：
        http://developer.qiniu.com/docs/v6/api/reference/rs/delete.html

        Args:
            bucket: 待获取信息资源所在的空间
            key:    待获取资源的文件名

        Returns:
            一个dict变量，成功返回NULL，失败返回{"error": "<errMsg string>"}
            一个ResponseInfo对象
        """
        resource = entry(bucket, key)
        return self.__rs_do('delete', resource)

    def rename(self, bucket, key, key_to, force='false'):
        """重命名文件:

        给资源进行重命名，本质为move操作。

        Args:
            bucket: 待操作资源所在空间
            key:    待操作资源文件名
            key_to: 目标资源文件名

        Returns:
            一个dict变量，成功返回NULL，失败返回{"error": "<errMsg string>"}
            一个ResponseInfo对象
        """
        return self.move(bucket, key, bucket, key_to, force)

    def move(self, bucket, key, bucket_to, key_to, force='false'):
        """移动文件:

        将资源从一个空间到另一个空间，具体规格参考：
        http://developer.qiniu.com/docs/v6/api/reference/rs/move.html

        Args:
            bucket:     待操作资源所在空间
            bucket_to:  目标资源空间名
            key:        待操作资源文件名
            key_to:     目标资源文件名

        Returns:
            一个dict变量，成功返回NULL，失败返回{"error": "<errMsg string>"}
            一个ResponseInfo对象
        """
        resource = entry(bucket, key)
        to = entry(bucket_to, key_to)
        return self.__rs_do('move', resource, to, 'force/{0}'.format(force))

    def copy(self, bucket, key, bucket_to, key_to, force='false'):
        """复制文件:

        将指定资源复制为新命名资源，具体规格参考：
        http://developer.qiniu.com/docs/v6/api/reference/rs/copy.html

        Args:
            bucket:     待操作资源所在空间
            bucket_to:  目标资源空间名
            key:        待操作资源文件名
            key_to:     目标资源文件名

        Returns:
            一个dict变量，成功返回NULL，失败返回{"error": "<errMsg string>"}
            一个ResponseInfo对象
        """
        resource = entry(bucket, key)
        to = entry(bucket_to, key_to)
        return self.__rs_do('copy', resource, to, 'force/{0}'.format(force))

    def fetch(self, url, bucket, key=None):
        """抓取文件:
        从指定URL抓取资源，并将该资源存储到指定空间中，具体规格参考：
        http://developer.qiniu.com/docs/v6/api/reference/rs/fetch.html

        Args:
            url:    指定的URL
            bucket: 目标资源空间
            key:    目标资源文件名

        Returns:
            一个dict变量，成功返回NULL，失败返回{"error": "<errMsg string>"}
            一个ResponseInfo对象
        """
        resource = urlsafe_base64_encode(url)
        to = entry(bucket, key)
        return self.__io_do(bucket, 'fetch', resource, 'to/{0}'.format(to))

    def prefetch(self, bucket, key):
        """镜像回源预取文件:

        从镜像源站抓取资源到空间中，如果空间中已经存在，则覆盖该资源，具体规格参考
        http://developer.qiniu.com/docs/v6/api/reference/rs/prefetch.html

        Args:
            bucket: 待获取资源所在的空间
            key:    代获取资源文件名

        Returns:
            一个dict变量，成功返回NULL，失败返回{"error": "<errMsg string>"}
            一个ResponseInfo对象
        """
        resource = entry(bucket, key)
        return self.__io_do(bucket, 'prefetch', resource)

    def change_mime(self, bucket, key, mime):
        """修改文件mimeType:

        主动修改指定资源的文件类型，具体规格参考：
        http://developer.qiniu.com/docs/v6/api/reference/rs/chgm.html

        Args:
            bucket: 待操作资源所在空间
            key:    待操作资源文件名
            mime:   待操作文件目标mimeType
        """
        resource = entry(bucket, key)
        encode_mime = urlsafe_base64_encode(mime)
        return self.__rs_do('chgm', resource, 'mime/{0}'.format(encode_mime))

    def change_type(self, bucket, key, storage_type):
        """修改文件的存储类型

        修改文件的存储类型为普通存储或者是低频存储，参考文档：
        https://developer.qiniu.com/kodo/api/3710/modify-the-file-type

        Args:
            bucket:         待操作资源所在空间
            key:            待操作资源文件名
            storage_type:   待操作资源存储类型，0为普通存储，1为低频存储
        """
        resource = entry(bucket, key)
        return self.__rs_do('chtype', resource, 'type/{0}'.format(storage_type))

    def change_status(self, bucket, key, status, cond):
        """修改文件的状态

        修改文件的存储类型为可用或禁用：

        Args:
            bucket:         待操作资源所在空间
            key:            待操作资源文件名
            storage_type:   待操作资源存储类型，0为启用，1为禁用
        """
        resource = entry(bucket, key)
        if cond and isinstance(cond, dict):
            condstr = ""
            for k, v in cond.items():
                condstr += "{0}={1}&".format(k, v)
            condstr = urlsafe_base64_encode(condstr[:-1])
            return self.__rs_do('chstatus', resource, 'status/{0}'.format(status), 'cond', condstr)
        return self.__rs_do('chstatus', resource, 'status/{0}'.format(status))

    def batch(self, operations):
        """批量操作:

        在单次请求中进行多个资源管理操作，具体规格参考：
        http://developer.qiniu.com/docs/v6/api/reference/rs/batch.html

        Args:
            operations: 资源管理操作数组，可通过

        Returns:
            一个dict变量，返回结果类似：
                [
                    { "code": <HttpCode int>, "data": <Data> },
                    { "code": <HttpCode int> },
                    { "code": <HttpCode int> },
                    { "code": <HttpCode int> },
                    { "code": <HttpCode int>, "data": { "error": "<ErrorMessage string>" } },
                    ...
                ]
            一个ResponseInfo对象
        """
        url = '{0}/batch'.format(config.get_default('default_rs_host'))
        return self.__post(url, dict(op=operations))

    def buckets(self):
        """获取所有空间名:

        获取指定账号下所有的空间名。

        Returns:
            一个dict变量，类似：
                [ <Bucket1>, <Bucket2>, ... ]
            一个ResponseInfo对象
        """
        return self.__rs_do('buckets')

    def delete_after_days(self, bucket, key, days):
        """更新文件生命周期

        Returns:
            一个dict变量，返回结果类似：
                [
                    { "code": <HttpCode int>, "data": <Data> },
                    { "code": <HttpCode int> },
                    { "code": <HttpCode int> },
                    { "code": <HttpCode int> },
                    { "code": <HttpCode int>, "data": { "error": "<ErrorMessage string>" } },
                    ...
                ]
            一个ResponseInfo对象
        Args:
            bucket: 目标资源空间
            key:    目标资源文件名
            days:   指定天数
        """
        resource = entry(bucket, key)
        return self.__rs_do('deleteAfterDays', resource, days)

    def mkbucketv2(self, bucket_name, region):
        """
        创建存储空间
        https://developer.qiniu.com/kodo/api/1382/mkbucketv2

        Args:
            bucket_name: 存储空间名
            region: 存储区域
        """
        bucket_name = urlsafe_base64_encode(bucket_name)
        return self.__rs_do('mkbucketv2', bucket_name, 'region', region)

    def list_bucket(self, region):
        """
        列举存储空间列表

        Args:
        """
        return self.__uc_do('v3/buckets?region={0}'.format(region))

    def bucket_info(self, bucket_name):
        """
        获取存储空间信息

        Args:
            bucket_name: 存储空间名
        """
        return self.__post('v2/bucketInfo?bucket={}'.format(bucket_name), )

    def __uc_do(self, operation, *args):
        return self.__server_do(config.get_default('default_uc_host'), operation, *args)

    def __rs_do(self, operation, *args):
        return self.__server_do(config.get_default('default_rs_host'), operation, *args)

    def __io_do(self, bucket, operation, *args):
        ak = self.auth.get_access_key()
        io_host = self.zone.get_io_host(ak, bucket)
        return self.__server_do(io_host, operation, *args)

    def __server_do(self, host, operation, *args):
        cmd = _build_op(operation, *args)
        url = '{0}/{1}'.format(host, cmd)
        return self.__post(url)

    def __post(self, url, data=None):
        return http._post_with_auth(url, data, self.auth)

    def __get(self, url, params=None):
        return http._get(url, params, self.auth)


def _build_op(*args):
    return '/'.join(args)


def build_batch_copy(source_bucket, key_pairs, target_bucket, force='false'):
    return _two_key_batch('copy', source_bucket, key_pairs, target_bucket, force)


def build_batch_rename(bucket, key_pairs, force='false'):
    return build_batch_move(bucket, key_pairs, bucket, force)


def build_batch_move(source_bucket, key_pairs, target_bucket, force='false'):
    return _two_key_batch('move', source_bucket, key_pairs, target_bucket, force)


def build_batch_delete(bucket, keys):
    return _one_key_batch('delete', bucket, keys)


def build_batch_stat(bucket, keys):
    return _one_key_batch('stat', bucket, keys)


def _one_key_batch(operation, bucket, keys):
    return [_build_op(operation, entry(bucket, key)) for key in keys]


def _two_key_batch(operation, source_bucket, key_pairs, target_bucket, force='false'):
    if target_bucket is None:
        target_bucket = source_bucket
    return [_build_op(operation, entry(source_bucket, k), entry(target_bucket, v), 'force/{0}'.format(force)) for k, v
            in key_pairs.items()]
