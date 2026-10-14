# R21-32 — broker `_process_order` / `_process_cancel_order`: a terminator is emitted BEFORE the rest of its own suite

The two biggest losses in the corpus, and they are not "missing analysis" — the text is there and the
compiler deletes it. Measured read-only on the sealed gate-31 bytes.

## 0. What the emitted product actually says

`site-packages/IQEngine/plugins/plugin_system_trade/trade_live_brokerOK.py:423`

```python
def _process_order(self, engine):
    engine.set_engine(engine)
    while len(self.open_orders) > 0:
        if self.trade_status in (TRADE_STOP, TRADE_DELETE):
            system_log.debug('交易状态异常：%s，撤销委托' % self.trade_status)
            continue
        break                                   # <-- 424 instructions follow this, unreachable
        try:
            amount = order._amount
            ...
```

`…OK.py:524`

```python
def _process_cancel_order(self, engine):
    engine.set_engine(engine)
    while len(self.pending_cancel_orders) > 0:
        if order in self.orders:
            break
        strategy_log.error(_('当前订单状态不支持撤单'))
        continue                                # <-- and here, the rest of the body is unreachable
        entrust_no = order.entrust_no
        ...
```

CPython ≥3.10 dead-code-eliminates statements after a terminator in the same suite, which is exactly why the
diffs look like content loss rather than relocation:

| unit | sealed shape | note |
|---|---|---|
| `_process_order` | `len 507/42 delta=-465 hunks=4 landings=1` | `hunk3` alone deletes 424 instructions `@@470..@3126` and inserts 1 |
| `_process_cancel_order` | `len 333/40 delta=-293 hunks=3 landings=0` | same class, `continue` placed ahead of the body |

The source-level claim is therefore **not** "the body is missing from the AST" — it is that the body is
attached as a *sibling after* a `break`/`continue` instead of being the arm's continuation. The two
statements that must be re-parented are visible above.

## 1. Start from the banked partial — do not re-invent it

`rounds/round25/CANDIDATE_r25b_dead_suite_region_ast_generator.py` is the registered attempt: its continue
re-entry pad criterion at `_process_if_blocks` (base ~:25709–25750, 42 lines) cut
`_process_order −465 → −59` and `_process_cancel_order −293 → −30` with **zero regressions but zero flips**,
so it was not installed and the ledger calls the surviving hunk "the try/finally ordering".

So this ticket's real target is the residual −59 / −30, not −465 / −293. Sequence you must follow:
1. Re-anchor that candidate onto the current bytes with `D:/Temp/t31_hunkpick.py <old_base> <new_base>
   <candidate> <out> <hunk_ids…>` — it applies a subset of a candidate's hunks onto a moved base by content
   anchors and asserts a unique anchor hit. Its base is gate-24-era bytes; today's generator is
   `37d9fecb893704ac` (+~1000 lines since). Expect anchor ambiguity here; resolve it by reading the two
   candidate contexts, do not force it.
2. Re-measure both units with it (they should land near −59 / −30). If they do not, report that the banked
   partial no longer reproduces and why — that is a real finding, not a nuisance.
3. Then attack the remainder. The ledger says it is the try/finally ordering inside the same suite, which
   matches what the emitted text shows (`break` then a bare `try:` with no `finally`).

## 2. Constraints that already killed attempts here

- A **landing** criterion is unexecutable: the generator emits an AST that is then `compile()`d, so nothing
  can set a jump operand. Fix the construct, or hand the analyzer-side declaration back as its own ticket.
- Bulk claim/ownership widening on this file produced zero flips before (T12-11 style, and R21-B7's pair
  where the analyzer half changed ZERO of 14 products because the generator half already routed the block).
- The `while len(...) > 0:` wrapper interacts with landed R21-14 (`_r2114_wrapper_is_sequential_loops`,
  `_r2114_defer_to_unemitted_sibling_loop`) and R21-B2 (empty-body `while …: pass` declared as a
  `LoopRegion`). Measure with those bytes as they are; do not revert them to make your criterion fire.
- `break`/`continue` placement is the trap that makes this unit look enormous: verify the EMITTED bytes and
  the dead-code consequence, never the intended tree.

## 3. Acceptance

- Both units must reach `delta=0 hunks=0 landings=0 judge_diff=False` and be named Equal by the judge →
  broker **121 → 123/128** (two unit flips; the file has seven mechanisms so this is not a file flip).
  One unit only is still a CANDIDATE; report which.
- 20-file panel with zero decreases: `python -X utf8 D:/Temp/t30/panel14.py <root> <tag> 0 20` — quotation
  153/153, quote 91/92, klinedata 64/64, handlers 29/30, wizard 58/58, trade_info_utils 40/41, api_base
  28/28, real_quote 45/45, strategy 27/27, order_api 37/37, broker 121/128, matcher 17/17,
  realtime_event_source 12/13, risk 43/43, canaries `arg_checker`×3 (49/39/43) and `profiler_func`×3
  (17/15/18). The canaries are mandatory because a −6-unit merge passed the old 14-file panel at gate 31.
- Report the other five broker units unchanged: `_sync_worker −3/5/6` (see NOTE_R21-31 — it is a
  relocation, not a loss), `_trade_status_handle −3/3/2`, `etf_purchase_redemption −12/5/0` (R21-27, live
  with r56a), `ipo_stocks_order −1/1/3` (R21-28), `get_ipo_stocks 0/0/1` (live with r54a). Two of those are
  being worked in this same file right now — keep your hunks clear of theirs and say where they sit.

## 4. Hygiene and deliverables

Repo READ-ONLY, no git write commands. Mirror: copy `pycdc.py core parsers utils bytecode scripts` (exclude
__pycache__) to `D:/Temp/r58/wt` plus `.trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/unit_diff.py`
at the same relative depth; verify sealed generator `37d9fecb893704ac` / analyzer `35e227ac3e7b25af`; prove
fidelity by regen + `cmp` against the committed `trade_live_brokerOK.py` before measuring. Only
`core/cfg/region_ast_generator.py` may change. `python -X utf8`, never `PYTHONIOENCODING`; byte-level
CRLF-preserving patches; nothing over 300 s; judge with `pyc_verify.py single <abs .pyc> --source <product>`;
ablation over print markers; `cmp`-prove any probe inert per target. Deliver `FIX_R21-32.md` (0–7, including
the re-anchored banked partial's re-measurement in section 2) plus a whole
`CANDIDATE_region_ast_generator.py` with its `sha256sum | cut -c1-16`. Never report a number you did not
observe.
