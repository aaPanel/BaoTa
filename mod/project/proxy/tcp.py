import sys

from mod.project.proxy import tools
from mod.project.proxy.base import StreamRequest, StreamProxy, Message

if "/www/server/panel/class" not in sys.path:
    sys.path.append('/www/server/panel/class')

import public


class TCPProxy(StreamProxy):
    name = 'tcp'

    def __init__(self):
        super().__init__()

    def create(self, request: StreamRequest):
        if self.data.get(request.listen) is not None:
            raise ValueError(Message.Error.exist.format(protocol=request.protocol, port=request.listen))
        self.file_name = '{}.conf'.format(request.listen)
        public.print_log(tools.to_dict(request))
        return StreamProxy.create(self, request)

    def delete(self, request: StreamRequest):
        self.file_name = '{}.conf'.format(request.listen)
        return StreamProxy.delete(self, request)

    def update(self, request: StreamRequest):
        self.file_name = '{}.conf'.format(request.listen)
        return StreamProxy.update(self, request)

    def delete_list(self, request: StreamRequest):
        return StreamProxy.delete_list(self, request)

    def allow(self, request: StreamRequest):
        self.file_name = '{}.conf'.format(request.listen)
        return StreamProxy.allow(self, request)

    def deny(self, request: StreamRequest):
        self.file_name = '{}.conf'.format(request.listen)
        return StreamProxy.deny(self, request)

    def delete_deny(self, request: StreamRequest):
        self.file_name = '{}.conf'.format(request.listen)
        return StreamProxy.delete_deny(self, request)

    def delete_allow(self, request: StreamRequest):
        self.file_name = '{}.conf'.format(request.listen)
        return StreamProxy.delete_allow(self, request)

    def log(self, request: StreamRequest):
        self.file_name = '{}.conf'.format(request.listen)
        return StreamProxy.log(self, request)

    def port(self, request: StreamRequest):
        self.file_name = '{}.conf'.format(request.listen)
        return StreamProxy.port(self, request)
