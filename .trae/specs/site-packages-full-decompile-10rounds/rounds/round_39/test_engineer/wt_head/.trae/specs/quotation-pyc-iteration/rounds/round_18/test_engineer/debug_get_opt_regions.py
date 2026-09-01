"""R18: 调试 get_opt_objects 的区域识别"""
import sys
import types
import dis

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.region_analyzer import RegionAnalyzer, AssertRegion, IfRegion, TryExceptRegion, LoopRegion
from core.cfg.cfg_builder import CFGBuilder


def main():
    module = load_pyc_file_v2('/workspace/quotation.pyc')
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()

    target = None
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == 'get_opt_objects':
            target = const
            break

    if not target:
        print("get_opt_objects not found")
        return

    print(f"=== get_opt_objects 字节码 ===")
    for ins in dis.get_instructions(target):
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        print(f"  {ins.offset:4d} {ins.opname:30s} {ins.argval!r}")

    print(f"\n=== 异常表 ===")
    for entry in target.co_exceptiontable:
        print(f"  {entry}")

    print(f"\n=== 构建 CFG ===")
    cfg = CFGBuilder().build(target)
    ra = RegionAnalyzer(cfg, parent_code=target)
    ra.analyze()

    print(f"\n=== 区域列表 ({len(ra.regions)} 个) ===")
    for r in sorted(ra.regions, key=lambda x: x.entry.start_offset if x.entry else 0):
        entry_off = r.entry.start_offset if r.entry else None
        blocks_off = sorted(b.start_offset for b in r.blocks)
        rtype = type(r).__name__
        print(f"  {rtype}: entry={entry_off}, blocks={blocks_off}")

    print(f"\n=== 基本块列表 ===")
    for blk in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
        last = blk.get_last_instruction()
        last_str = f"{last.opname}({last.argval!r})" if last else "None"
        succs = [s.start_offset for s in blk.successors]
        print(f"  block {blk.start_offset}: last={last_str}, succs={succs}")


if __name__ == '__main__':
    main()
