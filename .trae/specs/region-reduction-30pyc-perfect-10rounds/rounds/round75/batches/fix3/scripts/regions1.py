# -*- coding: utf-8 -*-
"""regions1.py <arm> <pyc> <func> [--out=file] -- dump the region tree + CFG of one function.

Read-only diagnostic: loads the arm through the standard harness (h62), runs the
region pipeline on the ORIGINAL pyc and prints, for the requested function:
  * every CFG block (start..end, successors, role),
  * every region produced by RegionASTGenerator (type, entry, block ranges,
    then/else/merge for IfRegion, try/handler for TryExceptRegion, children).
"""
import argparse
import io
import importlib.util
import marshal
import os
import sys
import types

sys.stdout.reconfigure(encoding='utf-8')
CENTER = r'D:\Temp\opencode\r75gate\center'


def load_h62():
    s = importlib.util.spec_from_file_location('h62x', os.path.join(CENTER, 'h62.py'))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def bkey(b):
    return '%d..%d' % (b.start_offset, getattr(b, 'end_offset', -1))


def succs(b):
    out = []
    for s in (getattr(b, 'successors', None) or []):
        out.append(getattr(s, 'start_offset', '?'))
    return out


def role(b):
    try:
        return b.get_block_role().name
    except Exception:
        return '?'


def show(reg, depth, out):
    ind = '  ' * depth
    line = '%s%s entry=%s blocks=%d' % (ind, type(reg).__name__,
                                        bkey(reg.entry) if reg.entry else '-', len(reg.blocks))
    if hasattr(reg, 'region_type'):
        line += ' type=%s' % getattr(reg.region_type, 'name', reg.region_type)
    out.append(line)
    if getattr(reg, 'condition_block', None) is not None:
        tb = getattr(reg, 'then_blocks', None) or []
        eb = getattr(reg, 'else_blocks', None) or []
        mb = getattr(reg, 'merge_block', None)
        out.append('%s  cond=%s then=[%s] else=[%s] merge=%s'
                   % (ind, bkey(reg.condition_block),
                      ' '.join(bkey(b) for b in tb),
                      ' '.join(bkey(b) for b in eb),
                      bkey(mb) if mb else '-'))
    for f in ('handler_block', 'try_block', 'else_blocks', 'finally_block'):
        v = getattr(reg, f, None)
        if v and f not in ('else_blocks',):
            try:
                out.append('%s  %s=%s' % (ind, f, bkey(v)))
            except Exception:
                pass
    for f in ('try_blocks', 'protected_blocks'):
        v = getattr(reg, f, None)
        if v:
            out.append('%s  %s=[%s]' % (ind, f, ' '.join(bkey(b) for b in sorted(v, key=lambda x: x.start_offset))))
    if getattr(reg, 'metadata', None):
        md = {k: v for k, v in reg.metadata.items() if isinstance(v, (int, float, str, bool))}
        if md:
            out.append('%s  meta=%s' % (ind, md))
    for c in (reg.children or []):
        show(c, depth + 1, out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('arm')
    ap.add_argument('pyc')
    ap.add_argument('func')
    ap.add_argument('--out', default='')
    a = ap.parse_args()
    out = []
    h62 = load_h62()
    pycdc = h62._load_arm(a.arm)
    from core.cfg import build_cfg
    from core.cfg.region_ast_generator import RegionASTGenerator

    data = io.open(a.pyc, 'rb').read()
    code = marshal.loads(data[16:])

    insts = []
    orig_init = RegionASTGenerator.__init__

    def patched(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        insts.append(self)

    RegionASTGenerator.__init__ = patched
    cfg_top = build_cfg(code)
    gen = RegionASTGenerator(cfg_top, top_level_code=code)
    ast = gen.generate()
    RegionASTGenerator.__init__ = orig_init

    hit = [g for g in insts if getattr(getattr(g, 'cfg', None), 'code', None) is not None
           and g.cfg.code.co_name == a.func.rsplit('.', 1)[-1]]
    if not hit:
        out.append('generator instances: %s' %
                   [getattr(getattr(g, 'cfg', None), 'code', None).co_name
                    for g in insts if getattr(getattr(g, 'cfg', None), 'code', None)])
        out.append('function %s not found' % a.func)
    for g in hit:
        c = g.cfg
        bl = getattr(c, 'blocks', []) or []
        if isinstance(bl, dict):
            bl = list(bl.values())
        bl = [b for b in bl if hasattr(b, 'start_offset')]
        out.append('=== CFG %s blocks=%d ===' % (c.code.co_name, len(bl)))
        for b in sorted(bl, key=lambda x: x.start_offset):
            out.append('  blk %s role=%-14s succ=%s' % (bkey(b), role(b), succs(b)))
        regs = getattr(g, 'regions', None) or []
        out.append('=== regions top=%d ===' % len(regs))
        for r in regs:
            show(r, 1, out)
    txt = '\n'.join(out) + '\n'
    if a.out:
        io.open(a.out, 'w', encoding='utf-8', newline='\n').write(txt)
    else:
        sys.stdout.write(txt)


main()
