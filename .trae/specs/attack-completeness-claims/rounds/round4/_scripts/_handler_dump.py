import importlib.util
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..', '..'))
spec = importlib.util.spec_from_file_location('pv', os.path.join(ROOT, 'scripts', 'pyc_verify.py'))
pv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pv)
PU = pv.DEFAULT_PYLINGUAL
sys.path.insert(0, PU)
import typing
if not hasattr(typing, 'override'):
    typing.override = lambda f: f
stub = types.ModuleType('pydot')
stub.graph_from_dot_data = lambda *a, **k: []
stub.Dot = stub.Node = stub.Edge = lambda *a, **k: None
sys.modules['pydot'] = stub
pkg = types.ModuleType('pylingual')
pkg.__path__ = [os.path.join(PU, 'pylingual')]
sys.modules['pylingual'] = pkg

from pylingual.editable_bytecode import PYCFile
from pylingual.editable_bytecode.bytecode_patches import (
    fix_indirect_jump, fix_unreachable, remove_extended_arg, remove_nop, replace_firstlno)

BASE = os.path.join(ROOT, '.trae', 'specs', 'attack-completeness-claims', 'rounds', 'round4')
A_PYC = os.path.join(BASE, '_probes', 'cp_except_tuple_order.pyc')
B_PY = os.path.join(BASE, '_scratch', 'construct', 'cp_except_tuple_order_mut.py')

import py_compile
recompiled = os.path.join(BASE, '_scratch', 'construct', '_recomp.pyc')
py_compile.compile(B_PY, cfile=recompiled, doraise=True, optimize=0)

pa = PYCFile(A_PYC)
pb = PYCFile(recompiled)
pa.apply_patches([remove_extended_arg, remove_nop, fix_indirect_jump, fix_unreachable, remove_extended_arg, replace_firstlno])
pb.apply_patches([remove_extended_arg, remove_nop, fix_indirect_jump, fix_unreachable, remove_extended_arg, replace_firstlno])


def dump(pf, label):
    print('=' * 12, label)
    for bc in pf.iter_bytecodes():
        print(' -- %s --' % bc.name)
        for ins in bc.instructions:
            print('   %-24s arg=%-4s argval=%r' % (ins.opname, ins.arg, ins.argval))


dump(pa, 'ORIGINAL pyc (except (A, B))')
dump(pb, 'MUTATED recompiled (except (B, A))')
