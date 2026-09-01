#!/usr/bin/env python3
"""实验：用 dis.stack_effect 做前向栈深模拟，定位条件块中「条件表达式」的起点。"""
import dis
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _find_root(start: Path) -> Path:
    for p in [start] + list(start.parents):
        if (p / 'core' / 'cfg').is_dir() and (p / 'pycdc.py').is_file():
            return p
    raise RuntimeError(start)


ROOT = _find_root(HERE)
sys.path.insert(0, str(ROOT))

from core.cfg import build_cfg  # noqa: E402

CASES = {
    'F4 basic': 'def fill(self, trade):\n    amount = trade.amount\n    assert self.filled_amount + amount <= self.amount\n    self.filled_amount += amount\n    return [trade]\n',
    'F4 msg': 'def fill(self, trade):\n    amount = trade.amount\n    assert amount > 0, "over"\n    return amount\n',
    'F4 method': 'def f(self, x):\n    y = self.compute(x)\n    assert y is not None\n    self.result = y\n',
    'no prefix': 'def f(a, b):\n    assert a < b\n    return a\n',
    'two prefix': 'def f(a, b):\n    x = 1\n    y = 2\n    assert a < x + y\n    return a\n',
    'expr stmt prefix': 'def f(a, g):\n    g()\n    assert a\n    return a\n',
    'walrus in cond': 'def f(g):\n    assert (n := g()) > 0\n    return n\n',
    'aug prefix': 'def f(self, a):\n    self.x += 1\n    assert a > self.x\n    return a\n',
    'and chain': 'def f(a, b):\n    z = a + b\n    assert a > 0 and b > 0, "m"\n    return z\n',
    'chained cmp': 'def f(a):\n    z = a\n    assert 0 < z < 10\n    return z\n',
    'import prefix': 'def f(a):\n    import os\n    assert a\n    return a\n',
}


def depth_after(opcode, arg):
    try:
        return dis.stack_effect(opcode, arg if arg is not None else 0)
    except Exception:
        return None


for name, src in CASES.items():
    code = compile(src, '<t>', 'exec')
    fn = [c for c in code.co_consts if hasattr(c, 'co_code')][0]
    cfg = build_cfg(fn)
    print('=' * 70)
    print(name)
    for b in cfg.get_blocks_in_order():
        last = b.get_last_instruction()
        print(f'  block {b.start_offset}-{b.end_offset} last={last.opname if last else None}')
        depth = 0
        zero_idx = -1
        instrs = b.instructions
        for idx, i in enumerate(instrs):
            if last is not None and i is last and (
                    i.opname.startswith('POP_JUMP') or i.opname.startswith('JUMP')
                    or i.opname.startswith('FOR_ITER') or i.opname.startswith('JUMP_IF')):
                print(f'    {idx:3d} {i.offset:5d} {i.opname:32s} <TERM JUMP>')
                break
            se = depth_after(i.opcode, i.arg)
            if se is None:
                print(f'    {idx:3d} {i.offset:5d} {i.opname:32s} ?? unknown effect')
                depth = None
                break
            depth += se
            if depth == 0:
                zero_idx = idx
            print(f'    {idx:3d} {i.offset:5d} {i.opname:32s} d={depth}')
        print(f'    -> condition starts after idx {zero_idx}')
