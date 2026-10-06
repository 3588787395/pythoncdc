"""Round-3 specimen generator + three-step battery (test-side only).

Pipeline per arm: write .py -> py_compile .pyc -> pycdc.py -o <base>OK.py -> judge batch.
Never hand-edits a decompiled product. Judge remains scripts/pyc_verify.py.
Usage: python -X utf8 test_repros/round3/_r3gen.py <py> [<py> ...]   (no args = all)
"""
import json
import pathlib
import py_compile
import subprocess
import sys

ROOT = pathlib.Path(r'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main')
D = ROOT / 'test_repros' / 'round3'

# ---- file 1: order_api.pyc  (base_order / future_order / option_order) ----
S1 = r'''
def f(a):
    o = mk(a)
    if o is None:
        return None
    if not is_trade():
        if o.symbol[:2] in ('11', '12'):
            info = 'CB'
        else:
            info = 'STK'
        LOG.info(info)
    return o.order_id
'''
S2 = r'''
def f(a):
    o = mk(a)
    if not is_trade():
        if o.symbol[:2] in ('11', '12'):
            info = 'CB'
        else:
            info = 'STK'
        LOG.info(info)
    return o.order_id
'''
S3 = r'''
def f(a):
    o = mk(a)
    if o is None:
        return None
    if not is_trade():
        side = 'BUY' if o.dir.value.upper() == 'BUY' else 'SELL'
        LOG.info('order {0} {1}'.format(o.order_id, side))
    return o.order_id
'''
S4 = r'''
def f(a):
    o = mk(a)
    if o is None:
        return None
    if not is_trade():
        LOG.info('x')
    return o.order_id
'''
S5 = r'''
class C:
    def m(self, a):
        o = mk(a)
        if o is None:
            return None
        if not is_trade():
            if o.symbol[:2] in ('11', '12'):
                info = 'CB'
            else:
                info = 'STK'
            LOG.info(info)
        return o.order_id
'''
S6 = r'''
for a in SEQ:
    o = mk(a)
    if o is None:
        continue
    if not is_trade():
        if o.symbol[:2] in ('11', '12'):
            info = 'CB'
        else:
            info = 'STK'
        LOG.info(info)
    LOG.info(o.order_id)
'''
S7 = r'''
def f(a):
    try:
        o = mk(a)
        if o is None:
            return None
        if not is_trade():
            if o.symbol[:2] in ('11', '12'):
                info = 'CB'
            else:
                info = 'STK'
            LOG.info(info)
        return o.order_id
    except ValueError:
        return None
'''
S8 = r'''
def f(a):
    with LOCK as lk:
        o = mk(a)
        if o is None:
            return None
        if not is_trade():
            if o.symbol[:2] in ('11', '12'):
                info = 'CB'
            else:
                info = 'STK'
            LOG.info(info)
        return o.order_id
'''
S9 = r'''
def f(a):
    o = mk(a)
    if o is None:
        return None
    elif not is_trade():
        if o.symbol[:2] in ('11', '12'):
            info = 'CB'
        else:
            info = 'STK'
        LOG.info(info)
    return o.order_id
'''
S10 = r'''
def f(a):
    o = mk(a)
    if o is None:
        return None
    if is_trade():
        if o.symbol[:2] in ('11', '12'):
            info = 'CB'
        else:
            info = 'STK'
        LOG.info(info)
    return o.order_id
'''
S11 = r'''
def f(a):
    o = mk(a)
    if o is None:
        return None
    if not is_trade():
        if o.symbol[:2] in ('11', '12'):
            info = 'CB'
        else:
            info = 'STK'
    LOG.info(info)
    return o.order_id
'''
S12 = r'''
def f(a):
    o = mk(a)
    if o.is_bad():
        return None
    if not is_trade():
        if o.symbol[:2] in ('11', '12'):
            info = 'CB'
        else:
            info = 'STK'
        LOG.info(info)
    return o.order_id
'''
S13 = r'''
def f(a):
    o = mk(a)
    if o is None:
        return None
    if not is_trade():
        if o.symbol[:2] in ('11', '12'):
            info = 'CB'
        else:
            info = 'STK'
        LOG.info(info)
        return o.order_id
    return None
'''
S14 = r'''
def f(a):
    o = mk(a)
    if o is None:
        return None
    if not is_trade():
        if o.symbol[:2] in ('11', '12'):
            info = 'CB'
        elif o.symbol[:2] in ('13',):
            info = 'CB2'
        else:
            info = 'STK'
        LOG.info(info)
    return o.order_id
'''
S15 = r'''
def f(a):
    o = mk(a)
    if o is None:
        return None
    if not is_trade():
        if o.symbol[:2] in ('11', '12'):
            info = 'CB'
        else:
            info = 'STK'
        LOG.info(info)
    o.used = True
    return o.order_id
'''

ARMS = {
    'r3_a01_terminal_return_join_absorbed': S1,
    'r3_a02_no_preceding_guard_return': S2,
    'r3_a03_ternary_and_format_future_shape': S3,
    'r3_a04_body_single_stmt': S4,
    'r3_a05_method_host': S5,
    'r3_a06_for_host_module_level': S6,
    'r3_a07_try_host': S7,
    'r3_a08_with_host': S8,
    'r3_a09_explicit_elif_source': S9,
    'r3_a10_positive_polarity': S10,
    'r3_a11_inner_if_no_else': S11,
    'r3_a12_guard_is_call_not_isnone': S12,
    'r3_a13_body_ends_terminal_return': S13,
    'r3_a14_three_arm_inner_chain': S14,
    'r3_a15_sibling_after_negated_if': S15,
}


def build(names):
    for n in names:
        p = D / (n + '.py')
        p.write_text(ARMS[n].lstrip('\n'), encoding='utf-8')
        py_compile.compile(str(p), cfile=str(D / (n + '.pyc')), doraise=True, quiet=1)


def decompile(names):
    for n in names:
        ok = D / (n + 'OK.py')
        if ok.exists():
            ok.unlink()
        r = subprocess.run([sys.executable, '-X', 'utf8', 'pycdc.py', '-o', str(ok),
                            str(D / (n + '.pyc'))], cwd=ROOT, capture_output=True, text=True)
        if r.returncode != 0:
            print('DECOMPILE_FAIL', n, r.stderr[-300:])


def write_index(names):
    f = D / 'r3_probe_index.json'
    seen = []
    if f.exists():
        seen = [e['path'] for e in json.loads(f.read_text(encoding='utf-8'))]
    new = [f'test_repros/round3/{n}.pyc' for n in names]
    merged = sorted(set(seen) | set(new))
    f.write_text(json.dumps([{'path': p} for p in merged], indent=2), encoding='utf-8')
    return merged


if __name__ == '__main__':
    names = sys.argv[1:] or sorted(ARMS)
    build(names)
    decompile(names)
    write_index(names)
    print('built', len(names), 'arms')
