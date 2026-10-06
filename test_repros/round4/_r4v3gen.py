"""Round-4 specimen generator + three-step battery (test-side only, no production edits).

Pipeline per arm: write .py -> py_compile .pyc -> pycdc.py -o <base>OK.py -> judge batch.
Never hand-edits a decompiled product. Judge remains scripts/pyc_verify.py.
Usage: python -X utf8 test_repros/round4/_r4v3gen.py [<arm> ...]   (no args = all)
"""
import json
import pathlib
import py_compile
import subprocess
import sys

ROOT = pathlib.Path(r'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main')
D = ROOT / 'test_repros' / 'round4'

# ============ A 组：if/elif 链的「臂出口 / 成员真边 -> 区域汇合块」身份族 ============
# 语料原形 = Strategy.tick_worker_thread（#3）/ DefaultMatcher.match（#6）/ get_history_df（#8）
A_CHAIN = '''
def f(dt_strf):
    while True:
        try:
            if 'x' in ACCTS:
                if is_ft(dt_strf):
                    Q.put(dt_strf)
                    sleep(3)
                elif not (dt_strf > '15:15:00' or dt_strf < '08:30:00'):
                    if '11:30:00' < dt_strf < '12:30:00':
                        sleep(60)
                    elif '08:30:00' <= dt_strf < '08:59:00' or '12:30:00' <= dt_strf < '12:59:00':
                        sleep(60)
                    elif '08:59:00' <= dt_strf < '09:00:00' or '12:59:00' <= dt_strf < '13:00:00':
                        sleep(1)
        except Exception:
            LOG.error('boom')
            return None
'''

A_NOTRY = '''
def f(dt_strf):
    while True:
        if 'x' in ACCTS:
            if is_ft(dt_strf):
                Q.put(dt_strf)
                sleep(3)
            elif not (dt_strf > '15:15:00' or dt_strf < '08:30:00'):
                if '11:30:00' < dt_strf < '12:30:00':
                    sleep(60)
                elif '08:30:00' <= dt_strf < '08:59:00' or '12:30:00' <= dt_strf < '12:59:00':
                    sleep(60)
                elif '08:59:00' <= dt_strf < '09:00:00' or '12:59:00' <= dt_strf < '13:00:00':
                    sleep(1)
'''

A_NOLOOP = '''
def f(dt_strf):
    if 'x' in ACCTS:
        if is_ft(dt_strf):
            Q.put(dt_strf)
            sleep(3)
        elif not (dt_strf > '15:15:00' or dt_strf < '08:30:00'):
            if '11:30:00' < dt_strf < '12:30:00':
                sleep(60)
            elif '08:30:00' <= dt_strf < '08:59:00' or '12:30:00' <= dt_strf < '12:59:00':
                sleep(60)
            elif '08:59:00' <= dt_strf < '09:00:00' or '12:59:00' <= dt_strf < '13:00:00':
                sleep(1)
'''

A_MODULE = '''
if 'x' in ACCTS:
    if is_ft(DT):
        Q.put(DT)
        sleep(3)
    elif not (DT > '15:15:00' or DT < '08:30:00'):
        if '11:30:00' < DT < '12:30:00':
            sleep(60)
        elif '08:30:00' <= DT < '08:59:00' or '12:30:00' <= DT < '12:59:00':
            sleep(60)
        elif '08:59:00' <= DT < '09:00:00' or '12:59:00' <= DT < '13:00:00':
            sleep(1)
'''

A_FORHOST = '''
def f(rows):
    for dt_strf in rows:
        if 'x' in ACCTS:
            if is_ft(dt_strf):
                Q.put(dt_strf)
                sleep(3)
            elif not (dt_strf > '15:15:00' or dt_strf < '08:30:00'):
                if '11:30:00' < dt_strf < '12:30:00':
                    sleep(60)
                elif '08:30:00' <= dt_strf < '08:59:00' or '12:30:00' <= dt_strf < '12:59:00':
                    sleep(60)
                elif '08:59:00' <= dt_strf < '09:00:00' or '12:59:00' <= dt_strf < '13:00:00':
                    sleep(1)
'''

# 对照：a05 = a02 删掉第三个 elif 臂（唯一改动）
A_TWO_ARM = '''
def f(dt_strf):
    while True:
        if 'x' in ACCTS:
            if is_ft(dt_strf):
                Q.put(dt_strf)
                sleep(3)
            elif not (dt_strf > '15:15:00' or dt_strf < '08:30:00'):
                if '11:30:00' < dt_strf < '12:30:00':
                    sleep(60)
                elif '08:30:00' <= dt_strf < '08:59:00' or '12:30:00' <= dt_strf < '12:59:00':
                    sleep(60)
'''

# 对照：a06 = a02 把每条臂条件里的 `or` 拆掉（只剩单个连环比较）
A_NO_OR = '''
def f(dt_strf):
    while True:
        if 'x' in ACCTS:
            if is_ft(dt_strf):
                Q.put(dt_strf)
                sleep(3)
            elif not (dt_strf > '15:15:00' or dt_strf < '08:30:00'):
                if '11:30:00' < dt_strf < '12:30:00':
                    sleep(60)
                elif '08:30:00' <= dt_strf < '08:59:00':
                    sleep(60)
                elif '08:59:00' <= dt_strf < '09:00:00':
                    sleep(1)
'''

# 对照：a07 = a02 把内层链的臂体换成不同语句（臂体不再是同形 call）
A_DIFF_BODY = '''
def f(dt_strf):
    while True:
        if 'x' in ACCTS:
            if is_ft(dt_strf):
                Q.put(dt_strf)
                sleep(3)
            elif not (dt_strf > '15:15:00' or dt_strf < '08:30:00'):
                if '11:30:00' < dt_strf < '12:30:00':
                    A = 1
                elif '08:30:00' <= dt_strf < '08:59:00' or '12:30:00' <= dt_strf < '12:59:00':
                    B = 2
                elif '08:59:00' <= dt_strf < '09:00:00' or '12:59:00' <= dt_strf < '13:00:00':
                    C = 3
'''

# 对照：a08 = a02 把内层 if/elif 链换成 if / else（无 elif 链）
A_ELSE_ONLY = '''
def f(dt_strf):
    while True:
        if 'x' in ACCTS:
            if is_ft(dt_strf):
                Q.put(dt_strf)
                sleep(3)
            elif not (dt_strf > '15:15:00' or dt_strf < '08:30:00'):
                if '11:30:00' < dt_strf < '12:30:00':
                    sleep(60)
                else:
                    sleep(1)
'''

# #8 get_history_df 原形：外层 `if A == B and C > D:` + 内层 if/elif（and 成员 + 比较成员）
A_AND_OUTER = '''
def f(symbol, count, qd, freq, inc):
    nd = int(ts())
    q1 = qd // 100
    if q1 == int(nd) and q1 > 930:
        if freq == 1 and inc:
            rd = get_daily(symbol)
        elif q1 <= 1130 and q1 >= 1000:
            rd = get_min(symbol)
        elif q1 >= 1300 or q1 <= 1500:
            rd = get_tick(symbol)
        else:
            rd = None
        return rd
    return get_history_df(symbol, count, qd, freq)
'''

# #5 finance.get_fields / B100 原形：try 体内 if 链的臂出口外推到函数尾
A_TRY_IF_TAIL = '''
def f(d):
    try:
        if d.kind == 1:
            out = build(d.a)
        elif d.kind == 2:
            out = build(d.b)
        else:
            out = None
        return out
    except Exception:
        LOG.error('x')
        return None
'''

A_TRY_IF_TAIL_FLAT = '''
def f(d):
    try:
        if d.kind == 1:
            out = build(d.a)
        elif d.kind == 2:
            out = build(d.b)
        out = post(out)
        return out
    except Exception:
        LOG.error('x')
        return None
'''

# ============ B 组：隐式 return None 双 sink 归并族（B99 / 新 B116） ============
# #4 trading_dates_reload 原形（已用候选源逐指令核对：ORIG == `if A: if not B: body`）
B_NESTED_NOT = '''
class M:
    def reload(self):
        if self.pre_flag:
            if not self.upd_flag:
                self._dates = self.engine.cal.get()
                self.upd_flag = True
'''

B_NESTED_NOT_SIB = '''
class M:
    def reload(self):
        if self.pre_flag:
            if not self.upd_flag:
                self._dates = self.engine.cal.get()
                self.upd_flag = True
        self.hit_count += 1
'''

B_FLAT_AND = '''
class M:
    def reload(self):
        if self.pre_flag and not self.upd_flag:
            self._dates = self.engine.cal.get()
            self.upd_flag = True
'''

B_SINGLE_IF = '''
class M:
    def reload(self):
        if not self.upd_flag:
            self._dates = self.engine.cal.get()
            self.upd_flag = True
'''

B_FUNC_HOST = '''
def reload(pre, upd):
    if pre:
        if not upd:
            reset()
            set_flag()
'''

B_MODULE_HOST = '''
if pre_flag:
    if not upd_flag:
        reset()
        set_flag()
'''

B_POS_POLARITY = '''
class M:
    def reload(self):
        if self.pre_flag:
            if self.upd_flag:
                self._dates = self.engine.cal.get()
                self.upd_flag = True
'''

B_THREE_NEST = '''
class M:
    def reload(self):
        if self.a_flag:
            if self.b_flag:
                if not self.c_flag:
                    self._dates = self.engine.cal.get()
                    self.upd_flag = True
'''

# #1 handlers._target 原形（B99）：if 臂内 while + try/except/else + 尾随隐式 return None
B99_WHILE_TRY_SINK = '''
class TWH:
    def _target(self):
        if self.sys_ver > 3:
            while self.running:
                try:
                    self.tick()
                except Exception:
                    LOG.error('boom')
                else:
                    self.ok += 1
'''

B99_WHILE_TRY_SINK_FNEND = '''
class TWH:
    def _target(self):
        while self.running:
            try:
                self.tick()
            except Exception:
                LOG.error('boom')
            else:
                self.ok += 1
'''

B_NESTED_NOT_LOOP = '''
def f(running, pre, upd):
    if pre:
        while running:
            if not upd:
                reset()
'''

# ============ C 组：终态 return 与凭空 None 尾 sink 族（B111 / #7） ============
C_ALL_RET_EXPR = '''
def f(s):
    d = mk_frame()
    parts = s.split('.')
    if len(parts) != 2:
        return d
    code = parts[0]
    if parts[1] == 'SS':
        dir_ = 'XSHG'
    elif parts[1] == 'SZ':
        dir_ = 'XSHE'
    else:
        return d
    rows = read_csv(dir_, code)
    return rows
'''

C_ALL_RET_EXPR_CTRL = '''
def f(s):
    d = mk_frame()
    parts = s.split('.')
    if len(parts) != 2:
        return d
    code = parts[0]
    if parts[1] == 'SS':
        dir_ = 'XSHG'
    elif parts[1] == 'SZ':
        dir_ = 'XSHE'
    else:
        return d
    rows = read_csv(dir_, code)
    return rows
    return d
'''

C_LOOP_TAIL = '''
def f(symbols, mk):
    res = mk(0)
    for s in symbols:
        if s:
            res = mk(s)
            break
    else:
        res = mk(-1)
    return res
'''

C_LOOP_TAIL_CTRL = '''
def f(symbols, mk):
    res = mk(0)
    for s in symbols:
        if s:
            res = mk(s)
    return res
'''

C_EARLY_RETURN_CHAIN = '''
def f(d, kind):
    if kind == 1:
        return d
    elif kind == 2:
        d = prep(d)
    else:
        return d
    return d
'''

# a13 = a02 去掉外层 `if 'x' in ACCTS:` 守卫（只剩循环 + 内层链）——隔离「臂」这一维
A13_NO_OUTER_GUARD = '''
def f(dt_strf):
    while True:
        if is_ft(dt_strf):
            Q.put(dt_strf)
            sleep(3)
        elif not (dt_strf > '15:15:00' or dt_strf < '08:30:00'):
            if '11:30:00' < dt_strf < '12:30:00':
                sleep(60)
            elif '08:30:00' <= dt_strf < '08:59:00' or '12:30:00' <= dt_strf < '12:59:00':
                sleep(60)
'''

# a14 = a02 只保留外层守卫 + 单个内层 if（最小臂形）
A14_MIN_ARM = '''
def f(dt_strf):
    while True:
        if 'x' in ACCTS:
            if is_ft(dt_strf):
                sleep(3)
'''

# b12 = b06 的同宿主对照（模块级单层 if）
B12_MODULE_SINGLE_IF = '''
if not upd_flag:
    reset()
    set_flag()
'''

ARMS = {
    'r4v3_a01_corpus_tick_elifchain': A_CHAIN,
    'r4v3_a02_while_no_try': A_NOTRY,
    'r4v3_a03_no_loop_host': A_NOLOOP,
    'r4v3_a04_module_host': A_MODULE,
    'r4v3_a05_for_host': A_FORHOST,
    'r4v3_a06_two_arm_control': A_TWO_ARM,
    'r4v3_a07_no_or_control': A_NO_OR,
    'r4v3_a08_diff_body_control': A_DIFF_BODY,
    'r4v3_a09_else_only_control': A_ELSE_ONLY,
    'r4v3_a10_and_outer_member': A_AND_OUTER,
    'r4v3_a11_try_if_tail_b100': A_TRY_IF_TAIL,
    'r4v3_a12_try_if_tail_sibling': A_TRY_IF_TAIL_FLAT,
    'r4v3_a13_no_outer_guard': A13_NO_OUTER_GUARD,
    'r4v3_a14_min_arm': A14_MIN_ARM,
    'r4v3_b01_nested_not_method': B_NESTED_NOT,
    'r4v3_b02_nested_not_sibling': B_NESTED_NOT_SIB,
    'r4v3_b03_flat_and_control': B_FLAT_AND,
    'r4v3_b04_single_if_control': B_SINGLE_IF,
    'r4v3_b05_func_host': B_FUNC_HOST,
    'r4v3_b06_module_host': B_MODULE_HOST,
    'r4v3_b07_positive_polarity': B_POS_POLARITY,
    'r4v3_b08_three_nested': B_THREE_NEST,
    'r4v3_b09_b99_while_try_ifarm': B99_WHILE_TRY_SINK,
    'r4v3_b10_b99_while_try_fnend': B99_WHILE_TRY_SINK_FNEND,
    'r4v3_b11_nested_not_in_loop': B_NESTED_NOT_LOOP,
    'r4v3_b12_module_single_if_control': B12_MODULE_SINGLE_IF,
    'r4v3_c01_all_paths_return_expr': C_ALL_RET_EXPR,
    'r4v3_c02_dead_tail_return_control': C_ALL_RET_EXPR_CTRL,
    'r4v3_c03_loop_else_terminal_return': C_LOOP_TAIL,
    'r4v3_c04_loop_plain_control': C_LOOP_TAIL_CTRL,
    'r4v3_c05_early_return_chain': C_EARLY_RETURN_CHAIN,
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
    f = D / 'r4_probe_index.json'
    new = [f'test_repros/round4/{n}.pyc' for n in names]
    f.write_text(json.dumps([{'path': p} for p in new], indent=2), encoding='utf-8')
    return new


if __name__ == '__main__':
    names = sys.argv[1:] or sorted(ARMS)
    build(names)
    decompile(names)
    write_index(names)
    print('built', len(names), 'arms')
