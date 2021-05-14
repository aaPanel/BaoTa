# -*- coding: utf-8 -*-
'''
Qiniu Resource Storage SDK for Python
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For detailed document, please see:
<https://developer.qiniu.com/kodo/sdk/1242/python>
'''

# flake8: noqa

__version__ = '7.2.4'

from .auth import Auth, QiniuMacAuth

from .config import set_default
from .zone import Zone
from .region import Region

from .services.storage.bucket import BucketManager, build_batch_copy, build_batch_rename, build_batch_move, \
    build_batch_stat, build_batch_delete
from .services.storage.uploader import put_data, put_file, put_stream
from .services.cdn.manager import CdnManager, create_timestamp_anti_leech_url, DomainManager
from .services.processing.pfop import PersistentFop
from .services.processing.cmd import build_op, pipe_cmd, op_save
from .services.compute.app import AccountClient
from .services.compute.qcos_api import QcosClient

from .services.pili.rtc_server_manager import RtcServer, get_room_token

from .utils import urlsafe_base64_encode, urlsafe_base64_decode, etag, entry
