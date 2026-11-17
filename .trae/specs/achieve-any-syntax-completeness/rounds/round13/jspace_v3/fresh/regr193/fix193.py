# -*- coding: utf-8 -*-
"""rr-v5r193 patch: let the B66 with-exit continue chain head recognise the
``while True:`` loop-entry trampoline as the loop top.

Single method, `core/cfg/region_ast_generator.py::_b66_is_with_exit_continue_chain_head`.

[drift D3] ``while True: with open(p) as f: if a: continue`` renders the then arm
as ``if a: pass`` (product returns 4, the original dead-loops / raises OSError).
B66 was written for the plain ``while <cond>: with ...: if a: continue`` shape,
whose back edge lands *on* ``loop.header_block``.  A ``while True:`` body is
entered through a compiler-inserted NOP block (offset 2, the loop frame's first
block, outside ``body_blocks``); the ``continue`` cleanup chain ends in
``JUMP_BACKWARD`` to *that* block, which falls through unconditionally to
``loop.header_block``.  Criterion (3) therefore can never hold in the
``while True`` shape, B66 returns False, and the NOP-only then-arm block degrades
to the folded-statement placeholder ``pass``.

Widening (strictly additive, C3): the back-edge target is accepted when it is the
loop header, or when it is a loop-frame block that is noise-only and whose only
normal successor *is* the loop header -- i.e. the compiler's loop-entry
trampoline, so the back edge still returns to the loop top.  Evidence is block
membership + block content opcodes + successor identity (I.4 whitelist); no
names, no offsets, no pyc special cases, no numeric cap.

Usage:
    python fix193.py            # apply (idempotent, skips an already-applied hunk)
    python fix193.py --revert   # revert to the pre-patch bytes
    python fix193.py --root DIR # patch the tree at DIR (default: the repo)
"""
import hashlib
import os
import py_compile
import sys
import tempfile

DEFAULT_ROOT = r'F:\Downloads\pythoncdc-main'
TARGET = os.path.join('core', 'cfg', 'region_ast_generator.py')

HUNK_A_OLD = """        _b66_tgt = self.cfg.get_block_by_offset(_b66_last.argval)
        if _b66_tgt is None or _b66_tgt is not self._current_loop.header_block:
            return False
"""

HUNK_A_NEW = """        _b66_tgt = self.cfg.get_block_by_offset(_b66_last.argval)
        if _b66_tgt is None:
            return False
        if _b66_tgt is not self._current_loop.header_block:
            # [v193-WTRAMPOLINE] 回边落点的「循环入口跳板」收窄（只增不破）：
            # ``while True:`` 的循环体之前有一个编译器插入的入口 NOP 块——它
            # 是循环帧的第一块（属 loop.blocks，不在 body_blocks 内）、剥噪后
            # 无任何用户指令、且**唯一普通后继就是 header_block**（无条件顺序
            # 落入循环体）。回边 JUMP_BACKWARD 的落点正是这个跳板块，不是
            # header_block 本身，于是判据 (3)「目标 == 当前循环 header」在
            # ``while True`` 形态下恒不成立：with 宿主内的 continue 链头
            # （NOP 边界块）判否 ⇒ 降级为折叠占位 ``pass``（drift D3 实测
            # ``while True: with open(p) as f: if a: continue`` → ``if a: pass``，
            # 直跑由死循环/OSError 变成 return 4）。
            # 判据（I.4 白名单：块归属 + 块内容 opcode + 后继/落空同一性）：
            # 落点属当前循环帧、剥噪后无用户指令、唯一普通后继就是
            # header_block ⇒ 该块与 header 同属循环入口，回边等价于回 header。
            # 普通 while 的条件块回边仍直接落 header（本支不进入，逐位不变）；
            # 循环外的 NOP 块不属 loop.blocks，不受影响。
            _b66_loop = self._current_loop
            _b66_tramp = False
            if _b66_tgt in (getattr(_b66_loop, 'blocks', None) or ()):
                if all(i.opname in _b66_noise for i in _b66_tgt.instructions):
                    _b66_tgt_exc = getattr(_b66_tgt, 'exception_successors',
                                           None) or set()
                    _b66_tgt_succs = [s for s in (_b66_tgt.successors or [])
                                      if s not in _b66_tgt_exc]
                    if (len(_b66_tgt_succs) == 1
                            and _b66_tgt_succs[0] is _b66_loop.header_block):
                        _b66_tramp = True
            if not _b66_tramp:
                return False
"""

HUNK_B_OLD = """              header，且 succ 剥噪内容全部为 __exit__(None, None, None)
"""

HUNK_B_NEW = """              header（``while True:`` 的回边落点是循环入口 NOP 跳板块，
              该块剥噪后无用户指令且唯一普通后继为 header_block 时等价
              接受——[v193-WTRAMPOLINE]），且 succ 剥噪内容全部为
              __exit__(None, None, None)
"""

HUNKS = (('A', HUNK_A_OLD, HUNK_A_NEW), ('B', HUNK_B_OLD, HUNK_B_NEW))


def read(path):
    raw = open(path, 'rb').read()
    return raw.decode('utf-8-sig'), raw.startswith(b'\xef\xbb\xbf')


def write(path, text, bom):
    with open(path, 'wb') as fh:
        if bom:
            fh.write(b'\xef\xbb\xbf')
        fh.write(text.encode('utf-8'))


def main(argv):
    revert = '--revert' in argv[1:]
    root = DEFAULT_ROOT
    args = argv[1:]
    for i, a in enumerate(args):
        if a == '--root' and i + 1 < len(args):
            root = args[i + 1]
        elif a.startswith('--root='):
            root = a.split('=', 1)[1]
    path = os.path.join(root, TARGET)
    text, bom = read(path)
    print('target: %s bom=%s' % (path, bom))
    changed = 0
    for name, old, new in HUNKS:
        src, dst = (new, old) if revert else (old, new)
        n = text.count(src)
        print('hunk %s anchor count=%d -> %s' % (name, n, 'REVERT' if revert else 'APPLY'))
        if n == 0:
            if text.count(dst) == 1:
                print('  already in target state, skip')
                continue
            print('  ERROR: anchor not found and target state not present')
            return 2
        if n != 1:
            print('  ERROR: anchor not unique')
            return 2
        text = text.replace(src, dst)
        changed += 1
    if changed:
        write(path, text, bom)
        print('wrote %d hunk(s), bytes=%d' % (changed, len(text.encode('utf-8'))))
        if bom and open(path, 'rb').read(3) != b'\xef\xbb\xbf':
            print('  ERROR: BOM lost')
            return 4
    else:
        print('nothing to do')
    tmp = tempfile.mkdtemp()
    try:
        py_compile.compile(path, cfile=os.path.join(tmp, 'p.pyc'), doraise=True)
        print('py_compile: OK')
    except py_compile.PyCompileError as exc:
        print('py_compile: FAILED %s' % exc)
        return 3
    print('sha256(file)=%s' % hashlib.sha256(open(path, 'rb').read()).hexdigest())
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
