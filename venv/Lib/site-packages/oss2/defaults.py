# -*- coding: utf-8 -*-

"""
oss2.defaults
~~~~~~~~~~~~~

全局缺省变量。

"""


def get(value, default_value):
    if value is None:
        return default_value
    else:
        return value


#: 连接超时时间
connect_timeout = 60

#: 缺省重试次数
request_retries = 3

#: 对于某些接口，上传数据长度大于或等于该值时，就采用分片上传。
multipart_threshold = 10 * 1024 * 1024

#: 分片上传缺省线程数
multipart_num_threads = 1

#: 缺省分片大小
part_size = 10 * 1024 * 1024


#: 每个Session连接池大小
connection_pool_size = 10


#: 对于断点下载，如果OSS文件大小大于该值就进行并行下载（multiget）
multiget_threshold = 100 * 1024 * 1024

#: 并行下载（multiget）缺省线程数
multiget_num_threads = 4

#: 并行下载（multiget）的缺省分片大小
multiget_part_size = 10 * 1024 * 1024
