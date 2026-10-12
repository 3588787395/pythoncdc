# r67a reclaimed WIP — merged-block (clock_worker loss B) census, truncated at the agent turn cap

r67a hit the 150-turn subagent cap while tightening its own criterion ("two over-fire shapes are
visible; let me tighten the criterion to genuine join arity and a noise-stripped tail, then re-measure")
and never wrote its census doc. Recovered from `D:/Temp/r67/DELIVER/`:

* `CANDIDATE_r67a_region_ast_generator_onto_LANDED.py` — sha16 **17b73582864fbba0**, 3841979 bytes,
  BOM + all-CRLF + `py_compile` OK (re-verified by me), based on the plain landed bytes
  `20fa73b4e8231f0f`.
* `CANDIDATE_r67a_region_ast_generator.py` — 3851843 bytes, left on the agent's own earlier base.

**Measured by me in my mirror** (`D:/Temp/r30chk`, restored and `cmp`-proved to the landed bytes right
after): panel index 12 → `realtime_event_source` **12/13 held**, and
`allwin_r63.py clock_worker` reads `len orig=1424 prod=1311 delta=-113 hunks=7` — i.e. **the landed
shape unchanged**: none of its hunks fired on this unit. So it is not a co-requisite, it is an unfinished
criterion, and it is kept only so the next dispatch starts from its text instead of from zero.

What the retry must do differently:
1. Base on `c4a934d595200c84` (M1+P1+P2), because loss (B) — `self.before_trading_date = now_date`
   `@6778..@6782`, the merge block of `IfRegion condition_block=@6690..@6700(4) then=[6702] else=[]
   merge=@6778..@6782(3)` emitted at the product's `@9170` instead of at the join — is only visible in
   that residual; on plain landed bytes it is buried under the other 107 instructions.
2. Decide the join-arity criterion by `compile()` on small shapes before touching the generator, the way
   §48/§49 settled the broker unit in two commands instead of three guesses.
3. Keep `ipo_stocks_order` and the six duplicated canaries as the no-fire witnesses.
