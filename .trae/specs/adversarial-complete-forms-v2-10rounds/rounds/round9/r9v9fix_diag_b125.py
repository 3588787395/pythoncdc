#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""9.2 续作 B125 诊断：else 块 42 的 generated 归属链（插桩，结束还原）。

插桩点：
  A = _loop_generate_while else 循环（9065 一带）：每 else 块打印 offset/是否 generated/是否 child_owned
  B = _loop_generate_for break 目标循环（7009 一带）：每 _bb 打印 offset/是否 generated
证据 → r9v9fix_diag_b125.txt
"""
import hashlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
GEN = os.path.join(ROOT, 'core', 'cfg', 'region_ast_generator.py')
BAKDIR = r'D:\Temp\opencode\r92bak2'
LOG = os.path.join(HERE, 'r9v9fix_diag_b125.txt')

A_OLD = ("            for _eb in _filtered_else_blocks:\r\n"
         "                if _eb in self.generated_blocks:\r\n"
         "                    _r2114_else_owned_skipped += 1\r\n"
         "                    continue\r\n")
A_NEW = ("            for _eb in _filtered_else_blocks:\r\n"
         "                import sys as _t_sys\r\n"
         "                print('[A] while-else blk@%s gen=%s child=%s skipped=%s' % (_eb.start_offset, _eb in self.generated_blocks, _eb in _child_region_blocks_r23, _r2114_else_owned_skipped), file=_t_sys.stderr)\r\n"
         "                if _eb in self.generated_blocks:\r\n"
         "                    _r2114_else_owned_skipped += 1\r\n"
         "                    continue\r\n")
B_OLD = ("            _bb_processed_offsets = set()\r\n"
         "            for _bb in region.break_blocks:\r\n"
         "                if _bb in _body_set:\r\n"
         "                    continue\r\n")
B_NEW = ("            _bb_processed_offsets = set()\r\n"
         "            import sys as _t_sys2\r\n"
         "            print('[B] for breakblocks=%s' % [b.start_offset for b in region.break_blocks], file=_t_sys2.stderr)\r\n"
         "            for _bb in region.break_blocks:\r\n"
         "                if _bb in _body_set:\r\n"
         "                    print('[B]   in-body skip blk@%s' % _bb.start_offset, file=_t_sys2.stderr)\r\n"
         "                    continue\r\n"
         "                print('[B]   proc blk@%s gen=%s' % (_bb.start_offset, _bb in self.generated_blocks), file=_t_sys2.stderr)\r\n")


def sha(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def main():
    os.makedirs(BAKDIR, exist_ok=True)
    base = sha(GEN)
    orig = open(GEN, 'rb').read()
    with open(os.path.join(BAKDIR, 'region_ast_generator.py'), 'wb') as g:
        g.write(orig)
    text = orig.decode('utf-8')
    for old, new in ((A_OLD, A_NEW), (B_OLD, B_NEW)):
        assert text.count(old) == 1, 'anchor x%d %r' % (text.count(old), old[:50])
        text = text.replace(old, new)
    try:
        with open(GEN, 'wb') as f:
            f.write(text.encode('utf-8'))
        out_lines = []
        p = subprocess.run([sys.executable, os.path.join(ROOT, 'pycdc.py'),
                            os.path.join(ROOT, 'test_repros', 'round4', 'r4v4r_b109_loopelse.pyc'),
                            '-o', r'D:\Temp\opencode\r92_products\b109_instr.py'],
                           capture_output=True, text=True, cwd=ROOT, timeout=250,
                           encoding='utf-8', errors='replace')
        out_lines += [l for l in ((p.stdout or '') + (p.stderr or '')).splitlines()
                      if '[A]' in l or '[B]' in l]
        open(LOG, 'w', encoding='utf-8', newline='\n').write('\n'.join(out_lines))
        print('\n'.join(out_lines[:40]))
    finally:
        with open(os.path.join(BAKDIR, 'region_ast_generator.py'), 'rb') as f:
            data = f.read()
        with open(GEN, 'wb') as f:
            f.write(data)
        assert sha(GEN) == base, 'RESTORE FAILED'
        print('-> restored OK')


if __name__ == '__main__':
    main()
