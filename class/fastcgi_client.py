#!/usr/bin/python
# coding:utf-8

import socket
import random
import re


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

    def __encodeFastCGIRecord(self, fcgi_type, content, requestid):
        length = len(content)
        return chr(self.__FCGI_VERSION) \
               + chr(fcgi_type) \
               + chr((requestid >> 8) & 0xFF) \
               + chr(requestid & 0xFF) \
               + chr((length >> 8) & 0xFF) \
               + chr(length & 0xFF) \
               + chr(0) \
               + chr(0) \
               + content

    def __encodeNameValueParams(self, name, value):
        nLen = len(str(name))
        vLen = len(str(value))
        record = ''
        if nLen < 128:
            record += chr(nLen)
        else:
            record += chr((nLen >> 24) | 0x80) \
                      + chr((nLen >> 16) & 0xFF) \
                      + chr((nLen >> 8) & 0xFF) \
                      + chr(nLen & 0xFF)
        if vLen < 128:
            record += chr(vLen)
        else:
            record += chr((vLen >> 24) | 0x80) \
                      + chr((vLen >> 16) & 0xFF) \
                      + chr((vLen >> 8) & 0xFF) \
                      + chr(vLen & 0xFF)
        return record + str(name) + str(value)

    def __decodeFastCGIHeader(self, stream):
        header = dict()
        header['version'] = ord(stream[0])
        header['type'] = ord(stream[1])
        header['requestId'] = (ord(stream[2]) << 8) + ord(stream[3])
        header['contentLength'] = (ord(stream[4]) << 8) + ord(stream[5])
        header['paddingLength'] = ord(stream[6])
        header['reserved'] = ord(stream[7])
        return header

    def __decodeFastCGIRecord(self):
        header = self.sock.recv(int(self.__FCGI_HEADER_SIZE))
        if not header:
            return False
        else:
            record = self.__decodeFastCGIHeader(header)
            record['content'] = ''
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
        request = ""
        beginFCGIRecordContent = chr(0) \
                                 + chr(self.__FCGI_ROLE_RESPONDER) \
                                 + chr(self.keepalive) \
                                 + chr(0) * 5
        request += self.__encodeFastCGIRecord(self.__FCGI_TYPE_BEGIN,
                                              beginFCGIRecordContent, requestId)
        paramsRecord = ''
        if nameValuePairs:
            for (name, value) in nameValuePairs.iteritems():
                paramsRecord += self.__encodeNameValueParams(name, value)
        if paramsRecord:
            request += self.__encodeFastCGIRecord(self.__FCGI_TYPE_PARAMS, paramsRecord, requestId)
        request += self.__encodeFastCGIRecord(self.__FCGI_TYPE_PARAMS, '', requestId)

        if post:
            request += self.__encodeFastCGIRecord(self.__FCGI_TYPE_STDIN, post, requestId)
        request += self.__encodeFastCGIRecord(self.__FCGI_TYPE_STDIN, '', requestId)
        self.sock.send(request)
        self.requests[requestId]['state'] = self.FCGI_STATE_SEND
        self.requests[requestId]['response'] = ''
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
        if self.requests[requestId]['response'].find('\r\n\r\n') != -1:
            tmp = ""
            tmp2 = self.requests[requestId]['response'].split('\r\n\r\n')
            for i in range(len(tmp2)):
                if i == 0: continue
                tmp += tmp2[i] + '\r\n\r\n'
            self.requests[requestId]['response'] = tmp.strip()
        return self.requests[requestId]['response']

    def __repr__(self):
        return "fastcgi connect host:{} port:{}".format(self.host, self.port)
