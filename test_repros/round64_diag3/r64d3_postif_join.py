# -*- coding: utf-8 -*-
"""R64 diag3 repro D1 (v5): post-if join block over-claimed into a nested
IfRegion's else arm.  STATUS: reproduces the REGION over-claim, NOT the product
defect -- see NONE.md N3 at the bottom of this docstring.

Target morphology (trade_info_utils.trade_operation, original line 324):

    for items in ...:                       # loop header 654
        if items[0] in trade_id_list:       # 656  FALSE -> join block 1000
            if B: ...                       # 678 then=[690] merge=704
            if C: ...                       # 704 then=[716] merge=726
            if operation == 'delete':       # 726 merge=654 (loop header)
                ...; continue               # 738 rich back-edge block, key (1,22,738)
            elif D: ...                     # 874  else arm entry
                ...                         # 886 896 908 918
        write_info.append(items)            # 1000 join block, key (1,6,1000)

Collected set of the failing call _collect_branch_blocks(entry=874, merge=654)
is [874, 886, 896, 908, 918, 1000]: the join block 1000 is claimed by the
nested if's else arm because 656 reaches it with a conditional JUMP and the
W14-C reverse prune is gated on `not merge` (region_analyzer.py:26569).

Two measured facts about getting the over-claim into the region forest:
  (1) REQUIRED.  The join block must NOT be the LoopRegion's back_edge_block,
      otherwise the caller-side in-loop filter (region_analyzer.py:18291)
      removes it first.  Back-edge choice is max() over (no exc-epilogue ops,
      #non-jump instructions, start_offset) (region_analyzer.py:4088-4095), so
      the `continue` block must carry MORE statements than the join block --
      as in the real function ((1,22,738) vs (1,6,1000)).
  (2) NOT REQUIRED (hypothesis falsified here).  Extra sequential `if` levels
      inside the outer body do not matter: this 3-level clone and the earlier
      1-level clone BOTH produce the over-claim
      (IfRegion@118 else_blocks=[280,292,334,346,388] /
       IfRegion@38  else_blocks=[200,212,254,266,308])
      and BOTH still decompile 2/2 clean on the landed arm and on the j2 arm.

Conclusion: region_analyzer.py:26569's `not merge` conjunct is necessary but
NOT sufficient for the visible trade_operation symptom; the discriminating
step lives in region_ast_generator.py.  This file is kept as the negative
result, not as a passing repro.
"""
from io import StringIO

LOG = []


def probe_join(rows, tags, op, out, drop, buf):
    try:
        with buf:
            for r in rows:
                if r[0] in tags:
                    if r[1] is None:
                        r = (r[0], '')
                    if r[1] == '':
                        r = (r[0], '-')
                    if op == 'del':
                        drop.append(r)
                        LOG.append(r)
                        drop.append(r[0])
                        continue
                    if op == 'add':
                        out.append(r)
                    if op == 'mod':
                        drop.append(r)
                out.append(r)
            return len(out)
    except BaseException:
        return -1
