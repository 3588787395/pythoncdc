# -*- coding: utf-8 -*-
"""R67 fix1: J1 (diag1's rejected wide guard) + a print at every guard HIT, so the
frame-local readings of the firing sites can be compared directly.

  python -X utf8 mkspec_j1dbg.py
  python -X utf8 h62.py build --spec=specs/cand_r67_j1dbg.json --dst=j1dbg

Diagnostic arm only; never lands.
"""
import io
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
LANDED = r'F:/Downloads/pythoncdc-main/core/cfg/region_ast_generator.py'
ANCHOR = (
    "            _region = self.region_analyzer.get_entry_region_for_block(block)\n"
    "            if isinstance(_region, RegionASTGenerator._STRUCTURAL_REGION_TYPES):\n"
    "                _rid = id(_region)\n"
    "                if (_rid not in self._generated_regions\n"
    "                        and _rid not in self._generating_regions):\n"
)
BODY = (
    "                    if (region is None and self._current_loop is not None\n"
    "                            and getattr(_region, 'parent', None) is None):\n"
    "                        _CL = self._current_loop\n"
    "                        _s = __import__('sys')\n"
    "                        _off = lambda b: getattr(b, 'start_offset', None)\n"
    "                        _offs = lambda bs: sorted(\n"
    "                            [_off(b) for b in (bs or [])] or [])\n"
    "                        print('[J1HIT] cfg=%s blk=%s blocks=%s | R=%s e=%s cb=%s mb=%s'\n"
    "                              ' x=%s nb=%s then=%s else=%s par=%s | L=%s e=%s h=%s'\n"
    "                              ' x=%s nb=%s bodyhas=%s elsehas=%s blkgen=%s'\n"
    "                              % (getattr(self.cfg, 'name', '?'), _off(block),\n"
    "                                 _offs(blocks), type(_region).__name__, _off(_region.entry),\n"
    "                                 _off(getattr(_region, 'condition_block', None)),\n"
    "                                 _off(getattr(_region, 'merge_block', None)),\n"
    "                                 _off(getattr(_region, 'exit', None)), len(_region.blocks),\n"
    "                                 _offs(getattr(_region, 'then_blocks', None)),\n"
    "                                 _offs(getattr(_region, 'else_blocks', None)),\n"
    "                                 type(getattr(_region, 'parent', None)).__name__,\n"
    "                                 type(_CL).__name__, _off(_CL.entry),\n"
    "                                 _off(getattr(_CL, 'header_block', None)),\n"
    "                                 _off(getattr(_CL, 'exit', None)), len(_CL.blocks),\n"
    "                                 block in _CL.blocks,\n"
    "                                 block in (_CL.else_blocks or []),\n"
    "                                 block in self.generated_blocks), file=sys.stderr)\n"
    "                        continue\n"
)
REPL = ANCHOR + BODY + "                    self._generating_regions.add(_rid)\n"
u = io.open(LANDED, encoding='utf-8-sig', newline='').read().replace('\r\n', '\n')
assert u.count(ANCHOR) == 1
io.open('specs/cand_r67_j1dbg.json', 'w', encoding='utf-8').write(json.dumps(
    {'name': 'cand_r67_j1dbg', 'file': 'core/cfg/region_ast_generator.py',
     'edits': [{'anchor': ANCHOR, 'repl': REPL}],
     'note': 'R67 fix1 J1 hit tracer, diagnostic only'}, ensure_ascii=False, indent=1))
print('wrote specs/cand_r67_j1dbg.json, inserted lines =', REPL.count('\n') - ANCHOR.count('\n'))
