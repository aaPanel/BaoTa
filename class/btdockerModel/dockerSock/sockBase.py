class dockerSock(object):
    def __init__(self):
        self._sock = "/var/run/docker.sock"
        self._url = "unix://{}".format(self._sock)
        self._api_version = "/127.0.0.1"

    def get_sock(self):
        return self._sock

    def get_url(self):
        return self._url

    def get_api_version(self):
        return self._api_version


class base(dockerSock):
    def __init__(self):
        super(base, self).__init__()
