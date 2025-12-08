#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
去重存储模块 - 支持内存与 Redis 双后端
"""
import hashlib
from typing import Optional, Dict, Set, Tuple
from utils.logger import get_logger

try:
    from config import config as app_config
    HAS_CONFIG = True
except ImportError:
    HAS_CONFIG = False

logger = get_logger("dedup_store")


class DedupStore:
    """去重存储抽象类"""
    
    def __init__(self, backend: str = "memory", redis_config: Optional[Dict] = None):
        """
        初始化去重存储
        
        Args:
            backend: "memory" 或 "redis"
            redis_config: Redis 配置 {"host": "127.0.0.1", "port": 6379, "db": 1, "password": "xxx"}
        """
        self.backend = backend
        self._redis = None
        self._memory_doc_hashes: Set[str] = set()
        self._memory_para_hashes: Set[str] = set()
        self._memory_para_simhash: Dict[str, int] = {}  # para_hash -> simhash_value
        
        if backend == "redis":
            try:
                import redis
                self._redis = redis.Redis(
                    host=redis_config.get("host", "127.0.0.1"),
                    port=redis_config.get("port", 6379),
                    db=redis_config.get("db", 1),
                    password=redis_config.get("password"),
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # 测试连接
                self._redis.ping()
                logger.info(f"Redis 连接成功: {redis_config.get('host')}:{redis_config.get('port')}/{redis_config.get('db')}")
            except Exception as e:
                logger.error(f"Redis 连接失败，回退到内存模式: {e}")
                logger.warning("!!! 重要提示: 当前使用内存模式，重启后去重数据将丢失 !!!")
                self.backend = "memory"
                self._redis = None
    
    def _get_doc_key(self) -> str:
        """文档级哈希集合键名"""
        if HAS_CONFIG:
            return app_config.Redis.DOC_HASHES_KEY
        return "kbjx:doc:hashes"
    
    def _get_para_key(self) -> str:
        """段落级哈希集合键名"""
        if HAS_CONFIG:
            return app_config.Redis.PARA_HASHES_KEY
        return "kbjx:para:hashes"
    
    def _get_simhash_key(self) -> str:
        """段落 SimHash 哈希表键名"""
        if HAS_CONFIG:
            return app_config.Redis.PARA_SIMHASH_KEY
        return "kbjx:para:simhash"
    
    def is_doc_seen(self, doc_hash: str) -> bool:
        """
        检查文档是否已存在
        
        Args:
            doc_hash: 文档 SHA256 哈希
        
        Returns:
            是否已存在
        """
        if self.backend == "redis" and self._redis:
            try:
                return bool(self._redis.sismember(self._get_doc_key(), doc_hash))
            except Exception as e:
                logger.error(f"Redis 查询失败: {e}")
                return False
        else:
            return doc_hash in self._memory_doc_hashes
    
    def mark_doc(self, doc_hash: str, ttl_days: Optional[int] = None) -> bool:
        """
        标记文档已处理
        
        Args:
            doc_hash: 文档 SHA256 哈希
            ttl_days: 过期天数（仅 Redis 支持）
        
        Returns:
            是否成功
        """
        if self.backend == "redis" and self._redis:
            try:
                self._redis.sadd(self._get_doc_key(), doc_hash)
                if ttl_days:
                    # 注意：Set 整体设置 TTL，不是单个成员
                    # 如需单成员 TTL，应使用 String 键: kbjx:doc:{hash} with SETEX
                    pass
                return True
            except Exception as e:
                logger.error(f"Redis 写入失败: {e}")
                return False
        else:
            self._memory_doc_hashes.add(doc_hash)
            return True
    
    def is_para_seen(self, para_hash: str) -> bool:
        """
        检查段落是否已存在（精确匹配）
        
        Args:
            para_hash: 段落 SHA256 哈希
        
        Returns:
            是否已存在
        """
        if self.backend == "redis" and self._redis:
            try:
                return bool(self._redis.sismember(self._get_para_key(), para_hash))
            except Exception as e:
                logger.error(f"Redis 查询失败: {e}")
                return False
        else:
            return para_hash in self._memory_para_hashes
    
    def mark_para(self, para_hash: str, simhash_value: Optional[int] = None) -> bool:
        """
        标记段落已处理
        
        Args:
            para_hash: 段落 SHA256 哈希
            simhash_value: SimHash 值（用于近重复检测）
        
        Returns:
            是否成功
        """
        if self.backend == "redis" and self._redis:
            try:
                self._redis.sadd(self._get_para_key(), para_hash)
                if simhash_value is not None:
                    self._redis.hset(self._get_simhash_key(), para_hash, str(simhash_value))
                return True
            except Exception as e:
                logger.error(f"Redis 写入失败: {e}")
                return False
        else:
            self._memory_para_hashes.add(para_hash)
            if simhash_value is not None:
                self._memory_para_simhash[para_hash] = simhash_value
            return True
    
    def get_all_para_simhash(self) -> Dict[str, int]:
        """
        获取所有段落的 SimHash（用于近重复比对）
        
        Returns:
            {para_hash: simhash_value}
        """
        if self.backend == "redis" and self._redis:
            try:
                raw = self._redis.hgetall(self._get_simhash_key())
                return {k: int(v) for k, v in raw.items()}
            except Exception as e:
                logger.error(f"Redis 查询失败: {e}")
                return {}
        else:
            return self._memory_para_simhash.copy()
    
    def clear_all(self) -> bool:
        """
        清空所有去重数据（谨慎使用）
        
        Returns:
            是否成功
        """
        if self.backend == "redis" and self._redis:
            try:
                self._redis.delete(self._get_doc_key(), self._get_para_key(), self._get_simhash_key())
                logger.warning("Redis 去重数据已清空")
                return True
            except Exception as e:
                logger.error(f"Redis 清空失败: {e}")
                return False
        else:
            self._memory_doc_hashes.clear()
            self._memory_para_hashes.clear()
            self._memory_para_simhash.clear()
            logger.warning("内存去重数据已清空")
            return True
    
    def get_stats(self) -> Dict[str, int]:
        """
        获取去重统计信息
        
        Returns:
            {"doc_count": xxx, "para_count": xxx, "simhash_count": xxx}
        """
        if self.backend == "redis" and self._redis:
            try:
                return {
                    "doc_count": self._redis.scard(self._get_doc_key()),
                    "para_count": self._redis.scard(self._get_para_key()),
                    "simhash_count": self._redis.hlen(self._get_simhash_key())
                }
            except Exception as e:
                logger.error(f"Redis 统计失败: {e}")
                return {"doc_count": 0, "para_count": 0, "simhash_count": 0}
        else:
            return {
                "doc_count": len(self._memory_doc_hashes),
                "para_count": len(self._memory_para_hashes),
                "simhash_count": len(self._memory_para_simhash)
            }


def compute_sha256(text: str) -> str:
    """计算文本的 SHA256 哈希"""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def compute_file_sha256(file_path: str, chunk_size: int = 8192) -> str:
    """计算文件的 binary SHA256 哈希
    
    Args:
        file_path: 文件路径
        chunk_size: 读取块大小（字节），默认 8KB
    
    Returns:
        文件的 SHA256 哈希值（十六进制字符串）
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            # 分块读取，避免大文件内存溢出
            for chunk in iter(lambda: f.read(chunk_size), b''):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"计算文件哈希失败: {file_path}, 错误: {e}")
        raise
