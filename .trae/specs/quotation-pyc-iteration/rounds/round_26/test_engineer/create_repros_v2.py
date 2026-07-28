"""R26: 精确复现if-continue vs if-not识别问题
原始: if cond: continue  (POP_JUMP_FORWARD_IF_TRUE to continue_block)
反编译误识别为: if not cond: <next statements>
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

# 精确复现get_option_info的结构
CASES = [
    ('repro_r26_01_if_continue_then_if', '''
def f(items, out):
    for key, value in items.items():
        if key == 'skip':
            continue
        if key == 'a':
            continue
        elif isinstance(value, dict):
            out.update(value)
            continue
        else:
            out[key] = value
            continue
    out.append(0)
'''),
    ('repro_r26_02_if_continue_chain', '''
def f(items, out):
    for x in items:
        if x == 1:
            continue
        if x == 2:
            continue
        out.append(x)
'''),
    ('repro_r26_03_if_continue_then_elif', '''
def f(items, out):
    for k, v in items.items():
        if k == 'skip':
            continue
        if k == 'x':
            continue
        elif isinstance(v, dict):
            out.update(v)
            continue
        else:
            out[k] = v
            continue
'''),
    ('repro_r26_04_if_continue_single', '''
def f(items, out):
    for x in items:
        if x == 0:
            continue
        if x == 1:
            continue
        out.append(x)
'''),
    ('repro_r26_05_if_continue_three', '''
def f(items, out):
    for x in items:
        if x == 1:
            continue
        if x == 2:
            continue
        if x == 3:
            continue
        out.append(x)
'''),
    ('repro_r26_06_if_continue_then_if_else', '''
def f(items, out):
    for k, v in items.items():
        if k == 'skip':
            continue
        if k == 'a':
            out.append(v)
        else:
            out[k] = v
'''),
    ('repro_r26_07_if_continue_while_loop', '''
def f(items, out):
    while items:
        x = items.pop()
        if x == 0:
            continue
        if x == 1:
            continue
        out.append(x)
'''),
    ('repro_r26_08_if_continue_nested_for', '''
def f(data, out):
    for i in data:
        for key, value in i.items():
            if key == 'skip':
                continue
            if key == 'a':
                continue
            elif isinstance(value, dict):
                out.update(value)
                continue
            else:
                out[key] = value
                continue
        out.append(1)
'''),
    ('repro_r26_09_if_continue_compare', '''
def f(items, out):
    for x in items:
        if x > 10:
            continue
        if x < 0:
            continue
        out.append(x)
'''),
    ('repro_r26_10_if_continue_isinstance', '''
def f(items, out):
    for x in items:
        if isinstance(x, str):
            continue
        if isinstance(x, dict):
            continue
        out.append(x)
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
                diff_detail = f' @{fd}: pyc={a[1] if a else None} src={b[1] if b else None}'
            results.append((cid, status, len(fi), len(di), diff_detail))
        else:
            results.append((cid, 'NO_FUNC', 0, 0, ''))
    except Exception as e:
        results.append((cid, f'ERR:{e}', 0, 0, ''))

print("=== R26 if-continue vs if-not 最小复现 ===")
print(f"{'CASE':<45} {'STATUS':<8} {'PYC':>4} {'SRC':>4} DETAIL")
for cid, status, plen, slen, detail in results:
    print(f"{cid:<45} {status:<8} {plen:>4} {slen:>4} {detail}")
matched = sum(1 for r in results if r[1] == 'MATCH')
diffed = sum(1 for r in results if r[1] == 'DIFF')
print(f"\n匹配: {matched}/{len(results)}, 差异: {diffed}/{len(results)}")
