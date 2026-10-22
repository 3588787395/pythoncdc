import importlib.util
import inspect
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..', '..'))
spec = importlib.util.spec_from_file_location('pv', os.path.join(ROOT, 'scripts', 'pyc_verify.py'))
pv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pv)
PU = pv.DEFAULT_PYLINGUAL
print('pylingual root:', PU, os.path.isdir(PU))

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

from pylingual.editable_bytecode import bytecode_patches as bp

for fn in ('fix_unreachable', 'remove_nop', 'replace_firstlno', 'fix_indirect_jump'):
    f = getattr(bp, fn, None)
    if f is None:
        print('MISSING', fn)
        continue
    try:
        src = inspect.getsource(f)
    except Exception as e:
        src = '?? %s' % e
    print('#' * 25, fn)
    print(src[:2400])
