# -*- coding: utf-8 -*-
"""R67 fix1: build a DEBUG arm (J2 + a frame dump at the detector) so the exact
conjunct that excludes the v3 site is read off, not guessed.

  python -X utf8 mkspec_dbg.py            -> specs/cand_r67_j2dbg.json
  python -X utf8 h62.py build --spec=specs/cand_r67_j2dbg.json --dst=j2dbg
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
DBG = (
    "                    if region is None:\n"
    "                        import sys as _s\n"
    "                        print('[J2DBG] cfg=%s blk=%s blocks_off=%s blocks_n=%s'\n"
    "                              ' _reg=%s@%s entry=%s parent=%s loop=%s@%s'\n"
    "                              ' loopexit=%s cond_is_blk=%s entry_is_blk=%s'\n"
    "                              % (getattr(self.cfg, 'name', '?'),\n"
    "                                 getattr(block, 'start_offset', None),\n"
    "                                 sorted(getattr(b, 'start_offset', -1) for b in blocks),\n"
    "                                 len(blocks), type(_region).__name__,\n"
    "                                 getattr(_region.entry, 'start_offset', None),\n"
    "                                 type(_region.entry).__name__,\n"
    "                                 getattr(_region.parent, 'region_type', None),\n"
    "                                 type(self._current_loop).__name__,\n"
    "                                 getattr(self._current_loop, 'start_offset', None)\n"
    "                                 if self._current_loop else None,\n"
    "                                 getattr(getattr(self._current_loop, 'exit', None),\n"
    "                                        'start_offset', None) if self._current_loop else None,\n"
    "                                 getattr(_region, 'condition_block', None) is block,\n"
    "                                 _region.entry is block), file=_s.stderr)\n"
)
REPL = ANCHOR + DBG + "                    self._generating_regions.add(_rid)\n"
u = io.open(LANDED, encoding='utf-8-sig', newline='').read().replace('\r\n', '\n')
assert u.count(ANCHOR) == 1
io.open('specs/cand_r67_j2dbg.json', 'w', encoding='utf-8').write(json.dumps(
    {'name': 'cand_r67_j2dbg', 'file': 'core/cfg/region_ast_generator.py',
     'edits': [{'anchor': ANCHOR, 'repl': REPL}],
     'note': 'R67 fix1 debug probe only, never lands'}, ensure_ascii=False, indent=1))
print('wrote specs/cand_r67_j2dbg.json, inserted lines =', REPL.count('\n') - ANCHOR.count('\n'))
