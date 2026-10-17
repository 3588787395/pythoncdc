"""_r2_linetrace.py — trace executed line numbers inside _generate_ternary."""
import io
import marshal
import os
import sys
import types

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PYC = sys.argv[1]
CO = sys.argv[2]
LO, HI = int(sys.argv[3]), int(sys.argv[4])
FNAME = sys.argv[5] if len(sys.argv) > 5 else '_generate_ternary'

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator


def find_code(code, name, out):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                out.append(const)
            find_code(const, name, out)


data = open(PYC, 'rb').read()
code = marshal.loads(data[16:])
targets = []
find_code(code, CO, targets)
co = targets[-1]
cfg = build_cfg(co)
gen = RegionASTGenerator(cfg, top_level_code=None)

log = []

def tracer(frame, event, arg):
    if event == 'call':
        if frame.f_code.co_name == FNAME:
            frame.f_trace_lines = True
            return tracer
        return None
    if event == 'line':
        ln = frame.f_lineno
        if LO <= ln <= HI:
            log.append(ln)
    if event == 'return':
        return None
    return tracer

sys.settrace(tracer)
try:
    gen.generate()
finally:
    sys.settrace(None)

for ln in log:
    print(ln)
