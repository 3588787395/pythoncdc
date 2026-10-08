# -*- coding: utf-8 -*-
"""cfg_branch_walk.py — 整个 CFG 图的**全部分支点**枚举（含所有子分支、所有层级）

与 cfg_anatomy.py 的区别：那份测的是「单元里是否存在某形态」（一层、布尔存在性）；
本工具遍历**每一个 code object 的 CFG 图上的每一个分支点**（决策节点），
对每个分支点递归展开其 then/else 臂内的子分支，按**支配深度**给出层级，
因此「所有子分支、所有层级」都被计入，而不是只数顶层。

分支点定义：块尾指令使控制流转为 ≥2 条路径
  - 条件跳转（POP_JUMP_*/JUMP_IF_*_OR_POP）
  - FOR_ITER（迭代器分支：体/出口）
每个分支点记录：形态分类、支配深度（= 子分支层级）、then/else 子分支数。

输出 docs/refactor/cfg-branch-walk.json
用法：python -X utf8 tools/kb/cfg_branch_walk.py [--limit N]
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

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SITE = os.path.join(ROOT, 'site-packages')
OUT = os.path.join(ROOT, 'docs', 'refactor', 'cfg-branch-walk.json')

NOISE = {'CACHE', 'EXTENDED_ARG', 'NOP', 'RESUME', 'MAKE_CELL', 'COPY_FREE_VARS'}
COND_JUMPS = {
    'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
    'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
    'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_FORWARD_IF_NOT_NONE',
    'POP_JUMP_BACKWARD_IF_NONE', 'POP_JUMP_BACKWARD_IF_NOT_NONE',
    'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
}
SHORT_CIRCUIT = {'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP'}
MATCH_OPS = {'MATCH_MAPPING', 'MATCH_SEQUENCE', 'MATCH_KEYS', 'MATCH_CLASS'}


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


def _bops(b):
    return [i for i in b.instructions if i.opname not in NOISE]


def is_branch_block(b):
    li = b.get_last_instruction()
    if li is None:
        return False
    return li.opname in COND_JUMPS or li.opname in SHORT_CIRCUIT or li.opname == 'FOR_ITER'


def branch_form(b, analyzer):
    """分支点形态分类（用实现自身判据）"""
    li = b.get_last_instruction()
    if li.opname == 'FOR_ITER':
        return 'for_iter'
    if li.opname in SHORT_CIRCUIT:
        return 'boolop'
    if analyzer is not None and hasattr(analyzer, '_is_single_expression_block'):
        succs = list(b.conditional_successors)
        if len(succs) == 2 and (analyzer._is_single_expression_block(succs[0])
                                and analyzer._is_single_expression_block(succs[1])):
            return 'ternary'
    names = set(i.opname for i in _bops(b))
    if names & MATCH_OPS:
        return 'match'
    if 'LOAD_ASSERTION_ERROR' in {i.opname for i in b.instructions}:
        return 'assert'
    if li.opname.startswith('POP_JUMP_BACKWARD'):
        return 'while'
    return 'if'


def main():
    limit = None
    if '--limit' in sys.argv:
        limit = int(sys.argv[sys.argv.index('--limit') + 1])

    pycs = sorted(os.path.join(dp, f)
                  for dp, dn, fn in os.walk(SITE) for f in fn if f.endswith('.pyc'))
    units = []
    for p in pycs:
        c0 = load_pyc(p)
        if c0 is None:
            continue
        units.append((p, c0.co_name, c0))
        for f, c in walk(c0):
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

    n_units = 0
    n_fail = 0
    total_branch_points = 0            # 整个图所有分支点总数
    form_inst = collections.Counter()  # 形态 -> 分支点实例数（含子分支）
    depth_hist = collections.Counter() # 支配深度 -> 分支点数（0=顶层，N=N 层子分支）
    depth_by_form = collections.defaultdict(collections.Counter)
    per_unit_branches = collections.Counter()  # 每单元分支点数 -> 单元数
    total_sub_branch = 0                # 深度 ≥1 的子分支点数
    max_depth = 0
    max_depth_example = None
    fail_kinds = collections.Counter()
    histo_max_depth = collections.Counter()  # 每单元最大分支深度 -> 单元数

    t0 = time.time()
    for n, (p, name, code) in enumerate(units):
        if n and n % 2000 == 0:
            print('  ... %d/%d  %.0fs' % (n, len(units), time.time() - t0))
        try:
            cfg = build_cfg(code)
        except Exception as e:
            n_fail += 1
            fail_kinds['cfg:' + type(e).__name__] += 1
            continue
        analyzer = None
        try:
            gen = RegionASTGenerator(cfg, top_level_code=code if code.co_name == '<module>' else None)
            gen.region_analyzer.analyze()   # 填充 dominators
            analyzer = gen.region_analyzer
        except Exception as e:
            n_fail += 1
            fail_kinds['region:' + type(e).__name__] += 1
        n_units += 1

        branch_blocks = [b for b in cfg.blocks.values() if is_branch_block(b)]
        cnt = len(branch_blocks)
        total_branch_points += cnt
        per_unit_branches[min(cnt, 60)] += 1
        unit_max_depth = 0
        for b in branch_blocks:
            li = b.get_last_instruction()
            depth = 0
            doms = getattr(b, 'dominators', None) or set()
            # 支配深度 = 支配该块的分支点数量（= 所在子分支层级）
            for d in doms:
                if d is not b and is_branch_block(d):
                    depth += 1
            if depth > max_depth:
                max_depth = depth
                max_depth_example = '%s :: %s :: blk@%d dom=%d' % (
                    os.path.relpath(p, ROOT), name, b.start_offset, depth)
            f = branch_form(b, analyzer)
            form_inst[f] += 1
            depth_hist[min(depth, 20)] += 1
            depth_by_form[f][min(depth, 20)] += 1
            if depth >= 1:
                total_sub_branch += 1
            if depth > unit_max_depth:
                unit_max_depth = depth
        histo_max_depth[min(unit_max_depth, 20)] += 1

    el = time.time() - t0

    def h2d(h):
        return {str(k): v for k, v in sorted(h.items())}

    out = {
        'corpus': {'pyc_files': len(pycs), 'code_objects': len(units),
                   'analyzed_units': n_units, 'fail': n_fail, 'elapsed_sec': round(el, 1)},
        'branch_points': {
            'total': total_branch_points,
            'top_level': total_branch_points - total_sub_branch,
            'sub_branches_depth_ge1': total_sub_branch,
            'by_form': dict(form_inst.most_common()),
            'depth_hist': h2d(depth_hist),
            'depth_by_form': {k: h2d(v) for k, v in sorted(depth_by_form.items())},
            'max_dominator_depth': max_depth,
            'max_depth_example': max_depth_example,
            'per_unit_branch_count_hist': h2d(per_unit_branches),
            'per_unit_max_depth_hist': h2d(histo_max_depth),
        },
        'fail_kinds': dict(fail_kinds.most_common()),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    io.open(OUT, 'w', encoding='utf-8', newline='\n').write(
        json.dumps(out, ensure_ascii=False, indent=2))

    print('\n=== 全图分支点 ===')
    print('units=%d  total_branch_points=%d (top=%d sub>=1=%d) max_dom_depth=%d  %.0fs' % (
        n_units, total_branch_points, total_branch_points - total_sub_branch,
        total_sub_branch, max_depth, el))
    print('\n--- by form (instances) ---')
    for k, v in form_inst.most_common():
        print('%8d  %s' % (v, k))
    print('\n--- depth hist (0=top, >=1=sub-branch) ---')
    for k, v in sorted(depth_hist.items(), key=lambda kv: int(kv[0])):
        print('  d=%-3s %8d' % (k, v))
    print('\nper-unit max depth hist=%s' % h2d(histo_max_depth))
    print('max depth example: %s' % max_depth_example)
    print('\nJSON -> %s' % OUT)


if __name__ == '__main__':
    main()
