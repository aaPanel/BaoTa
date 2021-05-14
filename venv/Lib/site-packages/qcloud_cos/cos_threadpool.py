# -*- coding: utf-8 -*-

from threading import Thread
from logging import getLogger
from six.moves.queue import Queue
from threading import Lock
import gc
logger = getLogger(__name__)


class WorkerThread(Thread):
    def __init__(self, task_queue, *args, **kwargs):
        super(WorkerThread, self).__init__(*args, **kwargs)

        self._task_queue = task_queue
        self._succ_task_num = 0
        self._fail_task_num = 0
        self._ret = list()

    def run(self):
        while True:
            func, args, kwargs = self._task_queue.get()
            # 判断线程是否需要退出
            if func is None:
                return
            try:
                ret = func(*args, **kwargs)
                self._succ_task_num += 1
                self._ret.append(ret)

            except Exception as e:
                logger.warn(str(e))
                self._fail_task_num += 1
                self._ret.append(e)
            finally:
                self._task_queue.task_done()

    def get_result(self):
        return self._succ_task_num, self._fail_task_num, self._ret


class SimpleThreadPool:

    def __init__(self, num_threads=5, num_queue=0):
        self._num_threads = num_threads
        self._queue = Queue(num_queue)
        self._lock = Lock()
        self._active = False
        self._workers = list()
        self._finished = False

    def add_task(self, func, *args, **kwargs):
        if not self._active:
            with self._lock:
                if not self._active:
                    self._workers = []
                    self._active = True

                    for i in range(self._num_threads):
                        w = WorkerThread(self._queue)
                        self._workers.append(w)
                        w.start()

        self._queue.put((func, args, kwargs))

    def wait_completion(self):
        self._queue.join()
        self._finished = True
        # 已经结束的任务, 需要将线程都退出, 防止卡死
        for i in range(self._num_threads):
            self._queue.put((None, None, None))

        self._active = False

    def get_result(self):
        assert self._finished
        detail = [worker.get_result() for worker in self._workers]
        succ_all = all([tp[1] == 0 for tp in detail])
        return {'success_all': succ_all, 'detail': detail}


if __name__ == '__main__':

    pool = SimpleThreadPool(2)

    def task_sleep(x):
        from time import sleep
        sleep(x)
        return 'hello, sleep %d seconds' % x

    def raise_exception():
        raise ValueError("Pa! Exception!")
    for i in range(1000):
        pool.add_task(task_sleep, 0.001)
        print(i)
    pool.add_task(task_sleep, 0)
    pool.add_task(task_sleep, 0)
    # pool.add_task(raise_exception)
    # pool.add_task(raise_exception)

    pool.wait_completion()
    print(pool.get_result())
    # [(1, 0, ['hello, sleep 5 seconds']), (2, 1, ['hello, sleep 2 seconds', 'hello, sleep 3 seconds', ValueError('Pa! Exception!',)])]
