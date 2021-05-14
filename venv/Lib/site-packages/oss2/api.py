# -*- coding: utf-8 -*-

"""
文件上传方法中的data参数
------------------------
诸如 :func:`put_object <Bucket.put_object>` 这样的上传接口都会有 `data` 参数用于接收用户数据。`data` 可以是下述类型
    - unicode类型（对于Python3则是str类型）：内部会自动转换为UTF-8的bytes
    - bytes类型：不做任何转换
    - file-like object：对于可以seek和tell的file object，从当前位置读取直到结束。其他类型，请确保当前位置是文件开始。
    - 可迭代类型：对于无法探知长度的数据，要求一定是可迭代的。此时会通过Chunked Encoding传输。

Bucket配置修改方法中的input参数
-----------------------------
诸如 :func:`put_bucket_cors <Bucket.put_bucket_cors>` 这样的Bucket配置修改接口都会有 `input` 参数接收用户提供的配置数据。
`input` 可以是下述类型
  - Bucket配置信息相关的类，如 `BucketCors`
  - unicode类型（对于Python3则是str类型）
  - 经过utf-8编码的bytes类型
  - file-like object
  - 可迭代类型，会通过Chunked Encoding传输
也就是说 `input` 参数可以比 `data` 参数多接受第一种类型的输入。

返回值
------
:class:`Service` 和 :class:`Bucket` 类的大多数方法都是返回 :class:`RequestResult <oss2.models.RequestResult>`
及其子类。`RequestResult` 包含了HTTP响应的状态码、头部以及OSS Request ID，而它的子类则包含用户真正想要的结果。例如，
`ListBucketsResult.buckets` 就是返回的Bucket信息列表；`GetObjectResult` 则是一个file-like object，可以调用 `read()` 来获取响应的
HTTP包体。

:class:`CryptoBucket`:
加密接口
-------
CryptoBucket仅提供上传下载加密数据的接口，诸如`get_object` 、 `put_object` ，返回值与Bucket相应接口一致。


异常
----
一般来说Python SDK可能会抛出三种类型的异常，这些异常都继承于 :class:`OssError <oss2.exceptions.OssError>` ：
    - :class:`ClientError <oss2.exceptions.ClientError>` ：由于用户参数错误而引发的异常；
    - :class:`ServerError <oss2.exceptions.ServerError>` 及其子类：OSS服务器返回非成功的状态码，如4xx或5xx；
    - :class:`RequestError <oss2.exceptions.RequestError>` ：底层requests库抛出的异常，如DNS解析错误，超时等；
当然，`Bucket.put_object_from_file` 和 `Bucket.get_object_to_file` 这类函数还会抛出文件相关的异常。


.. _byte_range:

指定下载范围
------------
诸如 :func:`get_object <Bucket.get_object>` 以及 :func:`upload_part_copy <Bucket.upload_part_copy>` 这样的函数，可以接受
`byte_range` 参数，表明读取数据的范围。该参数是一个二元tuple：(start, last)。这些接口会把它转换为Range头部的值，如：
    - byte_range 为 (0, 99) 转换为 'bytes=0-99'，表示读取前100个字节
    - byte_range 为 (None, 99) 转换为 'bytes=-99'，表示读取最后99个字节
    - byte_range 为 (100, None) 转换为 'bytes=100-'，表示读取第101个字节到文件结尾的部分（包含第101个字节）


分页罗列
-------
罗列各种资源的接口，如 :func:`list_buckets <Service.list_buckets>` 、 :func:`list_objects <Bucket.list_objects>` 都支持
分页查询。通过设定分页标记（如：`marker` 、 `key_marker` ）的方式可以指定查询某一页。首次调用将分页标记设为空（缺省值，可以不设），
后续的调用使用返回值中的 `next_marker` 、 `next_key_marker` 等。每次调用后检查返回值中的 `is_truncated` ，其值为 `False` 说明
已经到了最后一页。

.. _line_range:

指定查询CSV文件范围
------------
诸如 :func:`select_object <Bucket.select_object>` 以及 :func:`select_object_to_file <Bucket.select_object_to_file>` 这样的函数的select_csv_params参数，可以接受
`LineRange` 参数，表明读取CSV数据的范围。该参数是一个二元tuple：(start, last):
    - LineRange 为 (0, 99) 表示读取前100行
    - LineRange 为 (None, 99) 表示读取最后99行
    - LineRange 为 (100, None) 表示读取第101行到文件结尾的部分（包含第101行）

.. _split_range:

指定查询CSV文件范围
------------
split可以认为是切分好的大小大致相等的csv行簇。每个Split大小大致相等，这样以便更好的做到负载均衡。
诸如 :func:`select_object <Bucket.select_object>` 以及 :func:`select_object_to_file <Bucket.select_object_to_file>` 这样的函数的select_csv_params参数，可以接受
`SplitRange` 参数，表明读取CSV数据的范围。该参数是一个二元tuple：(start, last):
    - SplitRange 为 (0, 9) 表示读取前10个Split
    - SplitRange 为 (None, 9) 表示读取最后9个split
    - SplitRange 为 (10, None) 表示读取第11个split到文件结尾的部分（包含第11个Split）

分页查询
-------
和create_csv_object_meta配合使用，有两种方法：
    - 方法1：先获取文件总的行数(create_csv_object_meta返回)，然后把文件以line_range分成若干部分并行查询
    - 方法2：先获取文件总的Split数(create_csv_object_meta返回), 然后把文件分成若干个请求，每个请求含有大致相等的Split

.. _progress_callback:

上传下载进度
-----------
上传下载接口，诸如 `get_object` 、 `put_object` 、`resumable_upload`，都支持进度回调函数，可以用它实现进度条等功能。

`progress_callback` 的函数原型如下 ::

    def progress_callback(bytes_consumed, total_bytes):
        '''进度回调函数。

        :param int bytes_consumed: 已经消费的字节数。对于上传，就是已经上传的量；对于下载，就是已经下载的量。
        :param int total_bytes: 总长度。
        '''

其中 `total_bytes` 对于上传和下载有不同的含义：
    - 上传：当输入是bytes或可以seek/tell的文件对象，那么它的值就是总的字节数；否则，其值为None
    - 下载：当返回的HTTP相应中有Content-Length头部，那么它的值就是Content-Length的值；否则，其值为None


.. _unix_time:

Unix Time
---------
OSS Python SDK会把从服务器获得时间戳都转换为自1970年1月1日UTC零点以来的秒数，即Unix Time。
参见 `Unix Time <https://en.wikipedia.org/wiki/Unix_time>`_

OSS中常用的时间格式有
    - HTTP Date格式，形如 `Sat, 05 Dec 2015 11:04:39 GMT` 这样的GMT时间。
      用在If-Modified-Since、Last-Modified这些HTTP请求、响应头里。
    - ISO8601格式，形如 `2015-12-05T00:00:00.000Z`。
      用在生命周期管理配置、列举Bucket结果中的创建时间、列举文件结果中的最后修改时间等处。

`http_date` 函数把Unix Time转换为HTTP Date；而 `http_to_unixtime` 则做相反的转换。如 ::

    >>> import oss2, time
    >>> unix_time = int(time.time())             # 当前UNIX Time，设其值为 1449313829
    >>> date_str = oss2.http_date(unix_time)     # 得到 'Sat, 05 Dec 2015 11:10:29 GMT'
    >>> oss2.http_to_unixtime(date_str)          # 得到 1449313829

.. note::

    生成HTTP协议所需的日期（即HTTP Date）时，请使用 `http_date` ， 不要使用 `strftime` 这样的函数。因为后者是和locale相关的。
    比如，`strftime` 结果中可能会出现中文，而这样的格式，OSS服务器是不能识别的。

`iso8601_to_unixtime` 把ISO8601格式转换为Unix Time；`date_to_iso8601` 和 `iso8601_to_date` 则在ISO8601格式的字符串和
datetime.date之间相互转换。如 ::

    >>> import oss2
    >>> d = oss2.iso8601_to_date('2015-12-05T00:00:00.000Z')  # 得到 datetime.date(2015, 12, 5)
    >>> date_str = oss2.date_to_iso8601(d)                    # 得到 '2015-12-05T00:00:00.000Z'
    >>> oss2.iso8601_to_unixtime(date_str)                    # 得到 1449273600

.. _select_params:

    指定OSS Select的文件格式。
    对于Csv文件，支持如下Keys:
    >>> CsvHeaderInfo: None|Use|Ignore   #None表示没有CSV Schema头，Use表示启用CSV Schema头，可以在Select语句中使用Name，Ignore表示有CSV Schema头，但忽略它（Select语句中不可以使用Name)
                        默认值是None
    >>> CommentCharacter: Comment字符,默认值是#,不支持多个字符
    >>> RecordDelimiter: 行分隔符，默认是\n,最多支持两个字符分隔符（比如:\r\n)
    >>> FieldDelimiter: 列分隔符，默认是逗号(,), 不支持多个字符
    >>> QuoteCharacter: 列Quote字符，默认是双引号("),不支持多个字符。注意转义符合Quote字符相同。
    >>> LineRange: 指定查询CSV文件的行范围，参见 `line_range`。
    >>> SplitRange: 指定查询CSV文件的Split范围，参见 `split_range`.
        注意LineRange和SplitRange两种不能同时指定。若同时指定LineRange会被忽略。
    >>> CompressionType: 文件的压缩格式，默认值是None, 支持GZIP。
    >>> OutputRawData: 指定是响应Body返回Raw数据，默认值是False.
    >>> SkipPartialDataRecord: 当CSV行数据不完整时(select语句中出现的列在该行为空)，是否跳过该行。默认是False。
    >>> OutputHeader:是否输出CSV Header，默认是False.
    >>> EnablePayloadCrc:是否启用对Payload的CRC校验,默认是False. 该选项不能和OutputRawData:True混用。
    >>> MaxSkippedRecordsAllowed: 允许跳过的最大行数。默认值是0表示一旦有一行跳过就报错。当下列两种情况下该行CSV被跳过:1）当SkipPartialDataRecord为True时且该行不完整时 2）当该行的数据类型和SQL不匹配时
    对于Json 文件, 支持如下Keys:
    >>> Json_Type: DOCUMENT | LINES . DOCUMENT就是指一般的Json文件，LINES是指每一行是一个合法的JSON对象，文件由多行Json对象组成，整个文件本身不是合法的Json对象。
    >>> LineRange: 指定查询JSON LINE文件的行范围，参见 `line_range`。注意该参数仅支持LINES类型
    >>> SplitRange: 指定查询JSON LINE文件的Split范围，参见 `split_range`.注意该参数仅支持LINES类型
    >>> CompressionType: 文件的压缩格式，默认值是None, 支持GZIP。
    >>> OutputRawData: 指定是响应Body返回Raw数据，默认值是False. 
    >>> SkipPartialDataRecord: 当一条JSON记录数据不完整时(select语句中出现的Key在该对象为空)，是否跳过该Json记录。默认是False。
    >>> EnablePayloadCrc:是否启用对Payload的CRC校验,默认是False. 该选项不能和OutputRawData:True混用。
    >>> MaxSkippedRecordsAllowed: 允许跳过的最大Json记录数。默认值是0表示一旦有一条Json记录跳过就报错。当下列两种情况下该JSON被跳过:1）当SkipPartialDataRecord为True时且该条Json记录不完整时 2）当该记录的数据类型和SQL不匹配时
    >>> ParseJsonNumberAsString: 将Json文件中的数字解析成字符串。使用场景是当Json文件中的浮点数精度较高时，系统默认的浮点数精度无法达到要求，当解析成字符串时将完整保留原始数据精度，在Sql中使用Cast可以将字符串无精度损失地转成decimal.
    >>> AllowQuotedRecordDelimiter: 允许CSV中的列包含转义过的换行符。默认为true。当值为False时，select API可以用Range：bytes来设置选取目标对象内容的范围
    ‘
.. _select_meta_params:

    create_select_object_meta参数集合，支持如下Keys:
    - RecordDelimiter: CSV换行符，最多支持两个字符
    - FieldDelimiter: CSV列分隔符，最多支持一个字符
    - QuoteCharacter: CSV转移Quote符，最多支持一个字符
    - OverwriteIfExists: true|false. true表示重新获得csv meta，并覆盖原有的meta。一般情况下不需要使用

"""
import logging

from . import xml_utils
from . import http
from . import utils
from . import exceptions
from . import defaults
from . import models
from . import select_params

from .models import *
from .compat import urlquote, urlparse, to_unicode, to_string
from .crypto import BaseCryptoProvider
from .headers import *
from .select_params import *

import time
import shutil
import base64

logger = logging.getLogger(__name__)


class _Base(object):
    def __init__(self, auth, endpoint, is_cname, session, connect_timeout,
                 app_name='', enable_crc=True):
        self.auth = auth
        self.endpoint = _normalize_endpoint(endpoint.strip())
        self.session = session or http.Session()
        self.timeout = defaults.get(connect_timeout, defaults.connect_timeout)
        self.app_name = app_name
        self.enable_crc = enable_crc

        self._make_url = _UrlMaker(self.endpoint, is_cname)

    def _do(self, method, bucket_name, key, **kwargs):
        key = to_string(key)
        req = http.Request(method, self._make_url(bucket_name, key),
                           app_name=self.app_name,
                           **kwargs)
        self.auth._sign_request(req, bucket_name, key)

        resp = self.session.do_request(req, timeout=self.timeout)
        if resp.status // 100 != 2:
            e = exceptions.make_exception(resp)
            logger.info("Exception: {0}".format(e))
            raise e

        # Note that connections are only released back to the pool for reuse once all body data has been read;
        # be sure to either set stream to False or read the content property of the Response object.
        # For more details, please refer to http://docs.python-requests.org/en/master/user/advanced/#keep-alive.
        content_length = models._hget(resp.headers, 'content-length', int)
        if content_length is not None and content_length == 0:
            resp.read()

        return resp

    def _do_url(self, method, sign_url, **kwargs):
        req = http.Request(method, sign_url, app_name=self.app_name, **kwargs)
        resp = self.session.do_request(req, timeout=self.timeout)
        if resp.status // 100 != 2:
            e = exceptions.make_exception(resp)
            logger.info("Exception: {0}".format(e))
            raise e

        # Note that connections are only released back to the pool for reuse once all body data has been read;
        # be sure to either set stream to False or read the content property of the Response object.
        # For more details, please refer to http://docs.python-requests.org/en/master/user/advanced/#keep-alive.
        content_length = models._hget(resp.headers, 'content-length', int)
        if content_length is not None and content_length == 0:
            resp.read()

        return resp

    def _parse_result(self, resp, parse_func, klass):
        result = klass(resp)
        parse_func(result, resp.read())
        return result


class Service(_Base):
    """用于Service操作的类，如罗列用户所有的Bucket。

    用法 ::

        >>> import oss2
        >>> auth = oss2.Auth('your-access-key-id', 'your-access-key-secret')
        >>> service = oss2.Service(auth, 'oss-cn-hangzhou.aliyuncs.com')
        >>> service.list_buckets()
        <oss2.models.ListBucketsResult object at 0x0299FAB0>

    :param auth: 包含了用户认证信息的Auth对象
    :type auth: oss2.Auth

    :param str endpoint: 访问域名，如杭州区域的域名为oss-cn-hangzhou.aliyuncs.com

    :param session: 会话。如果是None表示新开会话，非None则复用传入的会话
    :type session: oss2.Session

    :param float connect_timeout: 连接超时时间，以秒为单位。
    :param str app_name: 应用名。该参数不为空，则在User Agent中加入其值。
        注意到，最终这个字符串是要作为HTTP Header的值传输的，所以必须要遵循HTTP标准。
    """

    QOS_INFO = 'qosInfo'

    def __init__(self, auth, endpoint,
                 session=None,
                 connect_timeout=None,
                 app_name=''):
        logger.debug("Init oss service, endpoint: {0}, connect_timeout: {1}, app_name: {2}".format(
            endpoint, connect_timeout, app_name))
        super(Service, self).__init__(auth, endpoint, False, session, connect_timeout,
                                      app_name=app_name)

    def list_buckets(self, prefix='', marker='', max_keys=100, params=None):
        """根据前缀罗列用户的Bucket。

        :param str prefix: 只罗列Bucket名为该前缀的Bucket，空串表示罗列所有的Bucket
        :param str marker: 分页标志。首次调用传空串，后续使用返回值中的next_marker
        :param int max_keys: 每次调用最多返回的Bucket数目
        :param dict params: list操作参数，传入'tag-key','tag-value'对结果进行过滤

        :return: 罗列的结果
        :rtype: oss2.models.ListBucketsResult
        """
        logger.debug("Start to list buckets, prefix: {0}, marker: {1}, max-keys: {2}".format(prefix, marker, max_keys))

        listParam = {}
        listParam['prefix'] = prefix
        listParam['marker'] = marker
        listParam['max-keys'] = str(max_keys)

        if params is not None:
            if 'tag-key' in params:
                listParam['tag-key'] = params['tag-key']
            if 'tag-value' in params:
                listParam['tag-value'] = params['tag-value']

        resp = self._do('GET', '', '', params=listParam)
        logger.debug("List buckets done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return self._parse_result(resp, xml_utils.parse_list_buckets, ListBucketsResult)

    def get_user_qos_info(self):
        """获取User的QoSInfo
        :return: :class:`GetUserQosInfoResult <oss2.models.GetUserQosInfoResult>`
        """
        logger.debug("Start to get user qos info.")
        resp = self._do('GET', '', '', params={Service.QOS_INFO: ''})
        logger.debug("get use qos, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return self._parse_result(resp, xml_utils.parse_get_qos_info, GetUserQosInfoResult)

class Bucket(_Base):
    """用于Bucket和Object操作的类，诸如创建、删除Bucket，上传、下载Object等。

    用法（假设Bucket属于杭州区域） ::

        >>> import oss2
        >>> auth = oss2.Auth('your-access-key-id', 'your-access-key-secret')
        >>> bucket = oss2.Bucket(auth, 'http://oss-cn-hangzhou.aliyuncs.com', 'your-bucket')
        >>> bucket.put_object('readme.txt', 'content of the object')
        <oss2.models.PutObjectResult object at 0x029B9930>

    :param auth: 包含了用户认证信息的Auth对象
    :type auth: oss2.Auth

    :param str endpoint: 访问域名或者CNAME
    :param str bucket_name: Bucket名
    :param bool is_cname: 如果endpoint是CNAME则设为True；反之，则为False。

    :param session: 会话。如果是None表示新开会话，非None则复用传入的会话
    :type session: oss2.Session

    :param float connect_timeout: 连接超时时间，以秒为单位。

    :param str app_name: 应用名。该参数不为空，则在User Agent中加入其值。
        注意到，最终这个字符串是要作为HTTP Header的值传输的，所以必须要遵循HTTP标准。
    """

    ACL = 'acl'
    CORS = 'cors'
    LIFECYCLE = 'lifecycle'
    LOCATION = 'location'
    LOGGING = 'logging'
    REFERER = 'referer'
    WEBSITE = 'website'
    LIVE = 'live'
    COMP = 'comp'
    STATUS = 'status'
    VOD = 'vod'
    SYMLINK = 'symlink'
    STAT = 'stat'
    BUCKET_INFO = 'bucketInfo'
    PROCESS = 'x-oss-process'
    TAGGING = 'tagging'
    ENCRYPTION = 'encryption'
    VERSIONS = 'versions'
    VERSIONING = 'versioning'
    VERSIONID = 'versionId'
    RESTORE = 'restore'
    OBJECTMETA = 'objectMeta'
    POLICY = 'policy'
    REQUESTPAYMENT  = 'requestPayment'
    QOS_INFO = 'qosInfo'
    USER_QOS = 'qos'
    ASYNC_FETCH = 'asyncFetch'
    SEQUENTIAL = 'sequential'

    def __init__(self, auth, endpoint, bucket_name,
                 is_cname=False,
                 session=None,
                 connect_timeout=None,
                 app_name='',
                 enable_crc=True):
        logger.debug("Init oss bucket, endpoint: {0}, isCname: {1}, connect_timeout: {2}, app_name: {3}, enabled_crc: "
                     "{4}".format(endpoint, is_cname, connect_timeout, app_name, enable_crc))
        super(Bucket, self).__init__(auth, endpoint, is_cname, session, connect_timeout,
                                     app_name, enable_crc)

        self.bucket_name = bucket_name.strip()
        if utils.is_valid_bucket_name(self.bucket_name) is not True:
            raise ClientError("The bucket_name is invalid, please check it.")

    def sign_url(self, method, key, expires, headers=None, params=None, slash_safe=False):
        """生成签名URL。

        常见的用法是生成加签的URL以供授信用户下载，如为log.jpg生成一个5分钟后过期的下载链接::

            >>> bucket.sign_url('GET', 'log.jpg', 5 * 60)
            r'http://your-bucket.oss-cn-hangzhou.aliyuncs.com/logo.jpg?OSSAccessKeyId=YourAccessKeyId\&Expires=1447178011&Signature=UJfeJgvcypWq6Q%2Bm3IJcSHbvSak%3D'

        :param method: HTTP方法，如'GET'、'PUT'、'DELETE'等
        :type method: str
        :param key: 文件名
        :param expires: 过期时间（单位：秒），链接在当前时间再过expires秒后过期

        :param headers: 需要签名的HTTP头部，如名称以x-oss-meta-开头的头部（作为用户自定义元数据）、
            Content-Type头部等。对于下载，不需要填。
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :param params: 需要签名的HTTP查询参数

        :param slash_safe: 是否开启key名称中的‘/’转义保护，如果不开启'/'将会转义成%2F
        :type slash_safe: bool

        :return: 签名URL。
        """
        key = to_string(key)
        logger.debug(
            "Start to sign_url, method: {0}, bucket: {1}, key: {2}, expires: {3}, headers: {4}, params: {5}, slash_safe: {6}".format(
                method, self.bucket_name, to_string(key), expires, headers, params, slash_safe))
        req = http.Request(method, self._make_url(self.bucket_name, key, slash_safe),
                           headers=headers,
                           params=params)
        return self.auth._sign_url(req, self.bucket_name, key, expires)

    def sign_rtmp_url(self, channel_name, playlist_name, expires):
        """生成RTMP推流的签名URL。
        常见的用法是生成加签的URL以供授信用户向OSS推RTMP流。

        :param channel_name: 直播频道的名称
        :param expires: 过期时间（单位：秒），链接在当前时间再过expires秒后过期
        :param playlist_name: 播放列表名称，注意与创建live channel时一致
        :param params: 需要签名的HTTP查询参数

        :return: 签名URL。
        """
        logger.debug("Sign RTMP url, bucket: {0}, channel_name: {1}, playlist_name: {2}, expires: {3}".format(
            self.bucket_name, channel_name, playlist_name, expires))
        url = self._make_url(self.bucket_name, 'live').replace('http://', 'rtmp://').replace(
            'https://', 'rtmp://') + '/' + channel_name
        params = {}
        if playlist_name is not None and playlist_name != "":
            params['playlistName'] = playlist_name
        return self.auth._sign_rtmp_url(url, self.bucket_name, channel_name, expires, params)

    def list_objects(self, prefix='', delimiter='', marker='', max_keys=100, headers=None):
        """根据前缀罗列Bucket里的文件。

        :param str prefix: 只罗列文件名为该前缀的文件
        :param str delimiter: 分隔符。可以用来模拟目录
        :param str marker: 分页标志。首次调用传空串，后续使用返回值的next_marker
        :param int max_keys: 最多返回文件的个数，文件和目录的和不能超过该值

        :param headers: HTTP头部
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :return: :class:`ListObjectsResult <oss2.models.ListObjectsResult>`
        """
        headers = http.CaseInsensitiveDict(headers)
        logger.debug(
            "Start to List objects, bucket: {0}, prefix: {1}, delimiter: {2}, marker: {3}, max-keys: {4}".format(
                self.bucket_name, to_string(prefix), delimiter, to_string(marker), max_keys))
        resp = self.__do_object('GET', '',
                                params={'prefix': prefix,
                                        'delimiter': delimiter,
                                        'marker': marker,
                                        'max-keys': str(max_keys),
                                        'encoding-type': 'url'}, 
                                        headers=headers)
        logger.debug("List objects done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return self._parse_result(resp, xml_utils.parse_list_objects, ListObjectsResult)

    def put_object(self, key, data,
                   headers=None,
                   progress_callback=None):
        """上传一个普通文件。

        用法 ::
            >>> bucket.put_object('readme.txt', 'content of readme.txt')
            >>> with open(u'local_file.txt', 'rb') as f:
            >>>     bucket.put_object('remote_file.txt', f)

        :param key: 上传到OSS的文件名

        :param data: 待上传的内容。
        :type data: bytes，str或file-like object

        :param headers: 用户指定的HTTP头部。可以指定Content-Type、Content-MD5、x-oss-meta-开头的头部等
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :param progress_callback: 用户指定的进度回调函数。可以用来实现进度条等功能。参考 :ref:`progress_callback` 。

        :return: :class:`PutObjectResult <oss2.models.PutObjectResult>`
        """
        headers = utils.set_content_type(http.CaseInsensitiveDict(headers), key)

        if progress_callback:
            data = utils.make_progress_adapter(data, progress_callback)

        if self.enable_crc:
            data = utils.make_crc_adapter(data)

        logger.debug("Start to put object, bucket: {0}, key: {1}, headers: {2}".format(self.bucket_name, to_string(key),
                                                                                       headers))
        resp = self.__do_object('PUT', key, data=data, headers=headers)
        logger.debug("Put object done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        result = PutObjectResult(resp)

        if self.enable_crc and result.crc is not None:
            utils.check_crc('put object', data.crc, result.crc, result.request_id)

        return result

    def put_object_from_file(self, key, filename,
                             headers=None,
                             progress_callback=None):
        """上传一个本地文件到OSS的普通文件。

        :param str key: 上传到OSS的文件名
        :param str filename: 本地文件名，需要有可读权限

        :param headers: 用户指定的HTTP头部。可以指定Content-Type、Content-MD5、x-oss-meta-开头的头部等
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :param progress_callback: 用户指定的进度回调函数。参考 :ref:`progress_callback`

        :return: :class:`PutObjectResult <oss2.models.PutObjectResult>`
        """
        headers = utils.set_content_type(http.CaseInsensitiveDict(headers), filename)
        logger.debug("Put object from file, bucket: {0}, key: {1}, file path: {2}".format(
            self.bucket_name, to_string(key), filename))
        with open(to_unicode(filename), 'rb') as f:
            return self.put_object(key, f, headers=headers, progress_callback=progress_callback)

    def put_object_with_url(self, sign_url, data, headers=None, progress_callback=None):

        """ 使用加签的url上传对象

        :param sign_url: 加签的url
        :param data: 待上传的数据
        :param headers: 用户指定的HTTP头部。可以指定Content-Type、Content-MD5、x-oss-meta-开头的头部等，必须和签名时保持一致
        :param progress_callback: 用户指定的进度回调函数。参考 :ref:`progress_callback`
        :return:
        """
        headers = http.CaseInsensitiveDict(headers)

        if progress_callback:
            data = utils.make_progress_adapter(data, progress_callback)

        if self.enable_crc:
            data = utils.make_crc_adapter(data)

        logger.debug("Start to put object with signed url, bucket: {0}, sign_url: {1}, headers: {2}".format(
            self.bucket_name, sign_url, headers))

        resp = self._do_url('PUT', sign_url, data=data, headers=headers)
        logger.debug("Put object with url done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        result = PutObjectResult(resp)

        if self.enable_crc and result.crc is not None:
            utils.check_crc('put object', data.crc, result.crc, result.request_id)

        return result

    def put_object_with_url_from_file(self, sign_url, filename,
                                      headers=None,
                                      progress_callback=None):
        """ 使用加签的url上传本地文件到oss

        :param sign_url: 加签的url
        :param filename: 本地文件路径
        :param headers: 用户指定的HTTP头部。可以指定Content-Type、Content-MD5、x-oss-meta-开头的头部等，必须和签名时保持一致
        :param progress_callback: 用户指定的进度回调函数。参考 :ref:`progress_callback`
        :return:
        """
        logger.debug("Put object from file with signed url, bucket: {0}, sign_url: {1}, file path: {2}".format(
            self.bucket_name, sign_url, filename))
        with open(to_unicode(filename), 'rb') as f:
            return self.put_object_with_url(sign_url, f, headers=headers, progress_callback=progress_callback)

    def append_object(self, key, position, data,
                      headers=None,
                      progress_callback=None,
                      init_crc=None):
        """追加上传一个文件。

        :param str key: 新的文件名，或已经存在的可追加文件名
        :param int position: 追加上传一个新的文件， `position` 设为0；追加一个已经存在的可追加文件， `position` 设为文件的当前长度。
            `position` 可以从上次追加的结果 `AppendObjectResult.next_position` 中获得。

        :param data: 用户数据
        :type data: str、bytes、file-like object或可迭代对象

        :param headers: 用户指定的HTTP头部。可以指定Content-Type、Content-MD5、x-oss-开头的头部等
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :param progress_callback: 用户指定的进度回调函数。参考 :ref:`progress_callback`

        :return: :class:`AppendObjectResult <oss2.models.AppendObjectResult>`

        :raises: 如果 `position` 和当前文件长度不一致，抛出 :class:`PositionNotEqualToLength <oss2.exceptions.PositionNotEqualToLength>` ；
                 如果当前文件不是可追加类型，抛出 :class:`ObjectNotAppendable <oss2.exceptions.ObjectNotAppendable>` ；
                 还会抛出其他一些异常
        """
        headers = utils.set_content_type(http.CaseInsensitiveDict(headers), key)

        if progress_callback:
            data = utils.make_progress_adapter(data, progress_callback)

        if self.enable_crc and init_crc is not None:
            data = utils.make_crc_adapter(data, init_crc)

        logger.debug("Start to append object, bucket: {0}, key: {1}, headers: {2}, position: {3}".format(
            self.bucket_name, to_string(key), headers, position))
        resp = self.__do_object('POST', key,
                                data=data,
                                headers=headers,
                                params={'append': '', 'position': str(position)})
        logger.debug("Append object done, req_id: {0}, statu_code: {1}".format(resp.request_id, resp.status))
        result = AppendObjectResult(resp)

        if self.enable_crc and result.crc is not None and init_crc is not None:
            utils.check_crc('append object', data.crc, result.crc, result.request_id)

        return result

    def get_object(self, key,
                   byte_range=None,
                   headers=None,
                   progress_callback=None,
                   process=None,
                   params=None):
        """下载一个文件。

        用法 ::

            >>> result = bucket.get_object('readme.txt')
            >>> print(result.read())
            'hello world'

        :param key: 文件名
        :param byte_range: 指定下载范围。参见 :ref:`byte_range`

        :param headers: HTTP头部
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :param progress_callback: 用户指定的进度回调函数。参考 :ref:`progress_callback`

        :param process: oss文件处理，如图像服务等。指定后process，返回的内容为处理后的文件。

        :param params: http 请求的查询字符串参数
        :type params: dict

        :return: file-like object

        :raises: 如果文件不存在，则抛出 :class:`NoSuchKey <oss2.exceptions.NoSuchKey>` ；还可能抛出其他异常
        """
        headers = http.CaseInsensitiveDict(headers)

        range_string = _make_range_string(byte_range)
        if range_string:
            headers['range'] = range_string

        params = {} if params is None else params
        if process:
            params.update({Bucket.PROCESS: process})

        logger.debug("Start to get object, bucket: {0}， key: {1}, range: {2}, headers: {3}, params: {4}".format(
            self.bucket_name, to_string(key), range_string, headers, params))
        resp = self.__do_object('GET', key, headers=headers, params=params)
        logger.debug("Get object done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))

        return GetObjectResult(resp, progress_callback, self.enable_crc)

    def select_object(self, key, sql,
                   progress_callback=None,
                   select_params=None,
                   byte_range=None,
                   headers=None
                   ):
        """Select一个文件内容，支持(Csv,Json Doc,Json Lines及其GZIP压缩文件).

        用法 ::
        对于Csv:
            >>> result = bucket.select_object('access.log', 'select * from ossobject where _4 > 40')
            >>> print(result.read())
            'hello world'
        对于Json Doc: { contacts:[{"firstName":"abc", "lastName":"def"},{"firstName":"abc1", "lastName":"def1"}]}
            >>> result = bucket.select_object('sample.json', 'select s.firstName, s.lastName from ossobject.contacts[*] s', select_params = {"Json_Type":"DOCUMENT"})
        
        对于Json Lines: {"firstName":"abc", "lastName":"def"},{"firstName":"abc1", "lastName":"def1"}
            >>> result = bucket.select_object('sample.json', 'select s.firstName, s.lastName from ossobject s', select_params = {"Json_Type":"LINES"})

        :param key: 文件名
        :param sql: sql statement
        :param select_params: select参数集合,对于Json文件必须制定Json_Type类型。参见 :ref:`select_params`

        :param progress_callback: 用户指定的进度回调函数。参考 :ref:`progress_callback`
        :param byte_range: select content of specific range。可以设置Bytes header指定select csv时的文件起始offset和长度。
        
        :param headers: HTTP头部
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :return: file-like object

        :raises: 如果文件不存在，则抛出 :class:`NoSuchKey <oss2.exceptions.NoSuchKey>` ；还可能抛出其他异常
        """
        range_select = False
        headers = http.CaseInsensitiveDict(headers)
        range_string = _make_range_string(byte_range)
        if range_string:
            headers['range'] = range_string
            range_select = True

        if (range_select == True and 
                (select_params is None or 
                        (SelectParameters.AllowQuotedRecordDelimiter not in select_params or str(select_params[SelectParameters.AllowQuotedRecordDelimiter]).lower() != 'false'))):
                        raise ClientError('"AllowQuotedRecordDelimiter" must be specified in select_params as False when "Range" is specified in header.')

        body = xml_utils.to_select_object(sql, select_params)
        params = {'x-oss-process':  'csv/select'}
        if select_params is not None and SelectParameters.Json_Type in select_params:
            params['x-oss-process'] = 'json/select'

        self.timeout = 3600
        resp = self.__do_object('POST', key, data=body, headers=headers, params=params)
        crc_enabled = False
        if select_params is not None and SelectParameters.EnablePayloadCrc in select_params:
            if str(select_params[SelectParameters.EnablePayloadCrc]).lower() == "true":
                crc_enabled = True
        return SelectObjectResult(resp, progress_callback, crc_enabled)

    def get_object_to_file(self, key, filename,
                           byte_range=None,
                           headers=None,
                           progress_callback=None,
                           process=None,
                           params=None):
        """下载一个文件到本地文件。

        :param key: 文件名
        :param filename: 本地文件名。要求父目录已经存在，且有写权限。
        :param byte_range: 指定下载范围。参见 :ref:`byte_range`

        :param headers: HTTP头部
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :param progress_callback: 用户指定的进度回调函数。参考 :ref:`progress_callback`

        :param process: oss文件处理，如图像服务等。指定后process，返回的内容为处理后的文件。

        :param params: http 请求的查询字符串参数
        :type params: dict

        :return: 如果文件不存在，则抛出 :class:`NoSuchKey <oss2.exceptions.NoSuchKey>` ；还可能抛出其他异常
        """
        logger.debug("Start to get object to file, bucket: {0}, key: {1}, file path: {2}".format(
            self.bucket_name, to_string(key), filename))
        with open(to_unicode(filename), 'wb') as f:
            result = self.get_object(key, byte_range=byte_range, headers=headers, progress_callback=progress_callback,
                                     process=process, params=params)

            if result.content_length is None:
                shutil.copyfileobj(result, f)
            else:
                utils.copyfileobj_and_verify(result, f, result.content_length, request_id=result.request_id)

            if self.enable_crc and byte_range is None:
                if (headers is None) or ('Accept-Encoding' not in headers) or (headers['Accept-Encoding'] != 'gzip'):
                    utils.check_crc('get', result.client_crc, result.server_crc, result.request_id)

            return result

    def get_object_with_url(self, sign_url,
                            byte_range=None,
                            headers=None,
                            progress_callback=None):
        """使用加签的url下载文件

        :param sign_url: 加签的url
        :param byte_range: 指定下载范围。参见 :ref:`byte_range`

        :param headers: HTTP头部
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict，必须和签名时保持一致

        :param progress_callback: 用户指定的进度回调函数。参考 :ref:`progress_callback`

        :return: file-like object

        :raises: 如果文件不存在，则抛出 :class:`NoSuchKey <oss2.exceptions.NoSuchKey>` ；还可能抛出其他异常
        """
        headers = http.CaseInsensitiveDict(headers)

        range_string = _make_range_string(byte_range)
        if range_string:
            headers['range'] = range_string

        logger.debug("Start to get object with url, bucket: {0}, sign_url: {1}, range: {2}, headers: {3}".format(
            self.bucket_name, sign_url, range_string, headers))
        resp = self._do_url('GET', sign_url, headers=headers)
        return GetObjectResult(resp, progress_callback, self.enable_crc)

    def get_object_with_url_to_file(self, sign_url,
                                    filename,
                                    byte_range=None,
                                    headers=None,
                                    progress_callback=None):
        """使用加签的url下载文件

        :param sign_url: 加签的url
        :param filename: 本地文件名。要求父目录已经存在，且有写权限。
        :param byte_range: 指定下载范围。参见 :ref:`byte_range`

        :param headers: HTTP头部
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict，，必须和签名时保持一致

        :param progress_callback: 用户指定的进度回调函数。参考 :ref:`progress_callback`

        :return: file-like object

        :raises: 如果文件不存在，则抛出 :class:`NoSuchKey <oss2.exceptions.NoSuchKey>` ；还可能抛出其他异常
        """
        logger.debug(
            "Start to get object with url, bucket: {0}, sign_url: {1}, file path: {2}, range: {3}, headers: {4}"
            .format(self.bucket_name, sign_url, filename, byte_range, headers))

        with open(to_unicode(filename), 'wb') as f:
            result = self.get_object_with_url(sign_url, byte_range=byte_range, headers=headers,
                                              progress_callback=progress_callback)
            if result.content_length is None:
                shutil.copyfileobj(result, f)
            else:
                utils.copyfileobj_and_verify(result, f, result.content_length, request_id=result.request_id)

            return result

    def select_object_to_file(self, key, filename, sql,
                   progress_callback=None,
                   select_params=None,
                   headers=None
                   ):
        """Select一个文件的内容到本地文件

        :param key: OSS文件名
        :param filename: 本地文件名。其父亲目录已经存在且有写权限。

        :param progress_callback: 调用进度的callback。参考 :ref:`progress_callback`
        :param select_params: select参数集合。参见 :ref:`select_params`

        :param headers: HTTP头部
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :return: 如果文件不存在, 抛出 :class:`NoSuchKey <oss2.exceptions.NoSuchKey>`
        """
        with open(to_unicode(filename), 'wb') as f:
            result = self.select_object(key, sql, progress_callback=progress_callback,
                                        select_params=select_params, headers=headers)

            for chunk in result:
                f.write(chunk)

            return result

    def head_object(self, key, headers=None, params=None):
        """获取文件元信息。

        HTTP响应的头部包含了文件元信息，可以通过 `RequestResult` 的 `headers` 成员获得。
        用法 ::

            >>> result = bucket.head_object('readme.txt')
            >>> print(result.content_type)
            text/plain

        :param key: 文件名

        :param headers: HTTP头部
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :param params: HTTP请求参数，传入versionId，获取指定版本Object元信息
        :type params: 可以是dict，建议是oss2.CaseInsensitiveDict

        :return: :class:`HeadObjectResult <oss2.models.HeadObjectResult>`

        :raises: 如果Bucket不存在或者Object不存在，则抛出 :class:`NotFound <oss2.exceptions.NotFound>`
        """
        logger.debug("Start to head object, bucket: {0}, key: {1}, headers: {2}".format(
            self.bucket_name, to_string(key), headers))

        resp = self.__do_object('HEAD', key, headers=headers, params=params)

        logger.debug("Head object done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return HeadObjectResult(resp)

    def create_select_object_meta(self, key, select_meta_params=None, headers=None):
        """获取或创建CSV,JSON LINES 文件元信息。如果元信息存在，返回之；不然则创建后返回之

        HTTP响应的头部包含了文件元信息，可以通过 `RequestResult` 的 `headers` 成员获得。
        CSV文件用法 ::

            >>> select_meta_params = {  'FieldDelimiter': ',',
                                'RecordDelimiter': '\r\n',
                                'QuoteCharacter': '"',
                                'OverwriteIfExists' : 'false'}
            >>> result = bucket.create_select_object_meta('csv.txt', select_meta_params)
            >>> print(result.rows)
           
        JSON LINES文件用法 ::
            >>> select_meta_params = { 'Json_Type':'LINES', 'OverwriteIfExists':'False'}
            >>> result = bucket.create_select_object_meta('jsonlines.json', select_meta_params)
        :param key: 文件名
        :param select_meta_params: 参数词典，可以是dict，参见ref:`csv_meta_params`

        :param headers: HTTP头部
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :return: :class:`GetSelectObjectMetaResult <oss2.models.HeadObjectResult>`. 
          除了 rows 和splits 属性之外, 它也返回head object返回的其他属性。
          rows表示该文件的总记录数。
          splits表示该文件的总Split个数，一个Split包含若干条记录，每个Split的总字节数大致相当。用户可以以Split为单位进行分片查询。

        :raises: 如果Bucket不存在或者Object不存在，则抛出:class:`NotFound <oss2.exceptions.NotFound>`
        """
        headers = http.CaseInsensitiveDict(headers)

        body = xml_utils.to_get_select_object_meta(select_meta_params)
        params = {'x-oss-process':  'csv/meta'}
        if select_meta_params is not None and 'Json_Type' in select_meta_params:
            params['x-oss-process'] = 'json/meta'

        self.timeout = 3600
        resp = self.__do_object('POST', key, data=body, headers=headers, params=params)
        return GetSelectObjectMetaResult(resp)

    def get_object_meta(self, key, params=None, headers=None):
        """获取文件基本元信息，包括该Object的ETag、Size（文件大小）、LastModified，并不返回其内容。

        HTTP响应的头部包含了文件基本元信息，可以通过 `GetObjectMetaResult` 的 `last_modified`，`content_length`,`etag` 成员获得。

        :param key: 文件名
        :param dict params: 请求参数

        :param headers: HTTP头部
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :return: :class:`GetObjectMetaResult <oss2.models.GetObjectMetaResult>`

        :raises: 如果文件不存在，则抛出 :class:`NoSuchKey <oss2.exceptions.NoSuchKey>` ；还可能抛出其他异常
        """
        headers = http.CaseInsensitiveDict(headers)
        logger.debug("Start to get object metadata, bucket: {0}, key: {1}".format(self.bucket_name, to_string(key)))

        if params is None:
            params = dict()

        if Bucket.OBJECTMETA not in params:
            params[Bucket.OBJECTMETA] = ''

        resp = self.__do_object('GET', key, params=params, headers=headers)
        logger.debug("Get object metadata done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return GetObjectMetaResult(resp)

    def object_exists(self, key, headers=None):
        """如果文件存在就返回True，否则返回False。如果Bucket不存在，或是发生其他错误，则抛出异常。"""
        #:param key: 文件名

        #:param headers: HTTP头部
        #:type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        # 如果我们用head_object来实现的话，由于HTTP HEAD请求没有响应体，只有响应头部，这样当发生404时，
        # 我们无法区分是NoSuchBucket还是NoSuchKey错误。
        #
        # 2.2.0之前的实现是通过get_object的if-modified-since头部，把date设为当前时间24小时后，这样如果文件存在，则会返回
        # 304 (NotModified)；不存在，则会返回NoSuchKey。get_object会受回源的影响，如果配置会404回源，get_object会判断错误。
        #
        # 目前的实现是通过get_object_meta判断文件是否存在。

        headers = http.CaseInsensitiveDict(headers)
        logger.debug("Start to check if object exists, bucket: {0}, key: {1}".format(self.bucket_name, to_string(key)))
        try:
            self.get_object_meta(key, headers=headers)
        except exceptions.NoSuchKey:
            return False
        except:
            raise

        return True

    def copy_object(self, source_bucket_name, source_key, target_key, headers=None, params=None):
        """拷贝一个文件到当前Bucket。

        :param str source_bucket_name: 源Bucket名
        :param str source_key: 源文件名
        :param str target_key: 目标文件名
        :param dict params: 请求参数

        :param headers: HTTP头部
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :return: :class:`PutObjectResult <oss2.models.PutObjectResult>`
        """

        headers = http.CaseInsensitiveDict(headers)

        if params and Bucket.VERSIONID in params:
            headers[OSS_COPY_OBJECT_SOURCE] = '/' + source_bucket_name + \
                '/' + urlquote(source_key, '') + '?versionId=' + params[Bucket.VERSIONID]
        else:
            headers[OSS_COPY_OBJECT_SOURCE] = '/' + source_bucket_name + '/' + urlquote(source_key, '')

        logger.debug(
            "Start to copy object, source bucket: {0}, source key: {1}, bucket: {2}, key: {3}, headers: {4}".format(
                source_bucket_name, to_string(source_key), self.bucket_name, to_string(target_key), headers))
        resp = self.__do_object('PUT', target_key, headers=headers)
        logger.debug("Copy object done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))

        return PutObjectResult(resp)

    def update_object_meta(self, key, headers):
        """更改Object的元数据信息，包括Content-Type这类标准的HTTP头部，以及以x-oss-meta-开头的自定义元数据。

        用户可以通过 :func:`head_object` 获得元数据信息。

        :param str key: 文件名

        :param headers: HTTP头部，包含了元数据信息
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :return: :class:`RequestResult <oss2.models.RequestResults>`
        """
        logger.debug("Start to update object metadata, bucket: {0}, key: {1}".format(self.bucket_name, to_string(key)))
        return self.copy_object(self.bucket_name, key, key, headers=headers)

    def delete_object(self, key, params=None, headers=None):
        """删除一个文件。

        :param str key: 文件名
        :param params: 请求参数

        :param headers: HTTP头部
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :return: :class:`RequestResult <oss2.models.RequestResult>`
        """
        
        headers = http.CaseInsensitiveDict(headers)

        logger.info("Start to delete object, bucket: {0}, key: {1}".format(self.bucket_name, to_string(key)))
        resp = self.__do_object('DELETE', key, params=params, headers=headers)
        logger.debug("Delete object done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return RequestResult(resp)

    def restore_object(self, key, params=None, headers=None):
        """restore an object
            如果是第一次针对该object调用接口，返回RequestResult.status = 202；
            如果已经成功调用过restore接口，且服务端仍处于解冻中，抛异常RestoreAlreadyInProgress(status=409)
            如果已经成功调用过restore接口，且服务端解冻已经完成，再次调用时返回RequestResult.status = 200，且会将object的可下载时间延长一天，最多延长7天。
            如果object不存在，则抛异常NoSuchKey(status=404)；
            对非Archive类型的Object提交restore，则抛异常OperationNotSupported(status=400)

            也可以通过调用head_object接口来获取meta信息来判断是否可以restore与restore的状态
            代码示例::
            >>> meta = bucket.head_object(key)
            >>> if meta.resp.headers['x-oss-storage-class'] == oss2.BUCKET_STORAGE_CLASS_ARCHIVE:
            >>>     bucket.restore_object(key)
            >>>         while True:
            >>>             meta = bucket.head_object(key)
            >>>             if meta.resp.headers['x-oss-restore'] == 'ongoing-request="true"':
            >>>                 time.sleep(5)
            >>>             else:
            >>>                 break
        :param str key: object name
        :param params: 请求参数

        :param headers: HTTP头部
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :return: :class:`RequestResult <oss2.models.RequestResult>`
        """
        headers = http.CaseInsensitiveDict(headers)
        logger.debug("Start to restore object, bucket: {0}, key: {1}".format(self.bucket_name, to_string(key)))

        if params is None:
            params = dict()
        
        if Bucket.RESTORE not in params:
            params[Bucket.RESTORE] = ''

        resp = self.__do_object('POST', key, params=params, headers=headers)
        logger.debug("Restore object done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return RequestResult(resp)

    def put_object_acl(self, key, permission, params=None, headers=None):
        """设置文件的ACL。

        :param str key: 文件名
        :param str permission: 可以是oss2.OBJECT_ACL_DEFAULT、oss2.OBJECT_ACL_PRIVATE、oss2.OBJECT_ACL_PUBLIC_READ或
            oss2.OBJECT_ACL_PUBLIC_READ_WRITE。
        :param dict params: 请求参数

        :param headers: HTTP头部
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :return: :class:`RequestResult <oss2.models.RequestResult>`
        """
        logger.debug("Start to put object acl, bucket: {0}, key: {1}, acl: {2}".format(
            self.bucket_name, to_string(key), permission))

        headers = http.CaseInsensitiveDict(headers)
        headers[OSS_OBJECT_ACL] = permission

        if params is None:
            params = dict()

        if Bucket.ACL not in params:
            params[Bucket.ACL] = ''

        resp = self.__do_object('PUT', key, params=params, headers=headers)
        logger.debug("Put object acl done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return RequestResult(resp)

    def get_object_acl(self, key, params=None, headers=None):
        """获取文件的ACL。

        :param key: 文件名
        :param params: 请求参数

        :param headers: HTTP头部
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :return: :class:`GetObjectAclResult <oss2.models.GetObjectAclResult>`
        """
        logger.debug("Start to get object acl, bucket: {0}, key: {1}".format(self.bucket_name, to_string(key)))
        headers = http.CaseInsensitiveDict(headers)

        if params is None:
            params = dict()

        if Bucket.ACL not in params:
            params[Bucket.ACL] = ''

        resp = self.__do_object('GET', key, params=params, headers=headers)
        logger.debug("Get object acl done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return self._parse_result(resp, xml_utils.parse_get_object_acl, GetObjectAclResult)

    def batch_delete_objects(self, key_list, headers=None):
        """批量删除文件。待删除文件列表不能为空。

        :param key_list: 文件名列表，不能为空。
        :type key_list: list of str

        :param headers: HTTP头部

        :return: :class:`BatchDeleteObjectsResult <oss2.models.BatchDeleteObjectsResult>`
        """
        if not key_list:
            raise ClientError('key_list should not be empty')

        logger.debug("Start to delete objects, bucket: {0}, keys: {1}".format(self.bucket_name, key_list))
        
        data = xml_utils.to_batch_delete_objects_request(key_list, False)

        headers = http.CaseInsensitiveDict(headers)
        headers['Content-MD5'] = utils.content_md5(data)

        resp = self.__do_object('POST', '',
                                data=data,
                                params={'delete': '', 'encoding-type': 'url'},
                                headers=headers)
        logger.debug("Delete objects done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return self._parse_result(resp, xml_utils.parse_batch_delete_objects, BatchDeleteObjectsResult)

    def delete_object_versions(self, keylist_versions, headers=None):
        """批量删除带版本文件。待删除文件列表不能为空。

        :param key_list_with_version: 带版本的文件名列表，不能为空。（如果传入，则不能为空）
        :type key_list: list of BatchDeleteObjectsList 

        :param headers: HTTP头部

        :return: :class:`BatchDeleteObjectsResult <oss2.models.BatchDeleteObjectsResult>`
        """
        if not keylist_versions:
            raise ClientError('keylist_versions should not be empty')

        logger.debug("Start to delete object versions, bucket: {0}".format(self.bucket_name))
        
        data = xml_utils.to_batch_delete_objects_version_request(keylist_versions, False)

        headers = http.CaseInsensitiveDict(headers)
        headers['Content-MD5'] = utils.content_md5(data)

        resp = self.__do_object('POST', '',
                                data=data,
                                params={'delete': '', 'encoding-type': 'url'},
                                headers=headers)
        logger.debug("Delete object versions done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return self._parse_result(resp, xml_utils.parse_batch_delete_objects, BatchDeleteObjectsResult)

    def init_multipart_upload(self, key, headers=None, params=None):
        """初始化分片上传。

        返回值中的 `upload_id` 以及Bucket名和Object名三元组唯一对应了此次分片上传事件。

        :param str key: 待上传的文件名

        :param headers: HTTP头部
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :return: :class:`InitMultipartUploadResult <oss2.models.InitMultipartUploadResult>`
        """
        headers = utils.set_content_type(http.CaseInsensitiveDict(headers), key)

        if params is None:
            tmp_params = dict()
        else:
            tmp_params = params.copy()

        tmp_params['uploads'] = ''
        logger.debug("Start to init multipart upload, bucket: {0}, keys: {1}, headers: {2}, params: {3}".format(
            self.bucket_name, to_string(key), headers, tmp_params))
        resp = self.__do_object('POST', key, params=tmp_params, headers=headers)
        logger.debug("Init multipart upload done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return self._parse_result(resp, xml_utils.parse_init_multipart_upload, InitMultipartUploadResult)

    def upload_part(self, key, upload_id, part_number, data, progress_callback=None, headers=None):
        """上传一个分片。

        :param str key: 待上传文件名，这个文件名要和 :func:`init_multipart_upload` 的文件名一致。
        :param str upload_id: 分片上传ID
        :param int part_number: 分片号，最小值是1.
        :param data: 待上传数据。
        :param progress_callback: 用户指定进度回调函数。可以用来实现进度条等功能。参考 :ref:`progress_callback` 。

        :param headers: 用户指定的HTTP头部。可以指定Content-MD5头部等
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :return: :class:`PutObjectResult <oss2.models.PutObjectResult>`
        """
        headers = http.CaseInsensitiveDict(headers)

        if progress_callback:
            data = utils.make_progress_adapter(data, progress_callback)

        if self.enable_crc:
            data = utils.make_crc_adapter(data)

        logger.debug(
            "Start to upload multipart, bucket: {0}, key: {1}, upload_id: {2}, part_number: {3}, headers: {4}".format(
                self.bucket_name, to_string(key), upload_id, part_number, headers))
        resp = self.__do_object('PUT', key,
                                params={'uploadId': upload_id, 'partNumber': str(part_number)},
                                headers=headers,
                                data=data)
        logger.debug("Upload multipart done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        result = PutObjectResult(resp)

        if self.enable_crc and result.crc is not None:
            utils.check_crc('upload part', data.crc, result.crc, result.request_id)

        return result

    def complete_multipart_upload(self, key, upload_id, parts, headers=None):
        """完成分片上传，创建文件。

        :param str key: 待上传的文件名，这个文件名要和 :func:`init_multipart_upload` 的文件名一致。
        :param str upload_id: 分片上传ID

        :param parts: PartInfo列表。PartInfo中的part_number和etag是必填项。其中的etag可以从 :func:`upload_part` 的返回值中得到。
        :type parts: list of `PartInfo <oss2.models.PartInfo>`

        :param headers: HTTP头部
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :return: :class:`PutObjectResult <oss2.models.PutObjectResult>`
        """
        headers = http.CaseInsensitiveDict(headers)
        parts = sorted(parts, key=lambda p: p.part_number);
        data = xml_utils.to_complete_upload_request(parts);

        logger.debug("Start to complete multipart upload, bucket: {0}, key: {1}, upload_id: {2}, parts: {3}".format(
            self.bucket_name, to_string(key), upload_id, data))

        resp = self.__do_object('POST', key,
                                params={'uploadId': upload_id},
                                data=data,
                                headers=headers)
        logger.debug(
            "Complete multipart upload done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))

        result = PutObjectResult(resp);

        if self.enable_crc:
            object_crc = utils.calc_obj_crc_from_parts(parts)
            utils.check_crc('resumable upload', object_crc, result.crc, result.request_id)

        return result

    def abort_multipart_upload(self, key, upload_id, headers=None):
        """取消分片上传。

        :param str key: 待上传的文件名，这个文件名要和 :func:`init_multipart_upload` 的文件名一致。
        :param str upload_id: 分片上传ID

        :param headers: HTTP头部
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :return: :class:`RequestResult <oss2.models.RequestResult>`
        """

        logger.debug("Start to abort multipart upload, bucket: {0}, key: {1}, upload_id: {2}".format(
            self.bucket_name, to_string(key), upload_id))

        headers = http.CaseInsensitiveDict(headers)

        resp = self.__do_object('DELETE', key,
                                params={'uploadId': upload_id}, headers=headers)
        logger.debug("Abort multipart done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return RequestResult(resp)

    def list_multipart_uploads(self,
                               prefix='',
                               delimiter='',
                               key_marker='',
                               upload_id_marker='',
                               max_uploads=1000, 
                               headers=None):
        """罗列正在进行中的分片上传。支持分页。

        :param str prefix: 只罗列匹配该前缀的文件的分片上传
        :param str delimiter: 目录分割符
        :param str key_marker: 文件名分页符。第一次调用可以不传，后续设为返回值中的 `next_key_marker`
        :param str upload_id_marker: 分片ID分页符。第一次调用可以不传，后续设为返回值中的 `next_upload_id_marker`
        :param int max_uploads: 一次罗列最多能够返回的条目数

        :param headers: HTTP头部
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :return: :class:`ListMultipartUploadsResult <oss2.models.ListMultipartUploadsResult>`
        """
        logger.debug("Start to list multipart uploads, bucket: {0}, prefix: {1}, delimiter: {2}, key_marker: {3}, "
                     "upload_id_marker: {4}, max_uploads: {5}".format(self.bucket_name, to_string(prefix), delimiter,
                                                                      to_string(key_marker), upload_id_marker,
                                                                      max_uploads))

        headers = http.CaseInsensitiveDict(headers)

        resp = self.__do_object('GET', '',
                                params={'uploads': '',
                                        'prefix': prefix,
                                        'delimiter': delimiter,
                                        'key-marker': key_marker,
                                        'upload-id-marker': upload_id_marker,
                                        'max-uploads': str(max_uploads),
                                        'encoding-type': 'url'},
                                        headers=headers)
        logger.debug("List multipart uploads done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return self._parse_result(resp, xml_utils.parse_list_multipart_uploads, ListMultipartUploadsResult)

    def upload_part_copy(self, source_bucket_name, source_key, byte_range,
                         target_key, target_upload_id, target_part_number,
                         headers=None, params=None):
        """分片拷贝。把一个已有文件的一部分或整体拷贝成目标文件的一个分片。
        :source_bucket_name: 源文件所在bucket的名称
        :source_key:源文件名称
        :param byte_range: 指定待拷贝内容在源文件里的范围。参见 :ref:`byte_range`
        :target_key: 目的文件的名称
        :target_upload_id: 目的文件的uploadid
        :target_part_number: 目的文件的分片号
        :param params: 请求参数

        :param headers: HTTP头部
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :return: :class:`PutObjectResult <oss2.models.PutObjectResult>`
        """
        headers = http.CaseInsensitiveDict(headers)

        if params and Bucket.VERSIONID in params:
            headers[OSS_COPY_OBJECT_SOURCE] = '/' + source_bucket_name + \
                '/' + urlquote(source_key, '') + '?versionId=' + params[Bucket.VERSIONID]
        else:
            headers[OSS_COPY_OBJECT_SOURCE] = '/' + source_bucket_name + '/' + urlquote(source_key, '')


        range_string = _make_range_string(byte_range)
        if range_string:
            headers[OSS_COPY_OBJECT_SOURCE_RANGE] = range_string

        logger.debug("Start to upload part copy, source bucket: {0}, source key: {1}, bucket: {2}, key: {3}, range"
                     ": {4}, upload id: {5}, part_number: {6}, headers: {7}".format(source_bucket_name,
                    to_string(source_key),self.bucket_name,to_string(target_key),
                    byte_range, target_upload_id,target_part_number, headers))

        if params is None:
            params = dict()

        params['uploadId'] = target_upload_id
        params['partNumber'] = str(target_part_number)

        resp = self.__do_object('PUT', target_key,
                                params=params,headers=headers)
        logger.debug("Upload part copy done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))

        return PutObjectResult(resp)

    def list_parts(self, key, upload_id,
                   marker='', max_parts=1000, headers=None):
        """列举已经上传的分片。支持分页。

        :param str key: 文件名
        :param str upload_id: 分片上传ID
        :param str marker: 分页符
        :param int max_parts: 一次最多罗列多少分片

        :param headers: HTTP头部
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :return: :class:`ListPartsResult <oss2.models.ListPartsResult>`
        """
        logger.debug("Start to list parts, bucket: {0}, key: {1}, upload_id: {2}, marker: {3}, max_parts: {4}".format(
            self.bucket_name, to_string(key), upload_id, marker, max_parts))

        headers = http.CaseInsensitiveDict(headers)

        resp = self.__do_object('GET', key,
                                params={'uploadId': upload_id,
                                        'part-number-marker': marker,
                                        'max-parts': str(max_parts)}, 
                                        headers=headers)
        logger.debug("List parts done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return self._parse_result(resp, xml_utils.parse_list_parts, ListPartsResult)

    def put_symlink(self, target_key, symlink_key, headers=None):
        """创建Symlink。

        :param str target_key: 目标文件，目标文件不能为符号连接
        :param str symlink_key: 符号连接类文件，其实质是一个特殊的文件，数据指向目标文件

        :param headers: HTTP头部
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :return: :class:`RequestResult <oss2.models.RequestResult>`
        """
        headers = http.CaseInsensitiveDict(headers)
        headers[OSS_SYMLINK_TARGET] = urlquote(target_key, '')

        logger.debug("Start to put symlink, bucket: {0}, target_key: {1}, symlink_key: {2}, headers: {3}".format(
            self.bucket_name, to_string(target_key), to_string(symlink_key), headers))
        resp = self.__do_object('PUT', symlink_key, headers=headers, params={Bucket.SYMLINK: ''})
        logger.debug("Put symlink done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return RequestResult(resp)

    def get_symlink(self, symlink_key, params=None, headers=None):
        """获取符号连接文件的目标文件。

        :param str symlink_key: 符号连接类文件
        :param dict params: 请求参数

        :param headers: HTTP头部
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :return: :class:`GetSymlinkResult <oss2.models.GetSymlinkResult>`

        :raises: 如果文件的符号链接不存在，则抛出 :class:`NoSuchKey <oss2.exceptions.NoSuchKey>` ；还可能抛出其他异常
        """
        logger.debug(
            "Start to get symlink, bucket: {0}, symlink_key: {1}".format(self.bucket_name, to_string(symlink_key)))

        headers = http.CaseInsensitiveDict(headers)

        if params is None:
            params = dict()

        if Bucket.SYMLINK not in params:
            params[Bucket.SYMLINK] = ''

        resp = self.__do_object('GET', symlink_key, params=params, headers=headers)
        logger.debug("Get symlink done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return GetSymlinkResult(resp)

    def create_bucket(self, permission=None, input=None):
        """创建新的Bucket。

        :param str permission: 指定Bucket的ACL。可以是oss2.BUCKET_ACL_PRIVATE（推荐、缺省）、oss2.BUCKET_ACL_PUBLIC_READ或是
            oss2.BUCKET_ACL_PUBLIC_READ_WRITE。

        :param input: :class:`BucketCreateConfig <oss2.models.BucketCreateConfig>` object
        """
        if permission:
            headers = {OSS_CANNED_ACL: permission}
        else:
            headers = None

        data = self.__convert_data(BucketCreateConfig, xml_utils.to_put_bucket_config, input)
        logger.debug("Start to create bucket, bucket: {0}, permission: {1}, config: {2}".format(self.bucket_name,
                                                                                                permission, data))
        resp = self.__do_bucket('PUT', headers=headers, data=data)
        logger.debug("Create bucket done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return RequestResult(resp)

    def delete_bucket(self):
        """删除一个Bucket。只有没有任何文件，也没有任何未完成的分片上传的Bucket才能被删除。

        :return: :class:`RequestResult <oss2.models.RequestResult>`

        ":raises: 如果试图删除一个非空Bucket，则抛出 :class:`BucketNotEmpty <oss2.exceptions.BucketNotEmpty>`
        """
        logger.info("Start to delete bucket, bucket: {0}".format(self.bucket_name))
        resp = self.__do_bucket('DELETE')
        logger.debug("Delete bucket done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return RequestResult(resp)

    def put_bucket_acl(self, permission):
        """设置Bucket的ACL。

        :param str permission: 新的ACL，可以是oss2.BUCKET_ACL_PRIVATE、oss2.BUCKET_ACL_PUBLIC_READ或
            oss2.BUCKET_ACL_PUBLIC_READ_WRITE
        """
        logger.debug("Start to put bucket acl, bucket: {0}, acl: {1}".format(self.bucket_name, permission))
        resp = self.__do_bucket('PUT', headers={OSS_CANNED_ACL: permission}, params={Bucket.ACL: ''})
        logger.debug("Put bucket acl done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return RequestResult(resp)

    def get_bucket_acl(self):
        """获取Bucket的ACL。

        :return: :class:`GetBucketAclResult <oss2.models.GetBucketAclResult>`
        """
        logger.debug("Start to get bucket acl, bucket: {0}".format(self.bucket_name))
        resp = self.__do_bucket('GET', params={Bucket.ACL: ''})
        logger.debug("Get bucket acl done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return self._parse_result(resp, xml_utils.parse_get_bucket_acl, GetBucketAclResult)

    def put_bucket_cors(self, input):
        """设置Bucket的CORS。

        :param input: :class:`BucketCors <oss2.models.BucketCors>` 对象或其他
        """
        data = self.__convert_data(BucketCors, xml_utils.to_put_bucket_cors, input)
        logger.debug("Start to put bucket cors, bucket: {0}, cors: {1}".format(self.bucket_name, data))
        resp = self.__do_bucket('PUT', data=data, params={Bucket.CORS: ''})
        logger.debug("Put bucket cors done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return RequestResult(resp)

    def get_bucket_cors(self):
        """获取Bucket的CORS配置。

        :return: :class:`GetBucketCorsResult <oss2.models.GetBucketCorsResult>`
        """
        logger.debug("Start to get bucket CORS, bucket: {0}".format(self.bucket_name))
        resp = self.__do_bucket('GET', params={Bucket.CORS: ''})
        logger.debug("Get bucket CORS done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return self._parse_result(resp, xml_utils.parse_get_bucket_cors, GetBucketCorsResult)

    def delete_bucket_cors(self):
        """删除Bucket的CORS配置。"""
        logger.debug("Start to delete bucket CORS, bucket: {0}".format(self.bucket_name))
        resp = self.__do_bucket('DELETE', params={Bucket.CORS: ''})
        logger.debug("Delete bucket CORS done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return RequestResult(resp)

    def put_bucket_lifecycle(self, input):
        """设置生命周期管理的配置。

        :param input: :class:`BucketLifecycle <oss2.models.BucketLifecycle>` 对象或其他
        """
        data = self.__convert_data(BucketLifecycle, xml_utils.to_put_bucket_lifecycle, input)
        logger.debug("Start to put bucket lifecycle, bucket: {0}, lifecycle: {1}".format(self.bucket_name, data))
        resp = self.__do_bucket('PUT', data=data, params={Bucket.LIFECYCLE: ''})
        logger.debug("Put bucket lifecycle done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return RequestResult(resp)

    def get_bucket_lifecycle(self):
        """获取生命周期管理配置。

        :return: :class:`GetBucketLifecycleResult <oss2.models.GetBucketLifecycleResult>`

        :raises: 如果没有设置Lifecycle，则抛出 :class:`NoSuchLifecycle <oss2.exceptions.NoSuchLifecycle>`
        """
        logger.debug("Start to get bucket lifecycle, bucket: {0}".format(self.bucket_name))
        resp = self.__do_bucket('GET', params={Bucket.LIFECYCLE: ''})
        logger.debug("Get bucket lifecycle done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return self._parse_result(resp, xml_utils.parse_get_bucket_lifecycle, GetBucketLifecycleResult)

    def delete_bucket_lifecycle(self):
        """删除生命周期管理配置。如果Lifecycle没有设置，也返回成功。"""
        logger.debug("Start to delete bucket lifecycle, bucket: {0}".format(self.bucket_name))
        resp = self.__do_bucket('DELETE', params={Bucket.LIFECYCLE: ''})
        logger.debug("Delete bucket lifecycle done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return RequestResult(resp)

    def get_bucket_location(self):
        """获取Bucket的数据中心。

        :return: :class:`GetBucketLocationResult <oss2.models.GetBucketLocationResult>`
        """
        logger.debug("Start to get bucket location, bucket: {0}".format(self.bucket_name))
        resp = self.__do_bucket('GET', params={Bucket.LOCATION: ''})
        logger.debug("Get bucket location done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return self._parse_result(resp, xml_utils.parse_get_bucket_location, GetBucketLocationResult)

    def put_bucket_logging(self, input):
        """设置Bucket的访问日志功能。

        :param input: :class:`BucketLogging <oss2.models.BucketLogging>` 对象或其他
        """
        data = self.__convert_data(BucketLogging, xml_utils.to_put_bucket_logging, input)
        logger.debug("Start to put bucket logging, bucket: {0}, logging: {1}".format(self.bucket_name, data))
        resp = self.__do_bucket('PUT', data=data, params={Bucket.LOGGING: ''})
        logger.debug("Put bucket logging done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return RequestResult(resp)

    def get_bucket_logging(self):
        """获取Bucket的访问日志功能配置。

        :return: :class:`GetBucketLoggingResult <oss2.models.GetBucketLoggingResult>`
        """
        logger.debug("Start to get bucket logging, bucket: {0}".format(self.bucket_name))
        resp = self.__do_bucket('GET', params={Bucket.LOGGING: ''})
        logger.debug("Get bucket logging done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return self._parse_result(resp, xml_utils.parse_get_bucket_logging, GetBucketLoggingResult)

    def delete_bucket_logging(self):
        """关闭Bucket的访问日志功能。"""
        logger.debug("Start to delete bucket loggging, bucket: {0}".format(self.bucket_name))
        resp = self.__do_bucket('DELETE', params={Bucket.LOGGING: ''})
        logger.debug("Put bucket lifecycle done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return RequestResult(resp)

    def put_bucket_referer(self, input):
        """为Bucket设置防盗链。

        :param input: :class:`BucketReferer <oss2.models.BucketReferer>` 对象或其他
        """
        data = self.__convert_data(BucketReferer, xml_utils.to_put_bucket_referer, input)
        logger.debug("Start to put bucket referer, bucket: {0}, referer: {1}".format(self.bucket_name, to_string(data)))
        resp = self.__do_bucket('PUT', data=data, params={Bucket.REFERER: ''})
        logger.debug("Put bucket referer done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return RequestResult(resp)

    def get_bucket_referer(self):
        """获取Bucket的防盗链配置。

        :return: :class:`GetBucketRefererResult <oss2.models.GetBucketRefererResult>`
        """
        logger.debug("Start to get bucket referer, bucket: {0}".format(self.bucket_name))
        resp = self.__do_bucket('GET', params={Bucket.REFERER: ''})
        logger.debug("Get bucket referer done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return self._parse_result(resp, xml_utils.parse_get_bucket_referer, GetBucketRefererResult)

    def get_bucket_stat(self):
        """查看Bucket的状态，目前包括bucket大小，bucket的object数量，bucket正在上传的Multipart Upload事件个数等。

        :return: :class:`GetBucketStatResult <oss2.models.GetBucketStatResult>`
        """
        logger.debug("Start to get bucket stat, bucket: {0}".format(self.bucket_name))
        resp = self.__do_bucket('GET', params={Bucket.STAT: ''})
        logger.debug("Get bucket stat done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return self._parse_result(resp, xml_utils.parse_get_bucket_stat, GetBucketStatResult)

    def get_bucket_info(self):
        """获取bucket相关信息，如创建时间，访问Endpoint，Owner与ACL等。

        :return: :class:`GetBucketInfoResult <oss2.models.GetBucketInfoResult>`
        """
        logger.debug("Start to get bucket info, bucket: {0}".format(self.bucket_name))
        resp = self.__do_bucket('GET', params={Bucket.BUCKET_INFO: ''})
        logger.debug("Get bucket info done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return self._parse_result(resp, xml_utils.parse_get_bucket_info, GetBucketInfoResult)

    def put_bucket_website(self, input):
        """为Bucket配置静态网站托管功能。

        :param input: :class:`BucketWebsite <oss2.models.BucketWebsite>`
        """
        data = self.__convert_data(BucketWebsite, xml_utils.to_put_bucket_website, input)

        headers = http.CaseInsensitiveDict()
        headers['Content-MD5'] = utils.content_md5(data)

        logger.debug("Start to put bucket website, bucket: {0}, website: {1}".format(self.bucket_name, to_string(data)))
        resp = self.__do_bucket('PUT', data=data, params={Bucket.WEBSITE: ''}, headers=headers)
        logger.debug("Put bucket website done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return RequestResult(resp)

    def get_bucket_website(self):
        """获取Bucket的静态网站托管配置。

        :return: :class:`GetBucketWebsiteResult <oss2.models.GetBucketWebsiteResult>`

        :raises: 如果没有设置静态网站托管，那么就抛出 :class:`NoSuchWebsite <oss2.exceptions.NoSuchWebsite>`
        """

        logger.debug("Start to get bucket website, bucket: {0}".format(self.bucket_name))
        resp = self.__do_bucket('GET', params={Bucket.WEBSITE: ''})
        logger.debug("Get bucket website done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))

        return self._parse_result(resp, xml_utils.parse_get_bucket_website, GetBucketWebsiteResult)

    def delete_bucket_website(self):
        """关闭Bucket的静态网站托管功能。"""
        logger.debug("Start to delete bucket website, bucket: {0}".format(self.bucket_name))
        resp = self.__do_bucket('DELETE', params={Bucket.WEBSITE: ''})
        logger.debug("Delete bucket website done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return RequestResult(resp)

    def create_live_channel(self, channel_name, input):
        """创建推流直播频道

        :param str channel_name: 要创建的live channel的名称
        :param input: LiveChannelInfo类型，包含了live channel中的描述信息

        :return: :class:`CreateLiveChannelResult <oss2.models.CreateLiveChannelResult>`
        """
        data = self.__convert_data(LiveChannelInfo, xml_utils.to_create_live_channel, input)
        logger.debug("Start to create live-channel, bucket: {0}, channel_name: {1}, info: {2}".format(
            self.bucket_name, to_string(channel_name), to_string(data)))
        resp = self.__do_object('PUT', channel_name, data=data, params={Bucket.LIVE: ''})
        logger.debug("Create live-channel done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return self._parse_result(resp, xml_utils.parse_create_live_channel, CreateLiveChannelResult)

    def delete_live_channel(self, channel_name):
        """删除推流直播频道

        :param str channel_name: 要删除的live channel的名称
        """
        logger.debug("Start to delete live-channel, bucket: {0}, live_channel: {1}".format(
            self.bucket_name, to_string(channel_name)))
        resp = self.__do_object('DELETE', channel_name, params={Bucket.LIVE: ''})
        logger.debug("Delete live-channel done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return RequestResult(resp)

    def get_live_channel(self, channel_name):
        """获取直播频道配置

        :param str channel_name: 要获取的live channel的名称

        :return: :class:`GetLiveChannelResult <oss2.models.GetLiveChannelResult>`
        """
        logger.debug("Start to get live-channel info: bucket: {0}, live_channel: {1}".format(
            self.bucket_name, to_string(channel_name)))
        resp = self.__do_object('GET', channel_name, params={Bucket.LIVE: ''})
        logger.debug("Get live-channel done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return self._parse_result(resp, xml_utils.parse_get_live_channel, GetLiveChannelResult)

    def list_live_channel(self, prefix='', marker='', max_keys=100):
        """列举出Bucket下所有符合条件的live channel

        param: str prefix: list时channel_id的公共前缀
        param: str marker: list时指定的起始标记
        param: int max_keys: 本次list返回live channel的最大个数

        return: :class:`ListLiveChannelResult <oss2.models.ListLiveChannelResult>`
        """
        logger.debug("Start to list live-channels, bucket: {0}, prefix: {1}, marker: {2}, max_keys: {3}".format(
            self.bucket_name, to_string(prefix), to_string(marker), max_keys))
        resp = self.__do_bucket('GET', params={Bucket.LIVE: '',
                                               'prefix': prefix,
                                               'marker': marker,
                                               'max-keys': str(max_keys)})
        logger.debug("List live-channel done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return self._parse_result(resp, xml_utils.parse_list_live_channel, ListLiveChannelResult)

    def get_live_channel_stat(self, channel_name):
        """获取live channel当前推流的状态

        param str channel_name: 要获取推流状态的live channel的名称

        return: :class:`GetLiveChannelStatResult <oss2.models.GetLiveChannelStatResult>`
        """
        logger.debug("Start to get live-channel stat, bucket: {0}, channel_name: {1}".format(
            self.bucket_name, to_string(channel_name)))
        resp = self.__do_object('GET', channel_name, params={Bucket.LIVE: '', Bucket.COMP: 'stat'})
        logger.debug("Get live-channel stat done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))

        return self._parse_result(resp, xml_utils.parse_live_channel_stat, GetLiveChannelStatResult)

    def put_live_channel_status(self, channel_name, status):
        """更改live channel的status，仅能在“enabled”和“disabled”两种状态中更改

        param str channel_name: 要更改status的live channel的名称
        param str status: live channel的目标status
        """
        logger.debug("Start to put live-channel status, bucket: {0}, channel_name: {1}, status: {2}".format(
            self.bucket_name, to_string(channel_name), status))
        resp = self.__do_object('PUT', channel_name, params={Bucket.LIVE: '', Bucket.STATUS: status})
        logger.debug("Put live-channel status done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return RequestResult(resp)

    def get_live_channel_history(self, channel_name):
        """获取live channel中最近的最多十次的推流记录，记录中包含推流的起止时间和远端的地址

        param str channel_name: 要获取最近推流记录的live channel的名称

        return: :class:`GetLiveChannelHistoryResult <oss2.models.GetLiveChannelHistoryResult>`
        """
        logger.debug("Start to get live-channel history, bucket: {0}, channel_name: {1}".format(
            self.bucket_name, to_string(channel_name)))
        resp = self.__do_object('GET', channel_name, params={Bucket.LIVE: '', Bucket.COMP: 'history'})
        logger.debug(
            "Get live-channel history done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return self._parse_result(resp, xml_utils.parse_live_channel_history, GetLiveChannelHistoryResult)

    def post_vod_playlist(self, channel_name, playlist_name, start_time=0, end_time=0):
        """根据指定的playlist name以及startTime和endTime生成一个点播的播放列表

        param str channel_name: 要生成点播列表的live channel的名称
        param str playlist_name: 要生成点播列表m3u8文件的名称
        param int start_time: 点播的起始时间，Unix Time格式，可以使用int(time.time())获取
        param int end_time: 点播的结束时间，Unix Time格式，可以使用int(time.time())获取
        """
        logger.debug("Start to post vod playlist, bucket: {0}, channel_name: {1}, playlist_name: {2}, start_time: "
                     "{3}, end_time: {4}".format(self.bucket_name, to_string(channel_name), playlist_name, start_time,
                                                 end_time))
        key = channel_name + "/" + playlist_name
        resp = self.__do_object('POST', key, params={Bucket.VOD: '', 'startTime': str(start_time),
                                                     'endTime': str(end_time)})
        logger.debug("Post vod playlist done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return RequestResult(resp)

    def get_vod_playlist(self, channel_name, start_time, end_time):
        """查看指定时间段内的播放列表

        param str channel_name: 要获取点播列表的live channel的名称
        param int start_time: 点播的起始时间，Unix Time格式，可以使用int(time.time())获取
        param int end_time: 点播的结束时间，Unix Time格式，可以使用int(time.time())获取
        """
        logger.debug("Start to get vod playlist, bucket: {0}, channel_name: {1},  start_time: "
                     "{2}, end_time: {3}".format(self.bucket_name, to_string(channel_name),  start_time, end_time))
        resp = self.__do_object('GET', channel_name, params={Bucket.VOD: '', 'startTime': str(start_time),
                                                     'endTime': str(end_time)})
        logger.debug("get vod playlist done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        result = GetVodPlaylistResult(resp)
        return result

    def process_object(self, key, process, headers=None):
        """处理图片的接口，支持包括调整大小，旋转，裁剪，水印，格式转换等，支持多种方式组合处理。

        :param str key: 处理的图片的对象名称
        :param str process: 处理的字符串，例如"image/resize,w_100|sys/saveas,o_dGVzdC5qcGc,b_dGVzdA"

        :param headers: HTTP头部
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict
        """

        headers = http.CaseInsensitiveDict(headers)

        logger.debug("Start to process object, bucket: {0}, key: {1}, process: {2}".format(
            self.bucket_name, to_string(key), process))
        process_data = "%s=%s" % (Bucket.PROCESS, process)
        resp = self.__do_object('POST', key, params={Bucket.PROCESS: ''}, headers=headers, data=process_data)
        logger.debug("Process object done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return ProcessObjectResult(resp)

    def put_object_tagging(self, key, tagging, headers=None, params=None):
        """

        :param str key: 上传tagging的对象名称，不能为空。

        :param tagging: tag 标签内容 
        :type tagging: :class:`Tagging <oss2.models.Tagging>` 对象

        :param headers: HTTP头部
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :param dict params: HTTP请求参数

        :return: :class:`RequestResult <oss2.models.RequestResult>`
        """
        logger.debug("Start to put object tagging, bucket: {0}, key: {1}, tagging: {2}".format(
            self.bucket_name, to_string(key), tagging))

        if headers is not None:
            headers = http.CaseInsensitiveDict(headers)

        if params is None:
            params = dict()

        params[Bucket.TAGGING] = ""

        data = self.__convert_data(Tagging, xml_utils.to_put_tagging, tagging) 
        resp = self.__do_object('PUT', key, data=data, params=params, headers=headers)

        return RequestResult(resp)

    def get_object_tagging(self, key, params=None, headers=None):

        """
        :param str key: 要获取tagging的对象名称
        :param dict params: 请求参数

        :param headers: HTTP头部
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :return: :class:`GetTaggingResult <oss2.models.GetTaggingResult>` 
        """
        logger.debug("Start to get object tagging, bucket: {0}, key: {1} params: {2}".format(
                    self.bucket_name, to_string(key), str(params)))
        
        headers = http.CaseInsensitiveDict(headers)

        if params is None:
            params = dict()

        params[Bucket.TAGGING] = ""

        resp = self.__do_object('GET', key, params=params, headers=headers)

        return self._parse_result(resp, xml_utils.parse_get_tagging, GetTaggingResult)

    def delete_object_tagging(self, key, params=None, headers=None):
        """
        :param str key: 要删除tagging的对象名称
        :param dict params: 请求参数

        :param headers: HTTP头部
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :return: :class:`RequestResult <oss2.models.RequestResult>` 
        """
        logger.debug("Start to delete object tagging, bucket: {0}, key: {1}".format(
                    self.bucket_name, to_string(key)))

        headers = http.CaseInsensitiveDict(headers)

        if params is None:
            params = dict()

        params[Bucket.TAGGING] = ""

        resp = self.__do_object('DELETE', key, params=params, headers=headers)

        logger.debug("Delete object tagging done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return RequestResult(resp)
    
    def put_bucket_encryption(self, rule):
        """设置bucket加密配置。

        :param rule: :class:` ServerSideEncryptionRule<oss2.models.ServerSideEncryptionRule>` 对象
        """
        data = self.__convert_data(ServerSideEncryptionRule, xml_utils.to_put_bucket_encryption, rule)

        logger.debug("Start to put bucket encryption, bucket: {0}, rule: {1}".format(self.bucket_name, data))
        resp = self.__do_bucket('PUT', data=data, params={Bucket.ENCRYPTION: ""})
        logger.debug("Put bucket encryption done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return RequestResult(resp)

    def get_bucket_encryption(self):
        """获取bucket加密配置。

        :return: :class:`GetServerSideEncryptionResult <oss2.models.GetServerSideEncryptionResult>`

        :raises: 如果没有设置Bucket encryption，则抛出 :class:`NoSuchServerSideEncryptionRule <oss2.exceptions.NoSuchServerSideEncryptionRule>`
        """
        logger.debug("Start to get bucket encryption, bucket: {0}".format(self.bucket_name))
        resp = self.__do_bucket('GET', params={Bucket.ENCRYPTION: ''})
        logger.debug("Get bucket encryption done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return self._parse_result(resp, xml_utils.parse_get_bucket_encryption, GetServerSideEncryptionResult)

    def delete_bucket_encryption(self):
        """删除Bucket加密配置。如果Bucket加密没有设置，也返回成功。"""
        logger.debug("Start to delete bucket encryption, bucket: {0}".format(self.bucket_name))
        resp = self.__do_bucket('DELETE', params={Bucket.ENCRYPTION: ''})
        logger.debug("Delete bucket encryption done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return RequestResult(resp)

    def put_bucket_tagging(self, tagging, headers=None):
        """

        :param str key: 上传tagging的对象名称，不能为空。

        :param tagging: tag 标签内容 
        :type tagging: :class:`Tagging <oss2.models.Tagging>` 对象

        :return: :class:`RequestResult <oss2.models.RequestResult>`
        """
        logger.debug("Start to put object tagging, bucket: {0} tagging: {1}".format(
            self.bucket_name, tagging))

        headers = http.CaseInsensitiveDict(headers)

        data = self.__convert_data(Tagging, xml_utils.to_put_tagging, tagging) 
        resp = self.__do_bucket('PUT', data=data, params={Bucket.TAGGING: ''}, headers=headers)

        logger.debug("Put bucket tagging done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return RequestResult(resp)

    def get_bucket_tagging(self):

        """
        :param str key: 要获取tagging的对象名称
        :param dict params: 请求参数
        :return: :class:`GetTaggingResult<oss2.models.GetTaggingResult>` 
        """
        logger.debug("Start to get bucket tagging, bucket: {0}".format(
                    self.bucket_name))
        
        resp = self.__do_bucket('GET', params={Bucket.TAGGING: ''})

        logger.debug("Get bucket tagging done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return self._parse_result(resp, xml_utils.parse_get_tagging, GetTaggingResult)

    def delete_bucket_tagging(self):
        """
        :return: :class:`RequestResult <oss2.models.RequestResult>` 
        """
        logger.debug("Start to delete bucket tagging, bucket: {0}".format(
                    self.bucket_name))

        resp = self.__do_bucket('DELETE', params={Bucket.TAGGING: ''})

        logger.debug("Delete bucket tagging done, req_id: {0}, status_code: {1}".format(
                    resp.request_id, resp.status))
        return RequestResult(resp)

    def list_object_versions(self, prefix='', delimiter='', key_marker='',
            max_keys=100, versionid_marker='', headers=None):
        """根据前缀罗列Bucket里的文件的版本。

        :param str prefix: 只罗列文件名为该前缀的文件
        :param str delimiter: 分隔符。可以用来模拟目录
        :param str key_marker: 分页标志。首次调用传空串，后续使用返回值的next_marker
        :param int max_keys: 最多返回文件的个数，文件和目录的和不能超过该值
        :param str versionid_marker: 设定结果从key-marker对象的
            versionid-marker之后按新旧版本排序开始返回，该版本不会在返回的结果当中。 

        :param headers: HTTP头部
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :return: :class:`ListObjectVersionsResult <oss2.models.ListObjectVersionsResult>`
        """
        logger.debug(
            "Start to List object versions, bucket: {0}, prefix: {1}, delimiter: {2},"
            +"key_marker: {3}, versionid_marker: {4}, max-keys: {5}".format(
            self.bucket_name, to_string(prefix), delimiter, to_string(key_marker),
            to_string(versionid_marker), max_keys))

        headers = http.CaseInsensitiveDict(headers)

        resp = self.__do_bucket('GET',
                                params={'prefix': prefix,
                                        'delimiter': delimiter,
                                        'key-marker': key_marker,
                                        'version-id-marker': versionid_marker,
                                        'max-keys': str(max_keys),
                                        'encoding-type': 'url',
                                        Bucket.VERSIONS: ''},
                                        headers=headers)
        logger.debug("List object versions done, req_id: {0}, status_code: {1}"
                .format(resp.request_id, resp.status))

        return self._parse_result(resp, xml_utils.parse_list_object_versions, ListObjectVersionsResult)

    def put_bucket_versioning(self, config, headers=None):
        """

        :param str operation: 设置bucket是否开启多版本特性，可取值为:[Enabled,Suspend] 

        :return: :class:`RequestResult <oss2.models.RequestResult>`
        """
        logger.debug("Start to put object versioning, bucket: {0}".format(self.bucket_name))
        data = self.__convert_data(BucketVersioningConfig, xml_utils.to_put_bucket_versioning, config) 

        headers = http.CaseInsensitiveDict(headers)
        headers['Content-MD5'] = utils.content_md5(data)

        resp = self.__do_bucket('PUT', data=data, params={Bucket.VERSIONING: ''}, headers=headers)
        logger.debug("Put bucket versiong done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))

        return RequestResult(resp)

    def get_bucket_versioning(self):
        """
        :return: :class:`GetBucketVersioningResult<oss2.models.GetBucketVersioningResult>` 
        """
        logger.debug("Start to get bucket versioning, bucket: {0}".format(self.bucket_name))
        resp = self.__do_bucket('GET', params={Bucket.VERSIONING: ''})
        logger.debug("Get bucket versiong done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))

        return self._parse_result(resp, xml_utils.parse_get_bucket_versioning, GetBucketVersioningResult)

    def put_bucket_policy(self, policy):
        """设置bucket授权策略, 具体policy书写规则请参考官方文档

        :param str policy: 授权策略
        """
        logger.debug("Start to put bucket policy, bucket: {0}, policy: {1}".format(self.bucket_name, policy))
        resp = self.__do_bucket('PUT', data=policy, params={Bucket.POLICY: ''}, headers={'Content-MD5': utils.content_md5(policy)})
        logger.debug("Put bucket policy done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))

        return RequestResult(resp)

    def get_bucket_policy(self):
        """获取bucket授权策略

        :return: :class:`GetBucketPolicyResult <oss2.models.GetBucketPolicyResult>`
        """

        logger.debug("Start to get bucket policy, bucket: {0}".format(self.bucket_name))
        resp = self.__do_bucket('GET', params={Bucket.POLICY:''})
        logger.debug("Get bucket policy done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return GetBucketPolicyResult(resp)

    def delete_bucket_policy(self):
        """删除bucket授权策略
        :return: :class:`RequestResult <oss2.models.RequestResult>`
        """
        logger.debug("Start to delete bucket policy, bucket: {0}".format(self.bucket_name))
        resp = self.__do_bucket('DELETE', params={Bucket.POLICY: ''})
        logger.debug("Delete bucket policy done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return RequestResult(resp)

    def put_bucket_request_payment(self, payer):
        """设置付费者。

        :param input: :class: str 
        """
        data = xml_utils.to_put_bucket_request_payment(payer)
        logger.debug("Start to put bucket request payment, bucket: {0}, payer: {1}".format(self.bucket_name, payer))
        resp = self.__do_bucket('PUT', data=data, params={Bucket.REQUESTPAYMENT: ''}, headers={'Content-MD5': utils.content_md5(data)})
        logger.debug("Put bucket request payment done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        
        return RequestResult(resp)
    
    def get_bucket_request_payment(self):
        """获取付费者设置。

        :return: :class:`GetBucketRequestPaymentResult <oss2.models.GetBucketRequestPaymentResult>`
        """
        logger.debug("Start to get bucket request payment, bucket: {0}.".format(self.bucket_name))
        resp = self.__do_bucket('GET', params={Bucket.REQUESTPAYMENT: ''})
        logger.debug("Get bucket request payment done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))

        return self._parse_result(resp, xml_utils.parse_get_bucket_request_payment, GetBucketRequestPaymentResult)

    def put_bucket_qos_info(self, bucket_qos_info):
        """配置bucket的QoSInfo

        :param bucket_qos_info :class:`BucketQosInfo <oss2.models.BucketQosInfo>`
        :return: :class:`RequestResult <oss2.models.RequestResult>`
        """
        logger.debug("Start to put bucket qos info, bucket: {0}".format(self.bucket_name))
        data = self.__convert_data(BucketQosInfo, xml_utils.to_put_qos_info, bucket_qos_info) 

        headers = http.CaseInsensitiveDict()
        headers['Content-MD5'] = utils.content_md5(data)
        resp = self.__do_bucket('PUT', data=data, params={Bucket.QOS_INFO: ''}, headers=headers)
        logger.debug("Get bucket qos info done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))

        return RequestResult(resp)

    def get_bucket_qos_info(self):
        """获取bucket的QoSInfo

        :return: :class:`GetBucketQosInfoResult <oss2.models.GetBucketQosInfoResult>`
        """
        logger.debug("Start to get bucket qos info, bucket: {0}".format(self.bucket_name))
        resp = self.__do_bucket('GET', params={Bucket.QOS_INFO: ''})
        logger.debug("Get bucket qos info, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))

        return self._parse_result(resp, xml_utils.parse_get_qos_info, GetBucketQosInfoResult)

    def delete_bucket_qos_info(self):
        """删除bucket的QoSInfo

        :return: :class:`RequestResult <oss2.models.RequestResult>`
        """
        logger.debug("Start to delete bucket qos info, bucket: {0}".format(self.bucket_name))
        resp = self.__do_bucket('DELETE', params={Bucket.QOS_INFO: ''})
        logger.debug("Delete bucket qos info done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))

        return RequestResult(resp)

    def set_bucket_storage_capacity(self, user_qos):
        """设置Bucket的容量，单位GB

        :param user_qos :class:`BucketUserQos <oss2.models.BucketUserQos>`
        """
        logger.debug("Start to set bucket storage capacity: {0}".format(self.bucket_name))
        data = xml_utils.to_put_bucket_user_qos(user_qos)
        resp = self.__do_bucket('PUT', data=data, params={Bucket.USER_QOS: ''})
        logger.debug("Set bucket storage capacity done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))

        return RequestResult(resp)

    def get_bucket_storage_capacity(self):
        """获取bucket的容量信息。

        :return: :class:`GetBucketUserQosResult <oss2.models.GetBucketUserQosResult>`
        """
        logger.debug("Start to get bucket storage capacity, bucket:{0}".format(self.bucket_name))
        resp = self._Bucket__do_bucket('GET', params={Bucket.USER_QOS: ''})
        logger.debug("Get bucket storage capacity done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))

        return self._parse_result(resp, xml_utils.parse_get_bucket_user_qos, GetBucketUserQosResult)

    def put_async_fetch_task(self, task_config):
        """创建一个异步获取文件到bucket的任务。

        :param task_config: 任务配置
        :type task_config: class:`AsyncFetchTaskConfiguration <oss2.models.AsyncFetchTaskConfiguration>` 

        :return: :class:`PutAsyncFetchTaskResult <oss2.models.PutAsyncFetchTaskResult>`
        """
        logger.debug("Start to put async fetch task, bucket:{0}".format(self.bucket_name))
        data = xml_utils.to_put_async_fetch_task(task_config)
        headers = http.CaseInsensitiveDict()
        headers['Content-MD5'] = utils.content_md5(data)
        resp = self._Bucket__do_bucket('POST', data=data, params={Bucket.ASYNC_FETCH: ''}, headers=headers)
        logger.debug("Put async fetch task done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))

        return self._parse_result(resp, xml_utils.parse_put_async_fetch_task_result, PutAsyncFetchTaskResult)

    def get_async_fetch_task(self, task_id):
        """获取一个异步获取文件到bucket的任务信息。

        :param str task_id: 任务id
        :return: :class:`GetAsyncFetchTaskResult <oss2.models.GetAsyncFetchTaskResult>`
        """
        logger.debug("Start to get async fetch task, bucket:{0}, task_id:{1}".format(self.bucket_name, task_id))
        resp = self._Bucket__do_bucket('GET', headers={OSS_TASK_ID: task_id}, params={Bucket.ASYNC_FETCH: ''})
        logger.debug("Put async fetch task done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))

        return self._parse_result(resp, xml_utils.parse_get_async_fetch_task_result, GetAsyncFetchTaskResult)

    def _get_bucket_config(self, config):
        """获得Bucket某项配置，具体哪种配置由 `config` 指定。该接口直接返回 `RequestResult` 对象。
        通过read()接口可以获得XML字符串。不建议使用。

        :param str config: 可以是 `Bucket.ACL` 、 `Bucket.LOGGING` 等。

        :return: :class:`RequestResult <oss2.models.RequestResult>`
        """
        logger.debug("Start to get bucket config, bucket: {0}".format(self.bucket_name))
        resp = self.__do_bucket('GET', params={config: ''})
        logger.debug("Get bucket config done, req_id: {0}, status_code: {1}".format(resp.request_id, resp.status))
        return resp

    def __do_object(self, method, key, **kwargs):
        return self._do(method, self.bucket_name, key, **kwargs)

    def __do_bucket(self, method, **kwargs):
        return self._do(method, self.bucket_name, '', **kwargs)

    def __convert_data(self, klass, converter, data):
        if isinstance(data, klass):
            return converter(data)
        else:
            return data


class CryptoBucket():
    """用于加密Bucket和Object操作的类，诸如上传、下载Object等。创建、删除bucket的操作需使用Bucket类接口。

    用法（假设Bucket属于杭州区域） ::

        >>> import oss2
        >>> auth = oss2.Auth('your-access-key-id', 'your-access-key-secret')
        >>> bucket = oss2.CryptoBucket(auth, 'http://oss-cn-hangzhou.aliyuncs.com', 'your-bucket', oss2.LocalRsaProvider())
        >>> bucket.put_object('readme.txt', 'content of the object')
        <oss2.models.PutObjectResult object at 0x029B9930>

    :param auth: 包含了用户认证信息的Auth对象
    :type auth: oss2.Auth

    :param str endpoint: 访问域名或者CNAME
    :param str bucket_name: Bucket名
    :param crypto_provider: 客户端加密类。该参数默认为空
    :type crypto_provider: oss2.crypto.LocalRsaProvider
    :param bool is_cname: 如果endpoint是CNAME则设为True；反之，则为False。

    :param session: 会话。如果是None表示新开会话，非None则复用传入的会话
    :type session: oss2.Session

    :param float connect_timeout: 连接超时时间，以秒为单位。

    :param str app_name: 应用名。该参数不为空，则在User Agent中加入其值。
        注意到，最终这个字符串是要作为HTTP Header的值传输的，所以必须要遵循HTTP标准。

    :param bool enable_crc: 如果开启crc校验则设为True；反之，则为False

    """

    def __init__(self, auth, endpoint, bucket_name, crypto_provider,
                 is_cname=False,
                 session=None,
                 connect_timeout=None,
                 app_name='',
                 enable_crc=True):

        if not isinstance(crypto_provider, BaseCryptoProvider):
            raise ClientError('Crypto bucket must provide a valid crypto_provider')

        self.crypto_provider = crypto_provider
        self.bucket_name = bucket_name.strip()
        self.enable_crc = enable_crc
        self.bucket = Bucket(auth, endpoint, bucket_name, is_cname, session, connect_timeout,
                             app_name, enable_crc=False)

    def put_object(self, key, data,
                   headers=None,
                   progress_callback=None):
        """上传一个普通文件。

        用法 ::
            >>> bucket.put_object('readme.txt', 'content of readme.txt')
            >>> with open(u'local_file.txt', 'rb') as f:
            >>>     bucket.put_object('remote_file.txt', f)

        :param key: 上传到OSS的文件名

        :param data: 待上传的内容。
        :type data: bytes，str或file-like object

        :param headers: 用户指定的HTTP头部。可以指定Content-Type、Content-MD5、x-oss-meta-开头的头部等
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :param progress_callback: 用户指定的进度回调函数。可以用来实现进度条等功能。参考 :ref:`progress_callback` 。

        :return: :class:`PutObjectResult <oss2.models.PutObjectResult>`
        """
        if progress_callback:
            data = utils.make_progress_adapter(data, progress_callback)

        random_key = self.crypto_provider.get_key()
        start = self.crypto_provider.get_start()
        data = self.crypto_provider.make_encrypt_adapter(data, random_key, start)
        headers = self.crypto_provider.build_header(headers)

        if self.enable_crc:
            data = utils.make_crc_adapter(data)

        return self.bucket.put_object(key, data, headers, progress_callback=None)

    def put_object_from_file(self, key, filename,
                             headers=None,
                             progress_callback=None):
        """上传一个本地文件到OSS的普通文件。

        :param str key: 上传到OSS的文件名
        :param str filename: 本地文件名，需要有可读权限

        :param headers: 用户指定的HTTP头部。可以指定Content-Type、Content-MD5、x-oss-meta-开头的头部等
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :param progress_callback: 用户指定的进度回调函数。参考 :ref:`progress_callback`

        :return: :class:`PutObjectResult <oss2.models.PutObjectResult>`
        """
        headers = utils.set_content_type(http.CaseInsensitiveDict(headers), filename)

        with open(to_unicode(filename), 'rb') as f:
            return self.put_object(key, f, headers=headers, progress_callback=progress_callback)

    def get_object(self, key,
                   headers=None,
                   progress_callback=None,
                   params=None):
        """下载一个文件。

        用法 ::

            >>> result = bucket.get_object('readme.txt')
            >>> print(result.read())
            'hello world'

        :param key: 文件名

        :param headers: HTTP头部
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :param progress_callback: 用户指定的进度回调函数。参考 :ref:`progress_callback`

        :param params: http 请求的查询字符串参数
        :type params: dict

        :return: file-like object

        :raises: 如果文件不存在，则抛出 :class:`NoSuchKey <oss2.exceptions.NoSuchKey>` ；还可能抛出其他异常
        """
        headers = http.CaseInsensitiveDict(headers)

        if 'range' in headers:
            raise ClientError('Crypto bucket do not support range get')

        encrypted_result = self.bucket.get_object(key, headers=headers, params=params, progress_callback=None)

        return GetObjectResult(encrypted_result.resp, progress_callback, self.enable_crc,
                               crypto_provider=self.crypto_provider)

    def get_object_to_file(self, key, filename,
                           headers=None,
                           progress_callback=None,
                           params=None):
        """下载一个文件到本地文件。

        :param key: 文件名
        :param filename: 本地文件名。要求父目录已经存在，且有写权限。

        :param headers: HTTP头部
        :type headers: 可以是dict，建议是oss2.CaseInsensitiveDict

        :param progress_callback: 用户指定的进度回调函数。参考 :ref:`progress_callback`

        :param params: http 请求的查询字符串参数
        :type params: dict

        :return: 如果文件不存在，则抛出 :class:`NoSuchKey <oss2.exceptions.NoSuchKey>` ；还可能抛出其他异常
        """
        with open(to_unicode(filename), 'wb') as f:
            result = self.get_object(key, headers=headers, progress_callback=progress_callback,
                                     params=params)

            if result.content_length is None:
                shutil.copyfileobj(result, f)
            else:
                utils.copyfileobj_and_verify(result, f, result.content_length, request_id=result.request_id)

            return result


def _normalize_endpoint(endpoint):
    if not endpoint.startswith('http://') and not endpoint.startswith('https://'):
        return 'http://' + endpoint
    else:
        return endpoint


_ENDPOINT_TYPE_ALIYUN = 0
_ENDPOINT_TYPE_CNAME = 1
_ENDPOINT_TYPE_IP = 2


def _make_range_string(range):
    if range is None:
        return ''

    start = range[0]
    last = range[1]

    if start is None and last is None:
        return ''

    return 'bytes=' + _range(start, last)


def _range(start, last):
    def to_str(pos):
        if pos is None:
            return ''
        else:
            return str(pos)

    return to_str(start) + '-' + to_str(last)


def _determine_endpoint_type(netloc, is_cname, bucket_name):
    if utils.is_ip_or_localhost(netloc):
        return _ENDPOINT_TYPE_IP

    if is_cname:
        return _ENDPOINT_TYPE_CNAME

    if utils.is_valid_bucket_name(bucket_name):
        return _ENDPOINT_TYPE_ALIYUN
    else:
        return _ENDPOINT_TYPE_IP


class _UrlMaker(object):
    def __init__(self, endpoint, is_cname):
        p = urlparse(endpoint)

        self.scheme = p.scheme
        self.netloc = p.netloc
        self.is_cname = is_cname

    def __call__(self, bucket_name, key, slash_safe=False):
        self.type = _determine_endpoint_type(self.netloc, self.is_cname, bucket_name)

        safe = '/' if slash_safe is True else ''
        key = urlquote(key, safe=safe)

        if self.type == _ENDPOINT_TYPE_CNAME:
            return '{0}://{1}/{2}'.format(self.scheme, self.netloc, key)

        if self.type == _ENDPOINT_TYPE_IP:
            if bucket_name:
                return '{0}://{1}/{2}/{3}'.format(self.scheme, self.netloc, bucket_name, key)
            else:
                return '{0}://{1}/{2}'.format(self.scheme, self.netloc, key)

        if not bucket_name:
            assert not key
            return '{0}://{1}'.format(self.scheme, self.netloc)

        return '{0}://{1}.{2}/{3}'.format(self.scheme, bucket_name, self.netloc, key)
