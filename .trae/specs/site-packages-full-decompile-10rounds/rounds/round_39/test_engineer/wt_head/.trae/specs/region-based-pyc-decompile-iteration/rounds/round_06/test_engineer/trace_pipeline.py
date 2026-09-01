"""在真实反编译流水线中追踪 MAP_ADD 的栈形状。

打桩 ExpressionReconstructor._process_instruction，记录每条指令的栈深变化，
并按 reset() 划分批次，观察 dict 字面量构造在跨基本块时的栈契约。

用法: D:/Python/python.exe trace_pipeline.py <pyc路径> [函数名] [offset_lo] [offset_hi]
"""
import sys
import os
import dis
import py_compile

ROOT = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, ROOT)

from core.cfg.ast_generator_v2 import ExpressionReconstructor

_state = {'batch': 0, 'n': 0}


def node_desc(n):
    if isinstance(n, dict):
        t = n.get('type', '?')
        if t == 'Dict':
            return 'Dict(%d)' % len(n.get('keys', []))
        if t == 'Constant':
            return 'Const(%r)' % (n.get('value'),)
        if t == 'Name':
            return 'Name(%s)' % n.get('id')
        if t == 'Attribute':
            return 'Attr(%s)' % n.get('attr')
        if t == 'IfExp':
            return 'IfExp'
        return t
    return type(n).__name__


_orig = ExpressionReconstructor._process_instruction
_orig_reset = ExpressionReconstructor.reset


def patched(self, instr):
    lo = _state.get('lo', 0)
    hi = _state.get('hi', 10 ** 9)
    before = len(self.stack)
    _orig(self, instr)
    after = len(self.stack)
    off = getattr(instr, 'offset', -1)
    _state['n'] += 1
    if lo <= off <= hi:
        top = node_desc(self.stack[-1]) if after else ''
        below = node_desc(self.stack[-2]) if after >= 2 else ''
        print('  [b%d] %4d %-32s %2d->%-2d top=%-22s below=%s'
              % (_state['batch'], off,
                 instr.opname + (' ' + str(instr.argval) if instr.arg is not None else ''),
                 before, after, top, below))


def patched_reset(self):
    _state['batch'] += 1
    _orig_reset(self)


ExpressionReconstructor._process_instruction = patched
ExpressionReconstructor.reset = patched_reset


def main():
    pyc = sys.argv[1]
    fname = sys.argv[2] if len(sys.argv) > 2 else 'save'
    _state['lo'] = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    _state['hi'] = int(sys.argv[4]) if len(sys.argv) > 4 else 10 ** 9

    from pycdc import decompile_pyc
    src = decompile_pyc(pyc, use_cfg=True)
    print('--- 反编译 save ---')
    i = src.find('def ' + fname + '(')
    print(src[i:i + 500] if i >= 0 else 'NOT FOUND')


if __name__ == '__main__':
    main()
