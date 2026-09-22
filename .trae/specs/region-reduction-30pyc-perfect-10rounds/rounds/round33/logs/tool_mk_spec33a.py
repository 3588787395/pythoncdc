# -*- coding: utf-8 -*-
"""Round 33 line A: derive the landing spec for R33-A.

R33-A widens the *thread-through* verdict of the return-chain walk
(_find_return_chain_via_successors -> _is_cleanup_only_no_return) with one structural arm:
a successor block that is a COMPLETED side-effect statement (net stack effect exactly 0,
terminating in POP_TOP, neither returning nor propagating an exception, no control transfer
inside) may be walked through on the way to a return-through-cleanup block.

Writes D:/Temp/r33gate/c33/spec_r33a.json {file, edits:[{anchor, repl}]} where
anchor/repl are LF-normalised fragments of the worktree file, and self-proves that
base.replace(anchor, repl) == the intended candidate text exactly once.
"""
import hashlib
import io
import json
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
REL = 'core/cfg/region_ast_generator.py'
SRC = os.path.join(REPO, REL)
sys.stdout.reconfigure(encoding='utf-8')

raw = io.open(SRC, 'rb').read()
assert raw[:3] == b'\xef\xbb\xbf', 'worktree core lost its BOM'
# identity of the file being patched: the *normalised* bytes must equal HEAD's blob, i.e. the
# worktree is pristine (core.autocrlf=true makes the raw CRLF hash a different number)
import subprocess
assert hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest()[:20] == '3781872bcc715f2fdb23'
assert hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest()[:20] == hashlib.sha256(
    subprocess.check_output(['git', 'cat-file', 'blob', 'HEAD:' + REL], cwd=REPO)).hexdigest()[:20], \
    'core drifted from HEAD'
txt = raw.decode('utf-8-sig').replace('\r\n', '\n')

ANCHOR = """        def _is_cleanup_only_no_return(b):
            instrs = [i for i in b.instructions
                      if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
            if not instrs:
                return False
            if any(i.opname in ('RETURN_VALUE', 'RETURN_CONST') for i in instrs):
                return False
            return all(i.opname in _cleanup_only_ops for i in instrs)
"""
assert txt.count(ANCHOR) == 1, txt.count(ANCHOR)

REPL = """        def _is_cleanup_only_no_return(b):
            instrs = [i for i in b.instructions
                      if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
            if not instrs:
                return False
            if any(i.opname in ('RETURN_VALUE', 'RETURN_CONST') for i in instrs):
                return False
            if all(i.opname in _cleanup_only_ops for i in instrs):
                return True
            # [R33-A] 区域归约算法原则 1（块 = 前导语句 + 尾跳转/终止）：return 值除穿过
            # 「白名单清理块」外，还可穿过一条**已完结的副作用语句块**。判据是 CPython 栈
            # 纪律而非操作码模式表：① 整块净栈效应恰为 0 —— 块入口值栈（被持有的 return 值）
            # 原样保留到块出口；② 块尾（跳过尾跳转后）是 POP_TOP —— 该块自压的值由该块自弃，
            # 它是语句而不是值，不会与 return 值争抢栈顶；③ 块内不传播异常（RERAISE /
            # PUSH_EXC_INFO / WITH_EXCEPT_START）、无任何跳转（含尾跳转）—— 穿过它之后控制流
            # 仍是直线后继，return 链路不因该块改变分叉。
            # 覆盖 try/finally + with 正常路径的清理语句 `loader.dispose()`
            # （LOAD_FAST/LOAD_METHOD/PRECALL/CALL/POP_TOP）：其 LOAD_* 不在
            # _cleanup_only_ops 白名单内，故旧判据在此返回 None，把 return 降级为 Expr。
            if any(i.opname in ('RERAISE', 'PUSH_EXC_INFO', 'WITH_EXCEPT_START')
                   for i in instrs):
                return False
            if any(i.opname.startswith('JUMP') or i.opname in ('FOR_ITER', 'SEND')
                   for i in instrs):
                return False
            _r33a_core = instrs[:]
            while _r33a_core and _r33a_core[-1].opname.startswith('JUMP'):
                _r33a_core.pop()
            if not _r33a_core or _r33a_core[-1].opname != 'POP_TOP':
                return False
            _r33a_delta = 0
            for i in b.instructions:
                if i.opname in ('RESUME', 'NOP', 'CACHE'):
                    continue
                _r33a_eff = self._instruction_stack_effect(i)
                if _r33a_eff is None:
                    return False
                _r33a_delta += _r33a_eff
            return _r33a_delta == 0
"""
cand = txt.replace(ANCHOR, REPL)
assert cand.count(REPL) == 1 and cand != txt
assert txt.count('def _instruction_stack_effect(ins:') == 1

io.open(r'D:/Temp/r33gate/c33/spec_r33a.json', 'w', encoding='utf-8').write(
    json.dumps({'file': REL, 'edits': [{'anchor': ANCHOR, 'repl': REPL}]}, ensure_ascii=False))
print('spec_r33a.json written; anchor unique; candidate %d -> %d chars (+%d lines)'
      % (len(txt), len(cand), REPL.count('\n') - ANCHOR.count('\n')))
