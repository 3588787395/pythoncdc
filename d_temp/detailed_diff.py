import sys, dis, marshal, types, importlib

sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from core.cfg import decompile

with open(r'F:\Downloads\pythoncdc-main\site-packages\IQData\utils\common_func.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

ok_source = open(r'F:\Downloads\pythoncdc-main\site-packages\IQData\utils\common_funcOK.py', 'r', encoding='utf-8').read()

compiled = compile(ok_source, '<decompiled>', 'exec')
for orig_const in code.co_consts:
    if isinstance(orig_const, types.CodeType) and orig_const.co_name == 'handle_exrights':
        for comp_const in compiled.co_consts:
            if isinstance(comp_const, types.CodeType) and comp_const.co_name == 'handle_exrights':
                orig_instrs = list(dis.get_instructions(orig_const))
                comp_instrs = list(dis.get_instructions(comp_const))
                print(f"orig instructions: {len(orig_instrs)}")
                print(f"comp instructions: {len(comp_instrs)}")
                diffs = 0
                for i, (o, c) in enumerate(zip(orig_instrs, comp_instrs)):
                    if o.opname != c.opname or o.arg != c.arg:
                        diffs += 1
                        if diffs <= 10:
                            print(f"  diff at {i}: orig={o.opname}({o.arg}) decomp={c.opname}({c.arg})")
                print(f"total diffs: {diffs}")
