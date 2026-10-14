"""§0/§1 support: exception-table coverage of _sync_worker (does the failing loop sit in a
try/except region?) + the successor sets of the compound test legs.

usage: python -X utf8 work/exc_probe.py <abs pyc>
"""
import os
import sys
import types

MIRROR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, MIRROR)
sys.path.insert(0, os.path.join(MIRROR, 'core'))

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg

PYC = sys.argv[1]
mod = load_pyc_file_v2(PYC)
code = mod.code.get() if hasattr(mod.code, 'get') else mod.code
if hasattr(code, 'to_python_code'):
    code = code.to_python_code()


def walk(c):
    yield c
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            yield from walk(k)


co = [c for c in walk(code) if c.co_name == '_sync_worker'][0]
cfg = build_cfg(co)
et = list(getattr(cfg, 'exception_table', None) or [])
print('_sync_worker co_exceptiontable entries =', len(et))
for e in et:
    print('  ', e)
print('successors of the compound test legs (exception edges would appear here as a handler block):')
for off in (232, 364, 522, 544):
    b = cfg.get_block_by_offset(off)
    last = b.get_last_instruction()
    print('  @%-5d last=%-28s succ=%s pred=%s' % (
        off, last.opname,
        sorted(x.start_offset for x in (b.successors or [])),
        sorted(x.start_offset for x in (b.predecessors or []))))
b = cfg.get_block_by_offset(704)
print('  body @704 pred=%s' % sorted(x.start_offset for x in (b.predecessors or [])))
