"""[B75b] 取证：pre-pass _b75_consume_arm_return_copies 判定链逐步回放。"""
import sys

sys.path.insert(0, r'F:\Downloads\pythoncdc-main')

import marshal

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator

PYC = r'F:\Downloads\pythoncdc-main\test_repros\round10\r10_15_global_hosts.pyc'


def load_code(pyc):
    with open(pyc, 'rb') as f:
        data = f.read()
    return marshal.loads(data[16:])


code = load_code(PYC)
fn_code = None
mod_code = code
for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'g_in_try_except':
        fn_code = c
        break

builder = CFGBuilder()
cfg = builder.build(fn_code)
analyzer = RegionAnalyzer(cfg, parent_code=None, top_level_code=None)
regions = analyzer.analyze()
print('=== regions ===')


def dump_region(r, depth=0):
    eb = getattr(r, 'entry_block', None) or getattr(r, 'entry', None)
    eo = eb.start_offset if eb is not None else '?'
    print('  ' * depth + f'{r.region_type.name}@{eo} blocks={sorted(b.start_offset for b in r.blocks)}')
    for ch in getattr(r, 'children', []) or []:
        dump_region(ch, depth + 1)


for r in regions:
    dump_region(r)

# 复刻 pre-pass 判定
print('=== pre-pass replay ===')
region = None
for r in regions:
    if getattr(r, 'has_finally', False):
        region = r
        break
if region is None:
    print('NO TryExceptRegion with finally')
    sys.exit(0)

_fb = getattr(region, 'finally_blocks', None)
print(f'region.blocks={sorted(b.start_offset for b in (region.blocks or ()))}')
print(f'try_blocks={sorted(b.start_offset for b in (region.try_blocks or ()))}')
print(f'finally_blocks={sorted(b.start_offset for b in (_fb or ()))}')
print(f'else_blocks={sorted(b.start_offset for b in (getattr(region, "else_blocks", None) or ()))}')
for _i, (et, en, hbs) in enumerate(getattr(region, 'except_handlers', None) or []):
    print(f'handler[{_i}] type={et} hbs={sorted(b.start_offset for b in (hbs or ()))}')
print(f'handler_entry_blocks={sorted(b.start_offset for b in (getattr(region, "handler_entry_blocks", None) or []))}')
print(f'cleanup_blocks={sorted(b.start_offset for b in (getattr(region, "cleanup_blocks", None) or ()))}')

_noise = ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')
_frame_tail = ('RERAISE', 'COPY', 'POP_EXCEPT', 'SWAP')
_exc_seq = []
for _fb_b in (_fb or ()):
    for _i in _fb_b.instructions:
        if _i.opname in _noise or _i.opname == 'PUSH_EXC_INFO':
            continue
        _exc_seq.append(_i.opname)
while _exc_seq and _exc_seq[-1] in _frame_tail:
    _exc_seq.pop()
print(f'_exc_seq={_exc_seq}')

_reserved = set(region.try_blocks or ())
_reserved |= set(_fb or ())
_reserved |= set(getattr(region, 'else_blocks', None) or ())
for _, _, _hbs in (getattr(region, 'except_handlers', None) or []):
    _reserved |= set(_hbs or ())
for _heb in (getattr(region, 'handler_entry_blocks', None) or []):
    _reserved.add(_heb)
for _cb in (getattr(region, 'cleanup_blocks', None) or ()):
    _reserved.add(_cb)
_region_blocks = set(region.blocks or ())
_other_try_blocks = set()
for _r in regions:
    if type(_r).__name__ == 'TryExceptRegion' and _r is not region:
        _other_try_blocks |= set(_r.blocks or ())

from core.cfg.region_analyzer import IfRegion  # noqa: E402

for cand in regions:
    if not isinstance(cand, IfRegion) or cand.entry is None:
        continue
    _cb = list(getattr(cand, 'blocks', None) or ())
    print(f'--- IfRegion@{cand.entry.start_offset} blocks={sorted(b.start_offset for b in _cb)}')
    if not _cb:
        print('    SKIP empty')
        continue
    _not_in = [b.start_offset for b in _cb if b not in _region_blocks]
    if _not_in:
        print(f'    SKIP blocks not in region.blocks: {_not_in}')
        continue
    _in_reserved = sorted(b.start_offset for b in _cb if b in _reserved)
    if _in_reserved:
        print(f'    SKIP blocks in _reserved: {_in_reserved}')
        continue
    _in_other = sorted(b.start_offset for b in _cb if b in _other_try_blocks)
    if _in_other:
        print(f'    SKIP blocks in other TryExceptRegion: {_in_other}')
        continue
    _cand_seq = []
    for _b in sorted(_cb, key=lambda b: b.start_offset):
        for _i in _b.instructions:
            if _i.opname in _noise:
                continue
            _cand_seq.append(_i.opname)
    while _cand_seq and (_cand_seq[-1] in ('RETURN_VALUE', 'RETURN_CONST')
                         or _cand_seq[-1] in _frame_tail):
        _cand_seq.pop()
    print(f'    _cand_seq={_cand_seq}')
    if len(_cand_seq) < len(_exc_seq) or _cand_seq[:len(_exc_seq)] != _exc_seq:
        print('    SKIP seq prefix mismatch')
        continue
    _terminals = [b for b in _cb
                  if b.get_last_instruction() is not None
                  and b.get_last_instruction().opname in ('RETURN_VALUE', 'RETURN_CONST')]
    print(f'    terminals={[b.start_offset for b in _terminals]}')
    if not _terminals:
        print('    SKIP no terminal')
        continue
    _preds = set()
    for _b in _cb:
        _preds.update(getattr(_b, 'predecessors', None) or ())
    _ext_preds = [p for p in _preds if p not in _cb]
    print(f'    ext_preds={sorted(p.start_offset for p in _ext_preds)}')
    if not _ext_preds:
        print('    SKIP no ext preds')
        continue
    _try_set = set(region.try_blocks or ())
    for _p in _ext_preds:
        _mi = [i for i in _p.instructions if i.opname not in _noise]
        print(f'    pred {_p.start_offset}: in_try={_p in _try_set} instrs={[i.opname for i in _mi]}')
    print('    => would PASS structural gates (guard replay needed for value tail)')
