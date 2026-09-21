# -*- coding: utf-8 -*-
# R24 battery case b03_cc_ternary_at_head
# SHAPE: a chained-compare conditional-expression assignment sitting at the TOP of a
#        function body -- i.e. the region entry block *is* the ternary header.  This is
#        the shape R23-era analysis said the predicate must keep working, because the
#        ternary header there is the region entry (can_be_ternary_header is reached with
#        block is self.entry), NOT a mid-region chained-compare block.
# EXPECTED: `data_count = int(data_count) if ... else 200` emitted as one statement.
# ACTUAL-HEAD: FAIL official 1/2 -- `get_cache_like` comes out 38 -> 36 instructions and the
#              ternary text is absent, i.e. this top-of-body shape is broken on HEAD by a
#              defect R24-A was never aimed at.
# ACTUAL-CAND: FAIL the same way, product sha identical to HEAD (measured 3f84535cb731b5a4 on
#              both cores).  Value of this case = G4 byte-identity, not an OK verdict.
# MARK: PRED_R24A_STABLE
# MUST_CONTAIN: data_count = int(data_count) if 0 < int(data_count) <= 200 else 200
def get_cache_like(data_count, symbols):
    data_count = int(data_count) if 0 < int(data_count) <= 200 else 200
    if isinstance(symbols, str):
        symbols = [symbols]
    else:
        symbols = list(symbols)
    return data_count, symbols
