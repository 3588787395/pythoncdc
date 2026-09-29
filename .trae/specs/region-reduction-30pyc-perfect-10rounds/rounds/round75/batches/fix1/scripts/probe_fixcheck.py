# -*- coding: utf-8 -*-
"""fix1: prove the fix target -- restore operand A in the two failing jq units'
product source and re-run the mandated ruler on that text."""
import io
import os
import py_compile
import sys
import tempfile

sys.path.insert(0, r'F:\Downloads\pythoncdc-main\scripts')
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:/Downloads\pythoncdc-main'
PYC = REPO + r'\site-packages\IQCommon\strategy\jq_trans_module.pyc'
SRC = REPO + r'\site-packages\IQCommon\strategy\jq_trans_moduleOK.py'

from pyc_verify import load_compare_pyc  # noqa: E402

compare_pyc = load_compare_pyc(r'D:\Desktop\ptrade相关\pylingual')

text = io.open(SRC, encoding='utf-8').read()
old = "if ')' not in stock_tmp or '[' in stock_tmp and ']' not in stock_tmp:"
new = "if '(' in stock_tmp and ')' not in stock_tmp or '[' in stock_tmp and ']' not in stock_tmp:"
n = text.count(old)
print('occurrences of target line: %d' % n)
text2 = text.replace(old, new)

tmp = tempfile.mkdtemp(prefix='fix1jq_')
srcp = os.path.join(tmp, 'x.py')
cpyp = os.path.join(tmp, 'x.pyc')
io.open(srcp, 'w', encoding='utf-8', newline='\n').write(text2)
py_compile.compile(srcp, cfile=cpyp, doraise=True, optimize=0)

res = compare_pyc(PYC, cpyp)
bad = [r for r in res if not r.success]
print('units %d/%d' % (len(res) - len(bad), len(res)))
for r in bad:
    print('  FAIL', r)
for r in res:
    if 'replace_args' in str(getattr(r, 'name', '')) or 'replace_args' in str(r):
        print('  unit:', r)
