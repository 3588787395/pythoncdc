"""R21-55 corpus-wide census of the [R47] rejection population and of the proposed
diamond-join recovery predicate (analyzer-only: build_cfg + RegionAnalyzer.analyze per code object,
no AST generation, so a whole shard fits in one command).

Counting rule (same as the panel census):
  EVAL   = guard statement executed (region_analyzer.py:26138)
  REJECT = guard body executed (:26141) -> ternary candidate declined for lack of a value exit
  FIRE   = a REJECT whose arms satisfy _r2155_diamond_join (counted once per (code object, cond block))

usage: python -X utf8 work/census_r2155_corpus.py <out.json> <shard-idx> <shard-count>
"""
import json
import os
import sys
import types
from collections import defaultdict

MIRROR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, MIRROR)
REPO = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main"
SP = os.path.join(REPO, "site-packages")

OUT = sys.argv[1]
SHARD = int(sys.argv[2])
NSHARDS = int(sys.argv[3])

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
import core.cfg.region_analyzer as an
from core.cfg.region_analyzer import RegionAnalyzer

ANALYZER_FILE = os.path.normcase(os.path.abspath(an.__file__))
GUARD_LINE = 26138
REJECT_LINE = 26141
JUMP_OPS = frozenset({'JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'})
HANDLER_FIRST_OPS = frozenset({'PUSH_EXC_INFO', 'WITH_EXCEPT_START'})


VARIANT = os.environ.get('R2155V', 'A').upper()
_PRODUCER_PREFIX = ('LOAD_', 'BUILD_', 'PUSH_')
EXC_ENTRY = ('PUSH_EXC_INFO', 'WITH_EXCEPT_START')


def _r2155_diamond_join(cfg, true_block, false_block):
    t_last = true_block.get_last_instruction()
    if t_last is None or not isinstance(t_last.argval, int):
        return None
    if t_last.opname not in JUMP_OPS:
        return None
    join = cfg.get_block_by_offset(t_last.argval)
    if join is None or join is true_block or join is false_block:
        return None
    if join not in list(false_block.successors or []):
        return None
    j_first = join.get_first_instruction()
    if j_first is None:
        return None
    if j_first.opname in (HANDLER_FIRST_OPS if 'HANDLER_FIRST_OPS' in dir() else EXC_ENTRY):
        return None
    if VARIANT == 'B' and j_first.opname.startswith(_PRODUCER_PREFIX):
        return None
    preds = [p for p in (join.predecessors or []) if p is not None]
    if len(preds) != 2:
        return None
    if set(id(p) for p in preds) != {id(true_block), id(false_block)}:
        return None
    return join


ST = {'eval': 0, 'reject': 0, 'fire': 0}
FILES = {}
_seen = set()


def _step(st):
    def step(frame, event, arg):
        if event == 'line':
            ln = frame.f_lineno
            if ln == GUARD_LINE:
                st['eval'] += 1
            elif ln == REJECT_LINE:
                st['reject'] += 1
                fl = frame.f_locals
                tb, fb = fl.get('true_block'), fl.get('false_block')
                cfg = fl['self'].cfg
                cond = getattr(fl.get('block'), 'start_offset', None)
                if tb is None or fb is None:
                    return step
                j = _r2155_diamond_join(cfg, tb, fb)
                if j is not None:
                    key = (cfg.name, cond)
                    if key not in _seen:
                        _seen.add(key)
                        st['fire'] += 1
                        st.setdefault('sites', []).append('%s:@%s(t@%s,f@%s->join@%s)' % (
                            cfg.name, cond, tb.start_offset, fb.start_offset, j.start_offset))
            return step
        return step
    return step


def dispatch(frame, event, arg):
    if event != 'call' or os.path.normcase(frame.f_code.co_filename) != ANALYZER_FILE:
        return None
    if frame.f_code.co_name != '_detect_ternary_pattern':
        return None
    return dispatch.step_frame(frame, event, arg)


dispatch.step_frame = lambda f, e, a: _step(ST)(f, e, a)

allpyc = []
for root, dirs, files in os.walk(SP):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for f in files:
        if f.endswith('.pyc'):
            allpyc.append(os.path.join(root, f))
allpyc.sort()
mine = [p for i, p in enumerate(allpyc) if i % NSHARDS == SHARD]
print('corpus pyc=%d shard=%d/%d files=%d' % (len(allpyc), SHARD, NSHARDS, len(mine)))


def walk_codes(c):
    yield c
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            yield from walk_codes(k)


results = {}
for p in mine:
    rel = os.path.relpath(p, SP).replace(os.sep, '/')
    st = {'eval': 0, 'reject': 0, 'fire': 0, 'sites': [], 'err': None}
    try:
        mod = load_pyc_file_v2(p)
        code = mod.code.get() if hasattr(mod.code, 'get') else mod.code
        if hasattr(code, 'to_python_code'):
            code = code.to_python_code()
        sys.settrace(dispatch)
        try:
            for co in walk_codes(code):
                ST['eval'] = 0
                ST['reject'] = 0
                ST['fire'] = 0
                ST['sites'] = []
                _seen.clear()
                try:
                    cfg = build_cfg(co)
                    RegionAnalyzer(cfg).analyze()
                except Exception as e:
                    continue
                st['eval'] += ST['eval']
                st['reject'] += ST['reject']
                st['fire'] += ST['fire']
                st['sites'] += ST['sites']
        finally:
            sys.settrace(None)
    except Exception as e:
        st['err'] = repr(e)[:120]
    results[rel] = st
    if st['reject'] or st['err']:
        print('%-64s eval=%-5d reject=%-4d fire=%-3d %s' % (rel, st['eval'], st['reject'], st['fire'],
                                                            (st['sites'][:4] if st['fire'] else st['err'] or '')))

tot = {k: sum(r[k] for r in results.values()) for k in ('eval', 'reject', 'fire')}
print('SHARD TOTALS', tot, 'files=', len(results))
os.makedirs(os.path.dirname(OUT) or '.', exist_ok=True)
json.dump({'shard': [SHARD, NSHARDS], 'totals': tot, 'files': results},
          open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
