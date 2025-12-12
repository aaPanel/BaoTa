"""
SQLite专用连接池库
支持线程安全和gevent+greenlet异步环境
"""
import os
import re
import shutil
import sqlite3
import threading
import weakref
import time
from collections import deque
from contextlib import contextmanager
from typing import Optional, Dict, Any, Callable, Union, Generator

try:
    import gevent
    from gevent import local as gevent_local
    from gevent.lock import RLock as GeventRLock
    from gevent.event import Event as GeventEvent

    HAS_GEVENT = True
except ImportError:
    HAS_GEVENT = False
    gevent = None
    gevent_local = None
    GeventRLock = None
    GeventEvent = None


class SQLiteConnectionError(Exception):
    """SQLite连接池相关异常"""
    pass


class SQLiteTimeoutError(SQLiteConnectionError):
    """连接获取超时异常"""
    pass


def detect_async_environment():
    """检测当前运行环境"""
    if HAS_GEVENT and gevent is not None:
        try:
            # 检查是否在gevent上下文中
            gevent.getcurrent()
            return 'gevent'
        except:
            pass
    return 'thread'


class SQLiteConnection:
    """SQLite连接包装器"""

    def __init__(self, pool: 'SQLitePool', connection: sqlite3.Connection,
                 created_at: float):
        self.pool = pool
        self._connection = connection
        self.created_at = created_at
        self.last_used = time.time()
        self.in_use = False
        self._closed = False

    def __enter__(self):
        return self._connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """归还连接到池中"""
        if not self._closed and self.pool:
            self.pool._return_connection(self)

    def invalidate(self):
        """标记连接为无效"""
        self._closed = True
        if self._connection:
            try:
                self._connection.close()
            except:
                pass

    @property
    def connection(self) -> sqlite3.Connection:
        """获取底层sqlite3连接"""
        if self._closed:
            raise SQLiteConnectionError("Connection is closed")
        self.last_used = time.time()
        return self._connection

    def __getattr__(self, name):
        """代理sqlite3.Connection的方法"""
        return getattr(self.connection, name)


class SQLitePool:
    """SQLite连接池基类"""

    def __init__(self,
                 database: str,
                 pool_size: int = 5,
                 max_overflow: int = 10,
                 timeout: float = 30.0,
                 recycle: int = 3600,
                 **connect_args):
        """
        初始化SQLite连接池

        Args:
            database: SQLite数据库文件路径
            pool_size: 池大小
            max_overflow: 最大溢出连接数
            timeout: 获取连接超时时间(秒)
            recycle: 连接回收时间(秒)
            **connect_args: sqlite3.connect的参数
        """
        if database.startswith("sqlite"):
            database = re.sub(r"sqlite[^/]*//", "", database)
        self.database = database
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.timeout = timeout
        self.recycle = recycle
        self.connect_args = connect_args

        # 设置SQLite文件数据库的默认参数
        if database != ':memory:':
            self.connect_args.setdefault('check_same_thread', False)
            self.connect_args.setdefault('timeout', 20.0)
        else:
            # 内存数据库需要共享连接
            self.connect_args.setdefault('check_same_thread', False)

        self._pool = deque()
        self._overflow_count = 0
        self._created_connections = 0

        # 环境适配
        self._env = detect_async_environment()
        self._setup_environment()

    def _setup_environment(self):
        """根据环境设置锁和本地存储"""
        if self._env == 'gevent' and GeventRLock is not None and gevent_local is not None:
            self._lock = GeventRLock()
            self._local = gevent_local.local()
        else:
            self._lock = threading.RLock()
            self._local = threading.local()

    def _create_connection(self) -> sqlite3.Connection:
        """创建新的SQLite连接"""
        try:
            conn = sqlite3.connect(self.database, **self.connect_args)

            # 设置SQLite优化参数
            if self.database != ':memory:':
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA cache_size=-64000")  # 64MB缓存
                conn.execute("PRAGMA temp_store=MEMORY")

            return conn
        except Exception as e:
            if self.database == ':memory:':
                raise SQLiteConnectionError(f"Failed to create connection: {e}")
            print("链接数据库失败，尝试重建数据库")
            os.makedirs(os.path.dirname(self.database), exist_ok=True)
            if os.path.exists(self.database):
                if os.path.exists(self.database + '.bak'):
                    os.remove(self.database + '.bak')
                shutil.move(self.database, self.database + '.bak')
            open(self.database, 'w').close()
            try:
                conn = self._create_connection()
                # 设置SQLite优化参数
                if self.database != ':memory:':
                    conn.execute("PRAGMA journal_mode=WAL")
                    conn.execute("PRAGMA synchronous=NORMAL")
                    conn.execute("PRAGMA cache_size=-64000")  # 64MB缓存
                    conn.execute("PRAGMA temp_store=MEMORY")

                return conn
            except:
                raise SQLiteConnectionError(f"Failed to create connection: {e}")

    def _is_connection_valid(self, conn: sqlite3.Connection,
                             created_at: float) -> bool:
        """检查连接是否有效"""
        # 检查回收时间
        if self.recycle > 0 and time.time() - created_at > self.recycle:
            return False

        # 简单的ping测试
        try:
            conn.execute("SELECT 1").fetchone()
            return True
        except:
            return False

    def _get_connection_from_pool(self) -> Optional[SQLiteConnection]:
        """从池中获取连接"""
        with self._lock:
            while self._pool:
                wrapped_conn = self._pool.popleft()
                if self._is_connection_valid(wrapped_conn._connection,
                                             wrapped_conn.created_at):
                    wrapped_conn.in_use = True
                    return wrapped_conn
                else:
                    # 连接已过期，关闭它
                    wrapped_conn.invalidate()
                    self._created_connections -= 1
        return None

    def _create_new_connection(self) -> SQLiteConnection:
        """创建新连接"""
        conn = self._create_connection()
        wrapped_conn = SQLiteConnection(self, conn, time.time())
        wrapped_conn.in_use = True

        with self._lock:
            self._created_connections += 1
            if self._created_connections > self.pool_size:
                self._overflow_count += 1

        return wrapped_conn

    def _cleanup_expired(self):
        """清理过期的连接"""
        current_time = time.time()
        expired_connections = []

        with self._lock:
            # 创建一个新的队列来存储有效连接
            valid_connections = deque()

            # 检查池中的每个连接
            while self._pool:
                wrapped_conn = self._pool.popleft()

                # 如果连接未在使用且已过期
                if (not wrapped_conn.in_use and
                        (self.recycle > 0 and
                         current_time - wrapped_conn.created_at > self.recycle)):
                    expired_connections.append(wrapped_conn)
                elif (not wrapped_conn.in_use and
                      not self._is_connection_valid(wrapped_conn._connection,
                                                    wrapped_conn.created_at)):
                    # 连接无效
                    expired_connections.append(wrapped_conn)
                else:
                    # 连接仍然有效
                    valid_connections.append(wrapped_conn)

            # 更新池
            self._pool = valid_connections

            # 更新计数器
            for _ in expired_connections:
                self._created_connections -= 1
                if self._overflow_count > 0:
                    self._overflow_count -= 1

        # 在锁外关闭过期连接
        for wrapped_conn in expired_connections:
            wrapped_conn.invalidate()

        return len(expired_connections)

    def get_connection(self) -> SQLiteConnection:
        """获取连接"""
        raise NotImplementedError

    def _return_connection(self, wrapped_conn: SQLiteConnection):
        """归还连接到池中"""
        if wrapped_conn._closed:
            return

        wrapped_conn.in_use = False

        with self._lock:
            # 检查是否应该保留在池中
            if (len(self._pool) < self.pool_size and
                    self._is_connection_valid(wrapped_conn._connection,
                                              wrapped_conn.created_at)):
                self._pool.append(wrapped_conn)
            else:
                # 关闭溢出连接或过期连接
                wrapped_conn.invalidate()
                self._created_connections -= 1
                if self._overflow_count > 0:
                    self._overflow_count -= 1

    def dispose(self):
        """清理所有连接"""
        with self._lock:
            while self._pool:
                conn = self._pool.popleft()
                conn.invalidate()

            self._created_connections = 0
            self._overflow_count = 0

    def status(self) -> Dict[str, Any]:
        """获取池状态"""
        with self._lock:
            return {
                'pool_size': self.pool_size,
                'connections_in_pool': len(self._pool),
                'total_created': self._created_connections,
                'overflow_count': self._overflow_count,
                'environment': self._env
            }


class ThreadSafePool(SQLitePool):
    """线程安全的SQLite连接池"""

    def get_connection(self) -> SQLiteConnection:
        """获取连接（线程安全版本）"""
        start_time = time.time()

        while True:
            # 尝试从池中获取连接
            conn = self._get_connection_from_pool()
            if conn:
                return conn

            # 检查是否可以创建新连接
            with self._lock:
                can_create = (self._created_connections <
                              self.pool_size + self.max_overflow)

            if can_create:
                return self._create_new_connection()

            # 检查超时
            if time.time() - start_time > self.timeout:
                raise SQLiteTimeoutError(
                    f"Could not get connection within {self.timeout} seconds"
                )

            # 等待一段时间后重试
            if self._env == 'gevent' and gevent is not None:
                gevent.sleep(0.01)
            else:
                time.sleep(0.01)


class StaticPool(SQLitePool):
    """静态连接池 - 适用于内存数据库"""

    def __init__(self, database: str, **connect_args):
        super().__init__(database, pool_size=1, max_overflow=0, **connect_args)
        self._static_connection: Optional[SQLiteConnection] = None
        if self._env == 'gevent' and GeventRLock is not None:
            self._static_lock = GeventRLock()
        else:
            self._static_lock = threading.RLock()

    def get_connection(self) -> SQLiteConnection:
        """获取静态连接"""
        with self._static_lock:
            if (self._static_connection is None or
                    not self._is_connection_valid(self._static_connection._connection, self._static_connection.created_at)):
                if self._static_connection:
                    self._static_connection.invalidate()

                conn = self._create_connection()
                self._static_connection = SQLiteConnection(self, conn, time.time())

            return self._static_connection

    def _return_connection(self, wrapped_conn: SQLiteConnection):
        """静态池不需要归还连接"""
        wrapped_conn.in_use = False

    def _cleanup_expired(self):
        """静态池的清理逻辑"""
        with self._static_lock:
            if (self._static_connection and
                    not self._static_connection.in_use and
                    (0 < self.recycle < time.time() - self._static_connection.created_at)):
                self._static_connection.invalidate()
                self._static_connection = None
                return 1
        return 0


def create_pool(database: str,
                pool_type: str = 'auto',
                **kwargs) -> SQLitePool:
    """
    创建SQLite连接池

    Args:
        database: 数据库文件路径
        pool_type: 池类型 ('auto', 'thread', 'static')
        **kwargs: 其他参数

    Returns:
        SQLitePool实例
    """
    if pool_type == 'auto':
        if database == ':memory:':
            pool_type = 'static'
        else:
            pool_type = 'thread'

    if pool_type == 'static':
        return StaticPool(database, **kwargs)
    elif pool_type == 'thread':
        return ThreadSafePool(database, **kwargs)
    else:
        raise ValueError(f"Unknown pool type: {pool_type}")


@contextmanager
def get_connection(pool: SQLitePool) -> Generator[sqlite3.Connection, None, None]:
    """
    上下文管理器方式获取连接

    Usage:
        pool = create_pool('test.db')
        with get_connection(pool) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
    """
    wrapped_conn = pool.get_connection()
    try:
        yield wrapped_conn.connection
    finally:
        wrapped_conn.close()


# Flask扩展集成示例
class FlaskSQLitePool:
    """Flask扩展集成"""

    def __init__(self, app=None):
        self.pool = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        """初始化Flask应用"""
        database = app.config.get('SQLITE_DATABASE', ':memory:')
        pool_config = app.config.get('SQLITE_POOL_CONFIG', {})

        self.pool = create_pool(database, **pool_config)

        # 注册清理函数
        @app.teardown_appcontext
        def close_db(error):
            # 在请求结束时清理过期连接
            if self.pool and hasattr(self.pool, '_cleanup_expired'):
                cleaned = self.pool._cleanup_expired()
                if cleaned > 0:
                    app.logger.debug(f"Cleaned up {cleaned} expired connections")

        app.extensions['sqlite_pool'] = self

    def get_connection(self) -> SQLiteConnection:
        """获取连接"""
        if not self.pool:
            raise RuntimeError("Pool not initialized")
        return self.pool.get_connection()


# 使用示例
if __name__ == "__main__":
    # 文件数据库示例
    print("=== 文件数据库示例 ===")
    file_pool = create_pool('test.db', pool_size=3, max_overflow=2)

    with get_connection(file_pool) as conn:
        conn.execute("""
                     CREATE TABLE IF NOT EXISTS users
                     (
                         id   INTEGER PRIMARY KEY,
                         name TEXT NOT NULL
                     )
                     """)
        conn.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
        conn.commit()

    print("文件数据库池状态:", file_pool.status())

    # 内存数据库示例
    print("\n=== 内存数据库示例 ===")
    memory_pool = create_pool(':memory:', pool_type='static')

    with get_connection(memory_pool) as conn:
        conn.execute("CREATE TABLE test (id INTEGER, value TEXT)")
        conn.execute("INSERT INTO test VALUES (1, 'test')")
        result = conn.execute("SELECT * FROM test").fetchall()
        print("查询结果:", result)

    print("内存数据库池状态:", memory_pool.status())

    # 多线程测试
    print("\n=== 多线程测试 ===")
    import concurrent.futures


    def worker(worker_id):
        with get_connection(file_pool) as conn:
            conn.execute("INSERT INTO users (name) VALUES (?)",
                         (f"Worker-{worker_id}",))
            conn.commit()
            result = conn.execute("SELECT COUNT(*) FROM users").fetchone()
            return f"Worker-{worker_id}: {result[0]} users"


    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(worker, i) for i in range(5)]
        for future in concurrent.futures.as_completed(futures):
            print(future.result())

    print("最终池状态:", file_pool.status())

    # 清理
    file_pool.dispose()
    memory_pool.dispose()