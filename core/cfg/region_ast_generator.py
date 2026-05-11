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
            entry_region = self.region_analyzer.get_region_for_block(entry_block)
            for r in self.regions:
                if isinstance(r, LoopRegion) and (r.condition_block is entry_block or
                    (r.header_block and entry_block.start_offset in [s.start_offset for s in r.header_block.predecessors])):
                    entry_region = r
                    break
            if isinstance(entry_region, LoopRegion) and (entry_region.condition_block == entry_block or
                (entry_region.header_block and entry_block.start_offset in [s.start_offset for s in entry_region.header_block.predecessors])):
                self.generated_blocks.add(entry_block)
                pass
            elif isinstance(entry_region, IfRegion) and entry_region.condition_block == entry_block:
                pass
            elif isinstance(entry_region, BoolOpRegion):
                pass
            elif isinstance(entry_region, TernaryRegion):
                pass
            elif isinstance(entry_region, AssertRegion):
                pass
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
            is_contained = False
            for other in top_level:
                if other is not r and r.entry and r.entry in other.blocks:
                    if other.region_type != RegionType.BASIC:
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
                        elif isinstance(other, TernaryRegion) and isinstance(r, TernaryRegion):
                            if r.entry and r.entry == other.merge_block:
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
        boolop_regions = [r for r in filtered if isinstance(r, BoolOpRegion)]
        other_regions = [r for r in filtered if not isinstance(r, BoolOpRegion)]
        
        loop_condition_boolops = set()
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

        boolop_regions = [r for r in boolop_regions
                          if id(r) not in loop_condition_boolops]
        
        sorted_other = sorted(other_regions, key=lambda r: r.entry.start_offset if r.entry else 0)
        top_level_regions = boolop_regions + sorted_other

        for region in top_level_regions:
            if region.region_type != RegionType.BASIC and region.blocks:
                if all(b in self.generated_blocks for b in region.blocks):
                    if _DEBUG_BOOLOP:
                        #print(f"[DEBUG generate] SKIP {type(region).__name__}(entry={region.entry.start_offset}) all blocks generated")
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
        if filtered_body:
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
                condition = expr
        message = None
        if region.message_block:
            msg_instrs = []
            for instr in region.message_block.instructions:
                if instr.opname in ('RAISE_VARARGS', 'POP_EXCEPT', 'RERAISE',
                                    'LOAD_ASSERTION_ERROR', 'PRECALL', 'CALL',
                                    'RESUME', 'NOP', 'CACHE', 'PUSH_NULL',
                                    'COPY', 'SWAP'):
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
        # 如果是，跳过循环生成，因为 yield from 语句已经在其他地方生成
        if region.metadata.get('is_yield_from_loop'):
            # 标记所有块为已生成，避免重复处理
            for block in region.blocks:
                self.generated_blocks.add(block)
            return {'type': 'Pass'}  # 返回空语句

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
            iter_expr = self.expr_reconstructor.reconstruct(instrs) if instrs else None
            if iter_expr is None and instrs:
                stmt = self._build_statement(instrs)
                iter_expr = stmt.get('value') if stmt and isinstance(stmt, dict) else None
            # Unwrap Iter wrapper (GET_ITER) - for-loop iter field uses inner expression directly
            if isinstance(iter_expr, dict) and iter_expr.get('type') == 'Iter' and isinstance(iter_expr.get('value'), dict):
                iter_expr = iter_expr['value']
        else:
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

            if _cond_was_generated:
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
                    cond_instrs = []
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
            self._loop_handle_continue(block, region, natural_back_edge, body_blocks_no_header)
            return True
        if block_role == BlockRole.LOOP_BACK_EDGE:
            self._loop_handle_back_edge(block, region, child_info, body_stmts,
                                         body_blocks_no_header, back_edge_stmts, natural_back_edge)
            return True
        if block_role in (BlockRole.BREAK, BlockRole.PURE_BREAK):
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
        if (region.region_type == RegionType.WHILE_LOOP
            and region.condition_block is not None
            and region.condition_block != header):
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
            self._loop_handle_header_no_condition(block, body_stmts)
            return
        _header_region = self.region_analyzer.get_region_for_block(block)
        _header_if_region = None
        for _r in region.iter_descendants((IfRegion,)):
            if _r.condition_block == block:
                _header_if_region = _r
                break
        if _header_if_region is not None:
            if (_header_if_region.condition_block == region.condition_block or
                _header_if_region.condition_block == region.header_block):
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
            for _sli in range(len(hdr.instructions) - 2, -1, -1):
                _sl_instr = hdr.instructions[_sli]
                if _sl_instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                    _last_store_idx = _sli
                    break
            if _last_store_idx >= 0:
                _body_end_idx = _last_store_idx
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
                        _body_end_idx = _sli - 1
                        break
        elif _last_i and _last_i.opname in FORWARD_CONDITIONAL_JUMP_OPS:
            _cond_break_instr = _last_i
            _last_store_idx = -1
            for _sli in range(len(hdr.instructions) - 2, -1, -1):
                _sl_instr = hdr.instructions[_sli]
                if _sl_instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                    _last_store_idx = _sli
                    break
            if _last_store_idx >= 0:
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
                    _self_loop_stmts.append({
                        'type': 'If',
                        'test': _cb_cond,
                        'body': [{'type': 'Break'}],
                        'orelse': [],
                    })
        return _self_loop_stmts

    def _loop_handle_header_no_condition(self, block: BasicBlock, body_stmts: List[Dict[str, Any]]) -> None:
        """处理无条件while header（如 while True 中带break的情形）"""
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
                    _return_stmts = self._generate_block_statements(_return_block)
                    _return_body = _return_stmts if _return_stmts else [{'type': 'Return', 'value': {'type': 'Constant', 'value': None}}]
                    _hdr_stmts.append({'type': 'If', 'test': _cond_expr, 'body': _return_body})
                    self.generated_blocks.add(_return_block)
                    self.generated_offsets.add(_return_block.start_offset)
                else:
                    _negate = (not _is_if_false) if _jumps_inside else _is_if_false
                    _cond_expr = _negate_expr(_expr) if _negate else _expr
                    _hdr_stmts.append({'type': 'If', 'test': _cond_expr, 'body': [{'type': 'Break'}]})
        for _bs in [s for s in block.successors if s not in _loop_body_set] + _block_succ_break:
            if self.region_analyzer.get_block_role(_bs) in (BlockRole.PURE_BREAK, BlockRole.BREAK):
                self.generated_blocks.add(_bs)
                self.generated_offsets.add(_bs.start_offset)

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
                _then_stmts = self._generate_block_statements(_then_succ)
                if not _then_stmts:
                    _then_stmts = [{'type': 'Pass'}]
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
            return False
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
        """找到回边块中条件判断指令的起始索引"""
        _nbe_cond_start_idx = None
        for _nbci in range(len(block.instructions) - 2, -1, -1):
            _nbc_instr = block.instructions[_nbci]
            if _nbc_instr.opname in ('COMPARE_OP', 'IS_OP', 'CONTAINS_OP'):
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
        """处理continue块"""
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
        if self.region_analyzer.get_block_role(block) == BlockRole.PURE_CONTINUE and not in_if_branch and is_if_else_fallthrough:
            self.generated_blocks.add(block)
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
            _be_meaningful = [i for i in block.instructions
                              if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP')
                              and i.opname not in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')]
            if not _be_meaningful:
                self.generated_blocks.add(block)
                self.generated_offsets.add(block.start_offset)
                return
            if _be_meaningful:
                _be_stmt = self._build_statement(_be_meaningful)
                if _be_stmt:
                    body_stmts.append(_be_stmt)
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
                    _be_stmt = self._build_statement(_be_meaningful)
                    if _be_stmt:
                        back_edge_stmts.append(_be_stmt)
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
        """生成完整 if-elif[-else] 链：外层If(test=外层条件, body=then, orelse=[elif节点,...])"""
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
        result = {'type': 'If', 'test': condition, 'body': then_stmts if then_stmts else [{'type': 'Pass'}], 'orelse': elif_part if isinstance(elif_part, list) else ([elif_part] if elif_part else [])}
        if pre_stmts:
            result = pre_stmts + [result]
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
        for child in (region.children or []):
            if not isinstance(child, (TryExceptRegion, WithRegion, LoopRegion, IfRegion)):
                continue
            if not hasattr(child, 'entry') or child.entry is None:
                continue
            if child.entry in self.generated_blocks:
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
            nested_chained = []
            if region.chained_compare_blocks:
                for cc in region.chained_compare_blocks:
                    if cc.start_offset > elif_cond_block.start_offset:
                        nested_chained.append(cc)
            nested_blocks = {region.elif_conditions[1]}
            if len(region.elif_bodies) > 1:
                nested_blocks.update(region.elif_bodies[1])
            nested_blocks.update(region.elif_conditions[2:])
            for body in region.elif_bodies[2:]:
                nested_blocks.update(body)
            if region.elif_final_else:
                nested_blocks.update(region.elif_final_else)
            nested_elif = IfRegion(
                region_type=RegionType.IF_ELIF_CHAIN, entry=region.elif_conditions[1],
                blocks=nested_blocks, condition_block=region.elif_conditions[1],
                then_blocks=region.elif_bodies[1] if len(region.elif_bodies) > 1 else [],
                elif_conditions=region.elif_conditions[2:], elif_bodies=region.elif_bodies[2:],
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
        final_else_stmts = None
        if not nested_elif_stmts and region.elif_final_else:
            final_else_stmts = self._process_if_blocks(region.elif_final_else, region, branch='else')
        elif_orelse = nested_elif_stmts if nested_elif_stmts else (final_else_stmts if final_else_stmts else [])
        return [{'type': 'If', '_is_elif': True, 'test': elif_condition if elif_condition else {'type': 'Constant', 'value': True}, 'body': elif_body_stmts if elif_body_stmts else [{'type': 'Pass'}], 'orelse': elif_orelse}]

    def _if_generate_normal(self, region: IfRegion) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """生成普通的 If AST 节点（非 ternary、非 chained_compare）"""
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
        then_stmts = self._if_generate_then_branch(region)
        else_stmts = self._if_generate_else_branch(region)
        self.generated_blocks.add(region.condition_block)
        if hasattr(region, 'elif_conditions') and region.elif_conditions:
            for elif_cond in region.elif_conditions:
                self.generated_blocks.add(elif_cond)
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
        for block in sorted(blocks, key=lambda b: b.start_offset):
            if block in self.generated_blocks:
                continue
            if stmts and stmts[-1].get('type') in ('Break', 'Continue', 'Return', 'Raise'):
                if self._current_loop and block not in self._post_break_blocks:
                    self._post_break_blocks.append(block)
                continue
            role = self.region_analyzer.get_block_role(block)
            if role in (BlockRole.BREAK, BlockRole.PURE_BREAK):
                stmts.append({'type': 'Break'})
                self.generated_blocks.add(block)
                self.generated_offsets.add(block.start_offset)
                continue
            if role == BlockRole.LOOP_BODY and self._current_loop:
                cond_break = self._try_generate_conditional_break(block)
                if cond_break is not None:
                    stmts.extend(cond_break)
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
            if nested and isinstance(nested, (IfRegion, LoopRegion, TryExceptRegion, WithRegion, MatchRegion)):
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
                    bs[-1] = {'type': 'Return', 'value': last_bs['value']}
                stmts.extend(bs)
            self.generated_blocks.add(block)
        return stmts

    def _try_generate_conditional_break(self, block: BasicBlock) -> Optional[List[Dict[str, Any]]]:
        loop = self._current_loop
        if loop is None:
            return None
        last_instr = block.get_last_instruction()
        if last_instr is None:
            return None
        if last_instr.opname not in FORWARD_CONDITIONAL_JUMP_OPS:
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
            cond_expr = self._negate_condition(expr) if is_if_false else expr
        else:
            cond_expr = expr if is_if_false else self._negate_condition(expr)
        exit_role = self.region_analyzer.get_block_role(exit_succ)
        if exit_role in (BlockRole.RETURN, BlockRole.RETURN_NONE) and exit_succ in loop_body_set:
            ret_stmts = self._generate_block_statements(exit_succ)
            body_stmts = ret_stmts if ret_stmts else [{'type': 'Return', 'value': {'type': 'Constant', 'value': None}}]
            self.generated_blocks.add(exit_succ)
        else:
            body_stmts = [{'type': 'Break'}]
            self.generated_blocks.add(exit_succ)
        if_stmt = {'type': 'If', 'test': cond_expr, 'body': body_stmts}
        self.generated_blocks.add(block)
        self.generated_offsets.add(block.start_offset)
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
                    if r.try_offset_end - r.try_offset_start < region.try_offset_end - region.try_offset_start:
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

        for block in region.try_blocks:
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

        return body_stmts

    def _generate_try(self, region: TryExceptRegion) -> Dict[str, Any]:
        region_id = id(region)
        self._generating_regions.add(region_id)

        try:
            body_stmts = self._generate_try_body(region)

            handlers = []
            for idx, (exc_type, exc_name, handler_blocks) in enumerate(region.except_handlers):
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
                for fb in region.finally_blocks:
                    if fb in self.generated_blocks:
                        continue
                    fbs = self._generate_handler_body_statements(fb)
                    if fbs:
                        finalbody_stmts.extend(fbs)
                    self.generated_blocks.add(fb)

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
                is_cleanup_reraise = (instr.arg == 0 and not remaining) or instr.arg == 1
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

        反编译逻辑：
        1. 标记cleanup块：将region.cleanup_blocks和exception_blocks标记为已生成，
           并扫描body_end_offset之后的with退出清理块
        2. 生成body语句：遍历region.with_blocks，对每个块：
           a. 跳过已生成块、cleanup块、LOOP_BACK_EDGE块、含RERAISE的PURE_BREAK块
           b. 若块属于嵌套区域（IfRegion/LoopRegion/TryExceptRegion/WithRegion），
              递归生成该区域
           c. 若块含BEFORE_WITH（内层with入口），跳过（由内层WithRegion处理）
           d. 检测with body中的return语句（_detect_with_body_return）
           e. 过滤掉目标变量的STORE指令（由with items的optional_vars处理）
           f. 对空语句块，检测break/continue/return路径
        3. 生成子区域：遍历region.children，跳过with cleanup相关的IfRegion
           （含PUSH_EXC_INFO/WITH_EXCEPT_START的条件块）和TryExceptRegion
           （handler含WITH_EXCEPT_START），其余递归生成
        4. 生成post-with语句：收集body_end_offset之后、属于region.blocks但
           不属于with_blocks/cleanup/已生成的块，作为with语句之后的代码
        5. 构建with items：从region.items中提取上下文表达式和目标变量，
           通过expr_reconstructor重建表达式AST
        6. 组装结果：pre_stmts + with_ast + post_with_stmts

        关键约束：
        - with cleanup块（WITH_EXIT_CLEANUP/WITH_STACK_CLEANUP/WITH_HANDLER）
          不生成可见代码，仅标记为已生成
        - break/continue在with body中需要通过cleanup路径检测
        - post_with_stmts处理with语句之后的代码（如w075/w21withelse）
        - 嵌套区域的orphan指令需要单独处理
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

        生成流程：
        1. 提取subject表达式：
           - 结构型模式：subject是MATCH_*操作码之前的LOAD指令
           - 字面量模式：subject是COPY之前的LOAD指令
           - 特殊：case None模式无COPY，subject是POP_JUMP_IF_NOT_NONE之前的LOAD指令

        2. 为每个case生成Case节点：
           a. pattern: 从region.case_patterns获取（已由pattern_parser解析）
           b. guard: 从region.case_guards获取
           c. body: 遍历region.case_bodies中的块生成语句

        body生成的关键逻辑：
        - 跳过pattern-only块（只含MATCH_*/COMPARE_OP/UNPACK_*/STORE_*等pattern指令的块）
        - 跳过guard条件块（含比较+条件跳转的块，由_collect_guard_pattern_blocks识别）
        - 跳过pattern store块（STORE指令的目标名在pattern_store_names中的块）
        - 使用case_body_start_indices分离同一块中的pattern指令和body指令
        - 对嵌套区域（if/for/while/try/with/MatchRegion），调用_generate_region生成

        隐式default处理：
        - 如果case body只含平凡操作（POP_TOP/LOAD_CONST/RETURN_VALUE/JUMP），
          视为隐式default，不生成显式case节点
        - 显式default（case _）生成MatchAs pattern

        OR模式处理：
        - region.case_patterns中MatchOr类型表示OR模式
        - 多个case共享同一body时由_mr_finalize_match_region合并
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
                if first_pat.get('type') == 'MatchAs' and first_pat.get('pattern', {}).get('type') == 'MatchSingleton':
                    is_literal_match = True
            
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
                    if instr.opname in ('LOAD_NAME', 'LOAD_GLOBAL'):
                        rest = region.subject_block.instructions[idx+1:]
                        if len(rest) >= 2 and rest[0].opname == 'LOAD_CONST' and isinstance(rest[0].argval, tuple) and rest[1].opname == 'MATCH_CLASS':
                            break
                    if (instr.opname in PATTERN_INSTRS and 
                        instr.opname != 'LOAD_FAST'):
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

            for block in body:
                if block in self.generated_blocks:
                    continue
                
                if block in guard_pattern_blocks:
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
                    _meaningful[1].opname in ('RETURN_VALUE', 'RETURN_CONST')):
                    self.generated_blocks.add(block)
                    continue
                
                PATTERN_OPS = ('MATCH_CLASS', 'MATCH_SEQUENCE', 'MATCH_MAPPING',
                               'MATCH_KEYS', 'MATCH_MAPPING_KEYS',
                               'GET_LEN', 'UNPACK_SEQUENCE', 'UNPACK_EX',
                               'UNPACK_EXTRACT', 'BINARY_SUBSCR', 'BINARY_OP')
                
                has_only_pattern = all(
                    instr.opname in PATTERN_OPS or 
                    instr.opname in ('LOAD_CONST', 'STORE_FAST', 'STORE_NAME',
                                'STORE_GLOBAL', 'STORE_DEREF',
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
                    non_store_non_trivial = [i for i in block.instructions
                                              if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL',
                                                                  'STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
                                                                  'LOAD_CONST', 'RETURN_VALUE', 'RETURN_CONST',
                                                                  'JUMP_FORWARD', 'JUMP_ABSOLUTE', 'POP_TOP')]
                    if not non_store_non_trivial:
                        self.generated_blocks.add(block)
                        continue
                
                nested_region = self.region_analyzer.get_entry_region_for_block(block)
                if not nested_region:
                    nested_region = self.region_analyzer.get_region_for_block(block)
                if nested_region and nested_region is not region and isinstance(nested_region, (IfRegion, LoopRegion, TryExceptRegion, WithRegion, MatchRegion)):
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
                pure_instrs = list(instrs)
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
        if not segments:
            return None
        if len(segments) == 1:
            op, values = segments[0]
            if len(values) == 1:
                return values[0]
            return {'type': 'BoolOp', 'op': op, 'values': values}
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
        return result

    def _generate_boolop(self, region: BoolOpRegion) -> Optional[List[Dict[str, Any]]]:
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
            if region.value_target:
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

    def _generate_block_statements(self, block: BasicBlock) -> List[Dict[str, Any]]:
        if block in self.generated_blocks or block.start_offset in self.generated_offsets:
            return []

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

            _cjb_then_stmts = self._if_generate_branch_stmts(_cjb_then_blocks) if any(b in _cjb_pending for b in _cjb_then_blocks) else []
            _cjb_else_stmts = self._if_generate_branch_stmts(_cjb_else_blocks) if any(b in _cjb_pending for b in _cjb_else_blocks) else []

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
                value_instrs = []
                for instr in block.instructions:
                    if instr == return_instr:
                        break
                    if instr.opname in ('RESUME', 'NOP', 'CACHE', 'POP_TOP', 'PUSH_NULL',
                                        'COPY', 'SWAP', 'POP_EXCEPT', 'PUSH_EXC_INFO',
                                        'PRECALL', 'CALL'):
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
                for bi in block.instructions:
                    if bi.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                        break
                    if bi.opname in ('RESUME', 'NOP', 'CACHE', 'POP_TOP', 'PUSH_NULL',
                                     'COPY', 'SWAP', 'POP_EXCEPT', 'PUSH_EXC_INFO',
                                     'PRECALL', 'CALL'):
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
