"""
数据库管理模块
基于 DBUtils 连接池，支持 SQLite / MySQL / PostgreSQL / SQL Server，通过配置自动选择驱动
"""
from typing import Any, Callable, Dict, List, Optional, Tuple

from dbutils.pooled_db import PooledDB

import setting as config
from common.logger import logger

# 驱动映射
_DRIVER_MAP = {
    'sqlite': 'sqlite3',
    'mysql': 'pymysql',
    'postgresql': 'psycopg2',
    'sqlserver': 'pymssql',
}

# 各类型默认端口
_DEFAULT_PORTS = {
    'mysql': 3306,
    'postgresql': 5432,
    'sqlserver': 1433,
}


class DatabaseManager:
    """数据库连接池管理器，由 pytest session fixture 注入"""

    def __init__(self):
        cfg = config.DATABASE_CONFIG
        self._pool: Optional[PooledDB] = None
        self._db_type = cfg.get('type', 'sqlite')

        default_port = _DEFAULT_PORTS.get(self._db_type, 3306)
        self._connect_kwargs = {
            'host': cfg.get('host', 'localhost'),
            'port': cfg.get('port', default_port),
            'database': cfg.get('database', 'autoapitest'),
            'user': cfg.get('username', 'root'),
            'password': cfg.get('password', ''),
        }

        # SQLite 只需要 database 参数
        if self._db_type == 'sqlite':
            self._connect_kwargs = {'database': cfg.get('database', ':memory:')}

        # MySQL 额外参数
        if self._db_type == 'mysql':
            self._connect_kwargs['charset'] = cfg.get('charset', 'utf8mb4')

        # SQL Server 使用 pymssql，连接参数名是 server 而非 host
        if self._db_type == 'sqlserver':
            self._connect_kwargs['server'] = self._connect_kwargs.pop('host')

        self._pool_min_size = cfg.get('pool_min_size', 2)
        self._pool_max_size = cfg.get('pool_max_size', 10)

    @property
    def db_type(self) -> str:
        return self._db_type

    def connect(self):
        """初始化连接池（幂等，重复调用不重建）"""
        if self._pool is not None:
            return

        driver_name = _DRIVER_MAP.get(self._db_type)
        if driver_name is None:
            raise ValueError(f'不支持的数据库类型: {self._db_type}，可选: {list(_DRIVER_MAP.keys())}')

        driver = __import__(driver_name)

        self._pool = PooledDB(
            creator=driver,
            mincached=self._pool_min_size,
            maxcached=self._pool_max_size,
            maxconnections=self._pool_max_size * 2,
            blocking=True,
            **self._connect_kwargs,
        )
        logger.info(f'数据库连接池已初始化: type={self._db_type}, min={self._pool_min_size}, max={self._pool_max_size}')

    def close(self):
        """关闭连接池，释放所有连接"""
        if self._pool is not None:
            self._pool.close()
            self._pool = None
            logger.info('数据库连接池已关闭')

    def _get_conn(self):
        """从池中获取连接"""
        if self._pool is None:
            raise RuntimeError('数据库未连接，请先调用 connect()')
        return self._pool.connection()

    # ==================== 查询 ====================

    def query(self, sql: str, params: Optional[tuple] = None) -> List[tuple]:
        """执行 SELECT，返回全部行"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params or ())
            rows = cursor.fetchall()
            return rows

    def query_one(self, sql: str, params: Optional[tuple] = None) -> Optional[tuple]:
        """执行 SELECT，返回单行或 None"""
        rows = self.query(sql, params)
        return rows[0] if rows else None

    def query_dict(self, sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """执行 SELECT，返回全部行（字典格式）"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params or ())
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    # ==================== 写入 ====================

    def execute(self, sql: str, params: Optional[tuple] = None) -> int:
        """执行 INSERT/UPDATE/DELETE，返回影响行数"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params or ())
            conn.commit()
            return cursor.rowcount

    def executemany(self, sql: str, params_list: List[tuple]) -> int:
        """批量执行 INSERT/UPDATE/DELETE，返回影响行数"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.executemany(sql, params_list)
            conn.commit()
            return cursor.rowcount

    # ==================== 事务 ====================

    def transaction(self, fn: Callable[..., Any], *args, **kwargs) -> Any:
        """在事务中执行回调函数，自动提交或回滚"""
        conn = self._get_conn()
        conn.__enter__()  # 开启事务（关闭自动提交）
        try:
            result = fn(conn, *args, **kwargs)
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.__exit__(None, None, None)
            conn.close()

    # ==================== 上下文管理器 ====================

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
