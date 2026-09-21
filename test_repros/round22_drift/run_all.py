# -*- coding: utf-8 -*-
"""Round 22 漂移电池 —— J1′/J2′/J3′ 三条规则的最小复现集（before/after 双镜像核判决）。

被测规则（全部已在 46e752ab 基线镜像 + 候选补丁镜像上语料级测过，本电池只做最小复现）：

  J1′  core/cfg/region_analyzer.py `_identify_conditional_regions`
       R13c 汇点塌缩站点（base 行 17132）
           if not _25b_else_is_cond and self._if_arm_is_sink(then_blocks, then_stop):
               merge = else_succ
       J1′ 给塌缩加两条同层前置条件：
         (a) _find_enclosing_loop(then_blocks[0]) is _find_enclosing_loop(else_succ)
         (b) not (臂内已有裸 `return None` 块 and else_succ 的直接后继也是裸 return None 块)

  J2′  core/cfg/region_ast_generator.py `_discover_predicate_and_chain`
       末尾 `return {'blocks': chain, 'op': 'and'}` 之前：链首块若是另一个纯操作数
       求值块（_chain_block_is_pure）前向条件跳转的落点 → 本 and 链只是 `X or <链>`
       的末析取支，拒绝重建（重建会整体丢掉左析取支）。

  J3′  core/cfg/region_ast_generator.py `_is_orphan_boundary_nop`
       纯删除 [A4/V-M] 子句：该子句只要 CFG 里**任何地方**有一条条件跳转以本边界
       NOP 为落点就拒绝折叠 —— 一个全局（跨区域）判据。

纪律（与 Round 21 相同）：**绝不使用工作树 core/ 做基线**。before/after 一律是仓库外
镜像核；本脚本只在 D:/Temp 下写构建产物，仓库内唯一写入 = 本目录。

    默认 before = D:/Temp/r23prep/mirror/base      （46e752ab，含三个缺陷）
    默认 after  = D:/Temp/r23prep/mirror/j123      （base + J1′+J2′+J3′ 三块补丁）

判决尺子 = 该镜像自带的 `_r10_strict_check.strict_compare`
    （NOISE={NOP,CACHE,PRECALL,EXTENDED_ARG}；非跳转指令逐位同；跳转按方向归一 +
      无条件跳转桩尾随；kind is None ⇒ 该函数一致）

流程（每个复现源文件）：复制→编译 .pyc→镜像核反编译→产物再编译→逐限定名 strict_compare。

用法：
    PYTHONIOENCODING=utf-8 python test_repros/round22_drift/run_all.py
    PYTHONIOENCODING=utf-8 python test_repros/round22_drift/run_all.py --only 01 05 28
    PYTHONIOENCODING=utf-8 python test_repros/round22_drift/run_all.py --show-defects
    PYTHONIOENCODING=utf-8 python test_repros/round22_drift/run_all.py \\
        --after D:/Temp/r23prep/mirror/j2p --single          # 单核归因（不判决）

真值表（键集合 == r22_*.py 去后缀，双向自检，缺项 fail-closed）：
    FIX     = 应被修好：before 必须 MISMATCH、after 必须 MATCH（否则门禁失败）
    GUARD   = 不得破坏：两世界都必须 MATCH（任一 MISMATCH ⇒ 门禁失败）
    RESIDUE = 同族异因残留：两世界都必须 MISMATCH（变 MATCH ⇒ REVIVED，仅告警不失败；
              before MATCH 而 after MISMATCH ⇒ NEW-REGRESSION，门禁失败）
退出码：0 全部分类正确；1 门禁失败；2 自检/环境失败。
"""
import sys

sys.dont_write_bytecode = True            # 绝不向仓库/镜像写 __pycache__

import json  # noqa: E402
import os  # noqa: E402
import subprocess  # noqa: E402
from pathlib import Path  # noqa: E402

HERE = Path(__file__).resolve().parent
PY = sys.executable
DEFAULT_BEFORE = 'D:/Temp/r23prep/mirror/base'
DEFAULT_AFTER = 'D:/Temp/r23prep/mirror/j123'
DEFAULT_BUILD = 'D:/Temp/r22batt/battery'

WORKER = r'''
import io, json, marshal, os, py_compile, shutil, sys, traceback
from pathlib import Path
sys.dont_write_bytecode = True
core, build, out = sys.argv[1], sys.argv[2], sys.argv[3]
srcs = sys.argv[4:]
os.makedirs(build, exist_ok=True)
sys.path.insert(0, core)
import importlib.util
_sp = importlib.util.spec_from_file_location('r22_sc', os.path.join(core, '_r10_strict_check.py'))
_sc = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(_sc)
strict_compare, load_map = _sc.strict_compare, _sc._load_map
import pycdc

def compile_to(src_py, out_pyc):
    tmp = os.path.join(build, Path(out_pyc).stem + '.c.tmp')
    pyc = py_compile.compile(str(src_py), cfile=str(tmp), doraise=True, quiet=2)
    shutil.move(str(pyc), str(out_pyc))
    return out_pyc

def one(src):
    name = os.path.splitext(os.path.basename(src))[0]
    s = os.path.join(build, name + '.py')
    shutil.copyfile(src, s)
    orig = compile_to(s, os.path.join(build, name + '.pyc'))
    text = pycdc.decompile_pyc(orig)
    if text is None:
        return {'verdict': 'ERROR', 'err': 'decompile returned None'}
    dsrc = os.path.join(build, name + '_DECOMP.py')
    io.open(dsrc, 'w', encoding='utf-8').write(text)
    dpyc = compile_to(dsrc, os.path.join(build, name + '_DECOMP.pyc'))
    a, b = load_map(orig), load_map(dpyc)
    defects = {}
    for k in sorted(set(a) & set(b)):
        kind, msg, _ = strict_compare(a[k], b[k])
        if kind is not None:
            defects[k] = '[%s] %s' % (kind, msg)
    for k in sorted(set(a) - set(b)):
        defects[k] = '[missing]'
    for k in sorted(set(b) - set(a)):
        defects[k] = '[extra]'
    return {'verdict': 'MISMATCH' if defects else 'MATCH', 'defects': defects,
            'textlen': len(text)}

res = {}
for src in srcs:
    try:
        res[os.path.splitext(os.path.basename(src))[0]] = one(src)
    except Exception as e:
        res[os.path.splitext(os.path.basename(src))[0]] = {
            'verdict': 'ERROR', 'err': '%s: %s' % (type(e).__name__, str(e)[:160]),
            'tb': traceback.format_exc()[-300:]}
io.open(out, 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1))
print('%s ok (%d)' % (os.path.basename(core), len(res)))
'''

# ---------------------------------------------------------------------------
# 实测真值（数据来源：D:/Temp/r22batt/out/attrib.txt —— base/j1a/j1b/j1g/j2p/j3/j123
# 七个镜像核对 37 个复现各跑一遍 strict 判决；逐项数值见 ANALYSIS.md §7）
# ---------------------------------------------------------------------------
KIND = {
    # ---- J1′ 锚点：before MISMATCH → after MATCH ----
    'r22_01_j1a_sink_then_loop_truncated': 'FIX',
    'r22_02_j1a_ifelse_both_loops': 'FIX',
    'r22_03_j1a_ifelse_loops_generator': 'FIX',
    'r22_04_j1ab_sink_return_none_then_loop': 'FIX',
    'r22_05_j1b_persist_nested_return_none': 'FIX',
    # ---- J1′ 守卫：塌缩该发生的仍要发生 / 站点不该触发的仍不触发 ----
    'r22_06_j1a_sink_return_in_for_legit': 'GUARD',
    'r22_07_j1a_nested_loop_split_guard': 'GUARD',
    'r22_08_j1a_arm_loop_else_plain_guard': 'GUARD',
    'r22_09_j1_plain_if_else_arms_guard': 'GUARD',
    'r22_10_j1b_return_none_then_call_guard': 'GUARD',
    'r22_11_j1b_return_none_after_stmt_guard': 'GUARD',
    # ---- J2′ 锚点 ----
    'r22_12_j2_trade_is_open_verbatim': 'FIX',
    'r22_13_j2_andor_numeric_operands': 'FIX',
    'r22_14_j2_andor_print_body': 'FIX',
    'r22_15_j2_andor_notin_operands': 'FIX',
    'r22_16_j2_andor_three_disjuncts': 'FIX',
    'r22_17_j2_andor_two_stmt_body': 'FIX',
    # ---- J2′ 守卫（含"纯 A and B 必须照常重建"与过火下限探针）----
    'r22_18_j2_plain_and_negative': 'GUARD',
    'r22_19_j2_nested_and_arms_guard': 'GUARD',
    'r22_20_j2_andor_elif_test_guard': 'GUARD',
    'r22_21_j2_andor_value_return_guard': 'GUARD',
    'r22_22_j2_prev_if_then_and_guard': 'GUARD',
    # ---- 同族异因残留（两世界都错，登记防止顺带修好/恶化）----
    'r22_23_j2_and_or_single_residue': 'RESIDUE',
    'r22_24_j2_or_paren_and_residue': 'RESIDUE',
    'r22_25_j2_and_or_while_test_residue': 'RESIDUE',
    'r22_26_j2_or_then_and_residue': 'RESIDUE',
    'r22_27_j1b_persist_in_while_residue': 'RESIDUE',
    # ---- J3′ 锚点 ----
    'r22_28_j3_elif_else_pass': 'FIX',
    'r22_29_j3_two_elif_chains_else_pass': 'FIX',
    'r22_30_j3_simple_elif_else_pass': 'FIX',
    'r22_31_j3_else_pass_in_for': 'FIX',
    'r22_32_j3_else_pass_boolop_arms': 'FIX',
    'r22_33_j3_three_chains_else_pass': 'FIX',
    # ---- J3′ 守卫（[A4/V-M] 原本保护的对象必须继续被保护）----
    'r22_34_j3_if_pass_tail_guard': 'GUARD',
    'r22_35_j3_while_false_pass_guard': 'GUARD',
    'r22_36_j3_else_pass_in_try_guard': 'GUARD',
    'r22_37_j3_elif_no_else_guard': 'GUARD',
}

EXPECT = {          # (before, after)
    'FIX': ('MISMATCH', 'MATCH'),
    'GUARD': ('MATCH', 'MATCH'),
    'RESIDUE': ('MISMATCH', 'MISMATCH'),
}


def _check_core(tag, d):
    p = Path(d)
    for need in ('pycdc.py', '_r10_strict_check.py'):
        if not (p / need).exists():
            print('ENV FAIL: %s 镜像核缺少 %s : %s' % (tag, need, p))
            return False
    if not p.exists():
        print('ENV FAIL: %s 镜像核目录不存在：%s' % (tag, p))
        print('        重建命令：D:/Python/python.exe D:/Temp/r23prep/probes/mk.py %s'
              % p.name)
        return False
    return True


def run_core(core, build, reps, tag):
    """在本进程外跑一个镜像核（两个世界必须互不串味），返回 {name: result}。"""
    wpath = Path(build) / '_r22_worker.py'
    wpath.parent.mkdir(parents=True, exist_ok=True)
    wpath.write_text(WORKER, encoding='utf-8')
    out = Path(build) / ('%s.json' % tag)
    if out.exists():
        out.unlink()
    cmd = [PY, str(wpath), str(Path(core).resolve()), str(build), str(out)]
    cmd += [str(r) for r in reps]
    env = dict(os.environ, PYTHONIOENCODING='utf-8')
    r = subprocess.run(cmd, capture_output=True, text=True, env=env,
                       cwd=str(build))
    if r.returncode or not out.exists():
        print('HARNESS FAIL (%s): rc=%d\n%s\n%s'
              % (tag, r.returncode, (r.stdout or '')[-1500:], (r.stderr or '')[-3000:]))
        return None
    return json.loads(out.read_text(encoding='utf-8'))


def selfcheck(files):
    ok = True
    for k in sorted(files - set(KIND)):
        print('SELF-CHECK FAIL: 复现文件没有真值条目: %s.py' % k)
        ok = False
    for k in sorted(set(KIND) - files):
        print('SELF-CHECK FAIL: 真值条目没有对应复现文件: %s' % k)
        ok = False
    for k, v in sorted(KIND.items()):
        if v not in EXPECT:
            print('SELF-CHECK FAIL: 非法类别 %s: %s' % (v, k))
            ok = False
    if len(files) < 10:
        print('SELF-CHECK FAIL: 复现数 %d < 10' % len(files))
        ok = False
    return ok


def first_defect(res):
    d = res.get('defects') or {}
    for k in sorted(d):
        return '%s %s' % (k.replace('<module>.', ''), d[k])
    return res.get('err', '')


def main():
    argv = sys.argv[1:]

    def flag(n):
        return n in argv

    def val(n, d):
        return argv[argv.index(n) + 1] if n in argv else d

    before = val('--before', DEFAULT_BEFORE)
    after = val('--after', DEFAULT_AFTER)
    build = val('--build', DEFAULT_BUILD)
    single = flag('--single')
    gate = not flag('--no-gate')
    show = flag('--show-defects')
    sel = [x for x in argv if not x.startswith('--')]
    sel = [x for x in sel if x not in (before, after, build)]
    if flag('--only'):
        sel = argv[argv.index('--only') + 1:] + sel
        sel = [x for x in sel if not x.startswith('r22_')]

    reps = sorted(HERE.glob('r22_*.py'))
    if not selfcheck({p.stem for p in reps}):
        return 2
    if sel:
        reps = [r for r in reps if any(s in r.stem for s in sel)]
    if not reps:
        print('没有选中的复现')
        return 2

    if single:
        core, tag = (after, 'after') if flag('--after') else (before, 'before')
        if not _check_core(tag, core):
            return 2
        data = run_core(core, build, reps, tag)
        if data is None:
            return 2
        print('single core = %s' % core)
        for r in reps:
            n = r.stem
            res = data.get(n, {'verdict': 'ERROR', 'err': 'no result'})
            print('%-44s %-9s %-8s %s' % (n, res['verdict'], KIND[n],
                                          first_defect(res)[:80]))
        return 0

    for tag, c in (('before', before), ('after', after)):
        if not _check_core(tag, c):
            return 2
    db = run_core(before, build, reps, 'before')
    da = run_core(after, build, reps, 'after')
    if db is None or da is None:
        return 2

    print('before = %s' % before)
    print('after  = %s' % after)
    print('build  = %s   (仓库内零写入)\n' % build)
    print('%-44s | %-8s | %-8s | %s' % ('id', 'before', 'after', 'verdict'))
    print('-' * 96)
    n_fail = n_rev = n_err = 0
    cnt = {'FIX': 0, 'GUARD': 0, 'RESIDUE': 0}
    cnt_ok = {'FIX': 0, 'GUARD': 0, 'RESIDUE': 0}
    for r in reps:
        n = r.stem
        kind = KIND[n]
        cnt[kind] += 1
        vb = db.get(n, {}).get('verdict', 'ERROR')
        va = da.get(n, {}).get('verdict', 'ERROR')
        eb, ea = EXPECT[kind]
        if 'ERROR' in (vb, va):
            verdict = 'ERROR'
            n_fail += 1
            n_err += 1
            detail = (db.get(n) or da.get(n) or {}).get('err', '')
        elif vb == eb and va == ea:
            verdict = {'FIX': 'FIXED-AS-CLAIMED', 'GUARD': 'STILL-CORRECT',
                       'RESIDUE': 'RESIDUE-AS-LOGGED'}[kind]
            cnt_ok[kind] += 1
            detail = ''
        elif kind == 'RESIDUE' and vb == 'MISMATCH' and va == 'MATCH':
            verdict = 'REVIVED(check)'
            n_rev += 1
            detail = '该残留被顺带修好，真值需重新基线'
        elif kind == 'RESIDUE' and vb == 'MATCH':
            verdict = 'NEW-REGRESSION'
            n_fail += 1
            detail = 'before 已 MATCH ⇒ 复现失效'
        elif kind == 'FIX' and vb == 'MATCH':
            verdict = 'NOT-REPRODUCED'
            n_fail += 1
            detail = 'before 未复现 ⇒ 锚点失效'
        elif kind == 'FIX':
            verdict = 'NOT-FIXED'
            n_fail += 1
            detail = first_defect(da.get(n, {}))
        else:
            verdict = 'BROKEN'
            n_fail += 1
            detail = first_defect(da.get(n, {}) if va != vb else db.get(n, {}))
        print('%-44s | %-8s | %-8s | %-17s %s' % (n, vb, va, verdict, detail[:46]))
        if show:
            for t, dsc in (('before', db), ('after', da)):
                for k, v in sorted((dsc.get(n, {}).get('defects') or {}).items()):
                    print('%33s %-6s %-30s %s' % ('', t, k, v))
    print()
    print('BATTERY :: repros=%d  FIX=%d/%d  GUARD=%d/%d  RESIDUE=%d/%d  '
          'REVIVED=%d  FAIL=%d  ERROR=%d'
          % (len(reps), cnt_ok['FIX'], cnt['FIX'], cnt_ok['GUARD'], cnt['GUARD'],
             cnt_ok['RESIDUE'], cnt['RESIDUE'], n_rev, n_fail, n_err))
    if gate and n_fail:
        print('GATE: FAIL —— 有锚点未被修好，或有守卫被破坏')
        return 1
    print('GATE: PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
