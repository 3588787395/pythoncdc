#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""9.2 续作 B126 诊断：assert 双识别守卫实况（插桩，结束还原）。"""
import hashlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
ANA = os.path.join(ROOT, 'core', 'cfg', 'region_analyzer.py')
BAKDIR = r'D:\Temp\opencode\r92bak2'
LOG = os.path.join(HERE, 'r9v9fix_diag_b126.txt')

G_OLD = ("            _existing_region = self.block_to_region.get(block)\r\n"
         "            if isinstance(_existing_region, AssertRegion):\r\n"
         "                continue\r\n")
G_NEW = ("            _existing_region = self.block_to_region.get(block)\r\n"
         "            import sys as _t_sys\r\n"
         "            if isinstance(_existing_region, AssertRegion):\r\n"
         "                print('[G] skip blk@%s owned by assert@%s' % (block.start_offset, getattr(getattr(_existing_region, 'entry', None), 'start_offset', None)), file=_t_sys.stderr)\r\n"
         "                continue\r\n"
         "            print('[G] cand blk@%s' % block.start_offset, file=_t_sys.stderr)\r\n")
R_OLD = ("            regions.append(region)\r\n"
         "            self.regions.append(region)\r\n"
         "            if block not in self.block_to_region:\r\n"
         "                self.block_to_region[block] = region\r\n")
R_NEW = ("            import sys as _t_sys2\r\n"
         "            print('[R] new assert entry@%s blocks=%s chain=%s ops=%s' % (block.start_offset, sorted(b.start_offset for b in region.blocks), [b.start_offset for b in chained_compare_blocks], chained_compare_ops), file=_t_sys2.stderr)\r\n"
         "            regions.append(region)\r\n"
         "            self.regions.append(region)\r\n"
         "            if block not in self.block_to_region:\r\n"
         "                self.block_to_region[block] = region\r\n")


def sha(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def main():
    os.makedirs(BAKDIR, exist_ok=True)
    base = sha(ANA)
    orig = open(ANA, 'rb').read()
    with open(os.path.join(BAKDIR, 'region_analyzer.py'), 'wb') as g:
        g.write(orig)
    text = orig.decode('utf-8')
    for old, new in ((G_OLD, G_NEW), (R_OLD, R_NEW)):
        assert text.count(old) == 1, 'anchor x%d %r' % (text.count(old), old[:60])
        text = text.replace(old, new)
    try:
        with open(ANA, 'wb') as f:
            f.write(text.encode('utf-8'))
        p = subprocess.run([sys.executable, os.path.join(ROOT, 'pycdc.py'),
                            os.path.join(ROOT, 'test_repros', 'round9', 'n9v9_stmt_sweep.pyc'),
                            '-o', r'D:\Temp\opencode\r92_products\n9sweep_instr.py'],
                           capture_output=True, text=True, cwd=ROOT, timeout=250,
                           encoding='utf-8', errors='replace')
        out = [l for l in ((p.stdout or '') + (p.stderr or '')).splitlines()
               if '[G]' in l or '[R]' in l]
        open(LOG, 'w', encoding='utf-8', newline='\n').write('\n'.join(out))
        print('\n'.join(out[:50]))
    finally:
        with open(os.path.join(BAKDIR, 'region_analyzer.py'), 'rb') as f:
            data = f.read()
        with open(ANA, 'wb') as f:
            f.write(data)
        assert sha(ANA) == base, 'RESTORE FAILED'
        print('-> restored OK')


if __name__ == '__main__':
    main()
