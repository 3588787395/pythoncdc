"""R26: 复现IfRegion then_blocks边界识别错误
原始: if cond: n=...; else: return data; data=...; return round(data,2)
反编译错误: if cond: n=...; data=...; return round(data,2); else: return data
"""
import sys
import os
import dis
import types
import marshal
import importlib.util

sys.path.insert(0, '/workspace')
from pycdc import decompile_pyc

OUT_DIR = '/workspace/.trae/specs/quotation-pyc-iteration/rounds/round_26/test_engineer/minimal_repros'
os.makedirs(OUT_DIR, exist_ok=True)

CASES = [
    ('repro_r26_chf_01_if_else_then_continue', '''
def f(series, data):
    n = None
    if len(series) > 1:
        n = list(series)[1]
    else:
        return data
    data = data * float(n) + 1
    return round(data, 2)
'''),
    ('repro_r26_chf_02_if_else_then_stmts', '''
def f(a, b):
    if a > 0:
        x = a + 1
    else:
        return b
    y = x * 2
    return y
'''),
    ('repro_r26_chf_03_nested_if_else_then', '''
def f(a, b):
    if a == b:
        if len(a) > 1:
            n = a[1]
        else:
            return b
        result = n * 2
        return result
    else:
        return b
'''),
    ('repro_r26_chf_04_elif_else_then', '''
def f(a, b):
    if a == 1:
        return b
    elif a == 2:
        x = a + 1
    else:
        return b
    y = x * 2
    return y
'''),
    ('repro_r26_chf_05_if_return_else_assign_then', '''
def f(a, b):
    if a > 10:
        return b
    else:
        x = a
    y = x + 1
    return y
'''),
    ('repro_r26_chf_06_if_else_return_then_compute', '''
def f(series, data, n):
    if len(series) > 1:
        n = list(series)[1]
    else:
        return data
    data = data * float(series[n]) + float(series[n+1])
    return round(data, 2)
'''),
    ('repro_r26_chf_07_if_else_with_complex_body', '''
def f(a, b, c):
    if a == b:
        if len(c) > 1:
            n = c[1]
        else:
            return b
        result = n * float(a) + float(b)
        return round(result, 2)
    return c
'''),
    ('repro_r26_chf_08_if_else_then_two_stmts', '''
def f(a, b):
    if a > 0:
        x = a
    else:
        return b
    y = x + 1
    z = y * 2
    return z
'''),
    ('repro_r26_chf_09_if_else_then_call', '''
def f(a, b):
    if a > 0:
        x = a
    else:
        return b
    return round(x, 2)
'''),
    ('repro_r26_chf_10_elif_chain_else_then', '''
def f(a, b):
    if a == 1:
        return b
    elif a == 2:
        return b
    elif a == 3:
        x = a
    else:
        return b
    y = x + 1
    return y
'''),
]

def get_instrs(co):
    out = []
    for ins in dis.get_instructions(co):
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        out.append((ins.offset, ins.opname, ins.argval))
    return out

def find_co(co, name):
    if co.co_name == name:
        return co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            r = find_co(c, name)
            if r:
                return r
    return None

results = []
for cid, src in CASES:
    spath = os.path.join(OUT_DIR, cid + '.py')
    with open(spath, 'w') as f:
        f.write(src)
    co = compile(src, cid, 'exec')
    pyc_path = os.path.join(OUT_DIR, cid + '.pyc')
    with open(pyc_path, 'wb') as f:
        f.write(importlib.util.MAGIC_NUMBER)
        f.write(b'\x00' * 12)
        f.write(marshal.dumps(co))
    try:
        decomp = decompile_pyc(pyc_path, use_cfg=False, cfg_hybrid=False)
    except Exception as e:
        decomp = f'# DECOMPILE ERROR: {e}'
    dpath = os.path.join(OUT_DIR, cid + '_decompiled.py')
    with open(dpath, 'w') as f:
        f.write(decomp)
    try:
        f_co = find_co(co, 'f')
        d_co = find_co(compile(decomp, cid + '_d', 'exec'), 'f')
        if f_co and d_co:
            fi = get_instrs(f_co)
            di = get_instrs(d_co)
            match = (len(fi) == len(di) and all(a==b for a,b in zip(fi,di)))
            fd = None
            for i in range(max(len(fi), len(di))):
                a = fi[i] if i < len(fi) else None
                b = di[i] if i < len(di) else None
                if not (a and b and a==b):
                    fd = i
                    break
            status = 'MATCH' if match else 'DIFF'
            diff_detail = ''
            if fd is not None:
                a = fi[fd] if fd < len(fi) else None
                b = di[fd] if fd < len(di) else None
                diff_detail = f' @{fd}: pyc={a[1] if a else None}/{a[2] if a else None} src={b[1] if b else None}/{b[2] if b else None}'
            results.append((cid, status, len(fi), len(di), diff_detail))
        else:
            results.append((cid, 'NO_FUNC', 0, 0, ''))
    except Exception as e:
        results.append((cid, f'ERR:{e}', 0, 0, ''))

print("=== R26 IfRegion then_blocks边界 最小复现 ===")
print(f"{'CASE':<45} {'STATUS':<8} {'PYC':>4} {'SRC':>4} DETAIL")
for cid, status, plen, slen, detail in results:
    print(f"{cid:<45} {status:<8} {plen:>4} {slen:>4} {detail}")
matched = sum(1 for r in results if r[1] == 'MATCH')
diffed = sum(1 for r in results if r[1] == 'DIFF')
print(f"\n匹配: {matched}/{len(results)}, 差异: {diffed}/{len(results)}")

# Show diff for first DIFF case
for cid, status, plen, slen, detail in results:
    if status == 'DIFF':
        print(f"\n=== {cid} 差异详情 ===")
        idx = [c[0] for c in CASES].index(cid)
        src = CASES[idx][1]
        co = compile(src, cid, 'exec')
        f_co = find_co(co, 'f')
        fi = get_instrs(f_co)
        # decompile
        pyc_path = os.path.join(OUT_DIR, cid + '.pyc')
        decomp = decompile_pyc(pyc_path, use_cfg=False, cfg_hybrid=False)
        d_co = find_co(compile(decomp, cid + '_d', 'exec'), 'f')
        di = get_instrs(d_co)
        print("--- PYC ---")
        for i, ins in enumerate(fi):
            print(f"  [{i:>3}] {ins[0]:>4} {ins[1]:<30} {ins[2]}")
        print("--- SRC ---")
        for i, ins in enumerate(di):
            print(f"  [{i:>3}] {ins[0]:>4} {ins[1]:<30} {ins[2]}")
        break
