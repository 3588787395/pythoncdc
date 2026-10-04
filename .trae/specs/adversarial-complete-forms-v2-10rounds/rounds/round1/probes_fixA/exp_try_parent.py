# -*- coding: utf-8 -*-
"""FIX-A 判定性实验：t_host_try_sections 假兄弟配对根因验证。

实验 A（基线）：analyze() + generate() 原样，打印产物。
实验 B（方案 B）：analyze() 后把「entry 在某 TryExceptRegion.try_blocks 内、
parent 为该 region、且 entry 不在 finally_blocks」的 TernaryRegion 的
parent 置 None 并从 children 移除，再 generate()，对比产物。

用法：python exp_try_parent.py <pyc路径> [函数名]
仅打印，不修改任何文件。
"""
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', '..')))

from core.pyc_loader_v2 import load_pyc_file_v2  # noqa: E402


def get_code(code, name):
    for c in code.co_consts:
        if hasattr(c, 'co_name'):
            if c.co_name == name:
                return c
            found = get_code(c, name)
            if found is not None:
                return found
    return None


def rn(r):
    if r is None:
        return 'None'
    return '%s@%s' % (type(r).__name__,
                      getattr(r, 'entry', None) is not None and r.entry.start_offset)


def run(pyc, name, detach, patch_try_blocks=False):
    module = load_pyc_file_v2(pyc)
    code_obj = module.code
    if hasattr(code_obj, 'get'):
        code_obj = code_obj.get()
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    c = get_code(code_obj, name)
    if c is None:
        print('!! not found', name)
        return
    from core.cfg import build_cfg
    from core.cfg.region_analyzer import TernaryRegion, TryExceptRegion
    from core.cfg.region_ast_generator import RegionASTGenerator

    cfg = build_cfg(c)
    gen = RegionASTGenerator(cfg)
    ra = gen.region_analyzer
    _regions = ra.analyze()
    # generate() 内部会无条件重跑 analyze()（且二次 analyze 不幂等），
    # 冻结为返回首次结果，保证下方 detach 修改不被覆盖。
    ra.analyze = lambda: _regions

    if detach or patch_try_blocks:
        for r in list(ra.regions):
            if not isinstance(r, TernaryRegion) or r.entry is None:
                continue
            p = getattr(r, 'parent', None)
            if not isinstance(p, TryExceptRegion):
                continue
            try_off = {b.start_offset for b in (p.try_blocks or [])}
            fin_off = {b.start_offset for b in (p.finally_blocks or [])}
            if (r.entry.start_offset in try_off
                    and r.entry.start_offset not in fin_off):
                if detach:
                    print('[EXP] detach %s from %s' % (rn(r), rn(p)))
                    r.parent = None
                    ch = getattr(p, 'children', None)
                    if ch and r in ch:
                        ch.remove(r)
            elif patch_try_blocks and r.entry.start_offset in fin_off:
                # 实验 C 侧臂：normal 副本 entry 补进 try_blocks
                # （生成端预_pass 条件 1 需 entry ∈ try_blocks 才会
                # 识别 finally normal 副本并跳过）。
                pass
        if patch_try_blocks:
            # 找 finally normal 副本 entry（有 exception 副本兄弟的候选），
            # 补进父 TryExceptRegion.try_blocks
            for r in list(ra.regions):
                if not isinstance(r, TernaryRegion) or r.entry is None:
                    continue
                p = getattr(r, 'parent', None)
                if not isinstance(p, TryExceptRegion):
                    continue
                fin_off = {b.start_offset for b in (p.finally_blocks or [])}
                if (not (getattr(p, 'has_finally', False) and p.finally_blocks)
                        or r.entry.start_offset not in fin_off):
                    continue
                # r 是 exception 副本（entry ∈ finally_blocks）。
                # 找与其 len 相等、parent 相同、entry 不在 finally 的兄弟。
                # normal 副本入口的白名单判据：entry ∈ finally_copy_blocks
                # 键集（analyzer try 识别阶段自产的常规副本入口映射），
                # 排除 handler 三元（如 T@60 entry=60 ∉ {42,86}）。
                for sib in (getattr(p, 'children', None) or []):
                    if (sib is r or not isinstance(sib, TernaryRegion)
                            or sib.entry is None):
                        continue
                    if (sib.entry.start_offset not in fin_off
                            and sib.entry.start_offset in (p.finally_copy_blocks or {})
                            and len(sib.blocks) == len(r.blocks)
                            and sib.entry not in (p.try_blocks or [])):
                        print('[EXP] patch try_blocks += blk@%s (normal copy entry of %s)'
                              % (sib.entry.start_offset, rn(r)))
                        p.try_blocks.append(sib.entry)

    ast_dict = gen.generate()
    print('==== [%s] detach=%s patch_try_blocks=%s' % (name, detach, patch_try_blocks))
    print(json.dumps(ast_dict, ensure_ascii=False, default=str)[:4000])
    print()


def main():
    pyc = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else 't_host_try_sections'
    run(pyc, name, False, False)
    run(pyc, name, True, False)
    run(pyc, name, True, True)


if __name__ == '__main__':
    main()
