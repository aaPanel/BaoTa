#!/usr/bin/python
# coding:utf-8

import socket
import random
import re
import sys

class fastcgi_client:
    __FCGI_VERSION = 1

    __FCGI_ROLE_RESPONDER = 1
    __FCGI_ROLE_AUTHORIZER = 2
    __FCGI_ROLE_FILTER = 3

    __FCGI_TYPE_BEGIN = 1
    __FCGI_TYPE_ABORT = 2
    __FCGI_TYPE_END = 3
    __FCGI_TYPE_PARAMS = 4
    __FCGI_TYPE_STDIN = 5
    __FCGI_TYPE_STDOUT = 6
    __FCGI_TYPE_STDERR = 7
    __FCGI_TYPE_DATA = 8
    __FCGI_TYPE_GETVALUES = 9
    __FCGI_TYPE_GETVALUES_RESULT = 10
    __FCGI_TYPE_UNKOWNTYPE = 11

    __FCGI_HEADER_SIZE = 8

    FCGI_STATE_SEND = 1
    FCGI_STATE_ERROR = 2
    FCGI_STATE_SUCCESS = 3

    def __init__(self, host, port, timeout, keepalive):
        self.host = host
        self.port = port
        self.timeout = timeout
        if keepalive:
            self.keepalive = 1
        else:
            self.keepalive = 0
        self.sock = None
        self.requests = dict()

    def __connect(self):
        if self.port == None:
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        else:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            if self.port != None:
                self.sock.connect((self.host, int(self.port)))
            else:
                self.sock.connect(self.host)
        except socket.error as msg:
            self.sock.close()
            self.sock = None
            print(repr(msg))
            return False
        return True

    def _chr(self,num):
        if sys.version_info[0] == 3:
            return chr(num).encode('latin1')
        return chr(num)

    def _ord(self,sbody):
        if sys.version_info[0] == 3:
            return sbody
        return ord(sbody)

    def __encodeFastCGIRecord(self, fcgi_type, content, requestid):
        if type(content) == str: content = content.encode()
        length = len(content)

        return self._chr(self.__FCGI_VERSION) \
               + self._chr(fcgi_type) \
               + self._chr((requestid >> 8) & 0xFF) \
               + self._chr(requestid & 0xFF) \
               + self._chr((length >> 8) & 0xFF) \
               + self._chr(length & 0xFF) \
               + self._chr(0) \
               + self._chr(0) \
               + content

    def __encodeNameValueParams(self, name, value):
        nLen = len(str(name))
        vLen = len(str(value))
        record = b''
        if nLen < 128:
            record += self._chr(nLen)
        else:
            record += self._chr((nLen >> 24) | 0x80) \
                      + self._chr((nLen >> 16) & 0xFF) \
                      + self._chr((nLen >> 8) & 0xFF) \
                      + self._chr(nLen & 0xFF)
        if vLen < 128:
            record += self._chr(vLen)
        else:
            record += self._chr((vLen >> 24) | 0x80) \
                      + self._chr((vLen >> 16) & 0xFF) \
                      + self._chr((vLen >> 8) & 0xFF) \
                      + self._chr(vLen & 0xFF)
        return record + str(name).encode() + str(value).encode()

    def __decodeFastCGIHeader(self, stream):
        header = dict()
        header['version'] = self._ord(stream[0])
        header['type'] = self._ord(stream[1])
        header['requestId'] = (self._ord(stream[2]) << 8) + self._ord(stream[3])
        header['contentLength'] = (self._ord(stream[4]) << 8) + self._ord(stream[5])
        header['paddingLength'] = self._ord(stream[6])
        header['reserved'] = self._ord(stream[7])
        return header

    def __decodeFastCGIRecord(self):
        header = self.sock.recv(int(self.__FCGI_HEADER_SIZE))
        if not header:
            return False
        else:
            record = self.__decodeFastCGIHeader(header)
            record['content'] = b''
            if 'contentLength' in record.keys():
                contentLength = int(record['contentLength'])
                buffer = self.sock.recv(contentLength)

                while contentLength and buffer:
                    contentLength -= len(buffer)
                    record['content'] += buffer
            if 'paddingLength' in record.keys():
                skiped = self.sock.recv(int(record['paddingLength']))
            return record

    def request(self, nameValuePairs={}, post=''):
        if not self.__connect():
            raise Exception('连接服务失败,请检查指定服务是否启动!')
            return

        requestId = random.randint(1, (1 << 16) - 1)
        self.requests[requestId] = dict()
        request = b""
        beginFCGIRecordContent = self._chr(0) \
                                 + self._chr(self.__FCGI_ROLE_RESPONDER) \
                                 + self._chr(self.keepalive) \
                                 + self._chr(0) * 5
        request += self.__encodeFastCGIRecord(self.__FCGI_TYPE_BEGIN,
                                              beginFCGIRecordContent, requestId)

        paramsRecord = b''

        if nameValuePairs:
            v_items = sorted(nameValuePairs.items())
            for (name, value) in v_items:
                paramsRecord += self.__encodeNameValueParams(name, value)


        if paramsRecord:
            request += self.__encodeFastCGIRecord(self.__FCGI_TYPE_PARAMS, paramsRecord, requestId)

        request += self.__encodeFastCGIRecord(self.__FCGI_TYPE_PARAMS, b'', requestId)

        if post:
            request += self.__encodeFastCGIRecord(self.__FCGI_TYPE_STDIN, post, requestId)
        request += self.__encodeFastCGIRecord(self.__FCGI_TYPE_STDIN, b'', requestId)

        self.sock.send(request)
        self.requests[requestId]['state'] = self.FCGI_STATE_SEND
        self.requests[requestId]['response'] = b''
        return self.__waitForResponse(requestId)

    def __waitForResponse(self, requestId):
        while True:
            response = self.__decodeFastCGIRecord()
            if not response:
                break
            if response['type'] == self.__FCGI_TYPE_STDOUT \
                    or response['type'] == self.__FCGI_TYPE_STDERR:
                if response['type'] == self.__FCGI_TYPE_STDERR:
                    self.requests['state'] = self.FCGI_STATE_ERROR
                if requestId == int(response['requestId']):
                    self.requests[requestId]['response'] += response['content']
            if response['type'] == self.FCGI_STATE_SUCCESS:
                self.requests[requestId]
        if self.requests[requestId]['response'].find(b'\r\n\r\n') != -1:
            tmp = b""
            tmp2 = self.requests[requestId]['response'].split(b'\r\n\r\n')
            for i in range(len(tmp2)):
                if i == 0: continue
                tmp += tmp2[i] + b'\r\n\r\n'
            self.requests[requestId]['response'] = tmp.strip()
        return self.requests[requestId]['response']

    def __repr__(self):
        return "fastcgi connect host:{} port:{}".format(self.host, self.port)




