"""Detailed diff for get_valuation_info"""
import sys
import types
import marshal
sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r15_decompiled.py'

with open(PYC, 'rb') as f:
    f.read(16)
    pyc_code = marshal.load(f)

with open(SRC, 'r', encoding='utf-8') as f:
    src = f.read()
src_code = compile(src, SRC, 'exec')

def collect(code, result, prefix):
    name = prefix + '.' + code.co_name if prefix else '<module>'
    result[name] = code
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            collect(c, result, name)

pyc_objs = {}
collect(pyc_code, pyc_objs, '')
src_objs = {}
collect(src_code, src_objs, '')

target = '<module>.get_valuation_info'
pc = pyc_objs[target]
sc = src_objs[target]

print("=== PYC co_consts ===")
for i, c in enumerate(pc.co_consts):
    print(f"  [{i}] {type(c).__name__}: {c!r}")
print("\n=== SRC co_consts ===")
for i, c in enumerate(sc.co_consts):
    print(f"  [{i}] {type(c).__name__}: {c!r}")

print(f"\n=== PYC co_names: {pc.co_names}")
print(f"=== SRC co_names: {sc.co_names}")

# Compare raw bytecodes
import dis
pc_instrs = list(dis.get_instructions(pc))
sc_instrs = list(dis.get_instructions(sc))

print(f"\n=== Instruction count: pyc={len(pc_instrs)}, src={len(sc_instrs)}")

print("\n=== Full side-by-side diff ===")
for i in range(max(len(pc_instrs), len(sc_instrs))):
    pi = pc_instrs[i] if i < len(pc_instrs) else None
    si = sc_instrs[i] if i < len(sc_instrs) else None
    if pi and si:
        p_repr = f"{pi.offset:4d} {pi.opname:30s} {pi.argval!r}"
        s_repr = f"{si.offset:4d} {si.opname:30s} {si.argval!r}"
        marker = "  " if p_repr == s_repr else ">>"
        print(f"  {marker} PYC: {p_repr}")
        print(f"  {marker} SRC: {s_repr}")
    elif pi:
        print(f"  >> PYC ONLY: {pi.offset:4d} {pi.opname:30s} {pi.argval!r}")
    elif si:
        print(f"  >> SRC ONLY: {si.offset:4d} {si.opname:30s} {si.argval!r}")
