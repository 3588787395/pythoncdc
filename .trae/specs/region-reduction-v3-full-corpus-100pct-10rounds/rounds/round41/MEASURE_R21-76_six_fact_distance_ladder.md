# [R21-76] the last unit is a SIX-FACT conjunction — measured distance ladder to a byte-identical 13/13 oracle

r103a's oracle `GOLD_realtime_event_source_PROOF.py` judges **`status=success units=13/13`**, and its
`clock_worker` code object is **byte-identical to the original** (`co_code` equal, `consts` equal). So the target
text is nailed and the residual is fully expressible.

Platform certified first: analyzer `1471c92eca157e46` + generator `566ff5c502276e48`, repo `core/` byte-unchanged,
panel holds (`broker 128/128`, `function 15/15`, `replace_utils 9/9`, `quote 92/92`, `quotation 153/153`,
`order_api 37/37`).

**My brief's `+2 / 4-window` premise is falsified on this platform** (it belonged to the banked `675ec7af` base).
Measured: `allwin delta=-113, 7 hunks`; `win_r91 orig=1442 prod=1330 delta=-112, 15 windows`. Proven not a mirror
artifact and not caused by [R21-74] (the pre-74 generator `0f4c3898` gives the same -113, and broker drops to 127/128
there).

Ladder, one sub-fact per step, all six CFG-visible and all necessary:

| step | what moved | `delta` / hunks | judge |
|---|---|---|---|
| 0 | pipeline as landed | −113 / 7 | 12/13 Different control flow |
| 1 | restore the holiday block `@6690` | +13 / 5 | 12/13 |
| 2 | drop the spurious duplicated tail | −7 / 4 | 12/13 |
| 3 | fix the `@7164` or-chain + restore the swallowed `system_log.debug` | −2 / 2 | 12/13 |
| 4 | fix the `@6322`/`@6496` `is_holiday` or-chains | −3 / 1 | 12/13 |
| 5 | remove the spurious `while True:` wrapper | **0 / 0** | **still 12/13** |
| 6 | fold the `@8904` inner-if into its `elif` (fixes jump TARGETS `@8972`/`@8978`) | 0 / 0 | **13/13** |

**The step-5 result is the load-bearing measurement of the round**: a variant reached `delta=0, hunks=0` under both
opcode-text tools and the judge STILL failed it; only the two jump-target diffs flipped it. `allwin`/`win_r91` blank
jump operands, so they cannot see the last fact — the campaign's "instruction parity is not judge equivalence" trap,
now demonstrated on the final unit. Consequences: (a) no single predicate can flip `clock_worker`, so any one-rule
candidate is a zero-flip candidate under the project bar; (b) progress must be scored as distance to this oracle
text plus the judge line, never as `|delta|`; (c) the emitter-side "no landing channel" rule stands (the fix at step
6 was a *nesting* change in the AST, i.e. the ordering/nesting channel).

Do-not-re-open list for this unit: the `@7248` manufactured-jump framing (wrong base), refusal-only predicate C
(−269 collapse), R21-60 arm ordering, P2/D/E broad signatures.
