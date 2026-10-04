# -*- coding: utf-8 -*-
"""FIX-A 诊断探针：dump MatchRegion 各 case 的 pattern/guard/body 块布局。"""
import sys
import os

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


def main():
    pyc = sys.argv[1]
    name = sys.argv[2]
    module = load_pyc_file_v2(pyc)
    code_obj = module.code
    if hasattr(code_obj, 'get'):
        code_obj = code_obj.get()
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    c = get_code(code_obj, name)
    from core.cfg import build_cfg
    from core.cfg.region_analyzer import RegionAnalyzer, MatchRegion

    cfg = build_cfg(c)
    print('==== blocks:')
    for b in cfg.get_blocks_in_order():
        print('  blk@%s: %s | succs=%s' % (
            b.start_offset,
            ' '.join('%s@%s' % (i.opname, i.argval if isinstance(i.argval, int) else '')
                     for i in b.instructions),
            sorted(s.start_offset for s in b.successors)))
    ra = RegionAnalyzer(cfg)
    ra.analyze()
    print('==== match regions:')
    for r in ra.regions:
        if not isinstance(r, MatchRegion):
            continue
        print('MatchRegion@%s blocks=%s case_blocks=%s' % (
            r.entry.start_offset, sorted(b.start_offset for b in r.blocks),
            [b.start_offset for b in (r.case_blocks or [])]))
        pats = r.case_patterns or []
        guards = r.case_guards or []
        for i, body in enumerate(r.case_bodies or []):
            pat = pats[i] if i < len(pats) else None
            grd = guards[i] if i < len(guards) else None
            print('  case[%d] pattern=%r guard=%r body_blocks=%s' % (
                i, pat, grd,
                [getattr(b, 'start_offset', None) for b in body]))


if __name__ == '__main__':
    main()
