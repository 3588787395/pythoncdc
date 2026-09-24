# Round 62 Batch 2 diagnosis (READ-ONLY)

Landed bytes verified locally: `core/cfg/region_ast_generator.py` sha256 prefix
`fa0808ca3766b5150dcf` (3058524 bytes), `core/cfg/region_analyzer.py` prefix `eab9c782a0b646f52781`.
Targets: quote.pyc (d11), real_quote.pyc (d5), main.pyc (d4), quote_handler.pyc (d2).

## 0. Status log (append-only)

- [setup] `run --arm=landed` started on targets.txt -> dump/landed.jsonl (baseline for this round;
  FACTS is from the r61 index and must be re-verified on the landed bytes).

## 1. Baseline on landed bytes — REPRODUCED EXACTLY

`run --arm=landed` on targets.txt -> `dump/landed.jsonl`:
quote.pyc 70/81 (11 mism), real_quote.pyc 39/44 (5), main.pyc 29/33 (2 mism),
quote_handler.pyc 55/57 (2). All 22 mismatch names/deltas match FACTS(r61) verbatim,
so Fix1/Fix2 landing did not move this batch. Log: `logs/landed.log`, full detail
incl. missing/extra + first_diff: `dump/diff_landed.json` (`probe_diff.py`).

### main.pyc self-consistency (asked explicitly)

`missing_in_decomp = ['<dictcomp>', '<lambda>']`, `extra_in_decomp = []` -> **not a stale
index**: the two nested code objects are genuinely absent from the product, and nothing
extra was invented. 33 total = 29 matched + 2 mismatched + 2 missing. The two missing
scopes belong to the *same two* mismatched functions:
`get_server_ip_info.co_cellvars = ('local_server_shard','same_shard_server_info')` and
`get_same_shard_server_ip_info.co_cellvars = ('local_server_shard',)`, while the product
has `co_cellvars = ()` and emits `STORE_FAST` where the original has `STORE_DEREF`.
So the deficit-4 is one root cause with two faces: a **contiguous region of the outer
`for` body (the statements between the inner `for` and the terminal `return`) is
silently deleted**, and that region is exactly what contained the dict-comp + the
`key=lambda` closure. Product evidence (`build_landed/IQCommon__common__mainOK.py`
lines 389-423 / 424-460): after the inner `for server_info ...` loop the body jumps
straight to `return {... 'index': new_index ...}`; `new_index` / `same_shard_servers_num`
degrade to LOAD_GLOBAL because their STOREs were deleted. **These are the highest-value
targets of the batch** (2 index slots each, one region-level cause).

## 1b. first_diff taxonomy (22 functions) — from `logs/typediff.txt`
(instructon-level difflib alignment, jumps compared by opcode only)

- **F-A dangling-TOS / short-circuit statement loss** (region-owned, IN SCOPE):
  `get_kline_local` loses `end_time = int(end[0:8] + (end[8:12] or '1530'))` 5x
  (-78; 2 of the 5 leave the trace `"""1530"""` as a bare expression statement,
  3 leave nothing). Signature statement = `JUMP_IF_TRUE_OR_POP` whose merge block is
  also the elif-branch tail block ending in `JUMP_FORWARD` to the chain exit.
- **F-B whole contiguous region deleted, no trace**: main.pyc x2, `get_price`,
  `load_get_price`, `load_bars_from_hundsun` tails.
- **F-C if/elif chain relocated after a terminal RETURN (becomes dead code)**:
  `get_individual_data`, `get_real_from_zeromq` (`flag==1/-1` logging chain moved to
  the function tail past `RETURN_VALUE`).
- **F-D f-string printer family (OUT of region ownership, prior-round falsified
  suppression patches)**: `check_limit`, `initImagedata`, `get_price`,
  `load_get_price`, `load_bars_from_hundsun`, `get_real_from_zeromq` prologue log
  statements (`LOAD_CONST 'self调用函数X，参数为：stocks=stocksNone'` collapse).
- **F-E layout-only (already counted matched by the verifier)**: EXTENDED_ARG/NOP,
  jump-target-only, code-object-address reprs.

## 2. Repro status

(pending)

## 5. Candidates + measured A/B

(pending)

## 6. GO / NO-GO

(pending)
