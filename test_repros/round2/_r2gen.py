"""Round-2 specimen generator + battery runner (test-side only).

For each specimen: write <name>.py -> py_compile to <name>.pyc -> pycdc.py -o <name>OK.py
-> judge with scripts/pyc_verify.py single (the ONLY judge).

Usage:
  python -X utf8 test_repros/round2/_r2gen.py write        # only emit .py files
  python -X utf8 test_repros/round2/_r2gen.py run a        # build+judge family a, write index
  python -X utf8 test_repros/round2/_r2gen.py index        # (re)write r2v3_probe_index.json only
"""
import json
import os
import py_compile
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
PY = sys.executable

HEAD = '# round-2 r2v3 specimen (synthetic, minimal)\n'
LOGIC = '    n = 0\n'

# ---------------------------------------------------------------- family A
# mirrors real_quote.get_tick_direction : if/elif chain whose join block is a
# TERMINAL `return v` block with several preds, followed by sibling statements.
A = {
    'r2v3_a01_chain_join_terminal_return': HEAD + """def f(flag, redata, sym):
    if flag == 1:
        log('a')
    elif flag == -1:
        log('b')
    return redata
    if redata:
        return sym
""",
    'r2v3_a02_chain_no_code_after_join': HEAD + """def f(flag, redata):
    if flag == 1:
        log('a')
    elif flag == -1:
        log('b')
    return redata
""",
    'r2v3_a03_chain_join_plain_stmt': HEAD + """def f(flag, redata):
    if flag == 1:
        log('a')
    elif flag == -1:
        log('b')
    redata = clean(redata)
    if redata:
        return redata
    return None
""",
    'r2v3_a04_chain_join_return_with_else': HEAD + """def f(flag, redata, sym):
    if flag == 1:
        log('a')
    elif flag == -1:
        log('b')
    else:
        log('c')
    return redata
    if sym:
        return sym
""",
    'r2v3_a05_chain_two_arms_join_return': HEAD + """def f(flag, redata, sym):
    if flag == 1:
        log('a')
    elif flag == 2:
        log('b')
    return redata
    use(sym)
""",
    'r2v3_a06_method_host_chain_join_return': HEAD + """class C:
    def m(self, flag, redata, sym):
        if flag == 1:
            log('a')
        elif flag == -1:
            log('b')
        return redata
        if sym:
            return sym
""",
    'r2v3_a07_inside_while_chain_join_return': HEAD + """def f(q, stop):
    while not stop:
        flag = q.poll()
        if flag == 1:
            log('a')
        elif flag == -1:
            log('b')
        return q
        log('after')
""",
    'r2v3_a08_inside_try_chain_join_return': HEAD + """def f(flag, redata):
    try:
        if flag == 1:
            log('a')
        elif flag == -1:
            log('b')
        return redata
        log('after')
    except ValueError:
        return None
""",
    'r2v3_a09_kline_or_isnone_join': HEAD + """def f(kline, fq, ex_info):
    if fq is None or ex_info is None:
        return kline
    names = list(ex_info)
    build(names, kline)
    return kline
""",
    'r2v3_a10_kline_nested_control': HEAD + """def f(kline, fq, ex_info):
    if fq is None:
        return kline
    if ex_info is None:
        return kline
    names = list(ex_info)
    build(names, kline)
    return kline
""",
    'r2v3_a11_kline_or_both_notnone': HEAD + """def f(kline, fq, ex_info):
    if fq is not None and ex_info is not None:
        names = list(ex_info)
        build(names, kline)
    return kline
""",
    'r2v3_a12_module_host_chain_join_return': HEAD + """flag = poll()
redata = get()
if flag == 1:
    log('a')
elif flag == -1:
    log('b')
return_if_true(redata)
log('after')
""",
}

# ---------------------------------------------------------------- family B
# mirrors plugin_system_risk_calculation._on_publish_after_trading_end
# (`while True:` with break + tail sibling dropped) and _save_testds_to_csv
# (`except X: continue` degraded, loop tail sibling dropped, while-else invented).
B = {
    'r2v3_b01_whiletrue_break_tail_in_if': HEAD + """def f(is_end, TH):
    if is_end:
        while True:
            from mod import THREAD_STATUS
            if THREAD_STATUS:
                break
            time.sleep(0.01)
    event_bus = get_bus()
    event_bus.publish()
""",
    'r2v3_b02_whiletrue_break_no_tail': HEAD + """def f(is_end, TH):
    if is_end:
        while True:
            if TH:
                break
    event_bus = get_bus()
    event_bus.publish()
""",
    'r2v3_b03_whilecond_break_tail_in_if': HEAD + """def f(is_end, TH, stop):
    if is_end:
        while not stop:
            if TH:
                break
            time.sleep(0.01)
    event_bus = get_bus()
    event_bus.publish()
""",
    'r2v3_b04_whiletrue_break_tail_toplevel': HEAD + """def f(TH):
    while True:
        if TH:
            break
        time.sleep(0.01)
    event_bus = get_bus()
""",
    'r2v3_b05_whiletrue_return_tail_in_if': HEAD + """def f(is_end, TH):
    if is_end:
        while True:
            if TH:
                return 1
            time.sleep(0.01)
    event_bus = get_bus()
""",
    'r2v3_b06_except_continue_in_while': HEAD + """def f(q, stop, w):
    while not stop:
        try:
            is_end, daily = q.get(timeout=1)
        except ValueError:
            continue
        w(is_end, daily)
        if is_end:
            break
    while not stop:
        if stop.flag:
            return None
        time.sleep(0.01)
""",
    'r2v3_b07_except_continue_nothing_after_try': HEAD + """def f(q, stop):
    while not stop:
        try:
            is_end, daily = q.get(timeout=1)
        except ValueError:
            continue
        w(daily)
""",
    'r2v3_b08_except_pass_then_stmts': HEAD + """def f(q, stop, w):
    while not stop:
        try:
            is_end, daily = q.get(timeout=1)
        except ValueError:
            pass
        w(is_end, daily)
        if is_end:
            break
""",
    'r2v3_b09_except_continue_method_host': HEAD + """class C:
    def m(self, q, stop, w):
        while not stop:
            try:
                is_end, daily = q.get(timeout=1)
            except ValueError:
                continue
            w(is_end, daily)
            if is_end:
                break
        return None
""",
    'r2v3_b10_except_continue_in_try_finally': HEAD + """def f(q, stop, w):
    while not stop:
        try:
            try:
                is_end, daily = q.get(timeout=1)
            except ValueError:
                continue
            w(is_end, daily)
        finally:
            log('fin')
""",
    'r2v3_b11_except_continue_inside_with': HEAD + """def f(q, stop, w, fp):
    while not stop:
        with fp:
            try:
                is_end, daily = q.get(timeout=1)
            except ValueError:
                continue
            w(is_end, daily)
""",
    'r2v3_b12_whiletail_return_after_if_arm': HEAD + """def f(stop, TH):
    while not stop:
        from mod import THREAD_STATUS
        if THREAD_STATUS:
            return None
        time.sleep(0.01)
    return None
""",
    'r2v3_b13_except_break_in_while': HEAD + """def f(q, stop, w):
    while not stop:
        try:
            is_end, daily = q.get(timeout=1)
        except ValueError:
            break
        w(is_end, daily)
    return None
""",
}

# ---------------------------------------------------------------- family C
# mirrors future_contract_info.info_conbine / check_user : boolop operand
# polarity reassociation (orig `A or not B` / `A or B` -> product `not (A or B)`
# / nested positive ifs).
C = {
    'r2v3_c01_or_not_operand_elifchain': HEAD + """def f(username, future_code, finfo, uinfo):
    if future_code not in finfo:
        raise Exception('no code')
    elif username not in uinfo or not uinfo[username]:
        raise Exception('no user')
    elif future_code not in uinfo[username]:
        raise Exception('no perm')
    out = finfo[future_code].copy()
    out.update(uinfo[username][future_code])
    return out
""",
    'r2v3_c02_or_not_operand_plain': HEAD + """def f(username, uinfo):
    if username not in uinfo or not uinfo[username]:
        raise Exception('no user')
    return 1
""",
    'r2v3_c03_control_single_operand': HEAD + """def f(username, uinfo):
    if username not in uinfo:
        raise Exception('no user')
    return 1
""",
    'r2v3_c04_control_explicit_not_or': HEAD + """def f(username, uinfo):
    if not (username not in uinfo or uinfo[username]):
        raise Exception('no user')
    return 1
""",
    'r2v3_c05_control_and_form': HEAD + """def f(username, uinfo):
    if username in uinfo and not uinfo[username]:
        raise Exception('no user')
    return 1
""",
    'r2v3_c06_keys_call_second_operand': HEAD + """def f(username, uinfo, acct):
    n = 0
    if username not in uinfo.keys() or not uinfo[username]:
        acct.lock.acquire()
        try:
            for m in JOBS:
                n = n + 1
                if n is None:
                    return 2
            return 1
        except BaseException:
            acct.lock.release()
            return 2
        finally:
            acct.lock.release()
    else:
        return 0
""",
    'r2v3_c07_or_isnone_two_operands': HEAD + """def f(a, b, c):
    if a is None or b is None:
        return c
    log('after')
    return c
""",
    'r2v3_c08_or_not_compare_operand': HEAD + """def f(x, y, out):
    if x != 1 or not y:
        raise Exception('bad')
    return out
""",
    'r2v3_c09_method_host_or_not_operand': HEAD + """class C:
    def m(self, username, uinfo):
        if username not in uinfo or not uinfo[username]:
            raise Exception('no user')
        return 1
""",
    'r2v3_c10_inside_try_or_not_operand': HEAD + """def f(username, uinfo):
    try:
        if username not in uinfo or not uinfo[username]:
            raise Exception('no user')
    except Exception as e:
        log(e)
    return 1
""",
    'r2v3_c11_inside_while_or_not_operand': HEAD + """def f(q, uinfo):
    while q:
        username = q.pop()
        if username not in uinfo or not uinfo[username]:
            continue
        use(username)
""",
    'r2v3_c12_or_three_operands': HEAD + """def f(a, b, c, out):
    if a not in b or not b[a] or c is None:
        raise Exception('bad')
    return out
""",
    'r2v3_c13_and_not_operand_control': HEAD + """def f(username, uinfo):
    if username in uinfo and uinfo[username]:
        return 1
    raise Exception('no user')
""",
}

# ---------------------------------------------------------------- family A2
# corrected host for the get_tick_direction / get_real_minute_kline shape:
# the if/elif chain's join block is a TERMINAL (`return v`) block that sits at the
# end of a loop body, and the enclosing loop's `break` target lies AFTER it.
A2 = {
    'r2v3_a13_loop_break_chain_join_return': HEAD + """def f(flag, redata, n):
    for i in n:
        if i:
            break
        if flag == 1:
            log('a')
        elif flag == -1:
            log('b')
        return redata
    if redata:
        log('x')
""",
    'r2v3_a14_control_join_plain_stmt': HEAD + """def f(flag, redata, n):
    for i in n:
        if i:
            break
        if flag == 1:
            log('a')
        elif flag == -1:
            log('b')
        redata = clean(redata)
    if redata:
        log('x')
""",
    'r2v3_a15_control_no_break_in_loop': HEAD + """def f(flag, redata, n):
    for i in n:
        if flag == 1:
            log('a')
        elif flag == -1:
            log('b')
        return redata
    if redata:
        log('x')
""",
    'r2v3_a16_while_host_break_chain_join': HEAD + """def f(flag, redata, stop):
    while not stop:
        if stop.x:
            break
        if flag == 1:
            log('a')
        elif flag == -1:
            log('b')
        return redata
    if redata:
        log('x')
""",
    'r2v3_a17_ifelse_arms_break_chain_join': HEAD + """def f(flag, redata, n):
    for i in n:
        if i:
            break
        if flag == 1:
            log('a')
        else:
            log('b')
        return redata
    if redata:
        log('x')
""",
    'r2v3_a18_control_nothing_after_loop': HEAD + """def f(flag, redata, n):
    for i in n:
        if i:
            break
        if flag == 1:
            log('a')
        elif flag == -1:
            log('b')
        return redata
""",
    'r2v3_a19_or_isnone_join_in_loop_break': HEAD + """def f(a, b, redata, n):
    for i in n:
        if i:
            break
        if a is None or b is None:
            return redata
        use(a, b)
    if redata:
        log('x')
""",
    'r2v3_a20_or_isnone_inside_try': HEAD + """def f(a, b, c):
    try:
        if a is None or b is None:
            return c
        use(a)
    except ValueError:
        log('e')
    return c
""",
    'r2v3_a21_or_isnone_nested_in_elsearm': HEAD + """def f(k, fq, ex, side):
    if side:
        k = prep(k)
    else:
        k = prep2(k)
    if fq is None or ex is None:
        return k
    names = list(ex)
    build(names, k)
    return k
""",
    'r2v3_a22_method_host_break_chain_join': HEAD + """class C:
    def m(self, flag, redata, n):
        for i in n:
            if i:
                break
            if flag == 1:
                log('a')
            elif flag == -1:
                log('b')
            return redata
        if redata:
            log('x')
""",
    'r2v3_a23_postloop_sibling_is_return': HEAD + """def f(flag, redata, n):
    for i in n:
        if i:
            break
        if flag == 1:
            log('a')
        elif flag == -1:
            log('b')
        return redata
    return None
""",
    'r2v3_a24_module_host_raise_join': HEAD + """flag = 1
for i in range(3):
    if i:
        break
    if flag == 1:
        log('a')
    elif flag == -1:
        log('b')
    raise SystemExit
log('after')
""",
}

# ---------------------------------------------------------------- family B2
B2 = {
    'r2v3_b14_whiletail_return_no_tailstmt': HEAD + """def f(stop, TH):
    while not stop:
        if TH:
            return None
    return None
""",
    'r2v3_b15_whiletail_break_after_if_arm': HEAD + """def f(stop, TH):
    while not stop:
        from mod import THREAD_STATUS
        if THREAD_STATUS:
            break
        time.sleep(0.01)
    return None
""",
    'r2v3_b16_whiletrue_break_tail_inside_try': HEAD + """def f(is_end, TH):
    try:
        while True:
            if TH:
                break
            time.sleep(0.01)
    except ValueError:
        log('e')
    event_bus = get_bus()
""",
    'r2v3_b17_whiletrue_break_tail_inside_for': HEAD + """def f(items, TH):
    for it in items:
        while True:
            if TH:
                break
            time.sleep(0.01)
    event_bus = get_bus()
""",
    'r2v3_b18_except_continue_try_else': HEAD + """def f(q, stop, w):
    while not stop:
        try:
            is_end, daily = q.get(timeout=1)
        except ValueError:
            continue
        else:
            w(daily)
        if is_end:
            break
    return None
""",
    'r2v3_b19_except_continue_nested_while': HEAD + """def f(q, stop, w):
    while not stop:
        while q:
            try:
                is_end, daily = q.get(timeout=1)
            except ValueError:
                continue
            w(is_end, daily)
        log('outer')
""",
}

FAM = {'a': A, 'a2': A2, 'b': B, 'b2': B2, 'c': C}


def write_all():
    for fam in FAM:
        for name, src in FAM[fam].items():
            with open(os.path.join(HERE, name + '.py'), 'w', encoding='utf-8') as f:
                f.write(src)
    print('written', sum(len(v) for v in FAM.values()), 'specimens')


def run(cmd, timeout=270):
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=timeout)
    return (p.stdout or '') + (p.stderr or '')


def one(name):
    base = os.path.join(HERE, name)
    try:
        py_compile.compile(base + '.py', base + '.pyc', doraise=True)
    except Exception as exc:  # noqa: BLE001
        print(f'{name:<40} COMPILE_FAIL {exc}')
        return None
    out = run([PY, '-X', 'utf8', 'pycdc.py', '-o', base + 'OK.py', base + '.pyc'])
    if not os.path.isfile(base + 'OK.py'):
        print(f'{name:<40} DECOMPILE_FAIL {out[-200:]}')
        return None
    txt = run([PY, '-X', 'utf8', 'scripts/pyc_verify.py', 'single', base + '.pyc'])
    verdict = 'MISMATCH' if 'status=failure' in txt else ('MATCH' if 'status=success' in txt else 'ERROR')
    units = [ln for ln in txt.splitlines() if 'status=' in ln]
    fail = [ln.strip() for ln in txt.splitlines() if ln.strip().startswith('***')]
    print(f'{name:<40} {verdict:<9} {(units[0].split("]")[-1].strip() if units else ""):<26} '
          + ' ; '.join(f[:78] for f in fail[:2]))
    return verdict


def index():
    entries = []
    for fam in FAM:
        for name in FAM[fam]:
            entries.append({'path': f'test_repros/round2/{name}.pyc'})
    p = os.path.join(HERE, 'r2v3_probe_index.json')
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(entries, f, indent=1)
    print('index written', p, len(entries), 'arms')


if __name__ == '__main__':
    what = sys.argv[1] if len(sys.argv) > 1 else 'write'
    if what == 'write':
        write_all()
    elif what == 'index':
        index()
    else:
        fam = sys.argv[2] if len(sys.argv) > 2 else what
        write_all()
        res = {}
        for name in FAM[fam]:
            res[name] = one(name)
        print(f'family {fam}: MISMATCH={sum(1 for v in res.values() if v == "MISMATCH")} '
              f'MATCH={sum(1 for v in res.values() if v == "MATCH")} '
              f'ERROR={sum(1 for v in res.values() if v not in ("MATCH", "MISMATCH"))}')
