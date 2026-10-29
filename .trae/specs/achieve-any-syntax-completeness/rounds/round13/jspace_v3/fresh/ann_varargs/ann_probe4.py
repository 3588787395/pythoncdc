# Probe4: what do the RENDERERS receive (which path renders the final def)?
import sys, os
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
os.chdir(r'D:\temp\opencode')

from core.cfg import code_generator as cg

orig_adict = cg.CFGCodeGenerator._generate_arguments_dict
orig_a = cg.CFGCodeGenerator._generate_arguments

def pd(self, args):
    _va = args.get('vararg') if isinstance(args, dict) else None
    _ka = args.get('kwarg') if isinstance(args, dict) else None
    _names = []
    aa = args.get('args') if isinstance(args, dict) else None
    if isinstance(aa, list):
        for x in aa:
            _names.append((x.get('arg'), 'ann' if x.get('annotation') else '-') if isinstance(x, dict) else (x, '-'))
    print('[P4-dict] vararg=%r kwarg=%r args=%r' % (_va, _ka, _names), file=sys.stderr)
    r = orig_adict(self, args)
    print('[P4-dict] -> %s' % r, file=sys.stderr)
    return r

def pa(self, args):
    _va = args.get('vararg') if isinstance(args, dict) else (getattr(args, 'vararg', None) if args is not None else None)
    print('[P4-ast] type=%s vararg=%r' % (type(args).__name__, _va), file=sys.stderr)
    r = orig_a(self, args)
    print('[P4-ast] -> %s' % r, file=sys.stderr)
    return r

cg.CFGCodeGenerator._generate_arguments_dict = pd
cg.CFGCodeGenerator._generate_arguments = pa

import importlib.util
spec = importlib.util.spec_from_file_location('pycdc_main', r'F:\Downloads\pythoncdc-main\pycdc.py')
mod = importlib.util.module_from_spec(spec)
sys.modules['pycdc_main'] = mod
spec.loader.exec_module(mod)
out = mod.decompile_pyc('ann_repro.pyc')
open('ann_repro_probe4.py', 'w', encoding='utf-8').write(out)
