"""
性能优化缓存系统
提供高效的缓存机制以提升性能
"""

import threading
import time
import weakref
from typing import Dict, Any, Optional, List, Callable, Union
from functools import wraps, lru_cache
from collections import OrderedDict
import hashlib
import pickle


class LRUCache:
    """LRU缓存实现"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache = OrderedDict()
        self._lock = threading.Lock()
    
    def get(self, key: Any) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key in self._cache:
                # 移动到末尾（最近使用）
                value = self._cache.pop(key)
                self._cache[key] = value
                return value
            return None
    
    def put(self, key: Any, value: Any) -> None:
        """设置缓存值"""
        with self._lock:
            if key in self._cache:
                # 更新现有键
                self._cache.pop(key)
            elif len(self._cache) >= self.max_size:
                # 移除最久未使用的项
                self._cache.popitem(last=False)
            
            self._cache[key] = value
    
    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
    
    def size(self) -> int:
        """获取缓存大小"""
        return len(self._cache)
    
    def stats(self) -> Dict[str, int]:
        """获取缓存统计"""
        with self._lock:
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hit_ratio': getattr(self, '_hit_ratio', 0.0)
            }


class TTLCache:
    """TTL缓存实现（Time To Live）"""
    
    def __init__(self, max_size: int = 1000, ttl: float = 300.0):
        self.max_size = max_size
        self.ttl = ttl
        self._cache = OrderedDict()
        self._timestamps = {}
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: Any) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key in self._cache:
                # 检查是否过期
                timestamp = self._timestamps[key]
                if time.time() - timestamp < self.ttl:
                    self._hits += 1
                    # 移动到末尾
                    value = self._cache.pop(key)
                    self._cache[key] = value
                    self._timestamps[key] = time.time()
                    return value
                else:
                    # 过期，删除
                    del self._cache[key]
                    del self._timestamps[key]
            
            self._misses += 1
            return None
    
    def put(self, key: Any, value: Any) -> None:
        """设置缓存值"""
        with self._lock:
            # 如果键已存在，更新
            if key in self._cache:
                self._cache.pop(key)
                self._timestamps.pop(key, None)
            elif len(self._cache) >= self.max_size:
                # 移除最久未使用的项
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                del self._timestamps[oldest_key]
            
            self._cache[key] = value
            self._timestamps[key] = time.time()
    
    def cleanup_expired(self) -> int:
        """清理过期项"""
        with self._lock:
            current_time = time.time()
            expired_keys = []
            
            for key, timestamp in self._timestamps.items():
                if current_time - timestamp >= self.ttl:
                    expired_keys.append(key)
            
            for key in expired_keys:
                self._cache.pop(key, None)
                self._timestamps.pop(key, None)
            
            return len(expired_keys)
    
    def stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_ratio = self._hits / max(1, total_requests)
            
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'ttl': self.ttl,
                'hits': self._hits,
                'misses': self._misses,
                'hit_ratio': hit_ratio,
                'expired_items': len(self._timestamps) - len(self._cache)
            }


class WeakValueCache:
    """弱引用缓存，用于缓存大对象"""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._cache = OrderedDict()
        self._lock = threading.Lock()
    
    def get(self, key: Any) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key in self._cache:
                weak_ref = self._cache[key]
                value = weak_ref()
                if value is not None:
                    # 移动到末尾
                    self._cache.pop(key)
                    self._cache[key] = weak_ref
                    return value
                else:
                    # 弱引用已被回收
                    del self._cache[key]
            
            return None
    
    def put(self, key: Any, value: Any) -> None:
        """设置缓存值"""
        with self._lock:
            if key in self._cache:
                self._cache.pop(key)
            elif len(self._cache) >= self.max_size:
                # 移除最久未使用的项
                self._cache.popitem(last=False)
            
            # 创建弱引用
            weak_ref = weakref.ref(value)
            self._cache[key] = weak_ref
    
    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()


class PerformanceCache:
    """综合性能缓存系统"""
    
    def __init__(self):
        self._lru_cache = LRUCache(max_size=1000)
        self._ttl_cache = TTLCache(max_size=500, ttl=300.0)
        self._weak_cache = WeakValueCache(max_size=100)
        self._function_cache = {}
        self._lock = threading.Lock()
    
    def get_lru(self, key: Any) -> Optional[Any]:
        """获取LRU缓存值"""
        return self._lru_cache.get(key)
    
    def put_lru(self, key: Any, value: Any) -> None:
        """设置LRU缓存值"""
        self._lru_cache.put(key, value)
    
    def get_ttl(self, key: Any) -> Optional[Any]:
        """获取TTL缓存值"""
        return self._ttl_cache.get(key)
    
    def put_ttl(self, key: Any, value: Any) -> None:
        """设置TTL缓存值"""
        self._ttl_cache.put(key, value)
    
    def get_weak(self, key: Any) -> Optional[Any]:
        """获取弱引用缓存值"""
        return self._weak_cache.get(key)
    
    def put_weak(self, key: Any, value: Any) -> None:
        """设置弱引用缓存值"""
        self._weak_cache.put(key, value)
    
    def cache_function(self, func: Callable) -> Callable:
        """缓存函数结果"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 创建缓存键
            key = self._make_cache_key(func.__name__, args, kwargs)
            
            # 尝试从缓存获取
            result = self._lru_cache.get(key)
            if result is not None:
                return result
            
            # 计算结果并缓存
            result = func(*args, **kwargs)
            self._lru_cache.put(key, result)
            return result
        
        return wrapper
    
    def _make_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """创建缓存键"""
        # 序列化参数
        try:
            args_serialized = pickle.dumps(args)
            kwargs_serialized = pickle.dumps(kwargs)
            key_data = f"{func_name}:{args_serialized.hex()}:{kwargs_serialized.hex()}"
            return hashlib.md5(key_data.encode()).hexdigest()
        except (pickle.PicklingError, TypeError):
            # 如果无法序列化，使用字符串表示
            return hashlib.md5(f"{func_name}:{str(args)}:{str(kwargs)}".encode()).hexdigest()
    
    def cleanup(self) -> Dict[str, int]:
        """清理缓存"""
        with self._lock:
            cleaned = {
                'lru_cleared': 0,
                'ttl_expired': 0,
                'weak_cleared': 0
            }
            
            # 清理TTL缓存
            cleaned['ttl_expired'] = self._ttl_cache.cleanup_expired()
            
            # 清理LRU缓存（根据需要）
            # lru_cache不主动清理
            
            # 清理弱引用缓存（自动清理过期引用）
            old_size = self._weak_cache.size()
            # 弱引用缓存的清理由GC自动处理
            
            return cleaned
    
    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有缓存的统计信息"""
        return {
            'lru': self._lru_cache.stats(),
            'ttl': self._ttl_cache.stats(),
            'weak': {'size': self._weak_cache.size()},
            'total_functions_cached': len(self._function_cache)
        }


# 全局缓存实例
_global_cache = None


def get_performance_cache() -> PerformanceCache:
    """获取全局性能缓存实例"""
    global _global_cache
    if _global_cache is None:
        _global_cache = PerformanceCache()
    return _global_cache


# 性能监控装饰器
def performance_cache_decorator(max_size: int = 1000):
    """性能缓存装饰器"""
    cache = get_performance_cache()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 创建缓存键
            key = cache._make_cache_key(func.__name__, args, kwargs)
            
            # 尝试从缓存获取
            result = cache.get_lru(key)
            if result is not None:
                return result
            
            # 计算结果并缓存
            result = func(*args, **kwargs)
            cache.put_lru(key, result)
            return result
        
        return wrapper
    return decorator


# AST节点缓存优化
class ASTNodeCache:
    """AST节点专用缓存"""
    
    def __init__(self):
        self._cache = TTLCache(max_size=500, ttl=600.0)  # 10分钟TTL
        self._node_types = {}
        self._lock = threading.Lock()
    
    def get_node_type(self, node_class_name: str) -> Optional[Any]:
        """获取节点类型"""
        return self._node_types.get(node_class_name)
    
    def cache_node_type(self, node_class_name: str, node_type: Any) -> None:
        """缓存节点类型"""
        with self._lock:
            self._node_types[node_class_name] = node_type
    
    def get_cached_node(self, key: str) -> Optional[Any]:
        """获取缓存的节点"""
        return self._cache.get(key)
    
    def cache_node(self, key: str, node: Any) -> None:
        """缓存节点"""
        self._cache.put(key, node)
    
    def cleanup(self) -> int:
        """清理过期节点"""
        return self._cache.cleanup_expired()
    
    def stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return self._cache.stats()


# 全局AST节点缓存
_global_ast_cache = None


def get_ast_node_cache() -> ASTNodeCache:
    """获取全局AST节点缓存"""
    global _global_ast_cache
    if _global_ast_cache is None:
        _global_ast_cache = ASTNodeCache()
    return _global_ast_cache


# 延迟导入NodeType以避免循环导入
def get_node_type():
    """延迟获取NodeType枚举"""
    try:
        from .ast_nodes import NodeType
        return NodeType
    except (ImportError, AttributeError):
        # 如果导入失败，返回None
        return None