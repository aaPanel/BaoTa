from mod.project.proxy.base import StreamRequest, StreamProxy, Message


class UDPProxy(StreamProxy):

    name = 'udp'

    def __init__(self):
        super().__init__()

    def create(self, request: StreamRequest):
        self.file_name = '{}_udp.conf'.format(request.listen)
        request.listen = request.listen + ' udp'
        if self.data.get(request.listen) is not None:
            raise ValueError(Message.Error.exist.format(protocol=request.protocol, port=request.listen))

        return StreamProxy.create(self, request)

    def delete(self, request: StreamRequest):
        self.file_name = '{}_udp.conf'.format(request.listen)
        request.listen = request.listen + ' udp'
        return StreamProxy.delete(self, request)

    def update(self, request: StreamRequest):
        self.file_name = '{}_udp.conf'.format(request.listen)
        request.listen = request.listen + ' udp'
        return StreamProxy.update(self, request)

    def allow(self, request: StreamRequest):
        self.file_name = '{}_udp.conf'.format(request.listen)
        request.listen = request.listen + ' udp'
        return StreamProxy.allow(self, request)

    def deny(self, request: StreamRequest):
        self.file_name = '{}_udp.conf'.format(request.listen)
        request.listen = request.listen + ' udp'
        return StreamProxy.deny(self, request)

    def delete_list(self, request: StreamRequest):
        request.listen = request.listen + ' udp'
        return StreamProxy.delete_list(self, request)

    def delete_allow(self, request: StreamRequest):
        self.file_name = '{}_udp.conf'.format(request.listen)
        request.listen = request.listen + ' udp'
        return StreamProxy.delete_allow(self, request)

    def delete_deny(self, request: StreamRequest):
        self.file_name = '{}_udp.conf'.format(request.listen)
        request.listen = request.listen + ' udp'
        return StreamProxy.delete_deny(self, request)

    def log(self, request: StreamRequest):
        self.file_name = '{}_udp.conf'.format(request.listen)
        request.listen = request.listen + ' udp'
        return StreamProxy.log(self, request)

    def port(self, request: StreamRequest):
        self.file_name = '{}_udp.conf'.format(request.listen)
        request.listen = request.listen + ' udp'
        return StreamProxy.port(self, request)