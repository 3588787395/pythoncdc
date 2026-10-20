# -*- coding: utf-8 -*-
"""R5 B122 hang 追踪：faulthandler 定时 dump 栈（单次，exit=True）后硬退。

用法: python -X utf8 _r5_hang_trace.py <pyc> <out_ok.py> <trace_txt> [timeout_sec]
"""
import faulthandler
import os
import runpy
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    '..', '..', '..', '..', '..'))
pyc, ok, trace = sys.argv[1], sys.argv[2], sys.argv[3]
timeout = int(sys.argv[4]) if len(sys.argv) > 4 else 20
f = open(trace, 'w', encoding='utf-8')
faulthandler.dump_traceback_later(timeout, exit=True, file=f)
sys.argv = ['pycdc.py', pyc, '-o', ok]
os.chdir(ROOT)
sys.path.insert(0, ROOT)
try:
    runpy.run_path(os.path.join(ROOT, 'pycdc.py'), run_name='__main__')
except SystemExit as e:
    print('SystemExit', e, file=sys.stderr)
