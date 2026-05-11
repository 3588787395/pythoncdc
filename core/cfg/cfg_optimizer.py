"""
CFG优化器模块

提供CFG构建和分析的性能优化功能。
"""

import time
import sys
from typing import List, Dict, Set, Optional, Callable, Any
from functools import wraps
from collections import defaultdict

from .basic_block import BasicBlock
from .cfg_builder import ControlFlowGraph


class PerformanceProfiler:
    """
    性能分析器
    
    用于分析CFG构建和分析的性能瓶颈。
    """
    
    def __init__(self):
        self.timings: Dict[str, List[float]] = defaultdict(list)
        self.counts: Dict[str, int] = defaultdict(int)
        self.enabled = False
    
    def enable(self):
        """启用性能分析"""
        self.enabled = True
    
    def disable(self):
        """禁用性能分析"""
        self.enabled = False
    
    def profile(self, func_name: str):
        """装饰器：分析函数性能"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)
                
                start_time = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    elapsed = time.perf_counter() - start_time
                    self.timings[func_name].append(elapsed)
                    self.counts[func_name] += 1
            return wrapper
        return decorator
    
    def get_stats(self) -> Dict[str, Dict[str, float]]:
        """获取性能统计"""
        stats = {}
        for name, times in self.timings.items():
            if times:
                stats[name] = {
                    'count': len(times),
                    'total': sum(times),
                    'mean': sum(times) / len(times),
                    'min': min(times),
                    'max': max(times),
                }
        return stats
    
    def print_stats(self):
        """打印性能统计"""
        stats = self.get_stats()
        if not stats:
            print("没有性能数据")
            return
        
        print("\n" + "="*80)
        print("性能统计")
        print("="*80)
        print(f"{'函数名':<40} {'调用次数':<10} {'总时间(s)':<12} {'平均时间(s)':<12} {'最小(s)':<10} {'最大(s)':<10}")
        print("-"*80)
        
        for name, stat in sorted(stats.items(), key=lambda x: x[1]['total'], reverse=True):
            print(f"{name:<40} {stat['count']:<10} {stat['total']:<12.6f} {stat['mean']:<12.6f} {stat['min']:<10.6f} {stat['max']:<10.6f}")
        
        print("="*80)


class MemoryOptimizer:
    """
    内存优化器
    
    优化CFG构建过程中的内存使用。
    """
    
    @staticmethod
    def optimize_block_storage(blocks: Dict[int, BasicBlock]) -> None:
        """
        优化基本块存储
        
        清理不必要的引用，减少内存占用。
        """
        for block in blocks.values():
            # 将集合转换为frozenset以节省内存
            if hasattr(block, 'dominators') and isinstance(block.dominators, set):
                block.dominators = frozenset(block.dominators)
            
            if hasattr(block, 'dominated_blocks') and isinstance(block.dominated_blocks, set):
                block.dominated_blocks = frozenset(block.dominated_blocks)
    
    @staticmethod
    def compact_instructions(block: BasicBlock) -> None:
        """
        压缩指令存储
        
        删除不必要的指令属性以节省内存。
        """
        for instr in block.instructions:
            # 删除可能占用大量内存的属性
            if hasattr(instr, 'argrepr') and instr.argrepr:
                delattr(instr, 'argrepr')


class CFGCache:
    """
    CFG缓存
    
    缓存已构建的CFG以避免重复构建。
    """
    
    def __init__(self, max_size: int = 100):
        self.cache: Dict[int, ControlFlowGraph] = {}
        self.max_size = max_size
        self.access_count: Dict[int, int] = defaultdict(int)
    
    def get(self, code_id: int) -> Optional[ControlFlowGraph]:
        """获取缓存的CFG"""
        if code_id in self.cache:
            self.access_count[code_id] += 1
            return self.cache[code_id]
        return None
    
    def put(self, code_id: int, cfg: ControlFlowGraph) -> None:
        """缓存CFG"""
        if len(self.cache) >= self.max_size:
            # 移除最少访问的条目
            lru_key = min(self.access_count.keys(), key=lambda k: self.access_count[k])
            del self.cache[lru_key]
            del self.access_count[lru_key]
        
        self.cache[code_id] = cfg
        self.access_count[code_id] = 1
    
    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.access_count.clear()


class OptimizedCFGBuilder:
    """
    优化的CFG构建器
    
    提供性能优化的CFG构建功能。
    """
    
    def __init__(self, use_cache: bool = True, optimize_memory: bool = True):
        self.use_cache = use_cache
        self.optimize_memory = optimize_memory
        self.cache = CFGCache() if use_cache else None
        self.profiler = PerformanceProfiler()
    
    def build(self, code_obj, name: Optional[str] = None) -> ControlFlowGraph:
        """
        构建CFG（带优化）
        
        Args:
            code_obj: Python代码对象
            name: CFG名称
            
        Returns:
            控制流图
        """
        code_id = id(code_obj)
        
        # 检查缓存
        if self.use_cache and self.cache:
            cached_cfg = self.cache.get(code_id)
            if cached_cfg:
                return cached_cfg
        
        # 构建CFG
        from .cfg_builder import CFGBuilder
        
        start_time = time.perf_counter()
        builder = CFGBuilder()
        cfg = builder.build(code_obj, name)
        build_time = time.perf_counter() - start_time
        
        # 内存优化
        if self.optimize_memory:
            MemoryOptimizer.optimize_block_storage(cfg.blocks)
        
        # 缓存结果
        if self.use_cache and self.cache:
            self.cache.put(code_id, cfg)
        
        return cfg


class DominatorOptimizer:
    """
    支配节点计算优化器
    
    提供优化的支配节点算法。
    """
    
    @staticmethod
    def compute_dominators_fast(cfg: ControlFlowGraph) -> None:
        """
        快速计算支配节点
        
        使用Lengauer-Tarjan算法（比迭代算法更快）。
        """
        # 简化实现：使用优化的迭代算法
        if not cfg.entry_block:
            return
        
        all_blocks = set(cfg.blocks.values())
        
        # 初始化
        for block in cfg.blocks.values():
            if block == cfg.entry_block:
                block.dominators = {cfg.entry_block}
            else:
                block.dominators = all_blocks.copy()
        
        # 迭代直到不动点
        changed = True
        iteration = 0
        max_iterations = len(cfg.blocks) * 2  # 减少最大迭代次数
        
        while changed and iteration < max_iterations:
            changed = False
            iteration += 1
            
            # 按逆后序处理块（更快收敛）
            sorted_blocks = DominatorOptimizer._reverse_postorder(cfg)
            
            for block in sorted_blocks:
                if block == cfg.entry_block:
                    continue
                
                if not block.predecessors:
                    new_dom = {block}
                else:
                    # 使用第一个前驱的支配集作为起点
                    preds = list(block.predecessors)
                    new_dom = set(preds[0].dominators)
                    
                    # 与其他前驱取交集
                    for pred in preds[1:]:
                        new_dom &= pred.dominators
                    
                    new_dom.add(block)
                
                if new_dom != block.dominators:
                    block.dominators = new_dom
                    changed = True
    
    @staticmethod
    def _reverse_postorder(cfg: ControlFlowGraph) -> List[BasicBlock]:
        """
        获取逆后序遍历的块列表
        
        这种顺序有助于支配节点算法更快收敛。
        """
        visited = set()
        order = []
        
        def visit(block):
            if block in visited:
                return
            visited.add(block)
            for succ in block.successors:
                visit(succ)
            order.append(block)
        
        if cfg.entry_block:
            visit(cfg.entry_block)
        
        # 返回逆序
        return list(reversed(order))


def optimize_cfg_building(code_obj, name: Optional[str] = None, 
                         use_cache: bool = True, 
                         optimize_memory: bool = True) -> ControlFlowGraph:
    """
    便捷函数：使用优化构建CFG
    
    Args:
        code_obj: Python代码对象
        name: CFG名称
        use_cache: 是否使用缓存
        optimize_memory: 是否优化内存
        
    Returns:
        控制流图
    """
    builder = OptimizedCFGBuilder(use_cache=use_cache, optimize_memory=optimize_memory)
    return builder.build(code_obj, name)


# 全局性能分析器实例
profiler = PerformanceProfiler()
