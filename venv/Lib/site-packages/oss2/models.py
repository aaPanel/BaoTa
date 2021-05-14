# -*- coding: utf-8 -*-

"""
oss2.models
~~~~~~~~~~

该模块包含Python SDK API接口所需要的输入参数以及返回值类型。
"""

from .utils import http_to_unixtime, make_progress_adapter, make_crc_adapter
from .exceptions import ClientError, InconsistentError
from .compat import urlunquote, to_string, urlquote
from .select_response import SelectResponseAdapter
from .headers import *
import json

class PartInfo(object):
    """表示分片信息的文件。

    该文件既用于 :func:`list_parts <oss2.Bucket.list_parts>` 的输出，也用于 :func:`complete_multipart_upload
    <oss2.Bucket.complete_multipart_upload>` 的输入。

    :param int part_number: 分片号
    :param str etag: 分片的ETag
    :param int size: 分片的大小。用在 `list_parts` 的结果里，也用与分片对象做crc combine得到整个对象crc64值
    :param int last_modified: 该分片最后修改的时间戳，类型为int。参考 :ref:`unix_time`
    :param int part_crc: 该分片的crc64值
    """
    def __init__(self, part_number, etag, size=None, last_modified=None, part_crc=None):
        self.part_number = part_number
        self.etag = etag
        self.size = size
        self.last_modified = last_modified
        self.part_crc = part_crc


def _hget(headers, key, converter=lambda x: x):
    if key in headers:
        return converter(headers[key])
    else:
        return None


def _get_etag(headers):
    return _hget(headers, 'etag', lambda x: x.strip('"'))


class RequestResult(object):
    def __init__(self, resp):
        #: HTTP响应
        self.resp = resp

        #: HTTP状态码
        self.status = resp.status

        #: HTTP头
        self.headers = resp.headers

        #: 请求ID，用于跟踪一个OSS请求。提交工单时，最后能够提供请求ID
        self.request_id = resp.request_id

        self.versionid = _hget(self.headers, 'x-oss-version-id')

        self.delete_marker = _hget(self.headers, 'x-oss-delete-marker', bool)

class HeadObjectResult(RequestResult):
    def __init__(self, resp):
        super(HeadObjectResult, self).__init__(resp)

        #: 文件类型，可以是'Normal'、'Multipart'、'Appendable'等
        self.object_type = _hget(self.headers, OSS_OBJECT_TYPE)

        #: 文件最后修改时间，类型为int。参考 :ref:`unix_time` 。

        self.last_modified = _hget(self.headers, 'last-modified', http_to_unixtime)

        #: 文件的MIME类型
        self.content_type = _hget(self.headers, 'content-type')

        #: Content-Length，可能是None。
        self.content_length = _hget(self.headers, 'content-length', int)

        #: HTTP ETag
        self.etag = _get_etag(self.headers)

        #: 文件 server_crc
        self._server_crc = _hget(self.headers, 'x-oss-hash-crc64ecma', int)

    @property
    def server_crc(self):
        return self._server_crc


class GetSelectObjectMetaResult(HeadObjectResult):
    def __init__(self, resp):
        super(GetSelectObjectMetaResult, self).__init__(resp)
        self.select_resp = SelectResponseAdapter(resp, None, None, False)

        for data in self.select_resp: # waiting the response body to finish
            pass

        self.csv_rows = self.select_resp.rows  # to be compatible with previous version. 
        self.csv_splits = self.select_resp.splits  # to be compatible with previous version. 
        self.rows = self.csv_rows 
        self.splits = self.csv_splits


class GetObjectMetaResult(RequestResult):
    def __init__(self, resp):
        super(GetObjectMetaResult, self).__init__(resp)

        #: 文件最后修改时间，类型为int。参考 :ref:`unix_time` 。
        self.last_modified = _hget(self.headers, 'last-modified', http_to_unixtime)

        #: Content-Length，文件大小，类型为int。
        self.content_length = _hget(self.headers, 'content-length', int)

        #: HTTP ETag
        self.etag = _get_etag(self.headers)


class GetSymlinkResult(RequestResult):
    def __init__(self, resp):
        super(GetSymlinkResult, self).__init__(resp)

        #: 符号连接的目标文件
        self.target_key = urlunquote(_hget(self.headers, OSS_SYMLINK_TARGET))
        
        
class GetObjectResult(HeadObjectResult):
    def __init__(self, resp, progress_callback=None, crc_enabled=False, crypto_provider=None):
        super(GetObjectResult, self).__init__(resp)
        self.__crc_enabled = crc_enabled
        self.__crypto_provider = crypto_provider

        if _hget(resp.headers, 'x-oss-meta-oss-crypto-key') and _hget(resp.headers, 'Content-Range'):
            raise ClientError('Could not get an encrypted object using byte-range parameter')

        if progress_callback:
            self.stream = make_progress_adapter(self.resp, progress_callback, self.content_length)
        else:
            self.stream = self.resp
        
        if self.__crc_enabled:
            self.stream = make_crc_adapter(self.stream)

        if self.__crypto_provider:
            key = self.__crypto_provider.decrypt_oss_meta_data(resp.headers, 'x-oss-meta-oss-crypto-key')
            start = self.__crypto_provider.decrypt_oss_meta_data(resp.headers, 'x-oss-meta-oss-crypto-start')
            cek_alg = _hget(resp.headers, 'x-oss-meta-oss-cek-alg')
            if key and start and cek_alg:
                self.stream = self.__crypto_provider.make_decrypt_adapter(self.stream, key, start)
            else:
                raise InconsistentError('all metadata keys are required for decryption (x-oss-meta-oss-crypto-key, \
                                        x-oss-meta-oss-crypto-start, x-oss-meta-oss-cek-alg)', self.request_id)

    def read(self, amt=None):
        return self.stream.read(amt)

    def __iter__(self):
        return iter(self.stream)
    
    @property
    def client_crc(self):
        if self.__crc_enabled:
            return self.stream.crc
        else:
            return None

class SelectObjectResult(HeadObjectResult):
    def __init__(self, resp, progress_callback=None, crc_enabled=False):
        super(SelectObjectResult, self).__init__(resp)
        self.__crc_enabled = crc_enabled
        self.select_resp = SelectResponseAdapter(resp, progress_callback, None, enable_crc = self.__crc_enabled)

    def read(self):
        return self.select_resp.read()
        
    def __iter__(self):
        return iter(self.select_resp)
    
    def __next__(self):
        return self.select_resp.next()

class PutObjectResult(RequestResult):
    def __init__(self, resp):
        super(PutObjectResult, self).__init__(resp)

        #: HTTP ETag
        self.etag = _get_etag(self.headers)
        
        #: 文件上传后，OSS上文件的CRC64值
        self.crc = _hget(resp.headers, OSS_HASH_CRC64_ECMA, int)


class AppendObjectResult(RequestResult):
    def __init__(self, resp):
        super(AppendObjectResult, self).__init__(resp)

        #: HTTP ETag
        self.etag = _get_etag(self.headers)

        #: 本次追加写完成后，OSS上文件的CRC64值
        self.crc = _hget(resp.headers, OSS_HASH_CRC64_ECMA, int)

        #: 下次追加写的偏移
        self.next_position = _hget(resp.headers, OSS_NEXT_APPEND_POSITION, int)

class BatchDeleteObjectVersion(object):
    def __init__(self, key=None, versionid=None):
        self.key = key or ''
        self.versionid = versionid or ''

class BatchDeleteObjectVersionList(object):
    def __init__(self, object_version_list=None):
        self.object_version_list = object_version_list or []

    def append(self, object_version):
        self.object_version_list.append(object_version)

    def len(self):
        return len(self.object_version_list)

class BatchDeleteObjectVersionResult(object):
    def __init__(self, key, versionid=None, delete_marker=None, delete_marker_versionid=None):
        self.key = key
        self.versionid = versionid or ''
        self.delete_marker = delete_marker or False
        self.delete_marker_versionid = delete_marker_versionid or ''

class BatchDeleteObjectsResult(RequestResult):
    def __init__(self, resp):
        super(BatchDeleteObjectsResult, self).__init__(resp)

        #: 已经删除的文件名列表
        self.deleted_keys = []

        #：已经删除的带版本信息的文件信息列表
        self.delete_versions = []


class InitMultipartUploadResult(RequestResult):
    def __init__(self, resp):
        super(InitMultipartUploadResult, self).__init__(resp)

        #: 新生成的Upload ID
        self.upload_id = None


class ListObjectsResult(RequestResult):
    def __init__(self, resp):
        super(ListObjectsResult, self).__init__(resp)

        #: True表示还有更多的文件可以罗列；False表示已经列举完毕。
        self.is_truncated = False

        #: 下一次罗列的分页标记符，即，可以作为 :func:`list_objects <oss2.Bucket.list_objects>` 的 `marker` 参数。
        self.next_marker = ''

        #: 本次罗列得到的文件列表。其中元素的类型为 :class:`SimplifiedObjectInfo` 。
        self.object_list = []

        #: 本次罗列得到的公共前缀列表，类型为str列表。
        self.prefix_list = []


class SimplifiedObjectInfo(object):
    def __init__(self, key, last_modified, etag, type, size, storage_class):
        #: 文件名，或公共前缀名。
        self.key = key

        #: 文件的最后修改时间
        self.last_modified = last_modified

        #: HTTP ETag
        self.etag = etag

        #: 文件类型
        self.type = type

        #: 文件大小
        self.size = size

        #: 文件的存储类别，是一个字符串。
        self.storage_class = storage_class

    def is_prefix(self):
        """如果是公共前缀，返回True；是文件，则返回False"""
        return self.last_modified is None


OBJECT_ACL_DEFAULT = 'default'
OBJECT_ACL_PRIVATE = 'private'
OBJECT_ACL_PUBLIC_READ = 'public-read'
OBJECT_ACL_PUBLIC_READ_WRITE = 'public-read-write'


class GetObjectAclResult(RequestResult):
    def __init__(self, resp):
        super(GetObjectAclResult, self).__init__(resp)

        #: 文件的ACL，其值可以是 `OBJECT_ACL_DEFAULT`、`OBJECT_ACL_PRIVATE`、`OBJECT_ACL_PUBLIC_READ`或
        #: `OBJECT_ACL_PUBLIC_READ_WRITE`
        self.acl = ''


class SimplifiedBucketInfo(object):
    """:func:`list_buckets <oss2.Service.list_objects>` 结果中的单个元素类型。"""
    def __init__(self, name, location, creation_date, extranet_endpoint, intranet_endpoint, storage_class):
        #: Bucket名
        self.name = name

        #: Bucket的区域
        self.location = location

        #: Bucket的创建时间，类型为int。参考 :ref:`unix_time`。
        self.creation_date = creation_date

        #: Bucket访问的外网域名
        self.extranet_endpoint = extranet_endpoint

        #: 同区域ECS访问Bucket的内网域名
        self.intranet_endpoint = intranet_endpoint

        #: Bucket存储类型，支持“Standard”、“IA”、“Archive”
        self.storage_class = storage_class


class ListBucketsResult(RequestResult):
    def __init__(self, resp):
        super(ListBucketsResult, self).__init__(resp)

        #: True表示还有更多的Bucket可以罗列；False表示已经列举完毕。
        self.is_truncated = False

        #: 下一次罗列的分页标记符，即，可以作为 :func:`list_buckets <oss2.Service.list_buckets>` 的 `marker` 参数。
        self.next_marker = ''

        #: 得到的Bucket列表，类型为 :class:`SimplifiedBucketInfo` 。
        self.buckets = []


class MultipartUploadInfo(object):
    def __init__(self, key, upload_id, initiation_date):
        #: 文件名
        self.key = key

        #: 分片上传ID
        self.upload_id = upload_id

        #: 分片上传初始化的时间，类型为int。参考 :ref:`unix_time`
        self.initiation_date = initiation_date

    def is_prefix(self):
        """如果是公共前缀则返回True"""
        return self.upload_id is None


class ListMultipartUploadsResult(RequestResult):
    def __init__(self, resp):
        super(ListMultipartUploadsResult, self).__init__(resp)

        #: True表示还有更多的为完成分片上传可以罗列；False表示已经列举完毕。
        self.is_truncated = False

        #: 文件名分页符
        self.next_key_marker = ''

        #: 分片上传ID分页符
        self.next_upload_id_marker = ''

        #: 分片上传列表。类型为`MultipartUploadInfo`列表。
        self.upload_list = []

        #: 公共前缀列表。类型为str列表。
        self.prefix_list = []


class ListPartsResult(RequestResult):
    def __init__(self, resp):
        super(ListPartsResult, self).__init__(resp)

        # True表示还有更多的Part可以罗列；False表示已经列举完毕。
        self.is_truncated = False

        # 下一个分页符
        self.next_marker = ''

        # 罗列出的Part信息，类型为 `PartInfo` 列表。
        self.parts = []


BUCKET_ACL_PRIVATE = 'private'
BUCKET_ACL_PUBLIC_READ = 'public-read'
BUCKET_ACL_PUBLIC_READ_WRITE = 'public-read-write'

BUCKET_STORAGE_CLASS_STANDARD = 'Standard'
BUCKET_STORAGE_CLASS_IA = 'IA'
BUCKET_STORAGE_CLASS_ARCHIVE = 'Archive'

BUCKET_DATA_REDUNDANCY_TYPE_LRS = "LRS"
BUCKET_DATA_REDUNDANCY_TYPE_ZRS = "ZRS"

REDIRECT_TYPE_MIRROR = 'Mirror'
REDIRECT_TYPE_EXTERNAL = 'External'
REDIRECT_TYPE_INTERNAL = 'Internal'
REDIRECT_TYPE_ALICDN = 'AliCDN'

PAYER_BUCKETOWNER = 'BucketOwner'
PAYER_REQUESTER = 'Requester'

class GetBucketAclResult(RequestResult):
    def __init__(self, resp):
        super(GetBucketAclResult, self).__init__(resp)

        #: Bucket的ACL，其值可以是 `BUCKET_ACL_PRIVATE`、`BUCKET_ACL_PUBLIC_READ`或`BUCKET_ACL_PUBLIC_READ_WRITE`。
        self.acl = ''


class GetBucketLocationResult(RequestResult):
    def __init__(self, resp):
        super(GetBucketLocationResult, self).__init__(resp)

        #: Bucket所在的数据中心
        self.location = ''


class BucketLogging(object):
    """Bucket日志配置信息。

    :param str target_bucket: 存储日志到这个Bucket。
    :param str target_prefix: 生成的日志文件名加上该前缀。
    """
    def __init__(self, target_bucket, target_prefix):
        self.target_bucket = target_bucket
        self.target_prefix = target_prefix


class GetBucketLoggingResult(RequestResult, BucketLogging):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        BucketLogging.__init__(self, '', '')


class BucketCreateConfig(object):
    def __init__(self, storage_class, data_redundancy_type=None):
        self.storage_class = storage_class
        self.data_redundancy_type = data_redundancy_type


class BucketStat(object):
    def __init__(self, storage_size_in_bytes, object_count, multi_part_upload_count):
        self.storage_size_in_bytes = storage_size_in_bytes
        self.object_count = object_count
        self.multi_part_upload_count = multi_part_upload_count


class AccessControlList(object):
    def __init__(self, grant):
        self.grant = grant


class Owner(object):
    def __init__(self, display_name, owner_id):
        self.display_name = display_name
        self.id = owner_id


class BucketInfo(object):
    def __init__(self, name=None, owner=None, location=None, storage_class=None, intranet_endpoint=None,
                 extranet_endpoint=None, creation_date=None, acl=None, data_redundancy_type=None, comment=None,
                 bucket_encryption_rule=None, versioning_status=None):
        self.name = name
        self.owner = owner
        self.location = location
        self.storage_class = storage_class
        self.intranet_endpoint = intranet_endpoint
        self.extranet_endpoint = extranet_endpoint
        self.creation_date = creation_date
        self.acl = acl
        self.data_redundancy_type = data_redundancy_type
        self.comment = comment

        self.bucket_encryption_rule = bucket_encryption_rule
        self.versioning_status = versioning_status


class GetBucketStatResult(RequestResult, BucketStat):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        BucketStat.__init__(self, 0, 0, 0)


class GetBucketInfoResult(RequestResult, BucketInfo):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        BucketInfo.__init__(self)


class BucketReferer(object):
    """Bucket防盗链设置。

    :param bool allow_empty_referer: 是否允许空的Referer。
    :param referers: Referer列表，每个元素是一个str。
    """
    def __init__(self, allow_empty_referer, referers):
        self.allow_empty_referer = allow_empty_referer
        self.referers = referers


class GetBucketRefererResult(RequestResult, BucketReferer):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        BucketReferer.__init__(self, False, [])

class Condition(object):
    """ 匹配规则

    :父节点: class `RoutingRule <oss2.models.RoutingRule>`
    :param key_prefix_equals: 匹配object的前缀，
    :type key_prefix_equals:  string str

    :param http_err_code_return_equals: 匹配访问object时返回的status。
    :type http_err_code_return_equals: int

    :param include_header_list: 匹配指定的header
    :type include_header_list: list of :class:`ConditionInlcudeHeader`
    """
    def __init__(self, key_prefix_equals=None, http_err_code_return_equals=None, include_header_list=None):
        if (include_header_list is not None): 
            if not isinstance(include_header_list, list):
                raise ClientError('class of include_header should be list')
            
            if len(include_header_list) > 5:
                raise ClientError('capacity of include_header_list should not > 5, please check!')

        self.key_prefix_equals = key_prefix_equals
        self.http_err_code_return_equals = http_err_code_return_equals
        self.include_header_list = include_header_list or []


class ConditionInlcudeHeader(object):
    """ 指定匹配的header

    :父节点: class `Condition <oss2.models.Condition>`
    :param key: header key
    :type key: str
    :param key: header value
    :type key: str
    """
    def __init__(self, key=None, equals= None):
        self.key = key
        self.equals = equals


class Redirect(object):
    """匹配规则之后执行的动作
    
    :父节点: class `RoutingRule <oss2.models.RoutingRule>`

    :param redirect_type: 跳转类型, 取值为Mirror, External, Internal, AliCDN其中一个。
    :type redirect_type: class: str

    :param pass_query_string: 执行跳转或者镜像回源时，是否要携带发起请求的请求参数，默认false。
    :type pass_query_string: bool

    :param replace_key_with: Redirect的时候object name将替换成这个值，可以支持变量（目前支持的变量是${key}
        当RedirectType为Internal, External或者AliCDN时有效。
    :type replace_key_with: str

    :param replace_key_prefix_with: Redirect的时候object name的前缀将替换成这个值。如果前缀为空则将这个字符串插入在object namde的最前面。
        当RedirectType为Internal, External或者AliCDN时有效。
    :type replace_key_prefix_with: str

    :param proto: 跳转时的协议，只能取值为http或者https。
        当RedirectType为External或者AliCDN时有效。
    :type proto: class: str

    :param host_name: 跳转时的域名
        当RedirectType为External或者AliCDN时有效。
    :type host_name: str

    :param http_redirect_code: 跳转时返回的状态码，取值为301、302或307。
        当RedirectType为External或者AliCDN时有效。
    :type http_redirect_code: int （HTTP状态码）
    
    :mirror相关当参数只有当RedirectType为Mirror时有效。
    
    :param mirror_url: 镜像回源的源站地址，
    :type mirror_url: str

    :param mirror_url_slave: 镜像回源的备站地址
    :type mirror_url_slave: str

    :param mirror_url_probe: 主备切换模式的探测url，这个url需要代表主源站的健康程度，mirror_url_slave指定时，此项必须指定。
    :type mirror_url_probe: str

    :param mirror_pass_query_string: 作用同pass_query_string，默认false。
    :type mirror_pass_query_string: bool

    :param mirror_follow_redirect: 如果镜像回源获取的结果是3xx，是否要继续跳转到指定的Location获取数据。默认true。
    :type mirror_follow_redirect: bool

    :param mirror_check_md5: 是否要检查回源body的md5, 默认false。
    :type mirror_check_md5: bool

    :param mirror_headers: 指定匹配此规则后执行的动作。
    :type mirror_headers: class:`RedirectMirrorHeaders <oss2.models.RedirectMirrorHeaders>`

    """
    def __init__(self, redirect_type=None, pass_query_string= None, replace_key_with=None, replace_key_prefix_with=None, 
                    proto=None, host_name=None, http_redirect_code=None,  mirror_url=None, mirror_url_slave=None, 
                    mirror_url_probe=None, mirror_pass_query_string=None, mirror_follow_redirect=None, 
                    mirror_check_md5=None, mirror_headers=None):

        if redirect_type not in [REDIRECT_TYPE_MIRROR, REDIRECT_TYPE_EXTERNAL, REDIRECT_TYPE_INTERNAL, REDIRECT_TYPE_ALICDN]:
            raise ClientError('redirect_type must be Internal, External, Mirror or AliCDN.')

        if redirect_type == REDIRECT_TYPE_INTERNAL:
            if any((host_name, proto, http_redirect_code)):
                 raise ClientError('host_name, proto, http_redirect_code must be empty when redirect_type is Internal.')

        if redirect_type in [REDIRECT_TYPE_EXTERNAL, REDIRECT_TYPE_ALICDN]:
            if http_redirect_code is not None:
                if http_redirect_code < 300 or http_redirect_code > 399:
                    raise ClientError("http_redirect_code must be a valid HTTP 3xx status code.")

        if redirect_type in [REDIRECT_TYPE_EXTERNAL, REDIRECT_TYPE_ALICDN, REDIRECT_TYPE_INTERNAL]:
            if all((replace_key_with, replace_key_prefix_with)):
                raise ClientError("replace_key_with or replace_key_prefix_with only choose one.")

        elif redirect_type == REDIRECT_TYPE_MIRROR: 
            if any((proto, host_name, replace_key_with, replace_key_prefix_with, http_redirect_code)):
                    raise ClientError('host_name, replace_key_with, replace_key_prefix_with, http_redirect_code and proto must be empty when redirect_type is Mirror.') 

            if mirror_url is None:
                raise ClientError('mirror_url should not be None when redirect_type is Mirror.')

            if (not mirror_url.startswith('http://') and not mirror_url.startswith('https://')) or not mirror_url.endswith('/'):
                raise ClientError(r'mirror_url is invalid, should startwith "http://" or "https://", and endwith "/"')

            if mirror_url_slave is not None:
                if mirror_url_probe is None:
                    raise ClientError('mirror_url_probe should not be none when mirror_url_slave is indicated')

                if (not mirror_url_slave.startswith('http://') and not mirror_url_slave.startswith('https://')) or not mirror_url_slave.endswith('/'):
                    raise ClientError(r'mirror_url_salve is invalid, should startwith "http://" or "https://", and endwith "/"')

        self.redirect_type = redirect_type
        self.pass_query_string = pass_query_string
        self.replace_key_with = replace_key_with
        self.replace_key_prefix_with = replace_key_prefix_with
        self.proto = proto
        self.host_name = host_name
        self.http_redirect_code = http_redirect_code
        self.mirror_url = mirror_url
        self.mirror_url_slave = mirror_url_slave
        self.mirror_url_probe = mirror_url_probe
        self.mirror_pass_query_string = mirror_pass_query_string
        self.mirror_check_md5 = mirror_check_md5
        self.mirror_follow_redirect = mirror_follow_redirect
        self.mirror_headers = mirror_headers


class RedirectMirrorHeaders(object):
    """指定镜像回源时携带的header
    
    :父节点: class `Redirect <oss2.models.Redirect>`
    :param pass_all: 是否透传请求中所有的header（除了保留的几个header以及以oss-/x-oss-/x-drs-开头的header）到源站。默认false
    :type pass_all: bool

    :param pass_list: 透传指定的header到源站，最多10个，只有在RedirectType为Mirror时生效
    :type pass_list: list of str

    :param remove_list: 禁止透传指定的header到源站，这个字段可以重复，最多10个
    :type remove_list: list of str

    :param set_list: 设置一个header传到源站，不管请求中是否携带这些指定的header，回源时都会设置这些header。
        该容器可以重复，最多10组。只有在RedirectType为Mirror时生效。
    :type set_list: list of :class:`MirrorHeadersSet <oss2.models.MirrorHeadersSet>`

    """
    def __init__(self,pass_all=None, pass_list=None, remove_list=None, set_list=None):
        if pass_list is not None:
            if not isinstance(pass_list, list):
                raise ClientError('The type of pass_list should be list.')
            
            if len(pass_list) > 10:
                raise ClientError('The capacity of pass_list should not > 10!')
        
        if remove_list is not None:
            if not isinstance(remove_list, list):
                raise ClientError('The type of remove_list should be list.')
            
            if len(remove_list) > 10:
                raise ClientError('The capacity of remove_list should not > 10!')
        
        if set_list is not None:
            if not isinstance(set_list, list):
                raise ClientError('The type of set_list should be list.')
            
            if len(set_list) > 10:
                raise ClientError('The capacity of set_list should not > 10!')

        self.pass_all = pass_all
        self.pass_list = pass_list or []
        self.remove_list = remove_list or []
        self.set_list = set_list or []
  

class MirrorHeadersSet(object):
    """父节点: class `RedirectMirrorHeaders <oss2.models.RedirectMirrorHeaders>`
    :param key:设置header的key，最多1024个字节，字符集与Pass相同。只有在RedirectType为Mirror时生效。
    :type key: str

    :param value:设置header的value，最多1024个字节，不能出现”\r\n” 。只有在RedirectType为Mirror时生效。
    :type value: str
    """
    def __init__(self, key=None, value=None):
        self.key = key
        self.value = value


class RoutingRule(object):
    """设置静态网站托管模式中的跳转规则
    :param rule_num: RoutingRule的序号, 必须为正整数
    :type rule_num: int

    :param condition: 匹配条件
    :type condition: class:`Condition <oss2.models.Condition>`

    :param redirect: 指定匹配此规则后执行的动作
    :type redirect: class:`Redirect <oss2.models.Redirect>`
    """
    def __init__(self, rule_num=None, condition=None, redirect=None):
        if (rule_num is None) or (not isinstance(rule_num, int)) or (rule_num <= 0):
            raise ClientError('rule_num should be positive integer.')
        
        if(condition is None) or (redirect is None):
            raise ClientError('condition and redirect should be effective.')
        
        if(redirect.redirect_type == REDIRECT_TYPE_MIRROR) and condition.http_err_code_return_equals != 404:
            raise ClientError('http_err_code not match redirect_type, it should be 404!')

        self.rule_num = rule_num
        self.condition = condition
        self.redirect = redirect

class BucketWebsite(object):
    """静态网站托管配置。

    :param str index_file: 索引页面文件
    :param str error_file: 404页面文件
    :param rules : list of class:`RoutingRule <oss2.models.RoutingRule>`
    
    """
    def __init__(self, index_file, error_file, rules=None):
        if rules is not None:
            if not isinstance(rules, list):
                raise ClientError('rules type should be list.')
            if len(rules) > 5:
                raise ClientError('capacity of rules should not be > 5.')

        self.index_file = index_file
        self.error_file = error_file
        self.rules = rules or []


class GetBucketWebsiteResult(RequestResult, BucketWebsite):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        BucketWebsite.__init__(self, '', '', [])


class LifecycleExpiration(object):
    """过期删除操作。

    :param days: 表示在文件修改后过了这么多天，就会匹配规则，从而被删除
    :type days: int

    :param date: 表示在该日期之后，规则就一直生效。即每天都会对符合前缀的文件执行删除操作（如，删除），而不管文件是什么时候生成的。*不建议使用*
    :type date: `datetime.date`

    :param created_before_date: delete files if their last modified time earlier than created_before_date
    :type created_before_date: `datetime.date`

    :param expired_detete_marker: 真实文件删除之后是否自动移除删除标记，适用于多版本场景。
    :param expired_detete_marker: bool

    """
    def __init__(self, days=None, date=None, created_before_date=None, expired_detete_marker=None):
        not_none_fields = 0
        if days is not None:
            not_none_fields += 1
        if date is not None:
            not_none_fields += 1
        if created_before_date is not None:
            not_none_fields += 1
        if expired_detete_marker is not None:
            not_none_fields += 1

        if not_none_fields > 1:
            raise ClientError('More than one field(days, date and created_before_date, expired_detete_marker) has been specified')

        self.days = days
        self.date = date
        self.created_before_date = created_before_date
        self.expired_detete_marker = expired_detete_marker


class AbortMultipartUpload(object):
    """删除parts

    :param days: 删除相对最后修改时间days天之后的parts
    :param created_before_date: 删除最后修改时间早于created_before_date的parts

    """
    def __init__(self, days=None, created_before_date=None):
        if days is not None and created_before_date is not None:
            raise ClientError('days and created_before_date should not be both specified')

        self.days = days
        self.created_before_date = created_before_date


class StorageTransition(object):
    """transit objects

    :param days: 将相对最后修改时间days天之后的Object转储
    :param created_before_date: 将最后修改时间早于created_before_date的对象转储
    :param storage_class: 对象转储到OSS的目标存储类型
    """
    def __init__(self, days=None, created_before_date=None, storage_class=None):
        if days is not None and created_before_date is not None:
            raise ClientError('days and created_before_date should not be both specified')

        self.days = days
        self.created_before_date = created_before_date
        self.storage_class = storage_class


class NoncurrentVersionExpiration(object):
    """OSS何时将非当前版本的object删除

    :param noncurrent_days: 指定多少天之后删除
    :type noncurrent_days: int
    """
    def __init__(self, noncurrent_days):
        self.noncurrent_days = noncurrent_days


class NoncurrentVersionStorageTransition(object):
    """生命周期内，OSS何时将指定Object的非当前版本转储为IA或者Archive存储类型。

    :param noncurrent_days: 多少天之后转存储
    :type noncurrent_days: int
    """
    def __init__(self, noncurrent_days, storage_class):
        self.noncurrent_days = noncurrent_days
        self.storage_class = storage_class


class LifecycleRule(object):
    """生命周期规则。

    :param id: 规则名
    :type id: str

    :param prefix: 只有文件名匹配该前缀的文件才适用本规则
    :type prefix: str

    :param expiration: 过期删除操作。
    :type expiration: :class:`LifecycleExpiration`

    :param status: 启用还是禁止该规则。可选值为 `LifecycleRule.ENABLED` 或 `LifecycleRule.DISABLED`

    :param storage_transitions: 存储类型转换规则
    :type storage_transitions: list of class:`StorageTransition <oss2.models.StorageTransition>`

    :param tagging: object tagging 规则
    :type tagging: :class:`Tagging <oss2.models.StorageTransition>`
    
    :param noncurrent_version_expiration: 指定Object非当前版本生命周期规则的过期属性。适用于多版本场景。
    :type noncurrent_version_expiration class:`NoncurrentVersionExpiration <oss2.models.NoncurrentVersionExpiration>`

    :param noncurrent_version_sotrage_transitions: 在有效生命周期中，OSS何时将指定Object的非当前版本转储为IA或者Archive存储类型，适用于多版本场景。
    :type noncurrent_version_sotrage_transitions: list of class:`NoncurrentVersionStorageTransition <oss2.models.NoncurrentVersionStorageTransition>`
    """

    ENABLED = 'Enabled'
    DISABLED = 'Disabled'

    def __init__(self, id, prefix,
                 status=ENABLED, expiration=None,
                 abort_multipart_upload=None,
                 storage_transitions=None, tagging=None,
                 noncurrent_version_expiration=None,
                 noncurrent_version_sotrage_transitions=None):
        self.id = id
        self.prefix = prefix
        self.status = status
        self.expiration = expiration
        self.abort_multipart_upload = abort_multipart_upload
        self.storage_transitions = storage_transitions
        self.tagging = tagging
        self.noncurrent_version_expiration = noncurrent_version_expiration
        self.noncurrent_version_sotrage_transitions = noncurrent_version_sotrage_transitions


class BucketLifecycle(object):
    """Bucket的生命周期配置。

    :param rules: 规则列表，
    :type rules: list of :class:`LifecycleRule <oss2.models.LifecycleRule>`
    """
    def __init__(self, rules=None):
        self.rules = rules or []


class GetBucketLifecycleResult(RequestResult, BucketLifecycle):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        BucketLifecycle.__init__(self)


class CorsRule(object):
    """CORS（跨域资源共享）规则。

    :param allowed_origins: 允许跨域访问的域。
    :type allowed_origins: list of str

    :param allowed_methods: 允许跨域访问的HTTP方法，如'GET'等。
    :type allowed_methods: list of str

    :param allowed_headers: 允许跨域访问的HTTP头部。
    :type allowed_headers: list of str


    """
    def __init__(self,
                 allowed_origins=None,
                 allowed_methods=None,
                 allowed_headers=None,
                 expose_headers=None,
                 max_age_seconds=None):
        self.allowed_origins = allowed_origins or []
        self.allowed_methods = allowed_methods or []
        self.allowed_headers = allowed_headers or []
        self.expose_headers = expose_headers or []
        self.max_age_seconds = max_age_seconds


class BucketCors(object):
    def __init__(self, rules=None):
        self.rules = rules or []


class GetBucketCorsResult(RequestResult, BucketCors):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        BucketCors.__init__(self)


class LiveChannelInfoTarget(object):
    """Live channel中的Target节点，包含目标协议的一些参数。

    :param type: 协议，目前仅支持HLS。
    :type type: str

    :param frag_duration: HLS协议下生成的ts文件的期望时长，单位为秒。
    :type frag_duration: int

    :param frag_count: HLS协议下m3u8文件里ts文件的数量。
    :type frag_count: int"""

    def __init__(self,
            type = 'HLS',
            frag_duration = 5,
            frag_count = 3,
            playlist_name = ''):
        self.type = type
        self.frag_duration = frag_duration
        self.frag_count = frag_count
        self.playlist_name = playlist_name


class LiveChannelInfo(object):
    """Live channel（直播频道）配置。

    :param status: 直播频道的状态，合法的值为"enabled"和"disabled"。
    :type status: str

    :param description: 直播频道的描述信息，最长为128字节。
    :type description: str

    :param target: 直播频道的推流目标节点，包含目标协议相关的参数。
    :type class:`LiveChannelInfoTarget <oss2.models.LiveChannelInfoTarget>`

    :param last_modified: 直播频道的最后修改时间，这个字段仅在`ListLiveChannel`时使用。
    :type last_modified: int, 参考 :ref:`unix_time`。
    
    :param name: 直播频道的名称。
    :type name: str
        
    :param play_url: 播放地址。
    :type play_url: str
        
    :param publish_url: 推流地址。
    :type publish_url: str"""
    
    def __init__(self,
            status = 'enabled',
            description = '',
            target = LiveChannelInfoTarget(),
            last_modified = None,
            name = None,
            play_url = None,
            publish_url = None):
        self.status = status
        self.description = description
        self.target = target
        self.last_modified = last_modified
        self.name = name
        self.play_url = play_url
        self.publish_url = publish_url


class LiveChannelList(object):
    """List直播频道的结果。

    :param prefix: List直播频道使用的前缀。
    :type prefix: str

    :param marker: List直播频道使用的marker。
    :type marker: str

    :param max_keys: List时返回的最多的直播频道的条数。
    :type max_keys: int

    :param is_truncated: 本次List是否列举完所有的直播频道
    :type is_truncated: bool

    :param next_marker: 下一次List直播频道使用的marker。
    :type marker: str

    :param channels: List返回的直播频道列表
    :type channels: list，类型为 :class:`LiveChannelInfo`"""

    def __init__(self,
            prefix = '',
            marker = '',
            max_keys = 100,
            is_truncated = False,
            next_marker = ''):
        self.prefix = prefix
        self.marker = marker
        self.max_keys = max_keys
        self.is_truncated = is_truncated
        self.next_marker = next_marker
        self.channels = []


class LiveChannelVideoStat(object):
    """LiveStat中的Video节点。

    :param width: 视频的宽度。
    :type width: int

    :param height: 视频的高度。
    :type height: int

    :param frame_rate: 帧率。
    :type frame_rate: int

    :param codec: 编码方式。
    :type codec: str

    :param bandwidth: 码率。
    :type bandwidth: int"""

    def __init__(self,
            width = 0,
            height = 0,
            frame_rate = 0,
            codec = '',
            bandwidth = 0):
        self.width = width
        self.height = height
        self.frame_rate = frame_rate
        self.codec = codec
        self.bandwidth = bandwidth


class LiveChannelAudioStat(object):
    """LiveStat中的Audio节点。

    :param codec: 编码方式。
    :type codec: str

    :param sample_rate: 采样率。
    :type sample_rate: int

    :param bandwidth: 码率。
    :type bandwidth: int"""

    def __init__(self,
            codec = '',
            sample_rate = 0,
            bandwidth = 0):
        self.codec = codec
        self.sample_rate = sample_rate
        self.bandwidth = bandwidth


class LiveChannelStat(object):
    """LiveStat结果。

    :param status: 直播状态。
    :type codec: str

    :param remote_addr: 客户端的地址。
    :type remote_addr: str

    :param connected_time: 本次推流开始时间。
    :type connected_time: int, unix time

    :param video: 视频描述信息。
    :type video: class:`LiveChannelVideoStat <oss2.models.LiveChannelVideoStat>`

    :param audio: 音频描述信息。
    :type audio: class:`LiveChannelAudioStat <oss2.models.LiveChannelAudioStat>`"""

    def __init__(self,
            status = '',
            remote_addr = '',
            connected_time = '',
            video = None,
            audio = None):
        self.status = status
        self.remote_addr = remote_addr
        self.connected_time = connected_time
        self.video = video
        self.audio = audio


class LiveRecord(object):
    """直播频道中的推流记录信息

    :param start_time: 本次推流开始时间。
    :type start_time: int，参考 :ref:`unix_time`。

    :param end_time: 本次推流结束时间。
    :type end_time: int， 参考 :ref:`unix_time`。

    :param remote_addr: 推流时客户端的地址。
    :type remote_addr: str"""

    def __init__(self,
            start_time = '',
            end_time = '',
            remote_addr = ''):
        self.start_time = start_time
        self.end_time = end_time
        self.remote_addr = remote_addr


class LiveChannelHistory(object):
    """直播频道下的推流记录。"""

    def __init__(self):
        self.records = []


class CreateLiveChannelResult(RequestResult, LiveChannelInfo):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        LiveChannelInfo.__init__(self)


class GetLiveChannelResult(RequestResult, LiveChannelInfo):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        LiveChannelInfo.__init__(self)


class ListLiveChannelResult(RequestResult, LiveChannelList):
    def __init__(self, resp):
       RequestResult.__init__(self, resp)
       LiveChannelList.__init__(self)


class GetLiveChannelStatResult(RequestResult, LiveChannelStat):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        LiveChannelStat.__init__(self)

class GetLiveChannelHistoryResult(RequestResult, LiveChannelHistory):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        LiveChannelHistory.__init__(self)

class GetVodPlaylistResult(RequestResult):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        self.playlist = to_string(resp.read())

class ProcessObjectResult(RequestResult):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        self.bucket = ""
        self.fileSize = 0
        self.object = ""
        self.process_status = ""
        result = json.loads(to_string(resp.read()))
        if 'bucket' in result:
            self.bucket = result['bucket']
        if 'fileSize' in result:
            self.fileSize = result['fileSize']
        if 'object' in result:
            self.object = result['object']
        if 'status' in result:
            self.process_status = result['status']

_MAX_OBJECT_TAGGING_KEY_LENGTH=128
_MAX_OBJECT_TAGGING_VALUE_LENGTH=256

class Tagging(object):

    def __init__(self, tagging_rules=None):
        
        self.tag_set = tagging_rules or TaggingRule() 

    def __str__(self):

        tag_str = ""
        
        tagging_rule = self.tag_set.tagging_rule

        for key in tagging_rule:
            tag_str += key
            tag_str += "#" + tagging_rule[key] + " "

        return tag_str

class TaggingRule(object):

    def __init__(self):
        self.tagging_rule = dict()

    def add(self, key, value):

        if key is None or key == '':
            raise ClientError("Tagging key should not be empty")

        if len(key) > _MAX_OBJECT_TAGGING_KEY_LENGTH:
            raise ClientError("Tagging key is too long")

        if len(value) > _MAX_OBJECT_TAGGING_VALUE_LENGTH:
            raise ClientError("Tagging value is too long")

        self.tagging_rule[key] = value

    def delete(self, key):
        del self.tagging_rule[key]

    def len(self):
        return len(self.tagging_rule)

    def to_query_string(self):
        query_string = ''

        for key in self.tagging_rule:
            query_string += urlquote(key)
            query_string += '='
            query_string += urlquote(self.tagging_rule[key])
            query_string += '&'

        if len(query_string) == 0:
            return ''
        else:
            query_string = query_string[:-1]

        return query_string

class GetTaggingResult(RequestResult, Tagging):
    
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        Tagging.__init__(self)

SERVER_SIDE_ENCRYPTION_AES256 = 'AES256'
SERVER_SIDE_ENCRYPTION_KMS = 'KMS'

class ServerSideEncryptionRule(object):

    def __init__(self, sse_algorithm=None, kms_master_keyid=None):

        self.sse_algorithm = sse_algorithm
        self.kms_master_keyid = kms_master_keyid

class GetServerSideEncryptionResult(RequestResult, ServerSideEncryptionRule):
    
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        ServerSideEncryptionRule.__init__(self)

class ListObjectVersionsResult(RequestResult):
    def __init__(self, resp):
        super(ListObjectVersionsResult, self).__init__(resp)

        #: True表示还有更多的文件可以罗列；False表示已经列举完毕。
        self.is_truncated = False

        #: 本次使用的分页标记符
        self.key_marker = ''

        #: 下一次罗列的分页标记符，即，可以作为 :func:`list_object_versions <oss2.Bucket.list_object_versions>` 的 `key_marker` 参数。
        self.next_key_marker = ''

        #: 本次使用的versionid分页标记符
        self.versionid_marker = ''

        #: 下一次罗列的versionid分页标记符，即，可以作为 :func:`list_object_versions <oss2.Bucket.list_object_versions>` 的 `versionid_marker` 参数。
        self.next_versionid_marker = ''

        self.name = ''
        
        self.owner = ''

        self.prefix = ''

        self.max_keys = ''

        self.delimiter = ''

        #: 本次罗列得到的delete marker列表。其中元素的类型为 :class:`DeleteMarkerInfo` 。
        self.delete_marker = []

        #: 本次罗列得到的文件version列表。其中元素的类型为 :class:`ObjectVersionInfo` 。
        self.versions = []

        self.common_prefix = []

class DeleteMarkerInfo(object):
    def __init__(self):
        self.key = ''
        self.versionid = ''
        self.is_latest = False
        self.last_modified = ''
        self.owner = Owner('', '')

class ObjectVersionInfo(object):
    def __init__(self):
        self.key = ''
        self.versionid = ''
        self.is_latest = False
        self.last_modified = ''
        self.owner = Owner('', '')
        self.type = ''
        self.storage_class = ''
        self.size = ''
        self.etag = ''

BUCKET_VERSIONING_ENABLE = 'Enabled'
BUCKET_VERSIONING_SUSPEND = 'Suspended'

class BucketVersioningConfig(object):
    def __init__(self, status=None):
        self.status = status

class GetBucketVersioningResult(RequestResult, BucketVersioningConfig):
    def __init__(self, resp):
        RequestResult.__init__(self,resp)
        BucketVersioningConfig.__init__(self) 

class GetBucketPolicyResult(RequestResult):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        self.policy = to_string(resp.read())

class GetBucketRequestPaymentResult(RequestResult):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        self.payer = ''

class BucketQosInfo(object):
    """bucket的Qos信息    
    :以下参数如果设置为0则表示完全禁止指定类型的访问，如果为-1则表示不单独限制

    :param total_upload_bw: 总上传带宽, 单位Gbps
    :type total_upload_bw: int

    :param intranet_upload_bw: 内网上传带宽, 单位Gbps
    :type intranet_upload_bw: int

    :param extranet_upload_bw: 外网上传带宽, 单位Gbps
    :type extranet_upload_bw: int

    :param total_download_bw: 总下载带宽, 单位Gbps
    :type total_download_bw: int

    :param intranet_download_bw: 内外下载带宽, 单位Gbps
    :type intranet_download_bw: int

    :param extranet_download_bw: 外网下载带宽, 单位Gbps
    :type extranet_download_bw: int

    :param total_qps: 总qps, 单位请求数/s
    :type total_qps: int

    :param intranet_qps: 内网访问qps, 单位请求数/s
    :type intranet_qps: int

    :param extranet_qps: 外网访问qps, 单位请求数/s
    :type extranet_qps: int
    """
    def __init__(self,
            total_upload_bw = None,
            intranet_upload_bw = None,
            extranet_upload_bw = None,
            total_download_bw = None,
            intranet_download_bw = None,
            extranet_download_bw = None,
            total_qps = None,
            intranet_qps = None,
            extranet_qps = None):

        self.total_upload_bw = total_upload_bw
        self.intranet_upload_bw = intranet_upload_bw
        self.extranet_upload_bw = extranet_upload_bw
        self.total_download_bw = total_download_bw
        self.intranet_download_bw = intranet_download_bw
        self.extranet_download_bw = extranet_download_bw
        self.total_qps = total_qps
        self.intranet_qps = intranet_qps
        self.extranet_qps = extranet_qps

class UserQosInfo(object):
    """User的Qos信息    

    :param region: 查询的qos配置生效的区域
    :type region: str

    :以下参数如果为0则表示完全禁止指定类型的访问，如果为-1表示不单独限制

    :param total_upload_bw: 总上传带宽, 单位Gbps
    :type total_upload_bw: int

    :param intranet_upload_bw: 内网上传带宽, 单位:Gbps
    :type intranet_upload_bw: int

    :param extranet_upload_bw: 外网上传带宽, 单位:Gbps
    :type extranet_upload_bw: int

    :param total_download_bw: 总下载带宽, 单位:Gbps
    :type total_download_bw: int

    :param intranet_download_bw: 内外下载带宽, 单位:Gbps
    :type intranet_download_bw: int

    :param extranet_download_bw: 外网下载带宽, 单位:Gbps
    :type extranet_download_bw: int

    :param total_qps: 总qps限制
    :type total_qps: int

    :param intranet_qps: 内网访问qps
    :type intranet_qps: int

    :param extranet_qps: 外网访问qps
    :type extranet_qps: int
    """
    def __init__(self, 
            region=None,
            total_upload_bw = None,
            intranet_upload_bw = None,
            extranet_upload_bw = None,
            total_download_bw = None,
            intranet_download_bw = None,
            extranet_download_bw = None,
            total_qps = None,
            intranet_qps = None,
            extranet_qps = None):

        self.region = region
        self.total_upload_bw = total_upload_bw
        self.intranet_upload_bw = intranet_upload_bw
        self.extranet_upload_bw = extranet_upload_bw
        self.total_download_bw = total_download_bw
        self.intranet_download_bw = intranet_download_bw
        self.extranet_download_bw = extranet_download_bw
        self.total_qps = total_qps
        self.intranet_qps = intranet_qps
        self.extranet_qps = extranet_qps

class GetUserQosInfoResult(RequestResult, UserQosInfo):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        UserQosInfo.__init__(self)

class GetBucketQosInfoResult(RequestResult, BucketQosInfo):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        BucketQosInfo.__init__(self)

class BucketUserQos(object):
    """用户服务质量。
    :param int storage_capacity: 容量大小，单位GB
    """
    def __init__(self, storage_capacity=None):
        self.storage_capacity = storage_capacity

class GetBucketUserQosResult(RequestResult, BucketUserQos):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        BucketUserQos.__init__(self)


ASYNC_FETCH_TASK_STATE_RUNNING = 'Running'
ASYNC_FETCH_TASK_STATE_RETRY = 'Retry'
ASYNC_FETCH_TASK_STATE_FETCH_SUCCESS_CALLBACK_FAILED = 'FetchSuccessCallbackFailed'
ASYNC_FETCH_TASK_STATE_FAILED= 'Failed'
ASYNC_FETCH_TASK_STATE_SUCCESS = 'Success'

class AsyncFetchTaskConfiguration(object):
    """异步获取文件到bucket到任务配置项

    :param url: 源文件url
    :type url: str

    :param object_name: 文件的名称。
    :type task_state: str

    :param host: 文件所在服务器的host，如果不指定则会根据url解析填充。
    :type host: str

    :param content_md5: 指定校验源文件的md5
    :type content_md5: str

    :param callback: 指定fetch成功知乎回调给用户的引用服务器，如果不指定则不回调。
            callback格式与OSS上传回调的请求头callback一致，详情见官网。
    :type callback: str

    :param ignore_same_key: 默认为True表示如果文件已存在则忽略本次任务，api调用将会报错。如果为False，则会覆盖已存在的object。
    :type ignore_same_key: bool
    """
    def __init__(self, 
            url, 
            object_name,
            host = None,
            content_md5 = None,
            callback = None,
            ignore_same_key = None):

        self.url = url
        self.object_name = object_name
        self.host = host
        self.content_md5 = content_md5
        self.callback = callback
        self.ignore_same_key = ignore_same_key

class PutAsyncFetchTaskResult(RequestResult):
    def __init__(self, resp, task_id=None):
        RequestResult.__init__(self, resp)
        self.task_id = task_id

class GetAsyncFetchTaskResult(RequestResult):
    """获取异步获取文件到bucket的任务的返回结果

    :param task_id: 任务id
    :type task_id: str

    :param task_state: 取值范围：oss2.models.ASYNC_FETCH_TASK_STATE_RUNNING, oss2.models.ASYNC_FETCH_TASK_STATE_RETRY, 
            oss2.models.ASYNC_FETCH_TASK_STATE_FETCH_SUCCESS_CALLBACK_FAILED, oss2.models.ASYNC_FETCH_TASK_STATE_FAILED, 
            oss2.models.ASYNC_FETCH_TASK_STATE_SUCCESS。
    :type task_state: str

    :param error_msg: 错误信息
    :type error_msg: str

    :param task_config: 任务配置信息
    :type task_config: class:`AsyncFetchTaskConfiguration <oss2.models.AsyncFetchTaskConfiguration>`
    """
    def __init__(self, resp, 
            task_id=None, 
            task_state=None, 
            error_msg=None, 
            task_config=None):

        RequestResult.__init__(self, resp)
        self.task_id = task_id
        self.task_state = task_state
        self.error_msg = error_msg
        self.task_config = task_config
