# -*- coding: utf-8 -*-
"""rr-v5r189 patch: narrow the r171 nested-arm claim gate and the r117 ELIFTEST gate.

Two hunks, both in core/cfg/region_ast_generator.py:

  1) [v171-NESTED-ARM] `_process_if_blocks`: the nested-IfRegion arm-block claim
     gate currently keys on "nested merge == this region's merge". That both
     misses real duplicates (a nested region whose merge differs still shares its
     pure jump arm tails with the parent arm walk -> the arm tail is emitted a
     second time as a sibling `continue`, killing every later statement of the
     arm) and over-claims ordinary operand/body blocks of a nested if. Narrowed
     to the structurally load-bearing fact: only arm blocks that carry no user
     instruction at all (pure noise + jump tail) are skipped, independent of the
     merge identity.

  2) [v117-ELIFTEST] `_loop_generate_while`: the exclusion guard must only fire
     when the candidate block really is the entry of the region returned by
     `get_entry_region_for_block` (the guard's own premise). When that lookup
     falls back to an enclosing region (entry is some other block), the block is
     an ordinary latch-recheck copy and must stay absorbed, otherwise the rotated
     while-condition chain breaks and the body's break arm disappears.

Usage:
    python fix189.py            # apply (idempotent, skips already-applied hunks)
    python fix189.py --revert   # revert to the pre-patch bytes
"""
import io
import os
import py_compile
import sys
import tempfile

TARGET = os.path.join('core', 'cfg', 'region_ast_generator.py')

HUNK_A_OLD = """            if _v171_mb is not _v171_pmb:
                if not (_v171_mb is not None and _v171_pmb is not None
                        and _v171_mb.start_offset == _v171_pmb.start_offset):
                    continue
            _v171_owned_arm.update(_v171_r.then_blocks or ())
            _v171_owned_arm.update(_v171_r.else_blocks or ())
"""

HUNK_A_NEW = """            for _v171_a in (list(_v171_r.then_blocks or ())
                            + list(_v171_r.else_blocks or ())):
                if _v171_a is _v171_r.entry:
                    continue
                if any(_v171_i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL',
                                              'EXTENDED_ARG', 'JUMP_BACKWARD',
                                              'JUMP_BACKWARD_NO_INTERRUPT', 'JUMP_FORWARD',
                                              'JUMP_ABSOLUTE')
                       for _v171_i in _v171_a.instructions):
                    continue
                _v171_owned_arm.add(_v171_a)
"""

HUNK_B_OLD = """                        _b_entry_region = self.region_analyzer.get_entry_region_for_block(b)
                        if _b_entry_region is not None:
                            continue
"""

HUNK_B_NEW = """                        _b_entry_region = self.region_analyzer.get_entry_region_for_block(b)
                        if (_b_entry_region is not None
                                and getattr(_b_entry_region, 'entry', None) is b):
                            continue
"""

HUNKS = (('A', HUNK_A_OLD, HUNK_A_NEW), ('B', HUNK_B_OLD, HUNK_B_NEW))


def read(path):
    raw = open(path, 'rb').read()
    bom = raw.startswith(b'\xef\xbb\xbf')
    return raw.decode('utf-8-sig'), bom


def write(path, text, bom):
    with open(path, 'wb') as fh:
        if bom:
            fh.write(b'\xef\xbb\xbf')
        fh.write(text.encode('utf-8'))


def main(argv):
    revert = '--revert' in argv[1:]
    root = os.path.dirname(os.path.abspath(__file__))
    for i, a in enumerate(argv[1:]):
        if a == '--root':
            root = argv[i + 2]
        elif a.startswith('--root='):
            root = a.split('=', 1)[1]
    path = os.path.join(root, TARGET)
    text, bom = read(path)
    print('target: %s bom=%s' % (path, bom))
    changed = 0
    for name, old, new in HUNKS:
        src, dst = (new, old) if revert else (old, new)
        n = text.count(src)
        print('hunk %s anchor count=%d -> %s' % (name, n, 'REVERT' if revert else 'APPLY'))
        if n == 0:
            if text.count(dst) == 1:
                print('  already in target state, skip')
                continue
            print('  ERROR: anchor not found and target state not present')
            return 2
        if n != 1:
            print('  ERROR: anchor not unique')
            return 2
        text = text.replace(src, dst)
        changed += 1
    if changed:
        write(path, text, bom)
        print('wrote %d byte(s), size=%d' % (changed, len(text.encode('utf-8'))))
    else:
        print('nothing to do')
    tmp = tempfile.mkdtemp()
    try:
        py_compile.compile(path, cfile=os.path.join(tmp, 'p.pyc'), doraise=True)
        print('py_compile: OK')
    except py_compile.PyCompileError as exc:
        print('py_compile: FAILED %s' % exc)
        return 3
    print('sha256(utf-8-sig payload)=%s' % __import__('hashlib').sha256(
        text.encode('utf-8')).hexdigest()[:16])
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
