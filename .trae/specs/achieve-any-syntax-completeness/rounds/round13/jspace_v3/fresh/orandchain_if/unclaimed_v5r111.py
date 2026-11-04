# rr-v5r111 [v111-ORAND] 未领形态 HEAD 基线验证（如实登记，不造绿）
#   对 3 个扩展合成案，复用 matrix_v5r111.py 已产出的 原件pyc / v111产品 /
#   HEAD产品（A/B 交换时由 git-show 的 HEAD 版反编译得到），证明：
#     (1) v111 产品与 HEAD 产品逐字节相同（本轮窄修复未改变其文本）；
#     (2) 原件 pyc 与 HEAD 产品重编译本就 recompile DIFF（HEAD 基线即错）；
#     (3) 原件 pyc 与 v111 产品重编译 DIFF 签名与 (2) 完全一致。
#   结论：这些形态属 HEAD 预存在的另一分析端缺陷族，本轮不认领、如实登记。
import os, sys, types, marshal, json

EV = 'F:/Downloads/pythoncdc-main/.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/orandchain_if'
MP = EV + '/matrix_products'
NAMES = ['v111_or_and3', 'v111_or3_and2', 'v111_prefix_stmts']


def norm(c):
    return (c.co_code.hex(), c.co_exceptiontable.hex(),
            c.co_names, c.co_varnames, c.co_freevars, c.co_cellvars,
            c.co_flags,
            tuple(norm(k) if isinstance(k, types.CodeType) else k
                  for k in c.co_consts))


def toplevels(c):
    return {k.co_name: norm(k) for k in c.co_consts if isinstance(k, types.CodeType)}


def load_pyc(p):
    with open(p, 'rb') as f:
        return marshal.loads(f.read()[16:])


def sig_of(text):
    try:
        return toplevels(compile(text, 'p', 'exec'))
    except SyntaxError as se:
        return {'__SYNTAX_ERR__': se.msg[:60]}


def diff_sig(orig, prod):
    rem = sorted(set(orig) - set(prod))
    add = sorted(set(prod) - set(orig))
    chg = sorted(n for n in set(orig) & set(prod) if orig[n] != prod[n])
    return 'rem=%s add=%s chg=%s' % (rem, add, chg)


def main():
    rows = []
    for n in NAMES:
        pyc = MP + '/%s.pyc' % n
        pv = MP + '/%s_v111.py' % n
        ph = MP + '/%s_head.py' % n
        tv = open(pv, 'rb').read()
        th = open(ph, 'rb').read()
        ab_same = (tv == th)
        orig = toplevels(load_pyc(pyc))
        sv = sig_of(tv.decode('utf-8'))
        sh = sig_of(th.decode('utf-8'))
        dv = diff_sig(orig, sv)
        dh = diff_sig(orig, sh)
        # 逐字节相同的产品 => 重编译签名必然相同
        consistent = ab_same and (dv == dh) and (sv == sh)
        rows.append({'name': n, 'v111_eq_head_bytes': ab_same,
                     'orig_vs_head_recompile': dh,
                     'orig_vs_v111_recompile': dv,
                     'head_baseline_already_diff': dh != 'rem=[] add=[] chg=[]',
                     'signature_consistent': consistent})
    print()
    for r in rows:
        print('%-20s v111==HEAD(字节)=%s  HEAD基线DIFF=%s  签名一致=%s'
              % (r['name'], r['v111_eq_head_bytes'],
                 r['head_baseline_already_diff'], r['signature_consistent']))
        print('    orig vs HEAD recompile : %s' % r['orig_vs_head_recompile'])
        print('    orig vs v111 recompile : %s' % r['orig_vs_v111_recompile'])
    ok = all(r['v111_eq_head_bytes'] and r['head_baseline_already_diff']
             and r['signature_consistent'] for r in rows)
    print()
    print('CONCLUSION: %s —— 3 个形态均为 HEAD 基线即 recompile DIFF、v111 产品文本'
          '与 HEAD 逐字节相同、本轮窄修复未触碰；如实登记为未闭合/未领形态。'
          % ('VERIFIED' if ok else 'INCONSISTENT'))
    json.dump({'verified': ok, 'rows': rows},
              open(EV + '/unclaimed_v5r111_result.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
