# TICKET_R21-52 — refuse the `inline_boolop_chains` fold from absorbing a `POP_TOP`-consumed member block (clock_worker's last defect)

Origin: my own measurement 2026-10-12 19:11, recorded in `ADJUDICATION_ROUND39_BANKED_NO_LANDING.md` §11.
Unit: `<module>.RealtimeEventSource.clock_worker` (`realtime_event_source.pyc`, file 12/13 ⇒ flip = 401/402 files).
Base to install: `rounds/round39/r75/CANDIDATE_r75a_r2146_AB_on_r74d_30a4d7827122e165.py` (whole
`region_ast_generator.py`); analyzer stays landed `f7d849e974904492`. My measurement of that base:
`delta=+2`, 2 windows, 7 landings, judge `status=failure units=12/13`, `changed files = 1`.

## The evidence, in the order I gathered it

1. Compiled the base's regenerated `realtime_event_source`, walked `dis.get_instructions()` and `co_lines()`.
2. Both residual `JUMP_FORWARD`s land on the **same** target, prod `@9206`:
   ```
   @9206 LOAD_DEREF self / @9208 LOAD_ATTR active / @9218 EXTENDED_ARG 7 / @9220 POP_JUMP_BACKWARD_IF_TRUE 5614
   ```
   i.e. line 216 = `while self.active:`'s condition re-test.
3. The two windows map to emitted source as:
   ```
   @7248 POP_JUMP_FORWARD_IF_FALSE -> 7254    line 249  if pre_before_trading <= now_time < pm_close or self.pre_before_trading_date == self.initial_trading_date:
   @7252 JUMP_FORWARD -> 9206                 line 250      pass
   @7578 STORE_ATTR pre_before_trading_date   line 259
   @7590 JUMP_FORWARD -> 9206                 line 259
   ```
   The `then` arm at line 249 is **empty (`pass`)** where the original carries
   `system_log.debug('获取重登信号量')`, and that same `debug()` call reappears **one arm later**, at emitted
   line 248, inside `elif now_date != self.first_run_date:`.
4. r78a's independent census (its `D` report) names the mechanism: the `inline_boolop_chains` fold absorbed the
   arm-entry block into the condition, `inline_blocks=[7248, 7270]`, so `@7270` — whose call result is consumed
   by `POP_TOP`, i.e. a **statement** — is no longer in the arm body.

## The rule to implement (identification-time, member-block-local, no offsets/names/thresholds)

The fold may absorb a member block **only if** the value that block pushes is consumed by the chain's own control
flow (the following conditional jump of the chain, i.e. it is a BoolOp *operand*). It must refuse to absorb a
member block whose pushed value is consumed by a `POP_TOP` before the chain's next conditional jump — such a
block is a discarded-expression **statement**, not an operand, and absorbing it silently deletes the statement and
re-parents the following code.

Where to look: `core/cfg/region_analyzer.py` — the chain is built into `_basic_inline_chains` (3 occurrences;
comment anchors at `:19364`, `:20420`, `:20858`, consumed at `:21406`, and the elif-chain merge at
`:23083`/`:23098`). Generator-side readers, all verified present: `region_ast_generator.py:921-933` (the
entry-region ibc test), `:16027-16040` (`_main_ibc = region.inline_boolop_chains.get(id(cond_block))`),
`:19760-19793` (elif-condition keys), and **`_inline_and_chain_exits_agree` at `:19452`** — which already exists
as the house way to *refute* an analyzer ibc `'and'` record (landed as part of `[R21-13]`, gate 29), so the natural
home for this rule is beside it rather than in the analyzer. Assert membership uniqueness before/after
(`two_owner`, `zero_owner`) — r78a's standard was `two_owner=186` unchanged.

## Why this is not a repeat of the closed axes

- `[R21-44]` conjunct ⑧ and its gated relaxation (`-274/5`, twice) refuse **whole sites** of the or-tail lift.
- `[R21-49]` (`+2 → -269`) refuses **whole chains**.
- `[R21-48]` suppressed the **filter** that deletes `IfRegion@7248` and patched a phantom `else` (`+3/+2/+3`).
- This rule edits **only which blocks a single fold may absorb**, per member block, from that member's own
  opcode/stack shape. Nothing before it changes the chain's `elif_final_else` (which is what made the two
  chain-level attempts catastrophic — that list is 44 blocks = the whole function tail).

## Acceptance bar (unchanged from the unit's other tickets)

`realtime_event_source` **13/13** (⇒ 401/402 files, corpus 6615/6617), with broker **126/128**, `quote.pyc`
**92/92**, `quotation.pyc` **153/153**, `order_api.pyc` **37/37** and no panel file decreasing. Below that ⇒ bank
with the killing numbers; a `delta` change is not progress (`|delta| ≤ 3` units judged `Different control flow`
four times today).

## Known cost of the surrounding shape, so nobody re-derives it

The two `JUMP_FORWARD → loop re-test` are the lawful consequence of r68a's elif-chain law (a whole `if/elif/else`
chain gets ONE end label): our flat chain's end label happens to be the `while self.active:` re-test, so every arm
tail must jump. Do **not** attack those jumps directly — fix the absorbed statement and re-measure; if the jumps
survive on a correct body, they become a nesting problem for `[R21-43]`'s family, which is a separate ticket.
