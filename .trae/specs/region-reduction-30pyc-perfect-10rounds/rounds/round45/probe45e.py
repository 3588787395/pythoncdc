"""Region roles + block_to_region ownership dumper (landed core, read-only).

usage: python -X utf8 probe45e.py <pyc> <LOAD_CONST marker> <dump.txt>
Monkeypatches RegionAnalyzer.analyze; dumps the function whose blocks contain
LOAD_CONST <marker>. Nothing in the repo is modified.
"""
import importlib.util
import io
import sys

REPO = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, REPO)
sys.stdout.reconfigure(encoding='utf-8')

from core.cfg.region_analyzer import RegionAnalyzer  # noqa: E402

ORIG = RegionAnalyzer.analyze
TARGET = sys.argv[1]
MARKER = sys.argv[2]
DUMP = sys.argv[3]
io.open(DUMP, 'w', encoding='utf-8').write('')


def bi(b):
    if b is None:
        return '-'
    ins = list(getattr(b, 'instructions', []) or [])
    if not ins:
        return 'B?'
    return 'B%d' % ins[0].offset


def bl(lst):
    return '[' + ','.join(bi(x) for x in (lst or [])) + ']'


def bll(lst):
    return '[' + ';'.join(bl(x) for x in (lst or [])) + ']'


def walk(r, depth, out):
    pad = '  ' * depth
    out.append('%s%s %s entry=%s exit=%s cond=%s then=%s else=%s merge=%s' % (
        pad, type(r).__name__, getattr(r, 'region_type', '?'), bi(r.entry),
        bi(getattr(r, 'exit', None)), bi(getattr(r, 'condition_block', None)),
        bl(getattr(r, 'then_blocks', None)), bl(getattr(r, 'else_blocks', None)),
        bi(getattr(r, 'merge_block', None))))
    out.append('%s   elif_cond=%s elif_bodies=%s final_else=%s' % (
        pad, bl(getattr(r, 'elif_conditions', None)),
        bll(getattr(r, 'elif_bodies', None)), bl(getattr(r, 'elif_final_else', None))))
    out.append('%s   blocks=%s' % (pad, bl(sorted(r.blocks, key=lambda b: b.instructions[0].offset))))
    for c in r.children:
        walk(c, depth + 1, out)


def patched(self):
    rs = ORIG(self)
    try:
        seen, allr = set(), []

        def collect(r):
            if id(r) in seen:
                return
            seen.add(id(r))
            allr.append(r)
            for c in r.children:
                collect(c)
        for r in rs:
            collect(r)
        blob = set()
        for r in allr:
            blob |= r.blocks
        hit = False
        for b in blob:
            for i in (getattr(b, 'instructions', []) or []):
                if i.opname == 'LOAD_CONST' and i.argval == MARKER:
                    hit = True
        if not hit:
            return rs
        out = ['', '########## REGIONS (%d top, %d total, %d blocks)' % (len(rs), len(allr), len(blob))]
        for r in rs:
            walk(r, 0, out)
        out.append('########## ownership')
        cfgb = [b for b in (getattr(self.cfg, 'blocks', None) or [])
                if getattr(b, 'instructions', None)] or list(blob)
        for b in sorted(cfgb, key=lambda q: q.instructions[0].offset):
            o = self.block_to_region.get(b)
            term = b.instructions[-1]
            out.append('  B%-4d term=%-30s succ=%s preds=%s owner=%s(%s)' % (
                b.instructions[0].offset, term.opname + ' ' + str(term.argval or ''),
                [bi(s) for s in (getattr(b, 'successors', []) or [])],
                [bi(p) for p in (getattr(b, 'predecessors', []) or [])],
                type(o).__name__ if o else 'None', getattr(o, 'region_type', '-') if o else '-'))
        io.open(DUMP, 'a', encoding='utf-8').write('\n'.join(out) + '\n')
    except Exception as e:
        io.open(DUMP, 'a', encoding='utf-8').write('PROBE ERROR %r\n' % (e,))
    return rs


RegionAnalyzer.analyze = patched
_s = importlib.util.spec_from_file_location('pc', REPO + '/pycdc.py')
pc = importlib.util.module_from_spec(_s)
_s.loader.exec_module(pc)
txt = pc.decompile_pyc(TARGET)
print('decompiled ok, chars=%d -> %s' % (len(txt), DUMP))
