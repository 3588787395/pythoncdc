# -*- coding: utf-8 -*-
"""cfg_anatomy.py — 控制流图解剖与分支覆盖统计（只读）

对 site-packages 全部 pyc 的全部 code object：
  1) CFG 形态分布：块数、边数、fan-in/out 直方图、回边、汇合点、
     支配树深度、异常表条目、出口块数、最大块指令数
  2) 区域类型分布：analyze() 产出的 region 类型直方图、嵌套深度直方图
  3) 分支形态识别 vs 归约覆盖：按字节码特征识别「语料里存在的分支形态」，
     核对是否产出对应 region 类型 -> 每形态的「已有分布占比」

输出 docs/refactor/cfg-anatomy.json（UTF-8 无 BOM, newline='\\n'）
用法：python -X utf8 tools/kb/cfg_anatomy.py [--limit N] [--no-regions]
"""
import collections
import dis
import io
import json
import marshal
import os
import sys
import time
import types

ROOT = r'F:\Downloads\pythoncdc-main'
SITE = os.path.join(ROOT, 'site-packages')
OUT = os.path.join(ROOT, 'docs', 'refactor', 'cfg-anatomy.json')

NOISE = {'CACHE', 'EXTENDED_ARG', 'NOP', 'RESUME', 'MAKE_CELL', 'COPY_FREE_VARS'}

# 条件跳转（3.11 全部形态）
COND_JUMPS = {
    'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
    'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
    'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_FORWARD_IF_NOT_NONE',
    'POP_JUMP_BACKWARD_IF_NONE', 'POP_JUMP_BACKWARD_IF_NOT_NONE',
    # 3.8 遗留（3.11 不产生，但保留识别）
    'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
}
SHORT_CIRCUIT = {'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP'}
UNCOND = {'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT', 'JUMP_ABSOLUTE'}
MATCH_OPS = {'MATCH_MAPPING', 'MATCH_SEQUENCE', 'MATCH_KEYS', 'MATCH_CLASS'}
AWAIT_OPS = {'GET_AWAITABLE', 'SEND', 'CLEANUP_THROW', 'END_SEND'}


def load_pyc(p):
    data = io.open(p, 'rb').read()
    for off in (16, 12, 8):
        try:
            return marshal.loads(data[off:])
        except Exception:
            continue
    return None


def walk(code, pref=''):
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            f = (pref + '.' + c.co_name).lstrip('.')
            yield f, c
            for x in walk(c, f):
                yield x


def instrs(code):
    return [i for i in dis.get_instructions(code) if i.opname not in NOISE]


# ---------- 分支形态识别（CFG 块级精确判定） ----------
def _block_ops(b):
    return [i for i in b.instructions if i.opname not in NOISE]


def _is_ternary_header(b, analyzer=None):
    """三元头判定 = region_analyzer 的两个判据叠加（以实现为唯一事实源）：
    (1) 条件块以条件跳转结尾且恰有 2 个条件后继；
    (2) 两个值块都是「单表达式块」——region_analyzer._is_single_expression_block
        (:2823)：剥掉尾部跳转/条件跳后不得为空，且不得含 STORE/RETURN 等副作用；
        三元值块的字节码形如 `LOAD_x; JUMP_FORWARD merge`（值留给 merge 处 STORE），
        而 if-return 形如 `LOAD_x; RETURN_VALUE`（不构成三元）。
    实测「同目标 STORE_」判据会把语句级钻石（if c: continue/break）误计为三元，
    必须用实现自身的判据，否则覆盖率被系统性低估。
    """
    li = b.get_last_instruction()
    if li is None or li.opname not in COND_JUMPS or li.argval is None:
        return False
    succs = list(b.conditional_successors)
    if len(succs) != 2:
        return False
    if analyzer is not None and hasattr(analyzer, '_is_single_expression_block'):
        return bool(analyzer._is_single_expression_block(succs[0])
                    and analyzer._is_single_expression_block(succs[1]))
    # 无 analyzer 时的保守回退：仅当两臂均为 LOAD/CALL 类且尾跳指向同一直跳目标
    for s in succs:
        si = _block_ops(s)
        while si and si[-1].opname in ('JUMP_FORWARD', 'JUMP', 'EXTENDED_ARG'):
            si = si[:-1]
        if not si or si[-1].opname.startswith('STORE_'):
            return False
        if si[-1].opname in ('RETURN_VALUE', 'RETURN_CONST', 'RAISE_VARARGS', 'YIELD_VALUE'):
            return False
    return True


def detect_forms(code, cfg, ops, et_entries, analyzer=None):
    """CFG 块级判定分支形态（返回形态集合）。analyzer 用于调用实现自身的判据。"""
    forms = set()
    all_ops = [i for i in ops]
    names = set(i.opname for i in all_ops)
    blocks = list(cfg.blocks.values())

    for i in all_ops:
        if i.opname == 'FOR_ITER':
            forms.add('for_loop')
        elif i.opname in ('JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP'):
            forms.add('boolop')
        elif i.opname == 'BEFORE_WITH':
            forms.add('with')
        elif i.opname in MATCH_OPS:
            forms.add('match')
        elif i.opname == 'LOAD_ASSERTION_ERROR':
            forms.add('assert')
        elif i.opname == 'YIELD_VALUE':
            forms.add('yield_suspend')
        elif i.opname in AWAIT_OPS:
            forms.add('await_suspend')
        elif i.opname in ('RETURN_VALUE', 'RETURN_CONST'):
            forms.add('return')
        elif i.opname in ('RAISE_VARARGS', 'RERAISE'):
            forms.add('raise')
    if et_entries:
        forms.add('try_except')
        if any(b.get_last_instruction() and b.get_last_instruction().opname == 'RERAISE'
               for b in blocks):
            forms.add('try_finally')
    if code.co_name in ('<listcomp>', '<setcomp>', '<dictcomp>', '<genexpr>'):
        forms.add('comprehension')
    if code.co_flags & 0x20:  # CO_GENERATOR
        forms.add('generator')

    # 块级分支判定
    cond_blocks = [b for b in blocks
                   if b.get_last_instruction() and b.get_last_instruction().opname in COND_JUMPS]
    back_cond = [b for b in cond_blocks
                 if b.get_last_instruction().opname.startswith('POP_JUMP_BACKWARD')]
    fwd_cond = [b for b in cond_blocks
                if b.get_last_instruction().opname.startswith('POP_JUMP_FORWARD')]
    if back_cond:
        forms.add('while_loop')
    # 链式比较：2+ 条件跳转发同一目标（配合 DUP_TOP/ROT_THREE/COPY）
    tgt = collections.Counter(b.get_last_instruction().argval for b in cond_blocks)
    if any(v >= 2 for v in tgt.values()) and ({'DUP_TOP', 'ROT_THREE', 'COPY'} & names):
        forms.add('chained_compare')
    # 三元
    if any(_is_ternary_header(b, analyzer) for b in cond_blocks):
        forms.add('ternary')
    # if 分支：非回边、非三元、非短路、非比较、且不是 assert/match 承载
    if fwd_cond:
        non_tern = [b for b in fwd_cond if not _is_ternary_header(b, analyzer)]
        if non_tern and not (forms & {'match', 'assert', 'boolop'}):
            forms.add('if_branch')
    return forms


# 形态 -> 期望 region 类型
FORM2REGION = {
    'for_loop': 'LoopRegion',
    'while_loop': 'LoopRegion',
    'if_branch': 'IfRegion',
    'boolop': 'BoolOpRegion',
    'ternary': 'TernaryRegion',
    'try_except': 'TryExceptRegion',
    'try_finally': 'TryExceptRegion',
    'with': 'WithRegion',
    'match': 'MatchRegion',
    'assert': 'AssertRegion',
    'chained_compare': None,
    'generator': None,
}
# 非区域形态（不参与 region 覆盖）
NONREGION = {'return', 'raise', 'yield_suspend', 'await_suspend', 'comprehension'}


def main():
    limit = None
    do_regions = True
    args = sys.argv[1:]
    if '--limit' in args:
        limit = int(args[args.index('--limit') + 1])
    if '--no-regions' in args:
        do_regions = False

    pycs = []
    for dp, dn, fn in os.walk(SITE):
        for f in fn:
            if f.endswith('.pyc'):
                pycs.append(os.path.join(dp, f))
    pycs.sort()

    units = []
    for p in pycs:
        code = load_pyc(p)
        if code is None:
            continue
        units.append((p, code.co_name, code))
        for f, c in walk(code):
            units.append((p, f, c))
    if limit:
        units = units[:limit]
    print('pyc=%d units=%d' % (len(pycs), len(units)))

    sys.path.insert(0, ROOT)
    cwd = os.getcwd()
    os.chdir(ROOT)
    try:
        from core.cfg import build_cfg
        from core.cfg.region_ast_generator import RegionASTGenerator
    finally:
        os.chdir(cwd)

    # 累加器
    n_units = 0
    n_fail_cfg = 0
    n_fail_region = 0
    blocks_hist = collections.Counter()
    edges_hist = collections.Counter()
    fanin_hist = collections.Counter()
    fanout_hist = collections.Counter()
    back_edges = 0
    join_points = 0
    dom_depth_hist = collections.Counter()
    et_entries_total = 0
    units_with_et = 0
    exit_blocks_hist = collections.Counter()
    max_block_instr = 0
    region_types = collections.Counter()
    region_nest_hist = collections.Counter()
    form_units = collections.Counter()      # 形态 -> 出现单元数
    form_covered = collections.Counter()    # 形态 -> 有对应 region 的单元数
    form_files = collections.defaultdict(set)
    n_any_region_form = 0                    # 含任一「区域形态」的单元数
    n_region_instances = 0                   # 非 BASIC 区域实例总数
    fail_kinds = collections.Counter()

    t0 = time.time()
    for n, (p, name, code) in enumerate(units):
        if n and n % 2000 == 0:
            print('  ... %d/%d  %.0fs' % (n, len(units), time.time() - t0))
        ops = instrs(code)
        try:
            et_entries = len(getattr(code, 'co_exceptiontable', b'') or b'')
        except Exception:
            et_entries = 0
        # CFG 形态
        try:
            cfg = build_cfg(code)
        except Exception as e:
            n_fail_cfg += 1
            fail_kinds['cfg:' + type(e).__name__] += 1
            continue
        n_units += 1
        # 区域分析（先建 analyzer，供形态检测调用实现自身判据）
        regions = []
        gen = None
        if do_regions:
            try:
                gen = RegionASTGenerator(cfg, top_level_code=code if code.co_name == '<module>' else None)
                regions = gen.region_analyzer.analyze()
            except Exception as e:
                n_fail_region += 1
                fail_kinds['region:' + type(e).__name__] += 1
        analyzer = getattr(gen, 'region_analyzer', None) if gen is not None else None
        # 分支形态识别（依赖 CFG + 实现自身判据）
        forms = detect_forms(code, cfg, ops, et_entries, analyzer)
        for f_ in forms:
            form_units[f_] += 1
            form_files[f_].add(os.path.relpath(p, ROOT))
        blocks = list(cfg.blocks.values())
        nb = len(blocks)
        blocks_hist[min(nb, 200)] += 1
        et_entries_total += et_entries
        if et_entries:
            units_with_et += 1
        exit_blocks_hist[len(cfg.exit_blocks)] += 1
        ne = 0
        fanin = []
        for b in blocks:
            preds = getattr(b, 'predecessors', []) or []
            succs = getattr(b, 'successors', []) or []
            ne += len(succs)
            fanin.append(len(preds))
            fanout_hist[min(len(succs), 6)] += 1
            if any(getattr(s, 'start_offset', 0) < b.start_offset for s in succs):
                back_edges += 1
            if len(preds) >= 2:
                join_points += 1
            mi = len([i for i in getattr(b, 'instructions', []) if i.opname not in NOISE])
            if mi > max_block_instr:
                max_block_instr = mi
        edges_hist[min(ne, 400)] += 1
        for fi in fanin:
            fanin_hist[min(fi, 6)] += 1
        # 区域类型 + 覆盖统计（regions 已在上方求出）
        if do_regions:
            present = set()
            for r in regions:
                rt = type(r).__name__
                region_types[rt] += 1
                present.add(rt)
                if rt != 'Region':
                    n_region_instances += 1
                d = 0
                cur = getattr(r, 'parent', None)
                while cur is not None:
                    d += 1
                    cur = getattr(cur, 'parent', None)
                region_nest_hist[min(d, 12)] += 1
            if forms & set(FORM2REGION):
                n_any_region_form += 1
            for f_ in forms:
                exp = FORM2REGION.get(f_)
                if exp and exp in present:
                    form_covered[f_] += 1
        else:
            # 无 region 时不判覆盖
            pass

    el = time.time() - t0
    # 汇总
    def hist2dict(h):
        return {str(k): v for k, v in sorted(h.items())}

    def pct(a, b):
        return (100.0 * a / b) if b else 0.0

    coverage = {}
    for f_ in sorted(form_units):
        tot = form_units[f_]
        cov = form_covered.get(f_, 0)
        coverage[f_] = {
            'units': tot,
            'covered_units': cov,
            'coverage_pct': round(pct(cov, tot), 2),
            'files': len(form_files[f_]),
            'region_form': ('非区域形态' if f_ in NONREGION
                            else FORM2REGION.get(f_, 'n/a')),
        }

    out = {
        'corpus': {
            'site_packages': SITE,
            'pyc_files': len(pycs),
            'code_objects': len(units),
            'analyzed_units': n_units,
            'cfg_fail': n_fail_cfg,
            'region_fail': n_fail_region,
            'elapsed_sec': round(el, 1),
        },
        'cfg_shape': {
            'blocks_hist': hist2dict(blocks_hist),
            'edges_hist': hist2dict(edges_hist),
            'fanin_hist': hist2dict(fanin_hist),
            'fanout_hist': hist2dict(fanout_hist),
            'back_edges_total': back_edges,
            'join_points_total': join_points,
            'exception_table_entries_total': et_entries_total,
            'units_with_exception_table': units_with_et,
            'exit_blocks_hist': hist2dict(exit_blocks_hist),
            'max_block_instructions': max_block_instr,
        },
        'region_distribution': {
            'region_types': dict(region_types.most_common()),
            'nesting_depth_hist': hist2dict(region_nest_hist),
            'non_basic_region_instances': n_region_instances,
            'units_with_any_region_form': n_any_region_form,
        },
        'branch_coverage': coverage,
        'fail_kinds': dict(fail_kinds.most_common()),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    io.open(OUT, 'w', encoding='utf-8', newline='\n').write(
        json.dumps(out, ensure_ascii=False, indent=2))

    # 打印摘要
    print('\n=== corpus ===')
    print('pyc=%d code_objects=%d analyzed=%d cfg_fail=%d region_fail=%d %.0fs' % (
        len(pycs), len(units), n_units, n_fail_cfg, n_fail_region, el))
    print('\n=== region types (top) ===')
    for k, v in region_types.most_common(20):
        print('%7d  %s' % (v, k))
    print('\n=== branch coverage ===')
    for f_ in sorted(form_units, key=lambda x: -form_units[x]):
        c = coverage[f_]
        print('%7d units  %6.2f%%  %-20s %-28s files=%d' % (
            c['units'], c['coverage_pct'], f_, c['region_form'], c['files']))
    print('\nJSON -> %s' % OUT)


if __name__ == '__main__':
    main()
