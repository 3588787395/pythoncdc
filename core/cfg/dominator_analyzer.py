"""
支配节点分析器模块

基于编译器理论实现支配节点分析和循环检测：
- 支配树计算：迭代数据流算法
- 回边检测：标准定义 - 边 B→H 当 H 支配 B
- 自然循环：从回边 (B, H) 计算循环体 = {H} ∪ {从 B 可达且不经过 H 的所有节点}
- 循环类型分类：基于 header 中的指令特征（FOR_ITER/GET_ANEXT/其他）
"""

from typing import Set, Optional, Dict, List, Tuple
from collections import deque

from .basic_block import BasicBlock
from .cfg_builder import ControlFlowGraph


class DominatorAnalyzer:
    """
    支配节点分析器
    
    计算控制流图中基本块的支配关系。
    节点d支配节点n，当且仅当从入口到n的所有路径都经过d。
    """
    
    def __init__(self, cfg: ControlFlowGraph):
        self.cfg = cfg
        self.blocks = list(cfg.blocks.values())
    
    def analyze(self) -> None:
        self._compute_dominators()
        self._compute_immediate_dominators()
        self._compute_dominated_blocks()
        self._compute_post_dominators()
        self._compute_immediate_post_dominators()

    def dominates(self, a: 'BasicBlock', b: 'BasicBlock') -> bool:
        if not hasattr(a, 'dominators'):
            return a == b
        return a in b.dominators
    
    def _compute_dominators(self) -> None:
        if not self.cfg.entry_block:
            return
        
        all_blocks = set(self.blocks)
        
        for block in self.blocks:
            if block == self.cfg.entry_block:
                block.dominators = {self.cfg.entry_block}
            else:
                block.dominators = all_blocks.copy()
        
        changed = True
        iteration = 0
        max_iterations = len(self.blocks) * 10
        
        while changed and iteration < max_iterations:
            changed = False
            iteration += 1
            
            sorted_blocks = sorted(self.blocks, key=lambda b: b.start_offset)
            
            for block in sorted_blocks:
                if block == self.cfg.entry_block:
                    continue
                
                if not block.predecessors:
                    new_dom = {block}
                else:
                    new_dom = all_blocks.copy()
                    for pred in block.predecessors:
                        new_dom &= pred.dominators
                    new_dom.add(block)
                
                if new_dom != block.dominators:
                    block.dominators = new_dom
                    changed = True
    
    def _compute_immediate_dominators(self) -> None:
        for block in self.blocks:
            if block == self.cfg.entry_block:
                block.immediate_dominator = None
                continue
            
            strict_doms = block.dominators - {block}
            
            if not strict_doms:
                block.immediate_dominator = None
                continue
            
            immediate = None
            for dom in strict_doms:
                is_immediate = True
                for other in strict_doms:
                    if other != dom and dom.dominates(other):
                        is_immediate = False
                        break
                
                if is_immediate:
                    immediate = dom
                    break
            
            block.immediate_dominator = immediate
    
    def _compute_dominated_blocks(self) -> None:
        for block in self.blocks:
            block.dominated_blocks = set()
        
        for block in self.blocks:
            for dom in block.dominators:
                if dom != block:
                    dom.dominated_blocks.add(block)

    def _compute_post_dominators(self) -> None:
        exit_blocks = [b for b in self.blocks if not b.successors or b.is_exit]
        if not exit_blocks:
            for block in self.blocks:
                block.post_dominators = {block}
            return

        virtual_exit = BasicBlock(-1)
        virtual_exit.is_exit = True
        virtual_exit.post_dominators = {virtual_exit}

        for block in exit_blocks:
            block.successors = block.successors | {virtual_exit}
        virtual_exit.predecessors = set(exit_blocks)

        all_blocks_and_exit = set(self.blocks) | {virtual_exit}

        for block in self.blocks:
            if block in exit_blocks:
                block.post_dominators = {block, virtual_exit}
            else:
                block.post_dominators = all_blocks_and_exit.copy()

        changed = True
        iteration = 0
        max_iterations = len(all_blocks_and_exit) * 10

        while changed and iteration < max_iterations:
            changed = False
            iteration += 1

            for block in list(self.blocks) + [virtual_exit]:
                if block == virtual_exit:
                    continue

                if not block.successors:
                    new_pdom = {block}
                else:
                    new_pdom = all_blocks_and_exit.copy()
                    for succ in block.successors:
                        new_pdom &= succ.post_dominators
                    new_pdom.add(block)

                if new_pdom != block.post_dominators:
                    block.post_dominators = new_pdom
                    changed = True

        for block in self.blocks:
            block.post_dominators.discard(virtual_exit)

        for block in exit_blocks:
            block.successors.discard(virtual_exit)
        virtual_exit.predecessors.clear()

    def _compute_immediate_post_dominators(self) -> None:
        for block in self.blocks:
            strict_pdoms = block.post_dominators - {block}

            if not strict_pdoms:
                block.immediate_post_dominator = None
                continue

            immediate = None
            for pdom in strict_pdoms:
                is_immediate = True
                for other in strict_pdoms:
                    if other != pdom and pdom.post_dominates(other):
                        is_immediate = False
                        break
                if is_immediate:
                    immediate = pdom
                    break

            block.immediate_post_dominator = immediate

    def get_post_dominance_frontier(self, block: BasicBlock) -> Set[BasicBlock]:
        frontier: Set[BasicBlock] = set()
        for b in self.blocks:
            if b == block:
                continue
            for succ in b.successors:
                if block.post_dominates(succ) and not block.strictly_post_dominates(b):
                    frontier.add(b)
                    break
        return frontier

    def compute_all_post_dominance_frontiers(self) -> Dict[BasicBlock, Set[BasicBlock]]:
        frontiers: Dict[BasicBlock, Set[BasicBlock]] = {}
        for block in self.blocks:
            frontiers[block] = self.get_post_dominance_frontier(block)
        return frontiers

    def find_nearest_common_post_dominator(self, blocks: Set[BasicBlock]) -> Optional[BasicBlock]:
        if not blocks:
            return None
        if len(blocks) == 1:
            return next(iter(blocks))

        common_pdoms = None
        for block in blocks:
            if common_pdoms is None:
                common_pdoms = block.post_dominators.copy()
            else:
                common_pdoms &= block.post_dominators

        if not common_pdoms:
            return None

        for pdom in list(common_pdoms):
            is_nearest = True
            for other in common_pdoms:
                if other != pdom and pdom.strictly_post_dominates(other):
                    is_nearest = False
                    break
            if is_nearest:
                return pdom
        return None

    def find_nearest_common_post_dominator_two(self, block_a: BasicBlock, block_b: BasicBlock) -> Optional[BasicBlock]:
        return self.find_nearest_common_post_dominator({block_a, block_b})

    def find_post_dominators_of(self, block: BasicBlock) -> Set[BasicBlock]:
        return block.post_dominators

    def get_dominator_tree(self) -> Dict[BasicBlock, Set[BasicBlock]]:
        tree: Dict[BasicBlock, Set[BasicBlock]] = {}
        
        for block in self.blocks:
            tree[block] = set()
        
        for block in self.blocks:
            if block.immediate_dominator:
                tree[block.immediate_dominator].add(block)
        
        return tree
    
    def find_nearest_common_dominator(self, blocks: Set[BasicBlock]) -> Optional[BasicBlock]:
        if not blocks:
            return None
        
        if len(blocks) == 1:
            return next(iter(blocks))
        
        common_doms = None
        for block in blocks:
            if common_doms is None:
                common_doms = block.dominators.copy()
            else:
                common_doms &= block.dominators
        
        if not common_doms:
            return None
        
        for dom in list(common_doms):
            is_nearest = True
            for other in common_doms:
                if other != dom and other.strictly_dominates(dom):
                    is_nearest = False
                    break
            
            if is_nearest:
                return dom
        
        return None
    
    def is_dominator(self, potential_dom: BasicBlock, block: BasicBlock) -> bool:
        return potential_dom in block.dominators
    
    def strictly_dominates(self, dom: BasicBlock, block: BasicBlock) -> bool:
        return dom != block and self.is_dominator(dom, block)
    
    def strictly_post_dominates(self, pdom: BasicBlock, block: BasicBlock) -> bool:
        return pdom != block and pdom in block.post_dominators
    
    def get_dominance_frontier(self, block: BasicBlock) -> Set[BasicBlock]:
        frontier: Set[BasicBlock] = set()
        
        for b in self.blocks:
            if b == block:
                continue
            
            for pred in b.predecessors:
                if block.dominates(pred) and not block.strictly_dominates(b):
                    frontier.add(b)
                    break
        
        return frontier
    
    def compute_all_dominance_frontiers(self) -> Dict[BasicBlock, Set[BasicBlock]]:
        frontiers: Dict[BasicBlock, Set[BasicBlock]] = {}
        
        for block in self.blocks:
            frontiers[block] = self.get_dominance_frontier(block)
        
        return frontiers
    
    def compute_dominance_depth(self) -> Dict[BasicBlock, int]:
        depths: Dict[BasicBlock, int] = {}
        
        if self.cfg.entry_block:
            depths[self.cfg.entry_block] = 0
            worklist = [self.cfg.entry_block]
            while worklist:
                current = worklist.pop()
                current_depth = depths[current]
                for child in current.dominated_blocks:
                    if child == current:
                        continue
                    depths[child] = current_depth + 1
                    worklist.append(child)
        
        for block in self.blocks:
            block.dominance_depth = depths.get(block, 0)
        
        return depths
    
    def get_control_dependence(self, block: BasicBlock) -> Set[BasicBlock]:
        dependent: Set[BasicBlock] = set()
        
        if len(block.successors) <= 1:
            return dependent
        
        for succ in block.successors:
            runner = succ
            while runner and runner != block.immediate_dominator:
                dependent.add(runner)
                runner = runner.immediate_dominator
        
        return dependent


FOR_ITER_OPS = frozenset({
    'FOR_ITER', 'FOR_ITER_RANGE', 'FOR_ITER_LIST',
    'FOR_ITER_TUPLE', 'FOR_ITER_GEN', 'FOR_ITER_DICT',
})

BACKWARD_JUMP_OPS = frozenset({
    'JUMP_BACKWARD',
    'POP_JUMP_BACKWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_TRUE',
    'POP_JUMP_BACKWARD_IF_NONE', 'POP_JUMP_BACKWARD_IF_NOT_NONE',
})

FORWARD_JUMP_OPS = frozenset({
    'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE',
    'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_FORWARD_IF_NOT_NONE',
})

PLACEHOLDER_OPS = frozenset({
    'NOP', 'RESUME', 'CACHE', 'PRECALL', 'CALL',
})


class LoopAnalyzer:
    """
    循环分析器 - 基于编译器理论的标准算法
    
    核心算法：
    1. 回边检测：边 B→H 是回边当且仅当 H 支配 B
    2. 自然循环：对于回边 (B, H)，循环体 = {H} ∪ {从 B 反向可达且不经过 H 的所有节点}
    3. 循环类型：基于 header 中的指令特征分类
    """
    
    def __init__(self, cfg: ControlFlowGraph, dom_analyzer: DominatorAnalyzer):
        self.cfg = cfg
        self.dom_analyzer = dom_analyzer
        self.loop_headers: Set[BasicBlock] = set()
        self.loop_bodies: Dict[BasicBlock, Set[BasicBlock]] = {}
        self.back_edges: List[Tuple[BasicBlock, BasicBlock]] = []
    
    def analyze(self) -> None:
        self._find_back_edges()
        self._classify_loop_headers()
        self._compute_loop_bodies()
        self._compute_loop_depths()
    
    def _find_back_edges(self) -> None:
        """
        检测所有回边
        
        标准定义：边 B→H 是回边当且仅当 H 支配 B。
        这是编译器理论中回边的唯一定义，不需要任何启发式判断。
        """
        self.back_edges = []
        
        for block in self.cfg.blocks.values():
            for succ in block.successors:
                if succ.dominates(block):
                    self.back_edges.append((block, succ))
    
    def _classify_loop_headers(self) -> None:
        """
        分类循环头部
        
        回边的目标就是循环header。这是由回边定义直接得出的结论。
        同时标记 FOR_ITER/GET_ANEXT 块为循环header（它们可能没有回边指向它们，
        但它们确实是循环的入口点）。
        """
        self.loop_headers = set()
        
        for block in self.cfg.blocks.values():
            for instr in block.instructions:
                if instr.opname in FOR_ITER_OPS or instr.opname == 'GET_ANEXT':
                    block.loop_header = True
                    self.loop_headers.add(block)
                    break
        
        for source, target in self.back_edges:
            target.loop_header = True
            self.loop_headers.add(target)
    
    def _compute_loop_bodies(self) -> None:
        """
        计算每个循环的循环体
        
        使用自然循环算法：
        对于回边 (B, H)，循环体 = {H} ∪ {从 B 沿前驱边反向可达且不经过 H 的所有节点}
        
        这是最标准的自然循环定义，保证：
        1. 循环体包含header
        2. 循环体包含所有回到header的路径上的节点
        3. 嵌套循环自然处理（内层循环的节点也在外层循环体中）
        """
        self.loop_bodies = {}
        
        for header in self.loop_headers:
            back_edge_sources = [src for src, tgt in self.back_edges if tgt == header]
            
            if back_edge_sources:
                body = self._compute_natural_loop(header, back_edge_sources)
            else:
                body = self._compute_for_loop_body(header)
            
            self.loop_bodies[header] = body
    
    def _compute_natural_loop(self, header: BasicBlock,
                               back_edge_sources: List[BasicBlock]) -> Set[BasicBlock]:
        body: Set[BasicBlock] = {header}
        stack: List[BasicBlock] = []

        non_self_sources = [s for s in back_edge_sources if s != header]

        if non_self_sources:
            for source in non_self_sources:
                if source not in body:
                    body.add(source)
                    stack.append(source)
        else:
            for source in back_edge_sources:
                if source != header:
                    if source not in body:
                        body.add(source)
                        stack.append(source)

        while stack:
            node = stack.pop()
            for pred in node.predecessors:
                if pred not in body:
                    body.add(pred)
                    stack.append(pred)

        return body
    
    def _compute_for_loop_body(self, header: BasicBlock) -> Set[BasicBlock]:
        """
        计算 for 循环体
        
        FOR_ITER 循环的 body 收集：
        header 有两个后继：fall-through（循环体）和 exit（迭代结束）
        从 fall-through 后继开始，收集所有可达且不经过 exit 的块，
        加上所有跳回 header 的块。
        """
        body: Set[BasicBlock] = {header}
        
        fall_through = self._get_for_iter_fall_through(header)
        if fall_through is None:
            if len(header.successors) >= 1:
                fall_through = min(header.successors, key=lambda s: s.start_offset)
            else:
                return body
        
        exit_succ = None
        for succ in header.successors:
            if succ != fall_through:
                exit_succ = succ
                break
        
        visited: Set[BasicBlock] = {header}
        if exit_succ:
            visited.add(exit_succ)
        
        worklist = [fall_through]
        while worklist:
            current = worklist.pop()
            if current in visited:
                continue
            visited.add(current)
            body.add(current)
            
            for succ in current.successors:
                if succ == header:
                    continue
                if succ in visited:
                    continue
                worklist.append(succ)
        
        return body
    
    def _get_for_iter_fall_through(self, header: BasicBlock) -> Optional[BasicBlock]:
        """
        获取 FOR_ITER 的 fall-through 后继
        
        FOR_ITER 的 fall-through 后继是偏移量紧接在 FOR_ITER 之后的块。
        """
        for instr in header.instructions:
            if instr.opname in FOR_ITER_OPS:
                next_offset = instr.offset + 2
                for succ in header.successors:
                    if succ.start_offset == next_offset:
                        return succ
                break
        return None
    
    def _compute_loop_depths(self) -> None:
        for block in self.cfg.blocks.values():
            block.loop_depth = 0
            block.in_loop = None
        
        for header, body in self.loop_bodies.items():
            for block in body:
                block.loop_depth += 1
                if block.in_loop is None or header.start_offset < block.in_loop.start_offset:
                    block.in_loop = header
    
    def _can_reach(self, from_block: BasicBlock, to_block: BasicBlock) -> bool:
        visited = set()
        worklist = [from_block]
        
        while worklist:
            block = worklist.pop()
            if block == to_block:
                return True
            if block in visited:
                continue
            visited.add(block)
            worklist.extend(block.successors)
        
        return False
    
    def get_loop_depth(self, block: BasicBlock) -> int:
        return block.loop_depth
    
    def is_in_loop(self, block: BasicBlock) -> bool:
        return block.loop_depth > 0
    
    def get_loop_header(self, block: BasicBlock) -> Optional[BasicBlock]:
        return block.in_loop
    
    def get_all_loops(self) -> Dict[BasicBlock, Set[BasicBlock]]:
        return self.loop_bodies.copy()


def analyze_dominators(cfg: ControlFlowGraph) -> DominatorAnalyzer:
    analyzer = DominatorAnalyzer(cfg)
    analyzer.analyze()
    return analyzer


def analyze_loops(cfg: ControlFlowGraph, dom_analyzer: Optional[DominatorAnalyzer] = None) -> LoopAnalyzer:
    if dom_analyzer is None:
        dom_analyzer = analyze_dominators(cfg)
    
    analyzer = LoopAnalyzer(cfg, dom_analyzer)
    analyzer.analyze()
    return analyzer
