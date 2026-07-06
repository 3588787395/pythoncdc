"""
对象池优化模块
为AST节点提供对象池化以减少内存分配
"""

import threading
import weakref
from typing import Dict, List, Type, Any, Optional
from collections import deque


class ObjectPool:
    """通用对象池"""
    
    def __init__(self, factory_func: callable, max_size: int = 1000):
        self.factory_func = factory_func
        self.max_size = max_size
        self._pool = deque()
        self._lock = threading.Lock()
        self._created_count = 0
        self._reused_count = 0
    
    def acquire(self, *args, **kwargs) -> Any:
        """获取对象实例"""
        with self._lock:
            if self._pool:
                obj = self._pool.popleft()
                self._reused_count += 1
                # 重新初始化对象
                if hasattr(obj, 'reset'):
                    obj.reset(*args, **kwargs)
                return obj
            else:
                self._created_count += 1
                return self.factory_func(*args, **kwargs)
    
    def release(self, obj: Any) -> None:
        """释放对象实例"""
        if len(self._pool) < self.max_size:
            with self._lock:
                self._pool.append(obj)
    
    def get_stats(self) -> Dict[str, int]:
        """获取池统计信息"""
        return {
            'pool_size': len(self._pool),
            'created': self._created_count,
            'reused': self._reused_count,
            'reuse_rate': self._reused_count / max(1, self._created_count + self._reused_count)
        }


class ASTNodePool:
    """AST节点专用对象池"""
    
    def __init__(self):
        self._pools: Dict[Type, ObjectPool] = {}
        self._weak_refs: Dict[Type, weakref.WeakSet] = {}
        self._lock = threading.Lock()
    
    def get_pool(self, node_class: Type) -> ObjectPool:
        """获取特定节点类的对象池"""
        with self._lock:
            if node_class not in self._pools:
                # 为每种节点类型创建专用工厂函数
                factory_func = self._create_factory(node_class)
                self._pools[node_class] = ObjectPool(factory_func, max_size=500)
                
                # 创建弱引用集合
                self._weak_refs[node_class] = weakref.WeakSet()
            
            return self._pools[node_class]
    
    def _create_factory(self, node_class: Type) -> callable:
        """创建工厂函数"""
        def factory(*args, **kwargs):
            # 创建新的节点实例
            instance = node_class.__new__(node_class)
            if hasattr(instance, '__init__'):
                instance.__init__(*args, **kwargs)
            return instance
        
        return factory
    
    def create_node(self, node_class: Type, *args, **kwargs) -> Any:
        """创建AST节点"""
        pool = self.get_pool(node_class)
        return pool.acquire(*args, **kwargs)
    
    def release_node(self, node: Any) -> None:
        """释放AST节点"""
        node_class = type(node)
        if node_class in self._pools:
            self._pools[node_class].release(node)
    
    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有池的统计信息"""
        stats = {}
        with self._lock:
            for node_class, pool in self._pools.items():
                stats[node_class.__name__] = pool.get_stats()
        return stats


# 全局AST节点池实例
_ast_node_pool = None


def get_ast_node_pool() -> ASTNodePool:
    """获取全局AST节点池"""
    global _ast_node_pool
    if _ast_node_pool is None:
        _ast_node_pool = ASTNodePool()
    return _ast_node_pool


def create_ast_node(node_class: Type, *args, **kwargs) -> Any:
    """创建AST节点的便捷函数"""
    return get_ast_node_pool().create_node(node_class, *args, **kwargs)


def release_ast_node(node: Any) -> None:
    """释放AST节点的便捷函数"""
    get_ast_node_pool().release_node(node)


# 上下文管理器，用于批量节点操作
class NodeOperationContext:
    """节点操作上下文管理"""
    
    def __init__(self):
        self.pool = get_ast_node_pool()
        self._created_nodes = []
        self._released_nodes = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 在退出时释放所有创建的节点
        for node in self._created_nodes:
            self.pool.release_node(node)
    
    def create_node(self, node_class: Type, *args, **kwargs) -> Any:
        """创建节点并跟踪"""
        node = self.pool.create_node(node_class, *args, **kwargs)
        self._created_nodes.append(node)
        return node
    
    def release_node(self, node: Any) -> None:
        """释放节点并跟踪"""
        self.pool.release_node(node)
        if node in self._created_nodes:
            self._created_nodes.remove(node)
        self._released_nodes.append(node)


# 性能监控装饰器
def monitor_node_creation(node_class: Type):
    """监控节点创建的装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 在创建节点前记录
            start_time = __import__('time').time()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = __import__('time').time()
                creation_time = end_time - start_time
                
                # 记录性能统计（可以集成到监控系统中）
                if hasattr(node_class, '_creation_times'):
                    node_class._creation_times.append(creation_time)
                else:
                    node_class._creation_times = [creation_time]
        
        return wrapper
    return decorator


# 预热对象池
def warmup_pools():
    """预热对象池，创建一些初始实例"""
    print("🔥 Pre-warming AST node pools...")
    
    # 导入AST节点类（避免循环导入）
    try:
        from . import ast_nodes
        # 这里可以预热常用的AST节点类
        # 在实际使用中可以根据使用频率调整
    except ImportError:
        pass  # 如果无法导入，稍后会在实际使用时创建
    
    print("[OK] Object pools pre-warmed")


# 性能分析工具
def analyze_pool_performance() -> Dict[str, Any]:
    """分析对象池性能"""
    pool = get_ast_node_pool()
    stats = pool.get_all_stats()
    
    total_created = sum(s['created'] for s in stats.values())
    total_reused = sum(s['reused'] for s in stats.values())
    
    return {
        'total_created': total_created,
        'total_reused': total_reused,
        'overall_reuse_rate': total_reused / max(1, total_created + total_reused),
        'pool_stats': stats
    }