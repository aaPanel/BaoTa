# -*- coding: utf-8 -*-

from qiniu import config
from qiniu import http


class PersistentFop(object):
    """持久化处理类

    该类用于主动触发异步持久化操作，具体规格参考：
    http://developer.qiniu.com/docs/v6/api/reference/fop/pfop/pfop.html

    Attributes:
        auth:       账号管理密钥对，Auth对象
        bucket:     操作资源所在空间
        pipeline:   多媒体处理队列，详见 https://portal.qiniu.com/mps/pipeline
        notify_url: 持久化处理结果通知URL
    """

    def __init__(self, auth, bucket, pipeline=None, notify_url=None):
        """初始化持久化处理类"""
        self.auth = auth
        self.bucket = bucket
        self.pipeline = pipeline
        self.notify_url = notify_url

    def execute(self, key, fops, force=None):
        """执行持久化处理:

        Args:
            key:    待处理的源文件
            fops:   处理详细操作，规格详见 https://developer.qiniu.com/dora/manual/1291/persistent-data-processing-pfop
            force:  强制执行持久化处理开关

        Returns:
            一个dict变量，返回持久化处理的persistentId，类似{"persistentId": 5476bedf7823de4068253bae};
            一个ResponseInfo对象
        """
        ops = ';'.join(fops)
        data = {'bucket': self.bucket, 'key': key, 'fops': ops}
        if self.pipeline:
            data['pipeline'] = self.pipeline
        if self.notify_url:
            data['notifyURL'] = self.notify_url
        if force == 1:
            data['force'] = 1

        url = '{0}/pfop'.format(config.get_default('default_api_host'))
        return http._post_with_auth(url, data, self.auth)
