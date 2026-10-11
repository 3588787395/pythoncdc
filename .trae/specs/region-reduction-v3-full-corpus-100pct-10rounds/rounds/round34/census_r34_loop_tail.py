"""R34 read-only census: which back-edge blocks does the P1-3b suppression claim today?

Replicates the INPUTS of `region_ast_generator._is_loop_tail_convergence_block`
(CRLF-safe, no generation, no repo writes) for every LoopRegion of every code object
of every verification pyc, and splits the population by one new fact the predicate
does not currently look at: whether the convergence block is the loop body's
TERMINAL block in offset order.

Why that split decides: suppression is only sound when the recompiled for/while
statement regenerates the back-edge itself, i.e. when the block is the body's last
block. A convergence block that is INTERIOR (more loop-body code follows it) is an
explicit `continue` that skips that code - ipo_stocks_order @3572, whose two preds are
the nested if's false edge and its then-body fall-through, is exactly that shape.

usage: python -X utf8 census_r34_loop_tail.py <out.jsonl> [name-filter ...]
       (no filter = the whole 402-file verification face)
"""
import glob
import json
import marshal
import os
import sys
import types

SPEC = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(SPEC, '..', '..', '..', '..', '..'))
if not os.path.isfile(os.path.join(ROOT, 'pycdc.py')):
    sys.exit('[fatal] ROOT wrong: no pycdc.py under %s' % ROOT)
sys.path.insert(0, ROOT)

from core.cfg import build_cfg                       # noqa: E402
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion  # noqa: E402

SITE = os.path.join(ROOT, 'site-packages')
BACK = ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')


def code_objects(co):
    yield co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            for x in code_objects(c):
                yield x


def verify_face():
    """The 402 pyc that have a sibling OK.py product (the gate's verification face)."""
    out = []
    for p in sorted(glob.glob(os.path.join(SITE, '**', '*.pyc'), recursive=True)):
        d, fn = os.path.split(p)
        stem = fn[:-4]
        if os.path.isfile(os.path.join(d, stem + 'OK.py')):
            out.append(p)
    return out


NONMEAN = ('RESUME', 'NOP', 'CACHE', 'EXTENDED_ARG', 'PUSH_NULL', 'POP_TOP',
             'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT', 'JUMP_FORWARD',
             'JUMP_ABSOLUTE')


def n_meaningful(block):
    return sum(1 for i in block.instructions if i.opname not in NONMEAN)


def last_instr(block):
    for i in reversed(block.instructions):
        if i.opname in ('NOP', 'CACHE', 'EXTENDED_ARG'):
            continue
        return i
    return None


def classify(cfg, analyzer, loop):
    hdr = getattr(loop, 'header_block', None)
    body = list(getattr(loop, 'body_blocks', None) or [])
    if hdr is None or not body:
        return
    universe = set(body) | {hdr}
    max_off = max(b.start_offset for b in universe)
    _bes = set(getattr(loop, 'back_edge_blocks', None) or set())
    if getattr(loop, 'back_edge_block', None) is not None:
        _bes.add(loop.back_edge_block)
    for b in body:
        li = last_instr(b)
        if li is None or li.opname not in BACK or li.argval is None:
            continue
        tgt = cfg.get_block_by_offset(li.argval)
        if tgt is None or tgt is not hdr:
            continue
        preds = [p for p in (getattr(b, 'predecessors', None) or []) if p is not b]
        if len(preds) < 2:
            continue
        if not all(p in universe for p in preds):
            continue
        # today's predicate returns True here => explicit Continue suppressed
        yield b, preds, max_off, (b in _bes)


def main():
    out_path = sys.argv[1]
    filters = sys.argv[2:]
    files = verify_face()
    if filters:
        files = [f for f in files if any(k in f for k in filters)]
    n_files = n_units = n_hits = n_term = n_inter = 0
    n_inter_pure = 0
    n_qual = 0
    with open(out_path, 'w', encoding='utf-8', newline='\n') as fh:
        for p in files:
            try:
                data = open(p, 'rb').read()
                if len(data) < 17:
                    continue
                code = marshal.loads(data[16:])
            except Exception as e:
                fh.write(json.dumps({'file': p, 'error': 'marshal:%s' % e}) + '\n')
                continue
            for co in code_objects(code):
                try:
                    cfg = build_cfg(co)
                    analyzer = RegionAnalyzer(cfg)
                    regions = analyzer.analyze()
                except Exception as e:
                    continue
                n_units += 1
                for r in regions:
                    if not isinstance(r, LoopRegion):
                        continue
                    for b, preds, max_off, in_be in classify(cfg, analyzer, r):
                        n_hits += 1
                        _term = (b.start_offset == max_off)
                        if _term:
                            n_term += 1
                        else:
                            n_inter += 1
                            if n_meaningful(b) == 0:
                                n_inter_pure += 1
                                if not in_be:
                                    n_qual += 1
                        rec = {
                            'file': os.path.relpath(p, SITE).replace('\\', '/'),
                            'unit': co.co_name,
                            'loop_kind': type(r).__name__,
                            'hdr': hdr_off(r),
                            'block': b.start_offset,
                            'block_end': (last_instr(b).offset if last_instr(b) else None),
                            'n_preds': len(preds),
                            'pred_offsets': sorted(x.start_offset for x in preds),
                            'terminal': _term,
                            'body_max_off': max_off,
                            'n_body': len(r.body_blocks or []),
                            'role': str(analyzer.get_block_role(b)),
                            'n_meaningful': n_meaningful(b),
                            'pure': n_meaningful(b) == 0,
                            'in_back_edges': in_be,
                            'qualifies': (not _term) and n_meaningful(b) == 0
                                           and not in_be,
                        }
                        fh.write(json.dumps(rec, ensure_ascii=False) + '\n')
            n_files += 1
    print('files=%d code_objects=%d convergence_hits=%d terminal=%d interior=%d '
          'interior_pure=%d qualifying=%d'
          % (n_files, n_units, n_hits, n_term,
             n_inter, n_inter_pure, n_qual))


def hdr_off(loop):
    h = getattr(loop, 'header_block', None)
    return h.start_offset if h else None


if __name__ == '__main__':
    main()
