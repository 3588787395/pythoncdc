# -*- coding: utf-8 -*-
"""diag4 r67: instrument the CANDIDATE helper (read-only on repo; loads mirr_hcand) and
report, per try/except handler back-edge candidate, exactly which gate failed.
usage: python -X utf8 dbg_hc.py <pyc> [funcname]
"""
import io
import marshal
import os
import sys
import types

REPO = r'F:/Downloads/pythoncdc-main'
GATE = r'D:/Temp/opencode/r67gate/diag4'
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(REPO)
sys.path.insert(0, GATE + r'/mirr_hcand')
sys.path.append(REPO)
import pycdc  # noqa: E402
assert os.path.dirname(os.path.abspath(pycdc.__file__)).replace('\\', '/') == GATE + '/mirr_hcand'

from core.cfg.region_ast_generator import (RegionASTGenerator, BlockRole, TryExceptRegion,  # noqa: E402
                                           LoopRegion)

LOG = []
_orig = RegionASTGenerator._handler_backedge_is_explicit_continue


def patched(self, hb):
    role = self.region_analyzer.get_block_role(hb)
    loop = self._current_loop
    hdr = getattr(loop, 'header_block', None) if loop else None
    be = getattr(loop, 'back_edge_block', None) if loop else None
    last = hb.get_last_instruction()
    tgt = None
    if last is not None and getattr(last, 'argval', None) is not None:
        tgt = self.cfg.get_block_by_offset(last.argval)
    noise = ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP', 'POP_EXCEPT', 'COPY')
    dirty = [i.opname for i in hb.instructions if i.opname not in noise]
    r = _orig(self, hb)
    LOG.append(dict(hb=hb.start_offset, role=str(role), loop=(getattr(loop, 'entry', None) and
                                                               loop.entry.start_offset),
                    hdr=hdr and hdr.start_offset, back_edge=be and be.start_offset,
                    last=last and last.opname, tgt=tgt and tgt.start_offset,
                    gen=hb in self.generated_blocks, dirty=dirty, res=r))
    return r


RegionASTGenerator._handler_backedge_is_explicit_continue = patched

# also trace the handler-block loop entry conditions: which blocks are visited at all
_seen = []
_gen_try = RegionASTGenerator._generate_try


def gen_try_patched(self, region):
    ent = region.entry.start_offset
    hs = [(i, h[0], h[1], [b.start_offset for b in (h[2] or [])])
          for i, h in enumerate(getattr(region, 'except_handlers', None) or [])]
    _seen.append(('try@%s' % ent, hs, [b.start_offset for b in (region.handler_entry_blocks or [])]))
    return _gen_try(self, region)


RegionASTGenerator._generate_try = gen_try_patched

pyc = sys.argv[1]
name = sys.argv[2] if len(sys.argv) > 2 else None
out = pycdc.decompile_pyc(pyc)
if name:
    i = out.find('def %s(' % name)
    print(out[max(0, i - 200):i + 900] if i >= 0 else out[:1500])
else:
    print(out)
print('--- _generate_try calls:', _seen)
print('--- helper invocations:')
for e in LOG:
    print('   ', e)
