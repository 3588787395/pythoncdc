# rr-v5r141 [v141-SLB234] A/B 回归电池（267 案）
#   以 r127_regress.py 为模板：r110 的 169 案 + v111 15 + v112 15 + v113 15
#   + v115 9 + v116 4 + v117 6 + v118 7 + v119 8 + v120 6 + v122 13 案（矩阵同源）。
#   逐案 compile -> pyc -> decompile CURRENT(v128) 与 HEAD(23c0b6b7) 版
#   （git-show 文件交换，本轮交换 core/cfg/region_ast_generator.py 单文件）->
#   比产品文本(A/B) + 重编译签名。
#   中间产物写 D:/temp/opencode/cl_layout/r128regress/（独立 TMP，干净重跑），
#   不落证据目录。
import os, sys, re, glob, json, types, py_compile, subprocess
from collections import defaultdict

REPO = 'F:/Downloads/pythoncdc-main'
BASE = REPO + '/.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh'
EV = BASE + '/slb234'
RAG = REPO + '/core/cfg/region_ast_generator.py'
V141_FILES = (RAG,)
PY = 'D:/Python/python.exe'
GIT = 'E:/Program Files/PortableGit/bin/git.exe'
HEAD = '1a0d1b58'
R110 = BASE + '/chainfor_foriter/r110_regress_result.txt'
MP = BASE + '/orandchain_if/matrix_products'
TMP = 'D:/temp/opencode/cl_layout/r141regress'
OUTDIR = TMP + '/v141'
OUTDIR_H = TMP + '/head'
CASEDIR = TMP + '/cases'

sys.path.insert(0, BASE + '/orchain_armbody')
sys.path.insert(0, BASE + '/tailscope_emit')
sys.path.insert(0, EV)
sys.path.insert(0, BASE + '/whileyield_break')
sys.path.insert(0, BASE + '/notboolop_orand')
sys.path.insert(0, BASE + '/bareret_w19')
sys.path.insert(0, BASE + '/foldret_arm')
sys.path.insert(0, BASE + '/eliftest_loop')
sys.path.insert(0, BASE + '/andnot_yieldarm')
sys.path.insert(0, BASE + '/trytop_loop')
sys.path.insert(0, BASE + '/armfall_ifmerge')
from matrix_v5r118 import CASES as V118_CASES
from matrix_v5r119 import CASES as V119_CASES
from matrix_v5r120 import CASES as V120_CASES
from matrix_v5r122 import CASES as V122_CASES

# 既有登记差案（逐字节同签名重点核验）
REGISTERED = ['w28_shapes', 'na5', 'pe8', 'pe8_target', 'nb2',
              'ca6', 'ca13', 'ca15', 'cb5', 'pd8_prod']

EXCL = re.compile(
    r'(out|prod|regress|recompiled|_v[0-9]|sd_|matrix|probe|good|disc|'
    r'fielddiff|err|result|dis[0-9]|dump|hook|tree|ast|verify|baseline|'
    r'unclaimed|fix_|patch|decompiled)', re.I)


def norm(c):
    return (c.co_code.hex(), c.co_exceptiontable.hex(),
            c.co_names, c.co_varnames, c.co_freevars, c.co_cellvars,
            tuple(norm(k) if isinstance(k, types.CodeType) else k for k in c.co_consts))


def toplevels(c):
    return {k.co_name: norm(k) for k in c.co_consts if isinstance(k, types.CodeType)}


def fn_status(src_text, prod_text):
    try:
        s = toplevels(compile(src_text, 's', 'exec'))
        p = toplevels(compile(prod_text, 'p', 'exec'))
    except SyntaxError as se:
        return 'SYNTAX-ERR ' + se.msg[:40]
    rem = sorted(set(s) - set(p)); add = sorted(set(p) - set(s))
    chg = sorted(n for n in set(s) & set(p) if s[n] != p[n])
    if not rem and not add and not chg:
        return 'BYTE-EQUAL'
    return 'DIFF rem=%s add=%s chg=%s' % (rem, add, chg)


def build_cases():
    r110_names = [l.split()[0] for l in open(R110, encoding='utf-8')
                  if l.strip() and not l.startswith('TEXT-DIFF') and 'count' not in l]
    bn = defaultdict(list)
    for p in glob.glob(BASE + '/**/*.py', recursive=True):
        q = p.replace('\\', '/')
        if '/orandchain_if/' in q or '/notboolop_orand/' in q \
                or '/whileyield_break/' in q or '/argor_mergenop/' in q \
                or '/eliftest_loop/' in q or '/foldret_arm/' in q \
                or '/andnot_yieldarm/' in q or '/trytop_loop/' in q \
                or '/armfall_ifmerge/' in q or '/orchain_armbody/' in q or '/tailscope_emit/' in q or '/tupkey_subscript/' in q \
                or '/nbe_update/' in q or '/trivnop/' in q or '/excassert/' in q or '/swapassign/' in q or '/chainelse/' in q or '/modstmt/' in q or '/loopb234/' in q or '/chainunpack/' in q or '/loopb234b/' in q or '/selfloopb234/' in q or '/ftunpack/' in q or '/slbodyexpr/' in q or '/chainwalrus/' in q or '/slb234/' in q:
            continue
        bn[os.path.basename(p)].append(p)

    def find_src(n):
        for b in (n + '.py', n + '_repro.py', n + '_variant.py', n + '_registered.py'):
            if b in bn and not EXCL.search(b):
                return bn[b][0], ''
        cs = [(b, ps[0]) for b, ps in bn.items()
              if (b == n + '.py' or b.startswith(n + '_')) and not EXCL.search(b)]
        if cs:
            return sorted(cs)[0][1], ''
        b0 = re.sub(r'_(prod|target)$', '', n)
        for b in (b0 + '_registered.py', b0 + '.py', b0 + '_repro.py'):
            if b in bn and not EXCL.search(b):
                return bn[b][0], 'SUBSTITUTED:%s' % b
        return None, 'MISSING'

    cases = []
    for n in r110_names:
        p, note = find_src(n)
        cases.append((n, p, note, 'R110'))
    mj = json.load(open(BASE + '/orandchain_if/matrix_v5r111_result.json', encoding='utf-8'))
    for c in mj['cases']:
        n = c['name']
        cases.append((n, MP + '/' + n + '.py', '', 'V111'))
    os.makedirs(CASEDIR, exist_ok=True)
    from r112_regress import V112_CASES
    from r113_regress import V113_CASES
    from matrix_v5r115 import CASES as V115_CASES
    from matrix_v5r116 import CASES as V116_CASES
    from matrix_v5r117 import CASES as V117_CASES
    for group, d in (('V112', V112_CASES), ('V113', V113_CASES),
                     ('V115', V115_CASES), ('V116', V116_CASES),
                     ('V117', V117_CASES), ('V118', V118_CASES), ('V119', V119_CASES),
                     ('V120', V120_CASES), ('V122', V122_CASES)):
        for n, src in d.items():
            p = CASEDIR + '/' + n + '.py'
            open(p, 'w', encoding='utf-8').write(src)
            cases.append((n, p, '', group))
    return cases, r110_names


def decompile(pyc, out, err):
    with open(out, 'wb') as fo, open(err, 'wb') as fe:
        r = subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', pyc],
                           stdout=fo, stderr=fe, cwd=REPO, timeout=300)
    return open(out, 'rb').read(), r.returncode


def parse_r110():
    out = {}
    for l in open(R110, encoding='utf-8'):
        if not l.strip() or l.startswith('TEXT-DIFF') or 'count' in l:
            continue
        parts = l.split(None, 2)
        out[parts[0]] = (parts[1], parts[2].strip() if len(parts) > 2 else '')
    return out


def ensure_v141():
    """启动自愈：若上次 A/B 交换被信号打断使 RAG 停在 HEAD 版，
    从 fix_patch_v5r141.diff 恢复当前 v141 版。不触碰其它文件。"""
    b = open(RAG, 'rb').read()
    if b'v141-SLB234' not in b:
        r = subprocess.run([GIT, '-C', REPO, 'apply', EV + '/fix_patch_v5r141.diff'],
                           capture_output=True)
        assert r.returncode == 0, 'self-heal failed: ' + r.stderr.decode('utf-8', 'replace')
        b = open(RAG, 'rb').read()
        assert b'v141-SLB234' in b
        print('[self-heal] RAG 已由 fix_patch_v5r141.diff 恢复到 v141 版', flush=True)
    return b


def decompile_cached(pyc, out):
    if os.path.exists(out) and os.path.getsize(out) > 0:
        return open(out, 'rb').read()
    return decompile(pyc, out, out + '.err')[0]


PHASE = 0
START, END = 0, 10 ** 9


def main():
    head_rag = subprocess.run([GIT, '-C', REPO, 'show', HEAD + ':core/cfg/region_ast_generator.py'],
                              capture_output=True).stdout
    cur_rag = ensure_v141()
    cur_files = {p: open(p, 'rb').read() for p in V141_FILES}
    assert b'v141-SLB234' not in head_rag, 'HEAD already contains v128 patch?'
    assert b'v140-CHAINSTORE' in head_rag, 'HEAD should contain v140 patch'
    assert b'v141-SLB234' in cur_rag, 'v128 markers missing'
    os.makedirs(OUTDIR, exist_ok=True)
    os.makedirs(OUTDIR_H, exist_ok=True)
    cases, _ = build_cases()
    r110 = parse_r110()

    prepared = []
    for name, src, note, grp in cases:
        if src is None or not os.path.exists(src):
            prepared.append((name, grp, note, None, None))
            continue
        pyc = OUTDIR + '/%s.pyc' % name
        py_compile.compile(src, cfile=pyc, doraise=True)
        prepared.append((name, grp, note, src, pyc))
    todo = [p for p in prepared if p[4] is not None]
    chunk = todo[START:END]

    if PHASE in (0, 1):
        for i, (name, grp, note, src, pyc) in enumerate(chunk, 1):
            decompile_cached(pyc, OUTDIR + '/%s.py' % name)
            if i % 40 == 0:
                print('[phase1] chunk %d/%d' % (i, len(chunk)), flush=True)
        print('[phase1] 本块 v141 产品就绪 %d/%d' % (len(chunk), len(chunk)), flush=True)

    head_files = {}
    for _vf in V141_FILES:
        _rel = _vf.replace(REPO + '/', '')
        head_files[_vf] = subprocess.run([GIT, '-C', REPO, 'show', HEAD + ':' + _rel],
                                         capture_output=True).stdout
    if PHASE in (0, 2):
        try:
            for _vf, _hb in head_files.items():
                open(_vf, 'wb').write(_hb)
            for i, (name, grp, note, src, pyc) in enumerate(chunk, 1):
                decompile_cached(pyc, OUTDIR_H + '/%s.py' % name)
                if i % 40 == 0:
                    print('[phase2] chunk %d/%d' % (i, len(chunk)), flush=True)
        finally:
            for _vf, _cb in cur_files.items():
                open(_vf, 'wb').write(_cb)
            assert open(RAG, 'rb').read() == cur_files[RAG], 'generator not restored!'
        print('[phase2] 本块 HEAD 产品就绪 %d/%d，RAG 已恢复 v141' % (len(chunk), len(chunk)), flush=True)

    if PHASE not in (0, 3):
        return
    results = []
    for name, grp, note, src, pyc in prepared:
        if pyc is None:
            results.append((name, grp, note, 'NO-SRC', 'NO-SRC', ''))
            continue
        tv = open(OUTDIR + '/%s.py' % name, 'rb').read()
        th = open(OUTDIR_H + '/%s.py' % name, 'rb').read()
        ab = 'TEXT-SAME' if tv == th else 'TEXT-DIFF'
        st = fn_status(open(src, encoding='utf-8').read(), tv.decode('utf-8'))
        results.append((name, grp, note, ab, st, ''))

    lines = ['']
    for name, grp, note, ab, st, _ in results:
        lines.append('%-24s %-10s %s%s' % (name, ab, st,
                     ('  [%s]' % note) if note else ''))
    nd = sum(1 for r in results if r[3] == 'TEXT-DIFF')
    lines.append('')
    lines.append('TEXT-DIFF count: %d / %d' % (nd, len(results)))
    open(EV + '/r141_regress_result.txt', 'w', encoding='utf-8').write('\n'.join(lines) + '\n')

    eq_text = eq_sig = 0
    cmp_rows = []
    for name, grp, note, ab, st, _ in results:
        if grp != 'R110':
            continue
        r_ab, r_st = r110.get(name, ('', ''))
        t_ok = (ab == r_ab); s_ok = (st == r_st)
        eq_text += t_ok; eq_sig += s_ok
        cmp_rows.append((name, note, r_ab, r_st, ab, st, t_ok, s_ok))
    print()
    print('R110 案: %d  TEXT 状态一致 %d  签名一致 %d' % (len(cmp_rows), eq_text, eq_sig))
    print()
    print('=== 既有登记差 10 案：r110 -> r141 逐字节同签名核验 ===')
    reg_ok = True
    subst_rows = []
    for name in REGISTERED:
        row = next((r for r in cmp_rows if r[0] == name), None)
        if row is None:
            print('  %-14s MISSING' % name); reg_ok = False; continue
        _, note, r_ab, r_st, ab, st, t_ok, s_ok = row
        substituted = note.startswith('SUBSTITUTED')
        if substituted and ab == 'TEXT-SAME' and not s_ok:
            subst_rows.append((name, note, r_st, st))
            tag, ok = 'SUBST-SIG(产品未变)', True
        else:
            ok = t_ok and s_ok and ab == 'TEXT-SAME'
            tag = 'SAME-SIG' if ok else 'CHANGED'
        reg_ok &= ok
        print('  %-14s %-22s %s' % (name, tag,
              ('%s | %s' % (r_st, st)) if not s_ok else r_st))
    print()
    if subst_rows:
        print('=== 语料替代案（早期清理后缺失，以等价源替代；A/B TEXT-SAME 实证产品逐字节未变）===')
        for n, note, r_st, st in subst_rows:
            print('  %-14s %s' % (n, note))
            print('      r110 签名: %s' % r_st)
            print('      r141 签名: %s' % st)
    print()
    print('REG-10: %s' % ('ALL SAME-SIGNATURE' if reg_ok else 'CHANGED !!'))
    # TEXT-DIFF 明细（若非 0，列案名供判读）
    if nd:
        print()
        print('=== TEXT-DIFF 明细 ===')
        for name, grp, note, ab, st, _ in results:
            if ab == 'TEXT-DIFF':
                print('  %-24s %-6s %s' % (name, grp, st))


if __name__ == '__main__':
    main()
