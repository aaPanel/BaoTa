# -*- coding: utf-8 -*-
import collections
import hashlib
import logging
import os
import errno

from requests.packages.urllib3.fields import guess_content_type
from .modules.sign import decode_msg

from .modules.compat import b, stringify
from .modules.exception import UpYunResumeTraceException, UpYunServiceException

try:
    import simplejson as json
except (ImportError, SyntaxError):
    import json

TEMP_DIR = '.up-python-resume'
DEFAULT_CHUNKSIZE = 8192
THRESHOLD = 5 * 1024 * 1024
PART_SIZE = 1024 * 1024
log = logging.getLogger(__name__)


class BaseStore(object):
    @staticmethod
    def get_key(service, key, filename):
        return hashlib.md5(b('{0}-{1}-{2}'.format(
            service, key, filename))).hexdigest()

    def get(self, key):
        raise NotImplementedError("get method not found")

    def set(self, key, value):
        raise NotImplementedError("set method not found")

    def delete(self, key):
        raise NotImplementedError("delete method not found")


class FileStore(BaseStore):
    """
    :param directory: 存储路径, 默认为'~/.up-python-resume/'
    """
    def __init__(self, directory=None):
        self.dir = directory or os.path.join(os.path.expanduser('~'), TEMP_DIR)

        if os.path.isdir(self.dir):
            return
        else:
            os.makedirs(self.dir)

    def get(self, key):
        file_path = os.path.join(self.dir, key)
        if not os.path.exists(file_path):
            return {}
        try:
            with open(file_path, 'r') as f:
                content = stringify(json.load(f))
        except ValueError:
            os.remove(file_path)
            return {}
        else:
            if not isinstance(content, dict):
                os.remove(file_path)
                return {}
            else:
                return content

    def set(self, key, value):
        file_path = os.path.join(self.dir, key)
        with open(file_path, 'w') as f:
            json.dump(value, f)

    def delete(self, key):
        file_path = os.path.join(self.dir, key)
        try:
            os.remove(file_path)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise e


class MemoryStore(BaseStore):
    def __init__(self):
        self.dict = {}

    def get(self, key):
        if key in self.dict:
            value = self.dict[key]
            if not isinstance(value, dict):
                self.delete(key)
                return {}
            else:
                return self.dict[key]
        else:
            return {}

    def set(self, key, value):
        self.dict[key] = value

    def delete(self, key):
        self.dict.pop(key, None)


memory_store = MemoryStore()


class ResumeTrace(object):
    def __init__(self, service, key, filename, file_md5, file_size,
                 store=None):
        self.store = store if store else memory_store
        self.file_md5 = file_md5
        self.file_size = file_size
        self.store_key = self.store.get_key(service, key, filename)
        self.record = UpYunRecord(self.store.get(self.store_key))
        try:
            self.check(self.record)
        except UpYunResumeTraceException:
            self.delete()

    def check(self, record):
        if not record:
            return

        if not isinstance(record, UpYunRecord):
            raise UpYunResumeTraceException(
                msg="get value error:" + str(record))

        if not isinstance(record.next_id, int):
            raise UpYunResumeTraceException(msg="next_id error")
        elif record.next_id == -1:
            raise UpYunResumeTraceException(msg="old file recode not deleted")

        for key in ("start", "end"):
            if not isinstance(record.get(key), int):
                raise UpYunResumeTraceException(msg="{} error".format(key))

        if not isinstance(record.multi_uuid, str):
            raise UpYunResumeTraceException(msg="multi_uuid error")

        if self.file_md5 != record.file_md5:
            raise UpYunResumeTraceException(msg="file md5 changed")

        if self.file_size != record.file_size:
            raise UpYunResumeTraceException(msg="file size changed")

    def get(self):
        return self.record

    def commit(self):
        if self.record and self.record.next_id != -1:
            self.store.set(self.store_key, self.record)
        else:
            self.delete()

    def delete(self):
        self.store.delete(self.store_key)
        self.record = UpYunRecord()

    def __enter__(self):
        return self.record

    def __exit__(self, exc_type, exc_val, exc_tb):
        log.debug("{0:>20}, next_id:{1:>10}, uuid:{2}".format(
            "commit record", self.record.next_id, self.record.multi_uuid))
        self.commit()


class UpYunRecord(dict):
    def __init__(self, *arg, **kw):
        super(UpYunRecord, self).__init__(*arg, **kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            return None

    def __setattr__(self, key, value):
        self[key] = value


class SizedFile(object):
    def __init__(self, file_object, start, end):
        self.file_object = file_object
        self.end = end
        self.start = start
        self.size = end - start
        self.offset = 0

    def reset(self):
        self.file_object.seek(self.start, os.SEEK_SET)
        self.offset = 0

    def read(self, chunk=None):
        if self.offset >= self.size:
            return b''

        if (chunk is None or chunk < 0) or (chunk + self.offset >= self.size):
            data = self.file_object.read(self.size - self.offset)
            self.offset = self.size
            return data

        self.offset += chunk
        return self.file_object.read(chunk)

    def __len__(self):
        return self.size

    def get_md5(self, chunksize=DEFAULT_CHUNKSIZE):
        md5 = hashlib.md5()
        for chunk in iter(lambda: self.read(chunksize), b''):
            md5.update(chunk)
        self.reset()
        return md5.hexdigest()


class BaseReporter(object):
    def __call__(self, uploaded_size, total_size, done):
        raise NotImplementedError('Reporter must be callable')


class PrintReporter(BaseReporter):
    def __call__(self, uploaded_size, total_size, done):
        if not done:
            print("reporter: {0:.2f}%".format(
                uploaded_size * 1.0 / total_size))
        else:
            print("reporter: Done")


print_reporter = PrintReporter()


class UpYunResume(object):
    """断点续传
    :param rest: upyun rest 实例
    :param key: upyun 文件名
    :param f: file object
    :param file_size: 文件大小
    :param headers: 传给 `initiate_upload` 的 HTTP 头部
    :param checksum: 默认 False，表示不进行 MD5 校验
    :param store: BaseStore 实例, 默认采用 memory_store
    """

    def __init__(self, rest, key, f, file_size,
                 headers=None, checksum=False, store=None,
                 reporter=None, part_size=None):
        self.key = key
        self.rest = rest
        self.f = f
        self.file_size = file_size
        self.part_size = part_size
        if not part_size:
            self.part_size = PART_SIZE
        self.file_md5 = self.make_md5() if checksum else ""
        self.trace = ResumeTrace(self.rest.service, key, f.name,
                                 self.file_md5, file_size, store)
        self.headers = headers or {}
        self.checksum = checksum
        self.init_headers(f.name)
        self.progress_reporter = reporter

    def make_md5(self, chunksize=DEFAULT_CHUNKSIZE):
        md5 = hashlib.md5()
        for chunk in iter(lambda: self.f.read(chunksize), b''):
            md5.update(chunk)
        self.f.seek(0)
        return decode_msg(md5.hexdigest())

    def init_headers(self, filename):
        if "X-Upyun-Multi-Type" not in self.headers:
            self.headers["X-Upyun-Multi-Type"] = guess_content_type(filename)
        self.headers["X-Upyun-Multi-Length"] = str(self.trace.file_size)
        self.headers["X-Upyun-Multi-Stage"] = "initiate,upload"
        self.headers["X-Upyun-Part-Id"] = "0"
        self.headers["X-Upyun-Multi-Part-Size"] = str(self.part_size)

    def set_record(self, record, headers):
        next_id = None
        headers = headers or []
        for header in headers:
            try:
                if 'x-upyun-next-part-id' == header[0].lower():
                    next_id = int(header[1])
                    log.debug(
                        "get {next_id} from headers".format(next_id=next_id))
                    break
            except (ValueError, KeyError, AttributeError):
                pass

        if next_id is None:
            record.clear()
        elif next_id == -1:
            record.start = self.file_size
            record.end = self.file_size
        else:
            record.start = next_id * self.part_size
            if record.start + self.part_size > self.file_size:
                record.end = self.file_size
            else:
                record.end = record.start + self.part_size
            record.next_id = next_id
        return next_id

    def get_request(self, record):
        headers = {}
        if record:
            log.debug("{0:>20}, next_id:{1:>10}".format(
                "load record", record.next_id))

            if record.start != self.file_size:
                headers.update({"X-Upyun-Multi-Uuid": record.multi_uuid,
                                "X-Upyun-Part-Id": str(record.next_id),
                                "X-Upyun-Multi-Stage": "upload"})
            else:
                headers.update({"X-Upyun-Multi-Uuid": record.multi_uuid})
        else:
            log.debug("init file")
            record.update({
                "next_id": 0, "file_size": self.file_size,
                "file_md5": self.file_md5, "start": 0,
                "end": self.part_size if self.part_size < self.file_size
                else self.file_size})
            headers.update(self.headers)

        if record.end == self.file_size:
            log.debug("complete file")
            stage = headers.get("X-Upyun-Multi-Stage", "")
            headers["X-Upyun-Multi-Stage"] = \
                stage + ",complete" if stage else "complete"
            if self.checksum:
                headers["X-Upyun-Multi-MD5"] = self.file_md5
        self.f.seek(record.start, os.SEEK_SET)
        value = SizedFile(self.f, record.start, record.end)
        if self.checksum:
            headers["Content-MD5"] = value.get_md5()
        log.debug("{0:>20}, part_id:{1:>10}, uuid:{2}".format(
            "upload file", record.next_id, record.multi_uuid))
        return dict(method="PUT", headers=headers, key=self.key, value=value)

    def step(self, res, record):
        if not record.multi_uuid:
            for header in res:
                if 'x-upyun-multi-uuid' == header[0].lower():
                    record.multi_uuid = header[1]
                    break

        if record.end == self.file_size:
            record.next_id = -1
            log.debug("upload done")
            return True
        else:
            record.start = record.end
            if record.start + self.part_size > self.file_size:
                record.end = self.file_size
            else:
                record.end = record.start + self.part_size
            record.next_id += 1
            return False

    def upload(self):
        while True:
            with self.trace as record:
                req = self.get_request(record)
                try:
                    res = self.rest.do_http_request(**req)
                except UpYunServiceException as e:
                    try:
                        reason = stringify(json.loads(e.err))
                    except (ValueError, TypeError, AttributeError):
                        raise e
                    else:
                        if reason['msg'] == "part id error":
                            next_id = self.set_record(record, e.headers)
                            if next_id is None:
                                raise e
                        elif reason['msg'] == "part already complete":
                            record.start = self.file_size
                            record.end = self.file_size
                        elif reason['msg'] == "file already upload":
                            record.next_id = -1
                            return e.headers
                        elif reason['msg'] in (
                                "x-upyun-multi-uuid not found",
                                "file md5 not match"):
                            log.debug(reason['msg'])
                            record.clear()
                            raise e
                        else:
                            raise e
                else:
                    done = self.step(res, record)
                    if isinstance(
                            self.progress_reporter, collections.Callable):
                        self.progress_reporter(
                            record.start or 0, self.file_size, done)
                    if done:
                        return res
