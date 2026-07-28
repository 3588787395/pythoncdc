"""R26 测试工程师：批量创建10+最小复现实例，验证for-else误识别问题
场景：for循环体所有分支都continue，循环后紧跟的语句应归for-else，
但反编译器错误放入循环体，导致多余JUMP_BACKWARD(continue)。
"""
import sys
import os
import dis
import types

sys.path.insert(0, '/workspace')
from pycdc import decompile_pyc

OUT_DIR = '/workspace/.trae/specs/quotation-pyc-iteration/rounds/round_26/test_engineer/minimal_repros'
os.makedirs(OUT_DIR, exist_ok=True)

CASES = [
    # (id, src)
    ('repro_01_for_else_after_continue_chain', '''
def f(items, result):
    for key, value in items.items():
        if not key == 'skip':
            if key == 'a':
                continue
            else:
                result.append(value)
                continue
    else:
        result.append(-1)
'''),
    ('repro_02_for_else_all_continue', '''
def f(items, result):
    for x in items:
        if x > 0:
            continue
        else:
            result.append(x)
            continue
    else:
        result.append(-1)
'''),
    ('repro_03_for_else_elif_continue', '''
def f(items, out):
    for k, v in items.items():
        if k == 'a':
            continue
        elif isinstance(v, dict):
            out.update(v)
            continue
        else:
            out[k] = v
            continue
    else:
        out.append(0)
'''),
    ('repro_04_for_else_negated_cond_continue', '''
def f(items, out):
    for k, v in items.items():
        if not k == 'skip':
            if k == 'x':
                continue
            else:
                out[k] = v
                continue
    else:
        out.append(0)
'''),
    ('repro_05_for_else_two_branches_continue', '''
def f(items, out):
    for x in items:
        if x == 1:
            continue
        if x == 2:
            continue
        out.append(x)
    else:
        out.append(-1)
'''),
    ('repro_06_for_else_nested_if_continue', '''
def f(items, out):
    for x in items:
        if x > 0:
            if x == 5:
                continue
            else:
                out.append(x)
                continue
    else:
        out.append(-1)
'''),
    ('repro_07_for_else_single_continue', '''
def f(items, out):
    for x in items:
        if x == 0:
            continue
        out.append(x)
    else:
        out.append(-1)
'''),
    ('repro_08_for_else_dict_update_continue', '''
def f(items, dict1):
    for k, v in items.items():
        if not k == 'skip':
            if k == 'a':
                continue
            elif isinstance(v, dict):
                dict1.update(v)
                continue
            else:
                dict1[k] = v
                continue
    else:
        dict1['done'] = True
'''),
    ('repro_09_for_else_while_inner_continue', '''
def f(items, out):
    for x in items:
        if x > 0:
            continue
        out.append(x)
    else:
        out.append(-1)
'''),
    ('repro_10_for_else_continue_then_append', '''
def f(items, data_out):
    for i in items:
        for key, value in i.items():
            if not key == 'skip':
                if key == 'a':
                    continue
                else:
                    pass
                    continue
        else:
            data_out.append(1)
'''),
    ('repro_11_for_else_all_branches_return_continue', '''
def f(items, out):
    for x in items:
        if x == 1:
            continue
        elif x == 2:
            out.append(x)
            continue
        else:
            out.append(x * 2)
            continue
    else:
        out.append(-1)
'''),
    ('repro_12_for_else_negated_continue_single', '''
def f(items, out):
    for k, v in items.items():
        if not k == 'skip':
            out[k] = v
            continue
    else:
        out.append(0)
'''),
]

def get_instrs(co):
    out = []
    for ins in dis.get_instructions(co):
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        out.append((ins.offset, ins.opname, ins.argval, ins.argrepr))
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
    # write source
    spath = os.path.join(OUT_DIR, cid + '.py')
    with open(spath, 'w') as f:
        f.write(src)
    # compile and decompile
    co = compile(src, cid, 'exec')
    pyc_path = os.path.join(OUT_DIR, cid + '.pyc')
    with open(pyc_path, 'wb') as f:
        import importlib.util
        f.write(importlib.util.MAGIC_NUMBER)
        f.write(b'\x00' * 12)
        import marshal
        f.write(marshal.dumps(co))
    try:
        decomp = decompile_pyc(pyc_path, use_cfg=False, cfg_hybrid=False)
    except Exception as e:
        decomp = f'# DECOMPILE ERROR: {e}'
    dpath = os.path.join(OUT_DIR, cid + '_decompiled.py')
    with open(dpath, 'w') as f:
        f.write(decomp)
    # compare bytecode
    try:
        f_co = find_co(co, 'f')
        d_co = find_co(compile(decomp, cid + '_d', 'exec'), 'f')
        if f_co and d_co:
            fi = get_instrs(f_co)
            di = get_instrs(d_co)
            match = (len(fi) == len(di) and all(a[1]==b[1] and a[2]==b[2] for a,b in zip(fi,di)))
            # find first diff
            fd = None
            for i in range(max(len(fi), len(di))):
                a = fi[i] if i < len(fi) else None
                b = di[i] if i < len(di) else None
                if not (a and b and a[1]==b[1] and a[2]==b[2]):
                    fd = i
                    break
            status = 'MATCH' if match else 'DIFF'
            diff_detail = ''
            if fd is not None:
                a = fi[fd] if fd < len(fi) else None
                b = di[fd] if fd < len(di) else None
                diff_detail = f' first_diff@{fd}: pyc={a[1] if a else None}({a[3] if a else ""}) src={b[1] if b else None}({b[3] if b else ""})'
            results.append((cid, status, len(fi), len(di), diff_detail))
        else:
            results.append((cid, 'NO_FUNC', 0, 0, ''))
    except Exception as e:
        results.append((cid, f'ERR:{e}', 0, 0, ''))

print("=== 最小复现实例验证结果 ===")
print(f"{'CASE':<45} {'STATUS':<10} {'PYC':>5} {'SRC':>5} DETAIL")
for cid, status, plen, slen, detail in results:
    print(f"{cid:<45} {status:<10} {plen:>5} {slen:>5} {detail}")

matched = sum(1 for r in results if r[1] == 'MATCH')
diffed = sum(1 for r in results if r[1] == 'DIFF')
print(f"\n匹配: {matched}/{len(results)}, 差异: {diffed}/{len(results)}")
