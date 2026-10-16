#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""9.2 续作 B124 生成器桶插桩诊断：T19-4 命中情况（字节级备份→插桩→regen→还原）。

在 _ternary_host_call_prefix_span 的关键点加 [T] 打印：
  - 入口（cond 块 offset）
  - 残差/residual/深度
  - 闭合点（close op+offset+dipped）
  - _generate_host_prefix_ternary_statement 的 span 尾指令
产物→D:\\Temp\\opencode\\r92_products；证据→r9v9fix_diag_t194.txt。
"""
import hashlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
GEN = os.path.join(ROOT, 'core', 'cfg', 'region_ast_generator.py')
BAKDIR = r'D:\Temp\opencode\r92bak2'
LOG = os.path.join(HERE, 'r9v9fix_diag_t194.txt')

INSTR1 = ("    def _ternary_host_call_prefix_span(self, region):\r\n",
          "    def _ternary_host_call_prefix_span(self, region):\r\n"
          "        import sys as _t_sys\r\n"
          "        print('[T] t194 enter region_cond=%s' % (getattr(region, 'condition_block', None) and region.condition_block.start_offset), file=_t_sys.stderr)\r\n")
INSTR2 = ("                    closed = True\r\n                    close_offset = ins.offset\r\n                    break\r\n",
          "                    closed = True\r\n                    close_offset = ins.offset\r\n"
          "                    print('[T] close op=%s off=%s dipped=%s' % (ins.opname, ins.offset, dipped), file=_t_sys.stderr)\r\n"
          "                    break\r\n")
INSTR3 = ("        if not closed or dipped is not True:\r\n            return None\r\n",
          "        if not closed or dipped is not True:\r\n"
          "            print('[T] bail closed=%s dipped=%s' % (closed, dipped), file=_t_sys.stderr)\r\n"
          "            return None\r\n")


def sha(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def main():
    os.makedirs(BAKDIR, exist_ok=True)
    base = sha(GEN)
    with open(GEN, 'rb') as f:
        orig = f.read()
    with open(os.path.join(BAKDIR, 'region_ast_generator.py'), 'wb') as g:
        g.write(orig)
    text = orig.decode('utf-8')
    for old, new in (INSTR1, INSTR2, INSTR3):
        assert text.count(old) == 1, 'anchor x%d: %r' % (text.count(old), old[:60])
        text = text.replace(old, new)
    try:
        with open(GEN, 'wb') as f:
            f.write(text.encode('utf-8'))
        out_lines = []
        for name, rel in [('e10', 'test_repros/round3/e10_g7_call_args.pyc'),
                          ('r8_10', 'test_repros/round8/r8_10_expr_cross_stmt.pyc')]:
            full = os.path.join(ROOT, rel.replace('/', os.sep))
            ok = os.path.join(r'D:\Temp\opencode\r92_products', name + '_t194.py')
            p = subprocess.run([sys.executable, os.path.join(ROOT, 'pycdc.py'),
                                full, '-o', ok], capture_output=True, text=True,
                               cwd=ROOT, timeout=250, encoding='utf-8', errors='replace')
            out_lines.append('=== %s regen stderr [T] lines ===' % name)
            out_lines += [l for l in ((p.stdout or '') + (p.stderr or '')).splitlines()
                          if '[T]' in l or 'Traceback' in l or 'Error' in l]
        open(LOG, 'w', encoding='utf-8', newline='\n').write('\n'.join(out_lines))
        print('\n'.join(out_lines[:80]))
    finally:
        with open(os.path.join(BAKDIR, 'region_ast_generator.py'), 'rb') as f:
            data = f.read()
        with open(GEN, 'wb') as f:
            f.write(data)
        assert sha(GEN) == base, 'RESTORE FAILED'
        print('-> restored OK, log -> ' + LOG)


if __name__ == '__main__':
    main()
