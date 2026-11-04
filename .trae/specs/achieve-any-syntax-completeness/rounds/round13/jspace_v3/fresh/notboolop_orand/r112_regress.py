# rr-v5r112 [v112-NOTBOOL] A/B 回归电池
#   以 r111_regress.py 为模板：r110 的 169 案名 + v111 的 15 案 + 本轮 15 案
#   = 199 案。逐案 compile -> pyc -> decompile CURRENT(v112) 与
#   HEAD(9139e4c3，已含 v111) 版（git-show 文件交换）-> 比产品文本(A/B)
#   + 重编译签名。中间产物写 D:/temp/opencode/cl_layout/r112regress/，
#   不落证据目录（上轮教训：不要提交 800+ 中间文件）。
import os, sys, re, glob, json, types, py_compile, subprocess
from collections import defaultdict

REPO = 'F:/Downloads/pythoncdc-main'
BASE = REPO + '/.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh'
EV = BASE + '/notboolop_orand'
GEN = REPO + '/core/cfg/region_ast_generator.py'
ANA = REPO + '/core/cfg/region_analyzer.py'
PY = 'D:/Python/python.exe'
GIT = 'E:/Program Files/PortableGit/bin/git.exe'
R110 = BASE + '/chainfor_foriter/r110_regress_result.txt'
MP = BASE + '/orandchain_if/matrix_products'
TMP = 'D:/temp/opencode/cl_layout/r112regress'
OUTDIR = TMP + '/v112'
OUTDIR_H = TMP + '/head'
CASEDIR = TMP + '/cases'

# 用户点名的既有登记差案（逐字节同签名重点核验）
REGISTERED = ['w28_shapes', 'na5', 'pe8', 'pe8_target', 'nb2',
              'ca6', 'ca13', 'ca15', 'cb5', 'pd8_prod']

EXCL = re.compile(
    r'(out|prod|regress|recompiled|_v[0-9]|sd_|matrix|probe|good|disc|'
    r'fielddiff|err|result|dis[0-9]|dump|hook|tree|ast|verify|baseline|'
    r'unclaimed|fix_|patch|decompiled)', re.I)

# 本轮 15 个新案（与 matrix_v5r112.py 同源，逐案内嵌避免对中间目录的依赖）
V112_CASES = {
 'm4_not': "def p(a, b):\n    r = not (a or b)\n    return r\n",
 'm5_hash': "def p(d):\n    ch = d.get('__hash__', None)\n    r = not (ch is None or (ch == 0 and '__eq__' in d))\n    return r\n",
 'm8_getfield': """def gf(cls, a_name, a_type, default_kw_only):
    default = getattr(cls, a_name, MISSING)
    if isinstance(default, Field):
        f = default
    else:
        if isinstance(default, types.MemberDescriptorType):
            default = MISSING
        f = field(default=default)
    f.name = a_name
    f.type = a_type
    f._field_type = _FIELD
    typing = sys.modules.get('typing')
    if typing:
        if _is_classvar(a_type, typing) or (isinstance(f.type, str) and _is_type(f.type, cls, typing, typing.ClassVar, _is_classvar)):
            f._field_type = _FIELD_CLASSVAR
    if f._field_type is _FIELD:
        dataclasses = sys.modules[__name__]
        if _is_initvar(a_type, dataclasses) or (isinstance(f.type, str) and _is_type(f.type, cls, dataclasses, dataclasses.InitVar, _is_initvar)):
            f._field_type = _FIELD_INITVAR
    if f._field_type in (_FIELD_CLASSVAR, _FIELD_INITVAR):
        if f.default_factory is not MISSING:
            raise TypeError('x')
    if f._field_type in (_FIELD, _FIELD_INITVAR):
        if f.kw_only is MISSING:
            f.kw_only = default_kw_only
    if f._field_type is _FIELD and f.default.__class__.__hash__ is None:
        raise ValueError('x')
    return f
""",
 'n8_not_or_and': "def p(a, b, c):\n    r = not (a or (b and c))\n    return r\n",
 'n8_notnot': "def p(a, b):\n    r = not not (a or b)\n    return r\n",
 'n8_loop_or_and': """def p(items, A, B, C, out):
    for t in items:
        tag = 1
        if A(t) or (B(t) and C(t)):
            out.append(t)
            continue
        out.append(0)
    return out
""",
 'm1_or': "def p(a, b, x):\n    if a or b:\n        x = 1\n    return x\n",
 'm2_orand': "def p(a, b, c, x):\n    if a or (b and c):\n        x = 1\n    return x\n",
 'm3_getfield': "def p(t, a, b, c, f):\n    if t:\n        if a or (isinstance(b, str) and c(b)):\n            f.v = 1\n    return f\n",
 'm6_for': "def p(items, A, B):\n    out = []\n    seen = False\n    for name, t in items:\n        if A(t) or (isinstance(t, str) and B(t)):\n            seen = True\n        else:\n            out.append(t)\n    return out, seen\n",
 'm7_twoif': """def p(t, a, b, c, f):
    f.v = 0
    if t:
        if c(a) or (isinstance(b, str) and c(b)):
            f.v = 1
    if f.v in (0, 1):
        if c(a) or (isinstance(b, str) and c(b)):
            f.v = 2
    return f
""",
 'n8_true_nested': "def p(a, b, c, f):\n    if not a:\n        if b and c:\n            f.v = 1\n    return f\n",
 'n8_or_and': "def p(a, b, c, f):\n    if a or (b and c):\n        f.v = 1\n    return f\n",
 'n8_or_and_term': "def p(a, b, c, f):\n    if a or (b and c):\n        raise TypeError('x')\n    return f\n",
 'n8_typing_merge': "def p(t, a, b, c, f):\n    if t:\n        if a or (isinstance(b, str) and c(b)):\n            f.v = 1\n    return f\n",
}


def norm(c):
    # 与 r110/r111 完全一致的口径（保证签名可比）
    return (c.co_code.hex(), c.co_exceptiontable.hex(),
            c.co_names, c.co_varnames, c.co_freevars, c.co_cellvars,
            tuple(norm(k) if isinstance(k, types.CodeType) else k
                  for k in c.co_consts))


def toplevels(c):
    return {k.co_name: norm(k) for k in c.co_consts
            if isinstance(k, types.CodeType)}


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
                  if l.strip() and not l.startswith('TEXT-DIFF')
                  and 'count' not in l]
    bn = defaultdict(list)
    for p in glob.glob(BASE + '/**/*.py', recursive=True):
        q = p.replace('\\', '/')
        # 排除证据目录自身的产品 / 诊断 / 矩阵脚本：不得被误当成 r110 语料。
        if '/orandchain_if/' in q or '/notboolop_orand/' in q:
            continue
        bn[os.path.basename(p)].append(p)

    def find_src(n):
        for b in (n + '.py', n + '_repro.py', n + '_variant.py',
                  n + '_registered.py'):
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
    # v111 的 15 案（沿用 r111 的源语料目录）
    mj = json.load(open(BASE + '/orandchain_if/matrix_v5r111_result.json', encoding='utf-8'))
    for c in mj['cases']:
        n = c['name']
        cases.append((n, MP + '/' + n + '.py', '', 'V111'))
    # 本轮 15 案
    os.makedirs(CASEDIR, exist_ok=True)
    for n, src in V112_CASES.items():
        p = CASEDIR + '/' + n + '.py'
        open(p, 'w', encoding='utf-8').write(src)
        cases.append((n, p, '', 'V112-NEW'))
    return cases, r110_names


def decompile(pyc, out, err, py):
    with open(out, 'wb') as fo, open(err, 'wb') as fe:
        r = subprocess.run([py, '-I', '-X', 'utf8', REPO + '/pycdc.py', pyc],
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


def ensure_v112():
    """启动自愈：若上次 A/B 交换被信号打断而使 GEN 停在 HEAD 版，
    从 fix_patch_v5r112.diff 恢复当前 v112 版。不触碰其它文件。"""
    if 'v112-NOTBOOL' not in open(GEN, encoding='utf-8').read():
        r = subprocess.run([GIT, '-C', REPO, 'apply', EV + '/fix_patch_v5r112.diff'],
                           capture_output=True)
        assert r.returncode == 0, 'self-heal failed: ' + r.stderr.decode('utf-8', 'replace')
        assert 'v112-NOTBOOL' in open(GEN, encoding='utf-8').read()
        print('[self-heal] GEN 已由 fix_patch_v5r112.diff 恢复到 v112 版', flush=True)
    return open(GEN, encoding='utf-8').read()


def decompile_cached(pyc, out):
    if os.path.exists(out) and os.path.getsize(out) > 0:
        return open(out, 'rb').read()
    return decompile(pyc, out, out + '.err', PY)[0]


PHASE = 0
START, END = 0, 10 ** 9


def main():
    head_gen = subprocess.run(
        [GIT, '-C', REPO, 'show', '9139e4c3:core/cfg/region_ast_generator.py'],
        capture_output=True).stdout.decode('utf-8')
    head_ana = subprocess.run(
        [GIT, '-C', REPO, 'show', '9139e4c3:core/cfg/region_analyzer.py'],
        capture_output=True).stdout.decode('utf-8')
    cur_gen = ensure_v112()
    cur_ana = open(ANA, encoding='utf-8').read()
    assert 'v112-NOTBOOL' not in head_gen, 'HEAD already contains v112 patch?'
    assert 'v111-ORAND' in head_gen, 'HEAD should still contain v111 patch'
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

    # 阶段 1：GEN=v112（全程无文件交换，最安全）
    if PHASE in (0, 1):
        for i, (name, grp, note, src, pyc) in enumerate(chunk, 1):
            decompile_cached(pyc, OUTDIR + '/%s.py' % name)
            if i % 40 == 0:
                print('[phase1] chunk %d/%d' % (i, len(chunk)), flush=True)
        print('[phase1] 本块 v112 产品就绪 %d/%d' % (len(chunk), len(chunk)), flush=True)

    # 阶段 2：一次性换 HEAD(9139e4c3) 版；finally 保证恢复
    if PHASE in (0, 2):
        try:
            open(GEN, 'w', encoding='utf-8').write(head_gen)
            open(ANA, 'w', encoding='utf-8').write(head_ana)
            for i, (name, grp, note, src, pyc) in enumerate(chunk, 1):
                decompile_cached(pyc, OUTDIR_H + '/%s.py' % name)
                if i % 40 == 0:
                    print('[phase2] chunk %d/%d' % (i, len(chunk)), flush=True)
        finally:
            open(GEN, 'w', encoding='utf-8').write(cur_gen)
            open(ANA, 'w', encoding='utf-8').write(cur_ana)
            assert open(GEN, encoding='utf-8').read() == cur_gen, 'generator not restored!'
            assert open(ANA, encoding='utf-8').read() == cur_ana, 'analyzer not restored!'
        print('[phase2] 本块 HEAD 产品就绪 %d/%d，GEN/ANA 已恢复 v112' % (len(chunk), len(chunk)), flush=True)

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
        lines.append('%-18s %-10s %s%s' % (name, ab, st,
                     ('  [%s]' % note) if note else ''))
    nd = sum(1 for r in results if r[3] == 'TEXT-DIFF')
    lines.append('')
    lines.append('TEXT-DIFF count: %d / %d' % (nd, len(results)))
    open(EV + '/r112_regress_result.txt', 'w', encoding='utf-8').write('\n'.join(lines) + '\n')

    # 与 r110 逐案签名对比（口径与 r111 一致）
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
    print('R110 案: %d  TEXT 状态一致 %d  签名一致 %d'
          % (len(cmp_rows), eq_text, eq_sig))
    print()
    print('=== 用户点名的 10 个既有登记差：r110 -> r112 逐字节同签名核验 ===')
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
        print('=== 语料替代案（r98 清理后缺失，以等价源替代；A/B TEXT-SAME 实证产品逐字节未变）===')
        for n, note, r_st, st in subst_rows:
            print('  %-14s %s' % (n, note))
            print('      r110 签名: %s' % r_st)
            print('      r112 签名: %s' % st)
        print()
    print('REGISTERED verdict:',
          'ALL SAME-SIGNATURE（含语料替代案如实登记）' if reg_ok else 'MISMATCH')
    print('TEXT-DIFF count:', nd, '/', len(results))
    print('NO-SRC 案:', [r[0] for r in results if r[3] == 'NO-SRC'])

    json.dump({
        'n_total': len(results), 'n_r110': len(cmp_rows),
        'text_status_match': eq_text, 'signature_match': eq_sig,
        'registered_all_same_signature': reg_ok,
        'registered': [
            {'name': n, 'note': note, 'r110_ab': a, 'r110_sig': s,
             'r112_ab': b, 'r112_sig': t,
             'same_signature': (ok_t and ok_s and b == 'TEXT-SAME'),
             'corpus_substituted': note.startswith('SUBSTITUTED')}
            for n, note, a, s, b, t, ok_t, ok_s in cmp_rows if n in REGISTERED],
        'corpus_substituted_cases': [
            {'name': n, 'note': note, 'r110_sig': a, 'r112_sig': b,
             'product_unchanged_ab_text_same': True}
            for n, note, a, b in subst_rows],
        'text_diff_count': nd,
        'no_src': [r[0] for r in results if r[3] == 'NO-SRC'],
        'cases': [{'name': n, 'group': g, 'note': note, 'ab': ab, 'status': st}
                  for n, g, note, ab, st, _ in results],
    }, open(EV + '/r112_regress_result.json', 'w', encoding='utf-8'),
        ensure_ascii=False, indent=1)


if __name__ == '__main__':
    for _a in sys.argv[1:]:
        if _a.startswith('--phase='):
            PHASE = int(_a.split('=', 1)[1])
        elif _a.startswith('--start='):
            START = int(_a.split('=', 1)[1])
        elif _a.startswith('--end='):
            END = int(_a.split('=', 1)[1])
    main()
