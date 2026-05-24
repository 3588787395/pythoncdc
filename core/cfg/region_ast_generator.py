"""
基于区域的AST生成器

使用 RegionAnalyzer 的分析结果直接生成AST，替代 ast_generator_v2.py 中的补丁式生成。

核心原则：
- 从区域直接映射到AST，不需要二次修正
- 每种区域类型对应唯一的AST生成方法
- 复用 ExpressionReconstructor 进行表达式重建
- 输出格式与 CFGASTConverter 兼容
"""

import types
import sys
import json
import logging
import builtins as _builtins_module
from typing import List, Dict, Set, Optional, Tuple, Any, Union, Iterable

logger = logging.getLogger(__name__)

_DEBUG_BOOLOP = True
from collections import deque

_BUILTIN_NAMES = set(dir(_builtins_module))

_UNHANDLED = object()

MIN_INSTRS_FOR_SUBSCR_ASSIGN = 3  # value + container + index 三指令构成下标赋值 a[b]=c
MIN_INSTRS_FOR_CHAIN_ASSIGN_PATTERN = 3  # value + COPY + first_store 三指令构成链式赋值 a=b=c

# Python字节码操作数语义常量（参考Python字节码规范）
# 这些常量消除硬编码magic number，提高代码可读性
COPY_STACK_TOP = 1  # COPY指令：复制栈顶元素到栈顶（TOS -> TOS）
RAISE_RE_RAISE = 0  # RAISE_VARARGS.arg==0：re-raise当前异常（无参数raise）
RAISE_WITH_CAUSE = 2  # RAISE_VARARGS.arg==2：raise with cause子句
SWAP_TOP_TWO = 2  # SWAP指令：交换栈顶两个元素的位置
FINALLY_COPY_FULL = 0  # finally copy block标记：需要完整复制整个块

_NEGATE_CMP_MAP = {
    '==': '!=', '!=': '==',
    '<': '>=', '>=': '<',
    '>': '<=', '<=': '>',
    'in': 'not in', 'not in': 'in',
    'is': 'is not', 'is not': 'is',
}

def _negate_expr(expr: Dict[str, Any]) -> Dict[str, Any]:
    if expr.get('type') == 'UnaryOp' and expr.get('op') == 'not':
        return expr.get('operand', expr)
    if expr.get('type') == 'Compare':
        ops = expr.get('ops')
        op = expr.get('op')
        if ops and isinstance(ops, list) and len(ops) == 1:
            op_val = ops[0]
            if isinstance(op_val, dict):
                op_type = op_val.get('type', '')
                negate_map = {
                    'Eq': 'NotEq', 'NotEq': 'Eq',
                    'Lt': 'GtE', 'GtE': 'Lt',
                    'Gt': 'LtE', 'LtE': 'Gt',
                    'In': 'NotIn', 'NotIn': 'In',
                    'Is': 'IsNot', 'IsNot': 'Is',
                }
                if op_type in negate_map:
                    r = dict(expr); r['ops'] = [{'type': negate_map[op_type]}]; return r
            elif op_val in _NEGATE_CMP_MAP:
                r = dict(expr); r['ops'] = [_NEGATE_CMP_MAP[op_val]]; return r
        if op and isinstance(op, str) and op in _NEGATE_CMP_MAP:
            r = dict(expr); r['op'] = _NEGATE_CMP_MAP[op]; return r
    return {'type': 'UnaryOp', 'op': 'not', 'operand': expr}

from .basic_block import BasicBlock, Instruction
from .cfg_builder import ControlFlowGraph
from .dominator_analyzer import FOR_ITER_OPS, BACKWARD_JUMP_OPS, FORWARD_JUMP_OPS, PLACEHOLDER_OPS
from .region_analyzer import (
    RegionAnalyzer, Region, RegionType, BlockRole,
    IfRegion, LoopRegion, TryExceptRegion, WithRegion, MatchRegion, AssertRegion,
    BoolOpRegion, TernaryRegion,
    CONDITIONAL_JUMP_OPS, SHORT_CIRCUIT_JUMP_OPS, NONE_CHECK_OPS,
    FORWARD_CONDITIONAL_JUMP_OPS, BACKWARD_CONDITIONAL_JUMP_OPS,
    NOISE_OPS,
)
from .ast_generator_v2 import ExpressionReconstructor
from .comprehension_generator import ComprehensionGenerator
from .opcode_feature_detector import get_opcode_detector


class RegionASTGenerator:
    """
    基于区域的AST生成器

    从 RegionAnalyzer 产生的区域树直接映射为AST。
    每种区域类型对应唯一的AST节点类型，不需要后处理修正。
    """

    def __init__(self, cfg: ControlFlowGraph, recursive: bool = True, parent_code=None, top_level_code=None):
        self.cfg = cfg
        self.recursive = recursive
        self.parent_code = parent_code
        self._top_level_code = top_level_code
        self.region_analyzer = RegionAnalyzer(cfg, parent_code=self.parent_code, top_level_code=self._top_level_code)
        self.expr_reconstructor = ExpressionReconstructor(cfg)
        self.region_analyzer.expr_reconstructor = self.expr_reconstructor
        self.comp_generator = ComprehensionGenerator(self.expr_reconstructor)

        self.regions: List[Region] = []
        self.generated_blocks: Set[BasicBlock] = set()
        self.generated_offsets: Set[int] = set()
        self._generating_regions: Set[int] = set()
        self._generated_regions: Set[int] = set()
        self._trailing_returns: List[Dict[str, Any]] = []
        self._loop_depth: int = 0
        self._current_loop: Optional['LoopRegion'] = None
        self._try_depth: int = 0
        self._post_break_blocks: List[BasicBlock] = []
        self._with_cleanup_generated_blocks: Set[BasicBlock] = set()
        self.detector = get_opcode_detector()

    def block_role(self, block: 'BasicBlock') -> 'BlockRole':
        return self.region_analyzer.get_block_role(block)

    def generate(self) -> Dict[str, Any]:
        from core.cfg.region_analyzer import LoopRegion
        func_name = self.cfg.name
        if func_name in ('<listcomp>', '<dictcomp>', '<setcomp>', '<genexpr>'):
            return self.comp_generator.generate_comprehension_function(self.cfg)

        self.regions = self.region_analyzer.analyze()

        entry_block = self.cfg.entry_block
        if entry_block is not None:
            if self.region_analyzer.metadata.get('is_generator_entry'):
                self.generated_blocks.add(entry_block)
                entry_block = self.region_analyzer.metadata.get('generator_entry_block', entry_block)

        ast_nodes = []

        if entry_block and entry_block not in self.generated_blocks:
            entry_region = self.region_analyzer.get_entry_region_for_block(entry_block) or self.region_analyzer.get_region_for_block(entry_block)
            for r in self.regions:
                if isinstance(r, LoopRegion) and (r.condition_block is entry_block or
                    (r.header_block and entry_block.start_offset in [s.start_offset for s in r.header_block.predecessors])):
                    entry_region = r
                    break
            if isinstance(entry_region, LoopRegion) and (entry_region.condition_block == entry_block or
                (entry_region.header_block and entry_block.start_offset in [s.start_offset for s in entry_region.header_block.predecessors])):
                _wildcard_match = self._detect_undetected_wildcard_match(entry_block)
                if _wildcard_match:
                    _match_ast = self._generate_match(_wildcard_match)
                    if _match_ast:
                        ast_nodes.append(_match_ast)
                self.generated_blocks.add(entry_block)
                pass
            elif isinstance(entry_region, IfRegion) and entry_region.condition_block == entry_block:
                pass
            elif isinstance(entry_region, BoolOpRegion):
                pass
            elif isinstance(entry_region, TernaryRegion):
                pass
            elif isinstance(entry_region, AssertRegion):
                assert_id = id(entry_region)
                if assert_id not in self._generated_regions and assert_id not in self._generating_regions:
                    assert_ast = self._generate_assert(entry_region)
                    if assert_ast:
                        ast_nodes.append(assert_ast)
                    for b in entry_region.blocks:
                        self.generated_blocks.add(b)
                    self._generated_regions.add(assert_id)
                self.generated_blocks.add(entry_block)
            else:
                _entry_region = self.region_analyzer.get_region_for_block(entry_block)
                entry_ast = []

                if _entry_region and isinstance(_entry_region, (MatchRegion, BoolOpRegion, TernaryRegion)):
                    entry_ast = []
                elif _entry_region and isinstance(_entry_region, (IfRegion, LoopRegion)):
                    _pre_stmts: List[Dict[str, Any]] = []
                    _stmt_instrs: List[Instruction] = []
                    _import_pending_store = False

                    for _instr in entry_block.instructions:
                        if _instr.opname in ('RESUME', 'NOP', 'CACHE', 'POP_TOP', 'PUSH_NULL'):
                            continue
                        if _instr.opname in FORWARD_JUMP_OPS or _instr.opname in BACKWARD_JUMP_OPS:
                            break
                        if _instr.opname in ('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE'):
                            break
                        if _instr.opname in ('POP_EXCEPT', 'PUSH_EXC_INFO', 'RERAISE'):
                            continue
                        if _instr.opname == 'IMPORT_NAME':
                            module_name = _instr.argval if _instr.argval else ''
                            _instr_idx = entry_block.instructions.index(_instr)
                            _has_import_from = False
                            _scan_start = _instr_idx + 1
                            for _s in range(_scan_start, min(_scan_start + 3, len(entry_block.instructions))):
                                if entry_block.instructions[_s].opname == 'IMPORT_FROM':
                                    _has_import_from = True
                                    break
                                elif entry_block.instructions[_s].opname not in ('LOAD_CONST', 'PUSH_NULL'):
                                    break
                            if _has_import_from:
                                from_names = []
                                _si = _instr_idx + 1
                                while _si < len(entry_block.instructions) - 1:
                                    _sc = entry_block.instructions[_si]
                                    _sn = entry_block.instructions[_si + 1]
                                    if _sc.opname == 'IMPORT_FROM':
                                        _imp_n = _sc.argval if _sc.argval else ''
                                        _sto_n = None
                                        if _sn.opname in ('STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL'):
                                            _sto_n = _sn.argval
                                            _si += 2
                                        elif _sn.opname == 'IMPORT_FROM':
                                            _sto_n = _imp_n
                                            _si += 1
                                        else:
                                            _sto_n = _imp_n
                                            _si += 1
                                            continue
                                        if _imp_n:
                                            from_names.append((_imp_n, _sto_n))
                                        continue
                                    elif _sc.opname in ('STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL'):
                                        _si += 1
                                        continue
                                    elif _sc.opname in ('LOAD_CONST', 'PUSH_NULL', 'POP_TOP'):
                                        _si += 1
                                        continue
                                    else:
                                        break
                                if from_names:
                                    _nl = []
                                    for _ipd, _std in from_names:
                                        if _ipd != _std:
                                            _nl.append({'name': _ipd, 'asname': _std})
                                        else:
                                            _nl.append({'name': _ipd, 'asname': None})
                                    _pre_stmts.append({'type': 'ImportFrom', 'module': module_name, 'names': _nl})
                            else:
                                _sn_list = []
                                for _si2 in range(_instr_idx + 1, len(entry_block.instructions)):
                                    _nxt = entry_block.instructions[_si2]
                                    if _nxt.opname in ('STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL'):
                                        _sn_list.append(_nxt.argval)
                                    elif _nxt.opname == 'POP_TOP':
                                        pass
                                    elif _nxt.opname in ('LOAD_CONST',) and not _sn_list:
                                        pass
                                    else:
                                        break
                                if _sn_list:
                                    if len(_sn_list) == 1 and _sn_list[0] != module_name:
                                        _aliases = [{'name': module_name, 'asname': _sn_list[0]}]
                                    else:
                                        _aliases = [{'name': _n, 'asname': None} for _n in _sn_list]
                                    _pre_stmts.append({'type': 'Import', 'names': _aliases})
                                else:
                                    _pre_stmts.append({'type': 'Import', 'names': [{'name': module_name, 'asname': None}]})
                            _stmt_instrs = []
                            _import_pending_store = True
                            continue
                        if _instr.opname == 'IMPORT_FROM':
                            _import_pending_store = True
                            continue
                        if _instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                            if _import_pending_store:
                                _stmt_instrs = []
                                _import_pending_store = False
                                continue
                            _stmt_instrs.append(_instr)
                            _stmt = self._build_store_statement(_stmt_instrs, block=entry_block)
                            if _stmt:
                                _pre_stmts.append(_stmt)
                            _stmt_instrs = []
                            continue
                        _stmt_instrs.append(_instr)

                    self.generated_blocks.add(entry_block)
                    entry_ast = _pre_stmts
                elif _entry_region and isinstance(_entry_region, WithRegion):
                    _pre_stmts: List[Dict[str, Any]] = []
                    _stmt_instrs: List[Instruction] = []
                    _import_pending_store = False
                    _unpack_targets: List[str] = []

                    for _instr in entry_block.instructions:
                        if _instr.opname == 'BEFORE_WITH':
                            break
                        if _instr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                            continue
                        if _instr.opname == 'POP_TOP':
                            if _stmt_instrs:
                                expr = self.expr_reconstructor.reconstruct(_stmt_instrs)
                                if expr:
                                    _pre_stmts.append({'type': 'Expr', 'value': expr})
                                _stmt_instrs = []
                            continue
                        if _instr.opname == 'IMPORT_NAME':
                            _import_result = self._process_instruction(_instr, entry_block, _stmt_instrs)
                            if _import_result:
                                _pre_stmts.extend(_import_result)
                            _stmt_instrs = []
                            _import_pending_store = True
                            continue
                        if _instr.opname == 'IMPORT_FROM':
                            _import_pending_store = True
                            continue
                        if _instr.opname == 'UNPACK_SEQUENCE':
                            _stmt_instrs.append(_instr)
                            _unpack_targets = []
                            continue
                        if _instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                            if _import_pending_store:
                                _stmt_instrs = []
                                _import_pending_store = False
                                continue
                            if _stmt_instrs and any(i.opname == 'IMPORT_NAME' for i in _stmt_instrs):
                                _stmt_instrs = []
                                continue
                            if _unpack_targets is not None and any(i.opname == 'UNPACK_SEQUENCE' for i in _stmt_instrs):
                                _unpack_targets.append(_instr.argval)
                                _stmt_instrs.append(_instr)
                                has_more_unpack = False
                                for _peek in entry_block.instructions[entry_block.instructions.index(_instr) + 1:]:
                                    if _peek.opname == 'BEFORE_WITH':
                                        break
                                    if _peek.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                                        has_more_unpack = True
                                        break
                                    if _peek.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                                        break
                                if not has_more_unpack:
                                    _stmt = self._build_store_statement(_stmt_instrs, block=entry_block)
                                    if _stmt and _unpack_targets:
                                        targets = [{'type': 'Name', 'id': t, 'ctx': 'Store'} for t in _unpack_targets]
                                        _stmt = {
                                            'type': 'Assign',
                                            'targets': [{'type': 'Tuple', 'elts': targets, 'ctx': 'Store'}],
                                            'value': _stmt.get('value'),
                                        }
                                        _pre_stmts.append(_stmt)
                                    elif _stmt:
                                        _pre_stmts.append(_stmt)
                                    _stmt_instrs = []
                                    _unpack_targets = []
                                continue
                            _stmt_instrs.append(_instr)
                            _stmt = self._build_store_statement(_stmt_instrs, block=entry_block)
                            if _stmt:
                                _pre_stmts.append(_stmt)
                            _stmt_instrs = []
                            continue
                        _stmt_instrs.append(_instr)

                    self.generated_blocks.add(entry_block)
                    entry_ast = _pre_stmts
                elif _entry_region and isinstance(_entry_region, TryExceptRegion):
                    _wildcard_match = self._detect_undetected_wildcard_match(entry_block)
                    if _wildcard_match:
                        _match_ast = self._generate_match(_wildcard_match)
                        if _match_ast:
                            ast_nodes.append(_match_ast)
                    _pre_stmts: List[Dict[str, Any]] = []
                    _stmt_instrs: List[Instruction] = []

                    for _instr in entry_block.instructions:
                        if _instr.opname in ('RESUME', 'NOP', 'CACHE', 'POP_TOP', 'PUSH_NULL'):
                            continue
                        if _instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                            _stmt_instrs.append(_instr)
                            _stmt = self._build_store_statement(_stmt_instrs, block=entry_block)
                            if _stmt:
                                _pre_stmts.append(_stmt)
                            _stmt_instrs = []
                            continue
                        _stmt_instrs.append(_instr)

                    self.generated_blocks.add(entry_block)
                    entry_ast = _pre_stmts
                else:
                    _wildcard_match = self._detect_undetected_wildcard_match(entry_block)
                    if _wildcard_match:
                        entry_ast = [self._generate_match(_wildcard_match)]
                    else:
                        entry_ast = self._generate_block_statements(entry_block)

                if entry_ast:
                    ast_nodes.extend(entry_ast)

        top_level = [r for r in self.regions if r.parent is None]
        if _DEBUG_BOOLOP:
            #print(f"[DEBUG generate] ({self.cfg.name}) ALL regions: {[(type(r).__name__, r.entry.start_offset if r.entry else '?', r.region_type.name, r.parent.entry.start_offset if r.parent else None) for r in self.regions]}")
            #print(f"[DEBUG generate] ({self.cfg.name}) TOP-LEVEL: {[(type(r).__name__, r.entry.start_offset if r.entry else '?', r.region_type.name) for r in top_level]}")
            pass
        with_regions = [r for r in self.regions if isinstance(r, WithRegion)]
        with_parent_ids = set()
        for wr in with_regions:
            if wr.parent is not None:
                with_parent_ids.add(id(wr.parent))
        with_internal_blocks = set()
        for wr in with_regions:
            for b in wr.blocks:
                if b != wr.entry:
                    with_internal_blocks.add(b)
        filtered = []
        for r in top_level:
            if r.region_type == RegionType.PASS:
                filtered.append(r)
                continue
            if isinstance(r, (TernaryRegion, MatchRegion)):
                filtered.append(r)
                continue
            is_contained = False
            for other in self.regions:
                if other is not r and r.entry and r.entry in other.blocks:
                    if other.region_type != RegionType.BASIC:
                        if other.parent is r:
                            continue
                        if len(r.blocks) > len(other.blocks):
                            continue
                        if isinstance(other, BoolOpRegion) and isinstance(r, LoopRegion):
                            if r.condition_block and r.condition_block in other.blocks:
                                pass
                            else:
                                is_contained = True
                                break
                        elif isinstance(other, BoolOpRegion) and isinstance(r, IfRegion):
                            if r.condition_block and r.condition_block in other.blocks:
                                pass
                            else:
                                is_contained = True
                                break
                        elif isinstance(r, BoolOpRegion) and isinstance(other, IfRegion):
                            if r.entry and r.entry == other.entry:
                                entry_owner = self.region_analyzer.block_to_region.get(r.entry)
                                if entry_owner is r:
                                    pass
                                else:
                                    is_contained = True
                                    break
                            else:
                                is_contained = True
                                break
                        elif isinstance(other, TernaryRegion) and isinstance(r, TernaryRegion):
                            if r.entry and r.entry == other.merge_block:
                                pass
                            else:
                                is_contained = True
                                break
                        elif isinstance(other, TernaryRegion) and isinstance(r, (BoolOpRegion, IfRegion)):
                            if r.entry and r.entry in other.blocks:
                                is_contained = True
                                break
                        elif isinstance(other, IfRegion) and isinstance(r, LoopRegion):
                            if r.condition_block and (r.condition_block in other.blocks or r.condition_block == other.entry):
                                pass
                            elif r.header_block and r.header_block in other.blocks:
                                pass
                            else:
                                is_contained = True
                                break
                        elif isinstance(r, IfRegion) and isinstance(other, TryExceptRegion):
                            # if_try嵌套：IfRegion的entry在TryExceptRegion的entry之前，
                            # 说明IfRegion是外层结构（if体内包含try），不应被标记为contained
                            if (r.entry and other.entry and
                                r.entry.start_offset < other.entry.start_offset):
                                pass
                            else:
                                is_contained = True
                                break
                        else:
                            is_contained = True
                            break
            if not is_contained and isinstance(r, TryExceptRegion):
                if r.entry and r.entry in with_internal_blocks and id(r) not in with_parent_ids:
                    is_contained = True
            if not is_contained:
                filtered.append(r)

        _loop_entries = set()
        _loop_block_sets = []
        _loop_entry_to_region = {}
        _wrapped_loop_entries = set()
        for r in filtered:
            if isinstance(r, LoopRegion):
                _loop_entries.add(r.entry)
                _loop_block_sets.append(set(r.blocks))
                if r.entry:
                    _loop_entry_to_region[r.entry] = r
        if _loop_block_sets:
            _refined = []
            for r in filtered:
                if isinstance(r, IfRegion) and r.blocks:
                    _rbs = set(r.blocks)
                    if any(_rbs >= _lbs for _lbs in _loop_block_sets):
                        _is_outer_wrapper = False
                        if r.entry and hasattr(r, 'condition_block') and r.condition_block:
                            for _lr_entry, _lr in _loop_entry_to_region.items():
                                if (_rbs >= set(_lr.blocks) and
                                    r.condition_block.start_offset < _lr_entry.start_offset):
                                    _is_outer_wrapper = True
                                    _wrapped_loop_entries.add(_lr_entry)
                                    break
                        if _is_outer_wrapper:
                            pass
                        else:
                            continue
                _refined.append(r)
            filtered = [r for r in _refined if not (isinstance(r, LoopRegion) and r.entry in _wrapped_loop_entries)]

        for r in self.regions:
            if isinstance(r, (TernaryRegion, MatchRegion)) and r.parent is not None:
                if r not in filtered:
                    parent = r.parent
                    is_nested_in_tm_parent = False
                    while parent:
                        if isinstance(parent, (TernaryRegion, MatchRegion)):
                            is_nested_in_tm_parent = True
                            break
                        parent = getattr(parent, 'parent', None)
                    if not is_nested_in_tm_parent:
                        filtered.append(r)
        boolop_regions = [r for r in filtered if isinstance(r, BoolOpRegion)]
        other_regions = [r for r in filtered if not isinstance(r, BoolOpRegion)]
        
        loop_condition_boolops = set()
        ternary_absorbed_boolops = set()
        for br in boolop_regions:
            for lr in other_regions:
                if isinstance(lr, LoopRegion):
                    overlap = len(set(br.blocks) & set(lr.blocks))
                    cond_match = lr.condition_block and (
                        lr.condition_block in br.blocks
                        or lr.condition_block == br.condition_block
                    )
                    if overlap > 0 and cond_match:
                        loop_condition_boolops.add(id(br))
                        break
                elif isinstance(lr, TernaryRegion):
                    if hasattr(lr, 'condition_chain_blocks') and lr.condition_chain_blocks:
                        chain_block_objs = set()
                        for item in lr.condition_chain_blocks:
                            if hasattr(item, 'start_offset'):
                                chain_block_objs.add(item)
                            elif isinstance(item, tuple) and len(item) >= 1 and hasattr(item[0], 'start_offset'):
                                chain_block_objs.add(item[0])
                        boolop_chain_blocks = set(cb for cb, _ in br.op_chain)
                        if chain_block_objs and boolop_chain_blocks and boolop_chain_blocks <= chain_block_objs:
                            ternary_absorbed_boolops.add(id(br))
                            break

        boolop_regions = [r for r in boolop_regions
                          if id(r) not in loop_condition_boolops
                          and id(r) not in ternary_absorbed_boolops]
        
        sorted_other = sorted(other_regions, key=lambda r: r.entry.start_offset if r.entry else 0)
        top_level_regions = boolop_regions + sorted_other

        for region in top_level_regions:
            if region.region_type != RegionType.BASIC and region.blocks:
                if all(b in self.generated_blocks for b in region.blocks):
                    if isinstance(region, (TernaryRegion, MatchRegion)):
                        if region.entry and region.entry in self.generated_blocks:
                            continue
                    else:
                        if _DEBUG_BOOLOP:
                            pass
                        continue
            if _DEBUG_BOOLOP:
                #print(f"[DEBUG generate] Processing {type(region).__name__}(entry={region.entry.start_offset}), blocks={sorted(b.start_offset for b in region.blocks)}, gen={sorted(b.start_offset for b in self.generated_blocks)}")
                pass
            region_ast = self._generate_region(region)
            if region_ast:
                if isinstance(region_ast, list):
                    ast_nodes.extend(region_ast)
                else:
                    ast_nodes.append(region_ast)

        decorator_names = set()
        for node in ast_nodes:
            if isinstance(node, dict) and node.get('type') in ('FunctionDef', 'AsyncFunctionDef'):
                for dec in node.get('decorator_list', []):
                    if isinstance(dec, dict):
                        if dec.get('type') == 'Name':
                            decorator_names.add(dec.get('id'))
                        elif dec.get('type') == 'Call':
                            f = dec.get('func', {})
                            if isinstance(f, dict) and f.get('type') == 'Name':
                                decorator_names.add(f.get('id'))
        if decorator_names:
            filtered = []
            for node in ast_nodes:
                if (isinstance(node, dict) and node.get('type') == 'Expr' and
                    isinstance(node.get('value'), dict) and
                    node.get('value', {}).get('type') == 'Name' and
                    node.get('value', {}).get('id') in decorator_names):
                    continue
                filtered.append(node)
            ast_nodes = filtered

        if self._trailing_returns:
            if func_name == '<module>':
                pass
            else:
                ast_nodes.extend(self._trailing_returns)

        if func_name == '<module>':
            if not ast_nodes:
                ast_nodes = [{'type': 'Pass'}]
            
            _has_while_loop = any(r.region_type.name == 'WHILE_LOOP' for r in self.regions)
            if not _has_while_loop:
                code_obj = getattr(self.cfg, 'code', None)
                if code_obj and hasattr(code_obj, 'co_consts'):
                    _consts = code_obj.co_consts
                    if _consts and len(_consts) >= 1 and (_consts[0] is False or _consts[0] is True):
                        _all_instrs = []
                        for b in self.cfg.blocks.values():
                            _all_instrs.extend(b.instructions)
                        _meaningful = [i for i in _all_instrs if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'RETURN_VALUE', 'RETURN_CONST')]
                        if not _meaningful or len(_meaningful) <= 2:
                            _cond_val = _consts[0]
                            if _cond_val is True and len(_consts) == 2 and _consts[1] is None:
                                ast_nodes = [{'type': 'If', 'test': {'type': 'Constant', 'value': True}, 'body': [{'type': 'Pass'}], 'orelse': None}]
                            else:
                                ast_nodes = [{'type': 'If', 'test': {'type': 'Constant', 'value': _cond_val}, 'body': [{'type': 'Pass'}], 'orelse': None}]
            
            code_obj = getattr(self.cfg, 'code', None)
            scope_decls = self.region_analyzer.global_declarations
            if scope_decls:
                ast_nodes = scope_decls + ast_nodes
            
            return {
                'type': 'Module',
                'body': ast_nodes,
            }

        code_obj = getattr(self.cfg, 'code', None)
        is_class_body = (code_obj is not None and
                         hasattr(code_obj, 'co_flags') and
                         not (code_obj.co_flags & 0x0001) and
                         func_name != '<module>')

        if is_class_body:
            return self._build_class_def(func_name, ast_nodes)
        else:
            return self._build_function_def(func_name, ast_nodes)


    def _build_function_def(self, func_name: str = None, body: List[Dict[str, Any]] = None,
                             func_obj: Dict[str, Any] = None, decorator: Any = None) -> Dict[str, Any]:
        is_async = False

        if func_obj is not None:
            code_obj = func_obj.get('code')
            if code_obj is None:
                return {'type': 'Pass'}

            if isinstance(code_obj, dict) and code_obj.get('type') == 'Constant':
                code_obj = code_obj.get('value')

            if isinstance(code_obj, dict) and code_obj.get('type') == 'CodeObject':
                code_obj = code_obj.get('code')

            if not isinstance(code_obj, types.CodeType):
                return {'type': 'Pass'}

            func_name = getattr(code_obj, 'co_name', '<unknown>')
            args = self._extract_function_args(code_obj)

            if isinstance(func_obj, dict) and 'defaults' in func_obj:
                pos_defaults_from_obj = func_obj.get('defaults')
                if pos_defaults_from_obj:
                    defaults_list = []
                    if isinstance(pos_defaults_from_obj, dict) and pos_defaults_from_obj.get('type') == 'Constant':
                        raw_value = pos_defaults_from_obj.get('value')
                        if isinstance(raw_value, (tuple, list)):
                            for val in raw_value:
                                defaults_list.append({'type': 'Constant', 'value': val})
                        else:
                            defaults_list = [pos_defaults_from_obj]
                    elif isinstance(pos_defaults_from_obj, dict) and pos_defaults_from_obj.get('type') == 'Tuple':
                        defaults_list = pos_defaults_from_obj.get('elsts', [])
                    elif isinstance(pos_defaults_from_obj, list):
                        defaults_list = pos_defaults_from_obj
                    elif isinstance(pos_defaults_from_obj, tuple):
                        defaults_list = [{'type': 'Constant', 'value': v} for v in pos_defaults_from_obj]
                    if defaults_list:
                        args['defaults'] = defaults_list

            body_stmts = [{'type': 'Pass'}]
            if self.recursive:
                try:
                    from .cfg_builder import CFGBuilder
                    builder = CFGBuilder()
                    nested_cfg = builder.build(code_obj)
                    nested_gen = RegionASTGenerator(nested_cfg, recursive=True, parent_code=self.cfg.code, top_level_code=self._top_level_code)
                    nested_ast = nested_gen.generate()
                    if nested_ast and nested_ast.get('body'):
                        body_stmts = nested_ast['body']
                except Exception:
                    pass

            body = body_stmts
            is_async = bool(code_obj.co_flags & 0x80) or bool(code_obj.co_flags & 0x100) or bool(code_obj.co_flags & 0x200)
        else:
            args = self._extract_function_args()

            code_obj = getattr(self.cfg, 'code', None)
            func_code_obj = None
            if code_obj and hasattr(code_obj, 'co_name') and code_obj.co_name != func_name:
                if hasattr(code_obj, 'co_consts'):
                    for const in code_obj.co_consts:
                        if hasattr(const, 'co_name') and const.co_name == func_name:
                            func_code_obj = const
                            break
            scope_stmts = self.region_analyzer._detect_global_declarations(func_code_obj or code_obj) if (func_code_obj or code_obj) else []
            if not scope_stmts:
                scope_stmts = [s for s in body if isinstance(s, dict) and s.get('type') in ('Global', 'Nonlocal')]
            if scope_stmts:
                body = [s for s in body if not (isinstance(s, dict) and s.get('type') in ('Global', 'Nonlocal'))]
                body = scope_stmts + body

            code_obj = getattr(self.cfg, 'code', None)
            if code_obj and hasattr(code_obj, 'co_flags'):
                is_async = bool(code_obj.co_flags & 0x80) or bool(code_obj.co_flags & 0x100) or bool(code_obj.co_flags & 0x200)

        filtered_body = body
        if filtered_body and isinstance(filtered_body, list):
            has_explicit_return = any(
                isinstance(s, dict) and s.get('type') == 'Return' and not self._is_trailing_return_none_statement(s)
                for s in filtered_body
            )
            if not has_explicit_return:
                if filtered_body and self._is_trailing_return_none_statement(filtered_body[-1]):
                    filtered_body = filtered_body[:-1]
                if func_obj is None:
                    has_preceding_pass = (
                        len(filtered_body) >= 2 and
                        isinstance(filtered_body[-2], dict) and
                        filtered_body[-2].get('type') == 'Pass' and
                        isinstance(filtered_body[-1], dict) and
                        filtered_body[-1].get('type') == 'Return'
                    )
                    if has_preceding_pass:
                        filtered_body = filtered_body[:-1]
                if not filtered_body:
                    filtered_body = [{'type': 'Pass'}]

        if func_name == '<lambda>':
            body_expr = None
            if filtered_body:
                for s in reversed(filtered_body):
                    if isinstance(s, dict) and s.get('type') == 'Return':
                        body_expr = s.get('value')
                        break
                if body_expr is None and len(filtered_body) == 1:
                    s = filtered_body[0]
                    if isinstance(s, dict) and s.get('type') == 'Return':
                        body_expr = s.get('value')
                    elif isinstance(s, dict) and s.get('type') == 'If':
                        # [DEPRECATED TERNARY PATH] Lambda body中的内联IfExp生成
                        # 这是历史遗留的多路径问题，理想情况下应该通过 _generate_ternary 处理
                        # 保留此代码以维持向后兼容性，未来应迁移到统一的TernaryRegion生成流程
                        # TODO: 考虑将Lambda中的三元表达式识别为TernaryRegion并委托给_generate_ternary
                        if_body = s.get('body', [])
                        else_body = s.get('orelse', [])
                        if len(if_body) == 1 and isinstance(if_body[0], dict) and if_body[0].get('type') == 'Return':
                            if len(else_body) == 1 and isinstance(else_body[0], dict) and else_body[0].get('type') == 'Return':
                                body_expr = {
                                    'type': 'IfExp',
                                    'test': s.get('test'),
                                    'body': if_body[0].get('value', {'type': 'Constant', 'value': None}),
                                    'orelse': else_body[0].get('value', {'type': 'Constant', 'value': None}),
                                }
                            elif len(else_body) == 1 and isinstance(else_body[0], dict) and else_body[0].get('type') == 'If':
                                pass
                            else:
                                body_expr = {
                                    'type': 'IfExp',
                                    'test': s.get('test'),
                                    'body': if_body[0].get('value', {'type': 'Constant', 'value': None}),
                                    'orelse': {'type': 'Constant', 'value': None},
                                }
            if body_expr is None:
                body_expr = {'type': 'Constant', 'value': None}
            return {
                'type': 'Lambda',
                'args': args,
                'body': body_expr,
            }

        result = {
            'type': 'AsyncFunctionDef' if is_async else 'FunctionDef',
            'name': func_name,
            'args': args,
            'body': filtered_body,
            'decorator_list': [],
            'returns': None,
        }

        if decorator:
            if isinstance(decorator, dict) and decorator.get('type') == 'Call':
                decorator_list = self._extract_decorators(decorator)
                if not decorator_list:
                    result['decorator_list'] = [decorator]
                else:
                    result['decorator_list'] = decorator_list
            elif isinstance(decorator, str):
                result['decorator_list'] = [{'type': 'Name', 'id': decorator}]

        if not result.get('decorator_list') and func_obj is not None:
            try:
                for block in self.cfg.blocks.values():
                    instructions = block.instructions
                    for i, instr in enumerate(instructions):
                        if instr.opname == 'MAKE_FUNCTION':
                            if i > 0:
                                prev_instr = instructions[i - 1]
                                if prev_instr.opname == 'LOAD_CONST' and prev_instr.argval is not func_obj:
                                    continue
                            bytecode_decorators = self._reconstruct_decorator_chain(instructions, i)
                            if bytecode_decorators:
                                result['decorator_list'] = bytecode_decorators
                                break
                    if result.get('decorator_list'):
                        break
            except Exception:
                pass

        return result

    def _extract_decorators(self, call_node: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从装饰器调用节点中提取装饰器列表（修复F08：无参装饰器不加括号）

        Args:
            call_node: 可能包含装饰器的Call节点，如:
                - Call(func=Name('dec'), args=[FunctionObject])  -- 单层无参
                - Call(func=Call(func=Name('dec'), args=[...]), args=[FunctionObject])  -- 单层带参
                - Call(func=Name('dec1'), args=[Call(func=Name('dec2'), args=[FunctionObject])])  -- 多层

        Returns:
            装饰器AST节点列表。无参装饰器为Name节点（@dec），带参为Call节点（@dec(args)）
        """
        if not isinstance(call_node, dict) or call_node.get('type') != 'Call':
            return []

        func = call_node.get('func', {})
        args = call_node.get('args', [])

        if func.get('type') in ('Name', 'Attribute'):
            if args:
                first_arg = args[0]
                if first_arg.get('type') == 'FunctionObject':
                    return [func]
                elif first_arg.get('type') == 'Call':
                    inner_decs = self._extract_decorators(first_arg)
                    return [func] + inner_decs if inner_decs else []
            return []

        elif func.get('type') == 'Call':
            inner_func = func.get('func', {})
            inner_args = func.get('args', [])
            if inner_func.get('type') in ('Name', 'Attribute'):
                decorator_with_args = {
                    'type': 'Call',
                    'func': inner_func,
                    'args': inner_args,
                }
                if args:
                    first_arg = args[0]
                    if first_arg.get('type') == 'FunctionObject':
                        return [decorator_with_args]
                    elif first_arg.get('type') == 'Call':
                        inner_decs = self._extract_decorators(first_arg)
                        return [decorator_with_args] + inner_decs if inner_decs else []
                else:
                    inner_decs = self._extract_decorators(func)
                    return inner_decs
            elif inner_func.get('type') == 'Call':
                inner_decs = self._extract_decorators(func)
                if inner_decs:
                    return [decorator_with_args] + inner_decs if args else inner_decs

        return []

    def _reconstruct_decorator_chain(self, instructions: List[Any], make_func_idx: int) -> Optional[List[Dict[str, Any]]]:
        """从字节码指令中重建装饰器链（基于MAKE_FUNCTION位置向前搜索）

        Args:
            instructions: 基本块指令列表
            make_func_idx: MAKE_FUNCTION指令的索引

        Returns:
            装饰器AST节点列表，无法识别时返回None
        """
        if make_func_idx <= 0:
            return None

        decorators = []
        idx = make_func_idx - 1

        while idx >= 0:
            instr = instructions[idx]
            opname = instr.opname

            if opname in ('LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF', 'LOAD_ATTR'):
                dec_name = instr.argval
                if dec_name and not dec_name.startswith('__'):
                    peek_idx = idx + 1
                    has_call = False
                    has_args = False
                    arg_nodes = []

                    while peek_idx < make_func_idx:
                        next_op = instructions[peek_idx].opname
                        if next_op in ('CALL', 'CALL_FUNCTION', 'CALL_METHOD',
                                       'CALL_FUNCTION_KW', 'CALL_FUNCTION_EX',
                                       'PRECALL', 'PUSH_NULL'):
                            if next_op in ('CALL', 'CALL_FUNCTION', 'CALL_METHOD',
                                           'CALL_FUNCTION_KW', 'CALL_FUNCTION_EX'):
                                has_call = True
                            peek_idx += 1
                        elif next_op in ('LOAD_CONST',):
                            arg_val = instructions[peek_idx].argval
                            arg_nodes.append({'type': 'Constant', 'value': arg_val})
                            has_args = True
                            peek_idx += 1
                        elif next_op in ('LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL',
                                         'LOAD_DEREF', 'LOAD_ATTR'):
                            arg_name = instructions[peek_idx].argval
                            arg_nodes.append({'type': 'Name', 'id': arg_name, 'ctx': 'Load'})
                            has_args = True
                            peek_idx += 1
                        else:
                            break

                    if has_args:
                        decorators.insert(0, {
                            'type': 'Call',
                            'func': {'type': 'Name', 'id': dec_name, 'ctx': 'Load'},
                            'args': arg_nodes,
                        })
                    else:
                        decorators.insert(0, {'type': 'Name', 'id': dec_name, 'ctx': 'Load'})

                    idx -= 1
                    continue

            elif opname in ('LOAD_CONST',) and isinstance(instr.argval, type(None)):
                idx -= 1
                continue

            elif opname in ('PUSH_NULL',):
                idx -= 1
                continue

            break

        return decorators if decorators else None

    def _build_effective_stmts(self, block: BasicBlock, effective: List[Instruction]) -> List[Dict[str, Any]]:
        stmts, expr_instrs, seen_for = [], [], set()
        for instr in effective:
            if instr.opname in ('RESUME', 'NOP', 'CACHE'):
                continue
            for_targets = self._current_loop.metadata.get('for_target_names', set()) if self._current_loop else set()
            if (instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
                    and instr.argval in for_targets and instr.argval not in seen_for):
                seen_for.add(instr.argval)
                if expr_instrs:
                    e = self.expr_reconstructor.reconstruct(expr_instrs)
                    if e:
                        stmts.append({'type': 'Expr', 'value': e})
                    expr_instrs = []
                continue
            if instr.opname == 'POP_TOP' and expr_instrs:
                e = self.expr_reconstructor.reconstruct(expr_instrs)
                if e:
                    stmts.append({'type': 'Expr', 'value': e})
                expr_instrs = []
                continue
            if instr.opname == 'STORE_SUBSCR' and len(expr_instrs) >= MIN_INSTRS_FOR_SUBSCR_ASSIGN:
                v, c, idx = (self.expr_reconstructor.reconstruct(expr_instrs[:-2]),
                            self.expr_reconstructor.reconstruct([expr_instrs[-2]]),
                            self.expr_reconstructor.reconstruct([expr_instrs[-1]]))
                if v and c and idx:
                    stmts.append({'type': 'Assign', 'targets': [{'type': 'Subscript', 'value': c, 'slice': idx, 'ctx': 'Store'}], 'value': v})
                expr_instrs = []
                continue
            if instr.opname.startswith('STORE') and expr_instrs:
                s = self._build_statement(expr_instrs + [instr])
                if s:
                    stmts.append(s)
                expr_instrs = []
                continue
            expr_instrs.append(instr)
        if expr_instrs:
            last = block.get_last_instruction()
            is_recheck = (self._current_loop is not None and last is not None
                          and last.opname in CONDITIONAL_JUMP_OPS and last.argval is not None)
            if is_recheck:
                tgt = self.cfg.get_block_by_offset(last.argval)
                if tgt in (self._current_loop.header_block, self._current_loop.condition_block):
                    if not any(i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF') for i in expr_instrs) \
                       and not any(i.opname in ('CALL', 'CALL_FUNCTION', 'CALL_METHOD', 'CALL_FUNCTION_KW',
                                                  'CALL_FUNCTION_EX', 'DELETE_SUBSCR', 'DELETE_ATTR',
                                                  'RAISE_VARARGS', 'IMPORT_NAME') for i in expr_instrs):
                        return stmts
            e = self.expr_reconstructor.reconstruct(expr_instrs)
            if e:
                stmts.append({'type': 'Expr', 'value': e})
        return stmts

    def _build_class_def(self, class_name: str = None, body: List[Dict[str, Any]] = None,
                          call_expr: Dict[str, Any] = None, name: Optional[str] = None,
                          outer_call: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        bases = []
        decorator_list = []

        if call_expr is not None:
            func = call_expr.get('func', {})
            is_direct_build_class = (call_expr.get('is_class_def') or
                                      (func.get('type') == 'Name' and func.get('id') == '__build_class__'))
            if not is_direct_build_class and outer_call is None:
                _fbc_stack = [call_expr]
                while _fbc_stack:
                    _fbc_node = _fbc_stack.pop()
                    if not isinstance(_fbc_node, dict) or _fbc_node.get('type') != 'Call':
                        continue
                    _fbc_func = _fbc_node.get('func', {})
                    if _fbc_func.get('type') == 'Name' and _fbc_func.get('id') == '__build_class__':
                        return self._build_class_def(call_expr=_fbc_node, name=name, outer_call=call_expr)
                    if isinstance(_fbc_func, dict):
                        _fbc_stack.append(_fbc_func)
                    for _fbc_arg in _fbc_node.get('args', []):
                        if isinstance(_fbc_arg, dict):
                            _fbc_stack.append(_fbc_arg)
                return None

            args = call_expr.get('args', [])
            class_code_obj = None

            for arg in args:
                if isinstance(arg, dict):
                    if arg.get('type') == 'FunctionObject':
                        code = arg.get('code')
                        if isinstance(code, dict) and code.get('type') == 'Constant':
                            code = code.get('value')
                        if isinstance(code, dict) and code.get('type') == 'CodeObject':
                            code = code.get('code')
                        if isinstance(code, types.CodeType):
                            class_code_obj = code
                    elif arg.get('type') == 'Constant' and isinstance(arg.get('value'), str):
                        if name is None:
                            name = arg['value']
                    else:
                        bases.append(arg)

            decorator_list = self._extract_decorators(outer_call if outer_call else call_expr)

            if name is None:
                name = 'UnknownClass'

            body_stmts = [{'type': 'Pass'}]
            if class_code_obj and self.recursive:
                try:
                    from .cfg_builder import CFGBuilder
                    builder = CFGBuilder()
                    nested_cfg = builder.build(class_code_obj)
                    nested_gen = RegionASTGenerator(nested_cfg, recursive=True, parent_code=self.cfg.code, top_level_code=self._top_level_code)
                    nested_ast = nested_gen.generate()
                    if nested_ast and nested_ast.get('body'):
                        body_stmts = nested_ast['body']
                except Exception:
                    pass

            body = body_stmts
            class_name = name
        else:
            if class_name is None:
                class_name = 'UnknownClass'

        filtered_body = []
        for stmt in body:
            if isinstance(stmt, dict) and stmt.get('type') == 'Assign':
                targets = stmt.get('targets', [])
                if len(targets) == 1 and isinstance(targets[0], dict):
                    target_id = targets[0].get('id', '')
                    if target_id in ('__module__', '__qualname__'):
                        continue
            filtered_body.append(stmt)

        if not filtered_body:
            filtered_body = [{'type': 'Pass'}]

        if filtered_body:
            _trn_last = filtered_body[-1]
            if _trn_last.get('type') == 'Return':
                _trn_val = _trn_last.get('value')
                if _trn_val is None or (isinstance(_trn_val, dict) and _trn_val.get('type') == 'Constant' and _trn_val.get('value') is None):
                    filtered_body = filtered_body[:-1]
        if not filtered_body:
            filtered_body = [{'type': 'Pass'}]

        return {
            'type': 'ClassDef',
            'name': class_name,
            'bases': bases,
            'keywords': [],
            'body': filtered_body,
            'decorator_list': decorator_list,
        }

    def _extract_function_args(self, code_obj: Any = None) -> Dict[str, Any]:
        """从code object提取函数参数信息

        Args:
            code_obj: 可选的代码对象。如果为None，则使用self.cfg.code
        """
        if code_obj is None:
            code_obj = getattr(self.cfg, 'code', None)

        if not code_obj:
            return {
                'type': 'arguments',
                'posonlyargs': [],
                'args': [],
                'vararg': None,
                'kwonlyargs': [],
                'kw_defaults': [],
                'kwarg': None,
                'defaults': [],
            }

        # 提取位置参数
        arg_count = getattr(code_obj, 'co_argcount', 0)
        varnames = list(getattr(code_obj, 'co_varnames', ()))

        # 位置参数（前arg_count个）
        pos_args = [{'type': 'arg', 'arg': name} for name in varnames[:arg_count]]

        # 检查是否有*args（vararg）
        has_vararg = False
        vararg_name = None
        posonly_count = getattr(code_obj, 'co_posonlyargcount', 0)

        # kwonly参数
        kwonly_count = getattr(code_obj, 'co_kwonlyargcount', 0)
        kwonly_start = arg_count
        if hasattr(code_obj, 'co_flags'):
            flags = code_obj.co_flags
            # CO_VARARGS = 0x04
            if flags & 0x04:
                vararg_name = varnames[arg_count] if arg_count < len(varnames) else None
                kwonly_start = arg_count + 1
                has_vararg = True

        kwonly_args = []
        for i in range(kwonly_start, kwonly_start + kwonly_count):
            if i < len(varnames):
                kwonly_args.append({'type': 'arg', 'arg': varnames[i]})

        # 检查是否有**kwargs（kwarg）
        has_kwarg = False
        kwarg_name = None
        if hasattr(code_obj, 'co_flags'):
            flags = code_obj.co_flags
            # CO_VARKEYWORDS = 0x08
            if flags & 0x08:
                kwargs_idx = kwonly_start + kwonly_count
                if has_vararg:
                    kwargs_idx = kwonly_start + kwonly_count
                else:
                    kwargs_idx = arg_count + kwonly_count
                if kwargs_idx < len(varnames):
                    kwarg_name = varnames[kwargs_idx]
                    has_kwarg = True

        return {
            'type': 'arguments',
            'posonlyargs': [],
            'args': pos_args,
            'vararg': vararg_name,
            'kwonlyargs': kwonly_args,
            'kw_defaults': [],
            'kwarg': kwarg_name,
            'defaults': [],
        }

    def _generate_region(self, region: Region, skip_store_targets: Set[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        if isinstance(region, (IfRegion, LoopRegion, TryExceptRegion, WithRegion, MatchRegion, AssertRegion, BoolOpRegion, TernaryRegion)):
            with_cleanup_roles = (BlockRole.WITH_EXIT_CLEANUP, BlockRole.WITH_STACK_CLEANUP, BlockRole.WITH_HANDLER)
            if all(self.region_analyzer.get_block_role(b) in with_cleanup_roles for b in region.blocks):
                for block in region.blocks:
                    self.generated_blocks.add(block)
                return None

        if isinstance(region, TryExceptRegion):
            all_generated = all(b in self.generated_blocks for b in region.try_blocks)
            if all_generated:
                for block in region.blocks:
                    self.generated_blocks.add(block)
                return None

        if isinstance(region, LoopRegion):
            return self._generate_loop(region, skip_store_targets=skip_store_targets)
        elif isinstance(region, IfRegion):
            return self._generate_if(region)
        elif isinstance(region, TryExceptRegion):
            return self._generate_try(region)
        elif isinstance(region, WithRegion):
            return self._generate_with(region)
        elif isinstance(region, MatchRegion):
            return self._generate_match(region)
        elif isinstance(region, AssertRegion):
            return self._generate_assert(region, skip_store_targets)
        elif isinstance(region, BoolOpRegion):
            return self._generate_boolop(region)
        elif isinstance(region, TernaryRegion):
            should_skip = False
            for r in self.regions:
                if r is not region and isinstance(r, IfRegion) and r.region_type.name == 'IF_ELIF_CHAIN':
                    if r.entry == region.entry or (region.entry and region.entry in r.blocks):
                        should_skip = True
                        break
            if should_skip:
                return None
            return self._generate_ternary(region)
        elif region.region_type == RegionType.PASS:
            return {'type': 'Pass'}
        elif region.region_type == RegionType.BASIC:
            return self._generate_basic_region(region)
        return None

    def _generate_assert(self, region: AssertRegion,
                         skip_store_targets: Set[str] = None) -> Dict[str, Any]:
        """生成AssertRegion的AST节点

        算法角色：区域AST生成器（Region AST Generator）
        输入：AssertRegion（条件块+可选消息块）
        输出：Dict - Assert AST节点

        【条件表达式重建】

        指令过滤规则（按顺序）：
        1. 噪声指令：RESUME/NOP/CACHE/POP_TOP/PUSH_NULL → 跳过
        2. 非None检查的前向/后向跳转 → 跳过（保留NONE_CHECK_OPS用于is None检测）
        3. JUMP_FORWARD/JUMP_BACKWARD → 跳过
        4. COPY(栈顶)：标记prev_was_copy，允许后续STORE跟随
        5. STORE指令：
           - 如果在skip_store_targets中 → 跳过（属于外层赋值）
           - 如果前一个指令是COPY → 保留（链式比较中的SWAP/COPY模式）
           - 否则 → 清空cond_instrs重新开始（防止吸收前缀赋值）
        6. 其他指令 → 追加到cond_instrs

        最终通过 expr_reconstructor.reconstruct(cond_instrs) 构建AST。

        【消息表达式重建】
        从message_block中提取非噪声指令，排除：
        RAISE_VARARGS, POP_EXCEPT, RERAISE,
        LOAD_ASSERTION_ERROR, PRECALL, CALL,
        RESUME, NOP, CACHE, PUSH_NULL, COPY, SWAP

        【输出格式】
        ```python
        {'type': 'Assert', 'test': condition_ast}  # 无消息
        {'type': 'Assert', 'test': condition_ast, 'msg': message_ast}  # 有消息
        ```

        如果condition为空，使用 Constant(True) 作为默认值。

        【已知问题与test失败对应关系】

        | 失败测试 | 根因 |
        |---------|------|
        | test_as01assertbasic_x | POP_JUMP_IF_NOT_NONE vs NONE 检查方向错误 |
        | test_as02assertmsg_n | f-string格式化指令数差异(20 vs 17) |
        | test_as03assertinif_* | if体中的assert被IfRegion"吞掉"，LOAD_ASSERTION_ERROR丢失 |
        | test_as04assertinloop_* | 循环体中的assert被LoopRegion"吞掉" |

        【修复方向建议】
        问题1的方向性bug可能是一个简单的操作码判断反转，
        类似Phase 2中发现的那种类型的高价值修复。
        """
        cond_block = region.condition_block
        if cond_block is None:
            return {'type': 'Pass'}
        cond_instrs = []
        prev_was_copy = False
        for instr in cond_block.instructions:
            if instr.opname in ('RESUME', 'NOP', 'CACHE', 'POP_TOP', 'PUSH_NULL'):
                continue
            if (instr.opname in FORWARD_JUMP_OPS or instr.opname in BACKWARD_JUMP_OPS) and instr.opname not in NONE_CHECK_OPS:
                continue
            if instr.opname == 'JUMP_FORWARD' or instr.opname == 'JUMP_BACKWARD':
                continue
            if instr.opname == 'COPY' and instr.arg == COPY_STACK_TOP:
                prev_was_copy = True
                cond_instrs.append(instr)
                continue
            if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                if skip_store_targets and instr.argval in skip_store_targets:
                    prev_was_copy = False
                    continue
                if prev_was_copy:
                    cond_instrs.append(instr)
                    prev_was_copy = False
                    continue
                cond_instrs = []
                continue
            prev_was_copy = False
            cond_instrs.append(instr)
        condition = None
        if cond_instrs:
            expr = self.expr_reconstructor.reconstruct(cond_instrs)
            if expr:
                condition = self._fix_assert_none_check_direction(expr)
        message = None
        if region.message_block:
            msg_instrs = []
            instrs = region.message_block.instructions
            has_build_string = any(i.opname == 'BUILD_STRING' for i in instrs)
            base_skip = {'RAISE_VARARGS', 'POP_EXCEPT', 'RERAISE',
                        'LOAD_ASSERTION_ERROR', 'RESUME', 'NOP', 'CACHE',
                        'PUSH_NULL', 'COPY', 'SWAP'}
            if has_build_string:
                raise_call_start = len(instrs)
                found_raise = False
                for idx in range(len(instrs) - 1, -1, -1):
                    op = instrs[idx].opname
                    if op == 'RAISE_VARARGS':
                        raise_call_start = idx
                        found_raise = True
                    elif found_raise and op in ('CALL', 'PRECALL', 'PUSH_NULL',
                                                'COPY', 'SWAP', 'NOP', 'CACHE',
                                                'RESUME'):
                        raise_call_start = idx
                    elif found_raise:
                        break
                for i, instr in enumerate(instrs):
                    if instr.opname in base_skip:
                        continue
                    if i >= raise_call_start and instr.opname in ('PRECALL', 'CALL'):
                        continue
                    msg_instrs.append(instr)
            else:
                for instr in instrs:
                    if instr.opname in base_skip or instr.opname in ('PRECALL', 'CALL'):
                        continue
                    msg_instrs.append(instr)
            if msg_instrs:
                message = self.expr_reconstructor.reconstruct(msg_instrs)
        for block in region.blocks:
            self.generated_blocks.add(block)
        result = {
            'type': 'Assert',
            'test': condition if condition else {'type': 'Constant', 'value': True},
        }
        if message:
            result['msg'] = message
        return result

    def _fix_assert_none_check_direction(self, expr: Dict[str, Any]) -> Dict[str, Any]:
        """修复assert上下文中None检查操作码的方向性问题

        【问题根因】
        expr_reconstructor 对 NONE_CHECK_OPS 的转换是基于if语句语义的：
        - POP_JUMP_IF_NOT_NONE → Compare(op='is', None)  [如果不是None就跳转→then体]
        - POP_JUMP_IF_NONE → Compare(op='is not', None)  [如果是None就跳转→then体]

        但在assert语句中，跳转语义相反：
        - POP_JUMP_IF_NOT_NONE → 如果不是None就跳转(跳过错误) → 条件是 is not None
        - POP_JUMP_IF_NONE → 如果是None就跳转(跳过错误) → 条件是 is None

        因此需要将 is/is not 互换。

        【示例】
        源码: assert x is not None
        字节码: LOAD x; POP_JUMP_IF_NOT_NONE → end; LOAD_ASSERTION_ERROR; RAISE
        expr_reconstructor输出: Compare(op='is', x, None)
        修复后: Compare(op='is not', x, None) ✅

        源码: assert x is None
        字节码: LOAD x; POP_JUMP_IF_NONE → end; LOAD_ASSERTION_ERROR; RAISE
        expr_reconstructor输出: Compare(op='is not', x, None)
        修复后: Compare(op='is', x, None) ✅

        【递归处理】
        对于 BoolOp 包装的 None 检查（如 `assert a and x is not None`），
        递归进入 values 列表查找并修复。
        """
        if not isinstance(expr, dict):
            return expr
        if expr.get('type') == 'Compare':
            ops = expr.get('ops', [])
            comparators = expr.get('comparators', [])
            if (len(ops) == 1 and len(comparators) >= 1 and
                    ops[0] in ('is', 'is not') and
                    isinstance(comparators[0], dict) and
                    comparators[0].get('type') == 'Constant' and
                    comparators[0].get('value') is None):
                fixed = dict(expr)
                fixed['ops'] = ['is not' if ops[0] == 'is' else 'is']
                return fixed
        if expr.get('type') == 'BoolOp':
            values = expr.get('values', [])
            if values:
                fixed_values = [self._fix_assert_none_check_direction(v) for v in values]
                if any(fv is not v for fv, v in zip(fixed_values, values)):
                    fixed = dict(expr)
                    fixed['values'] = fixed_values
                    return fixed
        return expr

    def _generate_loop(self, region: LoopRegion,
                        exclude_blocks: Set[BasicBlock] = None,
                        skip_store_targets: Set[str] = None) -> Dict[str, Any]:
        """
        统一的loop结构生成入口

        区域到AST映射：
        - LoopRegion(FOR_LOOP) → ast.For
        - LoopRegion(WHILE_LOOP) → ast.While
        - condition_block → while的条件表达式
        - body_blocks → 循环体语句列表
        - else_blocks → else子句语句列表（作为orelse字段，非独立语句）

        表达式重建：
        - for循环：从FOR_ITER前驱块提取迭代变量和可迭代对象
        - while循环：从condition_block提取条件表达式
        - while True：条件为True常量
        - 复合条件(and/or)：从BoolOpRegion构建BoolOp表达式
        - not条件：条件跳转为IF_TRUE时取反表达式

        嵌套处理：
        - 循环体内的区域递归生成
        - break/continue映射到ast.Break/ast.Continue
        - 内层循环的break/continue不泄漏到外层

        字节码等价保证：
        - 条件表达式必须与原始字节码语义一致
        - else子句仅在循环正常退出时执行
        - break跳过else子句
        - for循环else块必须作为For节点的orelse字段
        - while循环else块必须作为While节点的orelse字段
        - header含body+条件重检时，需分离body语句和条件重检指令
        - break_blocks中的块需正确生成break语句而非被忽略
        """
        header = region.header_block
        if header is None:
            return {'type': 'Pass'}

        # [yield from 修复] 检查是否是 yield from 实现循环
        # 如果是，提取yield-from表达式而非生成while循环
        if region.metadata.get('is_yield_from_loop'):
            _yf_expr = None
            _all_blocks = list(region.blocks)
            _pre_blocks = []
            for b in self.cfg.blocks.values():
                if b not in region.blocks and b.start_offset < (region.header_block.start_offset if region.header_block else 9999):
                    _pre_blocks.append(b)
            for block in _pre_blocks + _all_blocks:
                _yf_instrs = [i for i in block.instructions
                             if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL',
                                                 'YIELD_VALUE', 'RETURN_VALUE', 'RETURN_CONST',
                                                 'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT',
                                                 'POP_TOP', 'SEND', 'RETURN_GENERATOR')]
                if _yf_instrs:
                    _load_instrs = [i for i in _yf_instrs
                                    if i.opname in ('LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF')
                                    and i.argval]
                    if _load_instrs:
                        _yf_expr = self.expr_reconstructor.reconstruct(_load_instrs[:1])
                        if _yf_expr and _yf_expr.get('type') != 'Constant':
                            break
                    elif not _yf_expr:
                        _yf_exprs_clean = [i for i in _yf_instrs if i.opname != 'GET_YIELD_FROM_ITER']
                        if _yf_exprs_clean:
                            _yf_expr = self.expr_reconstructor.reconstruct(_yf_exprs_clean)
                            if _yf_expr and _yf_expr.get('type') != 'Constant':
                                break
            for block in region.blocks:
                self.generated_blocks.add(block)
            if _yf_expr:
                return {'type': 'Expr', 'value': {'type': 'YieldFrom', 'value': _yf_expr}}
            return {'type': 'Pass'}

        self._loop_depth += 1
        region_id = id(region)
        self._generating_regions.add(region_id)
        
        saved_loop = self._current_loop
        self._current_loop = region
        
        try:
            is_for = region.region_type == RegionType.FOR_LOOP

            if is_for:
                result = self._loop_generate_for(region)
            else:
                result = self._loop_generate_while(region, skip_store_targets=skip_store_targets)

            for block in region.blocks:
                if block not in region.else_blocks:
                    if exclude_blocks is None or block not in exclude_blocks:
                        block_region = self.region_analyzer.get_region_for_block(block)
                        if (block_region and 
                            block_region != region and 
                            not isinstance(block_region, LoopRegion) and
                            (block_region.parent == region or 
                             (block_region.parent is not None and isinstance(block_region, (WithRegion, TryExceptRegion))))):
                            continue
                        self.generated_blocks.add(block)

            return result
        finally:
            self._generating_regions.discard(region_id)
            self._generated_regions.add(region_id)
            self._loop_depth -= 1
            self._current_loop = saved_loop


    def _loop_generate_for(self, region: LoopRegion) -> Dict[str, Any]:
        pre_stmts = []

        for_iter_setup = region.metadata.get('for_iter_setup')

        if region.init_blocks:
            for ib in region.init_blocks:
                if ib == for_iter_setup:
                    continue
                if ib not in self.generated_blocks:
                    ib_stmts = self._generate_block_statements(ib)
                    pre_stmts.extend(ib_stmts)
                    self.generated_blocks.add(ib)
                    self.generated_offsets.add(ib.start_offset)

        # Build iterator expression
        for_iter_setup = region.metadata.get('for_iter_setup')
        if for_iter_setup and for_iter_setup in self.cfg.blocks.values():
            instrs = [i for i in for_iter_setup.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
            _fis_pre_stmts, _fis_iter_instrs = self._loop_extract_for_iter_pre_stmts(instrs, for_iter_setup)
            if _fis_pre_stmts:
                pre_stmts.extend(_fis_pre_stmts)
            iter_expr = self.expr_reconstructor.reconstruct(_fis_iter_instrs) if _fis_iter_instrs else None
            if iter_expr is None and instrs:
                stmt = self._build_statement(instrs)
                iter_expr = stmt.get('value') if stmt and isinstance(stmt, dict) else None
            # Unwrap Iter wrapper (GET_ITER) - for-loop iter field uses inner expression directly
            if isinstance(iter_expr, dict) and iter_expr.get('type') == 'Iter' and isinstance(iter_expr.get('value'), dict):
                iter_expr = iter_expr['value']
        else:
            # Phase 12修复: 当for_iter_setup块被TernaryRegion"借用"时（merge_context=='iter'），
            # 从TernaryRegion获取迭代器表达式
            iter_expr = None
            for r in self.region_analyzer.regions:
                if (isinstance(r, TernaryRegion) and
                    getattr(r, 'merge_context', None) == 'iter' and
                    r.merge_block and
                    r.merge_block.start_offset in [b.start_offset for b in region.blocks]):
                    
                    # 检查TernaryRegion是否已经被生成（在ast_nodes中）
                    # 如果已生成，从现有结果中提取IfExp
                    found_in_existing = False
                    for node in ast_nodes:
                        if (isinstance(node, dict) and node.get('type') == 'Expr' and
                            isinstance(node.get('value'), dict) and
                            node['value'].get('type') == 'IfExp'):
                            iter_expr = node['value']
                            found_in_existing = True
                            # 从ast_nodes中移除，避免重复输出
                            ast_nodes.remove(node)
                            break
                    
                    if not found_in_existing:
                        # TernaryRegion尚未生成，现在生成它
                        ternary_stmts = self._generate_ternary(r)
                        if ternary_stmts and len(ternary_stmts) > 0:
                            stmt = ternary_stmts[0]
                            if stmt.get('type') == 'Expr' and 'value' in stmt:
                                iter_expr = stmt['value']
                    break
            
            if iter_expr is None:
                iter_val = region.metadata.get('for_iter_value')
                iter_expr = {'type': 'Name', 'id': iter_val} if isinstance(iter_val, str) else (iter_val or {'type': 'Constant', 'value': None})

        # Resolve target variable
        target_name = region.metadata.get('for_target', '_')
        target = {'type': 'Name', 'id': target_name, 'ctx': 'Store'} if target_name else None
        if not target_name or target_name == '_':
            for search_block in [region.header_block] + (list(region.body_blocks) if hasattr(region,'body_blocks') else []):
                if not search_block:
                    continue
                found_unpack = False
                unpack_count = 0
                unpack_targets = []
                for i in search_block.instructions:
                    if i.opname in ('FOR_ITER', 'GET_ANEXT'):
                        continue
                    if i.opname == 'UNPACK_SEQUENCE' and hasattr(i, 'arg'):
                        found_unpack = True
                        unpack_count = i.arg
                        continue
                    if found_unpack and i.opname.startswith('STORE_') and hasattr(i, 'argval'):
                        unpack_targets.append({'type': 'Name', 'id': str(i.argval), 'ctx': 'Store'})
                        if len(unpack_targets) == unpack_count:
                            break
                    elif not found_unpack and i.opname.startswith('STORE_') and hasattr(i, 'argval'):
                        target_name = str(i.argval)
                        target = {'type': 'Name', 'id': target_name, 'ctx': 'Store'}
                        break
                if found_unpack and unpack_targets:
                    target = {'type': 'Tuple', 'elts': unpack_targets, 'ctx': 'Store'}
                    target_name = ','.join(t.get('id', '') for t in unpack_targets)
                    break
                if target_name != '_':
                    break

        for_target_name = target.get('id') if target else None
        if for_target_name and for_target_name != '_':
            if 'for_target_names' not in region.metadata:
                region.metadata['for_target_names'] = set()
            region.metadata['for_target_names'].add(for_target_name)

        body_stmts = self._loop_generate_body(region)

        if not region.else_blocks:
            else_stmts = []
        else:
            else_stmts = self._if_generate_branch_stmts(region.else_blocks)

        result = {
            'type': 'AsyncFor' if region.is_async else 'For',
            'target': target,
            'iter': iter_expr,
            'body': body_stmts if body_stmts else [{'type': 'Pass'}],
        }

        if else_stmts:
            result['orelse'] = else_stmts

        if pre_stmts:
            output = list(pre_stmts)
            output.append(result)
            return output
        return result

    def _loop_generate_while(self, region: LoopRegion, skip_store_targets: Set[str] = None) -> Dict[str, Any]:
        pre_stmts = []

        if region.init_blocks:
            for ib in region.init_blocks:
                if ib not in self.generated_blocks:
                    ib_stmts = self._generate_block_statements(ib)
                    pre_stmts.extend(ib_stmts)
                    self.generated_blocks.add(ib)
                    self.generated_offsets.add(ib.start_offset)

        cond_block = region.condition_block
        if cond_block is None and region.header_block:
            for pred in region.header_block.predecessors:
                if pred != region.header_block and any(i.opname.startswith('POP_JUMP') or i.opname.startswith('JUMP_IF') for i in pred.instructions):
                    cond_block = pred
                    break

        if region.is_while_true and cond_block is None:
            body_stmts = self._loop_generate_body(region)
            result = {'type': 'While', 'test': {'type': 'Constant', 'value': True}, 'body': body_stmts if body_stmts else [{'type': 'Pass'}]}
            output = list(pre_stmts)
            output.append(result)
            return output

        if region.is_while_true and cond_block == region.header_block:
            body_stmts = self._loop_generate_body(region)
            result = {'type': 'While', 'test': {'type': 'Constant', 'value': True}, 'body': body_stmts if body_stmts else [{'type': 'Pass'}]}
            output = list(pre_stmts)
            output.append(result)
            return output

        if region.is_while_true and cond_block == region.header_block:
            body_stmts = self._loop_generate_body(region)
            result = {'type': 'While', 'test': {'type': 'Constant', 'value': True}, 'body': body_stmts if body_stmts else [{'type': 'Pass'}]}
            output = list(pre_stmts)
            output.append(result)
            return output

        is_degenerate_while = region.metadata.get('is_degenerate_while', False)
        if not is_degenerate_while:
            is_degenerate_while = (cond_block == region.header_block and 
                                   cond_block is not None and
                                   any(i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_DEREF') 
                                       for i in cond_block.instructions))
        
        if cond_block and cond_block != region.header_block:
            pre_stmts: List[Dict[str, Any]] = []
            _eps_instrs: List[Instruction] = []
            _eps_unpack_info = None
            _cond_was_generated = cond_block in self.generated_blocks

            for _instr in cond_block.instructions:
                if _instr.opname in ('RESUME', 'NOP', 'CACHE'):
                    continue

                if _instr.opname == 'PUSH_NULL':
                    _eps_instrs.append(_instr)
                    continue

                if _instr.opname == 'POP_TOP':
                    if _eps_instrs:
                        _call_instrs = [i for i in _eps_instrs
                                       if i.opname not in ('POP_TOP', 'LOAD_CONST')
                                       or (i.opname == 'LOAD_CONST' and i.argval is not None)]
                        _has_call = any(i.opname in ('CALL', 'CALL_FUNCTION', 'CALL_METHOD',
                                                    'CALL_FUNCTION_KW', 'CALL_FUNCTION_EX')
                                       for i in _call_instrs)
                        if _has_call:
                            _stmt = self._build_statement(_call_instrs)
                            if _stmt:
                                pre_stmts.append(_stmt)
                            _eps_instrs = []
                            continue
                        _eps_instrs.append(_instr)
                        _stmt = self._build_statement(_eps_instrs)
                        if _stmt:
                            pre_stmts.append(_stmt)
                        _eps_instrs = []
                    continue
                if _instr.opname in FORWARD_JUMP_OPS or _instr.opname in BACKWARD_JUMP_OPS:
                    break
                if _instr.opname in ('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE'):
                    break
                if _instr.opname in ('POP_EXCEPT', 'PUSH_EXC_INFO', 'RERAISE',
                                    'WITH_EXCEPT_START', 'CHECK_EXC_MATCH', 'CHECK_EG_MATCH'):
                    continue
                if _instr.opname == 'RAISE_VARARGS':
                    if _instr.arg == 0:
                        _pre_stmts.append({'type': 'Raise', 'exc': None})
                    else:
                        _exc_instrs = [i for i in _stmt_instrs if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                        _exc_expr = self.expr_reconstructor.reconstruct(_exc_instrs) if _exc_instrs else None
                        if _exc_expr is None and _exc_instrs:
                            _exc_expr = self._build_statement(_exc_instrs)
                            if _exc_expr and _exc_expr.get('type') == 'Expr':
                                _exc_expr = _exc_expr.get('value')
                        _pre_stmts.append({'type': 'Raise', 'exc': _exc_expr})
                    _stmt_instrs = []
                    break
                if _instr.opname == 'RETURN_CONST':
                    _pre_stmts.append({'type': 'Return', 'value': {'type': 'Constant', 'value': _instr.argval}})
                    _stmt_instrs = []
                    break
                if _instr.opname == 'RETURN_VALUE':
                    _value_instrs = [i for i in _stmt_instrs if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                    _value = self.expr_reconstructor.reconstruct(_value_instrs) if _value_instrs else None
                    _pre_stmts.append({'type': 'Return', 'value': _value if _value else {'type': 'Constant', 'value': None}})
                    _stmt_instrs = []
                    break
                if _instr.opname == 'UNPACK_SEQUENCE':
                    _val_instrs = [i for i in _eps_instrs if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                    _val = self.expr_reconstructor.reconstruct(_val_instrs) if _val_instrs else None
                    _eps_unpack_info = {'value': _val, 'targets': [], 'count': _instr.arg}
                    _eps_instrs = []
                    continue
                if _instr.opname == 'UNPACK_EX':
                    _val_instrs = [i for i in _eps_instrs if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                    _val = self.expr_reconstructor.reconstruct(_val_instrs) if _val_instrs else None
                    _arg = _instr.argval
                    _before = _arg & 0xFF
                    _after = (_arg >> 8) & 0xFF
                    _eps_unpack_info = {'value': _val, 'targets': [], 'count': _before + 1 + _after, 'is_starred': True, 'starred_idx': _before}
                    _eps_instrs = []
                    continue
                if _instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                    if skip_store_targets and _instr.argval in skip_store_targets:
                        _eps_instrs = []
                        continue
                    _has_prev_copy = len(_eps_instrs) >= 1 and _eps_instrs[-1].opname == 'COPY' and _eps_instrs[-1].arg == 1
                    if _has_prev_copy:
                        _eps_instrs.append(_instr)
                        prev_was_copy = True
                        continue
                    if _eps_unpack_info is not None:
                        _is_starred = _eps_unpack_info.get('is_starred', False)
                        _starred_idx = _eps_unpack_info.get('starred_idx', -1)
                        _current_target_idx = len(_eps_unpack_info['targets'])
                        if _is_starred and _current_target_idx == _starred_idx:
                            _eps_unpack_info['targets'].append({
                                'type': 'Starred',
                                'value': {'type': 'Name', 'id': _instr.argval if _instr.argval else f'var_{_instr.arg}', 'ctx': 'Store'},
                            })
                        else:
                            _eps_unpack_info['targets'].append({
                                'type': 'Name',
                                'id': _instr.argval if _instr.argval else f'var_{_instr.arg}',
                                'ctx': 'Store',
                            })
                        if len(_eps_unpack_info['targets']) == _eps_unpack_info['count']:
                            _target = {
                                'type': 'Tuple',
                                'elts': _eps_unpack_info['targets'],
                                'ctx': 'Store',
                            }
                            if _eps_unpack_info['value']:
                                pre_stmts.append({'type': 'Assign', 'targets': [_target], 'value': _eps_unpack_info['value']})
                            _eps_unpack_info = None
                        _eps_instrs = []
                        continue
                    _eps_instrs.append(_instr)
                    _stmt = self._build_store_statement(_eps_instrs, block=cond_block)
                    if _stmt:
                        _dec_block = _stmt.pop('_decorator_block', None)
                        if _dec_block is not None:
                            _dec_name = None
                            _dec_list = _stmt.get('decorator_list', [])
                            for _d in _dec_list:
                                if isinstance(_d, dict):
                                    _f = _d.get('func', _d) if _d.get('type') == 'Call' else _d
                                    if isinstance(_f, dict) and _f.get('type') == 'Name':
                                        _dec_name = _f.get('id')
                                        break
                            if _dec_name:
                                for _i in range(len(pre_stmts) - 1, -1, -1):
                                    _s = pre_stmts[_i]
                                    if (isinstance(_s, dict) and _s.get('type') == 'Expr' and
                                        isinstance(_s.get('value'), dict) and
                                        _s.get('value', {}).get('type') == 'Name' and
                                        _s.get('value', {}).get('id') == _dec_name):
                                        pre_stmts.pop(_i)
                                        break
                        pre_stmts.append(_stmt)
                    _eps_instrs = []
                    continue

                if _instr.opname in ('DELETE_SUBSCR', 'DELETE_ATTR'):
                    _eps_instrs.append(_instr)

                    _stmt_nodes = self._process_instruction(_instr, cond_block, _eps_instrs)
                    if _stmt_nodes:
                        pre_stmts.extend(_stmt_nodes)

                    _eps_instrs = []
                    continue

                _eps_instrs.append(_instr)

            if _cond_was_generated and not pre_stmts:
                pre_stmts = []

            self.generated_blocks.add(cond_block)
            self.generated_offsets.add(cond_block.start_offset)
        elif is_degenerate_while:
            init_stmts: List[Dict[str, Any]] = []
            cond_instr_idx = None
            for i, instr in enumerate(cond_block.instructions):
                if instr.opname in CONDITIONAL_JUMP_OPS or instr.opname == 'COMPARE_OP':
                    cond_instr_idx = i
                    break
            if cond_instr_idx is not None:
                _init_instrs: List[Instruction] = []
                for instr in cond_block.instructions[:cond_instr_idx]:
                    if instr.opname in ('RESUME', 'NOP', 'CACHE'):
                        continue
                    _init_instrs.append(instr)
                    if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_DEREF'):
                        if skip_store_targets and instr.argval in skip_store_targets:
                            _init_instrs = []
                            continue
                        if len(_init_instrs) >= 2:
                            stmt = self._build_statement(_init_instrs)
                            if stmt:
                                init_stmts.append(stmt)
                        _init_instrs = []
            pre_stmts = init_stmts
            self.generated_blocks.add(cond_block)
            self.generated_offsets.add(cond_block.start_offset)
            for b in cond_block.predecessors:
                if b != region.header_block and b not in self.generated_blocks:
                    if b == region.back_edge_block:
                        continue
                    b_role = self.region_analyzer.get_block_role(b)
                    if b_role in (BlockRole.CONTINUE, BlockRole.PURE_CONTINUE):
                        continue
                    
                    b_region = self.region_analyzer.get_region_for_block(b)
                    if b_region and b_region != region:
                        continue
                    
                    b_stmts = self._generate_block_statements(b)
                    pre_stmts.extend(b_stmts)
                    self.generated_blocks.add(b)
                    self.generated_offsets.add(b.start_offset)

        seen = set()
        unique_pre = []
        for s in pre_stmts:
            key = (s.get('type'), tuple(sorted((k, str(v)[:80]) for k, v in s.items() if k != 'lineno')))
            if key not in seen:
                seen.add(key)
                unique_pre.append(s)
        pre_stmts = unique_pre

        condition = None
        if cond_block is None:
            cond_block = region.condition_block

        boolop_for_while = None
        for r in region.iter_descendants((BoolOpRegion,)):
            if r.prefix_block == cond_block:
                boolop_for_while = r
                break
            for chain_block, _ in r.op_chain:
                if chain_block == cond_block:
                    boolop_for_while = r
                    break
            if boolop_for_while:
                break

        if boolop_for_while is None:
            loop_blocks = set(region.blocks)
            if region.header_block:
                loop_blocks.add(region.header_block)
            for r in region.iter_descendants((BoolOpRegion,)):
                for chain_block, _ in r.op_chain:
                    if chain_block in loop_blocks:
                        boolop_for_while = r
                        break
                if boolop_for_while is None and r.merge_block and r.merge_block in loop_blocks:
                    boolop_for_while = r
                    if boolop_for_while:
                        break

        if boolop_for_while:
            boolop_expr = self._build_boolop_expression(boolop_for_while)
            if boolop_expr:
                condition = boolop_expr
                pre_stmts = []
                loop_blocks = set(region.blocks)
                for b in boolop_for_while.blocks:
                    if b not in loop_blocks:
                        self.generated_blocks.add(b)
                        self.generated_offsets.add(b.start_offset)
                if boolop_for_while.merge_block and boolop_for_while.merge_block not in loop_blocks:
                    self.generated_blocks.add(boolop_for_while.merge_block)
                for chain_block, _ in boolop_for_while.op_chain:
                    if chain_block != cond_block and chain_block not in loop_blocks:
                        chain_instrs = [i for i in chain_block.instructions
                                       if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                        last_i = chain_block.get_last_instruction()
                        pre_instrs = []
                        for i in chain_instrs:
                            if i == last_i:
                                break
                            if i.opname not in ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE',
                                                'POP_JUMP_BACKWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_TRUE',
                                                'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP',
                                                'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_FORWARD_IF_NOT_NONE',
                                                'POP_JUMP_BACKWARD_IF_NONE', 'POP_JUMP_BACKWARD_IF_NOT_NONE'):
                                pre_instrs.append(i)
                        if pre_instrs:
                            pre_expr = self.expr_reconstructor.reconstruct(pre_instrs)
                            if pre_expr and isinstance(pre_expr, dict) and pre_expr.get('type') == 'Assign':
                                pre_stmts.append(pre_expr)
                boolop_cond_var_names = set()
                for chain_block, _ in boolop_for_while.op_chain:
                    for i in chain_block.instructions:
                        if i.opname in ('LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF'):
                            boolop_cond_var_names.add(i.argval)
                boolop_recheck_blocks = set()
                for b in region.body_blocks:
                    if b == region.header_block:
                        continue
                    b_instrs = [i for i in b.instructions
                               if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                    if not b_instrs:
                        continue
                    last_i = b.get_last_instruction()
                    if not last_i or last_i.opname not in CONDITIONAL_JUMP_OPS:
                        continue
                    non_jmp_instrs = [i for i in b_instrs if i != last_i]
                    has_store = any(i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
                                   for i in non_jmp_instrs)
                    if has_store:
                        continue
                    load_names = set()
                    for i in non_jmp_instrs:
                        if i.opname in ('LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF'):
                            load_names.add(i.argval)
                    if load_names and load_names.issubset(boolop_cond_var_names):
                        boolop_recheck_blocks.add(b)
                for b in boolop_recheck_blocks:
                    self.generated_blocks.add(b)
                    self.generated_offsets.add(b.start_offset)
                    for s in b.successors:
                        if s not in region.else_blocks:
                            s_role = self.region_analyzer.get_block_role(s)
                            if s_role in (BlockRole.PURE_BREAK, BlockRole.BREAK,
                                         BlockRole.RETURN_NONE, BlockRole.PURE_JUMP):
                                if s not in self.generated_blocks:
                                    self.generated_blocks.add(s)
                                    self.generated_offsets.add(s.start_offset)

        if condition is None and cond_block:
            _cond_chain_expr = region.condition_chain_expr
            if _cond_chain_expr is not None:
                condition = _cond_chain_expr
                for cb in region.condition_chain_blocks:
                    if cb != cond_block:
                        self.generated_blocks.add(cb)
                        self.generated_offsets.add(cb.start_offset)
        if condition is None and cond_block:
            cond_instrs = []
            prev_was_copy = False
            for instr in cond_block.instructions:
                if instr.opname in ('RESUME', 'NOP', 'CACHE', 'POP_TOP', 'PUSH_NULL'):
                    continue
                if (instr.opname in FORWARD_JUMP_OPS or instr.opname in BACKWARD_JUMP_OPS) and instr.opname not in NONE_CHECK_OPS:
                    continue
                if instr.opname == 'JUMP_FORWARD' or instr.opname == 'JUMP_BACKWARD':
                    continue
                if instr.opname == 'COPY' and instr.arg == COPY_STACK_TOP:
                    prev_was_copy = True
                    cond_instrs.append(instr)
                    continue
                if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                    if skip_store_targets and instr.argval in skip_store_targets:
                        cond_instrs = []
                        prev_was_copy = False
                        continue
                    if prev_was_copy:
                        cond_instrs.append(instr)
                        prev_was_copy = False
                        continue
                    if not cond_instrs:
                        continue
                    prev_was_copy = False
                    continue
                prev_was_copy = False
                cond_instrs.append(instr)
            if cond_instrs:
                expr = self.expr_reconstructor.reconstruct(cond_instrs)
                if expr:
                    last = cond_block.get_last_instruction()
                    if last and last.argval is not None and last.opname in CONDITIONAL_JUMP_OPS:
                        body_start_offsets = {b.start_offset for b in region.body_blocks}
                        jumps_to_body = last.argval in body_start_offsets
                        # 对于NONE_CHECK_OPS，if_true=False（跳转发生在fall-through条件为False时）
                        if last.opname in NONE_CHECK_OPS:
                            if_true = False
                        else:
                            if_true = 'IF_TRUE' in last.opname
                        negate = jumps_to_body != if_true
                        condition = _negate_expr(expr) if negate else expr
                    else:
                        condition = expr

        body_stmts = self._loop_generate_body(region, boolop_for_while)

        if boolop_for_while:
            body_stmts = [s for s in body_stmts
                         if not (isinstance(s, dict) and s.get('type') == 'If'
                                 and isinstance(s.get('body'), list)
                                 and any(b.get('type') == 'Break' for b in s.get('body', [])))]

        else_stmts = self._if_generate_branch_stmts(region.else_blocks) if region.else_blocks else []

        if else_stmts and getattr(region, 'has_trailing_return_none', False):
            _non_trivial = [s for s in else_stmts if not self._is_trailing_return_none_statement(s)]
            if not _non_trivial:
                else_stmts = []

        _cond_offset = cond_block.start_offset if cond_block else (region.entry.start_offset if region.entry else 0)
        _preceding_if_cond = None
        if condition and _cond_offset > 0:
            for _tr in self.regions:
                if (not isinstance(_tr, __import__('core.cfg.region_analyzer', fromlist=['IfRegion']).IfRegion) or
                    _tr.parent is not None or
                    _tr.entry.start_offset >= _cond_offset or
                    id(_tr) in self._generated_regions or
                    id(_tr) in self._generating_regions):
                    continue
                _cco = getattr(_tr, 'chained_compare_ops', None)
                if _cco and len(_cco) >= 2:
                    _ccl = getattr(_tr, 'chained_compare_left_instr', None)
                    _ccb = getattr(_tr, 'chained_compare_blocks', None)
                    if _ccb and len(_ccb) >= 1:
                        _loop_blocks = set(region.blocks)
                        if region.header_block:
                            _loop_blocks.add(region.header_block)
                        if any(_cb in _loop_blocks for _cb in _ccb):
                            _prec_instrs = []
                            if _ccl:
                                _prec_instrs.append(_ccl)
                            _prec_entry_block = getattr(_tr, 'entry', None)
                            _prec_cond_block = getattr(_tr, 'condition_block', None)
                            if _prec_entry_block and _prec_entry_block != cond_block:
                                _ei = [i for i in _prec_entry_block.instructions
                                       if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                                _prec_instrs.extend(_ei)
                            elif _prec_cond_block and _prec_cond_block != cond_block:
                                _ci = [i for i in _prec_cond_block.instructions
                                       if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                                _prec_instrs.extend(_ci)
                            _prec_instrs.extend([
                                i for b in _ccb[:len(_cco)-1] for i in b.instructions
                                if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')
                            ])
                            if _prec_instrs:
                                _prec_expr = self.expr_reconstructor.reconstruct(_prec_instrs)
                            if _prec_expr:
                                _preceding_if_cond = _prec_expr
                                self._generated_regions.add(id(_tr))
                                for _tb in (_tr.then_blocks or []):
                                    if _tb not in self.generated_blocks and _tb != cond_block:
                                        self.generated_blocks.add(_tb)
                                        self.generated_offsets.add(_tb.start_offset)
                                break

        if _preceding_if_cond and condition:
            condition = {
                'type': 'BoolOp',
                'op': 'and',
                'values': [_preceding_if_cond, condition]
            }

        result = {
            'type': 'While',
            'test': condition if condition else {'type': 'Constant', 'value': True},
            'body': body_stmts if body_stmts else [{'type': 'Pass'}],
        }

        if else_stmts:
            result['orelse'] = else_stmts

        if pre_stmts:
            output = list(pre_stmts)
            output.append(result)
            return output
        return result



    def _loop_generate_body(self, region: LoopRegion, boolop_for_while: Optional['BoolOpRegion'] = None) -> List[Dict[str, Any]]:
        """纯角色分发器：根据block_role将每个body块分发给对应处理器"""
        body_stmts: List[Dict[str, Any]] = []
        back_edge_stmts: List[Dict[str, Any]] = []
        header = region.header_block
        if header is None:
            return body_stmts

        child_info = self._loop_collect_child_regions(region)

        pre_stmts = self._loop_generate_pre_stmts(region, body_stmts)
        if pre_stmts:
            body_stmts.extend(pre_stmts)

        body_blocks_no_header: List[BasicBlock] = []
        natural_back_edge = child_info['natural_back_edge']

        for block in region.body_blocks:
            if block in self.generated_blocks:
                continue
            if block in region.else_blocks:
                is_in_child = any(block in r.blocks for r in (region.children or []))
                if not is_in_child:
                    continue
            if block == child_info.get('iter_setup_block'):
                self.generated_blocks.add(block)
                continue
            handled = self._loop_dispatch_block(
                block, region, child_info, boolop_for_while,
                body_stmts, body_blocks_no_header, back_edge_stmts, natural_back_edge,
            )
            if not handled:
                body_blocks_no_header.append(block)

        self._loop_postprocess(region, body_stmts, body_blocks_no_header, back_edge_stmts, child_info)
        return body_stmts

    def _loop_collect_child_regions(self, region: LoopRegion) -> Dict[str, Any]:
        """从region.children收集子区域信息，不遍历全局regions列表"""
        iter_setup_block = None
        if region.region_type == RegionType.FOR_LOOP and region.header_block is not None:
            for pred in region.header_block.predecessors:
                if any(instr.opname in ('GET_ITER', 'GET_AITER') for instr in pred.instructions):
                    iter_setup_block = pred
                    break
        natural_back_edge = region.metadata.get('natural_back_edge', region.back_edge_block)
        child_try_regions: List[TryExceptRegion] = []
        child_with_regions: List[WithRegion] = []
        child_if_blocks: Set[BasicBlock] = set()
        for child in (region.children or []):
            if isinstance(child, TryExceptRegion):
                child_try_regions.append(child)
            if isinstance(child, WithRegion):
                child_with_regions.append(child)
            if isinstance(child, LoopRegion):
                if child.entry:
                    for pred in child.header_block.predecessors:
                        if any(instr.opname in ('GET_ITER', 'GET_AITER') for instr in pred.instructions):
                            if pred in region.body_blocks:
                                pass
                            break
            if isinstance(child, IfRegion) and child.parent == region:
                if (region.condition_block is not None and
                    child.condition_block == region.condition_block and
                    len(child.blocks) == 2 and
                    region.condition_block in child.blocks and
                    region.header_block in child.blocks):
                    pass
                if child.condition_block != child.entry if hasattr(child, 'entry') else True:
                    for b in child.then_blocks:
                        child_if_blocks.add(b)
                    for b in (child.else_blocks or []):
                        child_if_blocks.add(b)
        return {
            'iter_setup_block': iter_setup_block,
            'natural_back_edge': natural_back_edge,
            'child_try_regions': child_try_regions,
            'child_with_regions': child_with_regions,
            'child_if_blocks': child_if_blocks,
        }

    def _loop_generate_pre_stmts(self, region: LoopRegion, body_stmts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从init_blocks和内层for循环的iter_setup提取前置语句"""
        pre_stmts: List[Dict[str, Any]] = []

        if region.region_type == RegionType.FOR_LOOP:
            for child in (region.children or []):
                if isinstance(child, LoopRegion):
                    if child.entry:
                        for pred in child.header_block.predecessors:
                            if any(instr.opname in ('GET_ITER', 'GET_AITER') for instr in pred.instructions):
                                if pred in region.body_blocks:
                                    _pre_stmts = self._loop_extract_pre_stmts_from_block(pred)
                                    if _pre_stmts:
                                        body_stmts.extend(_pre_stmts)
                                    self.generated_blocks.add(pred)
                                break

        return pre_stmts

    def _loop_extract_for_iter_pre_stmts(self, instrs: List[Instruction], block: BasicBlock) -> Tuple[List[Dict[str,Any]], List[Instruction]]:
        """从for_iter_setup指令序列中提取前置赋值语句，返回(前置语句列表, 剩余迭代器指令)
        
        当for循环前有赋值语句时(如 result = [] / found = None)，CPython将这些语句
        和GET_ITER放在同一个基本块中。此方法将前置STORE语句提取出来作为pre_stmts，
        只保留迭代器相关指令(GET_ITER之前的LOAD等)用于表达式重建。
        """
        _pre_stmts: List[Dict[str, Any]] = []
        _remaining: List[Instruction] = []
        _buf: List[Instruction] = []
        _store_ops = ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
        for _idx, _instr in enumerate(instrs):
            if _instr.opname in _store_ops:
                _buf.append(_instr)
                _stmt = self._build_store_statement(_buf, block=block)
                if _stmt:
                    _pre_stmts.append(_stmt)
                _buf = []
                continue
            if _instr.opname in ('GET_ITER', 'GET_AITER'):
                if _buf:
                    _remaining.extend(_buf)
                    _buf = []
                _remaining.append(_instr)
                continue
            _buf.append(_instr)
        if _buf:
            _remaining.extend(_buf)
        return _pre_stmts, _remaining

    def _loop_extract_pre_stmts_from_block(self, pred: BasicBlock) -> List[Dict[str, Any]]:
        """从for循环的内层iter_setup前驱块提取前置语句"""
        _pre_stmts: List[Dict[str, Any]] = []
        _stmt_instrs: List[Instruction] = []
        for _instr in pred.instructions:
            if _instr.opname in ('GET_ITER', 'GET_AITER'):
                break
            if _instr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                continue
            if _instr.opname in FORWARD_JUMP_OPS or _instr.opname in BACKWARD_JUMP_OPS:
                break
            if _instr.opname in ('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE'):
                break
            if _instr.opname in ('POP_EXCEPT', 'PUSH_EXC_INFO', 'RERAISE',
                                'WITH_EXCEPT_START', 'CHECK_EXC_MATCH', 'CHECK_EG_MATCH'):
                continue
            if _instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_DEREF'):
                _stmt_instrs.append(_instr)
                _stmt = self._build_statement(list(_stmt_instrs))
                if _stmt:
                    _pre_stmts.append(_stmt)
                _stmt_instrs = []
                continue
            if _instr.opname == 'POP_TOP':
                if _stmt_instrs:
                    _stmt = self._build_statement(list(_stmt_instrs))
                    if _stmt:
                        _pre_stmts.append(_stmt)
                    _stmt_instrs = []
                continue
            _stmt_instrs.append(_instr)
        return _pre_stmts

    def _loop_dispatch_block(self, block: BasicBlock, region: LoopRegion,
                             child_info: Dict[str, Any], boolop_for_while,
                             body_stmts: List[Dict[str, Any]],
                             body_blocks_no_header: List[BasicBlock],
                             back_edge_stmts: List[Dict[str, Any]],
                             natural_back_edge: BasicBlock) -> bool:
        """纯粹根据block_role分发到对应的处理器，返回是否已处理"""
        header = region.header_block
        if block == header:
            stmts = self._loop_handle_header(block, region, boolop_for_while, body_stmts)
            return True
        if block == region.condition_block:
            return True
        if block == natural_back_edge and block != header:
            if self._loop_process_natural_back_edge(block, back_edge_stmts):
                return True
        block_role = self.region_analyzer.get_block_role(block)
        if block_role in (BlockRole.CONTINUE, BlockRole.PURE_CONTINUE):
            # 修复: 检查被标记为CONTINUE的块是否真的只包含跳转指令
            # 如果包含有意义的语句（如赋值、函数调用等），则不应该当作纯continue处理
            _meaningful_instrs = [
                i for i in block.instructions
                if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP')
                and i.opname not in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT',
                                    'JUMP_FORWARD', 'JUMP_ABSOLUTE')
                and i.opname not in ('POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                                    'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE')
                and i.opname not in ('JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP')
            ]
            
            # 调试输出
            # if block.start_offset in [44, 80]:
            #     import sys as _dbg
            #     _dbg.stderr.write(f'[FIX-DEBUG] Block {block.start_offset}: meaningful={len(_meaningful_instrs)}, total={len(block.instructions)}\n')
            
            if _meaningful_instrs:
                # 有意义语句，当作普通LOOP_BODY处理，添加到body_blocks_no_header
                body_blocks_no_header.append(block)
                return True
            
            # 纯continue块，使用原来的逻辑
            self._loop_handle_continue(block, region, natural_back_edge, body_blocks_no_header)
            return True
        if block_role == BlockRole.LOOP_BACK_EDGE:
            self._loop_handle_back_edge(block, region, child_info, body_stmts,
                                         body_blocks_no_header, back_edge_stmts, natural_back_edge)
            return True
        if block_role in (BlockRole.BREAK, BlockRole.PURE_BREAK):
            """
            【反编译逻辑】return → break 区分算法（Phase 35 核心修复）
            
            ═══════════════════════════════════════════════════════════════════════════════
            1. 问题描述（根因分析）:
            ─────────────────────
            **原始问题**:
            CPython 编译器对循环中的 return 语句生成的字节码块，其控制流特征与 break
            语句非常相似：两者都是跳出循环体的退出路径。
            
            **误判机制**:
            region_analyzer 在 _detect_break_continue() 方法中，将所有"跳出循环的退出块"
            统一标记为 BlockRole.BREAK，而没有区分：
            - 真正的 break 语句（用户显式写的 break）
            - 循环中的 return 语句（函数返回）
            
            这导致循环中的 return 被错误地生成为 break 语句。
            
            2. 字节码特征对比:
            ─────────────────────
            ┌─────────────────┬──────────────────────────┬──────────────────────────┐
            │ 特征             │ break 语句               │ return 语句              │
            ├─────────────────┼──────────────────────────┼──────────────────────────┤
            │ 最后指令         │ JUMP_FORWARD/JUMP_ABSOLUTE│ RETURN_VALUE/RETURN_CONST │
            │ 跳转目标         │ 循环外的第一个块         │ （无，函数终止）          │
            │ 栈行为           │ 栈不变（直接跳转）       │ 弹出返回值                │
            │ 后继块数量       │ 通常1个（跳转目标）      │ 0个（函数结束）           │
            │ 典型模式         │ JUMP_FORWARD → exit      │ LOAD_CONST x; RETURN     │
            └─────────────────┴──────────────────────────┴──────────────────────────┘
            
            3. 修复方案:
            ─────────────────────
            **核心思想**: 通过检查块的实际指令来判断真实语义
            
            **实现逻辑**:
            ```python
            if block_role in (BlockRole.BREAK, BlockRole.PURE_BREAK):
                # 检查块是否包含return操作码
                has_return = any(
                    i.opname in ('RETURN_VALUE', 'RETURN_CONST') 
                    for i in block.instructions
                )
                
                if has_return:
                    # 这是一个return块，不是break块
                    # 将其作为普通body块处理
                    body_blocks_no_header.append(block)
                    return True
                else:
                    # 这是真正的break块
                    # 返回False让调用者处理break
                    return False
            ```
            
            4. 影响范围:
            ─────────────────────
            - ✅ 修复前: basic=20f（20个测试失败）
            - ✅ 修复后: basic=7f（仅7个测试失败，改进-13f）
            - ✅ 影响: 所有包含循环内return的函数
            - ✅ 典型场景: 
                  * 搜索循环中的早期返回（找到就return）
                  * 验证循环中的错误返回
                  * 生成器函数中的yield/return混合
            
            5. 边界情况处理:
            ─────────────────────
            - ✅ 空return: RETURN_CONST None → 正确识别为return
            - ✅ 带值return: LOAD x; RETURN_VALUE → 正确识别为return
            - ✅ 表达式return: 复杂表达式计算后RETURN → 正确识别
            - ✅ 嵌套return: if中的return → 正确识别
            - ⚠️ finally中的return: 可能需要特殊处理（当前未覆盖）
            
            6. 与区域归约理论的关系:
            ────────────────────────────────
            本修复遵循"No More Gotos"论文的精确映射原则：
            - 论文要求: 每个区域节点必须准确对应源码结构
            - 实践问题: 字节码级别的模糊性需要语义级区分
            - 解决方案: 基于指令特征的启发式规则（符合论文精神）
            
            7. 测试验证:
            ─────────────────────
            运行命令: pytest tests/exhaustive/basic/ -v
            关键用例:
            - test_for_loop_return_*.py: 循环中return的各种形式
            - test_while_return_*.py: while循环中的return
            - test_nested_loop_return*.py: 嵌套循环中的return
            
            ═══════════════════════════════════════════════════════════════════════════════
            """
            # 反编译逻辑：包含RETURN_VALUE/RETURN_CONST的块是return块，不是break块
            # Python编译器对循环中的return语句生成的块可能被误标记为BREAK角色
            # 根因：region_analyzer在确定block_role时，将跳出循环的退出块统一标记为BREAK
            #       但没有区分"break退出"和"return退出"
            # 修复：检查块的实际指令，如果包含return操作码，则不当作break处理
            if any(i.opname in ('RETURN_VALUE', 'RETURN_CONST') for i in block.instructions):
                body_blocks_no_header.append(block)
                return True
            return False
        if block_role == BlockRole.LOOP_EXIT:
            self.generated_blocks.add(block)
            return True
        if self._loop_handle_child_region_entry(block, region, child_info, body_stmts):
            return True
        if block_role == BlockRole.LOOP_HEADER and block == region.header_block:
            self.generated_blocks.add(block)
            return True
        return False

    def _loop_handle_header(self, block: BasicBlock, region: LoopRegion,
                            boolop_for_while, body_stmts: List[Dict[str, Any]]) -> None:
        """处理header块的语句生成"""
        for ar in self.region_analyzer.regions:
            if isinstance(ar, AssertRegion) and ar.entry == block:
                ar_id = id(ar)
                if ar_id not in self._generated_regions and ar_id not in self._generating_regions:
                    assert_ast = self._generate_assert(ar)
                    if assert_ast:
                        body_stmts.append(assert_ast)
                    for b in ar.blocks:
                        self.generated_blocks.add(b)
                    self._generated_regions.add(ar_id)
                self.generated_blocks.add(block)
                return
        header = region.header_block
        _header_with_region = None
        for _r in region.iter_descendants((WithRegion,)):
            if _r.entry == block:
                _header_with_region = _r
                break
        if _header_with_region is not None:
            with_id = id(_header_with_region)
            if with_id not in self._generated_regions and with_id not in self._generating_regions:
                with_ast = self._generate_region(_header_with_region)
                if with_ast:
                    if isinstance(with_ast, list):
                        body_stmts.extend(with_ast)
                    else:
                        body_stmts.append(with_ast)
                for b in _header_with_region.blocks:
                    self.generated_blocks.add(b)
                self._generated_regions.add(with_id)
            self.generated_blocks.add(block)
            return
        if region.condition_block == header:
            self.generated_blocks.add(block)
            return
        if (region.region_type == RegionType.WHILE_LOOP
            and region.back_edge_block == header
            and region.condition_block is not None
            and region.condition_block != header):
            _self_loop_stmts = self._loop_extract_self_loop_stmts(header)
            body_stmts.extend(_self_loop_stmts)
            self.generated_blocks.add(header)
            self.generated_offsets.add(header.start_offset)
            return
        _header_if_region = None
        for _r in region.iter_descendants((IfRegion,)):
            if _r.condition_block == block or _r.entry == block:
                _header_if_region = _r
                break
        if (region.region_type == RegionType.WHILE_LOOP
            and region.condition_block is not None
            and region.condition_block != header):
            if _header_if_region is not None:
                pass
            else:
                _self_loop_stmts = self._loop_extract_self_loop_stmts(header)
                body_stmts.extend(_self_loop_stmts)
                self.generated_blocks.add(header)
                self.generated_offsets.add(header.start_offset)
                return
        if (region.region_type == RegionType.WHILE_LOOP and
            region.condition_block is None and
            header.instructions and
            header.instructions[0].opname in PLACEHOLDER_OPS and
            any(i.opname not in PLACEHOLDER_OPS for i in header.instructions)):
            self._loop_handle_header_no_condition(block, body_stmts, region)
            return
        _header_region = self.region_analyzer.get_region_for_block(block)
        if _header_if_region is None:
            for _r in region.iter_descendants((IfRegion,)):
                if _r.condition_block == block or _r.entry == block:
                    _header_if_region = _r
                    break
        if _header_if_region is not None:
            is_loop_cond_if = (_header_if_region.condition_block == region.condition_block or
                _header_if_region.condition_block == region.header_block)
            is_really_nested = (region.condition_block is not None and
                region.condition_block not in _header_if_region.blocks)
            if is_loop_cond_if and not is_really_nested:
                cond_succs = list(block.conditional_successors)
                is_if_break_pattern = False
                if len(cond_succs) == 2:
                    then_succ, else_succ = sorted(cond_succs, key=lambda s: s.start_offset)
                    then_last = then_succ.get_last_instruction()
                    else_last = else_succ.get_last_instruction()
                    is_if_break_pattern = (
                        then_last and then_last.opname in ('RETURN_VALUE', 'RETURN_CONST') and
                        else_last and else_last.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')
                    )
                if is_if_break_pattern and region.is_while_true:
                    instrs = [i for i in block.instructions
                             if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                    jump_instr = None
                    for i in instrs:
                        if i.opname.startswith('POP_JUMP') or i.opname.startswith('JUMP_IF') or i.opname in ('JUMP_FORWARD', 'JUMP_BACKWARD'):
                            jump_instr = i
                            break
                    if jump_instr:
                        pre_cond_instrs = [i for i in instrs if i != jump_instr]
                        if pre_cond_instrs:
                            _stmt_end = len(pre_cond_instrs)
                            for _si in range(len(pre_cond_instrs) - 1, -1, -1):
                                if pre_cond_instrs[_si].opname in ('POP_TOP', 'RETURN_VALUE', 'RETURN_CONST'):
                                    _stmt_end = _si + 1
                                    break
                                if pre_cond_instrs[_si].opname in ('COMPARE_OP', 'IS_OP', 'IS_NOT', 'CONTAINS_OP', 'NOT_OP', 'UNARY_NOT'):
                                    _stmt_end = _si
                                    break
                            if _stmt_end > 0 and _stmt_end < len(pre_cond_instrs):
                                _leading = pre_cond_instrs[:_stmt_end]
                                _cond_instrs = pre_cond_instrs[_stmt_end:]
                                _acc = []
                                for _li in _leading:
                                    _acc.append(_li)
                                    if _li.opname in ('POP_TOP', 'STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL', 'STORE_DEREF', 'RETURN_VALUE', 'RETURN_CONST'):
                                        _ls = self._build_statement(_acc)
                                        if _ls:
                                            body_stmts.append(_ls)
                                        _acc = []
                                test_expr = self.expr_reconstructor.reconstruct(_cond_instrs)
                            else:
                                test_expr = self.expr_reconstructor.reconstruct(pre_cond_instrs)
                            if test_expr is None:
                                test_expr = self._build_statement(pre_cond_instrs)
                                if test_expr and test_expr.get('type') == 'Expr':
                                    test_expr = test_expr.get('value')
                            if test_expr:
                                # Phase 41修复: 循环内if+return值保持为return而非break
                                # 当循环中"if cond: return <value>"被误识别为"if cond: break"时，
                                # 字节码会多出else: return None且丢失返回值。
                                # 检测then_succ是否包含RETURN_VALUE/RETURN_CONST且有实际返回值。
                                _then_jump_target = None
                                _last_i = block.get_last_instruction()
                                if _last_i and _last_i.argval is not None:
                                    _then_jump_target = self.cfg.get_block_by_offset(_last_i.argval)
                                _return_val = None
                                if _then_jump_target:
                                    _then_instrs = [i for i in _then_jump_target.instructions
                                                   if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                                    if _then_instrs and _then_instrs[0].opname in ('LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF'):
                                        _return_val = {'type': 'Name', 'id': _then_instrs[0].argval, 'ctx': 'Load'}
                                    elif _then_instrs and _then_instrs[0].opname == 'LOAD_CONST':
                                        _return_val = {'type': 'Constant', 'value': _then_instrs[0].argval}
                                if _return_val is not None:
                                    body_stmts.append({
                                        'type': 'If',
                                        'test': test_expr,
                                        'body': [{'type': 'Return', 'value': _return_val}],
                                        'orelse': None
                                    })
                                else:
                                    body_stmts.append({
                                        'type': 'If',
                                        'test': test_expr,
                                        'body': [{'type': 'Break'}],
                                        'orelse': None
                                    })
                                self.generated_blocks.add(block)
                else:
                    instrs = [i for i in block.instructions
                             if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                    jump_instr = None
                    for i in instrs:
                        if i.opname.startswith('POP_JUMP') or i.opname.startswith('JUMP_IF') or i.opname in ('JUMP_FORWARD', 'JUMP_BACKWARD'):
                            jump_instr = i
                            break
                    body_instrs = [i for i in instrs if i is not jump_instr]
                    if body_instrs:
                        acc = []
                        for bi in body_instrs:
                            acc.append(bi)
                            if bi.opname in ('STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL', 'STORE_DEREF',
                                            'POP_TOP', 'RETURN_VALUE', 'RETURN_CONST'):
                                s = self._build_statement(acc)
                                if s:
                                    body_stmts.append(s)
                                acc = []
                    self.generated_blocks.add(block)
            else:
                _if_ast = self._generate_region(_header_if_region)
                if _if_ast:
                    if isinstance(_if_ast, list):
                        body_stmts.extend(_if_ast)
                    else:
                        body_stmts.append(_if_ast)
                for b in _header_if_region.blocks:
                    self.generated_blocks.add(b)
                self.generated_blocks.add(block)
        elif _header_region is not None and isinstance(_header_region, IfRegion) and _header_region.condition_block == block:
            if (_header_region.condition_block == region.condition_block or
                _header_region.condition_block == region.header_block):
                instrs = [i for i in block.instructions
                         if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                jump_instr = None
                for i in instrs:
                    if i.opname.startswith('POP_JUMP') or i.opname.startswith('JUMP_IF') or i.opname in ('JUMP_FORWARD', 'JUMP_BACKWARD'):
                        jump_instr = i
                        break
                if jump_instr:
                    body_instrs = [i for i in instrs if i is not jump_instr]
                else:
                    body_instrs = instrs
                if body_instrs:
                    acc = []
                    for bi in body_instrs:
                        acc.append(bi)
                        if bi.opname in ('STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL', 'STORE_DEREF',
                                        'POP_TOP', 'RETURN_VALUE', 'RETURN_CONST'):
                            s = self._build_statement(acc)
                            if s:
                                body_stmts.append(s)
                            acc = []
                self.generated_blocks.add(block)
            else:
                self._loop_handle_boolop_or_if_header(block, _header_region, boolop_for_while, body_stmts)
        elif isinstance(_header_region, LoopRegion) and _header_region is not region:
            if _header_region.header_block == block or _header_region.condition_block == block:
                _region_id = id(_header_region)
                if _region_id in self._generating_regions or _region_id in self._generated_regions:
                    pass
                else:
                    self._generating_regions.add(_region_id)
                    try:
                        _loop_ast = self._generate_region(_header_region)
                    finally:
                        self._generating_regions.discard(_region_id)
                    if _loop_ast:
                        if isinstance(_loop_ast, list):
                            body_stmts.extend(_loop_ast)
                        else:
                            body_stmts.append(_loop_ast)
                    for b in _header_region.blocks:
                        self.generated_blocks.add(b)
                    self._generated_regions.add(_region_id)
            else:
                self.generated_blocks.add(block)
        else:
            _nested_loop = None
            for _nlr in self.region_analyzer.regions:
                if isinstance(_nlr, LoopRegion) and _nlr is not region:
                    if _nlr.header_block == block or _nlr.condition_block == block or _nlr.entry == block:
                        _nested_loop = _nlr
                        break
            if _nested_loop is not None:
                _region_id = id(_nested_loop)
                if _region_id not in self._generating_regions and _region_id not in self._generated_regions:
                    self._generating_regions.add(_region_id)
                    try:
                        _loop_ast = self._generate_region(_nested_loop)
                    finally:
                        self._generating_regions.discard(_region_id)
                    if _loop_ast:
                        if isinstance(_loop_ast, list):
                            body_stmts.extend(_loop_ast)
                        else:
                            body_stmts.append(_loop_ast)
                    for b in _nested_loop.blocks:
                        self.generated_blocks.add(b)
                    self._generated_regions.add(_region_id)
                else:
                    self.generated_blocks.add(block)
            else:
                _nested_region_generated = False
                _try_region = None
                for _ntr in self.region_analyzer.regions:
                    if isinstance(_ntr, TryExceptRegion) and _ntr.entry == block and id(_ntr) not in self._generated_regions:
                        _try_region = _ntr
                        break
                if _try_region:
                    _try_ast = self._generate_region(_try_region)
                    if _try_ast:
                        body_stmts.append(_try_ast)
                    for b in _try_region.blocks:
                        self.generated_blocks.add(b)
                    _nested_region_generated = True
                elif isinstance(_header_region, WithRegion) and _header_region.entry == block:
                    _with_ast = self._generate_region(_header_region)
                    if _with_ast:
                        if isinstance(_with_ast, list):
                            body_stmts.extend(_with_ast)
                        else:
                            body_stmts.append(_with_ast)
                    for b in _header_region.blocks:
                        self.generated_blocks.add(b)
                    _nested_region_generated = True
                if not _nested_region_generated:
                    self._loop_process_header_instructions(block, region, body_stmts)

    def _loop_extract_self_loop_stmts(self, hdr: BasicBlock) -> List[Dict[str, Any]]:
        """从self-loop header中提取普通语句（排除条件重检部分，处理条件break）"""
        import dis as _dis
        _self_loop_stmts: List[Dict[str, Any]] = []
        _self_loop_instrs: List[Instruction] = []
        _last_i = hdr.get_last_instruction()
        _body_end_idx = None
        _cond_break_start_idx = None
        _cond_break_instr = None
        if _last_i and _last_i.opname in BACKWARD_CONDITIONAL_JUMP_OPS:
            _last_store_idx = -1
            _last_store_is_walrus = False
            _walrus_store_idx = -1
            for _sli in range(len(hdr.instructions) - 2, -1, -1):
                _sl_instr = hdr.instructions[_sli]
                if _sl_instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                    if _sli > 0 and hdr.instructions[_sli - 1].opname == 'COPY' and hdr.instructions[_sli - 1].arg == 1:
                        _walrus_store_idx = _sli
                        _last_store_is_walrus = True
                    else:
                        _last_store_idx = _sli
                    break
            if _walrus_store_idx >= 0 and _walrus_store_idx < len(hdr.instructions) - 1:
                _next_idx = _walrus_store_idx + 1
                _next_instrs = hdr.instructions[_next_idx:]
                _is_pure_walrus_recheck = all(
                    i.opname in ('PUSH_NULL', 'LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF',
                                 'PRECALL', 'CALL', 'LOAD_METHOD', 'LOAD_ATTR', 'COPY', 'POP_TOP')
                    for i in _next_instrs if i.opname not in ('RESUME', 'NOP', 'CACHE')
                )
                if _is_pure_walrus_recheck:
                    _body_end_idx = _walrus_store_idx
            if _body_end_idx is None and _last_store_idx >= 0:
                _body_end_idx = _last_store_idx
                for _ext_idx in range(_last_store_idx + 1, len(hdr.instructions) - 1):
                    _ext_instr = hdr.instructions[_ext_idx]
                    if _ext_instr.opname == 'POP_TOP':
                        _body_end_idx = _ext_idx
                    elif _ext_instr.opname not in ('PUSH_NULL', 'LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL',
                                                     'LOAD_DEREF', 'PRECALL', 'CALL', 'LOAD_METHOD',
                                                     'LOAD_ATTR', 'BUILD_TUPLE', 'BUILD_LIST',
                                                     'BUILD_MAP', 'FORMAT_VALUE'):
                        break
            if _body_end_idx is None:
                stack_depth = 0
                for _sli in range(len(hdr.instructions) - 1, -1, -1):
                    _sl_instr = hdr.instructions[_sli]
                    try:
                        effect = _dis.stack_effect(_sl_instr.opcode, _sl_instr.arg)
                    except Exception:
                        effect = 0
                    stack_depth -= effect
                    if stack_depth <= 0:
                        _body_end_idx = _sli - 1
                        break
        elif _last_i and _last_i.opname in FORWARD_CONDITIONAL_JUMP_OPS:
            _cond_break_instr = _last_i
            _last_store_idx = -1
            _walrus_store_idx = -1
            for _sli in range(len(hdr.instructions) - 2, -1, -1):
                _sl_instr = hdr.instructions[_sli]
                if _sl_instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                    if _sli > 0 and hdr.instructions[_sli - 1].opname == 'COPY' and hdr.instructions[_sli - 1].arg == 1:
                        _walrus_store_idx = _sli
                    else:
                        _last_store_idx = _sli
                    break
            if _walrus_store_idx >= 0:
                _cond_break_start_idx = _walrus_store_idx + 1
                _body_end_idx = _walrus_store_idx
            elif _last_store_idx >= 0:
                _body_end_idx = _last_store_idx
                _cond_break_start_idx = _last_store_idx + 1
            else:
                stack_depth = 0
                for _sli in range(len(hdr.instructions) - 1, -1, -1):
                    _sl_instr = hdr.instructions[_sli]
                    try:
                        effect = _dis.stack_effect(_sl_instr.opcode, _sl_instr.arg)
                    except Exception:
                        effect = 0
                    stack_depth -= effect
                    if stack_depth <= 0:
                        _cond_break_start_idx = _sli
                        _body_end_idx = _sli - 1
                        break
        for _sli_idx, _sli_instr in enumerate(hdr.instructions):
            if _sli_instr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                continue
            if _body_end_idx is not None and _sli_idx > _body_end_idx:
                break
            if _sli_instr.opname in ('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE'):
                break
            if _sli_instr.opname in BACKWARD_CONDITIONAL_JUMP_OPS:
                break
            if _sli_instr.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                break
            if _sli_instr.opname in ('POP_EXCEPT', 'PUSH_EXC_INFO', 'RERAISE',
                                    'WITH_EXCEPT_START', 'CHECK_EXC_MATCH', 'CHECK_EG_MATCH'):
                continue
            if _sli_instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                _self_loop_instrs.append(_sli_instr)
                _stmt = self._build_store_statement(_self_loop_instrs, block=hdr)
                if _stmt:
                    _self_loop_stmts.append(_stmt)
                _self_loop_instrs = []
                continue
            _self_loop_instrs.append(_sli_instr)
        if _self_loop_instrs:
            _stmt = self._build_statement(_self_loop_instrs)
            if _stmt:
                _self_loop_stmts.append(_stmt)
        if _cond_break_start_idx is not None and _cond_break_instr is not None:
            _is_compound_loop_cond = False
            if self._current_loop and _cond_break_instr.argval is not None:
                for _succ_ft in hdr.successors:
                    if _succ_ft.start_offset != _cond_break_instr.argval:
                        _ft_role_tmp = self.region_analyzer.get_block_role(_succ_ft)
                        if _ft_role_tmp == BlockRole.LOOP_BACK_EDGE:
                            _ft_last_i = _succ_ft.get_last_instruction()
                            if _ft_last_i and _ft_last_i.opname in BACKWARD_CONDITIONAL_JUMP_OPS:
                                _is_compound_loop_cond = True
                            break
            if _is_compound_loop_cond:
                return _self_loop_stmts
            _cb_instrs = [i for i in hdr.instructions[_cond_break_start_idx:]
                         if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')
                         and i != _cond_break_instr]
            if _cb_instrs:
                _cb_expr = self.expr_reconstructor.reconstruct(_cb_instrs)
                if _cb_expr:
                    _cb_last = _cond_break_instr
                    _if_false = 'IF_FALSE' in _cb_last.opname or 'IF_NOT_NONE' not in _cb_last.opname and 'IF_NONE' not in _cb_last.opname
                    _negate = 'IF_TRUE' in _cb_last.opname or 'IF_NONE' in _cb_last.opname
                    _cb_cond = _negate_expr(_cb_expr) if _negate else _cb_expr
                    _if_body_type = 'Break'
                    _fall_through_block = None
                    _jump_to_continue = False
                    _ft_is_continue = False
                    if _if_false and _cb_last.argval is not None:
                        _jt_offset = _cb_last.argval
                        _jt_block = self.cfg.get_block_by_offset(_jt_offset)
                        if _jt_block and self._block_is_continue_target(_jt_block):
                            _jump_to_continue = True
                        for _succ in hdr.successors:
                            if _succ.start_offset != _jt_offset:
                                _fall_through_block = _succ
                                if self._block_is_continue_target(_succ):
                                    _if_body_type = 'Continue'
                                    _ft_is_continue = True
                                break
                    elif not _if_false and _cb_last.argval is not None:
                        _jt_block = self.cfg.get_block_by_offset(_cb_last.argval)
                        if _jt_block and self._block_is_continue_target(_jt_block):
                            _jump_to_continue = True
                            _if_body_type = 'Continue'
                        if not _jump_to_continue:
                            for _succ in hdr.successors:
                                if _succ.start_offset != _cb_last.argval:
                                    _fall_through_block = _succ
                                    if self._block_is_continue_target(_succ):
                                        _ft_is_continue = True
                                    break
                    if _ft_is_continue and _fall_through_block is not None and _cb_last.argval is not None:
                        _jt_block2 = self.cfg.get_block_by_offset(_cb_last.argval)
                        _jt_role2 = self.region_analyzer.get_block_role(_jt_block2) if _jt_block2 else None
                        _jt_is_exit = (_jt_role2 in (BlockRole.RETURN, BlockRole.RETURN_NONE, BlockRole.BREAK, BlockRole.PURE_BREAK))
                        if not _jt_is_exit:
                            _is_none_check = 'IF_NONE' in _cb_last.opname or 'IF_NOT_NONE' in _cb_last.opname
                            if _is_none_check:
                                if 'IF_NOT_NONE' in _cb_last.opname:
                                    _cont_cond = {'type': 'Compare', 'left': _cb_expr, 'ops': ['Is'], 'comparators': [{'type': 'Constant', 'value': None}]}
                                else:
                                    _cont_cond = {'type': 'Compare', 'left': _cb_expr, 'ops': ['IsNot'], 'comparators': [{'type': 'Constant', 'value': None}]}
                                _self_loop_stmts.append({
                                    'type': 'If',
                                    'test': _cont_cond,
                                    'body': [{'type': 'Continue'}],
                                    'orelse': [],
                                })
                                _jump_to_continue = True
                    if _jump_to_continue and _fall_through_block is not None and not _ft_is_continue:
                        _ft_role = self.region_analyzer.get_block_role(_fall_through_block)
                        _ft_is_exit = (_ft_role in (BlockRole.RETURN, BlockRole.RETURN_NONE, BlockRole.BREAK, BlockRole.PURE_BREAK) or
                            _fall_through_block not in self._current_loop.body_blocks and _fall_through_block != self._current_loop.header_block)
                        if not _ft_is_exit:
                            _then_stmts = self._generate_block_statements(_fall_through_block)
                            if _fall_through_block not in self.generated_blocks:
                                self.generated_blocks.add(_fall_through_block)
                            _self_loop_stmts.append({
                                'type': 'If',
                                'test': _cb_cond,
                                'body': _then_stmts if _then_stmts else [{'type': 'Pass'}],
                                'orelse': [],
                            })
                        else:
                            _ft_last_i = _fall_through_block.get_last_instruction() if _fall_through_block else None
                            _is_early_return = False
                            if _ft_last_i:
                                if _ft_last_i.opname == 'RETURN_CONST' and _ft_last_i.argval is not None:
                                    _is_early_return = True
                                elif _ft_last_i.opname == 'RETURN_VALUE':
                                    for _ri in reversed(_fall_through_block.instructions):
                                        if _ri == _ft_last_i:
                                            continue
                                        if _ri.opname in ('LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF'):
                                            _is_early_return = True
                                            break
                                        if _ri.opname == 'LOAD_CONST' and _ri.argval is not None:
                                            _is_early_return = True
                                            break
                                        if _ri.opname not in ('NOP', 'CACHE', 'POP_TOP'):
                                            break
                            if _is_early_return:
                                _ret_ast = self._generate_return_ast(_fall_through_block)
                                _then_ret = [_ret_ast] if _ret_ast else [{'type': 'Return', 'value': {'type': 'Constant', 'value': None}}]
                                if _fall_through_block not in self.generated_blocks:
                                    self.generated_blocks.add(_fall_through_block)
                                self.generated_offsets.add(_fall_through_block.start_offset)
                                _self_loop_stmts.append({
                                    'type': 'If',
                                    'test': _cb_cond,
                                    'body': _then_ret,
                                    'orelse': [],
                                })
                            else:
                                _self_loop_stmts.append({
                                    'type': 'If',
                                    'test': _cb_cond,
                                    'body': [{'type': _if_body_type}],
                                    'orelse': [],
                                })
                    else:
                        _jt_is_break = False
                        if _cb_last.argval is not None and _fall_through_block is not None:
                            _jt_block3 = self.cfg.get_block_by_offset(_cb_last.argval)
                            if _jt_block3:
                                _jt_role3 = self.region_analyzer.get_block_role(_jt_block3)
                                if _jt_role3 in (BlockRole.RETURN, BlockRole.RETURN_NONE, BlockRole.BREAK, BlockRole.PURE_BREAK, BlockRole.IF_THEN):
                                    _ft_role3 = self.region_analyzer.get_block_role(_fall_through_block)
                                    _ft_in_body = (_fall_through_block in self._current_loop.body_blocks or
                                        _fall_through_block == self._current_loop.header_block)
                                    if _ft_in_body and _ft_role3 not in (BlockRole.RETURN, BlockRole.RETURN_NONE, BlockRole.BREAK, BlockRole.PURE_BREAK):
                                        _jt_is_break = True
                        if _jt_is_break:
                            _then_stmts2 = self._generate_block_statements(_fall_through_block)
                            if _fall_through_block not in self.generated_blocks:
                                self.generated_blocks.add(_fall_through_block)
                            _self_loop_stmts.append({
                                'type': 'If',
                                'test': _cb_cond,
                                'body': _then_stmts2 if _then_stmts2 else [{'type': 'Pass'}],
                                'orelse': [{'type': 'Break'}],
                            })
                        else:
                            _ft_last_i2 = _fall_through_block.get_last_instruction() if _fall_through_block else None
                            _is_early_ret = False
                            if _ft_last_i2:
                                if _ft_last_i2.opname == 'RETURN_CONST' and _ft_last_i2.argval is not None:
                                    _is_early_ret = True
                                elif _ft_last_i2.opname == 'RETURN_VALUE':
                                    for _ri2 in reversed(_fall_through_block.instructions):
                                        if _ri2 == _ft_last_i2:
                                            continue
                                        if _ri2.opname in ('LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF'):
                                            _is_early_ret = True
                                            break
                                        if _ri2.opname == 'LOAD_CONST' and _ri2.argval is not None:
                                            _is_early_ret = True
                                            break
                                        if _ri2.opname not in ('NOP', 'CACHE', 'POP_TOP'):
                                            break
                            if _is_early_ret:
                                _ret_ast2 = self._generate_return_ast(_fall_through_block)
                                _then_ret2 = [_ret_ast2] if _ret_ast2 else [{'type': 'Return', 'value': {'type': 'Constant', 'value': None}}]
                                if _fall_through_block not in self.generated_blocks:
                                    self.generated_blocks.add(_fall_through_block)
                                self.generated_offsets.add(_fall_through_block.start_offset)
                                _self_loop_stmts.append({
                                    'type': 'If',
                                    'test': _cb_cond,
                                    'body': _then_ret2,
                                    'orelse': [],
                                })
                            else:
                                _self_loop_stmts.append({
                                    'type': 'If',
                                    'test': _cb_cond,
                                    'body': [{'type': _if_body_type}],
                                    'orelse': [],
                                })
        return _self_loop_stmts

    def _loop_handle_header_no_condition(self, block: BasicBlock, body_stmts: List[Dict[str, Any]], region: LoopRegion = None) -> None:
        """处理无条件while header（如 while True 中带break的情形）"""
        if region is not None:
            nested_if = None
            for _r in region.iter_descendants((IfRegion,)):
                if _r.entry == block or _r.condition_block == block:
                    nested_if = _r
                    break
            if nested_if is not None:
                cond_succs = list(block.conditional_successors)
                if len(cond_succs) == 2:
                    then_succ, else_succ = sorted(cond_succs, key=lambda s: s.start_offset)
                    then_last = then_succ.get_last_instruction()
                    if then_last and then_last.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                        cond_instrs = [i for i in block.instructions
                                      if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                        jump_instr = None
                        for i in cond_instrs:
                            if i.opname in ('POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                                           'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE'):
                                jump_instr = i
                                break
                        if jump_instr:
                            pre_cond_instrs = [i for i in cond_instrs if i != jump_instr]
                            if pre_cond_instrs:
                                _stmt_end = len(pre_cond_instrs)
                                for _si in range(len(pre_cond_instrs) - 1, -1, -1):
                                    if pre_cond_instrs[_si].opname in ('POP_TOP', 'RETURN_VALUE', 'RETURN_CONST'):
                                        _stmt_end = _si + 1
                                        break
                                    if pre_cond_instrs[_si].opname in ('COMPARE_OP', 'IS_OP', 'IS_NOT', 'CONTAINS_OP', 'NOT_OP', 'UNARY_NOT'):
                                        _stmt_end = _si
                                        break
                                if _stmt_end > 0 and _stmt_end < len(pre_cond_instrs):
                                    _leading = pre_cond_instrs[:_stmt_end]
                                    _cond_instrs = pre_cond_instrs[_stmt_end:]
                                    _acc = []
                                    for _li in _leading:
                                        _acc.append(_li)
                                        if _li.opname in ('POP_TOP', 'STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL', 'STORE_DEREF', 'RETURN_VALUE', 'RETURN_CONST'):
                                            _ls = self._build_statement(_acc)
                                            if _ls:
                                                body_stmts.append(_ls)
                                            _acc = []
                                    test_expr = self.expr_reconstructor.reconstruct(_cond_instrs)
                                else:
                                    test_expr = self.expr_reconstructor.reconstruct(pre_cond_instrs)
                                if test_expr is None:
                                    test_expr = self._build_statement(pre_cond_instrs)
                                    if test_expr and test_expr.get('type') == 'Expr':
                                        test_expr = test_expr.get('value')
                                if test_expr:
                                    # Phase 41修复: 循环内if+return值保持为return（for循环路径）
                                    _then_ret_val = None
                                    _then_target_block = then_succ
                                    if _then_target_block:
                                        _ti = [i for i in _then_target_block.instructions
                                              if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                                        if _ti and _ti[0].opname in ('LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF'):
                                            _then_ret_val = {'type': 'Name', 'id': _ti[0].argval, 'ctx': 'Load'}
                                        elif _ti and _ti[0].opname == 'LOAD_CONST':
                                            _then_ret_val = {'type': 'Constant', 'value': _ti[0].argval}
                                    if _then_ret_val is not None:
                                        body_stmts.append({
                                            'type': 'If',
                                            'test': test_expr,
                                            'body': [{'type': 'Return', 'value': _then_ret_val}],
                                            'orelse': None
                                        })
                                    else:
                                        body_stmts.append({
                                            'type': 'If',
                                            'test': test_expr,
                                            'body': [{'type': 'Break'}],
                                            'orelse': None
                                        })
                                    self.generated_blocks.add(block)
                                    for b in then_succ.blocks if hasattr(then_succ, 'blocks') else [then_succ]:
                                        self.generated_blocks.add(b)
                                    return
        _block_stmts = self._generate_block_statements(block)
        _filtered: List[Dict[str, Any]] = []
        _has_break = False
        for _s in _block_stmts:
            if _s.get('type') == 'Return' and _s.get('value', {}).get('value') is None:
                continue
            if _s.get('type') == 'Break':
                _has_break = True
            _filtered.append(_s)
        if not _has_break:
            _last_instr = block.get_last_instruction()
            if _last_instr and _last_instr.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                body_stmts.append({'type': 'Break'})
                _has_break = True
        if _has_break:
            _filtered = [s for s in _filtered if s.get('type') != 'Pass']
        body_stmts.extend(_filtered)
        self.generated_blocks.add(block)

    def _loop_handle_boolop_or_if_header(self, block: BasicBlock, _header_region: IfRegion,
                                         _boolop_for_while, body_stmts: List[Dict[str, Any]]) -> None:
        """处理boolop或嵌套if类型的header块"""
        _is_boolop_recheck_header = False
        if _boolop_for_while:
            boolop_cond_vars = set()
            for chain_block, _ in _boolop_for_while.op_chain:
                for i in chain_block.instructions:
                    if i.opname in ('LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF'):
                        boolop_cond_vars.add(i.argval)
            cond_instrs = [i for i in block.instructions
                          if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
            last_i = block.get_last_instruction()
            pre_cond_instrs = [i for i in cond_instrs if i != last_i]
            has_store = any(i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
                           for i in pre_cond_instrs)
            if has_store:
                pre_load_names = set()
                for i in pre_cond_instrs:
                    if i.opname in ('LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF'):
                        pre_load_names.add(i.argval)
                if last_i and last_i.opname in CONDITIONAL_JUMP_OPS:
                    _is_boolop_recheck_header = True
        if _is_boolop_recheck_header:
            _recheck_stmts: List[Dict[str, Any]] = []
            _recheck_instrs: List[Instruction] = []
            for _instr_idx, _instr in enumerate(block.instructions):
                if _instr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                    continue
                if _instr.opname in CONDITIONAL_JUMP_OPS or _instr.opname in FORWARD_JUMP_OPS:
                    break
                if _instr.opname in ('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE'):
                    break
                _recheck_instrs.append(_instr)
                if _instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                    _stmt = self._build_statement(list(_recheck_instrs))
                    if _stmt:
                        _recheck_stmts.append(_stmt)
                    _recheck_instrs = []
            body_stmts.extend(_recheck_stmts)
            self.generated_blocks.add(block)
            for b in _header_region.blocks:
                self.generated_blocks.add(b)
        else:
            _if_ast = self._generate_region(_header_region)
            if _if_ast:
                if isinstance(_if_ast, list):
                    body_stmts.extend(_if_ast)
                else:
                    body_stmts.append(_if_ast)
            for b in _header_region.blocks:
                self.generated_blocks.add(b)

    def _loop_process_header_instructions(self, block: BasicBlock, region: LoopRegion,
                                          body_stmts: List[Dict[str, Any]]) -> None:
        """指令级详细处理header块中的语句（~200行核心逻辑）"""
        _hdr_stmts: List[Dict[str, Any]] = []
        _hdr_instrs: List[Instruction] = []
        _seen_store = False
        _unpack_info = None
        _break_cause = None
        for _instr_idx, _instr in enumerate(block.instructions):
            if _instr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                continue
            if _instr.opname == 'POP_TOP':
                if _hdr_instrs:
                    _has_call = any(i.opname in ('CALL', 'CALL_FUNCTION', 'CALL_METHOD',
                                                'CALL_FUNCTION_KW', 'CALL_FUNCTION_EX')
                                   for i in _hdr_instrs)
                    if _has_call:
                        _stmt = self._build_statement(_hdr_instrs)
                        if _stmt:
                            _hdr_stmts.append(_stmt)
                        _hdr_instrs = []
                continue
            if _instr.opname in BACKWARD_JUMP_OPS:
                if _instr.opname in BACKWARD_CONDITIONAL_JUMP_OPS:
                    _break_cause = _instr
                break
            if _instr.opname in FORWARD_JUMP_OPS:
                _break_cause = _instr
                break
            if _instr.opname in ('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE'):
                break
            if _instr.opname in ('POP_EXCEPT', 'PUSH_EXC_INFO', 'RERAISE',
                                'WITH_EXCEPT_START', 'CHECK_EXC_MATCH', 'CHECK_EG_MATCH'):
                continue
            if _instr.opname == 'RAISE_VARARGS':
                _exc_expr = None
                if _instr.arg >= 1 and _hdr_instrs:
                    _exc_expr = self.expr_reconstructor.reconstruct(_hdr_instrs)
                _hdr_instrs = []
                _raise_node = {'type': 'Raise', 'exc': _exc_expr, 'cause': None}
                _hdr_stmts.append(_raise_node)
                continue
            if _instr.opname == 'COPY' and _instr.arg == COPY_STACK_TOP:
                _hdr_instrs.append(_instr)
                continue
            if _instr.opname == 'UNPACK_SEQUENCE':
                _val_instrs = [i for i in _hdr_instrs if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                _val = self.expr_reconstructor.reconstruct(_val_instrs) if _val_instrs else None
                _unpack_info = {'value': _val, 'targets': [], 'count': _instr.arg}
                _hdr_instrs = []
                continue
            if _instr.opname == 'UNPACK_EX':
                _val_instrs = [i for i in _hdr_instrs if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                _val = self.expr_reconstructor.reconstruct(_val_instrs) if _val_instrs else None
                _arg = _instr.argval
                _before = _arg & 0xFF
                _after = (_arg >> 8) & 0xFF
                _unpack_info = {'value': _val, 'targets': [], 'count': _before + 1 + _after, 'is_starred': True, 'starred_idx': _before}
                _hdr_instrs = []
                continue
            if _instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                _is_walrus = len(_hdr_instrs) >= 2 and _hdr_instrs[-1].opname == 'COPY' and _hdr_instrs[-1].arg == 1
                if _unpack_info is not None:
                    _is_starred = _unpack_info.get('is_starred', False)
                    _starred_idx = _unpack_info.get('starred_idx', -1)
                    _current_target_idx = len(_unpack_info['targets'])
                    if _is_starred and _current_target_idx == _starred_idx:
                        _unpack_info['targets'].append({
                            'type': 'Starred',
                            'value': {'type': 'Name', 'id': _instr.argval if _instr.argval else f'var_{_instr.arg}', 'ctx': 'Store'},
                        })
                    else:
                        _unpack_info['targets'].append({
                            'type': 'Name',
                            'id': _instr.argval if _instr.argval else f'var_{_instr.arg}',
                            'ctx': 'Store',
                        })
                    if len(_unpack_info['targets']) == _unpack_info['count']:
                        _target = {'type': 'Tuple', 'elts': _unpack_info['targets'], 'ctx': 'Store'}
                        if _unpack_info['value']:
                            _hdr_stmts.append({'type': 'Assign', 'targets': [_target], 'value': _unpack_info['value']})
                        _unpack_info = None
                    _hdr_instrs = []
                    _seen_store = True
                    continue
                if _is_walrus:
                    _hdr_instrs.append(_instr)
                    _seen_store = True
                    continue
                _hdr_instrs.append(_instr)
                _stmt = self._build_store_statement(_hdr_instrs, block=block)
                if _stmt:
                    _hdr_stmts.append(_stmt)
                _hdr_instrs = []
                _seen_store = True
                continue
            if _instr.opname == 'COMPARE_OP' and _seen_store:
                _next_idx = _instr_idx + 1
                _next_instr = block.instructions[_next_idx] if _next_idx < len(block.instructions) else None
                if _next_instr and _next_instr.opname in BACKWARD_CONDITIONAL_JUMP_OPS:
                    _hdr_instrs = []
                    continue
                _hdr_instrs.append(_instr)
                continue
            _hdr_instrs.append(_instr)
        if _break_cause is not None:
            self._loop_process_header_break_condition(block, _break_cause, _hdr_stmts, region)
        else:
            pass
        body_stmts.extend(_hdr_stmts)
        self.generated_blocks.add(block)

    def _loop_process_header_break_condition(self, block: BasicBlock, _break_cause: Instruction,
                                             _hdr_stmts: List[Dict[str, Any]], region: LoopRegion) -> None:
        """处理header中的break条件分支"""
        if _break_cause.opname not in FORWARD_CONDITIONAL_JUMP_OPS or (not _hdr_stmts and not []):
            return
        if block == region.header_block and region.pre_condition_blocks:
            _jump_target = None
            if _break_cause.argval is not None:
                _jump_target = self.cfg.get_block_by_offset(_break_cause.argval)
            _fall_through = None
            for _succ in block.successors:
                if _succ != _jump_target:
                    _fall_through = _succ
                    break
            if _fall_through and _fall_through in region.body_blocks:
                return
        _loop_body_set = region.metadata.get('loop_body_full_set', set(region.body_blocks) | {region.header_block})
        if region.condition_block and 'condition_block' not in str(_loop_body_set):
            _loop_body_set = _loop_body_set | {region.condition_block}
        _block_succ_outside = [s for s in block.successors if s not in _loop_body_set]
        _block_succ_break = [s for s in block.successors
                             if self.region_analyzer.get_block_role(s) in (BlockRole.PURE_BREAK, BlockRole.BREAK)]
        _block_succ_return = [s for s in block.successors
                              if self.region_analyzer.get_block_role(s) in (BlockRole.RETURN, BlockRole.RETURN_NONE)]
        _has_cond_chain = region.condition_block and len(region.condition_chain_blocks) > 1
        _exit_succs = _block_succ_break + _block_succ_return + _block_succ_outside
        _jump_block = self.cfg.get_block_by_offset(_break_cause.argval) if _break_cause.argval is not None else None
        _fall_through = None
        for _s in block.successors:
            if _s != _jump_block:
                _fall_through = _s
                break
        if (_block_succ_outside or _block_succ_break or _block_succ_return) and not _has_cond_chain:
            self._loop_handle_exit_successors(block, _break_cause, _jump_block, _fall_through,
                                              _exit_succs, _block_succ_break, _block_succ_return,
                                              _loop_body_set, _hdr_stmts)
        elif not _exit_succs and _jump_block and _fall_through and not _has_cond_chain:
            self._loop_handle_no_exit_successors(block, _break_cause, _jump_block, _fall_through, _hdr_stmts)
        if _break_cause.opname in BACKWARD_CONDITIONAL_JUMP_OPS and _hdr_stmts:
            _loop_body_set2 = region.metadata.get('loop_body_full_set', set(region.body_blocks) | {region.header_block})
            if region.condition_block and 'condition_block' not in str(_loop_body_set2):
                _loop_body_set2 = _loop_body_set2 | {region.condition_block}
            _jump_target2 = self.cfg.get_block_by_offset(_break_cause.argval) if _break_cause.argval else None
            if _jump_target2 and _jump_target2 in _loop_body_set2:
                self.generated_offsets.add(block.start_offset)

    def _loop_handle_exit_successors(self, block: BasicBlock, _break_cause: Instruction,
                                     _jump_block, _fall_through,
                                     _exit_succs, _block_succ_break, _block_succ_return,
                                     _loop_body_set, _hdr_stmts: List[Dict[str, Any]]) -> None:
        _cond_instrs: List[Instruction] = []
        for _cinstr in block.instructions:
            if _cinstr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                continue
            if _cinstr.opname in FORWARD_JUMP_OPS:
                break
            _cond_instrs.append(_cinstr)
        _split_idx = -1
        for _ci_i, _ci in enumerate(_cond_instrs):
            if _ci.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                _split_idx = _ci_i
        if _split_idx >= 0:
            _cond_instrs = _cond_instrs[_split_idx + 1:]
        # [修复] 过滤末尾可能多余的POP_TOP指令（避免指令数+1~+2）
        while _cond_instrs and _cond_instrs[-1].opname == 'POP_TOP':
            _cond_instrs.pop()
        if _cond_instrs:
            _expr = self.expr_reconstructor.reconstruct(_cond_instrs)
            if _expr:
                _is_none_check = _break_cause.opname in NONE_CHECK_OPS
                if _is_none_check:
                    _is_not_none = 'NOT_NONE' in _break_cause.opname
                    if _is_not_none:
                        _none_expr = {'type': 'Compare', 'left': _expr,
                                     'ops': [{'type': 'IsNot'}],
                                     'comparators': [{'type': 'Constant', 'value': None}]}
                    else:
                        _none_expr = {'type': 'Compare', 'left': _expr,
                                     'ops': [{'type': 'Is'}],
                                     'comparators': [{'type': 'Constant', 'value': None}]}
                    _expr = _none_expr
                _jumps_inside = (_jump_block in _loop_body_set and self.region_analyzer.get_block_role(_jump_block) not in (BlockRole.PURE_BREAK, BlockRole.BREAK)) if _jump_block else False
                _is_if_false = 'IF_FALSE' in _break_cause.opname
                if _is_none_check:
                    _is_if_false = not _is_not_none
                _ft_is_exit = _fall_through in _exit_succs if _fall_through else False
                _jt_is_exit = _jump_block in _exit_succs if _jump_block else False
                if _ft_is_exit or _jt_is_exit:
                    self._loop_build_if_with_exit_branches(_expr, _is_if_false, _fall_through, _jump_block,
                                                           _exit_succs, _block_succ_break, _block_succ_return, _hdr_stmts)
                elif _block_succ_return and not _block_succ_break and not [_s for s in _exit_succs if s not in _block_succ_return]:
                    _negate = (not _is_if_false) if _jumps_inside else _is_if_false
                    _cond_expr = _negate_expr(_expr) if _negate else _expr
                    _return_block = _block_succ_return[0]
                    _return_role = self.region_analyzer.get_block_role(_return_block)
                    if _return_role in (BlockRole.RETURN, BlockRole.RETURN_NONE):
                        _ret_ast = self._generate_return_ast(_return_block)
                        _return_stmts = [_ret_ast] if _ret_ast else [{'type': 'Return', 'value': {'type': 'Constant', 'value': None}}]
                    else:
                        _return_stmts = self._generate_block_statements(_return_block)
                    _return_body = _return_stmts if _return_stmts else [{'type': 'Return', 'value': {'type': 'Constant', 'value': None}}]
                    _hdr_stmts.append({'type': 'If', 'test': _cond_expr, 'body': _return_body})
                    self.generated_blocks.add(_return_block)
                    self.generated_offsets.add(_return_block.start_offset)
                else:
                    # [修复] 精确化break条件的取反逻辑
                    # 当jump_block是break（跳出循环）且跳转由IF_FALSE触发时，
                    # 表示"条件False→break"，即"条件True→执行body"，不应取反
                    # 原始逻辑: _negate = (not _is_if_false) if _jumps_inside else _is_if_false
                    # 问题: 当break在else分支时，_jumps_inside=False导致总是取反
                    _is_jump_to_break = (_jump_block and
                        self.region_analyzer.get_block_role(_jump_block) in (BlockRole.PURE_BREAK, BlockRole.BREAK))
                    _is_jump_to_continue = False
                    if not _is_jump_to_break and _jump_block:
                        _jb_last = _jump_block.get_last_instruction()
                        if (_jb_last and _jb_last.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')
                            and _jb_last.argval is not None):
                            _jt_target = self.cfg.get_block_by_offset(_jb_last.argval)
                            is_while_true_header = (region.is_while_true and block == region.header_block)
                            if _jt_target and _jt_target.loop_header and not is_while_true_header:
                                _is_jump_to_continue = True
                            elif (region.header_block
                                  and _jb_last.argval == region.header_block.start_offset
                                  and not is_while_true_header):
                                _is_jump_to_continue = True
                    if not _is_jump_to_continue and _fall_through:
                        _is_jump_to_continue = self._block_is_continue_target(_fall_through)
                    if _is_jump_to_break and not _is_if_false:
                        # jump_if_true to break: "条件True→break", 需要取反为"条件Not→body"
                        _negate = True
                    elif _is_jump_to_break and _is_if_false:
                        # jump_if_false to break: "条件False→break", 即"条件True→body", 不取反
                        _negate = False
                    elif _is_jump_to_continue:
                        # jump to loop header (continue): 保持原有取反逻辑
                        _negate = _is_if_false
                    elif _jumps_inside:
                        _negate = not _is_if_false
                    else:
                        _negate = _is_if_false
                    _cond_expr = _negate_expr(_expr) if _negate else _expr
                    if _is_jump_to_continue:
                        _hdr_stmts.append({'type': 'If', 'test': _cond_expr, 'body': [{'type': 'Continue'}]})
                    else:
                        _hdr_stmts.append({'type': 'If', 'test': _cond_expr, 'body': [{'type': 'Break'}]})
        for _bs in [s for s in block.successors if s not in _loop_body_set] + _block_succ_break:
            if self.region_analyzer.get_block_role(_bs) in (BlockRole.PURE_BREAK, BlockRole.BREAK):
                self.generated_blocks.add(_bs)
                self.generated_offsets.add(_bs.start_offset)

    def _block_is_continue_target(self, block: BasicBlock) -> bool:
        if block is None:
            return False
        last_instr = block.get_last_instruction()
        if last_instr and last_instr.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT') and last_instr.argval is not None:
            target = self.cfg.get_block_by_offset(last_instr.argval)
            if target and target.loop_header:
                return True
        role = self.region_analyzer.get_block_role(block)
        if role in (BlockRole.CONTINUE, BlockRole.PURE_CONTINUE):
            return True
        return False

    def _loop_handle_no_exit_successors(self, block: BasicBlock, _break_cause: Instruction,
                                        _jump_block, _fall_through,
                                        _hdr_stmts: List[Dict[str, Any]]) -> None:
        """处理无退出后继的header break条件（生成完整if/else）"""
        _cond_instrs: List[Instruction] = []
        for _cinstr in block.instructions:
            if _cinstr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                continue
            if _cinstr.opname in FORWARD_JUMP_OPS:
                break
            _cond_instrs.append(_cinstr)
        _split_idx = -1
        for _ci_i, _ci in enumerate(_cond_instrs):
            if _ci.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                _split_idx = _ci_i
        if _split_idx >= 0:
            _cond_instrs = _cond_instrs[_split_idx + 1:]
        while _cond_instrs and _cond_instrs[-1].opname == 'POP_TOP':
            _cond_instrs.pop()
        if _cond_instrs:
            _expr = self.expr_reconstructor.reconstruct(_cond_instrs)
            if _expr:
                _is_if_false = 'IF_FALSE' in _break_cause.opname
                if _is_if_false:
                    _then_succ = _fall_through
                    _else_succ = _jump_block
                else:
                    _then_succ = _jump_block
                    _else_succ = _fall_through
                _then_is_continue = self._block_is_continue_target(_then_succ)
                _else_is_continue = self._block_is_continue_target(_else_succ)
                if _then_is_continue:
                    _then_stmts = [{'type': 'Continue'}]
                else:
                    _then_stmts = self._generate_block_statements(_then_succ)
                    if not _then_stmts:
                        _then_stmts = [{'type': 'Pass'}]
                if _else_is_continue:
                    _else_stmts = [{'type': 'Continue'}]
                else:
                    _else_stmts = self._generate_block_statements(_else_succ)
                    if not _else_stmts:
                        _else_stmts = [{'type': 'Pass'}]
                self.generated_blocks.add(_then_succ)
                self.generated_offsets.add(_then_succ.start_offset)
                self.generated_blocks.add(_else_succ)
                self.generated_offsets.add(_else_succ.start_offset)
                _hdr_stmts.append({'type': 'If', 'test': _expr, 'body': _then_stmts, 'orelse': _else_stmts})

    def _loop_build_if_with_exit_branches(self, _expr, _is_if_false, _fall_through, _jump_block,
                                          _exit_succs, _block_succ_break, _block_succ_return,
                                          _hdr_stmts: List[Dict[str, Any]]) -> None:
        if _is_if_false:
            _then_succ = _fall_through
            _else_succ = _jump_block
            _negate = False
        else:
            _then_succ = _jump_block
            _else_succ = _fall_through
            _negate = False
        _then_is_exit = _then_succ in _exit_succs
        _else_is_exit = _else_succ in _exit_succs
        if _else_is_exit and not _then_is_exit:
            _then_succ, _else_succ = _else_succ, _then_succ
            _negate = True
        _then_stmts: List[Dict[str, Any]] = []
        _else_stmts: List[Dict[str, Any]] = []
        if _then_succ in _exit_succs:
            if _then_succ in _block_succ_break:
                _then_stmts = [{'type': 'Break'}]
            elif _then_succ in _block_succ_return:
                _then_role = self.region_analyzer.get_block_role(_then_succ)
                if _then_role in (BlockRole.RETURN, BlockRole.RETURN_NONE):
                    _ret_ast = self._generate_return_ast(_then_succ)
                    _then_stmts = [_ret_ast] if _ret_ast else [{'type': 'Return', 'value': {'type': 'Constant', 'value': None}}]
                else:
                    _rs = self._generate_block_statements(_then_succ)
                    _then_stmts = _rs if _rs else [{'type': 'Return', 'value': {'type': 'Constant', 'value': None}}]
                self.generated_blocks.add(_then_succ)
                self.generated_offsets.add(_then_succ.start_offset)
            else:
                _then_stmts = [{'type': 'Break'}]
        else:
            _then_stmts = self._generate_block_statements(_then_succ)
            if not _then_stmts:
                _then_stmts = [{'type': 'Pass'}]
            self.generated_blocks.add(_then_succ)
            self.generated_offsets.add(_then_succ.start_offset)
        if _else_succ and _else_succ not in _exit_succs:
            _then_has_break = any(s.get('type') == 'Break' for s in _then_stmts)
            if _then_has_break:
                pass
            else:
                _else_stmts = self._generate_block_statements(_else_succ)
                if not _else_stmts:
                    _else_stmts = [{'type': 'Pass'}]
                self.generated_blocks.add(_else_succ)
                self.generated_offsets.add(_else_succ.start_offset)
        _cond_expr = _negate_expr(_expr) if _negate else _expr
        if _else_stmts:
            _hdr_stmts.append({'type': 'If', 'test': _cond_expr, 'body': _then_stmts, 'orelse': _else_stmts})
        else:
            _hdr_stmts.append({'type': 'If', 'test': _cond_expr, 'body': _then_stmts})

    def _loop_process_natural_back_edge(self, block: BasicBlock, back_edge_stmts: List[Dict[str, Any]]) -> bool:
        """处理自然回边块（条件重检查），返回是否已处理"""
        _nbe_last = block.get_last_instruction()
        if not (_nbe_last and _nbe_last.opname in BACKWARD_CONDITIONAL_JUMP_OPS):
            return False
        _nbe_has_store = any(i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
                            for i in block.instructions)
        if _nbe_has_store:
            _nbe_cond_start_idx = self._loop_find_cond_start_idx(block)
            if _nbe_cond_start_idx is not None and _nbe_cond_start_idx > 0:
                _nbe_pre_instrs = list(block.instructions[:_nbe_cond_start_idx])
                _nbe_pre_stmts = self._loop_extract_pre_stmts_from_instrs(_nbe_pre_instrs, block)
                if _nbe_pre_stmts:
                    back_edge_stmts.extend(_nbe_pre_stmts)
            self.generated_blocks.add(block)
            self.generated_offsets.add(block.start_offset)
            return True
        _nbe_cond_start_idx = self._loop_find_cond_start_idx(block)
        if _nbe_cond_start_idx is None or _nbe_cond_start_idx <= 0:
            self.generated_blocks.add(block)
            self.generated_offsets.add(block.start_offset)
            return True
        _nbe_pre_instrs = list(block.instructions[:_nbe_cond_start_idx])
        _nbe_pre_stmts = self._loop_extract_pre_stmts_from_instrs(_nbe_pre_instrs, block)
        if _nbe_pre_stmts:
            back_edge_stmts.extend(_nbe_pre_stmts)
        self.generated_blocks.add(block)
        self.generated_offsets.add(block.start_offset)
        return True

    def _loop_find_cond_start_idx(self, block: BasicBlock) -> Optional[int]:
        _nbe_cond_start_idx = None
        _has_store = any(i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF') for i in block.instructions)
        _has_call = any(i.opname in ('CALL', 'PRECALL', 'LOAD_METHOD') for i in block.instructions)
        _needs_extended_trace = _has_store and _has_call
        for _nbci in range(len(block.instructions) - 2, -1, -1):
            _nbc_instr = block.instructions[_nbci]
            if _nbc_instr.opname in ('COMPARE_OP', 'IS_OP', 'CONTAINS_OP'):
                if _needs_extended_trace:
                    _extended_ops = ('LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF',
                                   'LOAD_CONST', 'COPY', 'SWAP', 'TO_BOOL',
                                   'CALL', 'PRECALL', 'LOAD_METHOD',
                                   'BINARY_SUBSCR', 'GET_ITER')
                    for _nbci2 in range(_nbci - 1, -1, -1):
                        if block.instructions[_nbci2].opname not in _extended_ops:
                            break
                        _nbe_cond_start_idx = _nbci2
                else:
                    for _nbci2 in range(_nbci - 1, -1, -1):
                        if block.instructions[_nbci2].opname not in ('LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF', 'LOAD_CONST', 'COPY'):
                            break
                        _nbe_cond_start_idx = _nbci2
                if _nbe_cond_start_idx is None:
                    _nbe_cond_start_idx = _nbci
                return _nbe_cond_start_idx
            if _nbc_instr.opname in NONE_CHECK_OPS:
                return _nbci
        for _nbci in range(len(block.instructions) - 2, -1, -1):
            _nbc_instr = block.instructions[_nbci]
            if _nbc_instr.opname in ('LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF'):
                return _nbci
        return None

    def _loop_extract_pre_stmts_from_instrs(self, instrs: List[Instruction], block: BasicBlock) -> List[Dict[str, Any]]:
        """从指令序列中提取前置语句"""
        _pre_stmts: List[Dict[str, Any]] = []
        _buf: List[Instruction] = []
        for _nbi in instrs:
            if _nbi.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                continue
            if _nbi.opname == 'POP_TOP':
                if _buf:
                    _has_call = any(i.opname in ('CALL', 'CALL_FUNCTION', 'CALL_METHOD',
                                                'CALL_FUNCTION_KW', 'CALL_FUNCTION_EX') for i in _buf)
                    if _has_call:
                        _nbe_stmt = self._build_statement(_buf)
                        if _nbe_stmt:
                            _pre_stmts.append(_nbe_stmt)
                        _buf = []
                continue
            if _nbi.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                _buf.append(_nbi)
                _stmt = self._build_store_statement(_buf, block=block)
                if _stmt:
                    _pre_stmts.append(_stmt)
                _buf = []
                continue
            _buf.append(_nbi)
        if _buf:
            _stmt = self._build_statement(_buf)
            if _stmt:
                _pre_stmts.append(_stmt)
        return _pre_stmts

    def _loop_handle_continue(self, block: BasicBlock, region: LoopRegion,
                              natural_back_edge: BasicBlock,
                              body_blocks_no_header: List[BasicBlock]) -> None:
        in_if_branch = False
        is_if_else_fallthrough = False
        for r in region.iter_descendants((IfRegion,)):
            if block in r.then_blocks:
                in_if_branch = True
                break
            if (not r.else_blocks and r.condition_block
                and block in r.condition_block.successors
                and block not in r.then_blocks):
                is_if_else_fallthrough = True
        if block == natural_back_edge and not in_if_branch:
            body_blocks_no_header.append(block)
            return
        body_blocks_no_header.append(block)

    def _loop_handle_back_edge(self, block: BasicBlock, region: LoopRegion,
                               child_info: Dict[str, Any],
                               body_stmts: List[Dict[str, Any]],
                               body_blocks_no_header: List[BasicBlock],
                               back_edge_stmts: List[Dict[str, Any]],
                               natural_back_edge: BasicBlock) -> None:
        """处理回边块（条件重检查）"""
        _child_region_for_be = None
        for _cr in (region.children or []):
            if isinstance(_cr, (TryExceptRegion, WithRegion)) and hasattr(_cr, 'entry') and _cr.entry == block:
                _child_region_for_be = _cr
                break
        if _child_region_for_be is None:
            _entry_region = self.region_analyzer.get_entry_region_for_block(block)
            if (_entry_region and isinstance(_entry_region, (TryExceptRegion, WithRegion))
                and _entry_region is not region and hasattr(_entry_region, 'entry') and _entry_region.entry == block):
                _child_region_for_be = _entry_region
        if _child_region_for_be is not None and block not in self.generated_blocks:
            _cr_id = id(_child_region_for_be)
            if _cr_id not in self._generated_regions and _cr_id not in self._generating_regions:
                _cr_ast = self._generate_region(_child_region_for_be)
                if _cr_ast:
                    if isinstance(_cr_ast, list):
                        body_stmts.extend(_cr_ast)
                    else:
                        body_stmts.append(_cr_ast)
                for b in _child_region_for_be.blocks:
                    self.generated_blocks.add(b)
                self._generated_regions.add(_cr_id)
            return
        _nested_loop_hdr = None
        for _nlr in region.iter_descendants((LoopRegion,)):
            if _nlr is not region and _nlr.header_block == block:
                _nested_loop_hdr = _nlr
                break
        if _nested_loop_hdr is not None:
            body_blocks_no_header.append(block)
            return
        if block == natural_back_edge and block != region.header_block:
            # Phase 42: 条件跳转fall-through后继检测
            _is_cond_ft = False
            for _pred in block.predecessors:
                if _pred in (region.body_blocks or []) or _pred == region.header_block:
                    _pred_last = _pred.get_last_instruction()
                    if (_pred_last and _pred_last.opname in FORWARD_CONDITIONAL_JUMP_OPS
                            and _pred_last.argval != block.start_offset):
                        _is_cond_ft = True
                        break
            if _is_cond_ft:
                body_blocks_no_header.append(block)
                return
            self._loop_process_back_edge_with_condition(block, region, back_edge_stmts)
            return
        _be_last = block.get_last_instruction()
        if _be_last and _be_last.opname in BACKWARD_CONDITIONAL_JUMP_OPS:
            _be_has_store = any(i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
                                for i in block.instructions)
            if not _be_has_store:
                self.generated_blocks.add(block)
                self.generated_offsets.add(block.start_offset)
                return
        elif _be_last and _be_last.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'):
            # Phase 42: JUMP_BACKWARD分支前驱检测
            _is_jmp_cond_ft = False
            for _jpred in block.predecessors:
                if _jpred in (region.body_blocks or []) or _jpred == region.header_block:
                    _jpred_last = _jpred.get_last_instruction()
                    if (_jpred_last and _jpred_last.opname in FORWARD_CONDITIONAL_JUMP_OPS
                            and _jpred_last.argval != block.start_offset):
                        _is_jmp_cond_ft = True
                        break
            if _is_jmp_cond_ft:
                body_blocks_no_header.append(block)
                return
            _be_meaningful = [i for i in block.instructions
                              if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP')
                              and i.opname not in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')]
            if not _be_meaningful:
                self.generated_blocks.add(block)
                self.generated_offsets.add(block.start_offset)
                return
            if _be_meaningful:
                _be_ft_names = region.metadata.get('for_target_names', set())
                _be_filtered = []
                _be_seen_targets = set()
                for _bei in _be_meaningful:
                    if _bei.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF') and _bei.argval in _be_ft_names:
                        if _bei.argval not in _be_seen_targets:
                            _be_seen_targets.add(_bei.argval)
                        else:
                            _be_filtered.append(_bei)
                            continue
                    _be_filtered.append(_bei)
                _be_stmts = self._generate_stmts_from_instrs(_be_filtered, block)
                if _be_stmts:
                    body_stmts.extend(_be_stmts)
                self.generated_blocks.add(block)
                self.generated_offsets.add(block.start_offset)
                return
        body_blocks_no_header.append(block)

    def _loop_process_back_edge_with_condition(self, block: BasicBlock, region: LoopRegion,
                                               back_edge_stmts: List[Dict[str, Any]]) -> None:
        """处理带回条件的回边块"""
        _be_last = block.get_last_instruction()
        if not (_be_last and _be_last.opname in BACKWARD_CONDITIONAL_JUMP_OPS):
            if _be_last and _be_last.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'):
                _be_meaningful = [i for i in block.instructions
                                  if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP')
                                  and i.opname not in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')]
                if _be_meaningful:
                    _be_ft_names2 = region.metadata.get('for_target_names', set())
                    _be_filtered2 = []
                    _be_seen2 = set()
                    for _bei2 in _be_meaningful:
                        if _bei2.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF') and _bei2.argval in _be_ft_names2:
                            if _bei2.argval not in _be_seen2:
                                _be_seen2.add(_bei2.argval)
                            else:
                                _be_filtered2.append(_bei2)
                                continue
                        _be_filtered2.append(_bei2)
                    _be_stmts2 = self._generate_stmts_from_instrs(_be_filtered2, block)
                    if _be_stmts2:
                        back_edge_stmts.extend(_be_stmts2)
                return
        _be_has_store = any(i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
                            for i in block.instructions)
        if _be_has_store:
            _be_store_idx = -1
            for _bei, _beinstr in enumerate(block.instructions):
                if _beinstr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                    _be_store_idx = _bei
            if _be_store_idx >= 0:
                _be_pre_instrs = list(block.instructions[:_be_store_idx + 1])
                _be_pre_stmts = self._loop_extract_pre_stmts_from_instrs(_be_pre_instrs, block)
                if _be_pre_stmts:
                    back_edge_stmts.extend(_be_pre_stmts)
            self.generated_blocks.add(block)
            self.generated_offsets.add(block.start_offset)
            return
        else:
            _be_cond_start_idx = self._loop_find_cond_start_idx(block)
            if _be_cond_start_idx is not None and _be_cond_start_idx > 0:
                _be_pre_instrs = list(block.instructions[:_be_cond_start_idx])
                _be_pre_stmts = self._loop_extract_pre_stmts_from_instrs(_be_pre_instrs, block)
                if _be_pre_stmts:
                    back_edge_stmts.extend(_be_pre_stmts)
            self.generated_blocks.add(block)
            self.generated_offsets.add(block.start_offset)

    def _loop_handle_break(self, block: BasicBlock, block_role: 'BlockRole',
                           body_blocks_no_header: List[BasicBlock]) -> None:
        if block_role == BlockRole.PURE_BREAK:
            block_meta = self.region_analyzer._block_metadata.get(block.start_offset, {})
            has_reraise = block_meta.get('has_reraise', any(i.opname == 'RERAISE' for i in block.instructions))
            if has_reraise:
                self.generated_blocks.add(block)
                return
        self.generated_blocks.add(block)
        self.generated_offsets.add(block.start_offset)

    def _loop_handle_child_region_entry(self, block: BasicBlock, region: LoopRegion,
                                        child_info: Dict[str, Any],
                                        body_stmts: List[Dict[str, Any]]) -> bool:
        """检查并处理子区域入口块，返回是否已处理"""
        child_if_blocks = child_info['child_if_blocks']
        block_region = self.region_analyzer.get_region_for_block(block)
        entry_region = self.region_analyzer.get_entry_region_for_block(block)
        if entry_region and isinstance(entry_region, WithRegion) and entry_region.entry == block and block not in self.generated_blocks:
            with_id = id(entry_region)
            if with_id not in self._generated_regions and with_id not in self._generating_regions:
                with_ast = self._generate_region(entry_region)
                if with_ast:
                    if isinstance(with_ast, list):
                        body_stmts.extend(with_ast)
                    else:
                        body_stmts.append(with_ast)
                for b in entry_region.blocks:
                    self.generated_blocks.add(b)
                self._generated_regions.add(with_id)
            return True
        if entry_region and isinstance(entry_region, TryExceptRegion) and entry_region.entry == block and block not in self.generated_blocks:
            try_id = id(entry_region)
            if try_id not in self._generated_regions and try_id not in self._generating_regions:
                try_ast = self._generate_region(entry_region)
                if try_ast:
                    if isinstance(try_ast, list):
                        body_stmts.extend(try_ast)
                    else:
                        body_stmts.append(try_ast)
                for b in entry_region.blocks:
                    self.generated_blocks.add(b)
                self._generated_regions.add(try_id)
            return True
        if entry_region and isinstance(entry_region, LoopRegion) and entry_region is not region and block not in self.generated_blocks:
            _region_id = id(entry_region)
            if _region_id not in self._generated_regions and _region_id not in self._generating_regions:
                self._generating_regions.add(_region_id)
                try:
                    _loop_ast = self._generate_region(entry_region)
                finally:
                    self._generating_regions.discard(_region_id)
                if _loop_ast:
                    if isinstance(_loop_ast, list):
                        body_stmts.extend(_loop_ast)
                    else:
                        body_stmts.append(_loop_ast)
                for b in entry_region.blocks:
                    self.generated_blocks.add(b)
                self._generated_regions.add(_region_id)
            return True
        if isinstance(block_region, LoopRegion) and block_region is not region and block_region.header_block == block and block not in self.generated_blocks:
            _region_id = id(block_region)
            if _region_id not in self._generated_regions and _region_id not in self._generating_regions:
                self._generating_regions.add(_region_id)
                try:
                    _loop_ast = self._generate_region(block_region)
                finally:
                    self._generating_regions.discard(_region_id)
                if _loop_ast:
                    if isinstance(_loop_ast, list):
                        body_stmts.extend(_loop_ast)
                    else:
                        body_stmts.append(_loop_ast)
                for b in block_region.blocks:
                    self.generated_blocks.add(b)
                self._generated_regions.add(_region_id)
            return True
        if isinstance(block_region, IfRegion) and block in child_if_blocks:
            return True
        if isinstance(block_region, AssertRegion) and block_region.entry == block:
            ar_id = id(block_region)
            if ar_id not in self._generated_regions and ar_id not in self._generating_regions:
                assert_ast = self._generate_assert(block_region)
                if assert_ast:
                    body_stmts.append(assert_ast)
                for b in block_region.blocks:
                    self.generated_blocks.add(b)
                self._generated_regions.add(ar_id)
            return True
        if not isinstance(block_region, AssertRegion):
            for r in self.region_analyzer.regions:
                if isinstance(r, AssertRegion) and r.entry == block and r is not block_region:
                    ar_id = id(r)
                    if ar_id not in self._generated_regions and ar_id not in self._generating_regions:
                        assert_ast = self._generate_assert(r)
                        if assert_ast:
                            body_stmts.append(assert_ast)
                        for b in r.blocks:
                            self.generated_blocks.add(b)
                        self._generated_regions.add(ar_id)
                    return True
        if isinstance(block_region, TryExceptRegion):
            child_if_for_block = None
            for child in (region.children or []):
                if isinstance(child, IfRegion) and child.condition_block == block:
                    child_if_for_block = child
                    break
            if child_if_for_block:
                if_ast = self._generate_region(child_if_for_block)
                if if_ast:
                    if isinstance(if_ast, list):
                        body_stmts.extend(if_ast)
                    else:
                        body_stmts.append(if_ast)
                for b in child_if_for_block.blocks:
                    self.generated_blocks.add(b)
                return True
            if block == block_region.entry and block not in self.generated_blocks:
                try_id = id(block_region)
                if try_id not in self._generated_regions and try_id not in self._generating_regions:
                    try_ast = self._generate_region(block_region)
                    if try_ast:
                        if isinstance(try_ast, list):
                            body_stmts.extend(try_ast)
                        else:
                            body_stmts.append(try_ast)
                    for b in block_region.blocks:
                        self.generated_blocks.add(b)
                    self._generated_regions.add(try_id)
                return True
        if isinstance(block_region, WithRegion):
            if block == block_region.entry and block not in self.generated_blocks:
                with_id = id(block_region)
                if with_id not in self._generated_regions and with_id not in self._generating_regions:
                    with_ast = self._generate_region(block_region)
                    if with_ast:
                        if isinstance(with_ast, list):
                            body_stmts.extend(with_ast)
                        else:
                            body_stmts.append(with_ast)
                    for b in block_region.blocks:
                        self.generated_blocks.add(b)
                    self._generated_regions.add(with_id)
                return True
        if isinstance(entry_region, AssertRegion) and entry_region.entry == block and block not in self.generated_blocks:
            assert_id = id(entry_region)
            if assert_id not in self._generated_regions and assert_id not in self._generating_regions:
                assert_ast = self._generate_region(entry_region)
                if assert_ast:
                    if isinstance(assert_ast, list):
                        body_stmts.extend(assert_ast)
                    else:
                        body_stmts.append(assert_ast)
                for b in entry_region.blocks:
                    self.generated_blocks.add(b)
                self._generated_regions.add(assert_id)
            return True
        # 反编译逻辑：
        # ==========
        # 循环体中的TernaryRegion和BoolOpRegion是表达式级子区域，
        # 需要在循环体生成时被正确识别并生成对应AST节点（IfExp/BoolOp）。
        # 基于"No More Gotos"区域归约算法的层次化生成原则：
        # - 内层表达式区域应优先于外层语句区域的平坦化处理
        # - 如果block是TernaryRegion/BoolOpRegion的入口，直接调用对应的_generate方法
        #
        # 边界条件：
        # - 由于block_to_region可能将块映射到父区域(如LoopRegion)，需要同时检查region.children
        # - 需要检查已生成标记防止重复生成
        # - 归约符合度：TernaryRegion→IfExp, BoolOpRegion→BoolOp(Expr)
        _expr_child = None
        if entry_region and isinstance(entry_region, (TernaryRegion, BoolOpRegion)) and entry_region.entry == block:
            _expr_child = entry_region
        if _expr_child is None and block_region and isinstance(block_region, (TernaryRegion, BoolOpRegion)) and block_region.entry == block:
            _expr_child = block_region
        if _expr_child is None:
            for _child in (region.children or []):
                if isinstance(_child, (TernaryRegion, BoolOpRegion)) and _child.entry == block:
                    _expr_child = _child
                    break
        if _expr_child and block not in self.generated_blocks:
            expr_region_id = id(_expr_child)
            if expr_region_id not in self._generated_regions and expr_region_id not in self._generating_regions:
                self._generating_regions.add(expr_region_id)
                try:
                    if isinstance(_expr_child, TernaryRegion):
                        expr_ast = self._generate_ternary(_expr_child)
                    else:
                        expr_ast = self._generate_boolop(_expr_child)
                finally:
                    self._generating_regions.discard(expr_region_id)
                if expr_ast:
                    if isinstance(expr_ast, list):
                        body_stmts.extend(expr_ast)
                    else:
                        body_stmts.append(expr_ast)
                for b in _expr_child.blocks:
                    self.generated_blocks.add(b)
                self._generated_regions.add(expr_region_id)
            return True
        return False

    def _loop_postprocess(self, region: LoopRegion, body_stmts: List[Dict[str, Any]],
                          body_blocks_no_header: List[BasicBlock],
                          back_edge_stmts: List[Dict[str, Any]],
                          child_info: Dict[str, Any]) -> None:
        """后处理：生成未处理的子区域、分支语句、回边语句"""
        child_try_regions = child_info['child_try_regions']
        child_with_regions = child_info['child_with_regions']
        for try_region in sorted(child_try_regions, key=lambda r: r.entry.start_offset):
            try_block = try_region.entry
            if try_block in self.generated_blocks:
                continue
            try_id = id(try_region)
            if try_id in self._generated_regions or try_id in self._generating_regions:
                self.generated_blocks.add(try_block)
                continue
            try_ast = self._generate_region(try_region)
            if try_ast:
                if isinstance(try_ast, list):
                    body_stmts.extend(try_ast)
                else:
                    body_stmts.append(try_ast)
            for b in try_region.blocks:
                self.generated_blocks.add(b)
        for with_region in child_with_regions:
            with_block = with_region.entry
            if with_block in self.generated_blocks:
                continue
            with_ast = self._generate_region(with_region)
            if with_ast:
                if isinstance(with_ast, list):
                    body_stmts.extend(with_ast)
                else:
                    body_stmts.append(with_ast)
            break
        branch_stmts = self._if_generate_branch_stmts(body_blocks_no_header)
        if branch_stmts and body_stmts:
            _last_body_type = body_stmts[-1].get('type') if isinstance(body_stmts[-1], dict) else None
            if _last_body_type in ('Try', 'If', 'For', 'While', 'With'):
                while branch_stmts and isinstance(branch_stmts[0], dict) and branch_stmts[0].get('type') == 'Continue':
                    branch_stmts.pop(0)
        body_stmts.extend(branch_stmts)
        body_stmts.extend(back_edge_stmts)


    def _generate_if(self, region: IfRegion) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        生成 if 语句的 AST 表示 - Phase 5 核心生成方法

        ═══════════════════════════════════════════════════════════════════════
        方法调度逻辑（根据 region_type 分流到不同的生成策略）
        ═══════════════════════════════════════════════════════════════════════

        本方法是 IfRegion AST 生成的入口点，负责：
        1. 判断区域类型并分发到对应的生成策略
        2. 处理重复生成防护（避免同一区域被多次生成）
        3. 处理 elif 链中子条件的嵌套关系
        4. 协调 BoolOp 子区域的生成顺序

        ┌──────────────────────────────────────────────────────────────────┐
        │                    _generate_if 调度流程                          │
        ├──────────────────────────────────────────────────────────────────┤
        │                                                                  │
        │   IfRegion                                                      │
        │      │                                                          │
        │      ├─── IF_ELIF_CHAIN ──→ _if_generate_full_elif_chain()     │
        │      │                         │                                │
        │      │                         ▼                                │
        │      │              完整的 if-elif-else 链                     │
        │      │              (递归处理每个 elif 条件)                    │
        │      │                                                          │
        │      ├─── 已生成过？ ──→ 检查 BoolOp 子区域                   │
        │      │                 │                                       │
        │      │                 ├── 有 BoolOp → (已处理，跳过)          │
        │      │                 └── 无 BoolOp → return []               │
        │      │                                                          │
        │      ├─── 是 elif 链的一部分？ ──→ return []                  │
        │      │       (父节点会统一生成)                                 │
        │      │                                                          │
        │      └─── 其他情况 ──→ _if_generate_normal()                  │
        │                            │                                   │
        │                            ▼                                   │
        │                   标准 if/if-else 生成                          │
        │                                                                  │
        └──────────────────────────────────────────────────────────────────┘

        输出 AST 结构（Python ast 模块格式）：
        ─────────────────────────────────
        基础 if:
          {type: 'If', test: <条件>, body: [then_stmts], orelse: None}

        if-else:
          {type: 'If', test: <条件>, body: [then_stmts], orelse: [else_stmts]}

        if-elif-else:
          {type: 'If', test: <cond1>, body: [then1],
           orelse: [{type: 'If', test: <cond2>, body: [then2],
                     orelse: [{type: 'If', ...}, {orelse: [else_stmts]}]}]}

        关键设计决策：
        ───────────────
        1. elif 链通过 orelse 嵌套实现（符合 Python AST 规范）
        2. 空分支用 [{'type': 'Pass'}] 占位
        3. BoolOp 条件在 condition_expr 缓存后直接使用
        4. 链式比较通过 chained_compare_ops 重建 Compare 节点

        Args:
            region: 已识别的 IfRegion 对象，包含条件/分支/合并点信息

        Returns:
            Union[Dict, List[Dict]]: AST 字典或语句列表
                - 成功: If 节点的 dict 或 [pre_stmts, If节点]
                - 空列表: 区域已被生成或属于父 elif 链
        """
        if region.region_type.name == 'IF_ELIF_CHAIN':
            return self._if_generate_full_elif_chain(region)
        if region.entry and region.entry in self.generated_blocks:
            boolop_child = None
            if region.children:
                for c in region.children:
                    if isinstance(c, BoolOpRegion) and c.entry == region.entry:
                        boolop_child = c
                        break
            if boolop_child is None:
                br = self.region_analyzer.get_region_for_block(region.entry)
                if isinstance(br, BoolOpRegion) and br.entry == region.entry:
                    boolop_child = br
            if boolop_child is None:
                return []
        for r in self.regions:
            if r is not region and isinstance(r, IfRegion) and hasattr(r, 'elif_conditions') and r.elif_conditions:
                if region.entry in r.elif_conditions:
                    return []
        return self._if_generate_normal(region)

    def _if_generate_full_elif_chain(self, region: IfRegion) -> Dict[str, Any]:
        """
        生成完整的 if-elif[-else] 链结构

        ═══════════════════════════════════════════════════════════════════════
        算法说明
        ═══════════════════════════════════════════════════════════════════════

        将 IfRegion(IF_ELIF_CHAIN 类型)转换为 Python AST 的嵌套 if-elif 结构。

        处理流程：
        1. 提取外层 if 条件（从 condition_block 的指令序列）
        2. 生成 then 分支语句
        3. 递归生成 elif 链（调用 _if_generate_elif_chain）
        4. 组装成最终的 AST 节点

        elif 链的 AST 构建：
        ─────────────────────
        源码:
            if a > 10:
                a = 10
            elif a > 5:
                a = 5
            else:
                a = 0

        AST 结构:
        If(test=Compare(a,>,10),
           body=[Store(a,10)],
           orelse=[
             If(_is_elif=True,
                test=Compare(a,>,5),
                body=[Store(a,5)],
                orelse=[Store(a,0)])
           ])

        特殊处理：
        - _is_elif 标记：区分 elif 和普通嵌套 if（影响缩进和代码风格）
        - pre_stmts：条件表达式中的副作用语句（如函数调用的 POP_TOP）
        - generated_blocks 跟踪：防止重复生成 elif 条件块

        Args:
            region: IF_ELIF_CHAIN 类型的 IfRegion，包含:
              - condition_block: 外层条件块
              - then_blocks: then 分支块列表
              - elif_conditions: elif 条件块列表
              - elif_bodies: elif 体块列表
              - elif_final_else: final else 块列表（可选）

        Returns:
            Dict: 完整的 if-elif[-else] AST 节点
        """
        cond_block = region.condition_block
        if cond_block is None:
            return {'type': 'Pass'}
        region_id = id(region)
        self._generating_regions.add(region_id)
        pre_stmts, cond_instrs = self._if_extract_cond_instructions(cond_block, region)
        condition = self._if_extract_condition_from_instructions(region, cond_block, cond_instrs)
        if hasattr(region, 'elif_conditions') and region.elif_conditions:
            for ec in region.elif_conditions:
                self.generated_blocks.add(ec)
        then_stmts = self._if_generate_then_branch(region)
        self.generated_blocks.add(cond_block)
        elif_part = self._if_generate_elif_chain(region)
        self._generating_regions.discard(region_id)
        self._generated_regions.add(region_id)

        trailing_return = None
        if not self._current_loop and isinstance(elif_part, list) and len(elif_part) > 0:
            last_elif = elif_part[-1]
            if isinstance(last_elif, dict) and last_elif.get('type') == 'If':
                orelse = last_elif.get('orelse', [])
                if isinstance(orelse, list) and len(orelse) == 1 and isinstance(orelse[0], dict) and orelse[0].get('type') == 'Return':
                    trailing_return = orelse[0]
                    last_elif['orelse'] = []

        result = {'type': 'If', 'test': condition, 'body': then_stmts if then_stmts else [{'type': 'Pass'}], 'orelse': elif_part if isinstance(elif_part, list) else ([elif_part] if elif_part else [])}
        if pre_stmts:
            result = pre_stmts + [result]
        if trailing_return is not None:
            if isinstance(result, list):
                result.append(trailing_return)
            else:
                result = [result, trailing_return]
        return result

    def _build_chained_compare_from_region_data(self, region: IfRegion) -> Optional[Dict[str, Any]]:
        if not region.chained_compare_ops or not region.chained_left_instr:
            return None
        left_ast = self.expr_reconstructor._load_instr_to_ast(region.chained_left_instr)
        comparators = []
        for ci in region.chained_comparator_instrs:
            comparators.append(self.expr_reconstructor._load_instr_to_ast(ci))
        if not comparators:
            return None
        return {
            'type': 'Compare',
            'left': left_ast,
            'ops': list(region.chained_compare_ops),
            'comparators': comparators,
        }

    def _if_extract_cond_instructions(self, cond_block: 'BasicBlock', region: IfRegion) -> Tuple[List[Dict], List]:
        """提取条件块的前置语句和条件指令"""
        pre_stmts, pre_instrs, pre_seen_store, pre_unpack_info, import_pending_store = [], [], False, None, False
        for instr in cond_block.instructions:
            if instr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                continue
            if instr.opname == 'POP_TOP':
                if pre_instrs:
                    has_call = any(i.opname in ('CALL', 'CALL_FUNCTION', 'CALL_METHOD', 'CALL_FUNCTION_KW', 'CALL_FUNCTION_EX') for i in pre_instrs)
                    if has_call:
                        stmt = self._build_statement(pre_instrs)
                        if stmt:
                            pre_stmts.append(stmt)
                        pre_instrs = []
                if import_pending_store:
                    import_pending_store = False
                continue
            if instr.opname in BACKWARD_JUMP_OPS:
                break
            if instr.opname in FORWARD_JUMP_OPS:
                break
            if instr.opname in ('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE'):
                break
            if instr.opname in ('POP_EXCEPT', 'PUSH_EXC_INFO', 'RERAISE', 'WITH_EXCEPT_START', 'CHECK_EXC_MATCH', 'CHECK_EG_MATCH'):
                continue
            if instr.opname == 'IMPORT_NAME':
                import_result = self._process_instruction(instr, cond_block, [])
                if import_result:
                    if isinstance(import_result, list):
                        pre_stmts.extend(import_result)
                    else:
                        pre_stmts.append(import_result)
                pre_instrs = []
                import_pending_store = True
                continue
            if instr.opname == 'IMPORT_FROM':
                import_pending_store = True
                continue
            if instr.opname == 'RAISE_VARARGS':
                exc_expr = None
                if instr.arg >= 1 and pre_instrs:
                    exc_expr = self.expr_reconstructor.reconstruct(pre_instrs)
                pre_instrs = []
                pre_stmts.append({'type': 'Raise', 'exc': exc_expr, 'cause': None})
                continue
            if instr.opname == 'COPY' and instr.arg == COPY_STACK_TOP:
                pre_instrs.append(instr)
                continue
            if instr.opname == 'UNPACK_SEQUENCE':
                val_instrs = [i for i in pre_instrs if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                val = self.expr_reconstructor.reconstruct(val_instrs) if val_instrs else None
                pre_unpack_info = {'value': val, 'targets': [], 'count': instr.arg}
                pre_instrs = []
                continue
            if instr.opname == 'UNPACK_EX':
                val_instrs = [i for i in pre_instrs if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                val = self.expr_reconstructor.reconstruct(val_instrs) if val_instrs else None
                arg = instr.argval
                before, after = arg & 0xFF, (arg >> 8) & 0xFF
                pre_unpack_info = {'value': val, 'targets': [], 'count': before + 1 + after, 'is_starred': True, 'starred_idx': before}
                pre_instrs = []
                continue
            if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                if import_pending_store:
                    pre_instrs = []
                    import_pending_store = False
                    continue
                is_walrus = len(pre_instrs) >= 2 and pre_instrs[-1].opname == 'COPY' and pre_instrs[-1].arg == 1
                if pre_unpack_info is not None:
                    is_starred = pre_unpack_info.get('is_starred', False)
                    starred_idx = pre_unpack_info.get('starred_idx', -1)
                    current_target_idx = len(pre_unpack_info['targets'])
                    if is_starred and current_target_idx == starred_idx:
                        pre_unpack_info['targets'].append({'type': 'Starred', 'value': {'type': 'Name', 'id': instr.argval if instr.argval else f'var_{instr.arg}', 'ctx': 'Store'}})
                    else:
                        pre_unpack_info['targets'].append({'type': 'Name', 'id': instr.argval if instr.argval else f'var_{instr.arg}', 'ctx': 'Store'})
                    if len(pre_unpack_info['targets']) == pre_unpack_info['count']:
                        target = {'type': 'Tuple', 'elts': pre_unpack_info['targets'], 'ctx': 'Store'}
                        if pre_unpack_info['value']:
                            pre_stmts.append({'type': 'Assign', 'targets': [target], 'value': pre_unpack_info['value']})
                        pre_unpack_info = None
                    pre_instrs = []
                    pre_seen_store = True
                    continue
                if is_walrus:
                    pre_instrs.append(instr)
                    pre_seen_store = True
                    continue
                pre_instrs.append(instr)
                stmt = self._build_store_statement(pre_instrs, block=cond_block)
                if stmt:
                    pre_stmts.append(stmt)
                pre_instrs = []
                pre_seen_store = True
                continue
            if instr.opname == 'COMPARE_OP' and pre_seen_store:
                pre_instrs = []
                continue
            pre_instrs.append(instr)
        cond_instrs = []
        prev_was_copy = False
        for instr in cond_block.instructions:
            if instr.opname in ('RESUME', 'NOP', 'CACHE', 'POP_TOP', 'PUSH_NULL'):
                continue
            if (instr.opname in FORWARD_JUMP_OPS or instr.opname in BACKWARD_JUMP_OPS) and instr.opname not in NONE_CHECK_OPS:
                continue
            if instr.opname == 'JUMP_FORWARD' or instr.opname == 'JUMP_BACKWARD':
                continue
            if instr.opname == 'COPY' and instr.arg == COPY_STACK_TOP:
                prev_was_copy = True
                cond_instrs.append(instr)
                if prev_was_copy:
                    cond_instrs.append(instr)
                    prev_was_copy = False
                    continue
                cond_instrs = []
                continue
            prev_was_copy = False
            cond_instrs.append(instr)
        return pre_stmts, cond_instrs

    def _if_generate_then_branch(self, region: IfRegion) -> List[Dict[str, Any]]:
        """生成 then 分支的语句列表"""
        then_stmts = self._process_if_blocks(region.then_blocks, region, branch='then')
        elif_cond_set = set()
        elif_body_block_set = set()
        if hasattr(region, 'elif_conditions') and region.elif_conditions:
            elif_cond_set = set(region.elif_conditions)
        if hasattr(region, 'elif_bodies'):
            for body in region.elif_bodies:
                elif_body_block_set.update(body)
        for child in (region.children or []):
            if not isinstance(child, (TryExceptRegion, WithRegion, LoopRegion, IfRegion)):
                continue
            if not hasattr(child, 'entry') or child.entry is None:
                continue
            if child.entry in self.generated_blocks:
                continue
            if child.entry in elif_cond_set:
                continue
            if elif_body_block_set and child.blocks and any(b in elif_body_block_set for b in child.blocks if hasattr(b, 'start_offset')):
                continue
            child_reachable_from_then = self._is_child_reachable_from_blocks(child, region.then_blocks)
            if not child_reachable_from_then:
                then_offset_min = min((b.start_offset for b in region.then_blocks), default=None)
                then_offset_max = max((b.start_offset for b in region.then_blocks), default=None)
                if then_offset_min is not None and then_offset_max is not None:
                    child_block_offsets = {b.start_offset for b in child.blocks}
                    has_overlap = any(
                        then_offset_min <= bo <= then_offset_max
                        for bo in child_block_offsets
                    )
                    if has_overlap:
                        child_reachable_from_then = True
                child_id = id(child)
                if child_id not in self._generated_regions and child_id not in self._generating_regions:
                    child_ast = self._generate_region(child)
                    if child_ast:
                        if isinstance(child_ast, list):
                            then_stmts.extend(child_ast)
                        else:
                            then_stmts.append(child_ast)
                    for b in child.blocks:
                        self.generated_blocks.add(b)
                    self._generated_regions.add(child_id)
        if not then_stmts:
            then_stmts = [{'type': 'Pass'}]
        return then_stmts

    def _if_generate_else_branch(self, region: IfRegion) -> Optional[List[Dict[str, Any]]]:
        """生成 else 分支的语句列表"""
        if region.elif_conditions:
            return self._if_generate_elif_chain(region)
        if region.chained_compare_blocks and region.else_blocks:
            if self._is_chained_compare_cleanup_else(region):
                return None
        if region.else_blocks:
            else_stmts = self._process_if_blocks(region.else_blocks, region, branch='else')
            for child in (region.children or []):
                if not isinstance(child, (TryExceptRegion, WithRegion)):
                    continue
                if not hasattr(child, 'entry') or child.entry is None:
                    continue
                if child.entry in self.generated_blocks:
                    continue
                child_reachable_from_else = self._is_child_reachable_from_blocks(child, region.else_blocks)
                if child_reachable_from_else:
                    child_id = id(child)
                    if child_id not in self._generated_regions and child_id not in self._generating_regions:
                        child_ast = self._generate_region(child)
                        if child_ast:
                            if isinstance(child_ast, list):
                                else_stmts.extend(child_ast)
                            else:
                                else_stmts.append(child_ast)
                        for b in child.blocks:
                            self.generated_blocks.add(b)
                        self._generated_regions.add(child_id)
            return else_stmts if else_stmts else None
        if region.elif_final_else:
            else_stmts = self._process_if_blocks(region.elif_final_else, region, branch='else')
            return else_stmts if else_stmts else None
        return None

    def _is_chained_compare_cleanup_else(self, region: IfRegion) -> bool:
        if not region.else_blocks:
            return False
        for block in region.else_blocks:
            meaningful_instrs = [i for i in block.instructions
                                 if i.opname not in ('RESUME', 'NOP', 'CACHE', 'COPY')]
            if not meaningful_instrs:
                continue
            is_cleanup = self._is_implicit_return_block(meaningful_instrs)
            if not is_cleanup:
                for instr in meaningful_instrs:
                    if instr.opname not in ('POP_TOP', 'RETURN_VALUE', 'RETURN_CONST',
                                             'JUMP_FORWARD', 'JUMP_BACKWARD',
                                             'POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE',
                                             'POP_JUMP_FORWARD_IF_FALSE',
                                             'POP_JUMP_FORWARD_IF_TRUE',
                                             'POP_JUMP_BACKWARD_IF_FALSE',
                                             'POP_JUMP_BACKWARD_IF_TRUE'):
                        return False
        return True

    def _is_implicit_return_block(self, instrs: list) -> bool:
        filtered = [i for i in instrs if i.opname not in ('POP_TOP',)]
        if len(filtered) == 2:
            if (filtered[0].opname in ('LOAD_CONST',) and
                filtered[1].opname in ('RETURN_VALUE', 'RETURN_CONST') and
                filtered[0].argval is None):
                return True
        return False

    def _if_generate_elif_chain(self, region: IfRegion) -> List[Dict[str, Any]]:
        if not getattr(region, 'elif_conditions', None):
            return [self._if_generate_normal(region)]
        elif_cond_block = region.elif_conditions[0]
        self.generated_blocks.add(elif_cond_block)
        elif_cond_instrs = []
        prev_was_copy = False
        for instr in elif_cond_block.instructions:
            if instr.opname in ('RESUME', 'NOP', 'CACHE', 'POP_TOP', 'PUSH_NULL'):
                continue
            if (instr.opname in FORWARD_JUMP_OPS or instr.opname in BACKWARD_JUMP_OPS) and instr.opname not in NONE_CHECK_OPS:
                continue
            if instr.opname == 'JUMP_FORWARD' or instr.opname == 'JUMP_BACKWARD':
                continue
            if instr.opname == 'COPY' and instr.arg == COPY_STACK_TOP:
                prev_was_copy = True
                elif_cond_instrs.append(instr)
                continue
            if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                if prev_was_copy:
                    elif_cond_instrs.append(instr)
                    prev_was_copy = False
                    continue
                elif_cond_instrs = []
                continue
            prev_was_copy = False
            elif_cond_instrs.append(instr)
        elif_condition = None
        cond_block = region.condition_block
        if region.chained_compare_ops and elif_cond_block == cond_block:
            chained = self._build_chained_compare_from_region_data(region)
            if chained:
                elif_condition = chained
        if elif_condition is None:
            elif_boolop = self.region_analyzer.get_region_for_block(elif_cond_block)
            if not isinstance(elif_boolop, BoolOpRegion):
                elif_boolop = region.find_descendant_region_for_block(elif_cond_block, (BoolOpRegion,))
            if isinstance(elif_boolop, BoolOpRegion):
                self._generate_boolop(elif_boolop)
                if elif_boolop.condition_expr is not None:
                    elif_condition = elif_boolop.condition_expr
        if elif_condition is None and elif_cond_instrs:
            expr2 = self.expr_reconstructor.reconstruct(elif_cond_instrs)
            if expr2:
                elif_negate = False
                elif_last = elif_cond_block.get_last_instruction()
                if elif_last is not None and elif_last.argval is not None:
                    if elif_last.opname in NONE_CHECK_OPS:
                        elif_if_true = False
                    else:
                        elif_if_true = 'IF_TRUE' in elif_last.opname
                    elif_jump_target = elif_last.argval
                    elif_then_offsets = set()
                    if region.elif_bodies and len(region.elif_bodies) > 0:
                        elif_then_offsets = {b.start_offset for b in region.elif_bodies[0]}
                    elif_jumps_to_then = elif_jump_target in elif_then_offsets
                    elif_negate = elif_jumps_to_then != elif_if_true
                elif_condition = _negate_expr(expr2) if elif_negate else expr2
        elif_body_stmts = []
        if region.elif_bodies:
            elif_body_stmts = self._process_if_blocks(region.elif_bodies[0], region, branch='elif')
            elif_body_stmts = [s for s in elif_body_stmts if not (s.get('type') == 'Expr' and isinstance(s.get('value'), dict) and s['value'].get('type') == 'Constant')]
        nested_elif_stmts = None
        if len(region.elif_conditions) > 1:
            remaining_elifs = region.elif_conditions[2:]
            if remaining_elifs:
                nested_chained = []
                if region.chained_compare_blocks:
                    for cc in region.chained_compare_blocks:
                        if cc.start_offset > elif_cond_block.start_offset:
                            nested_chained.append(cc)
                nested_blocks = {region.elif_conditions[1]}
                if len(region.elif_bodies) > 1:
                    nested_blocks.update(region.elif_bodies[1])
                nested_blocks.update(remaining_elifs)
                for body in region.elif_bodies[2:]:
                    nested_blocks.update(body)
                if region.elif_final_else:
                    nested_blocks.update(region.elif_final_else)
                nested_elif = IfRegion(
                    region_type=RegionType.IF_ELIF_CHAIN, entry=region.elif_conditions[1],
                    blocks=nested_blocks, condition_block=region.elif_conditions[1],
                    then_blocks=region.elif_bodies[1] if len(region.elif_bodies) > 1 else [],
                    elif_conditions=remaining_elifs, elif_bodies=region.elif_bodies[2:],
                    elif_final_else=region.elif_final_else, chained_compare_blocks=nested_chained,
                )
                nested_ast = self._generate_region(nested_elif)
                if nested_ast:
                    if isinstance(nested_ast, dict) and nested_ast.get('type') == 'If':
                        nested_ast['_is_elif'] = True
                    elif isinstance(nested_ast, list):
                        for item in nested_ast:
                            if isinstance(item, dict) and item.get('type') == 'If':
                                item['_is_elif'] = True
                    nested_elif_stmts = [nested_ast]
            else:
                last_elif_body_stmts = []
                if len(region.elif_bodies) > 1:
                    last_elif_body_stmts = self._process_if_blocks(region.elif_bodies[1], region, branch='elif')
                    last_elif_body_stmts = [s for s in last_elif_body_stmts if not (s.get('type') == 'Expr' and isinstance(s.get('value'), dict) and s['value'].get('type') == 'Constant')]
                nested_elif_stmts = [{'type': 'If', '_is_elif': True, 'test': self._extract_condition_for_elif_block(region.elif_conditions[1], region), 'body': last_elif_body_stmts if last_elif_body_stmts else [{'type': 'Pass'}], 'orelse': []}]
                if region.elif_final_else:
                    final_else_stmts = self._process_if_blocks(region.elif_final_else, region, branch='else')
                    if final_else_stmts:
                        nested_elif_stmts[0]['orelse'] = final_else_stmts
        final_else_stmts = None
        if not nested_elif_stmts and region.elif_final_else:
            final_else_stmts = self._process_if_blocks(region.elif_final_else, region, branch='else')
        elif_orelse = nested_elif_stmts if nested_elif_stmts else (final_else_stmts if final_else_stmts else [])
        return [{'type': 'If', '_is_elif': True, 'test': elif_condition if elif_condition else {'type': 'Constant', 'value': True}, 'body': elif_body_stmts if elif_body_stmts else [{'type': 'Pass'}], 'orelse': elif_orelse}]

    def _extract_condition_for_elif_block(self, cond_block, region: IfRegion = None):
        cond_instrs = []
        prev_was_copy = False
        for instr in cond_block.instructions:
            if instr.opname in ('RESUME', 'NOP', 'CACHE', 'POP_TOP', 'PUSH_NULL'):
                continue
            if (instr.opname in FORWARD_JUMP_OPS or instr.opname in BACKWARD_JUMP_OPS) and instr.opname not in NONE_CHECK_OPS:
                continue
            if instr.opname == 'JUMP_FORWARD' or instr.opname == 'JUMP_BACKWARD':
                continue
            if instr.opname == 'COPY' and instr.arg == COPY_STACK_TOP:
                prev_was_copy = True
                cond_instrs.append(instr)
                continue
            if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                if prev_was_copy:
                    cond_instrs.append(instr)
                    prev_was_copy = False
                    continue
                cond_instrs = []
                continue
            prev_was_copy = False
            cond_instrs.append(instr)
        if cond_instrs:
            expr = self.expr_reconstructor.reconstruct(cond_instrs)
            if expr:
                negate = False
                last = cond_block.get_last_instruction()
                if last is not None and last.opname in (FORWARD_CONDITIONAL_JUMP_OPS | BACKWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS) and last.argval is not None:
                    if last.opname in NONE_CHECK_OPS:
                        if_true = False
                    else:
                        if_true = 'IF_TRUE' in last.opname
                    then_offsets = set()
                    if region and region.elif_bodies and len(region.elif_bodies) > 0:
                        then_offsets = {b.start_offset for b in region.elif_bodies[0]}
                    negate = (last.argval in then_offsets) != if_true
                return _negate_expr(expr) if negate else expr
        return {'type': 'Constant', 'value': True}

    def _if_generate_normal(self, region: IfRegion) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """生成标准 if/if-else AST 节点（非 elif 链、非三元表达式）
        
        Phase 5 文档 - 处理 IF_THEN 和 IF_THEN_ELSE 类型的 IfRegion
        
        生成步骤:
        1. 安全检查：condition_block 为空返回 Pass
        2. With 冲突排除（所有块都是 with-handler 时跳过）
        3. 区域状态管理（_generating_regions 防止递归）
        4. 条件提取（三级回退：BoolOp缓存 → 链式比较 → 通用重建）
        5. 分支生成（then + else）
        6. AST 组装与前置语句拼接
        
        条件表达式重建优先级:
        - P0: BoolOpRegion.condition_expr 缓存（and/or 树）
        - P1: chained_compare_blocks（a < b < c 链式比较）
        - P2: expr_reconstructor.reconstruct() 通用重建
        
        取反逻辑: negate = (jump_target_in_then) != (opname_contains_TRUE)
        """
        cond_block = region.condition_block
        if cond_block is None:
            return {'type': 'Pass'}
        if all(self.region_analyzer.get_block_role(b) in (BlockRole.WITH_HANDLER, BlockRole.WITH_EXIT_CLEANUP) for b in region.blocks):
            for block in region.blocks:
                self.generated_blocks.add(block)
            return []
        region_id = id(region)
        self._generating_regions.add(region_id)
        pre_stmts, cond_instrs = self._if_extract_cond_instructions(cond_block, region)
        condition = self._if_extract_condition_from_instructions(region, cond_block, cond_instrs)
        self.generated_blocks.add(cond_block)
        if hasattr(region, 'elif_conditions') and region.elif_conditions:
            for elif_cond in region.elif_conditions:
                self.generated_blocks.add(elif_cond)
        then_stmts = self._if_generate_then_branch(region)
        else_stmts = self._if_generate_else_branch(region)
        result = {'type': 'If', 'test': condition, 'body': then_stmts, 'orelse': else_stmts if else_stmts else None}
        self._generating_regions.discard(region_id)
        self._generated_regions.add(region_id)
        if_result = result
        if pre_stmts:
            if_result = pre_stmts + [if_result]
        return if_result

    def _if_extract_condition_from_instructions(self, region: IfRegion, cond_block: 'BasicBlock', cond_instrs: List) -> Dict[str, Any]:
        boolop_region_for_cond = self.region_analyzer.get_region_for_block(cond_block)
        if not isinstance(boolop_region_for_cond, BoolOpRegion):
            boolop_region_for_cond = region.find_descendant_region_for_block(cond_block, (BoolOpRegion,))
        if isinstance(boolop_region_for_cond, BoolOpRegion):
            if boolop_region_for_cond.condition_expr is not None:
                return boolop_region_for_cond.condition_expr
            boolop_expr = self._build_boolop_expression(boolop_region_for_cond)
            if boolop_expr:
                _boolop_negate = False
                _last_cb = boolop_region_for_cond.op_chain[-1][0] if boolop_region_for_cond.op_chain else None
                if _last_cb:
                    _last_ci = _last_cb.get_last_instruction()
                    if _last_ci and _last_ci.argval is not None and _last_ci.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                        if 'TRUE' in _last_ci.opname or 'NONE' in _last_ci.opname:
                            _boolop_negate = True
                if _boolop_negate:
                    boolop_expr = _negate_expr(boolop_expr)
                boolop_region_for_cond.condition_expr = boolop_expr
                for b in boolop_region_for_cond.blocks:
                    self.generated_blocks.add(b)
                return boolop_expr
        if region.chained_compare_blocks and region.chained_compare_ops:
            compare_expr = self._build_chained_compare_from_region_data(region)
            if compare_expr is not None:
                for cb in region.chained_compare_blocks:
                    self.generated_blocks.add(cb)
                negate = False
                last = cond_block.get_last_instruction()
                if last is not None:
                    if last.opname in NONE_CHECK_OPS:
                        if_true = False
                    else:
                        if_true = 'IF_TRUE' in last.opname
                    jump_target = last.argval
                    if jump_target is not None:
                        then_start_offsets = {b.start_offset for b in region.then_blocks}
                        jumps_to_then = jump_target in then_start_offsets
                        negate = jumps_to_then != if_true
                return _negate_expr(compare_expr) if negate else compare_expr
        if cond_instrs:
            expr = self.expr_reconstructor.reconstruct(cond_instrs)
            if expr:
                expr = self.comp_generator.convert_comprehension_objects(expr, cond_block)
                negate = False
                last2 = cond_block.get_last_instruction()
                if last2 is not None and last2.opname in (FORWARD_CONDITIONAL_JUMP_OPS | BACKWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS):
                    if last2.opname in NONE_CHECK_OPS:
                        if_true2 = False
                    else:
                        if_true2 = 'IF_TRUE' in last2.opname
                    jump_target2 = last2.argval
                    if jump_target2 is not None:
                        then_start_offsets2 = {b.start_offset for b in region.then_blocks}
                        jumps_to_then2 = jump_target2 in then_start_offsets2
                        negate = jumps_to_then2 != if_true2
                return _negate_expr(expr) if negate else expr
        return {'type': 'Constant', 'value': True}

    def _process_if_blocks(self, blocks, region: IfRegion, branch: str = 'then') -> List[Dict[str, Any]]:
        """处理 if/else 分支的块列表"""
        stmts: List[Dict[str, Any]] = []
        child_region_blocks = set()
        child_entries = set()
        if region and hasattr(region, 'children'):
            for child in getattr(region, 'children', []):
                if isinstance(child, (LoopRegion, TryExceptRegion, WithRegion, MatchRegion)):
                    child_region_blocks.update(child.blocks)
                    if child.entry:
                        child_entries.add(child.entry)
        for block in sorted(blocks, key=lambda b: b.start_offset):
            if block in self.generated_blocks:
                continue
            if block in child_region_blocks and block not in child_entries:
                continue
            if hasattr(region, 'region_type') and hasattr(region.region_type, 'name') and 'IF' in region.region_type.name and branch == 'then':
                has_return = any(i.opname in ('RETURN_VALUE', 'RETURN_CONST') for i in block.instructions)
                if has_return and len(block.predecessors) > 1:
                    continue
                if len(block.predecessors) > 1 and block not in (getattr(region, 'then_blocks', []) or []):
                    if any(i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL') for i in block.instructions):
                        continue
            if stmts and stmts[-1].get('type') in ('Break', 'Continue', 'Return', 'Raise'):
                if self._current_loop and block not in self._post_break_blocks:
                    self._post_break_blocks.append(block)
                continue
            role = self.region_analyzer.get_block_role(block)
            if role in (BlockRole.BREAK, BlockRole.PURE_BREAK):
                _block_has_return = any(
                    i.opname in ('RETURN_VALUE', 'RETURN_CONST')
                    for i in block.instructions
                )
                if _block_has_return:
                    _ret_ast = self._generate_return_ast(block)
                    if _ret_ast:
                        stmts.append(_ret_ast)
                    else:
                        stmts.append({'type': 'Break'})
                else:
                    stmts.append({'type': 'Break'})
                self.generated_blocks.add(block)
                self.generated_offsets.add(block.start_offset)
                continue
            if role in (BlockRole.CONTINUE, BlockRole.PURE_CONTINUE):
                _meaningful_instrs = [
                    i for i in block.instructions
                    if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP')
                    and i.opname not in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT',
                                        'JUMP_FORWARD', 'JUMP_ABSOLUTE')
                    and i.opname not in ('POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                                        'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE')
                    and i.opname not in ('JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP')
                ]
                if _meaningful_instrs:
                    bs = self._generate_block_statements(block)
                    if bs:
                        stmts.extend(bs)
                    self.generated_blocks.add(block)
                    self.generated_offsets.add(block.start_offset)
                    continue
                stmts.append({'type': 'Continue'})
                self.generated_blocks.add(block)
                self.generated_offsets.add(block.start_offset)
                continue
            if role == BlockRole.LOOP_BODY and self._current_loop:
                nested_assert = self.region_analyzer.get_entry_region_for_block(block)
                if not isinstance(nested_assert, AssertRegion):
                    br = self.region_analyzer.get_region_for_block(block)
                    if isinstance(br, AssertRegion) and br.entry == block:
                        nested_assert = br
                if isinstance(nested_assert, AssertRegion):
                    nid = id(nested_assert)
                    if nid not in self._generated_regions and nid not in self._generating_regions:
                        assert_ast = self._generate_assert(nested_assert)
                        if assert_ast:
                            stmts.append(assert_ast)
                        for b in nested_assert.blocks:
                            self.generated_blocks.add(b)
                        self._generated_regions.add(nid)
                    continue
                cond_break = self._try_generate_conditional_break(block)
                if cond_break is not None:
                    stmts.extend(cond_break)
                    continue
            if self._current_loop and block in (self._current_loop.body_blocks or []) and role != BlockRole.LOOP_BODY:
                last_ib = block.get_last_instruction()
                if last_ib and last_ib.opname in ('POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE'):
                    cb_result = self._try_generate_conditional_break_or_continue(block)
                    if cb_result is not None:
                        stmts.extend(cb_result)
                        continue
            effective = self.region_analyzer.effective_instructions.get(block.start_offset)
            if role == BlockRole.LOOP_BACK_EDGE and effective is not None:
                if effective:
                    stmts.extend(self._build_effective_stmts(block, effective))
                else:
                    bs = self._generate_block_statements(block)
                    if bs:
                        stmts.extend(bs)
                self.generated_blocks.add(block)
                continue
            nested = self.region_analyzer.get_entry_region_for_block(block)
            if nested and isinstance(nested, (IfRegion, LoopRegion, TryExceptRegion, WithRegion, MatchRegion, AssertRegion, TernaryRegion, BoolOpRegion)):
                """
                【反编译逻辑】Ternary/BoolOp 子区域处理算法（Phase 35 扩展）
                
                ═══════════════════════════════════════════════════════════════════════════════
                1. 功能说明:
                ─────────────────────
                本代码段处理 if/elif/else 分支中嵌入的表达式级子区域，包括：
                - TernaryRegion: 三元表达式（x if cond else y）
                - BoolOpRegion: 布尔运算表达式（a and b or c）
                
                这些子区域在 region_analyzer 阶段已被识别并关联到对应的块，
                但在 AST 生成阶段需要特殊处理以正确嵌套到 if 分支结构中。
                
                2. 归约顺序与层次关系:
                ────────────────────────────────
                **识别顺序**（region_analyzer阶段）:
                Phase 1: Try → Loop → With → Match → Assert（底层结构）
                Phase 2: ChainedCompare → BoolOp → Ternary → If（高层结构）
                
                **生成顺序**（region_ast_generator阶段）:
                外层区域（IfRegion）先开始生成 → 遇到子区域块时暂停 → 
                递归生成子区域 → 将结果插入当前位置 → 继续外层生成
                
                **层次结构示例**:
                ```python
                # 源码:
                if condition:
                    result = x if a else b  # TernaryRegion 嵌套在 IfRegion 的 then 体中
                    flag = p and q          # BoolOpRegion 嵌套在 IfRegion 的 then 体中
                
                # 区域树:
                IfRegion (condition_block=cond)
                ├── then_blocks=[block1, block2, block3]
                │   ├── block1: 普通语句 "result = ..."
                │   ├── block2: TernaryRegion.entry (x if a else b)
                │   └── block3: BoolOpRegion.entry (p and q)
                └── else_blocks=[]
                
                # AST生成过程:
                _generate_if(region):
                  → 遍历 then_blocks
                  → block1: 生成赋值语句
                  → block2: 检测到 TernaryRegion → 调用 _generate_ternary()
                            → 返回 ast.IfExp(test=a, body=x, orelse=b)
                            → 包装为 Expr(stmt) 加入 stmts 列表
                  → block3: 检测到 BoolOpRegion → 调用 _generate_boolop()
                            → 返回 ast.BoolOp(op=And(), values=[p, q])
                            → 包装为 Expr(stmt) 加入 stmts 列表
                ```
                
                3. 处理逻辑详解:
                ────────────────────────────────
                ```python
                if isinstance(nested, (TernaryRegion, BoolOpRegion)):
                    child_id = id(nested)  # 使用对象ID作为唯一标识
                    
                    # 防止重复生成检查
                    if child_id not in self._generated_regions and \
                       child_id not in self._generating_regions:
                        
                        # 根据类型调用相应的生成器
                        if isinstance(nested, TernaryRegion):
                            child_ast = self._generate_ternary(nested)
                            # 生成 ast.IfExp 节点
                        else:
                            child_ast = self._generate_boolop(nested)
                            # 生成 ast.BoolOp 节点
                        
                        if child_ast:
                            # 将生成的AST插入到当前语句列表
                            if isinstance(child_ast, list):
                                stmts.extend(child_ast)  # 多个语句（罕见情况）
                            else:
                                stmts.append(child_ast)  # 单个表达式节点
                        
                        # 标记所有属于该子区域的块为已生成
                        for b in nested.blocks:
                            self.generated_blocks.add(b)
                        
                        # 记录已完成的区域
                        self._generated_regions.add(child_id)
                    
                    continue  # 跳过后续的普通块处理
                ```
                
                4. AST映射规则:
                ─────────────────────
                ┌────────────────┬─────────────────────┬────────────────────────────────┐
                │ 子区域类型       │ AST节点类型          │ 示例                          │
                ├────────────────┼─────────────────────┼────────────────────────────────┤
                │ TernaryRegion   │ ast.IfExp           │ x if cond else y              │
                │ BoolOpRegion   │ ast.BoolOp          │ a and b or c                  │
                └────────────────┴─────────────────────┴────────────────────────────────┘
                
                **包装规则**:
                - 表达式级区域必须包装为 ast.Expr(stmt) 才能作为语句使用
                - 如果子区域返回的是列表（多个语句），直接extend到stmts
                
                5. 防止循环和重复机制:
                ────────────────────────────────
                - `_generated_regions`: 已完成生成的区域ID集合
                - `_generating_regions`: 正在生成中的区域ID集合（防止递归循环）
                - 通过对象ID（id()）而非对象本身作为键，避免哈希问题
                
                6. 与其他子区域的协调:
                ────────────────────────────────
                **优先级**: TernaryRegion/BoolOpRegion > AssertRegion > LoopRegion > 其他
                
                **原因**: 表达式级区域应该最先被"消费"，避免被外层逻辑误处理。
                
                **后续处理**: AssertRegion 在紧接着的代码段中处理（L4694-4703）
                
                7. 典型应用场景:
                ─────────────────────
                - ✅ if条件中的复杂布尔表达式: `if (a and b) or c:`
                - ✅ if分支中的三元赋值: `x = 1 if flag else 0`
                - ✅ elif分支中的混合模式: `elif (x > 0 and y < 10) or z == 5:`
                - ✅ else分支中的表达式: `else: result = a or b or c`
                
                8. 已知限制:
                ─────────────────────
                - ❌ 深度嵌套（>3层）可能导致可读性下降
                - ⚠️ 子区域与父if块的边界模糊时可能遗漏
                - 🔮 未来改进: 支持更复杂的表达式组合模式
                
                ═══════════════════════════════════════════════════════════════════════════════
                """
                # 反编译逻辑：处理if分支中的TernaryRegion/BoolOpRegion子区域
                # 根因：三元表达式和布尔表达式可以嵌入if/else分支的任何位置
                # 归约顺序：内层（ternary/boolop）先识别、外层（if）后处理
                # 符合度：TernaryRegion→IfExp(Expr), BoolOpRegion→BoolOp(Expr)
                if isinstance(nested, (TernaryRegion, BoolOpRegion)):
                    child_id = id(nested)
                    if child_id not in self._generated_regions and child_id not in self._generating_regions:
                        if isinstance(nested, TernaryRegion):
                            child_ast = self._generate_ternary(nested)
                        else:
                            child_ast = self._generate_boolop(nested)
                        if child_ast:
                            if isinstance(child_ast, list):
                                stmts.extend(child_ast)
                            else:
                                stmts.append(child_ast)
                        for b in nested.blocks:
                            self.generated_blocks.add(b)
                        self._generated_regions.add(child_id)
                    continue
                if isinstance(nested, AssertRegion):
                    nid = id(nested)
                    if nid not in self._generated_regions and nid not in self._generating_regions:
                        assert_ast = self._generate_assert(nested)
                        if assert_ast:
                            stmts.append(assert_ast)
                        for b in nested.blocks:
                            self.generated_blocks.add(b)
                        self._generated_regions.add(nid)
                    continue
                # P0防护：跳过与父循环共享condition_block的冗余子LoopRegion
                if isinstance(nested, LoopRegion) and self._current_loop and nested is not self._current_loop:
                    if (nested.condition_block and self._current_loop.condition_block and
                        nested.condition_block.start_offset == self._current_loop.condition_block.start_offset):
                        block_role = self.region_analyzer.get_block_role(block)
                        if block_role in (BlockRole.CONTINUE, BlockRole.PURE_CONTINUE):
                            stmts.append({'type': 'Continue'})
                            self.generated_blocks.add(block)
                            self.generated_offsets.add(block.start_offset)
                            continue
                        bs = self._generate_block_statements(block)
                        if bs:
                            stmts.extend(bs)
                        self.generated_blocks.add(block)
                        continue
                nid = id(nested)
                if nid not in self._generated_regions and nid not in self._generating_regions:
                    na = self._generate_region(nested)
                    if na:
                        (stmts.append if isinstance(na, dict) else stmts.extend)(na)
                    for b in nested.blocks:
                        self.generated_blocks.add(b)
                    continue
            bs = self._generate_block_statements(block)
            if bs:
                last_bs = bs[-1]
                if isinstance(last_bs, dict) and last_bs.get('type') == 'Expr' and any(
                    self.region_analyzer.get_block_role(s) in (BlockRole.RETURN, BlockRole.RETURN_NONE) for s in block.successors):
                    if self._try_depth <= 0:
                        bs[-1] = {'type': 'Return', 'value': last_bs['value']}
                stmts.extend(bs)
            self.generated_blocks.add(block)
        return stmts

    def _try_generate_conditional_break(self, block: BasicBlock) -> Optional[List[Dict[str, Any]]]:
        result = self._try_generate_conditional_break_or_continue(block)
        if result is not None:
            return result
        loop = self._current_loop
        if loop is None:
            return None
        last_instr = block.get_last_instruction()
        if last_instr is None:
            return None
        if last_instr.opname not in FORWARD_CONDITIONAL_JUMP_OPS and last_instr.opname not in BACKWARD_CONDITIONAL_JUMP_OPS:
            return None
        if last_instr.argval is None:
            return None
        loop_body_set = loop.metadata.get('loop_body_full_set', set(loop.body_blocks) | {loop.header_block})
        if loop.condition_block:
            loop_body_set.add(loop.condition_block)
        jump_target = self.cfg.get_block_by_offset(last_instr.argval)
        fall_through = None
        for s in block.successors:
            if s != jump_target:
                fall_through = s
                break
        exit_succ = None
        continue_succ = None
        if jump_target and jump_target not in loop_body_set:
            exit_succ = jump_target
            if fall_through and fall_through in loop_body_set:
                continue_succ = fall_through
        elif fall_through and fall_through not in loop_body_set:
            exit_succ = fall_through
            if jump_target and jump_target in loop_body_set:
                continue_succ = jump_target
        if exit_succ is None:
            return None
        pre_stmts = []
        cond_instrs = []
        seen_store = False
        for instr in block.instructions:
            if instr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                continue
            if instr.opname in FORWARD_JUMP_OPS or instr.opname in BACKWARD_JUMP_OPS:
                break
            if instr.opname in ('POP_EXCEPT', 'PUSH_EXC_INFO', 'RERAISE',
                                'WITH_EXCEPT_START', 'CHECK_EXC_MATCH', 'CHECK_EG_MATCH'):
                continue
            if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                stmt = self._build_store_statement(cond_instrs + [instr], block=block)
                if stmt:
                    pre_stmts.append(stmt)
                cond_instrs = []
                seen_store = True
                continue
            if instr.opname == 'POP_TOP' and cond_instrs:
                stmt = self._build_statement(cond_instrs)
                if stmt:
                    pre_stmts.append(stmt)
                cond_instrs = []
                continue
            if instr.opname == 'COMPARE_OP' and seen_store:
                next_idx = block.instructions.index(instr) + 1
                next_i = block.instructions[next_idx] if next_idx < len(block.instructions) else None
                if next_i and next_i.opname in CONDITIONAL_JUMP_OPS:
                    cond_instrs.append(instr)
                    continue
            cond_instrs.append(instr)
        if not cond_instrs:
            self.generated_blocks.add(block)
            return pre_stmts if pre_stmts else None
        expr = self.expr_reconstructor.reconstruct(cond_instrs)
        if expr is None:
            self.generated_blocks.add(block)
            return pre_stmts if pre_stmts else None
        is_if_false = 'IF_FALSE' in last_instr.opname
        if exit_succ == jump_target:
            cond_expr = _negate_expr(expr) if is_if_false else expr
        else:
            cond_expr = expr if is_if_false else _negate_expr(expr)
        exit_role = self.region_analyzer.get_block_role(exit_succ)
        if exit_role in (BlockRole.RETURN, BlockRole.RETURN_NONE) and exit_succ in loop_body_set:
            ret_stmts = self._generate_block_statements(exit_succ)
            body_stmts = ret_stmts if ret_stmts else [{'type': 'Return', 'value': {'type': 'Constant', 'value': None}}]
            self.generated_blocks.add(exit_succ)
        else:
            _exit_has_return = any(i.opname in ('RETURN_VALUE', 'RETURN_CONST') for i in exit_succ.instructions)
            _ret_val = None
            if _exit_has_return:
                _exit_meaningful = [i for i in exit_succ.instructions
                                   if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                if _exit_meaningful and _exit_meaningful[0].opname in ('LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF'):
                    _ret_val = {'type': 'Name', 'id': _exit_meaningful[0].argval, 'ctx': 'Load'}
                elif _exit_meaningful and _exit_meaningful[0].opname == 'LOAD_CONST':
                    _ret_val = {'type': 'Constant', 'value': _exit_meaningful[0].argval}
            if _ret_val is not None:
                body_stmts = [{'type': 'Return', 'value': _ret_val}]
                self.generated_blocks.add(exit_succ)
            else:
                body_stmts = [{'type': 'Break'}]
                self.generated_blocks.add(exit_succ)
        if_stmt = {'type': 'If', 'test': cond_expr, 'body': body_stmts}
        self.generated_blocks.add(block)
        self.generated_offsets.add(block.start_offset)
        result = pre_stmts + [if_stmt] if pre_stmts else [if_stmt]
        return result

    def _try_generate_conditional_break_or_continue(self, block: BasicBlock) -> Optional[List[Dict[str, Any]]]:
        loop = self._current_loop
        if loop is None:
            return None
        if block == loop.condition_block or block == loop.header_block:
            return None
        last_instr = block.get_last_instruction()
        if last_instr is None:
            return None
        if last_instr.opname not in FORWARD_CONDITIONAL_JUMP_OPS and last_instr.opname not in BACKWARD_CONDITIONAL_JUMP_OPS:
            return None
        if last_instr.argval is None:
            return None
        loop_body_set = loop.metadata.get('loop_body_full_set', set(loop.body_blocks) | {loop.header_block})
        if loop.condition_block:
            loop_body_set.add(loop.condition_block)
        jump_target = self.cfg.get_block_by_offset(last_instr.argval)
        fall_through = None
        for s in block.successors:
            if s != jump_target:
                fall_through = s
                break
        if jump_target is None and fall_through is None:
            return None

        def _is_continue_like(b):
            if b is None:
                return False
            # Phase 43前置: LOOP_BACK_EDGE含meaningful instrs→非continue-like
            _lr = self.region_analyzer.get_block_role(b)
            if _lr == BlockRole.LOOP_BACK_EDGE:
                _lnj = [i for i in b.instructions
                       if i.opname not in NOISE_OPS
                       and i.opname not in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT',
                                            'JUMP_FORWARD', 'JUMP_ABSOLUTE')
                       and i.opname not in CONDITIONAL_JUMP_OPS
                       and i.opname not in SHORT_CIRCUIT_JUMP_OPS]
                if _lnj:
                    return False
            role = self.region_analyzer.get_block_role(b)
            if role in (BlockRole.PURE_CONTINUE, BlockRole.LOOP_BACK_EDGE):
                return True
            if role == BlockRole.CONTINUE:
                non_jump = [i for i in b.instructions
                           if i.opname not in NOISE_OPS
                           and i.opname not in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT',
                                                'JUMP_FORWARD', 'JUMP_ABSOLUTE')
                           and i.opname not in CONDITIONAL_JUMP_OPS
                           and i.opname not in SHORT_CIRCUIT_JUMP_OPS]
                if not non_jump:
                    return True
                return False
            return False

        def _is_break_like(b):
            if b is None:
                return False
            role = self.region_analyzer.get_block_role(b)
            if role in (BlockRole.BREAK, BlockRole.PURE_BREAK):
                return True
            if role in (BlockRole.RETURN, BlockRole.RETURN_NONE):
                return False
            if role in (BlockRole.LOOP_ELSE,):
                last = b.get_last_instruction()
                if (last and last.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')
                        and last.argval is not None
                        and loop.header_block is not None
                        and self.cfg.get_block_by_offset(last.argval) == loop.header_block):
                    return False
            if b not in loop_body_set:
                last_instr = b.get_last_instruction()
                if last_instr:
                    if last_instr.opname == 'RETURN_CONST' and last_instr.argval is not None:
                        return False
                    if last_instr.opname == 'RETURN_VALUE':
                        for _ri in reversed(b.instructions):
                            if _ri == last_instr:
                                continue
                            if _ri.opname == 'LOAD_FAST' or (_ri.opname == 'LOAD_CONST' and _ri.argval is not None):
                                return False
                            if _ri.opname not in ('NOP', 'CACHE', 'POP_TOP'):
                                break
                return True
            return False

        continue_succ = None
        break_succ = None
        normal_succ = None
        for succ, is_jump_target in [(jump_target, True), (fall_through, False)]:
            if succ is None:
                continue
            if _is_continue_like(succ):
                continue_succ = (succ, is_jump_target)
            elif _is_break_like(succ):
                break_succ = (succ, is_jump_target)
            else:
                normal_succ = (succ, is_jump_target)

        target_succ = None
        body_type = None
        if continue_succ and normal_succ:
            _norm = normal_succ[0]
            _is_simple_if = False
            _should_skip_transform = False
            _norm_last = _norm.get_last_instruction()
            _norm_is_backedge_recheck = (_norm_last is not None and
                _norm_last.opname in ('POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE'))
            if _norm not in (loop.back_edge_block, loop.header_block) and not _norm_is_backedge_recheck:
                _has_post_if_stmts = False
                _exit_roles = (BlockRole.RETURN, BlockRole.RETURN_NONE, BlockRole.PURE_JUMP)
                for _nsucc in _norm.successors:
                    if _nsucc != continue_succ[0] and _nsucc != loop.back_edge_block:
                        _nsucc_role = self.region_analyzer.get_block_role(_nsucc)
                        if _nsucc_role in _exit_roles:
                            continue
                        _nsucc_last = _nsucc.get_last_instruction()
                        if (_nsucc_last is not None and
                            _nsucc_last.opname in ('POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE')):
                            continue
                        if _nsucc not in loop_body_set or _nsucc.start_offset > block.start_offset:
                            _has_post_if_stmts = True
                            break
                if not _has_post_if_stmts:
                    _norm_is_control_flow = (
                        _norm_last is not None and
                        _norm_last.opname in FORWARD_CONDITIONAL_JUMP_OPS
                    )
                    if _norm_is_control_flow:
                        pass
                    else:
                        _is_simple_if = True
                else:
                    _should_skip_transform = True
            if _is_simple_if and not _norm_is_backedge_recheck:
                pre_stmts = []
                cond_instrs = []
                for instr in block.instructions:
                    if instr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                        continue
                    if instr.opname in FORWARD_JUMP_OPS or instr.opname in BACKWARD_JUMP_OPS:
                        break
                    if instr.opname in ('POP_EXCEPT', 'PUSH_EXC_INFO', 'RERAISE',
                                        'WITH_EXCEPT_START', 'CHECK_EXC_MATCH', 'CHECK_EG_MATCH'):
                        continue
                    if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                        stmt = self._build_store_statement(cond_instrs + [instr], block=block)
                        if stmt:
                            pre_stmts.append(stmt)
                        cond_instrs = []
                        continue
                    if instr.opname == 'POP_TOP' and cond_instrs:
                        stmt = self._build_statement(cond_instrs)
                        if stmt:
                            pre_stmts.append(stmt)
                        cond_instrs = []
                        continue
                    cond_instrs.append(instr)
                if not cond_instrs:
                    self.generated_blocks.add(block)
                    return pre_stmts if pre_stmts else None
                expr = self.expr_reconstructor.reconstruct(cond_instrs)
                if expr is None:
                    self.generated_blocks.add(block)
                    return pre_stmts if pre_stmts else None
                is_if_false = 'IF_FALSE' in last_instr.opname
                cond_expr = expr
                # Phase 42: IF_TRUE/IF_FALSE四组合then/else映射
                _norm_is_jump = normal_succ[1]
                _then_block = normal_succ[0]
                _else_block = None
                if is_if_false and _norm_is_jump:
                    _then_block = continue_succ[0]
                    _else_block = normal_succ[0]
                elif not is_if_false and _norm_is_jump:
                    _then_block = normal_succ[0]
                    _else_block = continue_succ[0]
                elif is_if_false and not _norm_is_jump:
                    _else_block = normal_succ[0]
                    _then_block = continue_succ[0]
                else:
                    _then_block = normal_succ[0]
                    _else_block = continue_succ[0]
                _then_role = self.region_analyzer.get_block_role(_then_block)
                if _then_role in (BlockRole.RETURN, BlockRole.RETURN_NONE):
                    _ret_ast = self._generate_return_ast(_then_block)
                    _then_stmts = [_ret_ast] if _ret_ast else [{'type': 'Return', 'value': {'type': 'Constant', 'value': None}}]
                    if _then_block not in self.generated_blocks:
                        self.generated_blocks.add(_then_block)
                elif _then_block not in self.generated_blocks:
                    _then_stmts = self._generate_block_statements(_then_block)
                    if _then_block not in self.generated_blocks:
                        self.generated_blocks.add(_then_block)
                else:
                    _then_stmts = []
                # Phase 42: 生成完整的orelse分支
                _else_stmts = []
                if _else_block and _else_block not in self.generated_blocks:
                    _else_role = self.region_analyzer.get_block_role(_else_block)
                    if _else_role in (BlockRole.CONTINUE, BlockRole.PURE_CONTINUE):
                        _else_stmts = [{'type': 'Continue'}]
                        self.generated_blocks.add(_else_block)
                    else:
                        _else_stmts = self._generate_block_statements(_else_block)
                        if _else_block not in self.generated_blocks:
                            self.generated_blocks.add(_else_block)
                if_stmt = {'type': 'If', 'test': cond_expr, 'body': _then_stmts if _then_stmts else [{'type': 'Pass'}], 'orelse': _else_stmts if _else_stmts else []}
                self.generated_blocks.add(block)
                self.generated_offsets.add(block.start_offset)
                result = pre_stmts + [if_stmt] if pre_stmts else [if_stmt]
                return result
            if _should_skip_transform:
                pre_stmts = []
                cond_instrs = []
                for instr in block.instructions:
                    if instr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                        continue
                    if instr.opname in FORWARD_JUMP_OPS or instr.opname in BACKWARD_JUMP_OPS:
                        break
                    if instr.opname in ('POP_EXCEPT', 'PUSH_EXC_INFO', 'RERAISE',
                                        'WITH_EXCEPT_START', 'CHECK_EXC_MATCH', 'CHECK_EG_MATCH'):
                        continue
                    if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                        stmt = self._build_store_statement(cond_instrs + [instr], block=block)
                        if stmt:
                            pre_stmts.append(stmt)
                        cond_instrs = []
                        continue
                    if instr.opname == 'POP_TOP' and cond_instrs:
                        stmt = self._build_statement(cond_instrs)
                        if stmt:
                            pre_stmts.append(stmt)
                        cond_instrs = []
                        continue
                    cond_instrs.append(instr)
                if not cond_instrs:
                    self.generated_blocks.add(block)
                    return pre_stmts if pre_stmts else None
                expr = self.expr_reconstructor.reconstruct(cond_instrs)
                if expr is None:
                    self.generated_blocks.add(block)
                    return pre_stmts if pre_stmts else None
                cond_expr = expr
                if_stmt = {'type': 'If', 'test': cond_expr, 'body': []}
                self.generated_blocks.add(block)
                self.generated_offsets.add(block.start_offset)
                result = pre_stmts + [if_stmt] if pre_stmts else [if_stmt]
                return result
            target_succ = continue_succ
            body_type = 'Continue'
        elif break_succ and normal_succ:
            target_succ = break_succ
            body_type = 'Break'
        elif break_succ and continue_succ:
            target_succ = break_succ
            body_type = 'Break'
        elif continue_succ:
            target_succ = continue_succ
            body_type = 'Continue'
        else:
            return None

        pre_stmts = []
        cond_instrs = []
        for instr in block.instructions:
            if instr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                continue
            if instr.opname in FORWARD_JUMP_OPS or instr.opname in BACKWARD_JUMP_OPS:
                break
            if instr.opname in ('POP_EXCEPT', 'PUSH_EXC_INFO', 'RERAISE',
                                'WITH_EXCEPT_START', 'CHECK_EXC_MATCH', 'CHECK_EG_MATCH'):
                continue
            if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                stmt = self._build_store_statement(cond_instrs + [instr], block=block)
                if stmt:
                    pre_stmts.append(stmt)
                cond_instrs = []
                continue
            if instr.opname == 'POP_TOP' and cond_instrs:
                stmt = self._build_statement(cond_instrs)
                if stmt:
                    pre_stmts.append(stmt)
                cond_instrs = []
                continue
            cond_instrs.append(instr)
        if not cond_instrs:
            self.generated_blocks.add(block)
            return pre_stmts if pre_stmts else None
        expr = self.expr_reconstructor.reconstruct(cond_instrs)
        if expr is None:
            self.generated_blocks.add(block)
            return pre_stmts if pre_stmts else None
        is_if_false = 'IF_FALSE' in last_instr.opname
        target_is_jump = target_succ[1]
        if target_is_jump:
            cond_expr = _negate_expr(expr) if is_if_false else expr
        else:
            cond_expr = expr if is_if_false else _negate_expr(expr)
        _target_blk = target_succ[0]
        _target_meaningful = [i for i in _target_blk.instructions
            if i.opname not in ('RESUME','NOP','CACHE','PUSH_NULL')
            and i.opname not in FORWARD_JUMP_OPS
            and i.opname not in BACKWARD_JUMP_OPS
            and i.opname not in ('RETURN_VALUE','RAISE_VARARGS','RERAISE','BREAK_LOOP','CONTINUE')
            and i.opname not in ('POP_TOP','SWAP')]
        if len(_target_meaningful) >= 3 and _target_blk not in self.generated_blocks:
            _target_stmts = self._generate_block_statements(_target_blk)
            if _target_blk not in self.generated_blocks:
                self.generated_blocks.add(_target_blk)
            if _target_stmts:
                _has_break = any(s.get('type') in ('Break','Continue','Return') for s in _target_stmts)
                if not _has_break and body_type in ('Break','Continue'):
                    _target_stmts.append({'type': body_type})
                _body_stmts = _target_stmts
            else:
                _body_stmts = [{'type': body_type}]
        else:
            if body_type == 'Break':
                _blk_has_ret = any(i.opname in ('RETURN_VALUE', 'RETURN_CONST') for i in _target_blk.instructions)
                _ret_val = None
                if _blk_has_ret:
                    _blk_meaningful = [i for i in _target_blk.instructions
                                       if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                    if _blk_meaningful and _blk_meaningful[0].opname in ('LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF'):
                        _ret_val = {'type': 'Name', 'id': _blk_meaningful[0].argval, 'ctx': 'Load'}
                    elif _blk_meaningful and _blk_meaningful[0].opname == 'LOAD_CONST':
                        _ret_val = {'type': 'Constant', 'value': _blk_meaningful[0].argval}
                if _ret_val is not None:
                    _body_stmts = [{'type': 'Return', 'value': _ret_val}]
                else:
                    _body_stmts = [{'type': body_type}]
            else:
                _body_stmts = [{'type': body_type}]
        if_stmt = {'type': 'If', 'test': cond_expr, 'body': _body_stmts}
        self.generated_blocks.add(block)
        self.generated_offsets.add(block.start_offset)
        if target_succ[0] not in self.generated_blocks:
            self.generated_blocks.add(target_succ[0])
            self.generated_offsets.add(target_succ[0].start_offset)
        if normal_succ:
            _norm_blk = normal_succ[0]
            _norm_last_instr = _norm_blk.get_last_instruction()
            if (_norm_last_instr is not None and
                _norm_last_instr.opname in ('POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE')):
                if _norm_blk not in self.generated_blocks:
                    self.generated_blocks.add(_norm_blk)
                    self.generated_offsets.add(_norm_blk.start_offset)
        result = pre_stmts + [if_stmt] if pre_stmts else [if_stmt]
        return result

    def _is_child_reachable_from_blocks(self, child: Region, blocks: Set) -> bool:
        """检查子区域是否可以从给定的块集到达"""
        for tb in blocks:
            if child.entry in tb.successors:
                return True
            for tb_succ in tb.successors:
                if child.entry in tb_succ.successors:
                    return True
                visited_succ = {tb, tb_succ}
                succ_frontier = list(tb_succ.successors)
                for depth in range(8):
                    next_frontier = []
                    for sf in succ_frontier:
                        if sf in visited_succ:
                            continue
                        visited_succ.add(sf)
                        if child.entry in sf.successors:
                            return True
                        next_frontier.extend(sf.successors)
                    if not next_frontier:
                        break
                    succ_frontier = next_frontier
        return False

    def _is_pure_continue_block(self, block: BasicBlock) -> bool:
        """检查块是否是纯 continue 块（仅包含 continue 逻辑）"""
        return self.block_role(block) == BlockRole.PURE_CONTINUE

    def _is_pure_break_block(self, block: BasicBlock) -> bool:
        """检查块是否是纯 break 块（仅包含 break 逻辑）"""
        return self.block_role(block) == BlockRole.PURE_BREAK

    def _is_handler_body_block(self, block: BasicBlock, region: TryExceptRegion = None) -> bool:
        """检查块是否是异常处理器体块"""
        if region and hasattr(region, 'handler_entry_blocks'):
            return block in region.handler_entry_blocks
        return False

    def _is_with_cleanup_block(self, block: BasicBlock) -> bool:
        """检查块是否是 with 清理块"""
        role = self.block_role(block)
        return role in (BlockRole.WITH_EXIT_CLEANUP, BlockRole.WITH_STACK_CLEANUP, BlockRole.WITH_HANDLER)

    def _if_generate_branch_stmts(self, blocks=None, _depth=0, region=None):
        if region is not None:
            return self._generate_if(region)
        if blocks is not None:
            stmts = self._process_if_blocks(blocks, region, branch='standalone')
            return self._merge_compares(stmts)
        return []

    def _merge_compares(self, stmts):
        if not stmts or self.cfg.name == '<module>':
            return stmts
        result, i = [], 0
        while i < len(stmts):
            s = stmts[i]
            if (isinstance(s, dict) and s.get('type') == 'Expr' and
                    isinstance(s.get('value'), dict) and s['value'].get('type') == 'Compare'):
                start = i
                while i < len(stmts) and (isinstance(stmts[i], dict) and stmts[i].get('type') == 'Expr'
                        and isinstance(stmts[i].get('value'), dict) and stmts[i]['value'].get('type') == 'Compare'):
                    i += 1
                cvs = [stmts[j]['value'] for j in range(start, i)]
                if i < len(stmts):
                    ns = stmts[i]
                    if (isinstance(ns, dict) and ns.get('type') == 'Return' and
                            isinstance(ns.get('value'), dict) and ns['value'].get('type') == 'Compare'):
                        cvs.append(ns['value']); i += 1
                    elif (isinstance(ns, dict) and ns.get('type') == 'Return' and
                            isinstance(ns.get('value'), dict) and ns['value'].get('type') == 'Constant'
                            and ns['value'].get('value') is True):
                        i += 1
                merged = cvs[0] if len(cvs) == 1 else {'type': 'BoolOp', 'op': 'And', 'values': cvs}
                result.append({'type': 'Return', 'value': merged} if i > start + len(cvs)
                              or (i < len(stmts) and isinstance(stmts[i], dict) and stmts[i].get('type') == 'Return'
                                  and isinstance(stmts[i].get('value'), dict) and stmts[i]['value'].get('type') == 'Constant'
                                  and stmts[i]['value'].get('value') is False and (i := i + 1) or True)
                              else {'type': 'Expr', 'value': merged} for _ in [0])
                if result[-1].get('type') != 'Return':
                    result.pop()
                    for cv in cvs:
                        result.append({'type': 'Expr', 'value': cv})
            else:
                result.append(s); i += 1
        return result

    def _generate_try_body(self, region: TryExceptRegion) -> List[Dict[str, Any]]:
        body_stmts: List[Dict[str, Any]] = []

        nested_try_regions = []
        for r in self.region_analyzer.regions:
            if isinstance(r, TryExceptRegion) and r is not region:
                is_child = r.parent is region
                is_in_try_blocks = r.entry in set(region.try_blocks)
                is_before_try_start = r.entry.start_offset < region.try_offset_start and r.try_offset_end > region.try_offset_start
                handler_in_range = False
                for heb in r.handler_entry_blocks:
                    if region.try_offset_start <= heb.start_offset < region.try_offset_end:
                        handler_in_range = True
                        break
                for _, _, hblocks in r.except_handlers:
                    for hb in hblocks:
                        if region.try_offset_start <= hb.start_offset < region.try_offset_end:
                            handler_in_range = True
                            break
                    if handler_in_range:
                        break
                is_nested = is_child or is_in_try_blocks or is_before_try_start or handler_in_range
                if is_nested and (r.parent is None or r.parent is region):
                    nested_is_smaller = r.try_offset_end - r.try_offset_start < region.try_offset_end - region.try_offset_start
                    if nested_is_smaller or is_child:
                        nested_try_regions.append(r)

        for ntr in sorted(nested_try_regions, key=lambda r: r.try_offset_start):
            if ntr.entry.start_offset < region.try_offset_start:
                if id(ntr) not in self._generated_regions and id(ntr) not in self._generating_regions:
                    self.generated_blocks.discard(ntr.entry)
                    for b in ntr.try_blocks:
                        self.generated_blocks.discard(b)
                    for _, _, hblocks in ntr.except_handlers:
                        for hb in hblocks:
                            self.generated_blocks.discard(hb)
                    for cb in ntr.cleanup_blocks:
                        self.generated_blocks.discard(cb)
                    nested_ast = self._generate_try(ntr)
                    if nested_ast:
                        body_stmts.append(nested_ast)
                    for b in ntr.blocks:
                        self.generated_blocks.add(b)

        for block in sorted(region.try_blocks, key=lambda b: b.start_offset):
            if block in self.generated_blocks:
                continue

            _fc_keep = region.finally_copy_blocks.get(block.start_offset)
            if _fc_keep is not None:
                if _fc_keep == 0:
                    continue
                _enhanced_meta = region.metadata.get('enhanced_finally_copies', {})
                _copy_info = _enhanced_meta.get(block.start_offset, {})

                cutoff_idx = _copy_info.get('cutoff_idx')
                if cutoff_idx is None:
                    meaningful_count = 0
                    cutoff_idx = len(block.instructions)
                    for idx, instr in enumerate(block.instructions):
                        if instr.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                            meaningful_count += 1
                            if meaningful_count == _fc_keep:
                                cutoff_idx = idx + 1
                                break
                if cutoff_idx < len(block.instructions):
                    truncated_instrs = block.instructions[:cutoff_idx]
                    import copy as _copy
                    temp_block = _copy.copy(block)
                    temp_block.instructions = truncated_instrs
                    temp_block.successors = []
                    stmts = self._generate_block_statements(temp_block)
                    body_stmts.extend(stmts)
                    self.generated_blocks.add(block)
                    continue

            if region.has_finally and block != region.entry:
                all_region_blocks = set(region.blocks)
                has_exc_instr = any(i.opname in ('PUSH_EXC_INFO', 'WITH_EXCEPT_START', 'CHECK_EXC_MATCH',
                                                   'CHECK_EG_MATCH', 'POP_EXCEPT') for i in block.instructions)
                succs_outside = [s for s in block.successors if s not in all_region_blocks]
                pred_in_try = any(p in set(region.try_blocks) and p != block for p in block.predecessors)
                _last_op = block.get_last_instruction()
                is_terminal = _last_op is not None and _last_op.opname in ('RETURN_VALUE', 'RETURN_CONST')
                if not has_exc_instr and (succs_outside or is_terminal) and pred_in_try:
                    self.generated_blocks.add(block)
                    continue

            is_nested_try_entry = False
            for ntr in nested_try_regions:
                if ntr.entry == block and id(ntr) not in self._generated_regions and id(ntr) not in self._generating_regions:
                    nested_ast = self._generate_try(ntr)
                    if nested_ast:
                        body_stmts.append(nested_ast)
                    for b in ntr.blocks:
                        self.generated_blocks.add(b)
                    is_nested_try_entry = True
                    break
            if is_nested_try_entry:
                continue

            is_nested_region_entry = False
            for nr in self.region_analyzer.regions:
                if nr is region or nr.entry != block:
                    continue
                if isinstance(nr, TryExceptRegion):
                    continue
                if id(nr) in self._generated_regions:
                    continue
                else:
                    pass
                if isinstance(nr, (LoopRegion, IfRegion, WithRegion, MatchRegion, BoolOpRegion, TernaryRegion, AssertRegion)):
                    for b in nr.blocks:
                        self.generated_blocks.discard(b)
                    nested_ast = self._generate_region(nr)
                    if nested_ast:
                        if isinstance(nested_ast, list):
                            body_stmts.extend(nested_ast)
                        else:
                            body_stmts.append(nested_ast)
                    for b in nr.blocks:
                        self.generated_blocks.add(b)
                    is_nested_region_entry = True
                    break
            if not is_nested_region_entry:
                pass
            if is_nested_region_entry:
                continue

            _meaningful_instrs = [i for i in block.instructions
                                  if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
            if not _meaningful_instrs:
                self.generated_blocks.add(block)
                continue

            _has_implicit_continue = (
                self._loop_depth > 0 and
                len(_meaningful_instrs) <= 3 and
                any(i.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT') for i in _meaningful_instrs) and
                not any(i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_DEREF', 'STORE_GLOBAL',
                                     'CALL', 'CALL_FUNCTION', 'BINARY_OP',
                                     'LOAD_ATTR', 'LOAD_METHOD', 'BINARY_SUBSCR',
                                     'GET_ITER', 'FOR_ITER', 'UNPACK_SEQUENCE')
                      for i in _meaningful_instrs
                      if i.opname not in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'))
            )
            if _has_implicit_continue:
                _pre_jump_instrs = []
                for i in _meaningful_instrs:
                    if i.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'):
                        break
                    _pre_jump_instrs.append(i)
                if _pre_jump_instrs:
                    _stmt = self._build_statement(_pre_jump_instrs)
                    if _stmt:
                        body_stmts.append(_stmt)
                body_stmts.append({'type': 'Continue'})
                self.generated_blocks.add(block)
                continue

            _is_reraise_cleanup = (
                any(i.opname == 'RERAISE' for i in _meaningful_instrs) and
                all(i.opname in ('COPY', 'POP_EXCEPT', 'RERAISE', 'SWAP', 'POP_TOP',
                                 'LOAD_CONST', 'STORE_FAST', 'STORE_NAME',
                                 'STORE_DEREF', 'STORE_GLOBAL',
                                 'DELETE_FAST', 'DELETE_NAME',
                                 'DELETE_DEREF', 'DELETE_GLOBAL')
                    for i in _meaningful_instrs)
            )
            if _is_reraise_cleanup:
                self.generated_blocks.add(block)
                continue

            _is_trivial_return = (
                len(_meaningful_instrs) == 2 and
                _meaningful_instrs[0].opname in ('LOAD_CONST',) and
                _meaningful_instrs[0].argval is None and
                _meaningful_instrs[1].opname in ('RETURN_VALUE', 'RETURN_CONST')
            )
            if _is_trivial_return:
                if self._loop_depth > 0:
                    body_stmts.append({'type': 'Break'})
                self.generated_blocks.add(block)
                continue

            _is_exc_cleanup = (
                any(i.opname == 'POP_EXCEPT' for i in _meaningful_instrs) and
                not any(i.opname in ('RERAISE', 'RETURN_VALUE', 'RETURN_CONST',
                                     'STORE_FAST', 'STORE_NAME', 'STORE_DEREF', 'STORE_GLOBAL',
                                     'CALL', 'CALL_FUNCTION', 'CALL_METHOD',
                                     'BUILD_LIST', 'BUILD_MAP', 'BUILD_TUPLE', 'BUILD_SET',
                                     'BUILD_STRING', 'BUILD_SLICE',
                                     'BINARY_OP', 'BINARY_SUBSCR',
                                     'LOAD_ATTR', 'LOAD_METHOD', 'LOAD_GLOBAL', 'LOAD_NAME',
                                     'COMPARE_OP')
                     for i in _meaningful_instrs) and
                all(i.opname in ('POP_EXCEPT', 'JUMP_FORWARD', 'JUMP_ABSOLUTE',
                                 'POP_TOP', 'LOAD_CONST', 'NOP', 'CACHE')
                    for i in _meaningful_instrs)
            )
            if _is_exc_cleanup:
                self.generated_blocks.add(block)
                continue

            nested_region = self.region_analyzer.get_entry_region_for_block(block)
            if not nested_region or nested_region is region:
                block_region = self.region_analyzer.get_region_for_block(block)
                if block_region and block_region is not region and isinstance(block_region, (IfRegion, LoopRegion, TryExceptRegion, WithRegion, MatchRegion, BoolOpRegion, TernaryRegion, AssertRegion)):
                    nested_region = block_region
                elif nested_region is region:
                    nested_region = None
                if nested_region is None:
                    for r in self.region_analyzer.regions:
                        if r is region:
                            continue
                        if isinstance(r, (IfRegion, LoopRegion, TryExceptRegion, WithRegion, MatchRegion, BoolOpRegion, TernaryRegion, AssertRegion)):
                            if block in r.blocks or (hasattr(r, 'init_blocks') and block in r.init_blocks):
                                nested_region = r
                                break
            if nested_region and isinstance(nested_region, (IfRegion, LoopRegion, TryExceptRegion, WithRegion, MatchRegion, BoolOpRegion, TernaryRegion, AssertRegion)):
                if nested_region is region:
                    stmts = self._generate_block_statements(block)
                    body_stmts.extend(stmts)
                    continue
                nested_id = id(nested_region)
                if nested_id in self._generated_regions or nested_id in self._generating_regions:
                    if block in region.try_blocks:
                        stmts = self._generate_block_statements(block)
                        body_stmts.extend(stmts)
                    self.generated_blocks.add(block)
                    continue
                if nested_region.entry == block or (hasattr(nested_region, 'condition_block') and nested_region.condition_block == block):
                    nested_ast = self._generate_region(nested_region)
                    if nested_ast:
                        if isinstance(nested_ast, list):
                            body_stmts.extend(nested_ast)
                        else:
                            body_stmts.append(nested_ast)
                    for b in nested_region.blocks:
                        self.generated_blocks.add(b)
                    if hasattr(nested_region, 'condition_block') and nested_region.condition_block:
                        self.generated_blocks.add(nested_region.condition_block)
                    if hasattr(nested_region, 'header_block') and nested_region.header_block:
                        self.generated_blocks.add(nested_region.header_block)
                    if hasattr(nested_region, 'init_blocks') and nested_region.init_blocks:
                        for ib in nested_region.init_blocks:
                            self.generated_blocks.add(ib)
                elif block in nested_region.blocks:
                    self.generated_blocks.add(block)
                else:
                    stmts = self._generate_block_statements(block)
                    body_stmts.extend(stmts)
                    self.generated_blocks.add(block)
            else:
                stmts = self._generate_block_statements(block)
                body_stmts.extend(stmts)
                self.generated_blocks.add(block)

        for ntr in nested_try_regions:
            if id(ntr) not in self._generated_regions and id(ntr) not in self._generating_regions:
                for b in ntr.blocks:
                    self.generated_blocks.discard(b)
                nested_ast = self._generate_try(ntr)
                if nested_ast:
                    body_stmts.append(nested_ast)
                for b in ntr.blocks:
                    self.generated_blocks.add(b)

        # 反编译逻辑：处理try语句体中的TernaryRegion/BoolOpRegion子区域
        # 根因：这些表达式级区域可以嵌入try体的任何位置
        # 归约顺序：内层（ternary/boolop）先识别、外层（try）后处理
        # 符合度：TernaryRegion→IfExp(Expr), BoolOpRegion→BoolOp(Expr)
        if hasattr(region, 'children') and region.children:
            """
            【反编译逻辑】Try语句体子区域处理扩展（Phase 35 统一框架）
            
            ═══════════════════════════════════════════════════════════════════════════════
            1. 功能概述:
            ─────────────────────
            本代码段实现 try 语句体内的表达式级子区域（TernaryRegion/BoolOpRegion）生成，
            是 Phase 35 统一子区域处理框架在 try-except-finally 场景中的应用。
            
            **设计目标**:
            - 确保try体中的三元表达式和布尔表达式被正确还原
            - 保持与if/with/match中相同子区域处理的一致性
            - 避免子区域与父try块的冲突和重复生成
            
            2. 处理范围:
            ─────────────────────
            
            **支持的区域类型**:
            - TernaryRegion: try 体中的三元表达式
              ```python
              try:
                  x = a if cond else b  # TernaryRegion 嵌套在 TryExceptRegion 的 try_blocks 中
              except:
                  handle_error()
              ```
              
            - BoolOpRegion: try 体中的布尔运算表达式
              ```python
              try:
                  flag = (p and q) or r   # BoolOpRegion 嵌套在 TryExceptRegion 中
                  result = risky_operation()
              except Exception:
                  fallback()
              ```
            
            3. 实现细节:
            ─────────────────────
            ```python
            if hasattr(region, 'children') and region.children:
                for child in region.children:
                    # 只处理表达式级子区域（TernaryRegion和BoolOpRegion）
                    if isinstance(child, (TernaryRegion, BoolOpRegion)):
                        child_id = id(child)
                        
                        # 防止重复生成检查
                        if child_id not in self._generated_regions and \
                           child_id not in self._generating_regions:
                            
                            # 根据类型调用相应的生成器
                            if isinstance(child, TernaryRegion):
                                child_ast = self._generate_ternary(child)
                                # 生成 ast.IfExp 节点
                            else:
                                child_ast = self._generate_boolop(child)
                                # 生成 ast.BoolOp 节点
                            
                            if child_ast:
                                # 将生成的AST插入到body_stmts
                                if isinstance(child_ast, list):
                                    body_stmts.extend(child_ast)
                                else:
                                    body_stmts.append(child_ast)
                            
                            # 标记所有属于该子区域的块为已生成
                            for b in child.blocks:
                                self.generated_blocks.add(b)
                            
                            # 记录已完成的区域
                            self._generated_regions.add(child_id)
            ```
            
            4. 执行时机与顺序:
            ────────────────────────────────
            
            **在 _generate_try_body() 中的位置**:
            ```
            _generate_try_body(region):
                Part 1: 生成普通块语句（L5447-5470）
                Part 2: 生成嵌套的TryExceptRegion（L5472-5480）
                Part 3: 【本代码段】生成Ternary/BoolOp子区域（L5482-5502）← 这里
                return body_stmts
            ```
            
            **为什么放在嵌套try之后？**
            - 嵌套try可能包含更内层的ternary/boolop
            - 先处理结构化区域，再处理表达式级区域
            - 保证层次从外到内的正确顺序
            
            5. 与其他方法的对比:
            ────────────────────────────────
            
            | 方法名 | 父区域类型 | 子区域类型 | 特殊逻辑 |
            |--------|-----------|-----------|---------|
            | _process_if_blocks | IfRegion | Ternary/BoolOp | 无额外过滤 |
            | _generate_with | WithRegion | Try/If/Loop/With | WithCleanup过滤 |
            | _generate_try_body | TryExceptRegion | Ternary/BoolOp | 无额外过滤 |
            | _generate_match | MatchRegion | Ternary/BoolOp | 通配符match检查 |
            
            **共同特征**:
            ✅ 相同的防重复机制
            ✅ 相同的类型分派逻辑
            ✅ 相同的结果插入方式
            
            **特有之处**:
            - 本方法位于try体生成流程中
            - 不需要特殊的cleanup过滤（try本身已处理异常相关代码）
            
            6. 典型应用场景:
            ─────────────────────
            
            **场景1: 资源管理中的条件赋值**
            ```python
            try:
                config = load_config() or default_config  # BoolOpRegion
                connection = connect(primary) or connect(backup)  # BoolOpRegion
                data = fetch_data() if is_online else cached_data  # TernaryRegion
                process(data)
            except ConnectionError:
                retry_or_fail()
            ```
            
            **场景2: 数据验证中的复合表达式**
            ```python
            try:
                user_input = get_input()
                is_valid = (user_input and user_input.strip()) or None  # BoolOp
                value = int(is_valid) if is_valid.isdigit() else 0     # Ternary
                save(value)
            except ValueError:
                use_default()
            ```
            
            **场景3: 复杂业务逻辑**
            ```python
            try:
                result = (
                    fast_path() 
                    if cache_hit and is_valid 
                    else slow_path()  # 混合Ternary+BoolOp
                )
                log(result)
            except Exception as e:
                report_error(e)
            finally:
                cleanup()
            ```
            
            7. 边界情况处理:
            ─────────────────────
            - ✅ 空children列表: hasattr检查避免AttributeError
            - ✅ 已生成的子区域: _generated_regions集合防止重复
            - ✅ 正在生成的子区域: _generating_regions防止循环
            - ⚠️ 子区域跨越try边界: 当前不处理（理论上不应发生）
            - ❌ 子区域与handler重叠: 可能导致重复（需要进一步测试）
            
            8. 性能考虑:
            ─────────────────────
            - 时间复杂度: O(children_count × avg_blocks_per_child)
            - 通常children数量很少（<5），性能影响可忽略
            - 空间复杂度: 仅使用已有的generated_blocks集合
            
            ═══════════════════════════════════════════════════════════════════════════════
            """
            for child in region.children:
                if isinstance(child, (TernaryRegion, BoolOpRegion)):
                    child_id = id(child)
                    if child_id not in self._generated_regions and child_id not in self._generating_regions:
                        if isinstance(child, TernaryRegion):
                            child_ast = self._generate_ternary(child)
                        else:
                            child_ast = self._generate_boolop(child)
                        if child_ast:
                            if isinstance(child_ast, list):
                                body_stmts.extend(child_ast)
                            else:
                                body_stmts.append(child_ast)
                        for b in child.blocks:
                            self.generated_blocks.add(b)
                        self._generated_regions.add(child_id)

        return body_stmts

    def _generate_try(self, region: TryExceptRegion) -> Dict[str, Any]:
        """
        将 TryExceptRegion 转换为 AST Try 节点 - 核心生成算法

        ═══════════════════════════════════════════════════════════════════════════════
        【功能说明】
        本方法是异常处理区域反编译的核心生成器，将 _identify_try_except_regions() 识别出的
        TryExceptRegion 对象转换为符合 Python AST 规范的字典结构（后续由 ast.fix_missing_nodes()
        和 compile() 验证正确性）。

        ═══════════════════════════════════════════════════════════════════════════════
        【AST 节点结构映射】

        生成的 AST 字典结构对应 Python 的 ast.Try 节点：
        {
            'type': 'Try',                  # 节点类型标识
            'body': [stmt1, stmt2, ...],     # try: 子句体（语句列表）
            'handlers': [handler1, ...],     # except/except* 子句列表
            'orelse': [stmt1, ...] | None,   # else: 子句体（可选）
            'finalbody': [stmt1, ...] | None # finally: 子句体（可选）
        }

        每个 handler 的结构：
        {
            'type': 'ExceptHandler',         # 节点类型标识
            'exc_type': Name(id='ValueError') | None,  # 异常类型表达式（bare except 为 None）
            'name': 'e' | None,              # as 变量名（可选）
            'body': [stmt1, stmt2, ...]      # handler 体语句列表
        }

        ═══════════════════════════════════════════════════════════════════════════════
        【生成流程】

        Step 1: 生成 try body (_generate_try_body)
        ─────────────────────────────────
        输入：region.try_blocks (BasicBlock 列表)
        输出：body_stmts (AST 语句字典列表)

        处理逻辑：
        a) 识别嵌套的 TryExceptRegion（内层 try 结构）
           - 检查 parent 关系、位置关系、handler 是否在外层 try 范围内
           - 递归调用 _generate_try() 生成嵌套的 Try AST

        b) 遍历 try_blocks 中的每个基本块：
           i.   跳过已生成的块（generated_blocks 集合）
           ii.  处理 finally copy 块（finally 代码在正常路径和异常路径都有副本）
           iii. 识别嵌套区域入口（IfRegion, LoopRegion, WithRegion 等）
                → 调用对应的 _generate_*() 方法
           iv.  过滤 trivial 块：
               - 纯 reraise cleanup 块（COPY+POP_EXCEPT+RERAISE 序列）
               - 纯 return None 块（在循环中可能转为 break）
               - 纯 exc cleanup 块（POP_EXCEPT + JUMP）
           v.   生成普通块的语句（_generate_block_statements）

        Step 2: 生成 except handlers
        ─────────────────────────────────
        输入：region.except_handlers, region.handler_entry_blocks
        输出：handlers (ExceptHandler 字典列表)

        对于每个 handler (exc_type, exc_name, handler_blocks)：

        a) 定位 handler_entry_block（handler 入口基本块）

        b) 生成 handler body 语句（_generate_handler_body_statements）
           这是关键步骤，需要正确处理异常处理相关的指令：
           ──────────────────────────────────────────────────────
           **需要过滤的指令**（不生成对应源码）：
           - RESUME, NOP, CACHE, PUSH_NULL: 框架指令
           - PUSH_EXC_INFO: 异常信息压栈（隐式操作）
           - POP_EXCEPT: 异常帧清理（隐式操作）
           - POP_TOP: 弹出异常类型检查结果
           - CHECK_EXC_MATCH / CHECK_EG_MATCH: 异常类型匹配（隐式操作）
           - WITH_EXCEPT_START: with 语句退出处理

           **特殊处理**：
           i.  异常分发跳转（exc_dispatch_jump）：
               CHECK_EXC_MATCH 后的条件跳转决定是否进入 handler body
               只生成跳转之后的指令（匹配成功的情况）

          ii. POP_EXCEPT 后的清理序列：
              如果后面跟着 LOAD_CONST(None) + STORE_* + DELETE_*，
              这是 `except ... as e:` 的清理代码（删除 e 以防止循环引用）
              不生成对应的源码

         iii. RERAISE 指令：
              - arg=0 且无后续指令 → cleanup reraise（不生成）
              - arg=0 但有其他上下文 → 可能是显式 raise（生成 Raise 节点）
              - arg=1 → 异常链 reraise（不生成，隐式操作）

          iv. RETURN_VALUE 在 handler 中：
              - 在循环体内且返回 None → 转为 Break 语句
              - 在函数中 → 生成 Return 语句

           v. JUMP_BACKWARD 在循环中：
              - 如果跳转目标是循环头 → 隐式 continue（不生成）
              - 否则 → 生成 Continue 语句

        c) 构建 ExceptHandler 节点：
           - type: 'ExceptHandler'
           - exc_type: 异常类型（Name 节点或 None 表示 bare except）
           - name: 异常变量名（as 子句）
           - body: handler 语句列表（如果为空则生成 Pass）

        Step 3: 生成 else 块（可选）
        ─────────────────────────────────
        条件：region.has_else == True 且 region.else_blocks 非空

        处理逻辑类似 try body，遍历 else_blocks 生成语句。
        else 块只在 try 正常完成（无异常）时执行。

        Step 4: 生成 finally 块（可选）
        ─────────────────────────────────
        条件：region.has_finally == True

        处理逻辑：
        a) 遍历 region.finally_blocks
        b) 对每个块调用 _generate_handler_body_statements
        c) 如果 finally 块为空但 has_finally=True，生成 Pass

        ═══════════════════════════════════════════════════════════════════════════════
        【特殊情况处理】

        1. **嵌套 try 结构**
           问题：try 块内部包含另一个完整的 try-except 结构
           解决：在 _generate_try_body() 中检测并递归生成内层 Try AST
           判定条件：
           - 内层 region.parent == 外层 region
           - 内层 entry 在外层 try_blocks 中
           - 内层 handler 入口在外层 try 偏移范围内

        2. **try 中的 break/continue**
           问题：break/continue 在 try 中时，需要先执行 finally 再跳出
           字节码特征：
           - break: 在循环条件检查后插入 finally 代码副本
           - continue: 类似，但在循环回边前插入
           解决：识别 return/break/continue 语义并生成正确的 AST 节点

        3. **try 中的 return**
           问题：return 在 try 中时，需要先执行 finally 再返回
           字节码特征：return 指令可能在 finally copy 块之后
           解决：正常生成 Return 节点，finally 由单独的逻辑处理

        4. **except as 变量清理**
           Python 3.11+ 会在 except 块末尾自动删除 as 变量以防止循环引用
           字节码：LOAD_CONST(None) + STORE(name) + DELETE(name)
           解决：在 _generate_handler_body_statements 中检测并过滤此序列

        5. **多 except 链**
           多个 except 子句形成链式结构（通过条件跳转连接）
           解决：_follow_except_chain() 已在识别阶段将链拆分为独立的 handler，
                 这里只需按顺序生成即可

        ═══════════════════════════════════════════════════════════════════════════════
        【字节码等价保证】

        为了确保重编译后的字节码与原始字节码一致（指令数和操作码都相同），
        本方法遵循以下原则：

        1. **精确的指令过滤**：只过滤确实不需要生成源码的框架指令
        2. **保留语义等价的操作**：即使某些操作可以优化，也保持原始形式
        3. **正确的语句边界**：使用 _build_statement() 确保语句边界与原始一致
        4. **异常处理流程一致性**：确保异常传播路径的字节码顺序正确

        ═══════════════════════════════════════════════════════════════════════════════
        【区域状态管理】

        使用以下集合管理生成状态，避免重复生成和无限递归：
        - self._generating_regions: 正在生成的区域 ID 集合（防止递归循环）
        - self._generated_regions: 已完成的区域 ID 集合
        - self.generated_blocks: 已生成的基本块集合

        进入方法时添加到 _generating_regions，完成后转移到 _generated_regions。

        ═══════════════════════════════════════════════════════════════════════════════
        【返回值】
        返回 Try AST 节点的字典表示，可直接用于后续的 AST 处理和编译验证。

        ═══════════════════════════════════════════════════════════════════════════════
        """
        region_id = id(region)
        self._generating_regions.add(region_id)
        self._try_depth += 1

        try:
            _handler_entry_blocks = set(region.handler_entry_blocks)
            _pre_consumed_handler_entries = _handler_entry_blocks & self.generated_blocks
            self.generated_blocks.update(_handler_entry_blocks)

            body_stmts = self._generate_try_body(region)

            self.generated_blocks -= (_handler_entry_blocks - _pre_consumed_handler_entries)

            handlers = []
            _enumerated_handlers = list(enumerate(region.except_handlers))
            if len(_enumerated_handlers) > 1 and len(region.handler_entry_blocks) >= len(_enumerated_handlers):
                _has_multiple_entries = len(set(id(heb) for heb in region.handler_entry_blocks[:len(_enumerated_handlers)])) > 1
                if _has_multiple_entries:
                    _enumerated_handlers.sort(
                        key=lambda x: region.handler_entry_blocks[x[0]].start_offset
                        if x[0] < len(region.handler_entry_blocks) and region.handler_entry_blocks[x[0]]
                        else float('inf')
                    )
            for idx, (exc_type, exc_name, handler_blocks) in _enumerated_handlers:
                handler_entry = region.handler_entry_blocks[idx] if idx < len(region.handler_entry_blocks) else None
                if handler_entry is None and handler_blocks:
                    handler_entry = handler_blocks[0]
                if handler_entry is None:
                    continue
                if handler_entry in self.generated_blocks:
                    continue
                handler_body = self._generate_handler_body_statements(handler_entry)
                self.generated_blocks.add(handler_entry)
                for hb in handler_blocks:
                    if hb in self.generated_blocks:
                        continue
                    if hb is handler_entry:
                        continue
                    hbs = self._generate_handler_body_statements(hb)
                    if hbs:
                        handler_body.extend(hbs)
                    self.generated_blocks.add(hb)
                handler_node = {'type': 'ExceptHandler', 'body': handler_body if handler_body else [{'type': 'Pass'}]}
                if exc_name:
                    handler_node['name'] = exc_name
                if exc_type:
                    handler_node['exc_type'] = {'type': 'Name', 'id': str(exc_type), 'ctx': 'Load'} if isinstance(exc_type, str) else exc_type
                handlers.append(handler_node)

            # try_try嵌套补偿：region_analyzer可能遗漏外层except handler
            # 当异常表中有target指向try_offset_end位置的handler（不在当前handler_entry_blocks中），
            # 说明存在外层except handler被遗漏。此时需要将当前handlers（内层）包装成嵌套Try AST，
            # 并用外层handler作为当前Try AST的handlers。
            # 关键条件：target_block不在当前region.blocks中（区分try_try与try/except/finally）
            _existing_handler_offsets = set()
            for heb in region.handler_entry_blocks:
                _existing_handler_offsets.add(heb.start_offset)
            _region_block_set = set(region.blocks)
            _outer_handler_entries = []
            if self.cfg.exception_table:
                for entry in self.cfg.exception_table:
                    target = entry.get('target', entry.get('handler_start', None))
                    if target is not None and target not in _existing_handler_offsets:
                        if target >= region.try_offset_end:
                            target_block = self.cfg.get_block_by_offset(target)
                            if (target_block and
                                target_block not in self.generated_blocks and
                                target_block not in _region_block_set):
                                has_push_exc = any(
                                    i.opname == 'PUSH_EXC_INFO'
                                    for i in target_block.instructions
                                )
                                if has_push_exc:
                                    _outer_handler_entries.append(target_block)
            if _outer_handler_entries and handlers:
                # 将内层try body + handlers 包装成嵌套的 Try AST
                _inner_try = {
                    'type': 'Try',
                    'body': body_stmts if body_stmts else [{'type': 'Pass'}],
                    'handlers': handlers,
                }
                body_stmts = [_inner_try]
                # 生成外层 handlers
                handlers = []
                for _outer_block in sorted(_outer_handler_entries, key=lambda b: b.start_offset):
                    if _outer_block in self.generated_blocks:
                        continue
                    _outer_body = self._generate_handler_body_statements(_outer_block)
                    self.generated_blocks.add(_outer_block)
                    for succ in _outer_block.successors:
                        if succ not in self.generated_blocks:
                            succ_has_pop_except = any(
                                i.opname == 'POP_EXCEPT'
                                for i in succ.instructions
                            )
                            if succ_has_pop_except:
                                _succ_stmts = self._generate_handler_body_statements(succ)
                                if _succ_stmts:
                                    _outer_body.extend(_succ_stmts)
                                self.generated_blocks.add(succ)
                    _outer_handler = {
                        'type': 'ExceptHandler',
                        'body': _outer_body if _outer_body else [{'type': 'Pass'}]
                    }
                    handlers.append(_outer_handler)

            orelse_stmts = None
            if region.else_blocks and region.has_else:
                orelse_stmts = []
                for eb in region.else_blocks:
                    if eb in self.generated_blocks:
                        continue
                    nested_region = self.region_analyzer.get_region_for_block(eb)
                    if nested_region and nested_region is not region and isinstance(nested_region, (IfRegion, LoopRegion, TryExceptRegion, WithRegion)):
                        nr_id = id(nested_region)
                        if nr_id not in self._generated_regions and nr_id not in self._generating_regions:
                            nested_ast = self._generate_region(nested_region)
                            if nested_ast:
                                if isinstance(nested_ast, list):
                                    orelse_stmts.extend(nested_ast)
                                else:
                                    orelse_stmts.append(nested_ast)
                            for b in nested_region.blocks:
                                self.generated_blocks.add(b)
                            continue
                    ebs = self._generate_block_statements(eb)
                    if ebs:
                        orelse_stmts.extend(ebs)
                    self.generated_blocks.add(eb)

            finalbody_stmts = None
            if region.finally_blocks and region.has_finally:
                finalbody_stmts = []
                _generated_finally_offsets = set()
                for fb in region.finally_blocks:
                    if fb in self.generated_blocks:
                        continue
                    if fb.start_offset in _generated_finally_offsets:
                        continue
                    fbs = self._generate_handler_body_statements(fb)
                    if fbs:
                        finalbody_stmts.extend(fbs)
                    self.generated_blocks.add(fb)
                    _generated_finally_offsets.add(fb.start_offset)

            for cb in region.cleanup_blocks:
                if cb not in self.generated_blocks:
                    self.generated_blocks.add(cb)

            try_ast = {
                'type': 'Try',
                'body': body_stmts if body_stmts else [{'type': 'Pass'}],
                'handlers': handlers,
            }
            if orelse_stmts:
                try_ast['orelse'] = orelse_stmts
            if finalbody_stmts:
                try_ast['finalbody'] = finalbody_stmts
            elif region.has_finally:
                try_ast['finalbody'] = [{'type': 'Pass'}]

            return try_ast
        finally:
            self._generating_regions.discard(region_id)
            self._generated_regions.add(region_id)
            for block in region.blocks:
                self.generated_blocks.add(block)
            self._try_depth -= 1

    def _generate_handler_body_statements(self, block: BasicBlock) -> List[Dict[str, Any]]:
        handler_instrs = [i for i in block.instructions
                          if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL',
                                               'PUSH_EXC_INFO', 'POP_EXCEPT', 'POP_TOP',
                                               'CHECK_EXC_MATCH', 'CHECK_EG_MATCH',
                                               'WITH_EXCEPT_START')]
        exc_dispatch_jump_offset = None
        for idx, instr in enumerate(block.instructions):
            if instr.opname in ('CHECK_EXC_MATCH', 'CHECK_EG_MATCH'):
                for next_instr in block.instructions[idx + 1:]:
                    if next_instr.opname in ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_FALSE',
                                             'JUMP_IF_FALSE', 'JUMP_IF_TRUE',
                                             'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_TRUE'):
                        exc_dispatch_jump_offset = next_instr.offset
                        break
                    elif next_instr.opname not in ('LOAD_GLOBAL', 'LOAD_NAME', 'LOAD_CONST',
                                                   'LOAD_ATTR', 'LOAD_DEREF'):
                        break
                break
        if exc_dispatch_jump_offset is not None:
            handler_instrs = [i for i in handler_instrs if i.offset > exc_dispatch_jump_offset]
        store_indices = [i for i, instr in enumerate(handler_instrs)
                        if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')]
        if len(store_indices) >= 2:
            return self._generate_block_statements(block)

        stmts: List[Dict[str, Any]] = []
        stmt_instrs: List[Instruction] = []
        skip_initial_pop = True
        skip_offsets: Set[int] = set()
        if exc_dispatch_jump_offset is not None:
            for instr in block.instructions:
                if instr.offset <= exc_dispatch_jump_offset:
                    if instr.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                        skip_offsets.add(instr.offset)

        for instr in block.instructions:
            if instr.offset in skip_offsets:
                continue
            if instr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                continue

            if instr.opname == 'POP_TOP' and skip_initial_pop:
                skip_initial_pop = False
                continue

            if instr.opname == 'POP_EXCEPT':
                remaining_after = block.instructions[block.instructions.index(instr)+1:]
                remaining = [i for i in remaining_after
                            if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                if len(remaining) >= 3:
                    r0, r1, r2 = remaining[0], remaining[1], remaining[2]
                    if (r0.opname == 'LOAD_CONST' and r0.argval is None and
                        r1.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF') and
                        r2.opname in ('DELETE_FAST', 'DELETE_NAME', 'DELETE_GLOBAL', 'DELETE_DEREF')):
                        if stmt_instrs:
                            stmt = self._build_statement(stmt_instrs)
                            if stmt:
                                stmts.append(stmt)
                        stmt_instrs = []
                        skip_initial_pop = True
                        for ri in remaining_after:
                            if ri.opname in ('LOAD_CONST', 'STORE_FAST', 'STORE_NAME',
                                           'STORE_GLOBAL', 'STORE_DEREF', 'DELETE_FAST',
                                           'DELETE_NAME', 'DELETE_GLOBAL', 'DELETE_DEREF'):
                                skip_offsets.add(ri.offset)
                            elif ri.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD',
                                             'JUMP_BACKWARD_NO_INTERRUPT', 'RETURN_VALUE', 'RETURN_CONST'):
                                skip_offsets.add(ri.offset)
                                break
                            else:
                                break
                        continue
                has_return_after = any(i.opname in ('RETURN_VALUE', 'RETURN_CONST')
                                       for i in remaining_after
                                       if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL',
                                                           'LOAD_CONST', 'STORE_FAST', 'STORE_NAME',
                                                           'STORE_DEREF', 'STORE_GLOBAL',
                                                           'DELETE_FAST', 'DELETE_NAME',
                                                           'DELETE_DEREF', 'DELETE_GLOBAL',
                                                           'SWAP', 'POP_TOP', 'COPY'))
                if has_return_after:
                    skip_initial_pop = True
                    continue
                if stmt_instrs:
                    stmt = self._build_statement(stmt_instrs)
                    if stmt:
                        stmts.append(stmt)
                stmt_instrs = []
                skip_initial_pop = True
                continue

            if instr.opname in ('PUSH_EXC_INFO', 'CHECK_EXC_MATCH', 'CHECK_EG_MATCH',
                                'WITH_EXCEPT_START'):
                continue

            if instr.opname == 'RERAISE':
                if stmt_instrs:
                    stmt = self._build_statement(stmt_instrs)
                    if stmt:
                        stmts.append(stmt)
                stmt_instrs = []
                remaining = [i for i in block.instructions[block.instructions.index(instr)+1:]
                            if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                _has_prior_except_stmts = any(
                    i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_DEREF', 'STORE_GLOBAL',
                                 'LOAD_CONST', 'LOAD_FAST', 'LOAD_NAME', 'CALL', 'CALL_FUNCTION',
                                 'BINARY_OP', 'UNARY_OP', 'COMPARE_OP')
                    for i in stmt_instrs
                ) if stmt_instrs else False
                is_cleanup_reraise = (
                    (instr.arg == 1) or
                    (instr.arg == 0 and not remaining and not _has_prior_except_stmts)
                )
                if not is_cleanup_reraise:
                    stmts.append({'type': 'Raise', 'exc': None})
                continue

            if instr.opname == 'RAISE_VARARGS':
                if instr.arg == 0:
                    if stmt_instrs:
                        stmt = self._build_statement(stmt_instrs)
                        if stmt:
                            stmts.append(stmt)
                    stmt_instrs = []
                    stmts.append({'type': 'Raise', 'exc': None})
                else:
                    all_instrs = stmt_instrs + [instr]
                    expr = self.expr_reconstructor.reconstruct(all_instrs)
                    if expr and expr.get('type') == 'Raise':
                        stmts.append(expr)
                    else:
                        exc_expr = None
                        if stmt_instrs:
                            exc_expr = self.expr_reconstructor.reconstruct(stmt_instrs)
                        stmts.append({'type': 'Raise', 'exc': exc_expr})
                stmt_instrs = []
                continue

            if instr.opname == 'COPY' and instr.arg == 1:
                stmt_instrs.append(instr)
                continue

            if instr.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                if self._loop_depth > 0:
                    is_only_load_none = (len(stmt_instrs) == 1 and
                                         stmt_instrs[0].opname == 'LOAD_CONST' and
                                         stmt_instrs[0].argval is None)
                    if is_only_load_none or not stmt_instrs:
                        _in_try_and_loop = (self._try_depth > 0 and self._loop_depth > 0)
                        _block_has_backward_jump = any(
                            i.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')
                            for i in block.instructions
                        )
                        if _in_try_and_loop and _block_has_backward_jump:
                            stmts.append({'type': 'Continue'})
                        else:
                            stmts.append({'type': 'Break'})
                        stmt_instrs = []
                        continue
                if self.cfg.name != '<module>':
                    value_instrs = list(stmt_instrs)
                    if instr.opname == 'RETURN_CONST':
                        value_instrs.append(instr)
                    expr = self.expr_reconstructor.reconstruct(value_instrs) if value_instrs else None
                    if expr and not (expr.get('type') == 'Constant' and expr.get('value') is None):
                        stmts.append({'type': 'Return', 'value': expr})
                        stmt_instrs = []
                        continue
                    elif not value_instrs:
                        stmts.append({'type': 'Return', 'value': None})
                        stmt_instrs = []
                        continue
                if stmt_instrs:
                    is_only_load_none = (len(stmt_instrs) == 1 and
                                         stmt_instrs[0].opname == 'LOAD_CONST' and
                                         stmt_instrs[0].argval is None)
                    if not is_only_load_none:
                        stmt = self._build_statement(stmt_instrs)
                        if stmt:
                            stmts.append(stmt)
                stmt_instrs = []
                continue

            if instr.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'):
                if stmt_instrs:
                    stmt = self._build_statement(stmt_instrs)
                    if stmt:
                        stmts.append(stmt)
                stmt_instrs = []
                if self._loop_depth > 0:
                    _is_implicit_loop_back = False
                    if self._current_loop is not None and instr.argval is not None:
                        _jb_target = self.cfg.get_block_by_offset(instr.argval)
                        if _jb_target is not None and (_jb_target == self._current_loop.header_block or _jb_target == self._current_loop.condition_block):
                            _is_implicit_loop_back = True
                    if not _is_implicit_loop_back:
                        stmts.append({'type': 'Continue'})
                continue

            if instr.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE',
                                 *BACKWARD_JUMP_OPS, *FORWARD_JUMP_OPS):
                if instr.opname in FORWARD_CONDITIONAL_JUMP_OPS and stmt_instrs:
                    cond_expr = self.expr_reconstructor.reconstruct(stmt_instrs)
                    if cond_expr:
                        is_true_jump = 'TRUE' in instr.opname or 'NONE' in instr.opname
                        if is_true_jump:
                            cond_expr = _negate_expr(cond_expr)
                        target_block = self.cfg.get_block_by_offset(instr.argval) if instr.argval is not None else None
                        then_stmts = []
                        else_stmts = []
                        if target_block:
                            _then_succ = None
                            for succ in block.successors:
                                if succ != target_block:
                                    _then_succ = succ
                                    then_stmts = self._generate_block_statements(succ)
                                    self.generated_blocks.add(succ)
                                    break
                            if self._loop_depth > 0 and _then_succ is not None:
                                _then_succ_role = self.region_analyzer.get_block_role(_then_succ)
                                if _then_succ_role in (BlockRole.BREAK, BlockRole.PURE_BREAK):
                                    if not then_stmts or (len(then_stmts) == 1 and then_stmts[0].get('type') == 'Pass'):
                                        then_stmts = [{'type': 'Break'}]
                                    elif then_stmts and then_stmts[-1].get('type') != 'Break':
                                        then_stmts.append({'type': 'Break'})
                            else_stmts = self._generate_block_statements(target_block)
                            self.generated_blocks.add(target_block)
                        if_stmt = {
                            'type': 'If',
                            'test': cond_expr,
                            'body': then_stmts if then_stmts else [{'type': 'Pass'}],
                        }
                        if else_stmts:
                            _suppress_else = False
                            if self._loop_depth > 0 and len(else_stmts) == 1:
                                _es = else_stmts[0]
                                if _es.get('type') == 'Continue':
                                    if target_block and self._current_loop:
                                        _loop_header = self._current_loop.header_block or self._current_loop.condition_block
                                        if _loop_header:
                                            if (target_block.successors and
                                                len(target_block.successors) == 1 and
                                                    target_block.successors[0] == _loop_header):
                                                _suppress_else = True
                                            elif any(i.opname == 'JUMP_BACKWARD' and i.argval == _loop_header.start_offset
                                                     for i in target_block.instructions):
                                                _suppress_else = True
                                    elif target_block and self._loop_depth > 0:
                                        for i in target_block.instructions:
                                            if i.opname == 'JUMP_BACKWARD':
                                                _jb_target = self.cfg.get_block_by_offset(i.argval) if i.argval else None
                                                if _jb_target and self._current_loop:
                                                    if _jb_target == self._current_loop.header_block or _jb_target == self._current_loop.condition_block:
                                                        _suppress_else = True
                                                        break
                            if not _suppress_else:
                                if_stmt['orelse'] = else_stmts
                        stmts.append(if_stmt)
                        stmt_instrs = []
                        continue
                if stmt_instrs:
                    stmt = self._build_statement(stmt_instrs)
                    if stmt:
                        stmts.append(stmt)
                stmt_instrs = []
                if self._loop_depth > 0 and instr.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE'):
                    block_role = self.region_analyzer.get_block_role(block)
                    if block_role in (BlockRole.BREAK, BlockRole.PURE_BREAK):
                        stmts.append({'type': 'Break'})
                continue

            if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                has_copy = any(i.opname == 'COPY' and i.arg == 1 for i in stmt_instrs)
                if has_copy:
                    remaining = block.instructions[block.instructions.index(instr)+1:]
                    next_store_idx = None
                    for ri_idx, ri in enumerate(remaining):
                        if ri.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                            continue
                        if ri.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                            next_store_idx = ri_idx
                            break
                        break
                    if next_store_idx is not None:
                        chained_targets = [{
                            'type': 'Name',
                            'id': instr.argval,
                            'ctx': 'Store',
                            'lineno': instr.starts_line
                        }]
                        skip_remaining = set()
                        for ri_idx, ri in enumerate(remaining):
                            if ri.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                                continue
                            if ri.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                                chained_targets.append({
                                    'type': 'Name',
                                    'id': ri.argval,
                                    'ctx': 'Store',
                                    'lineno': ri.starts_line
                                })
                                skip_remaining.add(ri.offset)
                                continue
                            break
                        value_instrs_no_copy = [i for i in stmt_instrs if i.opname != 'COPY' or i.arg != 1]
                        value = self.expr_reconstructor.reconstruct(value_instrs_no_copy) if value_instrs_no_copy else None
                        if value is not None:
                            stmts.append({
                                'type': 'Assign',
                                'targets': chained_targets,
                                'value': value,
                                'is_chain_assign': True,
                            })
                        stmt_instrs = []
                        skip_offsets.update(skip_remaining)
                        continue
                stmt = self._build_store_statement(stmt_instrs + [instr], block=block)
                if stmt:
                    stmts.append(stmt)
                stmt_instrs = []
                continue

            if instr.opname == 'STORE_SUBSCR':
                stmt = self._build_subscript_assign(stmt_instrs + [instr])
                if stmt:
                    stmts.append(stmt)
                stmt_instrs = []
                continue

            if instr.opname == 'STORE_ATTR':
                stmt = self._build_attr_assign(stmt_instrs + [instr])
                if stmt:
                    stmts.append(stmt)
                stmt_instrs = []
                continue

            stmt_instrs.append(instr)

        if stmt_instrs:
            stmt = self._build_statement(stmt_instrs)
            if stmt:
                stmts.append(stmt)

        return stmts

    def _build_statements_from_instructions(self, instrs: List[Instruction],
                                              block: Optional[BasicBlock] = None) -> List[Dict[str, Any]]:
        if not instrs:
            return []
        stmts = []
        stmt_instrs = []
        for instr in instrs:
            if instr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                continue
            if instr.opname in ('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE',
                                'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE',
                                'POP_JUMP_BACKWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_TRUE',
                                'POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE'):
                break
            if instr.opname in ('POP_EXCEPT', 'PUSH_EXC_INFO', 'RERAISE',
                                'WITH_EXCEPT_START', 'CHECK_EXC_MATCH', 'CHECK_EG_MATCH'):
                continue
            if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                stmt = self._build_store_statement(stmt_instrs + [instr], block=block)
                if stmt:
                    stmts.append(stmt)
                stmt_instrs = []
                continue
            if instr.opname == 'STORE_SUBSCR':
                stmt = self._build_subscript_assign(stmt_instrs + [instr])
                if stmt:
                    stmts.append(stmt)
                stmt_instrs = []
                continue
            if instr.opname == 'STORE_ATTR':
                stmt = self._build_attr_assign(stmt_instrs + [instr])
                if stmt:
                    stmts.append(stmt)
                stmt_instrs = []
                continue
            stmt_instrs.append(instr)
        if stmt_instrs:
            stmt = self._build_statement(stmt_instrs)
            if stmt:
                stmts.append(stmt)
        return stmts

    def _mark_with_cleanup_generated(self, block):
        self._with_cleanup_generated_blocks.add(block)

    def _extract_return_from_exit_block(self, block):
        value_instrs = []
        for instr in block.instructions:
            if instr.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                break
            if instr.opname in ('SWAP', 'POP_TOP', 'LOAD_CONST', 'PRECALL', 'CALL'):
                continue
            value_instrs.append(instr)
        if value_instrs:
            expr = self.expr_reconstructor.reconstruct(value_instrs)
            if expr:
                return expr
        return None

    def _generate_with(self, region: WithRegion) -> Dict[str, Any]:
        """生成with语句的AST节点。

        ╔═══════════════════════════════════════════════════════════════════╗
        ║          WITH区域AST生成算法 - 语法树构建与代码生成             ║
        ╠═══════════════════════════════════════════════════════════════════╣
        ║                                                                    ║
        ║ 【AST节点结构】                                                    ║
        ║ 生成的AST符合Python ast模块规范：                                 ║
        ║                                                                    ║
        ║ ast.With(                                                         ║
        ║     items=[                                                        # with item列表（1个或多个）                         ║
        ║         ast.withitem(                                             ║
        ║             context_expr=ast.Name/Call/...,  # 上下文表达式       ║
        ║             optional_vars=ast.Name/None    # 目标变量（as子句）   ║
        ║         )                                                          ║
        ║     ],                                                             ║
        ║     body=[...],        # with body中的语句列表                    ║
        ║     is_async=False     # 是否为async with (Python 3.5+)           ║
        ║ )                                                                  ║
        ║                                                                    ║
        ║ 示例对应关系：                                                    ║
        ║   源码: with open('f') as f:                                     ║
        ║             data = f.read()                                       ║
        ║                                                                    ║
        ║   AST: With(items=[withitem(context_expr=Call(func=Name('open')),║
        ║                                optional_vars=Name('f'))],           ║
        ║        body=[Assign(targets=[Name('data')],                      ║
        ║                        value=Call(...))])                         ║
        ║                                                                    ║
        ║ 【生成算法步骤】                                                  ║
        ║                                                                    ║
        ║ Step 1: 标记cleanup块（第4678-4696行）                            ║
        ║   目的：确保with的清理机制不生成可见代码                           ║
        ║                                                                    ║
        ║   操作：                                                           ║
        ║   a. 收集所有cleanup块：                                           ║
        ║      - region.cleanup_blocks (通用清理块)                          ║
        ║      - region.exception_blocks (异常处理块)                       ║
        ║      - 将它们加入 with_cleanup_blocks 集合                        ║
        ║   b. 标记这些块为已生成（generated_blocks）：                       ║
        ║      - 后续代码生成时会跳过已生成的块                              ║
        ║   c. 扫描body_end_offset之后的清理块：                             ║
        ║      - 调用 _is_with_exit_cleanup 检测额外的退出清理块           ║
        ║      - 这些块在with语句结束后执行__exit__()清理                   ║
        ║                                                                    ║
        ║   清理块类型及处理策略：                                           ║
        ║   ┌──────────────────┬─────────────┬────────────────────────────┐ ║
        ║   │ 类型              │ 角色标注    │ 处理方式                   │ ║
        ║   ├──────────────────┼─────────────┼────────────────────────────┤ ║
        ║   │ WITH_HANDLER      │ 异常处理器   │ 标记已生成，不输出代码     │ ║
        ║   │ WITH_EXIT_CLEANUP │ 退出清理     │ 标记已生成，不输出代码     │ ║
        ║   │ WITH_STACK_CLEANUP│ 栈清理       │ 标记已生成，不输出代码     │ ║
        ║   └──────────────────┴─────────────┴────────────────────────────┘ ║
        ║                                                                    ║
        ║ Step 2: 生成body语句（第4698-4836行）                             ║
        ║   遍历region.with_blocks，对每个块执行以下逻辑：                   ║
        ║                                                                    ║
        ║   2a. 跳过规则（按优先级）：                                      ║
        ║       ✗ 已生成的块（generated_blocks）                            ║
        ║       ✗ with_cleanup_generated_blocks（之前标记过）              ║
        ║       ✗ LOOP_BACK_EDGE角色（外层循环回边，不是with body内容）    ║
        ║       ✗ PURE_BREAK且含RERAISE（with异常路径的break，非真break）   ║
        ║                                                                    ║
        ║   2b. 嵌套区域处理：                                              ║
        ║       若当前块属于某个嵌套区域（通过get_entry_region_for_block   ║
        ║       或get_region_for_block检测）：                               ║
        ║                                                                    ║
        ║       支持的嵌套区域类型：                                        ║
        ║       - IfRegion: if/elif/else条件块                              ║
        ║       - LoopRegion: for/while循环块                               ║
        ║       - TryExceptRegion: try/except/finally块                     ║
        ║       - WithRegion: 内层with块                                   ║
        ║       - AssertRegion: assert语句块                                ║
        ║                                                                    ║
        ║       处理流程：                                                  ║
        ║       i. 检测orphan指令（identify_with_orphan_instructions）：    ║
        ║          - 嵌套区域前的独立指令（如循环变量的STORE）              ║
        ║          - 对LoopRegion特殊处理：找到GET_ITER之前的表达式指令     ║
        ║       ii. 递归调用 _generate_region 生成嵌套区域的AST            ║
        ║       iii. 跳过目标变量存储（skip_store_targets）：               ║
        ║            - 避免重复生成 `with ctx as f:` 中的f赋值              ║
        ║       iv. 标记嵌套区域的所有块为已生成                            ║
        ║                                                                    ║
        ║   2c. 内层with入口跳过：                                          ║
        ║       若块含BEFORE_WITH/BEFORE_ASYNC_WITH，跳过                  ║
        ║       （由内层WithRegion的_generate_with递归处理）                ║
        ║                                                                    ║
        ║   2d. return语句检测：                                            ║
        ║       调用 _detect_with_body_return 检测with body中的return       ║
        ║       - return需要经过with的__exit__清理路径                      ║
        ║       - 生成Return AST节点并标记相关cleanup块                     ║
        ║                                                                    ║
        ║   2e. 目标变量过滤：                                              ║
        ║       若当前块是with_blocks[0]（body第一个块）且region有target：  ║
        ║       - 找到STORE_FAST/STORE_NAME等目标变量存储指令               ║
        ║       - 从生成的语句中过滤掉该赋值                                ║
        ║       （因为 `as var` 已由with item处理）                        ║
        ║                                                                    ║
        ║   2f. 空语句块的break/continue/return检测：                       ║
        ║       若 _generate_block_statements 返回空列表：                 ║
        ║       遍历后继块检查：                                            ║
        ║       - 是否经过WITH_EXIT_CLEANUP路径到达break（_is_with_exit_   ║
        ║         leading_to_break）                                        ║
        ║       - 是否经过WITH_EXIT_CLEANUP路径到达continue                 ║
        ║       - 是否经过WITH_EXIT_CALL到达return                          ║
        ║       生成对应的Break/Continue/Return AST节点                    ║
        ║                                                                    ║
        ║   控制流路径示例（for + with + break）：                          ║
        ║   for i in range(3):                                              ║
        ║       with ctx:                                                   ║
        ║           if i > 1:                                               ║
        ║               break  # ← 需要经过ctx.__exit__()                  ║
        ║                                                                    ║
        ║   字节码路径：                                                     ║
        ║   [for body] → [if condition] → [break] → [with cleanup]         ║
        ║   → [for cleanup/next iteration]                                  ║
        ║                                                                    ║
        ║ Step 3: 生成子区域（略，在完整代码中处理children）               ║
        ║   - 跳过with cleanup相关的IfRegion（含PUSH_EXC_INFO/             ║
        ║     WITH_EXCEPT_START的条件块）                                    ║
        ║   - 跳过TryExceptRegion（handler含WITH_EXCEPT_START）            ║
        ║   - 其余子区域递归生成                                            ║
        ║                                                                    ║
        ║ Step 4: 生成post-with语句（第4956-4978行）                       ║
        ║   收集with语句结束后的代码：                                       ║
        ║                                                                    ║
        ║   筛选条件：                                                      ║
        ║   a. 块属于region.blocks（在with区域内）                         ║
        ║   b. 块不在with_blocks中（不是body部分）                         ║
        ║   c. 块不在cleanup_blocks中（不是清理部分）                      ║
        ║   d. 块未被生成过                                                 ║
        ║   e. 块start_offset >= body_end_offset（在body之后）             ║
        ║   f. 块不属于其他区域                                             ║
        ║   g. 块不含with相关指令（BEFORE_WITH/WITH_EXCEPT_START等）       ║
        ║   h. 块角色不是cleanup/back_edge/handler                          ║
        ║                                                                    ║
        ║   应用场景：                                                      ║
        ║   with ctx:                                                       ║
        ║       do_something()                                              ║
        ║   post_with_code()  # ← 这行代码在with结束后，但在同一区域内     ║
        ║                                                                    ║
        ║ Step 5: 构建with items（后续代码中处理）                          ║
        ║   从region.items提取：                                           ║
        ║   - context_expr: 上下文表达式（通过expr_reconstructor重建）     ║
        ║   - optional_vars: 目标变量名（None表示无as子句）                 ║
        ║                                                                    ║
        ║   多上下文示例：                                                  ║
        ║   with A as a, B as b:  # items长度为2                           ║
        ║       pass                                                         ║
        ║                                                                    ║
        ║ Step 6: 组装结果                                                  ║
        ║   最终AST结构：{                                                   ║
        ║     'type': 'With',                                               ║
        ║     'items': [...],          # Step 5生成                        ║
        ║     'body': [...],          # Step 2生成                        ║
        ║     'is_async': bool,       # 来自region.is_async               ║
        ║     'pre_stmts': [...],     # orphan指令（Step 2b-i）            ║
        ║     'post_with_stmts': [...] # Step 4生成                       ║
        ║   }                                                                ║
        ║                                                                    ║
        ║ 【关键约束与不变量】                                              ║
        ║ 1. cleanup块不可见性：                                            ║
        ║    with的__enter__/__exit__协议对用户透明                        ║
        ║    所有清理块只标记为已生成，不输出到源代码                      ║
        ║                                                                    ║
        ║ 2. 控制流完整性：                                                 ║
        ║    break/continue/return必须正确经过cleanup路径                  ║
        ║    否则会导致资源泄漏或异常处理错误                              ║
        ║                                                                    ║
        ║ 3. 变量赋值唯一性：                                               ║
        ║    `as var` 的赋值只出现在with item中                            ║
        ║    body中不再重复生成该赋值语句                                  ║
        ║                                                                    ║
        ║ 4. 嵌套区域独立性：                                               ║
        ║    每个嵌套区域（If/Loop/Try/With）独立递归生成                  ║
        ║    避免重复生成或遗漏                                            ║
        ║                                                                    ║
        ║ 【边界条件处理】                                                  ║
        ║                                                                    ║
        ║ 1. 空with body:                                                  ║
        ║    with ctx: pass                                                ║
        ║    → body生成空列表或包含pass语句                                ║
        ║                                                                    ║
        ║ 2. with + else (Python 3.9+):                                    ⚠️ 不常见
        ║    while/for支持else，但with本身不支持else                        ║
        ║    （测试案例w21withelse可能是其他结构的组合）                    ║
        ║                                                                    ║
        ║ 3. 嵌套with的orphan指令：                                        ║
        ║    外层with body开头可能有内层with不需要的指令                    ║
        ║    通过 identify_with_orphan_instructions 提取并单独生成        ║
        ║                                                                    ║
        ║ 4. async with的特殊性：                                          ⚠️ 已知问题
        ║    - is_async标志传递给AST节点                                    ║
        ║    - code_generator使用 async with 语法                          ║
        ║    - 但嵌套code object的重建可能不准确                            ║
        ║    - 导致test_w058等async with测试失败                           ║
        ║                                                                    ║
        ║ 【与其他生成方法的交互】                                          ║
        ║ 调用关系图：                                                      ║
        ║   _generate_region()                                             ║
        ║     └─ _generate_with()  ← 本方法                               ║
        ║          ├─ _generate_block_statements()  # 生成普通语句        ║
        ║          ├─ _generate_region()  # 递归生成嵌套区域              ║
        ║          │   ├─ _generate_if()                                  ║
        ║          │   ├─ _generate_for/_generate_while                   ║
        ║          │   ├─ _generate_try()                                 ║
        ║          │   └─ _generate_with()  # 递归（内层with）            ║
        ║          ├─ _build_statements_from_instructions()  # orphan指令  ║
        ║          └─ expr_reconstructor.reconstruct_expression() # 表达式 ║
        ║                                                                    ║
        ║ 【性能特征】                                                      ║
        ║ 时间复杂度: O(B * S)                                              ║
        ║   B = with_body块数量                                            ║
        ║   S = 平均每块生成的语句数                                       ║
        ║ 空间复杂度: O(B + S) (存储生成的AST节点)                         ║
        ║                                                                    ║
        ║ 【已知限制】                                                      ║
        ║ ⚠️ 1. async with + 嵌套code object (test_w058)                  ║
        ║      指令数: 原始43 vs 重编28 (-15条，-35%)                      ║
        ║      问题: 异步协议的SEND/YIELD循环被错误简化                    ║
        ║      影响: 低（async with使用频率相对较低）                       ║
        ║                                                                    ║
        ║ ⚠️ 2. with + break/continue (test_w079/w080)                     ║
        ║      指令数: 原始41 vs 重编32 (-9条，-22%)                       ║
        ║             原始38 vs 重编39 (+1条，+3%)                         ║
        ║      问题: 控制流路径计数不一致，可能遗漏或重复计数cleanup块    ║
        ║      影响: 中（循环+with是常见模式）                              ║
        ║                                                                    ║
        ║ ⚠️ 3. with + try/except/finally (test_w102)                      ║
        ║      指令数: 原始54 vs 重编59 (+5条，+9%)                        ║
        ║      问题: try-except的异常处理与with cleanup混淆               ║
        ║      导致额外生成了函数调用指令                                   ║
        ║      影响: 中（错误处理代码常用此模式）                           ║
        ║                                                                    ║
        ║ ⚠️ 4. 自定义上下文管理器 + 类定义 (test_w30)                     ║
        ║      指令数: 原始35 vs 重编38 (+3条，+9%)                        ║
        ║      问题: LOAD_BUILD_CLASS/MAKE_FUNCTION等元类操作顺序不准     ║
        ║      影响: 低（自定义context manager较少直接在with中使用类定义）  ║
        ║                                                                    ║
        ║ 【优化建议（Phase 4+）】                                          ║
        ║ 1. 引入async with专用的code object重建逻辑                       ║
        ║    - 正确处理GET_AWAITABLE/SEND/YIELD_VALUE的循环模式           ║
        ║    - 参考CPython编译器的异步协议实现                              ║
        ║                                                                    ║
        ║ 2. 统一控制流路径计数机制                                        ║
        ║    - 为break/continue/return建立统一的路径跟踪器                ║
        ║    - 确保cleanup路径不被遗漏或重复计数                            ║
        ║    - 可参考Phase 2对TryExceptRegion的成功修复经验               ║
        ║                                                                    ║
        ║ 3. 强化with与try的边界检测                                       ║
        ║    - 使用异常表的depth信息精确区分                               ║
        ║    - 建立with-cleanup与try-handler的严格分离规则                ║
        ║                                                                    ║
        ║ 4. 类定义+实例化的原子化处理                                     ║
        ║    - 将LOAD_BUILD_CLASS→MAKE_FUNCTION→CALL识别为原子单元        ║
        ║    - 保持其相对顺序不变                                          ║
        ║                                                                    ║
        ╚═══════════════════════════════════════════════════════════════════╝
        """
        region_id = id(region)
        self._generating_regions.add(region_id)

        try:
            entry = region.entry

            with_cleanup_blocks = set()
            if hasattr(region, 'cleanup_blocks'):
                with_cleanup_blocks.update(region.cleanup_blocks)
            if hasattr(region, 'exception_blocks'):
                with_cleanup_blocks.update(region.exception_blocks)
            for cb in with_cleanup_blocks:
                self.generated_blocks.add(cb)
            body_end_offset = region.body_offset_end if region.body_offset_end is not None and region.body_offset_end > 0 else 0
            if body_end_offset > 0:
                for blk in sorted(self.cfg.blocks.values(), key=lambda b: b.start_offset):
                    if blk.start_offset < body_end_offset:
                        continue
                    if blk in with_cleanup_blocks:
                        continue
                    if blk in self.generated_blocks:
                        continue
                    if self.region_analyzer._is_with_exit_cleanup(blk):
                        self.generated_blocks.add(blk)
                        with_cleanup_blocks.add(blk)

            body_stmts = []
            for block in region.with_blocks:
                if block in self.generated_blocks:
                    continue
                if block in self._with_cleanup_generated_blocks:
                    self.generated_blocks.add(block)
                    continue
                if self.region_analyzer.get_block_role(block) == BlockRole.WITH_EXIT_CLEANUP:
                    self.generated_blocks.add(block)
                    continue
                # 跳过属于外层循环的回边块（with-in-for情况）
                # 这些JUMP_BACKWARD块是外层for/while循环的一部分，不是with body的内容
                if self.region_analyzer.get_block_role(block) == BlockRole.LOOP_BACK_EDGE:
                    self.generated_blocks.add(block)
                    continue
                # 跳过with清理机制中的PURE_BREAK块（包含RERAISE指令）
                # 这些块是with异常处理路径的一部分，不是真正的break语句
                if self.region_analyzer.get_block_role(block) == BlockRole.PURE_BREAK:
                    has_reraise = any(i.opname == 'RERAISE' for i in block.instructions)
                    if has_reraise:
                        self.generated_blocks.add(block)
                        continue

                nested_region = self.region_analyzer.get_entry_region_for_block(block)
                if not nested_region:
                    nested_region = self.region_analyzer.get_region_for_block(block)
                if nested_region and nested_region != region and nested_region is not region.parent and isinstance(nested_region, (IfRegion, LoopRegion, TryExceptRegion, WithRegion, AssertRegion)):
                    if nested_region.entry == block or (hasattr(nested_region, 'condition_block') and nested_region.condition_block == block):
                        if isinstance(nested_region, WithRegion) and nested_region.entry == block:
                            pre_instrs = self.region_analyzer.identify_block_prefix_instructions(block)
                            if pre_instrs:
                                pre_stmts = self._build_statements_from_instructions(pre_instrs, block)
                                if pre_stmts:
                                    body_stmts.extend(pre_stmts)
                        skip_targets = set()
                        if region.target and isinstance(nested_region, LoopRegion):
                            skip_targets.add(region.target)
                        generated = self._generate_region(nested_region, skip_store_targets=skip_targets)
                        if generated:
                            if isinstance(generated, list):
                                body_stmts.extend(generated)
                            else:
                                body_stmts.append(generated)
                        for b in nested_region.blocks:
                            self.generated_blocks.add(b)
                        if hasattr(nested_region, 'condition_block') and nested_region.condition_block:
                            self.generated_blocks.add(nested_region.condition_block)
                        if hasattr(nested_region, 'header_block') and nested_region.header_block:
                            self.generated_blocks.add(nested_region.header_block)
                        continue
                    elif block in nested_region.blocks:
                        if id(nested_region) not in self._generated_regions:
                            if isinstance(nested_region, LoopRegion):
                                pre_instrs = self.region_analyzer.identify_block_prefix_instructions(block)
                                if pre_instrs:
                                    pre_stmts = self._build_statements_from_instructions(pre_instrs, block)
                                    if pre_stmts:
                                        body_stmts.extend(pre_stmts)
                            skip_targets = set()
                            if region.target and isinstance(nested_region, LoopRegion):
                                skip_targets.add(region.target)
                            generated = self._generate_region(nested_region, skip_store_targets=skip_targets)
                            if generated:
                                if isinstance(generated, list):
                                    body_stmts.extend(generated)
                                else:
                                    body_stmts.append(generated)
                            for b in nested_region.blocks:
                                self.generated_blocks.add(b)
                            if hasattr(nested_region, 'condition_block') and nested_region.condition_block:
                                self.generated_blocks.add(nested_region.condition_block)
                            if hasattr(nested_region, 'header_block') and nested_region.header_block:
                                self.generated_blocks.add(nested_region.header_block)
                            continue
                        orphan_instrs = self.region_analyzer.identify_with_orphan_instructions(block, region, nested_region)
                        if orphan_instrs:
                            orphan_stmts = self._build_statements_from_instructions(orphan_instrs, block)
                            if orphan_stmts:
                                body_stmts.extend(orphan_stmts)
                        self.generated_blocks.add(block)
                        continue

                if any(instr.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH') for instr in block.instructions):
                    self.generated_blocks.add(block)
                    continue

                return_info = self.region_analyzer._detect_with_body_return(block, region, self.expr_reconstructor)
                if return_info is not None:
                    body_stmts.append(return_info)
                    self.generated_blocks.add(block)
                    self._mark_with_cleanup_generated(block)
                    continue

                target_store_offset = None
                if region.target and block == region.with_blocks[0]:
                    for instr in block.instructions:
                        if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                            if instr.argval == region.target:
                                target_store_offset = instr.offset
                                break

                stmts = self._generate_block_statements(block)
                if target_store_offset is not None:
                    stmts = [s for s in stmts
                             if not (s.get('type') == 'Assign' and
                                     s.get('target', {}).get('id') == region.target)]

                if not stmts:
                    _break_visited = set()
                    _continue_visited = set()
                    for succ in block.successors:
                        _succ_role = self.region_analyzer.get_block_role(succ)
                        _is_cleanup_path = _succ_role in (BlockRole.WITH_EXIT_CLEANUP, BlockRole.WITH_STACK_CLEANUP, BlockRole.WITH_HANDLER)
                        if _is_cleanup_path and self._current_loop is not None:
                            if self.region_analyzer._is_with_exit_leading_to_break(succ, self._current_loop, _break_visited):
                                stmts = [{'type': 'Break'}]
                                self._mark_with_cleanup_generated(succ)
                                break
                            if self.region_analyzer._is_with_exit_leading_to_continue(succ, self._current_loop, _continue_visited):
                                stmts = [{'type': 'Continue'}]
                                self._mark_with_cleanup_generated(succ)
                                break
                            continue
                        if self.region_analyzer._is_with_exit_leading_to_break(succ, self._current_loop, _break_visited):
                            stmts = [{'type': 'Break'}]
                            self._mark_with_cleanup_generated(succ)
                            break
                        if self.region_analyzer._is_with_exit_leading_to_continue(succ, self._current_loop, _continue_visited):
                            stmts = [{'type': 'Continue'}]
                            self._mark_with_cleanup_generated(succ)
                            break
                        has_return = any(i.opname in ('RETURN_VALUE', 'RETURN_CONST') for i in succ.instructions)
                        has_exit_call = self.region_analyzer.get_block_role(succ) is BlockRole.WITH_EXIT_CALL
                        if has_return and has_exit_call:
                            return_value = self._extract_return_from_exit_block(succ)
                            stmts = [{'type': 'Return', 'value': return_value}]
                            self._mark_with_cleanup_generated(succ)
                            break

                if stmts and len(stmts) > 0:
                    last_stmt = stmts[-1]
                    if last_stmt.get('type') == 'Expr':
                        has_return_successor = False
                        for succ in block.successors:
                            has_swap = any(i.opname == 'SWAP' for i in succ.instructions)
                            has_return = any(i.opname in ('RETURN_VALUE', 'RETURN_CONST') for i in succ.instructions)
                            has_exit_call = self.region_analyzer.get_block_role(succ) is BlockRole.WITH_EXIT_CALL
                            if (has_swap and has_return) or (has_return and has_exit_call):
                                has_return_successor = True
                                self._mark_with_cleanup_generated(succ)
                                break
                        if has_return_successor:
                            stmts[-1] = {'type': 'Return', 'value': last_stmt.get('value')}

                body_stmts.extend(stmts)
                self.generated_blocks.add(block)

            for child in region.children:
                if isinstance(child, (TryExceptRegion, IfRegion, LoopRegion, WithRegion)):
                    """
                    【反编译逻辑】With语句子区域处理扩展（Phase 35 统一框架）
                    
                    ═══════════════════════════════════════════════════════════════════════════════
                    1. 功能概述:
                    ─────────────────────
                    本代码段实现 with 语句体内的子区域生成与嵌套，是 Phase 35 统一子区域
                    处理框架的组成部分。与 if/try/match 中的子区域处理保持一致的模式。
                    
                    **支持的区域类型**:
                    - TryExceptRegion: with 体中的 try-except-finally 块
                    - IfRegion: with 体中的 if/elif/else 条件块
                    - LoopRegion: with 体中的 for/while 循环块
                    - WithRegion: 嵌套的 with 语句（上下文管理器嵌套）
                    
                    2. 过滤机制（防止重复和冲突）:
                    ────────────────────────────────
                    
                    **过滤规则A: WithCleanup If 检测**
                    ```python
                    if isinstance(child, IfRegion):
                        _is_with_cleanup_if = False
                        if hasattr(child, 'condition_block') and child.condition_block:
                            # 检查条件块是否包含异常处理指令
                            if any(i.opname in ('PUSH_EXC_INFO', 'WITH_EXCEPT_START') 
                                   for i in child.condition_block.instructions):
                                _is_with_cleanup_if = True
                        
                        if _is_with_cleanup_if:
                            # 这是with清理生成的伪if，跳过
                            for b in child.blocks:
                                self.generated_blocks.add(b)
                            continue
                    ```
                    
                    **原因**: CPython 为 with 语句生成的 cleanup 代码可能包含类似 if 的结构，
                    但这不是用户写的 if 语句，而是编译器生成的异常处理路径。
                    
                    **特征指令**:
                    - PUSH_EXC_INFO: 异常信息压栈（异常处理标志）
                    - WITH_EXCEPT_START: with 异常处理开始
                    
                    **过滤规则B: WithCleanup Try 检测**
                    ```python
                    if isinstance(child, TryExceptRegion):
                        _is_with_cleanup_try = False
                        if hasattr(child, 'handler_entry_blocks') and child.handler_entry_blocks:
                            for hb in child.handler_entry_blocks:
                                # 检查handler入口是否包含with异常处理指令
                                if any(i.opname == 'WITH_EXCEPT_START' for i in hb.instructions):
                                    _is_with_cleanup_try = True
                                    break
                        
                        if _is_with_cleanup_try:
                            # 这是with清理生成的伪try，跳过
                            for b in child.blocks:
                                self.generated_blocks.add(b)
                            continue
                    ```
                    
                    **原因**: 类似规则A，针对 try-except 结构的清理代码。
                    
                    3. 子区域生成流程:
                    ────────────────────────────────
                    ```python
                    # 检查是否已生成（避免重复）
                    child_entry_generated = (child.entry in self.generated_blocks and 
                                             child.entry != region.entry)
                    child_handler_generated = False
                    
                    # 特殊检查TryExceptRegion的handler
                    if isinstance(child, TryExceptRegion) and child.handler_entry_blocks:
                        child_handler_generated = any(
                            b in self.generated_blocks 
                            for b in child.handler_entry_blocks
                        )
                    
                    # 只有未生成的子区域才需要处理
                    if not child_entry_generated and not child_handler_generated:
                        generated = self._generate_region(child)
                        
                        if generated:
                            if isinstance(generated, list):
                                body_stmts.extend(generated)  # 多个语句
                            else:
                                body_stmts.append(generated)  # 单个节点
                    ```
                    
                    4. 典型应用场景:
                    ─────────────────────
                    ```python
                    # 场景1: with中的循环
                    with open('file.txt') as f:
                        for line in f:           # LoopRegion 作为 WithRegion 的子区域
                            process(line)
                    
                    # 场景2: with中的条件判断
                    with context_manager():
                        if condition:             # IfRegion 作为 WithRegion 的子区域
                            do_something()
                    
                    # 场景3: with中的try（复杂资源管理）
                    with resource():
                        try:                      # TryExceptRegion 作为子区域
                            risky_operation()
                        except Error:
                            handle_error()
                    
                    # 场景4: 嵌套with
                    with outer():
                        with inner():            # 内层WithRegion作为外层的子区域
                            do_work()
                    ```
                    
                    5. 字节码结构与区域映射:
                    ────────────────────────────────
                    ```python
                    # 源码:
                    with ctx_manager() as var:
                        if condition:
                            action()
                        else:
                            alternative()
                    
                    # 区域层次:
                    WithRegion (entry=with_setup_block)
                    ├── body_blocks=[if_cond_block, then_blocks..., else_blocks...]
                    ├── children=[
                    │     IfRegion (condition_block=if_cond_block)
                    │     ├── then_blocks=[action_block]
                    │     └── else_blocks=[alt_block]
                    │   ]
                    └── cleanup_blocks=[cleanup...]  # __exit__调用
                    
                    # 生成过程:
                    _generate_with(with_region):
                      → 生成with头部: "with ctx_manager() as var:"
                      → 遍历body_blocks
                      → 发现if_cond_block属于IfRegion
                      → 调用_generate_region(if_region)
                      → 生成完整的if-else AST
                      → 插入到body_stmts
                      → 生成with清理代码
                    ```
                    
                    6. 与其他方法的统一性:
                    ────────────────────────────────
                    本实现在以下方面与其他子区域处理保持一致：
                    
                    ✅ 相同的防重复机制（_generated_regions集合）
                    ✅ 相同的类型检查模式（isinstance链式判断）
                    ✅ 相同的结果插入方式（extend/list/append）
                    ✅ 相同的特殊情况过滤（cleanup检测）
                    
                    不同点：
                    ⚠️ 额外的WithCleanup过滤（with特有的伪结构问题）
                    ⚠️ handler入口的特殊检查（TryExceptRegion）
                    
                    7. 已知限制与改进方向:
                    ────────────────────────────────
                    - ❌ 深度嵌套（>4层）可能导致性能下降
                    - ⚠️ with中的生成器/异步迭代器可能产生意外结构
                    - 🔮 未来改进: 更智能的cleanup检测（基于数据流分析）
                    
                    ═══════════════════════════════════════════════════════════════════════════════
                    """
                    if isinstance(child, IfRegion):
                        _is_with_cleanup_if = False
                        if hasattr(child, 'condition_block') and child.condition_block:
                            if any(i.opname in ('PUSH_EXC_INFO', 'WITH_EXCEPT_START') for i in child.condition_block.instructions):
                                _is_with_cleanup_if = True
                        if _is_with_cleanup_if:
                            for b in child.blocks:
                                self.generated_blocks.add(b)
                            continue
                    if isinstance(child, TryExceptRegion):
                        _is_with_cleanup_try = False
                        if hasattr(child, 'handler_entry_blocks') and child.handler_entry_blocks:
                            for hb in child.handler_entry_blocks:
                                if any(i.opname == 'WITH_EXCEPT_START' for i in hb.instructions):
                                    _is_with_cleanup_try = True
                                    break
                        if _is_with_cleanup_try:
                            for b in child.blocks:
                                self.generated_blocks.add(b)
                            continue
                    child_entry_generated = child.entry in self.generated_blocks and child.entry != region.entry
                    child_handler_generated = False
                    if isinstance(child, TryExceptRegion) and child.handler_entry_blocks:
                        child_handler_generated = any(b in self.generated_blocks for b in child.handler_entry_blocks)
                    if not child_entry_generated and not child_handler_generated:
                        generated = self._generate_region(child)
                        if generated:
                            if isinstance(generated, list):
                                body_stmts.extend(generated)
                            else:
                                body_stmts.append(generated)
                        for b in child.blocks:
                            self.generated_blocks.add(b)
                # 反编译逻辑：处理with语句体中的TernaryRegion/BoolOpRegion子区域
                # 根因：这些表达式级区域可以嵌入任何语句级区域（if/with/try/match）体内
                # 归约顺序：内层（ternary/boolop）先识别、外层（with）后处理
                # 符合度：TernaryRegion→IfExp(Expr), BoolOpRegion→BoolOp(Expr)
                elif isinstance(child, (TernaryRegion, BoolOpRegion)):
                    child_id = id(child)
                    if child_id not in self._generated_regions and child_id not in self._generating_regions:
                        if isinstance(child, TernaryRegion):
                            child_ast = self._generate_ternary(child)
                        else:
                            child_ast = self._generate_boolop(child)
                        if child_ast:
                            if isinstance(child_ast, list):
                                body_stmts.extend(child_ast)
                            else:
                                body_stmts.append(child_ast)
                        for b in child.blocks:
                            self.generated_blocks.add(b)
                        self._generated_regions.add(child_id)

            post_with_stmts = []
            body_end_offset = region.body_offset_end if region.body_offset_end is not None and region.body_offset_end > 0 else 0
            with_cleanup_blocks = set()
            if hasattr(region, 'cleanup_blocks'):
                with_cleanup_blocks.update(region.cleanup_blocks)
            if hasattr(region, 'exception_blocks'):
                with_cleanup_blocks.update(region.exception_blocks)
            if body_end_offset > 0:
                for blk in sorted(region.blocks, key=lambda b: b.start_offset):
                    if blk.start_offset < body_end_offset:
                        continue
                    if blk in region.with_blocks or blk == region.entry:
                        continue
                    if blk in self.generated_blocks:
                        continue
                    if blk in with_cleanup_blocks:
                        self.generated_blocks.add(blk)
                        continue
                    blk_role = self.region_analyzer.get_block_role(blk)
                    if blk_role in (BlockRole.WITH_EXIT_CLEANUP, BlockRole.WITH_STACK_CLEANUP, BlockRole.WITH_HANDLER):
                        if blk_role == BlockRole.WITH_EXIT_CLEANUP:
                            self.generated_blocks.add(blk)
                            continue
                        has_real_code = any(
                            instr.opname in ('LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_NAME', 'LOAD_ATTR', 'LOAD_METHOD',
                                            'STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
                                            'BINARY_OP', 'UNARY_OP', 'COMPARE_OP', 'IS_OP', 'CONTAINS_OP',
                                            'BUILD_TUPLE', 'BUILD_LIST', 'BUILD_MAP', 'BUILD_SET', 'BUILD_STRING',
                                            'IMPORT_NAME', 'IMPORT_FROM', 'LOAD_BUILD_CLASS',
                                            'GET_ITER', 'GET_AITER', 'FOR_ITER', 'YIELD_VALUE')
                            for instr in blk.instructions
                            if instr.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')
                        )
                        if not has_real_code:
                            self.generated_blocks.add(blk)
                            continue
                    if self.block_role(blk) == BlockRole.WITH_EXIT_CLEANUP:
                        self.generated_blocks.add(blk)
                        continue
                    if self.block_role(blk) == BlockRole.LOOP_BACK_EDGE:
                        self.generated_blocks.add(blk)
                        continue
                    if self.block_role(blk) == BlockRole.PURE_BREAK:
                        has_reraise = any(i.opname == 'RERAISE' for i in blk.instructions)
                        if has_reraise:
                            self.generated_blocks.add(blk)
                            continue
                    if any(instr.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH') for instr in blk.instructions):
                        self.generated_blocks.add(blk)
                        continue
                    in_child_region = False
                    for child in region.children:
                        if blk in child.blocks:
                            in_child_region = True
                            break
                    if in_child_region:
                        continue
                    post_stmts = self._generate_block_statements(blk)
                    if not post_stmts:
                        has_return = any(i.opname in ('RETURN_VALUE', 'RETURN_CONST') for i in blk.instructions)
                        if has_return:
                            return_ast = self._generate_return_ast(blk)
                            if return_ast:
                                post_stmts = [return_ast]
                    post_with_stmts.extend(post_stmts)
                    self.generated_blocks.add(blk)
                for blk in sorted(self.cfg.blocks.values(), key=lambda b: b.start_offset):
                    if blk in region.blocks:
                        continue
                    if blk in self.generated_blocks:
                        continue
                    if blk.start_offset < body_end_offset:
                        continue
                    blk_region = self.region_analyzer.get_region_for_block(blk)
                    if blk_region is not None and blk_region is not region:
                        continue
                    if any(instr.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH', 'WITH_EXCEPT_START',
                                           'PUSH_EXC_INFO', 'RERAISE', 'POP_EXCEPT') for instr in blk.instructions):
                        continue
                    if self.region_analyzer.get_block_role(blk) in (BlockRole.WITH_EXIT_CLEANUP,
                                                                     BlockRole.WITH_STACK_CLEANUP,
                                                                     BlockRole.WITH_HANDLER,
                                                                     BlockRole.LOOP_BACK_EDGE):
                        continue
                    post_stmts = self._generate_block_statements(blk)
                    if post_stmts:
                        post_with_stmts.extend(post_stmts)
                        self.generated_blocks.add(blk)

            for block in region.blocks:
                self.generated_blocks.add(block)

            items = []
            pre_stmts = []
            for context_instrs, target in region.items:
                    if context_instrs:
                        import_instrs = []
                        expr_instrs = []
                        i = 0
                        while i < len(context_instrs):
                            instr = context_instrs[i]
                            if instr.opname == 'IMPORT_NAME':
                                import_instrs.append(instr)
                                i += 1
                            elif instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL') and import_instrs:
                                import_instrs.append(instr)
                                i += 1
                            else:
                                expr_instrs.extend(context_instrs[i:])
                                break
                        for imp_instr in import_instrs:
                            if imp_instr.opname == 'IMPORT_NAME':
                                import_stmt = {
                                    'type': 'Import',
                                    'names': [{'name': imp_instr.argval, 'asname': None}],
                                }
                                pre_stmts.append(import_stmt)
                        expr = self.expr_reconstructor.reconstruct(expr_instrs) if expr_instrs else None
                        context_expr = expr if expr else {'type': 'Call', 'func': {'type': 'Name', 'id': 'context'}, 'args': [], 'keywords': []}
                    else:
                        context_expr = {'type': 'Call', 'func': {'type': 'Name', 'id': 'context'}, 'args': [], 'keywords': []}

                    item = {
                        'context_expr': context_expr,
                    }
                    if target:
                        item['optional_vars'] = {'type': 'Name', 'id': target, 'ctx': 'Store'}
                    items.append(item)

            with_ast = {
                'type': 'AsyncWith' if region.is_async else 'With',
                'items': items,
                'body': body_stmts if body_stmts else [{'type': 'Pass'}],
            }
            result_parts = []
            if pre_stmts:
                result_parts.extend(pre_stmts)
            result_parts.append(with_ast)
            if post_with_stmts:
                result_parts.extend(post_with_stmts)
            if len(result_parts) == 1:
                return result_parts[0]
            return result_parts
        finally:
            self._generating_regions.discard(region_id)
            self._generated_regions.add(region_id)



    def _generate_match(self, region: MatchRegion) -> Dict[str, Any]:
        """生成match-case语句的AST节点

        反编译逻辑概述：
        ====================

        核心任务：将MatchRegion数据结构转换为ast.Match节点（字典格式）

        输入: MatchRegion（由_identify_match_regions创建）
          - subject_block: 包含subject表达式的块
          - case_blocks: case模式块列表
          - case_patterns: 已解析的pattern字典列表
          - case_guards: guard表达式列表（可能为None）
          - case_bodies: case体块列表（每个是块的列表）
          - merge_block: 所有case体的汇合点
          - case_body_start_indices: 每个case body在块内的起始指令索引

        输出: ast.Match节点字典
          {
            'type': 'Match',
            'subject': <expr>,      # subject表达式
            'cases': [              # Case节点列表
              {
                'type': 'Case',
                'pattern': <pattern>,  # pattern表达式
                'guard': <expr>|None,  # guard条件（可选）
                'body': [<stmts>],     # case体语句列表
              },
              ...
            ]
          }

        生成流程详解：
        =============

        Phase 1: Subject表达式提取（第5303-5361行）
        ------------------------------------------
        目标：从subject_block中提取match subject的表达式

        关键挑战：
        - subject_block同时包含subject加载和第一个case的pattern匹配代码
        - 需要精确分离subject指令和pattern指令

        分离策略（基于match类型）：

        【情况A】结构型模式（MATCH_CLASS/SEQUENCE/MAPPING等）:
          字节码示例:
            RESUME
            LOAD_FAST 'x'           ← subject（停止点之前）
            COPY                    ← pattern开始
            MATCH_CLASS Point (x, y)
            ...

          分离规则：
          - 遇到MATCH_*操作码时停止
          - LOAD_FAST/LOAD_NAME/LOAD_GLOBAL通常是subject
          - 特殊处理：LOAD_GLOBAL + LOAD_CONST(tuple) + MATCH_CLASS组合
            （这是带类型参数的class pattern）

        【情况B】字面量模式（COPY + COMPARE_OP/IS_OP）:
          字节码示例:
            RESUME
            LOAD_FAST 'x'           ← subject
            COPY                    ← pattern开始（停止点）
            LOAD_CONST 1
            COMPARE_OP ==
            POP_JUMP_IF_FALSE -> next_case

          分离规则：
          - 遇到COPY操作码时停止（COPY是字面量模式的标志）
          - 如果LOAD_CONST后紧跟COMPARE_OP/IS_OP，则LOAD_CONST也是pattern
          - 特殊情况：case None模式没有COPY，遇到POP_JUMP_IF_NOT_NONE时停止

        【情况C】case None特殊模式:
          字节码示例:
            RESUME
            LOAD_FAST 'x'           ← subject
            POP_JUMP_IF_NOT_NONE    ← None检查（停止点）

          识别方法：
          - 第一个pattern是MatchAs包含MatchSingleton(None)
          - 停止点是POP_JUMP_IF_NOT_NONE而非COPY

        实现细节（第5331-5358行）:
        ```python
        for idx, instr in enumerate(subject_block.instructions):
            # 跳过噪音指令
            if instr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                continue

            # 结构型模式：遇MATCH_*停止
            if instr.opname in MATCH_OPS:
                break

            if is_literal_match:
                # 字面量模式：遇COPY/COMPARE_OP/IS_OP停止
                if instr.opname in PATTERN_STARTERS:
                    break
                # LOAD_CONST + COMPARE_OP/IS_OP 组合也是pattern
                if instr.opname == 'LOAD_CONST':
                    if next_instr.opname in ('COMPARE_OP', 'IS_OP'):
                        break
                # case None特殊情况
                if instr.opname in POP_JUMP_IF_NOT_NONE_OPS:
                    break
            else:
                # 结构型模式的LOAD_GLOBAL + LOAD_CONST(tuple) + MATCH_CLASS
                if instr.opname in ('LOAD_NAME', 'LOAD_GLOBAL'):
                    rest = instructions[idx+1:]
                    if is_class_pattern_with_type_params(rest):
                        break
                # 其他PATTERN_INSTRS继续（可能是复杂的subject表达式）
                if instr.opname in PATTERN_INSTRS and instr.opname != 'LOAD_FAST':
                    continue

            subject_instrs.append(instr)  # 这是subject的一部分
        ```

        提取完成后，调用expr_reconstructor.reconstruct()将指令列表转换为表达式AST

        Phase 2: Case节点生成（第5363-5539行）
        --------------------------------------
        对每个case（i from 0 to num_cases-1）:

        Step 2.1: 获取pattern和guard
          - pattern: 从region.case_patterns[i]获取（已解析的字典格式）
          - guard: 从region.case_guards[i]获取（可能为None）
          - body_blocks: 从region.case_bodies[i]获取（块列表）

        Step 2.2: 收集guard相关的pattern块（_collect_guard_pattern_blocks）
          目标：识别哪些块属于guard条件的计算，不应出现在body中

          guard的字节码特征：
          ```
          pattern matching code...
          STORE_FAST var1, var2, ...   # 存储pattern变量
          <guard expression calculation>
          LOAD_FAST var1               # 使用pattern变量
          LOAD_CONST 0
          COMPARE_OP >                 # 比较
          POP_JUMP_IF_FALSE -> next_case  # guard失败跳转
          JUMP_FORWARD -> body_entry    # guard成功进入body
          ```

          _collect_guard_pattern_blocks返回应该跳过的块集合

        Step 2.3: 遍历body块，生成语句
          对body中的每个block，应用过滤逻辑：

          【过滤规则1】已生成的块（第5391-5392行）
          if block in self.generated_blocks:
              continue  # 避免重复生成

          【过滤规则2】Guard pattern块（第5394-5396行）
          if block in guard_pattern_blocks:
              self.generated_blocks.add(block)
              continue  # 跳过guard计算块

          【过滤规则3】纯跳转块（第5399-5401行）
          只包含JUMP_FORWARD/JUMP_ABSOLUTE的块是连接器块，跳过

          【过滤规则4】纯清理块（第5403-5406行）
          只包含POP_TOP + JUMP的块是栈清理块，跳过

          【过滤规则5】常量返回块（第5408-5413行）
          LOAD_CONST + RETURN_VALUE/RETURN_CONST 是尾调用优化，跳过

          【过滤规则6】确定性pattern块（第5415-5438行）
          定义：包含DEFINITIVE_PATTERN_OPS中任一操作码的块
          DEFINITIVE_PATTERN_OPS = {
              'MATCH_CLASS', 'MATCH_SEQUENCE', 'MATCH_MAPPING',
              'MATCH_KEYS', 'MATCH_MAPPING_KEYS',
              'COMPARE_OP', 'IS_OP',
              'GET_LEN', 'UNPACK_SEQUENCE', 'UNPACK_EX',
              'UNPACK_EXTRACT',
          }

          判断条件：
          - has_only_pattern: 块中所有指令都在PATTERN_OPS或相关辅助集中
          - has_definitive_pattern: 块中至少有一个DEFINITIVE_PATTERN_OPS

          如果两者都为True，这是pattern匹配块，跳过

          【过滤规则7】Pattern store块（第5440-5455行）
          如果块的所有STORE目标都在pattern_store_names中，
          且没有其他非平凡操作，这是pattern变量存储块，跳过

          pattern_store_names来源：
          - 从pattern字典递归收集所有绑定变量名
          - 例如：case Point(x, y): → {'x', 'y'}
          - 例如：case [a, *rest]: → {'a', 'rest'}

          【过滤规则8】嵌套区域块（第5457-5481行）
          如果块属于嵌套区域（IfRegion/LoopRegion/TryExceptRegion/WithRegion/MatchRegion）:
          - 如果是区域入口块或条件块，递归调用_generate_region或_generate_match
          - 如果只是区域内部的普通块，标记为已生成并跳过

          这实现了match语句的嵌套支持：
          ```python
          match outer:
              case 1:
                  match inner:  # 内层match作为外层case body的一部分
                      case 2:
                          ...
          ```

        Step 2.4: 生成实际语句（第5483-5522行）
          使用case_body_start_indices确定body起始位置：

          【情况A】body_start > 0（pattern和body在同一块中）
          - 创建virtual_block，只包含body_start之后的指令
          - 对virtual_block调用_generate_block_statements
          - 这处理了一个块既包含pattern代码又包含body代码的情况

          【情况B】body_start == 0（整个块都是body）
          - 直接对整个块调用_generate_block_statements

          语句后处理：
          - 过滤掉Expr(Constant(value=None))（这些是NOP占位符）
          - 如果没有语句，插入Pass语句

        Step 2.5: 构建Case节点（第5524-5539行）
          ```python
          case = {
              'type': 'Case',
              'pattern': pattern if pattern else {'type': 'MatchAs'},  # 默认通配符
              'body': body_stmts if body_stmts else [{'type': 'Pass'}],
          }
          if guard:
              # Guard表达式标准化
              if isinstance(guard, dict) and guard.get('type') == 'Compare':
                  # 确保Compare节点有标准的ops/comparators结构
                  ...
              case['guard'] = guard
          cases.append(case)
          ```

        Pattern类型与AST映射：
        =====================

        region.case_patterns中的每个pattern是字典格式，对应ast中的pattern类型：

        1. MatchValue（字面量模式）
           用途: case 1:, case "hello":, case True:
           字典: {'type': 'MatchValue', 'value': <expr>}
           AST: ast.MatchValue(value=ast.Constant(1))

        2. MatchSingleton（单例模式）
           用途: case None:, case True:, case False:
           字典: {'type': 'MatchSingleton', 'value': None|True|False}
           AST: ast.MatchSingleton(value=None)

        3. MatchAs（捕获/通配符模式）
           用途: case x:, case _: （name=None时是通配符）
           字典: {'type': 'MatchAs', 'name': 'x'|None, 'pattern': <inner>|None}
           AST: ast.MatchAs(name='x', pattern=None)

           嵌套示例: case [a, b] as pair:
             {'type': 'MatchAs', 'name': 'pair',
              'pattern': {'type': 'MatchSequence', 'patterns': [
                  {'type': 'MatchAs', 'name': 'a'},
                  {'type': 'MatchAs', 'name': 'b'}
              ]}}

        4. MatchSequence（序列模式）
           用途: case [a, b, c]:, case (x, y):
           字典: {'type': 'MatchSequence', 'patterns': [<pattern list>]}
           AST: ast.MatchSequence(patterns=[ast.MatchAs(name='a'), ...])

        5. MatchMapping（映射模式）
           用途: case {"key": value}:, case {**rest}:
           字典: {'type': 'MatchMapping', 'keys': [<expr list>],
                  'patterns': [<pattern list>], 'rest': 'rest'|None}
           AST: ast.MappingPattern(keys=[...], patterns=[..., rest='rest'])

        6. MatchClass（类模式）
           用途: case Point(x=0, y=0):
           字典: {'type': 'MatchClass', 'cls': <expr>,
                  'patterns': [<positional patterns>],
                  'keyword_patterns': [{'arg': 'x', 'pattern': <pattern>}, ...]}
           AST: ast.ClassPattern(cls=ast.Name(id='Point'),
                                 patterns=[...],
                                 kwd_attrs=['x', 'y'],
                                 kwd_patterns=[...])

        7. MatchOr（OR模式）
           用途: case 1 | 2 | 3:
           字典: {'type': 'MatchOr', 'patterns': [<pattern list>]}
           AST: ast.MatchOr(patterns=[ast.MatchValue(...), ...])

        Guard条件重建：
        =============

        Guard是case的可选条件，语法: case <pattern> if <guard_expr>:

        字节码位置（在case块内）：
        1. Pattern匹配代码（MATCH_*/COMPARE_OP/UNPACK_*/STORE_*）
        2. Guard表达式计算（使用pattern绑定的变量）
        3. 条件跳转：POP_JUMP_IF_FALSE -> next_case（guard失败）
        4. 成功跳转：JUMP_FORWARD -> body_entry（guard成功）

        Guard表达式示例：
        ```python
        case x if x > 0:  # 简单比较
        case Point(x, y) if x > y and y > 0:  # 复杂布尔表达式
        case {"type": t} if t in ("user", "admin"):  # 成员测试
        ```

        Guard的标准化处理（第5530-5537行）:
        - Compare节点可能以非标准格式存储（right代替comparators）
        - 统一转换为标准ast.Compare格式：{left, ops, comparators}

        嵌套处理机制：
        =============

        Match语句可以嵌套在其他Match语句的case body中：

        示例：
        ```python
        match data:
            case {"type": "group", "items": items}:
                match items[0]:
                    case {"type": "header", "name": name}:
                        process_header(name)
                    case _:
                        unknown()
            case _:
                unknown()
        ```

        处理流程：
        1. 外层_match生成时，遍历外层case的body blocks
        2. 发现某个block属于内层MatchRegion（通过get_region_for_block查询）
        3. 递归调用_generate_match(内层region)
        4. 将内层Match AST节点作为外层case body的一个语句插入

        关键实现（第5457-5481行）:
        ```python
        nested_region = self.region_analyzer.get_region_for_block(block)
        if nested_region and nested_region is not region:
            if isinstance(nested_region, MatchRegion):
                generated = self._generate_match(nested_region)  # 递归调用
            else:
                generated = self._generate_region(nested_region)  # 其他区域类型
            if generated:
                body_stmts.append(generated)
            # 标记内层region的所有blocks为已生成
            for b in nested_region.blocks:
                self.generated_blocks.add(b)
        ```

        字节码等价保证：
        ===============

        目标：确保反编译生成的代码编译后的字节码与原始字节码一致

        关键保证措施：

        1. Subject提取准确性
           - 通过操作码分析精确定位subject/pattern边界
           - 区分不同match类型（结构型 vs 字面量型）
           - 处理特殊情况（case None、class pattern with type params）

        2. Pattern完整性
           - pattern_parser已完成字节码→pattern字典的转换
           - _generate_match只负责将字典包装成Case节点
           - 不修改pattern结构，确保信息不丢失

        3. Body边界正确性
           - case_body_start_indices精确标记body起始位置
           - 过滤规则确保pattern指令不泄漏到body中
           - virtual_block机制处理混合块

        4. 控制流一致性
           - Python match语义：从上到下评估cases，第一个匹配成功即执行body
           - 不允许隐式fall-through（不同于C switch）
           - 生成的case顺序必须与原始字节码一致
           - OR模式的多个子模式共享同一body，符合语义

        5. Guard语义保持
           - guard失败时跳转到下一个case（不是default）
           - guard成功时进入当前case的body
           - 生成的AST保持这一控制流语义

        6. 嵌套作用域正确性
           - 内层match的pattern变量在外层不可见
           - 每个case body有自己的作用域（虽然Python实际上不强制）
           - generated_blocks防止重复生成

        隐式default处理：
        ===============

        Python match语句不一定需要显式的case _:

        情况1: 显式default（case _:）
          - pattern为{'type': 'MatchAs', 'name': None}
          - 正常生成Case节点

        情况2: 隐式default（最后一个无pattern的分支）
          - 识别：_is_implicit_default_body()检测body是否只含平凡操作
          - 平凡操作：POP_TOP, LOAD_CONST, RETURN_VALUE, JUMP_FORWARD等
          - 处理：不生成Case节点（在_identify_match_regions阶段已过滤）

        情况3: 无default（所有case都显式匹配）
          - 最后一个case之后直接到merge_block
          - 不生成额外的default case

        性能优化：
        =========
        1. generated_blocks集合避免O(n²)重复检查
        2. pattern_store_names预计算减少重复遍历
        3. guard_pattern_blocks预收集减少运行时判断
        4. virtual_block只在必要时创建（body_start > 0时）
        5. 语句过滤管道：多层过滤逐步缩小范围

        常见问题与调试：
        ===============
        问题1: Subject提取错误
          症状：match后面跟着错误的表达式
          原因：subject/pattern边界判断错误
          解决：检查is_literal_match标志和PATTERN_STARTERS集合

        问题2: Body包含pattern代码
          症状：case body中出现奇怪的COMPARE_OP或STORE_FAST
          原因：case_body_start_indices计算错误或过滤规则失效
          解决：检查_compute_body_block_start和DEFINITIVE_PATTERN_OPS

        问题3: Guard表达式丢失或错误
          症状：缺少if guard或guard内容不对
          原因：_collect_guard_pattern_blocks识别不准确
          解决：检查guard的字节码特征和BFS搜索范围

        问题4: 嵌套match丢失
          症状：内层match变成if-elif或完全丢失
          原因：内层MatchRegion未正确识别或被外层误占
          解决：检查region_analyzer的区域优先级和dominator关系

        问题5: OR模式拆分
          症状：case 1|2|3 变成三个独立case
          原因：_mr_finalize_match_region未合并相同body的cases
          解决：检查body相等性判断逻辑
        """
        subject = None
        if region.subject_block:
            MATCH_OPS = ('MATCH_CLASS', 'MATCH_SEQUENCE', 'MATCH_MAPPING',
                         'MATCH_KEYS', 'MATCH_MAPPING_KEYS')
            subject_instrs = []

            # 字面量match模式：pattern类型为MatchValue/MatchOr/MatchSingleton
            # 这些模式使用COPY+COMPARE_OP/IS_OP而非MATCH_*操作码
            is_literal_match = (
                len(region.case_patterns) > 0 and
                region.case_patterns[0].get('type') in ('MatchValue', 'MatchOr', 'MatchSingleton')
            )
            
            # 字面量match还可能以POP_JUMP_IF_NOT_NONE结尾（case None模式）
            if not is_literal_match and len(region.case_patterns) > 0:
                first_pat = region.case_patterns[0]
                _first_pat_pattern = first_pat.get('pattern') or {}
                if first_pat.get('type') == 'MatchAs' and isinstance(_first_pat_pattern, dict) and _first_pat_pattern.get('type') == 'MatchSingleton':
                    is_literal_match = True
            
            # 通配符 match (case _: ...)：没有pattern匹配指令，
            # subject在POP_TOP或第一个非load指令处结束
            is_wildcard_match = (
                len(region.case_patterns) > 0 and
                region.case_patterns[0].get('type') == 'MatchAs' and
                region.case_patterns[0].get('name') in (None, '_') and
                not region.case_patterns[0].get('pattern')
            )
            
            # Pattern指令集合
            # 对于所有match类型，这些指令都属于pattern而不是subject
            PATTERN_INSTRS = (
                'COPY', 'LOAD_CONST', 'COMPARE_OP', 'IS_OP',
                'LOAD_GLOBAL',
                'UNPACK_SEQUENCE', 'STORE_FAST', 'STORE_NAME',
                'STORE_GLOBAL', 'STORE_DEREF',
            ) + tuple(CONDITIONAL_JUMP_OPS)
            
            for idx, instr in enumerate(region.subject_block.instructions):
                if instr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                    continue
                if instr.opname in MATCH_OPS:
                    break
                
                if is_literal_match:
                    # 字面量match：COPY之前的指令是subject，COPY及之后是pattern
                    PATTERN_STARTERS = ('COPY', 'COMPARE_OP', 'IS_OP')
                    if instr.opname in PATTERN_STARTERS:
                        break
                    if instr.opname == 'LOAD_CONST':
                        rest = region.subject_block.instructions[idx+1:]
                        if rest and rest[0].opname in ('COMPARE_OP', 'IS_OP'):
                            break
                    # case None模式：POP_JUMP_IF_NOT_NONE之前没有COPY
                    if instr.opname in ('POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_IF_NOT_NONE'):
                        break
                else:
                    if is_wildcard_match:
                        if instr.opname in ('POP_TOP', 'RETURN_VALUE', 'RETURN_CONST'):
                            break
                        if instr.opname not in ('LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF', 'LOAD_CONST'):
                            break
                    is_capture_match = (
                        not is_wildcard_match and not is_literal_match and
                        len(region.case_patterns) > 0 and
                        region.case_patterns[0].get('type') == 'MatchAs' and
                        region.case_patterns[0].get('name') is not None
                    )
                    if is_capture_match and instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                        break
                    if instr.opname in ('LOAD_NAME', 'LOAD_GLOBAL'):
                        rest = region.subject_block.instructions[idx+1:]
                        if len(rest) >= 2 and rest[0].opname == 'LOAD_CONST' and isinstance(rest[0].argval, tuple) and rest[1].opname == 'MATCH_CLASS':
                            break
                    if instr.opname == 'LOAD_CONST':
                        rest = region.subject_block.instructions[idx+1:]
                        if rest and rest[0].opname in ('COMPARE_OP', 'IS_OP'):
                            continue
                        if rest and len(rest) >= 2 and rest[0].opname == 'LOAD_CONST' and isinstance(rest[0].argval, tuple) and rest[1].opname in ('MATCH_CLASS', 'MATCH_SEQUENCE', 'MATCH_MAPPING'):
                            continue
                    if (instr.opname in PATTERN_INSTRS and 
                        instr.opname != 'LOAD_FAST' and 
                        instr.opname != 'LOAD_CONST'):
                        continue
                
                subject_instrs.append(instr)
            
            if subject_instrs:
                subject = self.expr_reconstructor.reconstruct(subject_instrs)

        cases = []
        
        num_cases = len(region.case_patterns)
        if num_cases == 0 and len(region.case_bodies) > 0:
            num_cases = len(region.case_bodies)
        
        # 确定性pattern指令：只有包含这些指令的块才是pattern块
        # 不包含这些指令的块（只有POP_TOP+LOAD_CONST+STORE_*+JUMP）是body块
        DEFINITIVE_PATTERN_OPS = frozenset({
            'MATCH_CLASS', 'MATCH_SEQUENCE', 'MATCH_MAPPING',
            'MATCH_KEYS', 'MATCH_MAPPING_KEYS',
            'COMPARE_OP', 'IS_OP',
            'GET_LEN', 'UNPACK_SEQUENCE', 'UNPACK_EX',
            'UNPACK_EXTRACT',
        })
        
        for i in range(num_cases):
            pattern = region.case_patterns[i] if i < len(region.case_patterns) else None
            guard = region.case_guards[i] if i < len(region.case_guards) else None
            body = region.case_bodies[i] if i < len(region.case_bodies) else []

            body_stmts = []
            
            guard_pattern_blocks = set()
            if guard is not None:
                guard_pattern_blocks = self._collect_guard_pattern_blocks(region, i)

            # 通配符match特殊情况：subject_block和body_block可能是同一个块
            # 反编译逻辑：
            # ==========
            # 对于 `match v: case _: <body>` 字节码形态：
            #   RESUME, LOAD_NAME(v), POP_TOP, <body instructions...>
            # subject_block == body_block（同一个基本块），需要用 body_start_index
            # 分割出 body 部分。关键问题：body 中可能包含嵌套控制流（if/for/while等），
            # 这些嵌套结构在 region_analyzer 阶段已被识别为独立的 Region（如 IfRegion），
            # 但其 entry/condition 引用的是原始块（subject_block），而非虚拟块。
            #
            # 修复策略（基于 "No More Gotos" 区域归约算法的层次化处理原则）：
            # 1. 先检查原始块上是否有嵌套区域的 entry/condition 落在 body 范围内
            # 2. 如果有，优先生成嵌套区域 AST（通过 _generate_region 递归）
            # 3. 嵌套区域覆盖的指令范围被标记为 generated_blocks
            # 4. 剩余未覆盖的指令由虚拟块的 _generate_block_statements 处理
            #
            # 边界条件：
            # - 嵌套区域的 entry 可能在 body_start 之前（如 IfRegion.condition_block = subject_block 本身）
            #   这种情况下需要检查 condition_block 的指令位置是否在 body 范围内
            # - 多个嵌套区域可能重叠（罕见），按识别顺序处理
            # - 归约符合度：内层先识别、外层后识别的自底向上归约保证无遗漏
            if is_wildcard_match and body and len(body) == 1 and body[0] == region.subject_block:
                body_start = region.case_body_start_indices.get(body[0].start_offset, 0)
                if body_start > 0:
                    body_instrs = body[0].instructions[body_start:] if body_start < len(body[0].instructions) else []
                    _non_noise = [i for i in body_instrs if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL',
                                                                'RETURN_VALUE', 'RETURN_CONST',
                                                                'LOAD_CONST', 'JUMP_FORWARD', 'JUMP_ABSOLUTE')]
                    if _non_noise or body_start >= len(body[0].instructions):
                        # 检查原始块上的嵌套区域，处理 body 内的控制流子结构
                        orig_block = body[0]
                        nested_found = False
                        for candidate_region in self.region_analyzer.regions:
                            if candidate_region is region or not isinstance(candidate_region, (IfRegion, LoopRegion, TryExceptRegion, WithRegion, MatchRegion)):
                                continue
                            cand_entry = getattr(candidate_region, 'entry', None)
                            cand_cond = getattr(candidate_region, 'condition_block', None)
                            cand_header = getattr(candidate_region, 'header_block', None)
                            # 检查嵌套区域的入口/条件/头块是否是原始块或其一部分
                            relevant_ref = None
                            _body_offset_threshold = orig_block.instructions[body_start].offset if body_start < len(orig_block.instructions) else (orig_block.instructions[-1].offset + 2 if orig_block.instructions else float('inf'))
                            if cand_entry and (cand_entry == orig_block or cand_entry.start_offset >= _body_offset_threshold):
                                relevant_ref = candidate_region
                            elif cand_cond and (cand_cond == orig_block or cand_cond.start_offset >= _body_offset_threshold):
                                relevant_ref = candidate_region
                            elif cand_header and (cand_header == orig_block or cand_header.start_offset >= _body_offset_threshold):
                                relevant_ref = candidate_region
                            if relevant_ref:
                                try:
                                    self.generated_blocks.add(orig_block)
                                    if isinstance(relevant_ref, MatchRegion):
                                        nested_gen = self._generate_match(relevant_ref)
                                    else:
                                        nested_gen = self._generate_region(relevant_ref)
                                    if nested_gen:
                                        if isinstance(nested_gen, list):
                                            body_stmts.extend(nested_gen)
                                        else:
                                            body_stmts.append(nested_gen)
                                        for b in relevant_ref.blocks:
                                            self.generated_blocks.add(b)
                                        if hasattr(relevant_ref, 'condition_block') and relevant_ref.condition_block:
                                            self.generated_blocks.add(relevant_ref.condition_block)
                                        if hasattr(relevant_ref, 'header_block') and relevant_ref.header_block:
                                            self.generated_blocks.add(relevant_ref.header_block)
                                    nested_found = True
                                except Exception:
                                    pass
                        if not nested_found:
                            if body_start < len(body[0].instructions):
                                from .basic_block import BasicBlock as _BB
                                virtual_block = _BB(body[0].instructions[body_start].offset)
                                for instr in body_instrs:
                                    virtual_block.add_instruction(instr)
                                stmts = self._generate_block_statements(virtual_block)
                                if stmts:
                                    filtered = []
                                    for s in stmts:
                                        if s.get('type') == 'Expr' and isinstance(s.get('value'), dict):
                                            val = s['value']
                                            if val.get('type') == 'Constant' and val.get('value') is None:
                                                continue
                                        filtered.append(s)
                                    body_stmts.extend(filtered)
                self.generated_blocks.add(body[0])

            for block in body:
                if block in self.generated_blocks:
                    continue
                
                if block in guard_pattern_blocks:
                    _gpn = self.region_analyzer.get_entry_region_for_block(block)
                    if not _gpn:
                        _gpn = self.region_analyzer.get_region_for_block(block)
                    if _gpn and _gpn is not region and not isinstance(_gpn, MatchRegion):
                        pass
                    else:
                        self.generated_blocks.add(block)
                        continue

                _non_noise = [i for i in block.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE')]
                if all(i.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE') for i in _non_noise):
                    self.generated_blocks.add(block)
                    continue
                
                if all(i.opname in ('POP_TOP', 'JUMP_FORWARD', 'JUMP_ABSOLUTE',
                                    'RESUME', 'NOP', 'CACHE') for i in block.instructions):
                    self.generated_blocks.add(block)
                    continue
                
                _meaningful = [i for i in block.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                if (len(_meaningful) == 2 and
                    _meaningful[0].opname == 'LOAD_CONST' and
                    _meaningful[1].opname in ('RETURN_VALUE', 'RETURN_CONST') and
                    _meaningful[0].argval is None):
                    self.generated_blocks.add(block)
                    continue
                
                nested_region = self.region_analyzer.get_entry_region_for_block(block)
                if not nested_region:
                    nested_region = self.region_analyzer.get_region_for_block(block)
                if nested_region and nested_region is not region and isinstance(nested_region, (IfRegion, LoopRegion, TryExceptRegion, WithRegion, MatchRegion, TernaryRegion, BoolOpRegion)):
                    # 反编译逻辑：处理match case body中的TernaryRegion/BoolOpRegion子区域
                    # 根因：三元表达式和布尔表达式可以嵌入case body的任何位置
                    # 归约顺序：内层（ternary/boolop）先识别、外层（match）后处理
                    # 符合度：TernaryRegion→IfExp(Expr), BoolOpRegion→BoolOp(Expr)
                    if isinstance(nested_region, (TernaryRegion, BoolOpRegion)):
                        """
                        【反编译逻辑】Match通配符体嵌套区域生成（Phase 35 扩展）
                        
                        ═══════════════════════════════════════════════════════════════════════════════
                        1. 功能概述:
                        ─────────────────────
                        本代码段实现 match 语句 case 分支体内的表达式级子区域生成，
                        是 Phase 35 统一子区域处理框架在 match-case 场景中的特殊应用。
                        
                        **特殊之处**: 
                        与if/try/with中的子区域处理相比，match case body中的处理需要额外考虑：
                        - 通配符 case _ 的特殊语义（匹配所有剩余情况）
                        - case guard 条件的影响
                        - match语句的控制流特性（只执行第一个匹配的case）
                        
                        2. 支持的区域类型:
                        ─────────────────────
                        
                        **A. TernaryRegion（三元表达式）**
                        ```python
                        match value:
                            case int():
                                result = x if x > 0 else -x  # TernaryRegion 在 case body 中
                            case str():
                                result = s if len(s) > 0 else "(empty)"
                            case _:
                                result = default if condition else fallback
                        ```
                        
                        **B. BoolOpRegion（布尔运算表达式）**
                        ```python
                        match status:
                            case "active":
                                is_valid = (has_data and is_current) or is_important
                                process(is_valid)
                            case "pending":
                                flag = can_proceed and not is_blocked
                                handle(flag)
                            case _:
                                result = a or b or c  # 默认情况下的复合布尔表达式
                        ```
                        
                        3. 实现逻辑:
                        ─────────────────────
                        ```python
                        if isinstance(nested_region, (TernaryRegion, BoolOpRegion)):
                            child_id = id(nested_region)
                            
                            # 标准防重复检查（与其他方法一致）
                            if child_id not in self._generated_regions and \
                               child_id not in self._generating_regions:
                                
                                # 类型分派
                                if isinstance(nested_region, TernaryRegion):
                                    child_ast = self._generate_ternary(nested_region)
                                else:
                                    child_ast = self._generate_boolop(nested_region)
                                
                                if child_ast:
                                    # 结果插入到case body的语句列表
                                    if isinstance(child_ast, list):
                                        body_stmts.extend(child_ast)
                                    else:
                                        body_stmts.append(child_ast)
                                
                                # 块标记和区域记录
                                for b in nested_region.blocks:
                                    self.generated_blocks.add(b)
                                self._generated_regions.add(child_id)
                            
                            continue  # 跳过后续普通块处理
                        ```
                        
                        4. 在 _generate_match() 中的位置与上下文:
                        ──────────────────────────────────────────
                        
                        **调用位置**: 遍历 match case body 块时的子区域检测点
                        
                        **周围代码结构**:
                        ```python
                        def _generate_match_case_body(region, case_blocks):
                            body_stmts = []
                            
                            for block in case_blocks:
                                # Step 1: 噪音块过滤（L7504-7519）
                                #         跳过纯跳转、空return等无意义块
                                
                                # Step 2: 子区域检测（本代码段 L7522-7544）
                                nested_region = get_entry_region_for_block(block)
                                if nested_region and isinstance(...):
                                    if isinstance(nested_region, (TernaryRegion, BoolOpRegion)):
                                        # 【这里】生成子区域AST
                                        
                                # Step 3: 普通块语句生成（后续代码）
                                #         如果不是子区域，则作为普通语句生成
                                
                            return body_stmts
                        ```
                        
                        5. 通配符 case _ 的特殊性:
                        ────────────────────────────
                        
                        **为什么通配符match需要特殊处理？**
                        
                        问题: 通配符 case _ 的字节码模式可能与 if True: 非常相似，
                             导致 IfRegion 抢占本应属于 MatchRegion 的块。
                             
                        解决方案:
                        - 在 region_analyzer 阶段优先识别 MatchRegion
                        - 在 ast_generator 阶段通过类型检查过滤
                        - 本代码段确保即使存在歧义，ternary/boolop也能正确处理
                        
                        **示例冲突场景**:
                        ```python
                        # 源码
                        match x:
                            case _:
                                y = a if cond else b  # 应该是TernaryRegion
                        
                        # 可能的错误识别
                        match x:
                            case _:           # MatchRegion
                            if True:          # 错误识别为 IfRegion（不应该发生）
                                y = a if cond else b
                        
                        # 正确识别（通过本代码段）
                        match x:
                            case _:                   # MatchRegion
                                [TernaryRegion]        # 正确识别为三元表达式
                        ```
                        
                        6. 典型应用场景:
                        ─────────────────────
                        
                        **场景1: 类型匹配+条件表达式**
                        ```python
                        def process(value):
                            match value:
                                case int() as n:
                                    result = n if n >= 0 else abs(n)
                                    return result
                                case str() as s:
                                    cleaned = s.strip() if s else "(empty)"
                                    return cleaned.upper()
                                case _:
                                    return str(value) if value else "None"
                        ```
                        
                        **场景2: 状态机处理+布尔逻辑**
                        ```python
                        def handle_event(event, state):
                            match state:
                                case "idle":
                                    should_start = (event == "start") or (event == "resume")
                                    transition("running" if should_start else "idle")
                                case "running":
                                    is_error = (event == "error") or (event == "timeout")
                                    stop(immediate=is_error and critical_level > 3)
                                case _:
                                    log_unknown(event) or ignore()
                        ```
                        
                        **场景3: 数据验证+默认值**
                        ```python
                        def validate(config):
                            match config.get("type"):
                                case "database":
                                    host = config["host"] or "localhost"
                                    port = config["port"] if config["port"] else 5432
                                    connect(host, port)
                                case "api":
                                    url = base_url or default_endpoint
                                    timeout = config["timeout"] if config["timeout"] else 30
                                    call_api(url, timeout=timeout)
                                case _:
                                    use_fallback() or raise_error()
                        ```
                        
                        7. 已知限制与边界情况:
                        ───────────────────────────────
                        
                        ✅ **正常工作的情况**:
                        - 简单的 ternary/boolop 表达式在 case body 中
                        - 多个表达式顺序排列
                        - 嵌套在其他控制流中（if/loop）
                        
                        ⚠️ **需要注意的情况**:
                        - case guard 中的 boolop（可能被guard机制消费）
                        - 跨多个case的模式（理论上不应存在）
                        
                        ❌ **当前不支持的情况**:
                        - 极复杂的嵌套表达式（>5层）
                        - 子区域跨越case边界（语法不允许）
                        - match嵌套在ternary/boolop中（罕见）
                        
                        8. 性能与复杂度:
                        ─────────────────────
                        - 时间复杂度: O(case_blocks × subregion_check_cost)
                        - 通常每个case只有1-3个子区域，性能影响可忽略
                        - 内存开销: 复用已有的 generated_blocks 集合
                        
                        9. 测试覆盖建议:
                        ─────────────────────
                        - test_match_ternary_in_case.py: case中的三元表达式
                        - test_match_boolop_in_case.py: case中的布尔运算
                        - test_match_wildcard_*.py: 通配符case的特殊处理
                        - test_match_nested_subregion.py: 嵌套子区域的组合测试
                        
                        ═══════════════════════════════════════════════════════════════════════════════
                        """
                        child_id = id(nested_region)
                        if child_id not in self._generated_regions and child_id not in self._generating_regions:
                            if isinstance(nested_region, TernaryRegion):
                                child_ast = self._generate_ternary(nested_region)
                            else:
                                child_ast = self._generate_boolop(nested_region)
                            if child_ast:
                                if isinstance(child_ast, list):
                                    body_stmts.extend(child_ast)
                                else:
                                    body_stmts.append(child_ast)
                            for b in nested_region.blocks:
                                self.generated_blocks.add(b)
                            self._generated_regions.add(child_id)
                        continue
                    if nested_region.entry == block or (hasattr(nested_region, 'condition_block') and nested_region.condition_block == block):
                        if isinstance(nested_region, MatchRegion):
                            generated = self._generate_match(nested_region)
                        else:
                            generated = self._generate_region(nested_region)
                        if generated:
                            if isinstance(generated, list):
                                body_stmts.extend(generated)
                            else:
                                body_stmts.append(generated)
                        for b in nested_region.blocks:
                            self.generated_blocks.add(b)
                        if hasattr(nested_region, 'condition_block') and nested_region.condition_block:
                            self.generated_blocks.add(nested_region.condition_block)
                        if hasattr(nested_region, 'header_block') and nested_region.header_block:
                            self.generated_blocks.add(nested_region.header_block)
                        continue
                    elif block in nested_region.blocks:
                        if block not in self.generated_blocks:
                            self.generated_blocks.add(block)
                        continue
                
                PATTERN_OPS = ('MATCH_CLASS', 'MATCH_SEQUENCE', 'MATCH_MAPPING',
                               'MATCH_KEYS', 'MATCH_MAPPING_KEYS',
                               'GET_LEN', 'UNPACK_SEQUENCE', 'UNPACK_EX',
                               'UNPACK_EXTRACT', 'BINARY_SUBSCR', 'BINARY_OP')

                has_only_pattern = all(
                    instr.opname in PATTERN_OPS or
                    instr.opname in ('LOAD_CONST', 'LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF',
                                'STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
                                'COMPARE_OP', 'IS_OP', 'POP_TOP', 'COPY', 'SWAP',
                                'EXTENDED_ARG',
                                ) or instr.opname in CONDITIONAL_JUMP_OPS or
                        instr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')
                    for instr in block.instructions
                )
                
                has_definitive_pattern = any(
                    instr.opname in DEFINITIVE_PATTERN_OPS
                    for instr in block.instructions
                )
                
                if has_only_pattern and has_definitive_pattern:
                    _jump_in_body = False
                    body_block_set = set(body)
                    for instr in block.instructions:
                        if instr.opname in CONDITIONAL_JUMP_OPS and instr.argval is not None:
                            _jt = self.cfg.get_block_by_offset(instr.argval)
                            if _jt and _jt in body_block_set:
                                _jump_in_body = True
                                break
                    if not _jump_in_body:
                        self.generated_blocks.add(block)
                        continue
                
                pattern_store_names = set()
                if pattern:
                    self._collect_pattern_store_names(pattern, pattern_store_names)
                block_store_names = set()
                for instr in block.instructions:
                    if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                        block_store_names.add(instr.argval)
                if block_store_names and block_store_names.issubset(pattern_store_names):
                    has_real_pattern_op = any(
                        instr.opname in ('MATCH_CLASS', 'MATCH_SEQUENCE', 'MATCH_MAPPING',
                                        'MATCH_KEYS', 'MATCH_MAPPING_KEYS',
                                        'COMPARE_OP', 'IS_OP', 'GET_LEN',
                                        'UNPACK_SEQUENCE', 'UNPACK_EX', 'UNPACK_EXTRACT')
                        for instr in block.instructions
                    )
                    if has_real_pattern_op:
                        non_store_non_trivial = [i for i in block.instructions
                                                  if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL',
                                                                      'STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
                                                                      'LOAD_CONST', 'RETURN_VALUE', 'RETURN_CONST',
                                                                      'JUMP_FORWARD', 'JUMP_ABSOLUTE', 'POP_TOP')]
                        if not non_store_non_trivial:
                            self.generated_blocks.add(block)
                            continue
                    else:
                        meaningful = [i for i in block.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                        store_instrs = [i for i in meaningful if i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')]
                        non_trivial = [i for i in meaningful if i.opname not in (
                            'LOAD_CONST', 'LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF',
                            'STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
                            'RETURN_VALUE', 'RETURN_CONST', 'POP_TOP'
                        )]
                        is_simple_body_block = len(meaningful) >= 2 and len(store_instrs) >= 1 and len(non_trivial) == 0
                        if not is_simple_body_block:
                            non_store_non_trivial = [i for i in block.instructions
                                                      if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL',
                                                                          'STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
                                                                          'LOAD_CONST', 'RETURN_VALUE', 'RETURN_CONST',
                                                                          'JUMP_FORWARD', 'JUMP_ABSOLUTE', 'POP_TOP')]
                            if not non_store_non_trivial:
                                self.generated_blocks.add(block)
                                continue
                
                body_start = region.case_body_start_indices.get(block.start_offset, 0)
                if body_start == 0 and pattern:
                    pattern_store_names = set()
                    self._collect_pattern_store_names(pattern, pattern_store_names)
                    if pattern_store_names:
                        computed_start = self._compute_body_block_start(block, pattern_store_names)
                        if computed_start > 0:
                            body_start = computed_start
                if body_start > 0:
                    body_instrs = block.instructions[body_start:]
                    if not body_instrs or all(
                        i.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL',
                                    'RETURN_VALUE', 'RETURN_CONST',
                                    'LOAD_CONST', 'JUMP_FORWARD', 'JUMP_ABSOLUTE')
                        for i in body_instrs
                    ):
                        self.generated_blocks.add(block)
                        continue
                    virtual_block = BasicBlock(block.instructions[body_start].offset)
                    for instr in body_instrs:
                        virtual_block.add_instruction(instr)
                    virtual_block.successors = block.successors
                    virtual_block.predecessors = block.predecessors
                    stmts = self._generate_block_statements(virtual_block)
                else:
                    stmts = self._generate_block_statements(block)
                if stmts:
                    filtered = []
                    for s in stmts:
                        if s.get('type') == 'Expr' and isinstance(s.get('value'), dict):
                            val = s['value']
                            if val.get('type') == 'Constant' and val.get('value') is None:
                                continue
                        filtered.append(s)
                    stmts = filtered
                if stmts:
                    body_stmts.extend(stmts)
                else:
                    body_stmts.append({'type': 'Pass'})
                self.generated_blocks.add(block)

            case = {
                'type': 'Case',
                'pattern': pattern if pattern else {'type': 'MatchAs'},
                'body': body_stmts if body_stmts else [{'type': 'Pass'}],
            }
            filtered_body = []
            for s in case['body']:
                if s.get('type') == 'Assign':
                    targets = s.get('targets', [])
                    has_empty_tuple = any(
                        t.get('type') == 'Tuple' and not t.get('elts')
                        for t in targets
                    )
                    if has_empty_tuple:
                        continue
                filtered_body.append(s)
            case['body'] = filtered_body if filtered_body else [{'type': 'Pass'}]
            if guard:
                if isinstance(guard, dict) and guard.get('type') == 'Compare':
                    if 'right' in guard and 'comparators' not in guard:
                        guard = {
                            'type': 'Compare',
                            'left': guard.get('left'),
                            'ops': [op.get('op', '==') if isinstance(op, dict) and op.get('type') == 'CompareOp' else op for op in guard.get('ops', [])],
                            'comparators': [guard.get('right')]
                        }
                case['guard'] = guard
            cases.append(case)

        for block in region.blocks:
            self.generated_blocks.add(block)

        return {
            'type': 'Match',
            'subject': subject if subject else {'type': 'Name', 'id': '_'},
            'cases': cases,
        }

    def _detect_undetected_wildcard_match(self, entry_block):
        """检测未识别的通配符match语句（Phase 37.4修复 - 收紧版）

        当match语句只有通配符case（case _:）且body包含控制流结构时，
        region_analyzer可能只识别了内层区域（LoopRegion/IfRegion等），
        而没有识别外层的MatchRegion。本方法检测这种情况并创建虚拟MatchRegion。

        字节码特征：
            RESUME
            LOAD_NAME/LOAD_FAST/LOAD_GLOBAL v   # match subject
            POP_TOP                             # wildcard pattern discard
            <body instructions>                 # for/if/try等控制流

        收紧版检测条件（仅当以下全部满足时才返回虚拟MatchRegion）:
        1. 入口块以 LOAD_* + POP_TOP 开头（RESUME之后）
        2. POP_TOP之后紧跟的内层区域是LoopRegion或TryExceptRegion
        3. 内层区域的entry_block == entry_block 或 entry_block的fallthrough后继
        4. 不存在已识别的MatchRegion覆盖此入口块
        5. 入口块指令数 <= 5（避免在大块上误检）
        """
        if entry_block is None or len(entry_block.instructions) < 3:
            return None

        if len(entry_block.instructions) > 10:
            return None

        instructions = entry_block.instructions

        _resume_idx = -1
        _load_idx = -1
        _pop_top_idx = -1

        for idx, instr in enumerate(instructions):
            if instr.opname == 'RESUME':
                _resume_idx = idx
            elif instr.opname in ('LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF') and _load_idx == -1 and _resume_idx != -1:
                _load_idx = idx
            elif instr.opname == 'POP_TOP' and _pop_top_idx == -1 and _load_idx != -1:
                _pop_top_idx = idx
                break

        if _load_idx == -1 or _pop_top_idx == -1 or _pop_top_idx <= _load_idx:
            return None

        _has_inner_region = False
        _valid_inner_region = None

        for r in self.regions:
            if isinstance(r, (LoopRegion, TryExceptRegion)):
                _check_offset = instructions[_pop_top_idx + 1].offset if _pop_top_idx + 1 < len(instructions) else instructions[_pop_top_idx].offset + 2
                _offset_ok = (r.entry and r.entry.start_offset >= _check_offset) or \
                             (r.header_block and r.header_block.start_offset >= _check_offset)
                if _offset_ok:
                    _has_inner_region = True
                    _valid_inner_region = r
                    break

        _remaining = instructions[_pop_top_idx + 1:]
        _meaningful_after_pop = [i for i in _remaining if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL',
                                                                          'LOAD_CONST', 'RETURN_VALUE', 'RETURN_CONST',
                                                                          'JUMP_FORWARD', 'JUMP_ABSOLUTE')]

        if not _meaningful_after_pop and not _has_inner_region:
            return None

        for r in self.regions:
            if isinstance(r, MatchRegion) and r.subject_block == entry_block:
                return None

        from core.cfg.region_analyzer import MatchRegion as _MR
        _subject_instr = instructions[_load_idx]
        _subject_expr = self.expr_reconstructor.reconstruct([_subject_instr])
        if not _subject_expr:
            _subject_expr = {'type': 'Name', 'id': str(_subject_instr.argval)}

        _inner_blocks = set()
        for r in self.regions:
            if isinstance(r, (LoopRegion, IfRegion, TryExceptRegion, WithRegion)) and r.entry and r.entry.start_offset > _subject_instr.offset:
                _inner_blocks.update(r.blocks)

        _inner_blocks.discard(entry_block)

        _virtual_mr = _MR(
            subject_block=entry_block,
            case_patterns=[{'type': 'MatchAs', 'name': '_'}],
            case_guards=[None],
            case_bodies=[[entry_block]],
            merge_block=None,
            blocks=set([entry_block]) | _inner_blocks,
            case_body_start_indices={entry_block.start_offset: _pop_top_idx + 1},
            parent=None,
            region_type=None,
            entry=entry_block,
        )
        if hasattr(_virtual_mr, 'metadata'):
            _virtual_mr.metadata['is_virtual_wildcard'] = True

        return _virtual_mr

    def _collect_guard_pattern_blocks(self, region, case_idx):
        guard_pattern_blocks = set()
        guard = region.case_guards[case_idx] if case_idx < len(region.case_guards) else None
        if guard is None:
            return guard_pattern_blocks
        body_blocks = region.case_bodies[case_idx] if case_idx < len(region.case_bodies) else []
        guard_op = None
        if isinstance(guard, dict):
            if guard.get('type') == 'Compare':
                ops = guard.get('ops', [])
                if ops:
                    op = ops[0]
                    guard_op = op.get('op') if isinstance(op, dict) else str(op)
        for block in body_blocks:
            meaningful = [i for i in block.instructions if i.opname not in NOISE_OPS]
            if not meaningful:
                continue
            allowed = frozenset({
                'UNPACK_SEQUENCE', 'UNPACK_EX', 'UNPACK_EXTRACT',
                'MATCH_CLASS', 'MATCH_SEQUENCE', 'MATCH_MAPPING',
                'MATCH_KEYS', 'MATCH_MAPPING_KEYS', 'GET_LEN',
                'LOAD_CONST', 'COMPARE_OP', 'IS_OP',
                'STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
                'LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF',
                'COPY', 'SWAP', 'POP_TOP',
                'LOAD_ATTR', 'BINARY_SUBSCR',
            }) | frozenset(CONDITIONAL_JUMP_OPS)
            if not all(i.opname in allowed for i in meaningful):
                continue
            has_compare = any(i.opname in ('COMPARE_OP', 'IS_OP') for i in meaningful)
            has_cond_jump = any(i.opname in CONDITIONAL_JUMP_OPS for i in meaningful)
            if has_compare and has_cond_jump:
                if guard_op:
                    for i in meaningful:
                        if i.opname == 'COMPARE_OP' and i.argval == guard_op:
                            guard_pattern_blocks.add(block)
                            break
                        elif i.opname == 'IS_OP' and guard_op in ('is', 'is not'):
                            guard_pattern_blocks.add(block)
                            break
                else:
                    guard_pattern_blocks.add(block)
        return guard_pattern_blocks

    def _compute_body_block_start(self, block, pattern_store_names):
        instrs = block.instructions
        idx = 0
        NOISE = frozenset(('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'))
        MATCH_OPS = frozenset(('MATCH_CLASS', 'MATCH_SEQUENCE', 'MATCH_MAPPING',
                               'MATCH_KEYS', 'MATCH_MAPPING_KEYS'))
        STORE_OPS = frozenset(('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'))
        saw_unpack = False
        pattern_store_counts = {}
        while idx < len(instrs):
            op = instrs[idx].opname
            if op in NOISE or op in MATCH_OPS or op in CONDITIONAL_JUMP_OPS or op == 'POP_TOP' or op == 'EXTENDED_ARG':
                idx += 1
                continue
            if op in ('UNPACK_SEQUENCE', 'UNPACK_EX'):
                saw_unpack = True
                idx += 1
                continue
            if op in STORE_OPS:
                if saw_unpack:
                    saw_unpack = False
                    idx += 1
                    continue
                store_name = instrs[idx].argval
                if store_name in pattern_store_names:
                    prev_count = pattern_store_counts.get(store_name, 0)
                    if prev_count == 0:
                        pattern_store_counts[store_name] = 1
                        pattern_store_names.discard(store_name)
                        idx += 1
                        continue
                break
            if op == 'LOAD_CONST':
                if idx + 1 < len(instrs) and instrs[idx + 1].opname in ('COMPARE_OP', 'IS_OP'):
                    idx += 1
                    continue
                break
            if op in ('COMPARE_OP', 'IS_OP') or op == 'GET_LEN' or op == 'SWAP' or op == 'COPY':
                idx += 1
                continue
            if op in ('BUILD_MAP', 'DICT_UPDATE', 'DELETE_SUBSCR',
                       'BINARY_SUBSCR', 'LOAD_ATTR'):
                idx += 1
                continue
            break
        return idx

    def _collect_pattern_store_names(self, pattern, names):
        if not pattern or not isinstance(pattern, dict):
            return
        ptype = pattern.get('type')
        if ptype == 'MatchAs':
            name = pattern.get('name')
            if name:
                names.add(name)
            inner = pattern.get('pattern')
            if inner:
                self._collect_pattern_store_names(inner, names)
        elif ptype == 'MatchStarred':
            inner = pattern.get('pattern')
            if inner:
                self._collect_pattern_store_names(inner, names)
        elif ptype == 'MatchSequence':
            for p in pattern.get('patterns', []):
                self._collect_pattern_store_names(p, names)
        elif ptype == 'MatchMapping':
            for p in pattern.get('patterns', []):
                self._collect_pattern_store_names(p, names)
            rest = pattern.get('rest')
            if rest:
                names.add(rest)
        elif ptype == 'MatchClass':
            for p in pattern.get('patterns', []):
                self._collect_pattern_store_names(p, names)
            for p in pattern.get('keyword_patterns', []):
                self._collect_pattern_store_names(p, names)
        elif ptype == 'MatchOr':
            for p in pattern.get('patterns', []):
                self._collect_pattern_store_names(p, names)

    def _build_boolop_expression(self, region: 'BoolOpRegion') -> Optional[Dict[str, Any]]:
        """从BoolOpRegion的op_chain重建布尔表达式AST

        算法角色：表达式重建器（Expression Reconstructor）
        输入：BoolOpRegion（包含op_chain: List[(BasicBlock, op_type)]）
        输出：Dict格式的AST节点（BoolOp/Name/Constant等）

        【字节码到AST的映射】
        每个chain元素 (block, op_type) 对应boolop的一个操作数：
        - block中的非跳转指令 → 该操作数的求值代码
        - op_type ('and'/'or') → 操作符

        源码: a and b and c
        op_chain: [(block_a, 'and'), (block_b, 'and'), (block_c, 'and')]
        → BoolOp(op='and', values=[Name('a'), Name('b'), Name('c')])

        【算法步骤】
        1. 遍历op_chain，对每个chain_block：
           - 过滤噪声指令（RESUME/NOP/CACHE/PUSH_NULL）
           - 剥离末尾的跳转指令
           - 调用expr_reconstructor.reconstruct()重建子表达式
        2. 分组：将连续相同op_type的值合并为一个segment
        3. 构建AST：
           - 单segment单值 → 直接返回该值
           - 单segment多值 → BoolOp(op, values)
           - 多segment → 从右向左嵌套（反映Python求值优先级）

        【混合and/or的处理】
        源码: a and b or c
        segments: [('and', [a, b]), ('or', [c])]
        → BoolOp(op='or', values=[BoolOp(op='and', values=[a, b]), c])

        这正确反映了 Python 的运算优先级：and绑定比or更紧。

        【与区域抢占问题的关联】
        当此方法返回None或错误结果时，通常是因为：
        1. op_chain中的块被其他区域错误地占用了
        2. 表达式重建器无法处理某些指令模式
        3. 链中包含了不属于boolop的额外指令

        【调用位置】
        _generate_boolop() → _build_boolop_expression(region)
          → expr_reconstructor.reconstruct(pure_instrs) [每个操作数]
        """
        op_chain = region.op_chain
        if not op_chain:
            return None
        STRIP_JUMP_OPS = SHORT_CIRCUIT_JUMP_OPS | FORWARD_CONDITIONAL_JUMP_OPS
        segments = []
        current_op = None
        current_values = []
        for chain_block, chain_op in op_chain:
            instrs = [i for i in chain_block.instructions
                     if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
            last_instr = chain_block.get_last_instruction()
            if last_instr and last_instr.opname in STRIP_JUMP_OPS:
                pure_instrs = [i for i in instrs if i != last_instr]
            else:
                clean_instrs = []
                for i in instrs:
                    if i.opname in ('POP_TOP', 'RETURN_VALUE', 'RETURN_CONST',
                                   'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE'):
                        break
                    clean_instrs.append(i)
                pure_instrs = clean_instrs if clean_instrs else list(instrs[:1]) if instrs else []
            if not pure_instrs:
                continue
            sub_expr = self.expr_reconstructor.reconstruct(pure_instrs)
            if sub_expr is None:
                continue
            if current_op is None:
                current_op = chain_op
                current_values = [sub_expr]
            elif chain_op == current_op:
                current_values.append(sub_expr)
            else:
                if current_values:
                    segments.append((current_op, current_values))
                current_op = chain_op
                current_values = [sub_expr]
        if current_values:
            segments.append((current_op, current_values))
        chain_blocks = set(b for b, _ in op_chain)
        if segments and len(op_chain) >= 1:
            last_chain_block = op_chain[-1][0]
            last_instr = last_chain_block.get_last_instruction()
            if last_instr and last_instr.opname in STRIP_JUMP_OPS:
                ft_succs = sorted(last_chain_block.conditional_successors, key=lambda s: s.start_offset)
                ft_block = next((s for s in ft_succs
                                 if s.start_offset != last_instr.argval
                                 and s not in chain_blocks
                                 and s != region.merge_block), None)
                if ft_block and ft_block in region.blocks:
                    ft_instrs = [i for i in ft_block.instructions
                                 if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                    clean_ft = []
                    for i in ft_instrs:
                        if i.opname in ('POP_TOP', 'RETURN_VALUE', 'RETURN_CONST',
                                       'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE'):
                            break
                        clean_ft.append(i)
                    if clean_ft:
                        ft_expr = self.expr_reconstructor.reconstruct(clean_ft)
                        if ft_expr:
                            last_op, last_vals = segments[-1]
                            last_vals.append(ft_expr)
                            segments[-1] = (last_op, last_vals)
        if not segments:
            return None
        if len(segments) == 1 and len(segments[0][1]) == 1 and len(op_chain) == 1:
            chain_block = op_chain[0][0]
            chain_op = op_chain[0][1]
            last_instr = chain_block.get_last_instruction()
            if last_instr and last_instr.argval is not None and last_instr.opname in (SHORT_CIRCUIT_JUMP_OPS | FORWARD_CONDITIONAL_JUMP_OPS):
                jt_block = self.cfg.get_block_by_offset(last_instr.argval)
                ft_succs = sorted(chain_block.conditional_successors, key=lambda s: s.start_offset)
                ft_block = next((s for s in ft_succs if s.start_offset != last_instr.argval), None)
                ft_expr = None
                if ft_block:
                    ft_instrs = [i for i in ft_block.instructions
                                if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                    clean_ft = []
                    for i in ft_instrs:
                        if i.opname in ('POP_TOP', 'RETURN_VALUE', 'RETURN_CONST',
                                       'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE'):
                            break
                        clean_ft.append(i)
                    if clean_ft:
                        ft_expr = self.expr_reconstructor.reconstruct(clean_ft)
                if ft_expr:
                    _result = {'type': 'BoolOp', 'op': chain_op, 'values': [segments[0][1][0], ft_expr]}
                    _has_unary_not = False
                    if region.merge_block:
                        _merge_instrs = [i for i in region.merge_block.instructions
                                         if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                        if any(i.opname == 'UNARY_NOT' for i in _merge_instrs):
                            _has_unary_not = True
                    if _has_unary_not:
                        _result = {'type': 'UnaryOp', 'op': 'not', 'operand': _result}
                    return _result
        if len(segments) == 1:
            op, values = segments[0]
            if len(values) == 1:
                result = values[0]
            else:
                result = {'type': 'BoolOp', 'op': op, 'values': values}
        else:
            result = None
            for op, values in reversed(segments):
                if len(values) == 1:
                    node = values[0]
                else:
                    node = {'type': 'BoolOp', 'op': op, 'values': values}
                if result is None:
                    result = node
                else:
                    result = {'type': 'BoolOp', 'op': op, 'values': [node, result]}
        _has_unary_not = False
        if region.merge_block:
            _merge_instrs = [i for i in region.merge_block.instructions
                             if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
            if any(i.opname == 'UNARY_NOT' for i in _merge_instrs):
                _has_unary_not = True
        if not _has_unary_not and len(op_chain) >= 1:
            _last_chain_block = op_chain[-1][0]
            _remaining_blocks = [b for b in region.blocks
                                 if b.start_offset > _last_chain_block.start_offset
                                 and b != region.merge_block]
            for _rb in _remaining_blocks:
                if any(i.opname == 'UNARY_NOT' for i in _rb.instructions):
                    _has_unary_not = True
                    break
        if _has_unary_not and result:
            result = {'type': 'UnaryOp', 'op': 'not', 'operand': result}
        return result

    def _generate_boolop(self, region: BoolOpRegion) -> Optional[List[Dict[str, Any]]]:
        """生成BoolOp区域的AST节点列表

        算法角色：区域AST生成器（Region AST Generator）
        输入：BoolOpRegion（包含完整的链结构信息）
        输出：List[Dict] - AST语句列表，或None（如果是条件上下文则仅设置condition_expr）

        【生成策略 - 两种模式】

        模式1：条件上下文模式（_is_outer_condition=True）
        ─────────────────────────────────────────────
        当boolop作为if/while/for的条件时：
        - 不生成独立语句
        - 将重建的boolop表达式设置到 region.condition_expr
        - 父区域（IfRegion/LoopRegion）在生成时会读取此属性
        - 处理取反：如果最后跳转是IF_TRUE/NONE类型，对表达式取反

        模式2：独立表达式模式（_is_outer_condition=False）
        ───────────────────────────────────────────────
        当boolop是独立的赋值/返回/表达式语句时：
        a) 赋值模式（region.value_target存在）:
           → Assign(targets=[Name(value_target)], value=boolop_expr)
        b) 返回模式（merge块以RETURN_VALUE/RETURN_CONST结尾）:
           → Return(value=boolop_expr)
        c) 表达式语句模式（有短路跳转操作码）:
           → Expr(value=boolop_expr)
        d) 带body的if-like模式（罕见，用于复杂短路结构）:
           → 生成then/else分支语句

        【条件上下文检测算法】
        1. 查找enclosing parent（LoopRegion或IfRegion）
        2. 检查以下任一条件：
           a. region.prefix_block == enclosing.condition_block
           b. op_chain中任一chain_block == enclosing.condition_block
        3. 满足则标记为条件上下文

        【prefix指令处理】
        在boolop链之前可能有前缀指令（如变量加载）：
        - 通过 identify_block_prefix_instructions() 提取
        - 如果前缀中有STORE指令，将其及之前的LOAD作为pre-statement
        - 这确保了 `x = a; result = x and b` 中 x 的赋值被正确保留

        【与Phase 5修复的关联】
        Phase 5修复了IfRegion的"过度合并"问题。类似地，此方法中的
        _body_is_if_body 检测逻辑防止boolop错误地吸收相邻的if-body块。
        但test_bool11/12表明循环条件中的boolop仍可能被遗漏。

        【已知问题】
        1. test_bool13 (flag = a and b or c): 被TernaryRegion抢占
        2. test_bool19 ((a and b) or (c and d) or None): 复合嵌套失败
        3. test_bool15 (assert中的boolop): AssertRegion抢占
        4. 循环条件中的boolop可能不被识别为子区域
        """
        op_chain = region.op_chain
        if not op_chain and not region.prefix_block:
            return None

        _is_outer_condition = False
        _enclosing = region.find_enclosing_parent((LoopRegion, IfRegion))
        if _enclosing and hasattr(_enclosing, 'condition_block') and _enclosing.condition_block:
            if region.prefix_block and region.prefix_block == _enclosing.condition_block:
                _is_outer_condition = True
            if not _is_outer_condition:
                for chain_block, _ in region.op_chain:
                    if chain_block == _enclosing.condition_block:
                        _is_outer_condition = True
                        break

        if _is_outer_condition:
            for block in region.blocks:
                self.generated_blocks.add(block)
            if region.merge_block:
                is_loop_else = False
                is_if_else = False
                _enclosing_loop = region.find_enclosing_parent((LoopRegion,))
                if _enclosing_loop and region.merge_block in _enclosing_loop.else_blocks:
                    is_loop_else = True
                if not is_loop_else:
                    _enclosing_if = region.find_enclosing_parent((IfRegion,))
                    if _enclosing_if and _enclosing_if.else_blocks and region.merge_block in _enclosing_if.else_blocks:
                        is_if_else = True
                if not is_loop_else and not is_if_else:
                    self.generated_blocks.add(region.merge_block)
            boolop_expr = self._build_boolop_expression(region)
            if boolop_expr:
                _boolop_negate = False
                _last_cb = region.op_chain[-1][0] if region.op_chain else None
                if _last_cb:
                    _last_ci = _last_cb.get_last_instruction()
                    if _last_ci and _last_ci.argval is not None and _last_ci.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                        if 'TRUE' in _last_ci.opname or 'NONE' in _last_ci.opname:
                            _boolop_negate = True
                if _boolop_negate:
                    boolop_expr = _negate_expr(boolop_expr)
                region.condition_expr = boolop_expr
            return None

        pre_stmts = []
        if region.prefix_block:
            pre_instrs = self.region_analyzer.identify_block_prefix_instructions(region.prefix_block)
            pre_stmts = self._build_prefix_stmt_list(pre_instrs, region.prefix_block) if pre_instrs else []
        elif op_chain:
            first_chain_block = op_chain[0][0]
            pre_instrs = self.region_analyzer.identify_block_prefix_instructions(first_chain_block)
            last_store_idx = -1
            for idx, instr in enumerate(pre_instrs):
                if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                    last_store_idx = idx
            if last_store_idx >= 0:
                filtered_pre_instrs = pre_instrs[:last_store_idx + 1]
                pre_stmts = self._build_prefix_stmt_list(filtered_pre_instrs, first_chain_block) if filtered_pre_instrs else []
            else:
                pre_stmts = []

        results = list(pre_stmts)
        _body_is_if_body = False
        if region.body_block:
            _body_instrs = [i for i in region.body_block.instructions
                           if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
            _body_has_store = any(
                i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
                for i in _body_instrs
            )
            _body_has_expr_stmt = False
            if not _body_has_store:
                for idx, i in enumerate(_body_instrs):
                    if i.opname == 'POP_TOP' and idx > 0:
                        _prev = [j for j in _body_instrs[:idx]
                                 if j.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP')]
                        if _prev:
                            _body_has_expr_stmt = True
                            break
            _body_has_only_jump = all(
                i.opname in ('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE',
                             'JUMP_BACKWARD_NO_INTERRUPT', 'RETURN_VALUE', 'RETURN_CONST')
                for i in _body_instrs
            ) if _body_instrs else True
            _body_is_if_body = _body_has_store or _body_has_expr_stmt or _body_has_only_jump

        boolop_expr = self._build_boolop_expression(region)
        if boolop_expr:
            if region.value_target:
                results.append({
                    'type': 'Assign',
                    'targets': [{'type': 'Name', 'id': region.value_target, 'ctx': 'Store'}],
                    'value': boolop_expr,
                })
                if region.merge_block:
                    _merge_instrs = [i for i in region.merge_block.instructions
                                    if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                    _after_store = False
                    for i in _merge_instrs:
                        if i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                            _after_store = True
                            continue
                        if _after_store and i.opname not in ('JUMP_FORWARD', 'JUMP_BACKWARD',
                                                              'JUMP_ABSOLUTE', 'JUMP_BACKWARD_NO_INTERRUPT'):
                            _stmts = self._generate_block_statements(region.merge_block)
                            for s in _stmts:
                                if s.get('type') != 'Assign' or s.get('targets', [{}])[0].get('id') != region.value_target:
                                    results.append(s)
                            break
            else:
                has_short_circuit_op = any(
                    cb.get_last_instruction() and cb.get_last_instruction().opname in SHORT_CIRCUIT_JUMP_OPS
                    for cb, _ in op_chain
                )
                _merge_is_return_only = False
                if region.merge_block:
                    _merge_non_noise = [i for i in region.merge_block.instructions
                                       if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                    if _merge_non_noise and all(i.opname in ('RETURN_VALUE', 'RETURN_CONST', 'LOAD_CONST', 'LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF')
                                                for i in _merge_non_noise):
                        _last_merge = region.merge_block.get_last_instruction()
                        if _last_merge and _last_merge.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                            _merge_is_return_only = True
                if _merge_is_return_only:
                    results.append({'type': 'Return', 'value': boolop_expr})
                elif has_short_circuit_op:
                    results.append({'type': 'Expr', 'value': boolop_expr})
                else:
                    region_block_set = set(id(b) for b in region.blocks)
                    last_chain_block = op_chain[-1][0] if op_chain else region.prefix_block
                    then_block = None
                    else_block = None

                    if last_chain_block:
                        last_instr = last_chain_block.get_last_instruction()
                        if last_instr and last_instr.argval is not None:
                            jump_target = self.cfg.get_block_by_offset(last_instr.argval)
                            succs = list(last_chain_block.successors)
                            for s in succs:
                                if s is jump_target:
                                    else_block = s
                                else:
                                    then_block = s

                    _then_is_body = (then_block is not None and then_block == region.body_block
                                     and then_block in region.blocks and _body_is_if_body)

                    if then_block and (then_block not in region.blocks or _then_is_body):
                        if _then_is_body:
                            then_stmts = self._generate_block_statements(then_block)
                            self.generated_blocks.add(then_block)
                        else:
                            then_region = self.region_analyzer.get_region_for_block(then_block)
                            if isinstance(then_region, LoopRegion) and (then_region.entry == then_block or then_region.condition_block == then_block):
                                then_stmts = [self._generate_region(then_region)]
                                for b in then_region.blocks:
                                    self.generated_blocks.add(b)
                            elif isinstance(then_region, TryExceptRegion) and then_region.entry == then_block:
                                then_stmts = [self._generate_region(then_region)]
                                for b in then_region.blocks:
                                    self.generated_blocks.add(b)
                            else:
                                then_stmts = self._generate_block_statements(then_block)
                            self.generated_blocks.add(then_block)

                        else_stmts = []
                        if else_block and else_block not in region.blocks and else_block is not region.merge_block:
                            else_region = self.region_analyzer.get_region_for_block(else_block)
                            if isinstance(else_region, LoopRegion) and (else_region.entry == else_block or else_region.condition_block == else_block):
                                else_stmts = [self._generate_region(else_region)]
                                for b in else_region.blocks:
                                    self.generated_blocks.add(b)
                            elif isinstance(else_region, TryExceptRegion) and else_region.entry == else_block:
                                else_stmts = [self._generate_region(else_region)]
                                for b in else_region.blocks:
                                    self.generated_blocks.add(b)
                            elif isinstance(else_region, IfRegion) and else_region.condition_block == else_block:
                                else_if_ast = self._generate_region(else_region)
                                if else_if_ast:
                                    else_stmts = [else_if_ast] if isinstance(else_if_ast, dict) else else_if_ast
                                for b in else_region.blocks:
                                    self.generated_blocks.add(b)
                            else:
                                else_stmts = self._generate_block_statements(else_block)
                            self.generated_blocks.add(else_block)
                        elif else_block is region.merge_block and region.merge_block:
                            if not (self.region_analyzer._is_return_none_block(region.merge_block) or
                                    self.block_role(region.merge_block) in (BlockRole.RETURN_NONE, BlockRole.PURE_JUMP)):
                                else_stmts = self._generate_block_statements(region.merge_block)
                                self.generated_blocks.add(region.merge_block)

                        _negate = False
                        if last_chain_block:
                            _last = last_chain_block.get_last_instruction()
                            if _last and _last.argval is not None:
                                if 'TRUE' in _last.opname or 'NONE' in _last.opname:
                                    if else_block:
                                        _negate = True
                                elif 'FALSE' in _last.opname or 'NOT_NONE' in _last.opname:
                                    pass
                                if not _negate and then_block and else_block:
                                    if _last.argval == then_block.start_offset:
                                        _negate = True
                        test_expr = _negate_expr(boolop_expr) if _negate else boolop_expr

                        results.append({
                            'type': 'If',
                            'test': test_expr,
                            'body': then_stmts if then_stmts else [{'type': 'Pass'}],
                            'orelse': else_stmts,
                        })
                    else:
                        results.append({'type': 'Expr', 'value': boolop_expr})

        for block in region.blocks:
            self.generated_blocks.add(block)
        if region.merge_block:
            self.generated_blocks.add(region.merge_block)
        if op_chain:
            last_chain_block = op_chain[-1][0]
            last_instr = last_chain_block.get_last_instruction()
            if last_instr and last_instr.argval is not None:
                for s in last_chain_block.conditional_successors:
                    if s.start_offset != last_instr.argval:
                        self.generated_blocks.add(s)
                        break

        return results if results is not None and len(results) > 0 else None

    def _build_ternary_boolop_condition(self, region: TernaryRegion) -> Optional[Dict]:
        """构建三元表达式中嵌套的BoolOp条件

        当TernaryRegion有condition_chain_blocks（长度>1）时调用，
        表示条件部分是一个and/or链而非简单表达式。

        源码: x if a and b else y
        condition_chain_blocks: [(block_a, 'and'), (block_b, 'and')]
        → BoolOp(op='and', values=[Name('a'), Name('b')])

        【算法】
        1. 遍历condition_chain_blocks中的每个(块, 操作符)对
        2. 过滤噪声指令，剥离末尾跳转
        3. 调用expr_reconstructor重建每个子表达式
        4. 从左向右合并为BoolOp树

        【与 _build_boolop_expression 的区别】
        - 此方法专门处理ternary内部的boolop条件
        - 假设所有操作符类型相同（纯and链或纯or链）
        - 不处理混合and/or（那种情况应该在识别阶段被拆分）
        """
        chain = getattr(region, 'condition_chain_blocks', None)
        if not chain or len(chain) <= 1:
            return None
        values = []
        op_type = None
        for cb, cop in chain:
            instrs = [i for i in cb.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
            last = cb.get_last_instruction()
            if last and last.opname in ('POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE', 'JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP'):
                instrs = [i for i in instrs if i != last]
            if instrs:
                sub = self.expr_reconstructor.reconstruct(instrs)
                if sub:
                    values.append(sub)
                    if op_type is None:
                        op_type = cop
        if len(values) < 2 or op_type is None:
            return None
        result = values[0]
        for v in values[1:]:
            result = {'type': 'BoolOp', 'op': op_type, 'values': [result, v]}
        return result

    def _build_ternary_value_expr(self, block: 'BasicBlock') -> Optional[Dict]:
        """从基本块重建三元表达式的true/false值表达式

        处理三种情况：
        1. 嵌套TernaryRegion：递归调用 _build_nested_ternary_expr
        2. 普通值块：过滤噪声后调用expr_reconstructor
        3. 返回值块：剥离末尾RETURN_VALUE/RETURN_CONST后重建

        【POP_TOP处理】
        如果块末尾有POP_TOP（表示表达式语句被丢弃），
        则剥离该指令。但如果连续两个POP_TOP，则只剥一个。
        这处理了 `func()` vs `x = func()` 的区别。

        【返回None的情况】
        - block为None（理论上不应该发生）
        - 过滤后无指令
        - expr_reconstructor失败
        """
        if block is None:
            return None
        existing = self.region_analyzer.get_region_for_block(block)
        if isinstance(existing, TernaryRegion) and existing.entry == block:
            return self._build_nested_ternary_expr(existing)
        instrs = [i for i in block.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE')]
        last = block.get_last_instruction()
        if last and last.opname in ('RETURN_VALUE', 'RETURN_CONST'):
            instrs = [i for i in instrs if i != last]
        if not instrs:
            return None
        if len(instrs) >= 2 and instrs[-1].opname == 'POP_TOP':
            instrs = instrs[:-1]
        if not instrs:
            return None
        if len(instrs) >= 2 and instrs[-2].opname == 'POP_TOP':
            instrs = instrs[:-1]
        if not instrs:
            return None
        return self.expr_reconstructor.reconstruct(instrs)

    def _build_nested_ternary_expr(self, region: TernaryRegion) -> Optional[Dict]:
        """构建嵌套三元表达式AST

        当三元表达式的true/false值本身是另一个三元表达式时调用。
        递归结构：外层ternary的值块是内层TernaryRegion的entry。

        源码: a if cond1 else (b if cond2 else c)
        外层: TernaryRegion(cond=cond1, true=a, false=内层entry)
        内层: TernaryRegion(cond=cond2, true=b, false=c)

        → IfExp(test=cond1, body=Name('a'),
                 orelse=IfExp(test=cond2, body=Name('b'), orelse=Name('c')))

        【递归终止条件】
        - _build_ternary_value_expr检测到值块是TernaryRegion时触发此方法
        - 内层ternary的值块如果不是TernaryRegion，则走普通重建路径
        """
        cond_block = region.condition_block
        if cond_block is None:
            return None
        cond_instrs = [i for i in cond_block.instructions
                       if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
        last_cond = cond_block.get_last_instruction()
        if last_cond and last_cond.opname in (FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS):
            cond_instrs = [i for i in cond_instrs if i != last_cond]
        cond_expr = self.expr_reconstructor.reconstruct(cond_instrs) if cond_instrs else None
        true_expr = self._build_ternary_value_expr(region.true_value_block)
        false_expr = self._build_ternary_value_expr(region.false_value_block)
        if cond_expr and true_expr and false_expr:
            return {
                'type': 'IfExp',
                'test': cond_expr,
                'body': true_expr,
                'orelse': false_expr,
            }
        return None

    def _generate_ternary(self, region: TernaryRegion) -> Optional[List[Dict[str, Any]]]:
        """生成TernaryRegion的AST语句列表

        算法角色：区域AST生成器（Region AST Generator）
        输入：TernaryRegion（完整的三元表达式区域信息）
        输出：List[Dict] - 包含IfExp节点的AST语句列表

        【条件表达式重建策略】

        策略A - BoolOp条件链（condition_chain_blocks长度>1）:
        ───────────────────────────────────────────────
        当三元条件的部分是and/or链时：
        调用 _build_ternary_boolop_condition(region) 构建BoolOp AST

        策略B - 单块条件表达式:
        ────────────────────────
        处理更复杂的情况，包括：
        1. 函数调用上下文：检测PUSH_NULL + LOAD_*模式，跳过函数调用前缀
        2. 前缀赋值：提取条件中的STORE指令作为pre-statement
        3. None检查操作码保留：POP_JUMP_IF_NONE等特殊处理

        【值表达式重建】
        true_expr = _build_ternary_value_expr(true_block)
        false_expr = _build_ternary_value_expr(false_block)
        两者都可能触发嵌套ternary递归。

        【输出格式决策树】

        1. 有value_target → Assign(targets, value=IfExp(...))
           + merge_block有RETURN → 额外追加Return语句

        2. 无value_target但有container_type:
           - 'dict' → Expr(value=Dict(keys=[key], values=[IfExp]))
           - 'list' → Expr(value=List(elts=[IfExp]))
           - 'tuple' → Expr(value=Tuple(elts=[IfExp]))
           - 'set' → Expr(value=Set(elts=[IfExp]))

        3. 无value_target无container:
           a) 值块有POP_TOP → Expr(value=IfExp)  [表达式语句]
           b) merge块以RETURN结尾 → Return(value=IfExp)

        【test_tn20/tn21失败的根因分析】
        源码: `a if a and b else 0`
        失败原因：此源码被识别为IfRegion而非TernaryRegion。
        根因在 _identify_ternary_regions 而非此方法。
        当BoolOpRegion抢占 `a and b` 的链后，ternary识别的
        _detect_ternary_pattern 中 skip_ternary=True 导致跳过。

        【与Phase 5修复的关系】
        Phase 5修复了IfRegion对简单 `x if cond else y` 的过度抢占，
        但对于含boolop的三元表达式，边界仍偏向保守。
        """
        cond_block = region.condition_block
        true_block = region.true_value_block
        false_block = region.false_value_block
        pre_stmts = []

        if region.condition_chain_blocks and len(region.condition_chain_blocks) > 1:
            cond_expr = self._build_ternary_boolop_condition(region)
        else:
            cond_instrs_raw = [i for i in cond_block.instructions
                               if i.opname not in ('RESUME', 'NOP', 'CACHE')]
            last_cond_instr = cond_block.get_last_instruction()

            func_call_skip = 0
            push_null_idx = None
            for idx, i in enumerate(cond_instrs_raw):
                if i.opname == 'PUSH_NULL':
                    push_null_idx = idx
                    break
            if push_null_idx is not None and push_null_idx + 1 < len(cond_instrs_raw):
                next_i = cond_instrs_raw[push_null_idx + 1]
                if next_i.opname in ('LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_FAST', 'LOAD_DEREF', 'LOAD_ATTR'):
                    func_call_skip = push_null_idx + 2
                    if next_i.opname == 'LOAD_ATTR' and push_null_idx > 0:
                        obj_i = cond_instrs_raw[push_null_idx - 1]
                        if obj_i.opname.startswith('LOAD_'):
                            func_call_skip = push_null_idx + 2

            cond_instrs = cond_instrs_raw[func_call_skip:]
            cond_start_idx = 0

            i = 0
            while i < len(cond_instrs):
                instr = cond_instrs[i]
                if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                    load_instrs = []
                    j = i - 1
                    while j >= cond_start_idx:
                        if cond_instrs[j].opname.startswith('LOAD_'):
                            load_instrs.insert(0, cond_instrs[j])
                            j -= 1
                        else:
                            break

                    if load_instrs:
                        val_expr = self.expr_reconstructor.reconstruct(load_instrs)
                        if val_expr:
                            pre_stmts.append({
                                'type': 'Assign',
                                'targets': [{'type': 'Name', 'id': instr.argval, 'ctx': 'Store'}],
                                'value': val_expr,
                            })
                        cond_start_idx = i + 1

                i += 1

            filtered_cond = []
            for i in range(cond_start_idx, len(cond_instrs)):
                instr = cond_instrs[i]
                if instr == last_cond_instr:
                    if last_cond_instr.opname in NONE_CHECK_OPS:
                        filtered_cond.append(instr)
                    break
                filtered_cond.append(instr)

            cond_expr = self.expr_reconstructor.reconstruct(filtered_cond)
        
        true_expr = self._build_ternary_value_expr(true_block)
        false_expr = self._build_ternary_value_expr(false_block)

        if cond_expr and true_expr and false_expr:
            ternary_expr = {
                'type': 'IfExp',
                'test': cond_expr,
                'body': true_expr,
                'orelse': false_expr,
            }

            results = list(pre_stmts)
            merge_ctx = getattr(region, 'merge_context', None)  # Phase 12: 获取merge上下文
            
            # Phase 12修复: 根据merge_context决定输出格式（保守策略）
            if merge_ctx == 'iter':
                # for循环迭代器: 生成Expr(IfExp)，由for循环生成器使用
                results.append({'type': 'Expr', 'value': ternary_expr})
                
            elif merge_ctx == 'compare':
                # if/while条件: 生成Expr(IfExp)，由条件语句生成器使用
                results.append({'type': 'Expr', 'value': ternary_expr})
                
            elif merge_ctx == 'return':
                # lambda/嵌套return: 直接返回Return(IfExp)
                results.append({'type': 'Return', 'value': ternary_expr})
                
            elif region.value_target and not str(region.value_target).startswith('__'):
                # 标准赋值模式: value_target是真实变量名
                results.append({
                    'type': 'Assign',
                    'targets': [{'type': 'Name', 'id': region.value_target, 'ctx': 'Store'}],
                    'value': ternary_expr,
                })
                if region.merge_block:
                    merge_instrs = [i for i in region.merge_block.instructions
                                    if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL')]
                    return_value = None
                    for instr in merge_instrs:
                        if instr.opname == 'LOAD_FAST':
                            return_value = {'type': 'Name', 'id': instr.argval, 'ctx': 'Load'}
                        elif instr.opname == 'LOAD_NAME':
                            return_value = {'type': 'Name', 'id': instr.argval, 'ctx': 'Load'}
                        elif instr.opname == 'LOAD_GLOBAL':
                            return_value = {'type': 'Name', 'id': instr.argval, 'ctx': 'Load'}
                        elif instr.opname == 'LOAD_CONST':
                            return_value = {'type': 'Constant', 'value': instr.argval}
                        elif instr.opname == 'RETURN_VALUE' and return_value is not None:
                            results.append({'type': 'Return', 'value': return_value})
                        elif instr.opname == 'RETURN_CONST':
                            results.append({'type': 'Return', 'value': {'type': 'Constant', 'value': instr.argval}})
            else:
                container_type = region.container_type
                container_info = None
                if container_type:
                    if container_type == 'dict':
                        key_expr = region.dict_key_info
                        if key_expr:
                            container_info = {'type': 'Dict', 'keys': [key_expr], 'values': [ternary_expr]}
                    elif container_type == 'list':
                        container_info = {'type': 'List', 'elts': [ternary_expr], 'ctx': 'Load'}
                    elif container_type == 'tuple':
                        container_info = {'type': 'Tuple', 'elts': [ternary_expr], 'ctx': 'Load'}
                    elif container_type == 'set':
                        container_info = {'type': 'Set', 'elts': [ternary_expr], 'ctx': 'Load'}
                if container_info:
                    results.append({'type': 'Expr', 'value': container_info})
                else:
                    has_pop_top = any(
                        any(i.opname == 'POP_TOP' for i in b.instructions)
                        for b in (true_block, false_block)
                    )
                    if has_pop_top:
                        results.append({'type': 'Expr', 'value': ternary_expr})
                    else:
                        is_return = False
                        if region.merge_block:
                            merge_non_noise = [i for i in region.merge_block.instructions
                                              if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                            if merge_non_noise:
                                merge_last = region.merge_block.get_last_instruction()
                                if merge_last and merge_last.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                                    before_return = [i for i in merge_non_noise
                                                    if i.opname not in ('RETURN_VALUE', 'RETURN_CONST')]
                                    if not before_return:
                                        is_return = True
                        if is_return:
                            results.append({'type': 'Return', 'value': ternary_expr})
                        else:
                            func_call_info = region.func_call_info
                            if func_call_info:
                                call_expr = {
                                    'type': 'Call',
                                    'func': func_call_info['func'],
                                    'args': func_call_info.get('args', []) + [ternary_expr],
                                    'keywords': [],
                                }
                                results.append({'type': 'Expr', 'value': call_expr})
                            else:
                                results.append({'type': 'Expr', 'value': ternary_expr})
            
            for block in region.blocks:
                self.generated_blocks.add(block)
            
            return results

        return None




    def _generate_basic_region(self, region: Region) -> List[Dict[str, Any]]:
        stmts = []
        for block in sorted(region.blocks, key=lambda b: b.start_offset):
            if block in self.generated_blocks:
                continue
            if self.block_role(block) == BlockRole.WITH_EXIT_CLEANUP:
                self.generated_blocks.add(block)
                continue
            block_stmts = self._generate_block_statements(block)
            if block_stmts:
                pass
            stmts.extend(block_stmts)
            self.generated_blocks.add(block)
        return stmts

    def _generate_block_statements(self, block: BasicBlock, _cjb_parent: BasicBlock = None) -> List[Dict[str, Any]]:
        if block in self.generated_blocks or block.start_offset in self.generated_offsets:
            return []
        if any(i.opname == 'BINARY_OP' for i in block.instructions):
            pass

        _block_role = self.region_analyzer.get_block_role(block)
        if _block_role in (BlockRole.BREAK, BlockRole.PURE_BREAK):
            _has_return_instr = any(
                i.opname in ('RETURN_VALUE', 'RETURN_CONST')
                for i in block.instructions
            )
            if _has_return_instr:
                _ret_ast = self._generate_return_ast(block)
                if _ret_ast:
                    self.generated_blocks.add(block)
                    self.generated_offsets.add(block.start_offset)
                    return [_ret_ast]
            
            _meaningful = [i for i in block.instructions
                           if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
            _is_trivial_ret = (len(_meaningful) == 2
                                and _meaningful[0].opname == 'LOAD_CONST'
                                and _meaningful[0].argval is None
                                and _meaningful[1].opname in ('RETURN_VALUE', 'RETURN_CONST'))
            if _is_trivial_ret:
                _in_try_region = False
                for _tr in self.region_analyzer.regions:
                    if hasattr(_tr, 'try_blocks') and block in (_tr.try_blocks or []):
                        _in_try_region = True
                        break
                if _in_try_region:
                    self.generated_blocks.add(block)
                    self.generated_offsets.add(block.start_offset)
                    return [{'type': 'Break'}]

        meaningful = [i for i in block.instructions
                     if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
        if len(meaningful) == 2:
            load_instr = meaningful[0]
            store_instr = meaningful[1]
            load_ops = ('LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF')
            store_ops = ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
            if (load_instr.opname in load_ops and store_instr.opname in store_ops
                and load_instr.argval == store_instr.argval):
                self.generated_blocks.add(block)
                return [{'type': 'Pass'}]

        pass_return_stmts = None
        instrs = block.instructions
        if len(instrs) >= 2:
            has_nop = any(i.opname == 'NOP' for i in instrs)
            has_return = any(i.opname in ('RETURN_VALUE', 'RETURN_CONST') for i in instrs)
            if has_nop and has_return:
                trivial_ops = {
                    'RESUME', 'NOP', 'CACHE', 'PUSH_NULL',
                    'LOAD_CONST', 'RETURN_VALUE', 'RETURN_CONST',
                    'POP_TOP', 'COPY', 'SWAP',
                }
                if all(instr.opname in trivial_ops for instr in instrs):
                    if (len(instrs) == 3 and
                        instrs[0].opname == 'NOP' and
                        instrs[1].opname == 'LOAD_CONST' and
                        instrs[1].argval is None and
                        instrs[2].opname == 'RETURN_VALUE'):
                        nop_positions = getattr(instrs[0], 'positions', None)
                        if (nop_positions is not None and
                            nop_positions.lineno is not None and
                            nop_positions.end_lineno is not None and
                            nop_positions.lineno != nop_positions.end_lineno):
                            self.generated_blocks.add(block)
                            return [{
                                'type': 'While',
                                'test': {'type': 'Constant', 'value': True},
                                'body': [{'type': 'Break'}],
                            }]
                    stmts = []
                    return_value = None
                    for instr in block.instructions:
                        if instr.opname in ('LOAD_CONST', 'LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL'):
                            return_value = self.expr_reconstructor.reconstruct([instr])
                        elif instr.opname == 'RETURN_VALUE' or instr.opname == 'RETURN_CONST':
                            break
                    stmts.append({
                        'type': 'Return',
                        'value': return_value if return_value else {'type': 'Constant', 'value': None}
                    })
                    pass_return_stmts = stmts
        if pass_return_stmts is not None:
            self.generated_blocks.add(block)
            return pass_return_stmts

        block_role = self.block_role(block)

        if block_role == BlockRole.WITH_EXIT_CLEANUP:
            self.generated_blocks.add(block)
            return []

        if block_role == BlockRole.LOOP_EXIT:
            self.generated_blocks.add(block)
            return []

        if block_role == BlockRole.PURE_CONTINUE:
            self.generated_blocks.add(block)
            _is_natural_be_gbs = False
            if self._current_loop:
                if block == self._current_loop.back_edge_block:
                    _is_natural_be_gbs = True
                else:
                    _gbs_succs = list(block.successors)
                    if len(_gbs_succs) == 1 and self._current_loop.header_block and _gbs_succs[0] == self._current_loop.header_block:
                        _is_natural_be_gbs = True
                    elif len(_gbs_succs) == 1 and self._current_loop.condition_block and _gbs_succs[0] == self._current_loop.condition_block:
                        _is_natural_be_gbs = True
            if not _is_natural_be_gbs:
                return [{'type': 'Continue'}]
            return []
        elif block_role == BlockRole.CONTINUE:
            effective = self.region_analyzer.effective_instructions.get(block.start_offset)
            if effective:
                _eff_stmts = []
                if effective:
                    _eff_expr_instrs = []
                    _seen_for_targets3 = set()
                    for _instr in effective:
                        if _instr.opname in ('RESUME', 'NOP', 'CACHE'):
                            continue
                        if _instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF') and _instr.argval in (self._current_loop.metadata.get('for_target_names', set()) if self._current_loop else set()) and _instr.argval not in _seen_for_targets3:
                            _seen_for_targets3.add(_instr.argval)
                            if _eff_expr_instrs:
                                _expr = self.expr_reconstructor.reconstruct(_eff_expr_instrs)
                                if _expr:
                                    _eff_stmts.append({'type': 'Expr', 'value': _expr})
                            _eff_expr_instrs = []
                            continue
                        if _instr.opname == 'POP_TOP' and _eff_expr_instrs:
                            _expr = self.expr_reconstructor.reconstruct(_eff_expr_instrs)
                            if _expr:
                                _eff_stmts.append({'type': 'Expr', 'value': _expr})
                            _eff_expr_instrs = []
                            continue
                        if _instr.opname == 'STORE_SUBSCR' and len(_eff_expr_instrs) >= MIN_INSTRS_FOR_SUBSCR_ASSIGN:
                            _val_expr = self.expr_reconstructor.reconstruct(_eff_expr_instrs[:-2])
                            _cont_expr = self.expr_reconstructor.reconstruct([_eff_expr_instrs[-2]])
                            _idx_expr = self.expr_reconstructor.reconstruct([_eff_expr_instrs[-1]])
                            if _val_expr and _cont_expr and _idx_expr:
                                _eff_stmts.append({
                                    'type': 'Assign',
                                    'targets': [{
                                        'type': 'Subscript',
                                        'value': _cont_expr,
                                        'slice': _idx_expr,
                                        'ctx': 'Store',
                                    }],
                                    'value': _val_expr,
                                })
                            _eff_expr_instrs = []
                            continue
                        if _instr.opname.startswith('STORE') and _eff_expr_instrs:
                            _stmt = self._build_statement(_eff_expr_instrs + [_instr])
                            if _stmt:
                                _eff_stmts.append(_stmt)
                            _eff_expr_instrs = []
                            continue
                        _eff_expr_instrs.append(_instr)
                    if _eff_expr_instrs:
                        _expr = self.expr_reconstructor.reconstruct(_eff_expr_instrs)
                        if _expr:
                            _eff_has_return_succ = False
                            for _eff_succ in block.successors:
                                _eff_succ_instrs = [i for i in _eff_succ.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE')]
                                if len(_eff_succ_instrs) == 1 and _eff_succ_instrs[0].opname == 'RETURN_VALUE':
                                    _eff_has_return_succ = True
                                    self.generated_blocks.add(_eff_succ)
                                    break
                                if len(_eff_succ_instrs) == 1 and _eff_succ_instrs[0].opname == 'RETURN_CONST':
                                    _eff_has_return_succ = True
                                    self.generated_blocks.add(_eff_succ)
                                    break
                            if _eff_has_return_succ:
                                _eff_stmts.append({'type': 'Return', 'value': _expr})
                            else:
                                _eff_stmts.append({'type': 'Expr', 'value': _expr})
                stmts = _eff_stmts
                if stmts:
                    self.generated_blocks.add(block)
                    stmts.append({'type': 'Continue'})
                    return stmts
            meaningful = [i for i in block.instructions
                         if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL',
                                             'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')]
            if meaningful:
                stmts = []
                for instr in block.instructions:
                    if instr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL',
                                       'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'):
                        continue
                    result = self.expr_reconstructor.reconstruct(block.instructions, initial_stack=None)
                    if result:
                        stmts.append(result)
                    break
                self.generated_blocks.add(block)
                stmts.append({'type': 'Continue'})
                return stmts
            self.generated_blocks.add(block)
            return [{'type': 'Continue'}]

        if block_role in (BlockRole.BREAK, BlockRole.PURE_BREAK):
            if block_role == BlockRole.PURE_BREAK:
                cleanup_ops = ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP', 'POP_EXCEPT')
                user_instrs = [i for i in block.instructions if i.opname not in cleanup_ops]
                if not user_instrs:
                    self.generated_blocks.add(block)
                    return []
                self.generated_blocks.add(block)
                return [{'type': 'Break'}]
            last = block.get_last_instruction()
            if last and last.opname == 'RETURN_VALUE':
                instrs = [i for i in block.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                if ([i.opname for i in instrs] == ['POP_TOP', 'LOAD_CONST', 'RETURN_VALUE'] and
                    instrs[1].argval is None):
                    self.generated_blocks.add(block)
                    return [{'type': 'Break'}]
            if last and last.opname == 'RETURN_CONST' and last.argval is None:
                instrs = [i for i in block.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                user_instrs = [i for i in instrs if i.opname not in ('POP_TOP',)]
                if len(user_instrs) == 1 and user_instrs[0].opname == 'RETURN_CONST':
                    self.generated_blocks.add(block)
                    return [{'type': 'Break'}]

        if block_role == BlockRole.LOOP_BACK_EDGE:
            effective = self.region_analyzer.effective_instructions.get(block.start_offset)
            if effective:
                _be_stmts = []
                if effective:
                    _be_expr_instrs = []
                    _seen_for_targets4 = set()
                    for _instr in effective:
                        if _instr.opname in ('RESUME', 'NOP', 'CACHE'):
                            continue
                        if _instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF') and _instr.argval in (self._current_loop.metadata.get('for_target_names', set()) if self._current_loop else set()) and _instr.argval not in _seen_for_targets4:
                            if block == self._current_loop.header_block if self._current_loop else False:
                                _seen_for_targets4.add(_instr.argval)
                                if _be_expr_instrs:
                                    _expr = self.expr_reconstructor.reconstruct(_be_expr_instrs)
                                    if _expr:
                                        _be_stmts.append({'type': 'Expr', 'value': _expr})
                                _be_expr_instrs = []
                                continue
                        if _instr.opname == 'POP_TOP' and _be_expr_instrs:
                            _expr = self.expr_reconstructor.reconstruct(_be_expr_instrs)
                            if _expr:
                                _be_stmts.append({'type': 'Expr', 'value': _expr})
                            _be_expr_instrs = []
                            continue
                        if _instr.opname == 'STORE_SUBSCR' and len(_be_expr_instrs) >= MIN_INSTRS_FOR_SUBSCR_ASSIGN:
                            _val_expr = self.expr_reconstructor.reconstruct(_be_expr_instrs[:-2])
                            _cont_expr = self.expr_reconstructor.reconstruct([_be_expr_instrs[-2]])
                            _idx_expr = self.expr_reconstructor.reconstruct([_be_expr_instrs[-1]])
                            if _val_expr and _cont_expr and _idx_expr:
                                _be_stmts.append({
                                    'type': 'Assign',
                                    'targets': [{
                                        'type': 'Subscript',
                                        'value': _cont_expr,
                                        'slice': _idx_expr,
                                        'ctx': 'Store',
                                    }],
                                    'value': _val_expr,
                                })
                            _be_expr_instrs = []
                            continue
                        if _instr.opname.startswith('STORE') and _be_expr_instrs:
                            _stmt = self._build_statement(_be_expr_instrs + [_instr])
                            if _stmt:
                                _be_stmts.append(_stmt)
                            _be_expr_instrs = []
                            continue
                        _be_expr_instrs.append(_instr)
                    if _be_expr_instrs:
                        _be_last = block.get_last_instruction()
                        _be_is_cond_recheck = (
                            self._current_loop is not None
                            and _be_last is not None
                            and _be_last.opname in CONDITIONAL_JUMP_OPS
                            and _be_last.argval is not None
                        )
                        if _be_is_cond_recheck:
                            _be_jump_target = self.cfg.get_block_by_offset(_be_last.argval)
                            if _be_jump_target in (self._current_loop.header_block, self._current_loop.condition_block):
                                _be_has_store = any(i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
                                                    for i in _be_expr_instrs)
                                _be_has_side_effect = any(i.opname in ('CALL', 'CALL_FUNCTION', 'CALL_METHOD',
                                                                        'CALL_FUNCTION_KW', 'CALL_FUNCTION_EX',
                                                                        'DELETE_SUBSCR', 'DELETE_ATTR',
                                                                        'RAISE_VARARGS', 'IMPORT_NAME')
                                                          for i in _be_expr_instrs)
                                if not _be_has_store and not _be_has_side_effect:
                                    _be_expr_instrs = []
                        if _be_expr_instrs:
                            _expr = self.expr_reconstructor.reconstruct(_be_expr_instrs)
                            if _expr:
                                _be_has_return_succ = False
                                for _be_succ in block.successors:
                                    _be_succ_instrs = [i for i in _be_succ.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE')]
                                    if len(_be_succ_instrs) == 1 and _be_succ_instrs[0].opname == 'RETURN_VALUE':
                                        _be_has_return_succ = True
                                        self.generated_blocks.add(_be_succ)
                                        break
                                    if len(_be_succ_instrs) == 1 and _be_succ_instrs[0].opname == 'RETURN_CONST':
                                        _be_has_return_succ = True
                                        self.generated_blocks.add(_be_succ)
                                        break
                                if _be_has_return_succ:
                                    _be_stmts.append({'type': 'Return', 'value': _expr})
                                else:
                                    _be_stmts.append({'type': 'Expr', 'value': _expr})
                stmts = _be_stmts
                if stmts:
                    self.generated_blocks.add(block)
                    return stmts
            skip_ops = ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL',
                        'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')
            fallback_instrs = [i for i in block.instructions if i.opname not in skip_ops]
            if fallback_instrs:
                _fb_stmts = []
                if fallback_instrs:
                    _fb_expr_instrs = []
                    _seen_for_targets5 = set()
                    for _instr in fallback_instrs:
                        if _instr.opname in ('RESUME', 'NOP', 'CACHE'):
                            continue
                        if _instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF') and _instr.argval in (self._current_loop.metadata.get('for_target_names', set()) if self._current_loop else set()) and _instr.argval not in _seen_for_targets5:
                            if block == self._current_loop.header_block if self._current_loop else False:
                                _seen_for_targets5.add(_instr.argval)
                                if _fb_expr_instrs:
                                    _expr = self.expr_reconstructor.reconstruct(_fb_expr_instrs)
                                    if _expr:
                                        _fb_stmts.append({'type': 'Expr', 'value': _expr})
                                _fb_expr_instrs = []
                                continue
                        if _instr.opname == 'POP_TOP' and _fb_expr_instrs:
                            _expr = self.expr_reconstructor.reconstruct(_fb_expr_instrs)
                            if _expr:
                                _fb_stmts.append({'type': 'Expr', 'value': _expr})
                            _fb_expr_instrs = []
                            continue
                        if _instr.opname == 'STORE_SUBSCR' and len(_fb_expr_instrs) >= MIN_INSTRS_FOR_SUBSCR_ASSIGN:
                            _val_expr = self.expr_reconstructor.reconstruct(_fb_expr_instrs[:-2])
                            _cont_expr = self.expr_reconstructor.reconstruct([_fb_expr_instrs[-2]])
                            _idx_expr = self.expr_reconstructor.reconstruct([_fb_expr_instrs[-1]])
                            if _val_expr and _cont_expr and _idx_expr:
                                _fb_stmts.append({
                                    'type': 'Assign',
                                    'targets': [{
                                        'type': 'Subscript',
                                        'value': _cont_expr,
                                        'slice': _idx_expr,
                                        'ctx': 'Store',
                                    }],
                                    'value': _val_expr,
                                })
                            _fb_expr_instrs = []
                            continue
                        if _instr.opname.startswith('STORE') and _fb_expr_instrs:
                            _stmt = self._build_statement(_fb_expr_instrs + [_instr])
                            if _stmt:
                                _fb_stmts.append(_stmt)
                            _fb_expr_instrs = []
                            continue
                        _fb_expr_instrs.append(_instr)
                    if _fb_expr_instrs:
                        _fb_last = block.get_last_instruction()
                        _fb_is_cond_recheck = (
                            self._current_loop is not None
                            and _fb_last is not None
                            and _fb_last.opname in CONDITIONAL_JUMP_OPS
                            and _fb_last.argval is not None
                        )
                        if _fb_is_cond_recheck:
                            _fb_jump_target = self.cfg.get_block_by_offset(_fb_last.argval)
                            if _fb_jump_target in (self._current_loop.header_block, self._current_loop.condition_block):
                                _fb_has_store = any(i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
                                                    for i in _fb_expr_instrs)
                                _fb_has_side_effect = any(i.opname in ('CALL', 'CALL_FUNCTION', 'CALL_METHOD',
                                                                        'CALL_FUNCTION_KW', 'CALL_FUNCTION_EX',
                                                                        'DELETE_SUBSCR', 'DELETE_ATTR',
                                                                        'RAISE_VARARGS', 'IMPORT_NAME')
                                                          for i in _fb_expr_instrs)
                                if not _fb_has_store and not _fb_has_side_effect:
                                    _fb_expr_instrs = []
                        if _fb_expr_instrs:
                            _expr = self.expr_reconstructor.reconstruct(_fb_expr_instrs)
                            if _expr:
                                _fb_has_return_succ = False
                                for _fb_succ in block.successors:
                                    _fb_succ_instrs = [i for i in _fb_succ.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE')]
                                    if len(_fb_succ_instrs) == 1 and _fb_succ_instrs[0].opname == 'RETURN_VALUE':
                                        _fb_has_return_succ = True
                                        self.generated_blocks.add(_fb_succ)
                                        break
                                    if len(_fb_succ_instrs) == 1 and _fb_succ_instrs[0].opname == 'RETURN_CONST':
                                        _fb_has_return_succ = True
                                        self.generated_blocks.add(_fb_succ)
                                        break
                                if _fb_has_return_succ:
                                    _fb_stmts.append({'type': 'Return', 'value': _expr})
                                else:
                                    _fb_stmts.append({'type': 'Expr', 'value': _expr})
                stmts = _fb_stmts
                self.generated_blocks.add(block)
                return stmts if stmts else []
            self.generated_blocks.add(block)
            return []

        stmts: List[Dict[str, Any]] = []

        # 收集所有特殊模式检测结果，而不是首次命中就返回
        # 这对于包含多种语句类型的大块（如模块级代码）至关重要
        
        _chain_instrs = [i for i in block.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
        _chain_result = None
        if len(_chain_instrs) > MIN_INSTRS_FOR_CHAIN_ASSIGN_PATTERN:
            _store_indices = []
            for _ci, _instr in enumerate(_chain_instrs):
                if _instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                    _store_indices.append(_ci)
            if len(_store_indices) >= 2:
                _first_store_idx = _store_indices[0]
                if _first_store_idx >= 1:
                    _prev_idx = _first_store_idx - 1
                    if _chain_instrs[_prev_idx].opname == 'COPY' and _chain_instrs[_prev_idx].arg == COPY_STACK_TOP:
                        _value_start_idx = _prev_idx - 1
                        if _value_start_idx >= 0:
                            _value_instr = _chain_instrs[_value_start_idx]
                            if _value_instr.opname in ('LOAD_CONST', 'LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL'):
                                _targets = []
                                _valid_chain = True
                                for _si, _store_idx in enumerate(_store_indices):
                                    if _si > 0:
                                        _expected_copy_idx = _store_idx - 1
                                        if (_expected_copy_idx < 0 or
                                            _chain_instrs[_expected_copy_idx].opname != 'COPY' or
                                            _chain_instrs[_expected_copy_idx].arg != 1):
                                            if _si != len(_store_indices) - 1:
                                                _valid_chain = False
                                                break
                                    _store_instr = _chain_instrs[_store_idx]
                                    _targets.append({
                                        'type': 'Name',
                                        'id': _store_instr.argval,
                                        'ctx': 'Store',
                                        'lineno': _store_instr.starts_line
                                    })
                                if _valid_chain and len(_targets) >= 2:
                                    _value_expr = self.expr_reconstructor.reconstruct([_value_instr])
                                    if _value_expr is not None:
                                        _chain_stmts = [{
                                            'type': 'Assign',
                                            'targets': _targets,
                                            'value': _value_expr,
                                            'is_chain_assign': True,
                                            'lineno': _value_instr.starts_line
                                        }]
                                        _last_store_idx = _store_indices[-1]
                                        _remaining_instrs = _chain_instrs[_last_store_idx + 1:]
                                        if _remaining_instrs:
                                            _has_return = any(i.opname in ('RETURN_VALUE', 'RETURN_CONST') for i in _remaining_instrs)
                                            if _has_return:
                                                _rv_instrs = []
                                                for _instr in _remaining_instrs:
                                                    if _instr.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                                                        break
                                                    if _instr.opname not in ('RESUME', 'NOP', 'CACHE', 'POP_TOP', 'PUSH_NULL',
                                                                        'COPY', 'SWAP', 'POP_EXCEPT', 'PUSH_EXC_INFO'):
                                                        _rv_instrs.append(_instr)
                                                _return_value = self.expr_reconstructor.reconstruct(_rv_instrs) if _rv_instrs else None
                                                _chain_stmts.append({
                                                    'type': 'Return',
                                                    'value': _return_value if _return_value else {'type': 'Constant', 'value': None}
                                                })
                                        _chain_result = _chain_stmts
        if _chain_result is not None:
            stmts.extend(_chain_result)
            self.generated_blocks.add(block)
            return stmts

        try_region_cf = self.region_analyzer.find_enclosing_region(block, 'try_finally', require_finally=True)
        inlined_result = None
        if try_region_cf is not None and try_region_cf.has_finally:
            _finally_meta = try_region_cf.metadata
            _exc_path_blocks = _finally_meta.get('finally_exc_path_blocks')
            if _exc_path_blocks is None:
                _exc_path_blocks = set()
                for _fb in try_region_cf.finally_blocks:
                    if any(i.opname in ('PUSH_EXC_INFO', 'RERAISE', 'POP_EXCEPT') for i in _fb.instructions):
                        _exc_path_blocks.add(_fb)

            normal_blocks = _finally_meta.get('finally_normal_blocks')
            if normal_blocks is None:
                normal_blocks = [_fb for _fb in try_region_cf.finally_blocks if _fb not in _exc_path_blocks]

            is_finally_copy = try_region_cf.finally_copy_blocks.get(block.start_offset) is not None
            if normal_blocks:
                normal_finally = normal_blocks[0]
                last_instr_cf = block.instructions[-1] if block.instructions else None
                if last_instr_cf is not None:
                    _enhanced_copies = _finally_meta.get('enhanced_finally_copies', {})
                    _copy_meta = _enhanced_copies.get(block.start_offset, {})

                    if last_instr_cf.opname == 'JUMP_BACKWARD':
                        _is_implicit_cont = _copy_meta.get('is_implicit_continue')
                        if _is_implicit_cont is None:
                            target_cf = last_instr_cf.argval
                            if target_cf is not None:
                                target_block_cf = self.cfg.get_block_by_offset(target_cf)
                                innermost_loop_cf = self.region_analyzer.find_enclosing_region(block, 'loop')
                                if innermost_loop_cf and target_block_cf == innermost_loop_cf.header_block:
                                    _is_implicit_cont = True

                        if _is_implicit_cont and is_finally_copy:
                            inlined_result = [{'type': 'Continue'}]
                    elif last_instr_cf.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE'):
                        if self.block_role(block) in (BlockRole.BREAK, BlockRole.PURE_BREAK):
                            if is_finally_copy:
                                inlined_result = [{'type': 'Break'}]
                    elif last_instr_cf.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                        if is_finally_copy:
                            innermost_loop_cf = self.region_analyzer.find_enclosing_region(block, 'loop')
                            is_none_return = self.block_role(block) == BlockRole.RETURN_NONE
                            if innermost_loop_cf and is_none_return and block in innermost_loop_cf.body_blocks:
                                inlined_result = [{'type': 'Break'}]
                            else:
                                user_instrs = [_i for _i in block.instructions if _i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP', 'JUMP_BACKWARD', 'JUMP_FORWARD', 'JUMP_ABSOLUTE', 'COPY', 'POP_EXCEPT', 'RERAISE', 'PUSH_EXC_INFO', 'SWAP', 'PRECALL', 'RETURN_VALUE', 'RETURN_CONST') and not (_i.opname == 'LOAD_CONST' and _i.argval is None)]
                                finally_user = [_i for _i in normal_finally.instructions if _i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP', 'JUMP_BACKWARD', 'JUMP_FORWARD', 'JUMP_ABSOLUTE', 'COPY', 'POP_EXCEPT', 'RERAISE', 'PUSH_EXC_INFO', 'SWAP', 'PRECALL', 'RETURN_VALUE', 'RETURN_CONST') and not (_i.opname == 'LOAD_CONST' and _i.argval is None)]
                                remaining = user_instrs[:len(user_instrs) - len(finally_user)] if len(user_instrs) > len(finally_user) else []
                                if remaining:
                                    stmt_cf = self._build_statement(remaining)
                                    if stmt_cf:
                                        inlined_result = [stmt_cf, self._generate_return_ast(block)]
                                    else:
                                        inlined_result = [self._generate_return_ast(block)]
                                else:
                                    inlined_result = [self._generate_return_ast(block)]
        if inlined_result is not None:
            stmts.extend(inlined_result)
            self.generated_blocks.add(block)
            return stmts

        comp_stmt = self.comp_generator.try_generate_comprehension_assign(block, region_ast_gen=self)
        if comp_stmt is not None:
            stmts.extend(comp_stmt)
            self.generated_blocks.add(block)
            return stmts

        _unpack_result = None
        _has_unpack = any(i.opname in ('UNPACK_SEQUENCE', 'UNPACK_EX') for i in block.instructions)
        if _has_unpack:
            _has_unpack_ex = any(i.opname == 'UNPACK_EX' for i in block.instructions)
            if _has_unpack_ex:
                _ua_all_instrs = [i for i in block.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                _unpack_ex_idx = None
                for _idx, _instr in enumerate(_ua_all_instrs):
                    if _instr.opname == 'UNPACK_EX':
                        _unpack_ex_idx = _idx
                        break
                if _unpack_ex_idx is not None:
                    _ua_value_instrs = _ua_all_instrs[:_unpack_ex_idx]
                    _ua_value_expr = self.expr_reconstructor.reconstruct(_ua_value_instrs) if _ua_value_instrs else None
                    _ua_unpack_instr = _ua_all_instrs[_unpack_ex_idx]
                    _ua_arg = _ua_unpack_instr.argval
                    _ua_before = _ua_arg & 0xFF
                    _ua_after = (_ua_arg >> 8) & 0xFF
                    _ua_elts = []
                    _ua_idx = _unpack_ex_idx + 1
                    for _ in range(_ua_before):
                        if _ua_idx < len(_ua_all_instrs):
                            _ua_store_instr = _ua_all_instrs[_ua_idx]
                            if _ua_store_instr.opname in ('STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL', 'STORE_DEREF'):
                                _ua_elts.append({'type': 'Name', 'id': _ua_store_instr.argval, 'ctx': 'Store'})
                            _ua_idx += 1
                    if _ua_idx < len(_ua_all_instrs):
                        _ua_star_instr = _ua_all_instrs[_ua_idx]
                        if _ua_star_instr.opname in ('STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL', 'STORE_DEREF'):
                            _ua_elts.append({'type': 'Starred', 'value': {'type': 'Name', 'id': _ua_star_instr.argval, 'ctx': 'Store'}})
                        _ua_idx += 1
                    for _ in range(_ua_after):
                        if _ua_idx < len(_ua_all_instrs):
                            _ua_store_instr = _ua_all_instrs[_ua_idx]
                            if _ua_store_instr.opname in ('STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL', 'STORE_DEREF'):
                                _ua_elts.append({'type': 'Name', 'id': _ua_store_instr.argval, 'ctx': 'Store'})
                            _ua_idx += 1
                    _ua_target = {'type': 'Tuple', 'elts': _ua_elts, 'ctx': 'Store'}
                    _unpack_result = [{'type': 'Assign', 'targets': [_ua_target], 'value': _ua_value_expr}]
                else:
                    _ua_expr = self.expr_reconstructor.reconstruct(_ua_all_instrs)
                    if _ua_expr:
                        _unpack_result = [_ua_expr]
            else:
                _ua_stmts: List[Dict[str, Any]] = []
                _ua_stmt_instrs: List[Instruction] = []
                _ua_unpack_info = None
                _ua_pending_import = None
                for _instr in block.instructions:
                    if _instr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                        continue
                    if _instr.opname == 'IMPORT_NAME':
                        if _ua_stmt_instrs:
                            _ua_stmt = self._build_statement(_ua_stmt_instrs)
                            if _ua_stmt:
                                _ua_stmts.append(_ua_stmt)
                            _ua_stmt_instrs = []
                        _ua_pending_import = _instr
                        continue
                    if _instr.opname == 'IMPORT_FROM':
                        continue
                    if _instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF') and _ua_pending_import is not None:
                        _import_name = _ua_pending_import.argval
                        _alias = _instr.argval if _instr.argval != _import_name else None
                        _ua_stmts.append({'type': 'Import', 'names': [{'name': _import_name, 'asname': _alias}]})
                        _ua_pending_import = None
                        continue
                    if _instr.opname == 'UNPACK_SEQUENCE':
                        _ua_vi = [i for i in _ua_stmt_instrs if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                        _ua_val = self.expr_reconstructor.reconstruct(_ua_vi) if _ua_vi else None
                        _ua_unpack_info = {'value': _ua_val, 'targets': [], 'count': _instr.arg}
                        _ua_stmt_instrs = []
                        continue
                    if _instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                        if _ua_unpack_info is not None:
                            _ua_unpack_info['targets'].append({
                                'type': 'Name',
                                'id': _instr.argval if _instr.argval else f'var_{_instr.arg}',
                                'ctx': 'Store',
                            })
                            if len(_ua_unpack_info['targets']) == _ua_unpack_info['count']:
                                _ua_tgt = {
                                    'type': 'Tuple',
                                    'elts': _ua_unpack_info['targets'],
                                    'ctx': 'Store',
                                }
                                if _ua_unpack_info['value']:
                                    _ua_stmts.append({'type': 'Assign', 'targets': [_ua_tgt], 'value': _ua_unpack_info['value']})
                                _ua_unpack_info = None
                            _ua_stmt_instrs = []
                            continue
                        _ua_stmt_instrs.append(_instr)
                        _ua_stmt = self._build_store_statement(_ua_stmt_instrs, block=block)
                        if _ua_stmt:
                            _ua_stmts.append(_ua_stmt)
                        _ua_stmt_instrs = []
                        continue
                    if _instr.opname in ('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE'):
                        if _ua_stmt_instrs:
                            _ua_stmt = self._build_subscript_assign(_ua_stmt_instrs) or self._build_attr_assign(_ua_stmt_instrs) or self._build_statement(_ua_stmt_instrs)
                            if _ua_stmt:
                                _ua_stmts.append(_ua_stmt)
                            _ua_stmt_instrs = []
                        break
                    if _instr.opname in FORWARD_JUMP_OPS or _instr.opname in BACKWARD_JUMP_OPS:
                        if _ua_stmt_instrs:
                            _ua_stmt = self._build_subscript_assign(_ua_stmt_instrs) or self._build_attr_assign(_ua_stmt_instrs) or self._build_statement(_ua_stmt_instrs)
                            if _ua_stmt:
                                _ua_stmts.append(_ua_stmt)
                            _ua_stmt_instrs = []
                        break
                    if _instr.opname in ('DELETE_SUBSCR', 'DELETE_ATTR'):
                        if _ua_stmt_instrs:
                            _ua_stmt_instrs.append(_instr)
                            _ua_del_stmt = self._build_delete_stmt(_instr, _ua_stmt_instrs)
                        if _ua_del_stmt:
                            if isinstance(_ua_del_stmt, list):
                                _ua_stmts.extend(_ua_del_stmt)
                            else:
                                _ua_stmts.append(_ua_del_stmt)
                        _ua_stmt_instrs = []
                        continue
                    if _instr.opname in ('POP_EXCEPT', 'PUSH_EXC_INFO', 'RERAISE',
                                        'WITH_EXCEPT_START', 'CHECK_EXC_MATCH', 'CHECK_EG_MATCH'):
                        continue
                    if _instr.opname == 'POP_TOP':
                        if _ua_stmt_instrs:
                            _ua_stmt = self._build_statement(_ua_stmt_instrs)
                            if _ua_stmt:
                                _ua_stmts.append(_ua_stmt)
                            _ua_stmt_instrs = []
                        continue
                    _ua_stmt_instrs.append(_instr)
                if _ua_stmt_instrs:
                    _ua_stmt = self._build_subscript_assign(_ua_stmt_instrs) or self._build_attr_assign(_ua_stmt_instrs) or self._build_statement(_ua_stmt_instrs)
                    if _ua_stmt:
                        _ua_stmts.append(_ua_stmt)
                _unpack_result = _ua_stmts if _ua_stmts else None
        if _unpack_result is not None:
            stmts.extend(_unpack_result)
            self.generated_blocks.add(block)
            return stmts

        _await_result = None
        _has_awaitable = any(i.opname == 'GET_AWAITABLE' for i in block.instructions)
        if _has_awaitable:
            _aw_stmts: List[Dict[str, Any]] = []
            _aw_stmt_instrs: List[Instruction] = []
            _aw_after_awaitable = False
            for _instr in block.instructions:
                if _instr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP'):
                    continue
                if _instr.opname == 'GET_AWAITABLE':
                    _aw_stmt_instrs.append(_instr)
                    _aw_after_awaitable = True
                    continue
                if _aw_after_awaitable and _instr.opname == 'LOAD_CONST' and _instr.argval is None:
                    continue
                if _aw_after_awaitable and _instr.opname == 'SEND':
                    continue
                if _instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                    _aw_stmt_instrs.append(_instr)
                    _aw_stmt = self._build_store_statement(_aw_stmt_instrs, block=block)
                    if _aw_stmt:
                        _aw_stmts.append(_aw_stmt)
                    _aw_stmt_instrs = []
                    continue
                if _instr.opname in ('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE',
                                    'JUMP_BACKWARD_NO_INTERRUPT'):
                    break
                if _instr.opname in FORWARD_JUMP_OPS or _instr.opname in BACKWARD_JUMP_OPS:
                    break
                _aw_stmt_instrs.append(_instr)
            if _aw_stmt_instrs:
                _aw_expr = self.expr_reconstructor.reconstruct(_aw_stmt_instrs)
                if _aw_expr:
                    if _aw_expr.get('type') == 'Await':
                        _aw_stmts.append({'type': 'Expr', 'value': _aw_expr})
                    else:
                        _aw_stmt = self._build_statement(_aw_stmt_instrs)
                        if _aw_stmt:
                            _aw_stmts.append(_aw_stmt)
            _await_result = _aw_stmts if _aw_stmts else None
        if _await_result is not None:
            stmts.extend(_await_result)
            self.generated_blocks.add(block)
            return stmts

        if self.block_role(block) == BlockRole.AWAIT_SEND:
            self.generated_blocks.add(block)
            return stmts

        _boolop_result = None
        _has_boolop = any(self.detector.is_short_circuit_jump(i) for i in block.instructions)
        if _has_boolop:
            _bo_last_instr = block.get_last_instruction()
            if not _bo_last_instr or not self.detector.is_short_circuit_jump(_bo_last_instr):
                for _instr in reversed(block.instructions):
                    if self.detector.is_short_circuit_jump(_instr):
                        _bo_last_instr = _instr
                        break
                if not _bo_last_instr:
                    _has_boolop = False
            if _has_boolop:
                _bo_all_instrs = [i for i in block.instructions
                             if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                _bo_expr = self.expr_reconstructor.reconstruct(_bo_all_instrs)
                if _bo_expr is not None:
                    _bo_succ = block.conditional_successors
                    if len(_bo_succ) >= 2:
                        _bo_merge_offset = _bo_last_instr.argval
                        _bo_merge_block = self.cfg.get_block_by_offset(_bo_merge_offset)
                        if _bo_merge_block:
                            _bo_merge_instrs = [i for i in _bo_merge_block.instructions
                                           if i.opname not in ('RESUME', 'NOP', 'CACHE')]
                            _bo_store_instrs = []
                            for _i in _bo_merge_instrs:
                                if _i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL',
                                                'STORE_DEREF'):
                                    _bo_store_instrs.append(_i)
                            if _bo_store_instrs:
                                _bo_target_name = _bo_store_instrs[-1].argval if _bo_store_instrs[-1].argval else f'var_{_bo_store_instrs[-1].arg}'
                                _boolop_result = [{
                                    'type': 'Assign',
                                    'targets': [{'type': 'Name', 'id': _bo_target_name, 'ctx': 'Store'}],
                                    'value': _bo_expr,
                                }]
                    if _boolop_result is None and _bo_expr is not None:
                        _boolop_result = [{'type': 'Expr', 'value': _bo_expr}]
        if _boolop_result is not None:
            stmts.extend(_boolop_result)
            self.generated_blocks.add(block)
            return stmts

        _cond_jump_bs = None
        for _cjb_i in block.instructions:
            if _cjb_i.opname in CONDITIONAL_JUMP_OPS or _cjb_i.opname in FORWARD_CONDITIONAL_JUMP_OPS or _cjb_i.opname in BACKWARD_CONDITIONAL_JUMP_OPS:
                _cond_jump_bs = _cjb_i
                break
        if _cond_jump_bs is None:
            _cjb_last = block.get_last_instruction()
            if _cjb_last and _cjb_last.opname in FORWARD_CONDITIONAL_JUMP_OPS | BACKWARD_CONDITIONAL_JUMP_OPS:
                _cond_jump_bs = _cjb_last

        if _cond_jump_bs is not None and len(block.conditional_successors) >= 2:
            if _cjb_parent is not None:
                _cjb_succs_check = list(block.conditional_successors)
                if _cjb_parent in _cjb_succs_check:
                    _cond_jump_bs = None
            if _cond_jump_bs is not None:
                _cjb_succs = list(block.conditional_successors)
                _cjb_jump_target = _cond_jump_bs.argval
                _cjb_then_entry = None
                _cjb_else_entry = None
                for _cjb_cs in _cjb_succs:
                    if _cjb_cs.start_offset == _cjb_jump_target:
                        _cjb_else_entry = _cjb_cs
                    else:
                        _cjb_then_entry = _cjb_cs
                if _cjb_then_entry is None and len(_cjb_succs) >= 1:
                    _cjb_then_entry = _cjb_succs[0]
                if _cjb_else_entry is None and len(_cjb_succs) >= 2:
                    _cjb_else_entry = _cjb_succs[1]

                _cjb_cond_instrs = []
                for _cjb_ci in block.instructions:
                    if _cjb_ci.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                        continue
                    if _cjb_ci.opname in CONDITIONAL_JUMP_OPS or _cjb_ci.opname in FORWARD_CONDITIONAL_JUMP_OPS or _cjb_ci.opname in BACKWARD_CONDITIONAL_JUMP_OPS:
                        continue
                    if _cjb_ci.opname in FORWARD_JUMP_OPS or _cjb_ci.opname in BACKWARD_JUMP_OPS:
                        continue
                    if _cjb_ci.opname in ('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE'):
                        continue
                    _cjb_cond_instrs.append(_cjb_ci)

                _cjb_pre_stmts = []
                _cjb_pure_cond = []
                _cjb_last_store = -1
                for _cjb_pi, _cjb_pci in enumerate(_cjb_cond_instrs):
                    if _cjb_pci.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                        _cjb_last_store = _cjb_pi
                if _cjb_last_store >= 0:
                    _cjb_accum = []
                    for _cjb_pi, _cjb_pci in enumerate(_cjb_cond_instrs):
                        if _cjb_pi <= _cjb_last_store:
                            _cjb_accum.append(_cjb_pci)
                            if _cjb_pci.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                                _cjb_s = self._build_store_statement(_cjb_accum, block=block)
                                if _cjb_s:
                                    _cjb_pre_stmts.append(_cjb_s)
                                _cjb_accum = []
                        else:
                            _cjb_pure_cond.append(_cjb_pci)
                    if _cjb_accum:
                        _cjb_pure_cond.extend(_cjb_accum)
                else:
                    _cjb_pure_cond = _cjb_cond_instrs

                _cjb_cond_expr = None
                if _cjb_pure_cond:
                    _cjb_cond_expr = self.expr_reconstructor.reconstruct(_cjb_pure_cond)
                if _cjb_cond_expr is None:
                    _cjb_cond_expr = {'type': 'Constant', 'value': True}

                _cjb_negate = False
                if _cjb_then_entry and _cjb_jump_target is not None:
                    if _cjb_then_entry.start_offset == _cjb_jump_target:
                        _cjb_negate = True
                if _cjb_negate:
                    _cjb_cond_expr = _negate_expr(_cjb_cond_expr)

                _cjb_then_blocks = [_cjb_then_entry] if _cjb_then_entry else []
                _cjb_else_blocks = [_cjb_else_entry] if _cjb_else_entry else []

                _cjb_pending = [b for b in (_cjb_then_blocks + _cjb_else_blocks) if b not in self.generated_blocks]
                for _gb in _cjb_pending:
                    self.generated_blocks.add(_gb)

                _cjb_then_stmts = []
                for _tb in _cjb_then_blocks:
                    if _tb in _cjb_pending:
                        self.generated_blocks.discard(_tb)
                        _ts = self._generate_block_statements(_tb, _cjb_parent=block)
                        self.generated_blocks.add(_tb)
                        if _ts:
                            _cjb_then_stmts.extend(_ts)

                _cjb_else_stmts = []
                for _eb in _cjb_else_blocks:
                    if _eb in _cjb_pending:
                        self.generated_blocks.discard(_eb)
                        _es = self._generate_block_statements(_eb, _cjb_parent=block)
                        self.generated_blocks.add(_eb)
                        if _es:
                            _cjb_else_stmts.extend(_es)

                if not _cjb_then_stmts:
                    _cjb_then_stmts = [{'type': 'Pass'}]

                _cjb_if_node = {
                    'type': 'If',
                    'test': _cjb_cond_expr,
                    'body': _cjb_then_stmts,
                    'orelse': _cjb_else_stmts if _cjb_else_stmts else None,
                }
                if _cjb_pre_stmts:
                    stmts.extend(_cjb_pre_stmts)
                stmts.append(_cjb_if_node)
                self.generated_blocks.add(block)
                return stmts

        stmt_instrs: List[Instruction] = []
        skip_offsets: Set[int] = set()
        _import_skip = False

        for instr in block.instructions:
            if instr.opname in self.SKIP_OPS:
                continue

            if _import_skip:
                if instr.opname in ('IMPORT_FROM', 'POP_TOP'):
                    continue
                if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                    stmt_instrs = []
                    _import_skip = False
                    continue
                _import_skip = False

            if instr.opname == 'IMPORT_NAME':
                module_name = instr.argval if instr.argval else ''
                instr_idx = block.instructions.index(instr)
                has_import_from = False
                _scan_start = instr_idx + 1
                _max_lookahead = 3
                for _i in range(_scan_start, min(_scan_start + _max_lookahead, len(block.instructions))):
                    if block.instructions[_i].opname == 'IMPORT_FROM':
                        has_import_from = True
                        break
                    elif block.instructions[_i].opname not in ('LOAD_CONST', 'PUSH_NULL'):
                        break
                if has_import_from:
                    from_names = []
                    _i = instr_idx + 1
                    while _i < len(block.instructions) - 1:
                        curr = block.instructions[_i]
                        next_instr = block.instructions[_i + 1]
                        if curr.opname == 'IMPORT_FROM':
                            imported_name = curr.argval if curr.argval else ''
                            stored_name = None
                            if next_instr.opname in ('STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL'):
                                stored_name = next_instr.argval
                                _i += 2
                            elif next_instr.opname == 'IMPORT_FROM':
                                stored_name = imported_name
                                _i += 1
                            else:
                                stored_name = imported_name
                                _i += 1
                                continue
                            if imported_name:
                                from_names.append((imported_name, stored_name))
                            continue
                        elif curr.opname in ('STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL'):
                            _i += 1
                            continue
                        elif curr.opname in ('LOAD_CONST', 'PUSH_NULL', 'POP_TOP'):
                            _i += 1
                            continue
                        else:
                            break
                    if from_names:
                        names_list = []
                        for _imported, _stored in from_names:
                            if _imported != _stored:
                                names_list.append({'name': _imported, 'asname': _stored})
                            else:
                                names_list.append({'name': _imported, 'asname': None})
                        stmts.append({'type': 'ImportFrom', 'module': module_name, 'names': names_list})
                else:
                    store_names = []
                    for _i in range(instr_idx + 1, len(block.instructions)):
                        next_instr = block.instructions[_i]
                        if next_instr.opname in ('STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL'):
                            store_names.append(next_instr.argval)
                        elif next_instr.opname == 'POP_TOP':
                            pass
                        elif next_instr.opname in ('LOAD_CONST',) and not store_names:
                            pass
                        else:
                            break
                    if store_names:
                        if len(store_names) == 1 and store_names[0] != module_name:
                            aliases = [{'name': module_name, 'asname': store_names[0]}]
                        else:
                            aliases = [{'name': name, 'asname': None} for name in store_names]
                        stmts.append({'type': 'Import', 'names': aliases})
                    else:
                        stmts.append({'type': 'Import', 'names': [{'name': module_name, 'asname': None}]})
                stmt_instrs = []
                _import_skip = True
                continue
            if instr.opname == 'IMPORT_FROM':
                stmt_instrs = []
                continue

            if instr.opname == 'STORE_ATTR' and stmt_instrs:
                attr_stmt = self._build_attr_assign(stmt_instrs + [instr])
                if attr_stmt:
                    stmts.append(attr_stmt)
                    stmt_instrs = []
                    continue

            if instr.opname == 'STORE_SUBSCR' and stmt_instrs:
                subscr_stmt = self._build_subscript_assign(stmt_instrs + [instr])
                if subscr_stmt:
                    stmts.append(subscr_stmt)
                    stmt_instrs = []
                    continue

            if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                _ft_names = self._current_loop.metadata.get('for_target_names', set()) if self._current_loop else set()
                _ft_debug = f'[FT-DEBUG] {instr.opname} {instr.argval!r} loop={self._current_loop is not None} ft={_ft_names} role={self.block_role(block)}'
                if instr.argval in _ft_names and self.block_role(block) in (BlockRole.LOOP_BODY, BlockRole.NORMAL):
                    if not hasattr(self, '_gbs_seen_ft'):
                        self._gbs_seen_ft = set()
                    if instr.argval not in self._gbs_seen_ft:
                        self._gbs_seen_ft.add(instr.argval)
                        if stmt_instrs:
                            _stmt = self._build_statement(stmt_instrs)
                            if _stmt:
                                stmts.append(_stmt)
                            stmt_instrs = []
                        continue
            if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF') and stmt_instrs:
                has_copy = any(i.opname == 'COPY' and i.arg == 1 for i in stmt_instrs)
                if has_copy:
                    remaining = block.instructions[block.instructions.index(instr)+1:]
                    next_store_idx = None
                    for ri_idx, ri in enumerate(remaining):
                        if ri.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                            continue
                        if ri.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                            next_store_idx = ri_idx
                            break
                        break
                    if next_store_idx is not None:
                        chained_targets = [{
                            'type': 'Name',
                            'id': instr.argval,
                            'ctx': 'Store',
                            'lineno': instr.starts_line
                        }]
                        skip_remaining = set()
                        for ri_idx, ri in enumerate(remaining):
                            if ri.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                                continue
                            if ri.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                                chained_targets.append({
                                    'type': 'Name',
                                    'id': ri.argval,
                                    'ctx': 'Store',
                                    'lineno': ri.starts_line
                                })
                                skip_remaining.add(ri.offset)
                                continue
                            break
                        value_instrs_no_copy = [i for i in stmt_instrs if i.opname != 'COPY' or i.arg != 1]
                        value = self.expr_reconstructor.reconstruct(value_instrs_no_copy) if value_instrs_no_copy else None
                        if value is not None:
                            stmts.append({
                                'type': 'Assign',
                                'targets': chained_targets,
                                'value': value,
                                'is_chain_assign': True,
                            })
                        stmt_instrs = []
                        skip_offsets.update(skip_remaining)
                        continue
                store_stmt = self._build_store_statement(stmt_instrs + [instr], block=block)
                if store_stmt:
                    stmts.append(store_stmt)
                stmt_instrs = []
                continue

            if instr.opname == 'RAISE_VARARGS':
                if instr.arg == 0:
                    stmts.append({'type': 'Raise', 'exc': None})
                elif instr.arg == 2 and stmt_instrs:
                    cause_instr = stmt_instrs[-1]
                    exc_instrs = stmt_instrs[:-1]
                    cause_expr = self.expr_reconstructor.reconstruct([cause_instr])
                    exc_expr = self.expr_reconstructor.reconstruct(exc_instrs) if exc_instrs else None
                    stmts.append({'type': 'Raise', 'exc': exc_expr, 'cause': cause_expr})
                else:
                    exc_expr = None
                    if stmt_instrs:
                        exc_expr = self.expr_reconstructor.reconstruct(stmt_instrs)
                    if exc_expr is None and stmt_instrs:
                        exc_expr = self._build_statement(stmt_instrs)
                        if exc_expr and exc_expr.get('type') == 'Expr':
                            exc_expr = exc_expr.get('value')
                    stmts.append({'type': 'Raise', 'exc': exc_expr})
                stmt_instrs = []
                continue

            if instr.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                if self.cfg.name == '<module>':
                    if stmt_instrs:
                        is_only_load_none = (len(stmt_instrs) == 1 and
                                             stmt_instrs[0].opname == 'LOAD_CONST' and
                                             stmt_instrs[0].argval is None)
                        if not is_only_load_none:
                            stmt = self._build_statement(stmt_instrs)
                            if stmt:
                                stmts.append(stmt)
                    stmt_instrs = []
                    continue
                if stmt_instrs:
                    ret_expr = self.expr_reconstructor.reconstruct(stmt_instrs)
                    if ret_expr and not (ret_expr.get('type') == 'Constant' and ret_expr.get('value') is None):
                        stmts.append({'type': 'Return', 'value': ret_expr})
                    else:
                        stmts.append({'type': 'Return', 'value': {'type': 'Constant', 'value': None}})
                else:
                    stmts.append({'type': 'Return', 'value': {'type': 'Constant', 'value': None}})
                stmt_instrs = []
                continue

            if instr.opname == 'POP_TOP' and stmt_instrs:
                pop_expr = self.expr_reconstructor.reconstruct(stmt_instrs)
                if pop_expr and pop_expr.get('type') not in ('Constant',):
                    stmts.append({'type': 'Expr', 'value': pop_expr})
                    stmt_instrs = []
                    continue
                elif pop_expr:
                    stmt_instrs = []
                    continue

            if instr.opname in ('DELETE_FAST', 'DELETE_NAME', 'DELETE_DEREF', 'DELETE_GLOBAL'):
                stmt_instrs = []
                target_name = instr.argval if instr.argval else f'var_{instr.arg}'
                stmts.append({
                    'type': 'Delete',
                    'targets': [{
                        'type': 'Name',
                        'id': target_name,
                        'ctx': 'Del',
                    }],
                })
                continue

            if instr.opname in ('DELETE_ATTR', 'DELETE_SUBSCR'):
                stmt_instrs.append(instr)
                delete_stmt = self._build_delete_stmt(instr, stmt_instrs)
                if delete_stmt:
                    if isinstance(delete_stmt, list):
                        stmts.extend(delete_stmt)
                    elif isinstance(delete_stmt, dict):
                        stmts.append(delete_stmt)
                stmt_instrs = []
                continue

            if instr.opname == 'GET_YIELD_FROM_ITER' and stmt_instrs:
                # [yield from 修复] 使用增强的 yield from 检测和重建
                # 检查后续指令是否包含 YIELD_VALUE，确认是 yield from 模式
                _remaining_in_block = block.instructions[block.instructions.index(instr)+1:]
                _is_yield_from = any(
                    i.opname == 'YIELD_VALUE' for i in _remaining_in_block[:10]  # 查看后10条指令
                )

                if _is_yield_from:
                    # 使用新的重建方法
                    yield_from_node = self.expr_reconstructor._reconstruct_yield_from(stmt_instrs + [instr])
                    if yield_from_node:
                        stmts.append({'type': 'Expr', 'value': yield_from_node})
                    else:
                        # 回退到简单重建
                        iter_expr = self.expr_reconstructor.reconstruct(stmt_instrs)
                        if iter_expr:
                            stmts.append({'type': 'Expr', 'value': {'type': 'YieldFrom', 'value': iter_expr}})
                else:
                    # 不是 yield from 模式，按普通指令处理
                    iter_expr = self.expr_reconstructor.reconstruct(stmt_instrs)
                    if iter_expr:
                        stmts.append({'type': 'Expr', 'value': {'type': 'YieldFrom', 'value': iter_expr}})
                stmt_instrs = []
                continue

            stmt_instrs.append(instr)

        # 处理剩余的多语句情况
        # 当一个块包含多条独立语句时（如 while 循环体），需要正确分割
        if stmt_instrs:
            if (len(stmt_instrs) == 1 and
                stmt_instrs[0].opname == 'LOAD_CONST' and stmt_instrs[0].argval is None):
                has_yield_from_before = any(
                    i.opname == 'GET_YIELD_FROM_ITER'
                    for i in block.instructions
                    if i.offset < stmt_instrs[0].offset
                )
                if has_yield_from_before:
                    stmt_instrs = []
        if stmt_instrs:
            return_succ = None
            for succ in block.conditional_successors:
                if self.block_role(succ) in (BlockRole.RETURN, BlockRole.RETURN_NONE):
                    return_succ = succ
                    break
            if return_succ is None:
                for succ in getattr(block, 'successors', []):
                    check = succ
                    visited = set()
                    while check and id(check) not in visited:
                        visited.add(id(check))
                        meaningful = [i for i in check.instructions
                                      if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                        is_simple_return = (
                            len(meaningful) == 1 and
                            meaningful[0].opname in ('RETURN_VALUE', 'RETURN_CONST')
                        )
                        if is_simple_return:
                            return_succ = check
                            break
                        is_swap_only = (
                            all(i.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'SWAP', 'POP_TOP')
                                for i in check.instructions) and
                            any(i.opname == 'SWAP' for i in check.instructions)
                        )
                        is_ret_cleanup = (
                            any(i.opname == 'POP_EXCEPT' for i in meaningful) and
                            any(i.opname == 'RETURN_VALUE' for i in meaningful) and
                            not any(i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL',
                                                      'POP_EXCEPT', 'DELETE_FAST', 'LOAD_CONST',
                                                      'STORE_FAST', 'RETURN_VALUE', 'POP_TOP',
                                                      'SWAP')
                                    for i in meaningful)
                        )
                        if is_ret_cleanup:
                            return_succ = check
                            break
                        if is_swap_only:
                            swap_succs = getattr(check, 'successors', [])
                            if len(swap_succs) == 1:
                                check = swap_succs[0]
                                continue
                        break
            if return_succ is not None:
                return_stmt = None
                if self.cfg.name != '<module>':
                    ret_expr = self.expr_reconstructor.reconstruct(stmt_instrs)
                    if ret_expr and not (ret_expr.get('type') == 'Constant' and ret_expr.get('value') is None):
                        return_stmt = {'type': 'Return', 'value': ret_expr}
                    else:
                        _sp1_filtered = [i for i in stmt_instrs if i.opname not in self.SKIP_OPS]
                        _sp1_split = []
                        if stmt_instrs and len(stmt_instrs) > 2 and len(_sp1_filtered) > 2:
                            _sp1_store_positions = []
                            for _sp1_idx, _sp1_instr in enumerate(_sp1_filtered):
                                if _sp1_instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL',
                                                  'STORE_DEREF', 'STORE_SUBSCR', 'STORE_ATTR'):
                                    _sp1_store_positions.append(_sp1_idx)
                            if len(_sp1_store_positions) > 1:
                                _sp1_is_chain = True
                                for _sp1_si in _sp1_store_positions:
                                    if _sp1_si > 0 and _sp1_filtered[_sp1_si - 1].opname != 'COPY':
                                        _sp1_is_chain = False
                                        break
                                if not (_sp1_is_chain and len(_sp1_store_positions) >= 2):
                                    _sp1_start = 0
                                    for _sp1_si in _sp1_store_positions:
                                        _sp1_chunk = _sp1_filtered[_sp1_start:_sp1_si + 1]
                                        if _sp1_chunk:
                                            _sp1_stmt = self._build_statement(_sp1_chunk)
                                            if _sp1_stmt:
                                                _sp1_split.append(_sp1_stmt)
                                        _sp1_start = _sp1_si + 1
                                    if _sp1_start < len(_sp1_filtered):
                                        _sp1_remaining = _sp1_filtered[_sp1_start:]
                                        if _sp1_remaining and _sp1_remaining[-1].opname in ('JUMP_BACKWARD', 'JUMP_ABSOLUTE'):
                                            pass
                                        else:
                                            _sp1_expr = self.expr_reconstructor.reconstruct(_sp1_remaining)
                                            if _sp1_expr:
                                                _sp1_split.append({'type': 'Expr', 'value': _sp1_expr})
                        split = _sp1_split
                        if len(split) > 1:
                            last = split[-1]
                            if last.get('type') == 'Expr':
                                val = last.get('value')
                                if val and not (val.get('type') == 'Constant' and val.get('value') is None):
                                    split[-1] = {'type': 'Return', 'value': val}
                                    stmts.extend(split)
                                    self.generated_blocks.add(block)
                                    if hasattr(return_succ, 'instructions'):
                                        self.generated_blocks.add(return_succ)
                                    return stmts
                            elif last.get('type') == 'Assign':
                                val = last.get('value')
                                if val and not (val.get('type') == 'Constant' and val.get('value') is None):
                                    split[-1] = {'type': 'Return', 'value': val}
                                    stmts.extend(split)
                                    self.generated_blocks.add(block)
                                    if hasattr(return_succ, 'instructions'):
                                        self.generated_blocks.add(return_succ)
                                    return stmts
                if return_stmt:
                    stmts.append(return_stmt)
                    # 只有当return_succ不属于任何独立的顶层Region时才标记
                    # 如果return_succ有自己的Region（如WI2的return @134），
                    # 应该让该Region负责生成，避免重复或丢失
                    succ_region = self.region_analyzer.get_region_for_block(return_succ)
                    if not succ_region or succ_region.parent is not None:
                        self.generated_blocks.add(return_succ)
                    self.generated_blocks.add(block)
                    return stmts
            
            # 尝试将多条指令分割为独立语句
            _sp2_filtered = [i for i in stmt_instrs if i.opname not in self.SKIP_OPS]
            _sp2_split = []
            if stmt_instrs and len(stmt_instrs) > 2 and len(_sp2_filtered) > 2:
                _sp2_store_positions = []
                for _sp2_idx, _sp2_instr in enumerate(_sp2_filtered):
                    if _sp2_instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL',
                                      'STORE_DEREF', 'STORE_SUBSCR', 'STORE_ATTR'):
                        _sp2_store_positions.append(_sp2_idx)
                if len(_sp2_store_positions) > 1:
                    _sp2_is_chain = True
                    for _sp2_si in _sp2_store_positions:
                        if _sp2_si > 0 and _sp2_filtered[_sp2_si - 1].opname != 'COPY':
                            _sp2_is_chain = False
                            break
                    if not (_sp2_is_chain and len(_sp2_store_positions) >= 2):
                        _sp2_start = 0
                        for _sp2_si in _sp2_store_positions:
                            _sp2_chunk = _sp2_filtered[_sp2_start:_sp2_si + 1]
                            if _sp2_chunk:
                                _sp2_stmt = self._build_statement(_sp2_chunk)
                                if _sp2_stmt:
                                    _sp2_split.append(_sp2_stmt)
                            _sp2_start = _sp2_si + 1
                        if _sp2_start < len(_sp2_filtered):
                            _sp2_remaining = _sp2_filtered[_sp2_start:]
                            if _sp2_remaining and _sp2_remaining[-1].opname in ('JUMP_BACKWARD', 'JUMP_ABSOLUTE'):
                                pass
                            else:
                                _sp2_expr = self.expr_reconstructor.reconstruct(_sp2_remaining)
                                if _sp2_expr:
                                    _sp2_split.append({'type': 'Expr', 'value': _sp2_expr})
            split_stmts = _sp2_split
            if len(split_stmts) > 1:
                stmts.extend(split_stmts)
            else:
                stmt = self._build_statement(stmt_instrs)
                if stmt:
                    stmts.append(stmt)

        if stmts and self.cfg.name != '<module>':
            has_return_value = any(i.opname in ('RETURN_VALUE', 'RETURN_CONST') for i in block.instructions)
            if has_return_value:
                last = stmts[-1]
                if isinstance(last, dict) and last.get('type') == 'Expr':
                    val = last.get('value')
                    if isinstance(val, dict) and val.get('type') == 'Compare':
                        stmts[-1] = {'type': 'Return', 'value': val}
            else:
                all_succs_are_return = False
                cond_succs = getattr(block, 'conditional_successors', [])
                if cond_succs and len(cond_succs) >= 2:
                    all_succs_are_return = all(
                        self.block_role(s) in (BlockRole.RETURN, BlockRole.RETURN_NONE)
                        for s in cond_succs
                    )
                if all_succs_are_return:
                    last = stmts[-1]
                    if isinstance(last, dict) and last.get('type') == 'Expr':
                        val = last.get('value')
                        if isinstance(val, dict) and val.get('type') == 'Compare':
                            stmts[-1] = {'type': 'Return', 'value': val}
                            for succ in cond_succs:
                                self.generated_blocks.add(succ)

        self.generated_blocks.add(block)
        return stmts

    def _process_instruction(self, instr, block, stmt_instrs=None):
        opname = instr.opname

        if opname == 'IMPORT_NAME':
            module_name = instr.argval if instr.argval else ''
            instr_idx = block.instructions.index(instr)

            has_import_from = False
            _scan_start = instr_idx + 1
            _max_lookahead = 3
            for i in range(_scan_start, min(_scan_start + _max_lookahead, len(block.instructions))):
                if block.instructions[i].opname == 'IMPORT_FROM':
                    has_import_from = True
                    break
                elif block.instructions[i].opname not in ('LOAD_CONST', 'PUSH_NULL'):
                    break

            if has_import_from:
                from_names = []
                i = instr_idx + 1
                while i < len(block.instructions) - 1:
                    curr = block.instructions[i]
                    next_instr = block.instructions[i + 1]
                    if curr.opname == 'IMPORT_FROM':
                        imported_name = curr.argval if curr.argval else ''
                        stored_name = None
                        if next_instr.opname in ('STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL'):
                            stored_name = next_instr.argval
                            i += 2
                        elif next_instr.opname == 'IMPORT_FROM':
                            stored_name = imported_name
                            i += 1
                        else:
                            stored_name = imported_name
                            i += 1
                            continue
                        if imported_name:
                            from_names.append((imported_name, stored_name))
                        continue
                    elif curr.opname in ('STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL'):
                        i += 1
                        continue
                    elif curr.opname in ('LOAD_CONST', 'PUSH_NULL', 'POP_TOP'):
                        i += 1
                        continue
                    else:
                        break
                if from_names:
                    names_list = []
                    for imported, stored in from_names:
                        if imported != stored:
                            names_list.append({'name': imported, 'asname': stored})
                        else:
                            names_list.append({'name': imported, 'asname': None})
                    return [{'type': 'ImportFrom', 'module': module_name, 'names': names_list}]

            store_names = []
            for i in range(instr_idx + 1, len(block.instructions)):
                next_instr = block.instructions[i]
                if next_instr.opname in ('STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL'):
                    store_names.append(next_instr.argval)
                elif next_instr.opname == 'POP_TOP':
                    pass
                elif next_instr.opname in ('LOAD_CONST',) and not store_names:
                    pass
                else:
                    break
            if store_names:
                if len(store_names) == 1 and store_names[0] != module_name:
                    aliases = [{'name': module_name, 'asname': store_names[0]}]
                else:
                    aliases = [{'name': name, 'asname': None} for name in store_names]
                return [{'type': 'Import', 'names': aliases}]
            return [{'type': 'Import', 'names': [{'name': module_name, 'asname': None}]}]

        elif opname == 'IMPORT_FROM':
            return None

        if opname in ('DELETE_ATTR', 'DELETE_SUBSCR'):
            return self._build_delete_stmt(instr, stmt_instrs)

        return _UNHANDLED

    SKIP_OPS = frozenset({'RESUME', 'NOP', 'CACHE', 'PUSH_NULL',
                          'POP_EXCEPT', 'PUSH_EXC_INFO', 'RERAISE',
                          'WITH_EXCEPT_START', 'CHECK_EXC_MATCH', 'CHECK_EG_MATCH',
                          'SWAP'})

    def _build_delete_stmt(self, delete_instr, stmt_instrs):
        """
        构建Delete语句AST节点

        对于 del a.b.c:
        - stmt_instrs 包含: [LOAD_NAME(a), LOAD_ATTR(b), DELETE_ATTR(c)]
        - 需要重建完整的目标表达式: a.b.c

        Args:
            delete_instr: DELETE_ATTR 或 DELETE_SUBSCR 指令
            stmt_instrs: 导致该delete的指令序列（包含构建对象引用的指令）

        Returns:
            Delete AST节点列表
        """
        if not stmt_instrs or len(stmt_instrs) < 1:
            return None

        delete_op = delete_instr.opname

        if delete_op == 'DELETE_ATTR':
            attr_name = delete_instr.argval if delete_instr.argval else ''

            load_instrs = [i for i in stmt_instrs[:-1]
                          if i.opname in ('LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL',
                                          'LOAD_ATTR', 'LOAD_DEREF')]

            if not load_instrs:
                return None

            target_expr = self._reconstruct_delete_target(load_instrs, attr_name, is_attr=True)

            if target_expr:
                return [{'type': 'Delete', 'targets': [target_expr]}]

        elif delete_op == 'DELETE_SUBSCR':
            load_instrs = [i for i in stmt_instrs[:-1]
                          if i.opname in ('LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL',
                                          'LOAD_ATTR', 'LOAD_DEREF', 'LOAD_CONST')]

            if not load_instrs or len(load_instrs) < 2:
                return None

            target_expr = self._reconstruct_delete_target(load_instrs, None, is_attr=False)

            if target_expr:
                return [{'type': 'Delete', 'targets': [target_expr]}]

        return None

    def _reconstruct_delete_target(self, load_instrs, last_attr=None, is_attr=True):
        """
        从加载指令序列重建delete目标表达式

        对于 del a.b.c (is_attr=True):
        - load_instrs: [LOAD_NAME(a), LOAD_ATTR(b)]
        - last_attr: 'c'
        - 返回: Attribute(value=Attribute(value=Name('a'), attr='b'), attr='c')

        对于 del a[i] (is_attr=False):
        - load_instrs: [LOAD_NAME(a), LOAD_CONST(i)]
        - 返回: Subscript(value=Name('a'), slice=Constant(i))

        Args:
            load_instrs: 加载指令列表
            last_attr: 最后一个属性名（仅用于 DELETE_ATTR）
            is_attr: 是否是属性删除（True）或下标删除（False）

        Returns:
            目标表达式AST节点
        """
        if not load_instrs:
            return None

        stack = []

        for instr in load_instrs:
            opname = instr.opname

            if opname in ('LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF'):
                var_name = instr.argval if instr.argval else f'var_{instr.arg}'
                stack.append({
                    'type': 'Name',
                    'id': var_name,
                    'ctx': 'Del'
                })

            elif opname == 'LOAD_ATTR':
                attr_name = instr.argval if instr.argval else ''
                if stack:
                    value = stack.pop()
                    stack.append({
                        'type': 'Attribute',
                        'value': value,
                        'attr': attr_name,
                        'ctx': 'Del'
                    })

            elif opname == 'LOAD_CONST':
                stack.append({
                    'type': 'Constant',
                    'value': instr.argval
                })

        if not stack:
            return None

        target = stack[-1]

        if is_attr and last_attr:
            target = {
                'type': 'Attribute',
                'value': target,
                'attr': last_attr,
                'ctx': 'Del'
            }
        elif not is_attr and len(stack) >= 2:
            index = stack[-1]
            value = stack[-2]
            target = {
                'type': 'Subscript',
                'value': value,
                'slice': index,
                'ctx': 'Del'
            }

        return target

    def _generate_stmts_from_instrs(self, instrs: List[Instruction], block: BasicBlock) -> List[Dict[str, Any]]:
        """从指令列表中提取多条语句，用于回边块等多语句场景"""
        _stmts: List[Dict[str, Any]] = []
        _buf: List[Instruction] = []
        for _instr in instrs:
            if _instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF') and _buf:
                _stmt = self._build_store_statement(_buf + [_instr], block=block)
                if _stmt:
                    _stmts.append(_stmt)
                _buf = []
                continue
            if _instr.opname == 'POP_TOP' and _buf:
                _stmt = self._build_statement(_buf)
                if _stmt:
                    _stmts.append(_stmt)
                _buf = []
                continue
            _buf.append(_instr)
        if _buf:
            _stmt = self._build_statement(_buf)
            if _stmt:
                _stmts.append(_stmt)
        return _stmts

    def _build_prefix_stmt_list(self, pre_instrs: List[Instruction], block: BasicBlock) -> List[Dict[str, Any]]:
        """
        将前缀指令序列转换为AST语句节点列表。

        区域归约算法符合度:
        ─────────────────────
        本方法服务于BoolOp/Ternary等表达式级区域的AST生成阶段。
        在区域归约完成后，区域的前缀块(prefix_block)中可能包含需要在
        表达式语句之前执行的赋值语句（如循环变量初始化、迭代器获取等）。
        本方法将这些指令正确转换为AST语句，保证字节码等价性。

        字节码模式:
        ────────────
        前缀指令通常包含:
        - LOAD_* + STORE_*: 变量赋值 (x = ...)
        - LOAD_* + CALL + POP_TOP: 表达式语句 (func())
        - GET_ITER + STORE_*: 迭代器获取 (it = iter(x))
        - FOR_ITER: 循环迭代（应在此前终止）

        参数:
            pre_instrs: identify_block_prefix_instructions返回的前缀指令列表
            block: 前缀指令所属的基本块

        返回:
            AST语句字典列表，每个元素格式为 {'type': 'Assign'|'Expr', ...}
        """
        if not pre_instrs:
            return []

        stmts = []
        buf = []

        for instr in pre_instrs:
            if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF') and buf:
                _stmt = self._build_statement(buf + [instr])
                if _stmt:
                    stmts.append(_stmt)
                buf = []
                continue
            if instr.opname == 'POP_TOP' and buf:
                expr = self.expr_reconstructor.reconstruct(buf)
                if expr:
                    stmts.append({'type': 'Expr', 'value': expr})
                buf = []
                continue
            buf.append(instr)

        if buf:
            _stmt = self._build_statement(buf)
            if _stmt:
                stmts.append(_stmt)

        return stmts

    def _build_statement(self, instrs: List[Instruction]) -> Optional[Dict[str, Any]]:
        if not instrs:
            return None

        expr = self.expr_reconstructor.reconstruct(instrs)
        if expr is None:
            return None

        if expr.get('type') == 'FunctionObject':
            return self._build_function_def(func_obj=expr)

        if expr.get('type') == 'ClassDef':
            return expr

        if expr.get('type') in ('Raise', 'Return', 'Delete', 'Assert', 'Assign', 'AugAssign', 'AnnAssign'):
            # 检查 Assign 中的 __build_class__ 调用
            # 当 expr_reconstructor.reconstruct 处理包含 STORE 指令的指令序列时，
            # 会创建 Assign 节点，其 value 可能是 __build_class__ 调用，
            # 需要将其转换为 class 定义而非保留为赋值语句
            if expr.get('type') == 'Assign':
                value = expr.get('value')
                if isinstance(value, dict):
                    if value.get('type') == 'Call':
                        targets = expr.get('targets', [])
                        target_name = None
                        if targets and isinstance(targets[0], dict):
                            target_name = targets[0].get('id')
                        func = value.get('func', {})
                        if value.get('is_class_def') or (func.get('type') == 'Name' and func.get('id') == '__build_class__'):
                            return self._build_class_def(call_expr=value, name=target_name)
                    if value.get('type') == 'FunctionObject':
                        targets = expr.get('targets', [])
                        target_name = None
                        if targets and isinstance(targets[0], dict):
                            target_name = targets[0].get('id')
                        func_def = self._build_function_def(func_obj=value)
                        if func_def.get('type') == 'Lambda':
                            return expr
                        if target_name and func_def.get('type') in ('FunctionDef', 'AsyncFunctionDef'):
                            func_def['name'] = target_name
                        return func_def
            return expr

        if expr.get('type') == 'Await':
            return {'type': 'Expr', 'value': expr}

        if expr.get('type') == 'Call':
            func = expr.get('func', {})
            args = expr.get('args', [])

            if expr.get('is_class_def') or (func.get('type') == 'Name' and func.get('id') == '__build_class__'):
                return self._build_class_def(call_expr=expr)

            class_def = self._build_class_def(call_expr=expr)
            if class_def is not None:
                return class_def

            if func.get('type') == 'Name' and func.get('id') in ('staticmethod', 'classmethod'):
                for arg in args:
                    if isinstance(arg, dict) and arg.get('type') == 'FunctionObject':
                        return self._build_function_def(func_obj=arg, decorator=func['id'])

            for arg in args:
                if isinstance(arg, dict) and arg.get('type') == 'FunctionObject':
                    return self._build_function_def(func_obj=arg, decorator=expr)

        return {
            'type': 'Expr',
            'value': expr,
        }

    def _build_store_statement(self, instrs: List[Instruction],
                                block: Optional[BasicBlock] = None) -> Optional[Dict[str, Any]]:
        if not instrs:
            return None

        store_instr = None
        value_instrs = []
        for instr in instrs:
            if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                store_instr = instr
            else:
                value_instrs.append(instr)

        if store_instr is None:
            return None

        target_name = store_instr.argval if store_instr.argval else f'var_{store_instr.arg}'

        value = None
        if value_instrs:
            value = self.expr_reconstructor.reconstruct(value_instrs)

        if value is None:
            return None

        if value.get('type') == 'FunctionObject':
            func_def = self._build_function_def(func_obj=value)
            # Lambda should be wrapped in Assign, not returned as FunctionDef
            if func_def.get('type') == 'Lambda':
                target = {
                    'type': 'Name',
                    'id': target_name,
                    'ctx': 'Store',
                }
                return {
                    'type': 'Assign',
                    'targets': [target],
                    'value': func_def,
                }
            if func_def.get('name') == target_name or func_def.get('type') in ('FunctionDef', 'AsyncFunctionDef'):
                func_def['name'] = target_name
            return func_def

        if value.get('type') == 'Call':
            func = value.get('func', {})
            args = value.get('args', [])
            if value.get('is_class_def') or (func.get('type') == 'Name' and func.get('id') == '__build_class__'):
                return self._build_class_def(call_expr=value, name=target_name)

            class_def = self._build_class_def(call_expr=value, name=target_name)
            if class_def is not None:
                return class_def
            
            for arg in args:
                if isinstance(arg, dict) and arg.get('type') == 'FunctionObject':
                    func_def = self._build_function_def(func_obj=arg, decorator=value)
                    if func_def.get('type') in ('FunctionDef', 'AsyncFunctionDef'):
                        func_def['name'] = target_name
                        return func_def
            
            _ffid_stack = [value]
            func_obj_info = None
            while _ffid_stack:
                _ffid_node = _ffid_stack.pop()
                if not isinstance(_ffid_node, dict) or _ffid_node.get('type') != 'Call':
                    continue
                _ffid_args = _ffid_node.get('args', [])
                for arg in _ffid_args:
                    if isinstance(arg, dict) and arg.get('type') == 'FunctionObject':
                        func_obj_info = (arg, _ffid_node)
                        break
                if func_obj_info:
                    break
                _ffid_func = _ffid_node.get('func', {})
                if isinstance(_ffid_func, dict) and _ffid_func.get('type') == 'Call':
                    _ffid_stack.append(_ffid_func)
                for arg in _ffid_args:
                    if isinstance(arg, dict) and arg.get('type') == 'Call':
                        _ffid_stack.append(arg)
            if func_obj_info:
                func_obj, _ = func_obj_info
                func_def = self._build_function_def(func_obj=func_obj, decorator=value)
                if func_def.get('type') in ('FunctionDef', 'AsyncFunctionDef'):
                    func_def['name'] = target_name
                    return func_def

            if func.get('type') == 'FunctionObject' and not args and block is not None:
                _fpd_visited = set()
                _fpd_stack = [block]
                dec_result = None
                while _fpd_stack:
                    _fpd_blk = _fpd_stack.pop()
                    _fpd_visited.add(_fpd_blk.id)
                    for pred in _fpd_blk.predecessors:
                        if pred.id in _fpd_visited:
                            continue
                        meaningful = [i for i in pred.instructions
                                     if i.opname not in ('RESUME', 'NOP', 'CACHE', 'POP_TOP', 'PUSH_NULL')]
                        if meaningful:
                            last = meaningful[-1]
                            if last.opname in ('LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF'):
                                dec_result = (last.argval, pred)
                                break
                        else:
                            _fpd_stack.append(pred)
                    if dec_result:
                        break
                if dec_result:
                    dec_name, dec_block = dec_result
                    decorator_call = {
                        'type': 'Call',
                        'func': {'type': 'Name', 'id': dec_name, 'ctx': 'Load'},
                        'args': [func],
                        'kwargs': [],
                    }
                    func_def = self._build_function_def(func_obj=func, decorator=decorator_call)
                    if func_def.get('type') in ('FunctionDef', 'AsyncFunctionDef'):
                        func_def['name'] = target_name
                        func_def['_decorator_block'] = dec_block
                        return func_def

        if value.get('type') == 'AugAssign':
            target = {
                'type': 'Name',
                'id': target_name,
                'ctx': 'Store',
            }
            aug = value.copy()
            aug['target'] = target
            return aug

        target = {
            'type': 'Name',
            'id': target_name,
            'ctx': 'Store',
        }

        return {
            'type': 'Assign',
            'targets': [target],
            'value': value,
        }










    def _build_subscript_assign(self, instrs: List[Instruction]) -> Optional[Dict[str, Any]]:
        store_subscr = None
        store_idx = -1
        for i, instr in enumerate(instrs):
            if instr.opname == 'STORE_SUBSCR':
                store_subscr = instr
                store_idx = i
                break

        if store_subscr is None:
            return None

        obj_instrs = instrs[:store_idx]
        if not obj_instrs:
            return None

        aug_op = None
        aug_op_idx = -1
        for i, instr in enumerate(obj_instrs):
            if instr.opname in ('BINARY_OP', 'INPLACE_ADD', 'INPLACE_SUBTRACT',
                                'INPLACE_MULTIPLY', 'INPLACE_TRUE_DIVIDE',
                                'INPLACE_FLOOR_DIVIDE', 'INPLACE_MODULO',
                                'INPLACE_POWER', 'INPLACE_LSHIFT',
                                'INPLACE_RSHIFT', 'INPLACE_AND',
                                'INPLACE_XOR', 'INPLACE_OR'):
                aug_op = instr
                aug_op_idx = i

        if aug_op:
            op_map = {
                'BINARY_OP': {0: '+', 1: '&', 2: '//', 3: '<<', 4: '@', 5: '*',
                              6: '%', 7: '|', 8: '**', 9: '>>', 10: '-', 11: '/',
                              12: '^', 13: '+=', 14: '&=', 15: '//=', 16: '<<=',
                              17: '@=', 18: '*=', 19: '%=', 20: '|=', 21: '**=',
                              22: '>>=', 23: '-=', 24: '/=', 25: '^='},
                'INPLACE_ADD': '+=',
                'INPLACE_SUBTRACT': '-=',
                'INPLACE_MULTIPLY': '*=',
                'INPLACE_TRUE_DIVIDE': '/=',
                'INPLACE_FLOOR_DIVIDE': '//=',
                'INPLACE_MODULO': '%=',
                'INPLACE_POWER': '**=',
                'INPLACE_LSHIFT': '<<=',
                'INPLACE_RSHIFT': '>>=',
                'INPLACE_AND': '&=',
                'INPLACE_XOR': '^=',
                'INPLACE_OR': '|=',
            }
            if aug_op.opname == 'BINARY_OP':
                op_symbol = op_map['BINARY_OP'].get(aug_op.arg, None)
            else:
                op_symbol = op_map.get(aug_op.opname, None)

            if op_symbol and op_symbol.endswith('='):
                pre_aug_instrs = obj_instrs[:aug_op_idx]
                value_instrs_for_recon = []
                found_binary_op = False
                for idx in range(len(pre_aug_instrs) - 1, -1, -1):
                    if pre_aug_instrs[idx].opname in ('BINARY_OP', 'BINARY_MULTIPLY',
                                                        'BINARY_ADD', 'BINARY_SUBTRACT',
                                                        'BINARY_TRUE_DIVIDE'):
                        value_instrs_for_recon = pre_aug_instrs[idx+1:]
                        found_binary_op = True
                        break
                    elif pre_aug_instrs[idx].opname in ('LOAD_CONST', 'LOAD_FAST',
                                                          'LOAD_NAME', 'LOAD_GLOBAL',
                                                          'LOAD_DEREF'):
                        continue
                    else:
                        break
                if not found_binary_op or not value_instrs_for_recon:
                    value_instrs_for_recon = []
                    copy_count = 0
                    for instr in reversed(obj_instrs[:aug_op_idx]):
                        if instr.opname == 'COPY':
                            copy_count += 1
                            if copy_count >= 2:
                                break
                        elif instr.opname not in ('COPY', 'SWAP'):
                            value_instrs_for_recon.insert(0, instr)

                value_expr = self.expr_reconstructor.reconstruct(value_instrs_for_recon) if value_instrs_for_recon else None
                if value_expr is None:
                    value_expr = {'type': 'Constant', 'value': 0}

                target_instrs = []
                obj_expr = None
                key_expr = None
                binary_subscr_idx = -1
                for idx, instr in enumerate(obj_instrs):
                    if instr.opname == 'BINARY_SUBSCR':
                        binary_subscr_idx = idx
                        break

                if binary_subscr_idx > 0:
                    load_instrs = []
                    for idx in range(binary_subscr_idx):
                        if obj_instrs[idx].opname in ('LOAD_FAST', 'LOAD_NAME',
                                                      'LOAD_GLOBAL', 'LOAD_DEREF',
                                                      'LOAD_CONST'):
                            load_instrs.append((idx, obj_instrs[idx]))

                    if len(load_instrs) >= 2:
                        obj_expr = self.expr_reconstructor.reconstruct([load_instrs[0][1]])
                        key_expr = self.expr_reconstructor.reconstruct([load_instrs[1][1]])

                if obj_expr is None:
                    obj_expr = {'type': 'Name', 'id': '_'}
                if key_expr is None:
                    key_expr = {'type': 'Constant', 'value': 0}

                target = {
                    'type': 'Subscript',
                    'value': obj_expr,
                    'slice': key_expr,
                    'ctx': 'Store',
                }

                op_simple = op_symbol.replace('=', '')
                return {
                    'type': 'AugAssign',
                    'target': target,
                    'op': op_simple,
                    'value': value_expr,
                }

        key_expr = self.expr_reconstructor.reconstruct(obj_instrs[-1:])
        if key_expr is None:
            key_expr = {'type': 'Constant', 'value': None}

        value_and_obj_instrs = obj_instrs[:-1]
        if not value_and_obj_instrs:
            return None

        obj_expr = self.expr_reconstructor.reconstruct(value_and_obj_instrs[-1:])
        if obj_expr is None:
            obj_expr = {'type': 'Name', 'id': str(value_and_obj_instrs[-1].argval), 'ctx': 'Load'}

        target = {
            'type': 'Subscript',
            'value': obj_expr,
            'slice': key_expr,
            'ctx': 'Store',
        }

        value_instrs = value_and_obj_instrs[:-1]
        if value_instrs:
            value_expr = self.expr_reconstructor.reconstruct(value_instrs)
            if value_expr is None:
                value_expr = {'type': 'Name', 'id': str(value_instrs[-1].argval), 'ctx': 'Load'}
        else:
            value_expr = {'type': 'Constant', 'value': None}

        return {
            'type': 'Assign',
            'targets': [target],
            'value': value_expr,
        }

    def _build_attr_assign(self, instrs: List[Instruction]) -> Optional[Dict[str, Any]]:
        store_attr = None
        store_idx = -1
        for i, instr in enumerate(instrs):
            if instr.opname == 'STORE_ATTR':
                store_attr = instr
                store_idx = i
                break

        if store_attr is None:
            return None

        obj_instrs = instrs[:store_idx]
        if not obj_instrs:
            return None

        # 检测增强赋值模式: COPY + ... + BINARY_OP(+=等) [+ SWAP] + STORE_ATTR
        # 字节码示例: self._count += 1
        #   LOAD_FAST self, COPY 1, LOAD_ATTR _count, LOAD_CONST 1, BINARY_OP 13(+=), [SWAP 2,] STORE_ATTR _count
        # 注意：
        #   - obj_instrs可能包含前面的无关指令，需要定位最后一个COPY段
        #   - SWAP可能被_should_skip_instruction过滤掉，所以不能依赖它
        aug_assign_ops = {
            13: '+=', 14: '&=', 15: '//=', 16: '<<=', 17: '@=',
            18: '*=', 19: '%=', 20: '|=', 21: '**=', 22: '>>=',
            23: '-=', 24: '/=', 25: '^='
        }

        # 找到所有COPY的位置（取最后一个）
        copy_indices = [i for i, instr in enumerate(obj_instrs) if instr.opname == 'COPY']

        if copy_indices:
            last_copy_idx = copy_indices[-1]

            # 检查最后一个COPY之后是否有BINARY_OP(增强赋值)
            after_copy = obj_instrs[last_copy_idx:]
            binary_op_after_copy = [(i + last_copy_idx, instr) for i, instr in enumerate(after_copy)
                                    if instr.opname == 'BINARY_OP' and aug_assign_ops.get(instr.arg)]

            if len(binary_op_after_copy) >= 1:
                # 使用第一个（或唯一一个）BINARY_OP
                # 有时候由于指令收集机制，可能出现重复的BINARY_OP，取第一个即可
                binop_global_idx, bin_op = binary_op_after_copy[0]
                op_symbol = aug_assign_ops.get(bin_op.arg)

                if op_symbol:
                    # 正确提取增强赋值的指令段
                    # 字节码顺序: ..., COPY, LOAD_ATTR target, LOAD_CONST value, BINARY_OP, [SWAP,]
                    # 
                    # 关键修正：
                    # - target_instrs 应该只包含 COPY 后的第一个非COPY指令（即 LOAD_ATTR）
                    # - value_instrs 应该包含 LOAD_ATTR 之后、BINARY_OP 之前的指令（即 LOAD_CONST）
                    # - 不能简单使用切片，因为可能包含无关指令
                    
                    # 方法1: 精确查找 LOAD_ATTR 和 LOAD_CONST 的位置
                    target_instrs = []
                    value_instrs = []
                    found_load_attr = False
                    
                    for i in range(last_copy_idx + 1, binop_global_idx):
                        instr = obj_instrs[i]
                        if not found_load_attr:
                            # 第一个非COPY指令应该是 LOAD_ATTR（目标属性）
                            if instr.opname == 'LOAD_ATTR':
                                target_instrs.append(instr)
                                found_load_attr = True
                            # 跳过其他可能的指令（理论上不应该有）
                        else:
                            # LOAD_ATTR 之后的指令是值（如 LOAD_CONST）
                            if instr.opname not in ('COPY',):
                                value_instrs.append(instr)
                    
                    # 如果没有找到 LOAD_ATTR，回退到切片方法
                    if not target_instrs:
                        target_instrs = obj_instrs[last_copy_idx+1:binop_global_idx]
                        # 假设最后一个指令是值，其余是目标
                        if len(target_instrs) > 1:
                            value_instrs = [target_instrs[-1]]
                            target_instrs = target_instrs[:-1]
                    
                    # 提取 BINARY_OP 之后的值指令（如果有，通常被过滤掉了）
                    after_binop_instrs = obj_instrs[binop_global_idx+1:]
                    # 过滤掉 SWAP 等栈操作指令
                    after_binop_filtered = [i for i in after_binop_instrs 
                                           if i.opname not in ('SWAP', 'COPY')]
                    
                    # 如果前面的 value_instrs 为空，尝试从后面获取
                    if not value_instrs and after_binop_filtered:
                        value_instrs = after_binop_filtered

                    # 构建目标表达式 (如 self._count)
                    # target_instrs 可能只有 LOAD_ATTR，不足以重建完整表达式
                    # 需要包含前面的对象加载指令（如 LOAD_NAME self）
                    target_expr = self.expr_reconstructor.reconstruct(target_instrs)
                    
                    # 如果 target_expr 为 None 或不是 Attribute 类型，尝试使用更多上下文指令
                    if target_expr is None or target_expr.get('type') != 'Attribute':
                        # 手动构建 Attribute 表达式
                        # 从 COPY 之前提取对象名（如 self）
                        obj_name = None
                        for i, instr in enumerate(obj_instrs):
                            if instr.opname == 'COPY':
                                # COPY 之前的指令应该是对象加载
                                break
                            if instr.opname in ('LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL'):
                                obj_name = instr.argval
                        
                        if obj_name:
                            target = {
                                'type': 'Attribute',
                                'value': {'type': 'Name', 'id': obj_name, 'ctx': 'Load'},
                                'attr': store_attr.argval,
                                'ctx': 'Store',
                            }
                        else:
                            return None
                    elif target_expr.get('type') == 'Attribute':
                        target = {
                            'type': 'Attribute',
                            'value': target_expr.get('value'),
                            'attr': target_expr.get('attr', store_attr.argval),
                            'ctx': 'Store',
                        }
                    else:
                        return None

                    # 构建值表达式 (如 1)，过滤掉SWAP等栈操作
                    value_instrs_filtered = [i for i in value_instrs
                                            if i.opname not in ('SWAP',)]
                    value_expr = self.expr_reconstructor.reconstruct(value_instrs_filtered)
                    if value_expr is None:
                        value_expr = {'type': 'Constant', 'value': value_instrs_filtered[-1].argval if value_instrs_filtered else None}

                    op_simple = op_symbol.replace('=', '')
                    return {
                        'type': 'AugAssign',
                        'target': target,
                        'op': op_simple,
                        'value': value_expr,
                    }

        obj_expr = self.expr_reconstructor.reconstruct(obj_instrs[-1:])
        if obj_expr is None:
            obj_expr = {'type': 'Name', 'id': str(obj_instrs[-1].argval), 'ctx': 'Load'}

        target = {
            'type': 'Attribute',
            'value': obj_expr,
            'attr': store_attr.argval,
            'ctx': 'Store',
        }

        value_instrs = obj_instrs[:-1]
        if value_instrs:
            value_expr = self.expr_reconstructor.reconstruct(value_instrs)
            if value_expr is None:
                value_expr = {'type': 'Name', 'id': str(value_instrs[-1].argval), 'ctx': 'Load'}
        else:
            value_expr = {'type': 'Constant', 'value': None}

        return {
            'type': 'Assign',
            'targets': [target],
            'value': value_expr,
        }

    def _is_trailing_return_none_statement(self, stmt):
        if not isinstance(stmt, dict):
            return False
        if stmt.get('type') != 'Return':
            return False
        value = stmt.get('value')
        if value is None:
            return True
        if isinstance(value, dict) and value.get('type') == 'Constant' and value.get('value') is None:
            return True
        return False

    def _generate_return_ast(self, block: BasicBlock, return_instr: Instruction = None) -> Dict[str, Any]:
        if return_instr is not None:
            if return_instr.opname == 'RETURN_CONST':
                return {'type': 'Return', 'value': {'type': 'Constant', 'value': return_instr.argval}}
            if return_instr.opname == 'RETURN_VALUE':
                instrs = block.instructions
                return_idx = None
                for i, instr in enumerate(instrs):
                    if instr == return_instr:
                        return_idx = i
                        break
                if return_idx is not None and return_idx > 0:
                    prev = instrs[return_idx - 1]
                    if prev.opname == 'LOAD_CONST' and prev.argval is None:
                        return {'type': 'Return', 'value': {'type': 'Constant', 'value': None}}
                
                has_swap_pattern = False
                if return_idx is not None and return_idx >= 3:
                    _maybe_swap = instrs[return_idx - 2]
                    _maybe_pop = instrs[return_idx - 1]
                    if (_maybe_swap.opname == 'SWAP' and 
                        _maybe_pop.opname == 'POP_TOP'):
                        has_swap_pattern = True
                
                value_instrs = []
                for instr in block.instructions:
                    if instr == return_instr:
                        break
                    skip_ops = ('RESUME', 'NOP', 'CACHE', 'POP_TOP', 'PUSH_NULL',
                                'COPY', 'POP_EXCEPT', 'PUSH_EXC_INFO',
                                'PRECALL', 'CALL')
                    if not has_swap_pattern:
                        skip_ops = skip_ops + ('SWAP',)
                    if instr.opname in skip_ops:
                        continue
                    value_instrs.append(instr)
                if value_instrs:
                    expr = self.expr_reconstructor.reconstruct(value_instrs)
                    if expr:
                        return {'type': 'Return', 'value': expr}
                return {'type': 'Return', 'value': {'type': 'Constant', 'value': None}}

        for instr in reversed(block.instructions):
            if instr.opname == 'RETURN_CONST':
                return {'type': 'Return', 'value': {'type': 'Constant', 'value': instr.argval}}
            if instr.opname == 'RETURN_VALUE':
                value_instrs = []
                is_in_gen_loop = (
                    self._current_loop is not None or
                    (hasattr(self.cfg, 'code') and 
                     hasattr(self.cfg.code, 'co_flags') and 
                     self.cfg.code.co_flags & 0x20)
                )
                _skip_base = ('RESUME', 'NOP', 'CACHE', 'POP_TOP', 'PUSH_NULL',
                              'COPY', 'POP_EXCEPT', 'PUSH_EXC_INFO',
                              'PRECALL', 'CALL')
                _skip_with_swap = _skip_base + ('SWAP',)
                _skip_ops = _skip_base if is_in_gen_loop else _skip_with_swap
                for bi in block.instructions:
                    if bi.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                        break
                    if bi.opname in _skip_ops:
                        continue
                    value_instrs.append(bi)
                if value_instrs:
                    expr = self.expr_reconstructor.reconstruct(value_instrs)
                    if expr:
                        return {'type': 'Return', 'value': expr}
                return {'type': 'Return', 'value': None}
        return {'type': 'Return', 'value': None}



def generate_ast_from_regions(cfg: ControlFlowGraph, top_level_code=None) -> Dict[str, Any]:
    generator = RegionASTGenerator(cfg, top_level_code=top_level_code)
    try:
        return generator.generate()
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise
        raise
