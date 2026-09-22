# -*- coding: utf-8 -*-
"""Derive the Round 35 candidate R35-B patch spec for the mirror harness.

R35-B (one same-level predicate, emission side, _generate_try fall-through arm :24695):
do not materialise a handler-tail `return None` when the block behind it is a pure cleanup
epilogue (POP_EXCEPT*[LOAD_CONST]RETURN) AND the same code object holds another pure cleanup
epilogue whose block role is RETURN (the function's terminal exit).  CPython 3.11 duplicates
one source-level fall-out per exception-scope exit; the terminal copy is already claimed by the
implicit function return, so materialising the non-terminal copy double-claims the exit and
merges two epilogues into one statement (region-reduction principle 2).

usage: python -X utf8 mkspec35b.py
"""
import io
import json
import os

OUT = r'D:/Temp/r35gate/r35'

HELPER = '''# [R35-B] 清理尾声（cleanup epilogue）形状判据。
#
# CPython 3.11 把每一条「从异常作用域落出」的退出路径内联复制成一份尾声
# POP_EXCEPT×k [+ LOAD_CONST None] + RETURN_VALUE：块内没有任何源码级语句，它是编译器为
# 隐式退出补发的。同一 code object 内若同时存在「终末」那一份（block_role == RETURN，
# 已由函数隐式返回认领），把非终末的那一份也物化成 `return None` 就是对一个源码级落出的
# 双认领（区域归约算法原则 2：每块唯一归属），两份额本应分别编译的尾声被合并成一条语句，
# 结果是少发射 POP_EXCEPT×k + LOAD_CONST + RETURN_VALUE。
_CLEANUP_EPILOGUE_NOISE = frozenset({'RESUME', 'NOP', 'CACHE', 'PUSH_NULL'})
_CLEANUP_EPILOGUE_TERMINAL_OPS = frozenset({'RETURN_VALUE', 'RETURN_CONST'})


def _cleanup_epilogue_pops(block):
    """块是否为纯清理尾声（POP_EXCEPT* [+ LOAD_CONST] + RETURN）；是则返回 POP_EXCEPT 个数。"""
    _ops = [i.opname for i in block.instructions if i.opname not in _CLEANUP_EPILOGUE_NOISE]
    if not _ops or _ops[-1] not in _CLEANUP_EPILOGUE_TERMINAL_OPS:
        return 0
    _core = _ops[:-1]
    if _core and _core[-1] == 'LOAD_CONST':
        _core = _core[:-1]
    if not _core or any(o != 'POP_EXCEPT' for o in _core):
        return 0
    return len(_core)


def _is_duplicated_cleanup_exit_return(analyzer, block, stmts):
    """stmts 是否为「重复清理尾声的非终末副本」被物化成的隐式 `return None`。

    三条判据全部只读结构事实：语句形态（唯一一条 Return(Constant(None))）、本块的
    操作码类别（纯清理尾声）、同 code object 内另一同形块的 block_role（RETURN 即函数
    终末出口）。不含名字、常量值、绝对偏移或指令计数。
    """
    if len(stmts) != 1 or not isinstance(stmts[0], dict):
        return False
    _st = stmts[0]
    _val = _st.get('value')
    if _st.get('type') != 'Return' or not isinstance(_val, dict):
        return False
    if _val.get('type') != 'Constant' or _val.get('value') is not None:
        return False
    if not _cleanup_epilogue_pops(block):
        return False
    _cfg = getattr(analyzer, 'cfg', None)
    if _cfg is None:
        return False
    for _b in _cfg.blocks.values():
        if _b is block:
            continue
        if _cleanup_epilogue_pops(_b) and analyzer.get_block_role(_b) == BlockRole.RETURN:
            return True
    return False


'''

ANCHOR_A = 'class _IfRegionProxy:'
REPL_A = HELPER + ANCHOR_A

ANCHOR_B = """                    hbs = self._generate_handler_body_statements(hb)
                    if hbs:
                        handler_body.extend(hbs)
                    self.generated_blocks.add(hb)"""

REPL_B = """                    hbs = self._generate_handler_body_statements(hb)
                    # [R35-B] 重复清理尾声的非终末副本不得物化为 `return None`（终末副本
                    # 已由函数隐式返回认领）。handler_body 仍为空时保留原发射：空 handler
                    # 落出后需要 pass，而 `pass` 与落出形态编译结果不同。
                    if hbs and not (handler_body and _is_duplicated_cleanup_exit_return(
                            self.region_analyzer, hb, hbs)):
                        handler_body.extend(hbs)
                    self.generated_blocks.add(hb)"""

spec = {'file': 'core/cfg/region_ast_generator.py',
        'edits': [{'anchor': ANCHOR_A, 'repl': REPL_A},
                  {'anchor': ANCHOR_B, 'repl': REPL_B}]}
dst = os.path.join(OUT, 'spec_r35b.json')
io.open(dst, 'w', encoding='utf-8', newline='\n').write(json.dumps(spec, ensure_ascii=False))
print('wrote %s  edits=%d  helper_lines=%d site_delta_lines=%d'
      % (dst, len(spec['edits']), ANCHOR_A.join(['', REPL_A]).count('\n'),
         REPL_B.count('\n') - ANCHOR_B.count('\n')))
