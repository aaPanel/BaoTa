# -*- coding: utf-8 -*-

from qiniu import zone

RS_HOST = 'http://rs.qiniu.com'  # 管理操作Host
RSF_HOST = 'http://rsf.qbox.me'  # 列举操作Host
API_HOST = 'http://api.qiniu.com'  # 数据处理操作Host
UC_HOST = 'https://uc.qbox.me'  # 获取空间信息Host

_BLOCK_SIZE = 1024 * 1024 * 4  # 断点续上传分块大小，该参数为接口规格，暂不支持修改

_config = {
    'default_zone': zone.Zone(),
    'default_rs_host': RS_HOST,
    'default_rsf_host': RSF_HOST,
    'default_api_host': API_HOST,
    'default_uc_host': UC_HOST,
    'connection_timeout': 30,  # 链接超时为时间为30s
    'connection_retries': 3,  # 链接重试次数为3次
    'connection_pool': 10,  # 链接池个数为10
}


def get_default(key):
    return _config[key]


def set_default(
        default_zone=None, connection_retries=None, connection_pool=None,
        connection_timeout=None, default_rs_host=None, default_uc_host=None,
        default_rsf_host=None, default_api_host=None):
    if default_zone:
        _config['default_zone'] = default_zone
    if default_rs_host:
        _config['default_rs_host'] = default_rs_host
    if default_rsf_host:
        _config['default_rsf_host'] = default_rsf_host
    if default_api_host:
        _config['default_api_host'] = default_api_host
    if default_uc_host:
        _config['default_uc_host'] = default_api_host
    if connection_retries:
        _config['connection_retries'] = connection_retries
    if connection_pool:
        _config['connection_pool'] = connection_pool
    if connection_timeout:
        _config['connection_timeout'] = connection_timeout
