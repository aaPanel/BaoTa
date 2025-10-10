from contextlib import contextmanager
import threading


# 存储所有已排序的线程锁
_local = threading.local()


@contextmanager
def acquire(*locks, timeout=-1):
    '''
        @name 避免死锁
        @author Zhj
        @param locks<[]threading.Lock> 线程锁
        @param timeout<integer> 最长阻塞时间/秒
        @return None
    '''
    # 升序排序
    locks = sorted(locks, key=lambda x: id(x))

    # 确保按顺序加锁
    acquired = getattr(_local, 'acquired', [])
    if timeout <= 0 and acquired and max(id(lock) for lock in acquired) >= id(locks[0]):
        raise RuntimeError('Lock Order Violation')

    # 加锁
    acquired.extend(locks)
    _local.acquired = acquired

    try:
        # 按顺序加锁
        for lock in locks:
            lock.acquire(timeout=timeout)

        # 转出程序控制权
        yield
    finally:
        # 倒序释放锁
        for lock in reversed(locks):
            try:
                lock.release()
            except: pass
        del (acquired[-len(locks):],)