"""R30-6: dump CFG blocks for change_his_to_forward, focus on 978 region."""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import build_cfg

PYC = '/workspace/quotation.pyc'


def main():
    module = load_pyc_file_v2(PYC)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()

    target = None
    for const in code_obj.co_consts:
        if hasattr(const, 'co_name') and const.co_name == 'change_his_to_forward':
            target = const
            break

    cfg = build_cfg(target)
    print("=== CFG blocks (sorted by start_offset) ===")
    blocks = sorted(cfg.blocks.values(), key=lambda b: getattr(b, 'start_offset', getattr(b, 'offset', 0)))
    for b in blocks:
        so = getattr(b, 'start_offset', getattr(b, 'offset', '?'))
        # Filter to those near 596-1300 (the elif region)
        if isinstance(so, int) and 540 <= so <= 1320:
            preds = sorted([getattr(p, 'start_offset', getattr(p, 'offset', '?')) for p in b.predecessors])
            succs = sorted([getattr(s, 'start_offset', getattr(s, 'offset', '?')) for s in b.successors])
            print(f"  block@{so}: preds={preds} succs={succs}")


if __name__ == '__main__':
    main()
