# -*- coding: utf-8 -*-

import threading
import sys
import logging

logger = logging.getLogger(__name__)

try:
    import Queue as queue
except ImportError:
    import queue

import traceback


class TaskQueue(object):
    def __init__(self, producer, consumers):
        self.__producer = producer
        self.__consumers = consumers

        self.__threads = []

        # must be an infinite queue, otherwise producer may be blocked after all consumers being dead.
        self.__queue = queue.Queue()

        self.__lock = threading.Lock()
        self.__exc_info = None
        self.__exc_stack = ''

    def run(self):
        self.__add_and_run(threading.Thread(target=self.__producer_func))

        for c in self.__consumers:
            self.__add_and_run(threading.Thread(target=self.__consumer_func, args=(c,)))

        # give KeyboardInterrupt chances to happen by joining with timeouts.
        while self.__any_active():
            for t in self.__threads:
                t.join(1)

        if self.__exc_info:
            logger.error('An exception was thrown by producer or consumer, backtrace: {0}'.format(self.__exc_stack))
            raise self.__exc_info[1]

    def put(self, data):
        assert data is not None
        self.__queue.put(data)

    def get(self):
        return self.__queue.get()

    def ok(self):
        with self.__lock:
            return self.__exc_info is None

    def __add_and_run(self, thread):
        thread.daemon = True
        thread.start()
        self.__threads.append(thread)

    def __any_active(self):
        return any(t.is_alive() for t in self.__threads)

    def __producer_func(self):
        try:
            self.__producer(self)
        except:
            self.__on_exception(sys.exc_info())
            self.__put_end()
        else:
            self.__put_end()

    def __consumer_func(self, consumer):
        try:
            consumer(self)
        except:
            self.__on_exception(sys.exc_info())

    def __put_end(self):
        for i in range(len(self.__consumers)):
            self.__queue.put(None)

    def __on_exception(self, exc_info):
        with self.__lock:
            if self.__exc_info is None:
                self.__exc_info = exc_info
                self.__exc_stack = traceback.format_exc()



