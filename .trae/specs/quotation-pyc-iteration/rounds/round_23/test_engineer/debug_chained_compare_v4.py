"""R23-N7: 详细检查 TryExceptRegion 中是否包含 b694"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, TryExceptRegion

PYC = '/workspace/quotation.pyc'


def find_code_obj(co, name):
    for const in co.co_consts:
        if isinstance(const, type(co)):
            if const.co_name == name:
                return const
            sub = find_code_obj(const, name)
            if sub:
                return sub
    return None


def main():
    module = load_pyc_file_v2(PYC)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()

    target = find_code_obj(code_obj, 'api_get_financial')

    cfg = build_cfg(target)
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()

    # Find block@694
    b694 = None
    for b in cfg.blocks.values():
        if b.start_offset == 694:
            b694 = b
            break

    if not b694:
        print("block@694 not found")
        return

    # Find TryExceptRegion containing b694
    print("=== TryExceptRegion details ===")
    for region in analyzer.regions:
        if isinstance(region, TryExceptRegion) and b694 in region.blocks:
            print(f"  entry: {region.entry.start_offset if region.entry else None}")
            print(f"  region_type: {region.region_type}")
            print(f"  blocks (sorted): {sorted(b.start_offset for b in region.blocks)}")
            print(f"  try_blocks: {[b.start_offset for b in region.try_blocks]}")
            # All handler-related attrs
            for attr in ['handler_blocks', 'handlers', 'except_blocks',
                         'handler_entries', 'else_blocks', 'final_blocks',
                         'try_body_blocks']:
                val = getattr(region, attr, None)
                if val is not None:
                    try:
                        offsets = [b.start_offset for b in val]
                        print(f"  {attr}: {offsets}")
                    except Exception:
                        print(f"  {attr}: {val}")
            # Print all list/set attrs that contain BasicBlock
            print(f"  === All attrs containing b694 ===")
            for attr in dir(region):
                if attr.startswith('_'):
                    continue
                try:
                    val = getattr(region, attr)
                except Exception:
                    continue
                if isinstance(val, (list, set, tuple)):
                    for item in val:
                        if item is b694:
                            print(f"    {attr} contains b694 directly")
                            break
                        if hasattr(item, 'blocks') and b694 in item.blocks:
                            print(f"    {attr}: item {item} contains b694")
            # Check children
            print(f"  === Children ===")
            for child in getattr(region, 'children', []) or []:
                if b694 in getattr(child, 'blocks', set()):
                    print(f"    {type(child).__name__} (entry={child.entry.start_offset if child.entry else None}) contains b694")
                    print(f"      blocks: {sorted(b.start_offset for b in child.blocks)}")


if __name__ == '__main__':
    main()
