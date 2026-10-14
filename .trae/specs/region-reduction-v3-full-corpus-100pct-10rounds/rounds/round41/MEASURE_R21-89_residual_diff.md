# MEASURE R21-89 - the residual on clock_worker, classified as text-only versus structural

Measured 2026-10-14 07:43 by the orchestrator, diffing the unit body of the current best arm against the
byte-identical `13/13` oracle.

- Product: `D:/Temp/r91m/out/rt_r113_47d44ec51fa325c5.py` (analyzer `996a1b1acf143458` = `[R21-77-F5]`,
  generator `47d44ec51fa325c5` = `[R21-88]`), rig reading `ours=256`, `DELTAS instrs=-25 back=+0 jsites=-4`,
  `indeg-equal=False`, judge `12/13`, zero collateral.
- Oracle: `rounds/round41/GOLD_realtime_event_source_PROOF.py`, 254-line `clock_worker` body,
  `hunks=0 / instrs=+0 / back=+0 / jsites=+0 / indeg-equal=True / 13/13`.

`gold=256-2` lines, `delta=+2`. Six differences remain, and they are **not** equally load-bearing:

## Text-only, instruction-equivalent - do not spend an arm on these

| hunk | gold | product | why it cannot move the judge |
|---|---|---|---|
| `@@ -176,6 +176,6 @@` (two tests) | `if (A and B) or C:` | `if A and B or C:` | `A and B or C` parses to exactly `(A and B) or C`; same AST, same bytecode |
| `@@ -220,3 +220,3 @@` | `return` | `return None` | both emit `LOAD_CONST None; RETURN_VALUE` |

This is the standing rule that a text change is not unit movement, applied in the defensive
direction: an arm that "fixes" only these buys nothing and risks the parity it already has.

## Structural residual A - a swallowed guard plus a mis-attached else, inside the `@7164` or-chain arm

`@@ -194,12 +194,12 @@`. Gold:

```
if (now_date > self.pre_before_trading_date and ...) or self.pre_before_trading_date == ...:
    if now_date != self.first_run_date:
        system_log.debug('获取重登信号量')
        if login_semaphore.acquire(timeout=LOGIN_TIMEOUT * 60) is False:
            system_log.error(...)
            self.event_queue.put((dt, EventEnum.SYSTEM_EXIT))
            return None
    self.event_queue.put((dt, EventEnum.PRE_BEFORE_TRADING_START))
    self.pre_before_trading_date = now_date
```

Product: the test `if now_date != self.first_run_date:` is **absent**, its two siblings are hoisted one
level, and the arm continuation became the `else:` of `acquire(...) is False`. So one guard block is
consumed without emitting its statement, and the sequential continuation is re-parented as an else arm.

## Structural residual B - the ladder's first leg becomes `else:`, a later flat leg nests, and a trailing `else: return None` appears

`@@ -238,3 +238,3 @@` and `@@ -245,8 +245,10 @@`:

```
gold:   elif check_trading_time(am_open, am_close, pm_open, pm_close, pm_over, ...):   product: else:
gold:   elif now_date == self.before_trading_date and now_date > self.after_trading_date
             and delay_after_trading >= now_time >= after_trading:                      product: nested if inside the previous else body
gold:   else:  (loop-tail sequential)                                                  product: else: return None  at an outer level
```

So the inherited ladder loses the `elif` identity of its first leg, flattens a second leg into nesting, and
materialises a terminal `return None` the oracle does not have at that position.

## Structural residual C - one level of dedent in the holiday arm

`@@ -184,5 +184,5 @@`: gold keeps `if holiday_not_do_before == '0': ... self.before_trading_date = now_date`
inside the preceding `try:`-sibling block; the product dedents both by one level. Decide by the oracle CFG
whether this is the same walk-coverage cause as A (it presents the same signature: statements emitted at
the arm level instead of the nested level).

## Route taken

Ticket **R21-89** was dispatched twice: r114a never created its mirror (no `D:/Temp/r114`, no
notification of work) so that attempt is recorded as never started, not as failed; r115a carries the same
ticket with this classification as its starting evidence, building on `[R21-88]` rather than on the
cancellation-parity `[R21-86]`, and with the excluded-shape list from addenda 1-15 attached.

Bar unchanged: from `instrs=-25, jsites=-4, ours=256` both instruction metrics must move toward 0 with
`back=+0` kept and `ours` approaching 254 without overshoot; then the nine collateral files byte-identical,
panel 20 by index unchanged, ROOT-joined 402 sweep `CHANGED={realtime_event_source.pyc}`, and **judge
`13/13` is the only flip**.

## Arithmetic attribution of the -25, measured 08:15 on the same arm

Two readings of the same unit body were scored side by side after the classification above:

| arm | ours | instrs | back | jsites | hunks | judge | collateral |
|---|---|---|---|---|---|---|---|
| [R21-88] base `47d44ec51fa325c5` | 256 | -25 | +0 | -4 | 8 | 12/13 | none (broker, klinedata, quote, real_quote, quotation, order_api, replace_utils, function, handlers all byte-identical) |
| r115a in-flight `301e491d4da74670` (23:15 snapshot, not a verdict) | 244 | -96 | +0 | -7 | 8 | 12/13 | broker CHANGED |

The base reading decomposes: two extra lines of text (`ours=256` against 254) while **25 instructions are missing**. Residual A removes one small guard (`if now_date != self.first_run_date:`, a compare plus a conditional jump, roughly three to five instructions). Residual B removes an entire test expression: the gold leg `elif check_trading_time(am_open, am_close, pm_open, pm_close, pm_over, self._engine.config.strategy.frequency, now_time)` is replaced in the product by a bare `else:`, so the whole call chain - `LOAD_GLOBAL check_trading_time`, seven argument loads including a two-level attribute access, `CALL`, and the conditional jump that the `else:` no longer needs - disappears. That accounts for the bulk of the -25, which makes **residual B the dominant instruction loss and residual A mostly a control-flow-shape loss**. Residual C (the dedent) changes nesting, not instruction count.

Consequence for the remaining work, stated as a priority rather than a guess: a rule that restores the dropped ladder condition closes most of the instruction gap and is the only candidate to make `indeg-equal` flip, because a `POP_JUMP_FORWARD_IF_FALSE` whose target is an `else:` body versus an `elif` test changes the in-degree of exactly the blocks the judge compares. The `+2` lines of overshoot are the nested `if`/`if` decomposition of the following leg, so the same rule should also flatten that leg rather than nest it.

Also worth keeping: the in-flight r115a state moved `ours` the other way (244, below the oracle) with `instrs=-96` and a broker change, i.e. its current shape removes more than it restores - a progress reading, not a verdict, recorded so the next hand does not mistake a falling `ours` for progress. `[[feedback-text-change-is-not-unit-movement]]` in force: `ours` approaching 254 from either direction is not the metric, `instrs` plus `jsites` plus the judge are.

Compliance state at this moment: repo `core/` clean at landed bytes `1471c92eca157e46` / `566ff5c502276e48`, `origin/rr-v3r01-f557fd` = `31e590c9` with `unpushed=0` verified by fetch plus `rev-list`, corpus 6616/6617 (99.9849 percent), 401/402 files, gate label 41 unconsumed, objective not achieved.
