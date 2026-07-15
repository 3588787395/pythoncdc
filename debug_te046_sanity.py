import sys, ast, dis
sys.path.insert(0, '/workspace')
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator

src = "try:\n    with open('a') as fa:\n        with open('b') as fb:\n            x = fa.read() + fb.read()\nexcept:\n    x = ''"
code = compile(src, '<t>', 'exec')

cfg = CFGBuilder().build(code)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()
gen = RegionASTGenerator(cfg, analyzer)
ast_dict = gen.generate()
code_gen = CodeGenerator()
decompiled = code_gen.generate(ast_dict)
print("==== CURRENT DECOMPILED ====")
print(decompiled)
print()

# Now strip the spurious "if True:\n    pass"
import re
fixed = re.sub(r'\nif True:\n    pass\n?$', '', decompiled.rstrip() + '\n')
print("==== FIXED DECOMPILED (if True: pass removed) ====")
print(fixed)
print()

# Verify bytecode equivalence
orig_instrs = list(dis.get_instructions(code))
print("Original instruction count:", len(orig_instrs))

recomp_cur = compile(decompiled, '<d>', 'exec')
cur_instrs = list(dis.get_instructions(recomp_cur))
print("Current decompiled instruction count:", len(cur_instrs))

recomp_fix = compile(fixed, '<d>', 'exec')
fix_instrs = list(dis.get_instructions(recomp_fix))
print("Fixed decompiled instruction count:", len(fix_instrs))

print()
print("==== Compare orig vs fixed (opname sequence) ====")
orig_ops = [i.opname for i in orig_instrs]
fix_ops = [i.opname for i in fix_instrs]
if orig_ops == fix_ops:
    print("MATCH! orig opnames == fixed opnames")
else:
    print("MISMATCH")
    for i, (o, f) in enumerate(zip(orig_ops, fix_ops)):
        if o != f:
            print(f"  diff at {i}: orig={o} fix={f}")
    if len(orig_ops) != len(fix_ops):
        print(f"  length diff: orig={len(orig_ops)} fix={len(fix_ops)}")
        print(f"  orig tail: {orig_ops[-10:]}")
        print(f"  fix tail: {fix_ops[-10:]}")
