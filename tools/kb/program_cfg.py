# -*- coding: utf-8 -*-
"""program_cfg.py — **程序自身**（61 个白名单模块）的控制流图分支点枚举

分析对象是反编译器**自己的源码**（不是任何 pyc 语料）：把白名单模块编译成字节码，
对其中每个 code object 建 CFG，枚举**图上每一个分支点**（决策节点），按支配深度
展开**所有层级的所有子分支**。得到程序自身的分支规模/层级/形态分布。

程序 = core/ parsers/ bytecode/ utils/ + pycdc.py + pycdas.py（与 reachability.py 同口径）。

输出 docs/refactor/program-cfg.json
用法：python -X utf8 tools/kb/program_cfg.py [--no-compile]
"""
import collections
import dis
import io
import json
import os
import sys
import types

ROOT = r'F:\Downloads\pythoncdc-main'
OUT = os.path.join(ROOT, 'docs', 'refactor', 'program-cfg.json')
WL_DIRS = ['core', 'parsers', 'bytecode', 'utils']
ENTRIES = ['pycdc', 'pycdas']

NOISE = {'CACHE', 'EXTENDED_ARG', 'NOP', 'RESUME', 'MAKE_CELL', 'COPY_FREE_VARS'}
COND_JUMPS = {
    'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
    'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
    'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_FORWARD_IF_NOT_NONE',
    'POP_JUMP_BACKWARD_IF_NONE', 'POP_JUMP_BACKWARD_IF_NOT_NONE',
    'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
    'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP',
}
EXC_OPCODES = {'CHECK_EXC_MATCH', 'CHECK_EG_MATCH', 'PUSH_EXC_INFO', 'RERAISE',
               'WITH_EXCEPT_START', 'BEFORE_WITH', 'BEFORE_ASYNC_WITH'}


def is_branch_block(b):
    li = b.get_last_instruction()
    if li is None:
        return False
    return li.opname in COND_JUMPS or li.opname == 'FOR_ITER'


def branch_form(b):
    li = b.get_last_instruction()
    if li.opname == 'FOR_ITER':
        return 'for_iter'
    if li.opname in ('JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP'):
        return 'boolop'
    if li.opname.startswith('POP_JUMP_BACKWARD'):
        return 'while_backward'
    names = set(i.opname for i in b.instructions)
    if names & EXC_OPCODES:
        return 'exc_branch'
    return 'if'


def walk_code(code, pref=''):
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            f = (pref + '.' + c.co_name).lstrip('.')
            yield f, c
            for x in walk_code(c, f):
                yield x


def main():
    sys.path.insert(0, ROOT)
    cwd = os.getcwd()
    os.chdir(ROOT)
    try:
        from core.cfg import build_cfg
        from core.cfg.region_analyzer import DominatorAnalyzer
    finally:
        os.chdir(cwd)

    # 收集白名单源文件
    srcs = []
    for d in WL_DIRS:
        base = os.path.join(ROOT, d)
        for dp, dn, fn in os.walk(base):
            for f in sorted(fn):
                if f.endswith('.py'):
                    srcs.append(os.path.join(dp, f))
    for e in ENTRIES:
        srcs.append(os.path.join(ROOT, e + '.py'))
    srcs.sort()
    print('program modules=%d' % len(srcs))

    n_code = 0
    n_fail = 0
    total_bp = 0            # 程序自身全部分支点
    total_sub = 0           # 深度 ≥1 子分支
    form_inst = collections.Counter()
    depth_hist = collections.Counter()
    per_mod = collections.Counter()      # 模块 -> 分支点数
    per_mod_top = collections.Counter()  # 模块 -> 顶层分支数
    per_func_branches = collections.Counter()  # 每函数分支数 -> 函数数
    func_max_depth_hist = collections.Counter()
    fail_kinds = collections.Counter()
    max_depth = 0
    max_depth_fn = None

    import io as _io
    for path in srcs:
        rel = os.path.relpath(path, ROOT).replace('\\', '/')
        try:
            src = _io.open(path, encoding='utf-8-sig', errors='replace').read()  # utf-8-sig：region_ast_generator.py 带 BOM（G0 保护），裸 utf-8 读会 SyntaxError
            top = compile(src, rel, 'exec')
        except Exception as e:
            n_fail += 1
            fail_kinds['compile:' + type(e).__name__] += 1
            continue
        mod_bp = 0
        mod_top = 0
        for name, code in walk_code(top):
            n_code += 1
            try:
                cfg = build_cfg(code)
            except Exception as e:
                n_fail += 1
                fail_kinds['cfg:' + type(e).__name__] += 1
                continue
            # 填充支配信息（支配深度 = 支配该块的分支点数量）
            try:
                da = DominatorAnalyzer(cfg)
                da.analyze()
            except Exception:
                pass
            branch_blocks = [b for b in cfg.blocks.values() if is_branch_block(b)]
            mod_bp += len(branch_blocks)
            per_func_branches[min(len(branch_blocks), 200)] += 1
            fmax = 0
            for b in branch_blocks:
                depth = 0
                for d in (getattr(b, 'dominators', None) or ()):
                    if d is not b and is_branch_block(d):
                        depth += 1
                if depth == 0:
                    mod_top += 1
                else:
                    total_sub += 1
                f = branch_form(b)
                form_inst[f] += 1
                depth_hist[min(depth, 60)] += 1
                if depth > max_depth:
                    max_depth = depth
                    max_depth_fn = '%s :: %s' % (rel, name)
                if depth > fmax:
                    fmax = depth
            func_max_depth_hist[min(fmax, 60)] += 1
        total_bp += mod_bp
        per_mod[rel] = mod_bp
        per_mod_top[rel] = mod_top

    def h2d(h):
        return {str(k): v for k, v in sorted(h.items())}

    out = {
        'program': {
            'modules': len(srcs), 'code_objects': n_code, 'fail': n_fail,
            'total_branch_points': total_bp,
            'top_level': total_bp - total_sub,
            'sub_branches_depth_ge1': total_sub,
            'max_dominator_depth': max_depth, 'max_depth_fn': max_depth_fn,
        },
        'branch_forms': dict(form_inst.most_common()),
        'depth_hist': h2d(depth_hist),
        'per_func_branch_hist': h2d(per_func_branches),
        'func_max_depth_hist': h2d(func_max_depth_hist),
        'top_modules_by_branches': dict(per_mod.most_common(30)),
        'top_modules_by_toplevel': dict(per_mod_top.most_common(30)),
        'fail_kinds': dict(fail_kinds.most_common()),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    io.open(OUT, 'w', encoding='utf-8', newline='\n').write(
        json.dumps(out, ensure_ascii=False, indent=2))

    print('\n=== 程序自身控制流图 ===')
    print('modules=%d code_objects=%d fail=%d' % (len(srcs), n_code, n_fail))
    print('总分支点=%d (顶层=%d 子分支=%d) 最深支配深度=%d' % (
        total_bp, total_bp - total_sub, total_sub, max_depth))
    print('\n--- by form ---')
    for k, v in form_inst.most_common():
        print('%8d  %s' % (v, k))
    print('\n--- depth hist ---')
    for k, v in sorted(depth_hist.items(), key=lambda kv: int(kv[0])):
        if int(k) < 20 or int(k) % 10 == 0 or int(k) >= 150:
            print('  d=%-3s %8d' % (k, v))
    print('\n--- 分支点最多的模块 top 20 ---')
    for k, v in per_mod.most_common(20):
        print('%8d  %s' % (v, k))
    print('max depth fn: %s' % max_depth_fn)
    print('\nJSON -> %s' % OUT)


if __name__ == '__main__':
    main()
