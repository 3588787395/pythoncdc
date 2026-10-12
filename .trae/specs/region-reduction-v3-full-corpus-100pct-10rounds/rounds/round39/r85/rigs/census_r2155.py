"""R21-55 population census (read-only, BEFORE any edit to the pipeline).

Signature under test: at the analyzer's ternary consumption-point guard
(`region_analyzer.py:26138-26141`, `[R47 消费点守卫]`) a candidate is rejected when
`merge_block is None and value_target is None and has_jump_forward_skip is False`.
For such a rejection, would the diamond's join be recoverable from pure
successor/predecessor structure?

    _r2155_diamond_join(tb, fb) is the predicate that will be mounted in the analyzer.

Counting rule (state this, do not cite bare numbers):
  EVAL_REACHED = executions of the guard statement (line 26138) by `_detect_ternary_pattern`
  REJECT       = executions of its body (line 26141), i.e. the candidate was declined
  FIRE         = a REJECT whose true/false value blocks satisfy the predicate
One FIRE per (code object, condition-block) is counted once even if the same block is
re-examined by several passes.

usage: python -X utf8 work/census_r2155.py <out-dir> [rel-pyc ...]   (default: PANEL_20files.txt)
"""
import hashlib
import json
import os
import sys
from collections import defaultdict

MIRROR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, MIRROR)

REPO = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main"
SP = os.path.join(REPO, "site-packages")

OUTDIR = sys.argv[1]
rest = sys.argv[2:]
if rest:
    FILES = rest
else:
    FILES = [l.strip() for l in open(os.path.join(MIRROR, 'PANEL_20files.txt'), encoding='utf-8')
             if l.strip()]

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
import core.cfg.region_analyzer as an
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator

ANALYZER_FILE = os.path.normcase(os.path.abspath(an.__file__))
GUARD_LINE = 26138
REJECT_LINE = 26141

NOISE_OPS = an.NOISE_OPS if hasattr(an, 'NOISE_OPS') else frozenset({'NOP', 'CACHE', 'EXTENDED_ARG'})
JUMP_OPS = frozenset({'JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'})
COND_JUMP_OPS = frozenset({
    'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_NONE',
    'POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_BACKWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_TRUE',
    'POP_JUMP_BACKWARD_IF_NONE', 'POP_JUMP_BACKWARD_IF_NOT_NONE',
    'JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP', 'POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE'})
HANDLER_FIRST_OPS = frozenset({'PUSH_EXC_INFO', 'WITH_EXCEPT_START'})


VARIANT = os.environ.get('R2155V', 'A').upper()
_PRODUCER_PREFIX = ('LOAD_', 'BUILD_', 'PUSH_')
EXC_ENTRY = ('PUSH_EXC_INFO', 'WITH_EXCEPT_START')


def _r2155_diamond_join(cfg, true_block, false_block):
    """Candidate analyzer-side criterion (verbatim what the patch will install)."""
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


STATS = defaultdict(lambda: {'eval': 0, 'reject': 0, 'fire': 0, 'fire_sites': [], 'rejects': []})
_cur = {'file': None, 'co': None, 'seen': set()}


def _step_factory(st):
    def step(frame, event, arg):
        if event == 'line':
            ln = frame.f_lineno
            if ln == GUARD_LINE:
                st['eval'] += 1
            elif ln == REJECT_LINE:
                st['reject'] += 1
                tb = frame.f_locals.get('true_block')
                fb = frame.f_locals.get('false_block')
                cfg = frame.f_locals.get('self').cfg
                key = (cfg.name, getattr(frame.f_locals.get('block'), 'start_offset', None))
                j = _r2155_diamond_join(cfg, tb, fb) if tb is not None and fb is not None else None
                st.setdefault('rejects', []).append('%s:@%s(t@%s,f@%s)' % (
                    cfg.name, getattr(frame.f_locals.get('block'), 'start_offset', '?'),
                    tb.start_offset if tb else '?', fb.start_offset if fb else '?'))
                if j is not None and key not in _cur['seen']:
                    _cur['seen'].add(key)
                    st['fire'] += 1
                    st['fire_sites'].append('%s:@%d(t@%d,f@%d->join@%d)' % (
                        cfg.name, key[1], tb.start_offset, fb.start_offset, j.start_offset))
            return step
        return step
    return step


def dispatch(frame, event, arg):
    if event != 'call' or os.path.normcase(frame.f_code.co_filename) != ANALYZER_FILE:
        return None
    if frame.f_code.co_name != '_detect_ternary_pattern':
        return None
    st = getattr(_tls, 'st', None)
    if st is None:
        return None
    return _step_factory(st)(frame, event, arg)


# The per-code-object analysis runs in worker threads, so the trace function must be
# installed per analyze() call rather than once on the main thread.
import threading
_tls = threading.local()

orig_analyze = RegionAnalyzer.analyze
def analyze(self, *a, **kw):
    _tls.st = getattr(_tls, 'st', None)
    sys.settrace(dispatch)
    try:
        return orig_analyze(self, *a, **kw)
    finally:
        sys.settrace(None)


RegionAnalyzer.analyze = analyze


results = {}
for rel in FILES:
    pyc = os.path.join(SP, rel.replace('/', os.sep))
    if not os.path.exists(pyc):
        print('MISSING', rel)
        continue
    st = STATS[rel]
    _tls.st = st
    _cur['seen'] = set()
    mod = load_pyc_file_v2(pyc)
    code = mod.code.get() if hasattr(mod.code, 'get') else mod.code
    if hasattr(code, 'to_python_code'):
        code = code.to_python_code()
    cfg = build_cfg(code)
    sys.settrace(dispatch)
    try:
        gen = RegionASTGenerator(cfg, top_level_code=code if code.co_name == '<module>' else None)
        gen.generate()
    finally:
        sys.settrace(None)
    print('%-62s eval=%-5d reject=%-4d fire=%-3d %s' % (
        rel, st['eval'], st['reject'], st['fire'], st['fire_sites'][:6]))
    results[rel] = dict(st=st, eval=st['eval'], reject=st['reject'], fire=st['fire'],
                        sites=st['fire_sites'])

os.makedirs(OUTDIR, exist_ok=True)
tot = {'eval': 0, 'reject': 0, 'fire': 0}
for rel, r in results.items():
    tot['eval'] += r['eval']
    tot['reject'] += r['reject']
    tot['fire'] += r['fire']
print('TOTALS', tot)
with open(os.path.join(OUTDIR, 'census_r2155.json'), 'w', encoding='utf-8') as f:
    json.dump({'totals': tot,
               'files': {k: {'eval': v['eval'], 'reject': v['reject'], 'fire': v['fire'],
                             'sites': v['sites'], 'rejects': v['st']['rejects'] if 'st' in v else []} for k, v in results.items()}},
              f, ensure_ascii=False, indent=1)
