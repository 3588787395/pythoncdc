#!/usr/bin/env python3
"""Find all partial pyc files in site-packages."""
import os, sys, types, marshal, dis
sys.path.insert(0, '.')

from core.cfg import build_cfg, RegionASTGenerator
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CodeGenerator

pyc_files = []
for root, dirs, files in os.walk('site-packages'):
    for f in files:
        if f.endswith('.pyc'):
            pyc_files.append(os.path.join(root, f))

partials = []
for pyc_path in sorted(pyc_files):
    try:
        with open(pyc_path, 'rb') as f:
            f.read(16)
            code = marshal.load(f)

        total = [0]
        matched = [0]

        def check_code(c):
            try:
                cfg = build_cfg(c)
                gen = RegionASTGenerator(cfg)
                ast_dict = gen.generate()
                converter = CFGASTConverter()
                py_ast = converter.convert(ast_dict)
                generator = CodeGenerator()
                src = generator.generate(py_ast)
                recompiled = compile(src, '<decompiled>', 'exec')
                orig_instrs = list(dis.get_instructions(c))
                recomp_instrs = list(dis.get_instructions(recompiled))
                if len(orig_instrs) == len(recomp_instrs):
                    if all(a.opname == b.opname for a, b in zip(orig_instrs, recomp_instrs)):
                        matched[0] += 1
                total[0] += 1
            except Exception:
                total[0] += 1
            for const in c.co_consts:
                if isinstance(const, types.CodeType):
                    check_code(const)

        check_code(code)
        if total[0] > 0 and matched[0] < total[0]:
            partials.append((pyc_path, matched[0], total[0]))
    except Exception as e:
        pass

for p, m, t in sorted(partials, key=lambda x: x[1]/x[2], reverse=True):
    print(f'{p}: {m}/{t} ({100*m/t:.0f}%)')
