# Register: the region-generator signature validator was BLIND, not green (fixed + armed)

Measured 2026-10-11 00:30–00:35, orchestrator-side, while the round-31 crew was mid-flight.

## 1. What was found

`scripts/validate_region_generator_signatures.py` (guard: "每个区域类型有且只有一个主生成方法，防止补丁式编程")
opened its target with `encoding='utf-8'`, but `core/cfg/region_ast_generator.py` carries a UTF-8 BOM
(`ef bb bf` at offset 0). Every run therefore died before analyzing:

    语法错误: invalid non-printable character U+FEFF (region_ast_generator.py, line 1)

The BOM is **not** something this round introduced: the pristine pre-landing backup of the gate-29 bytes
(`D:/Temp/r150/deliver_backup/fd0e4c4d73cf5efc_region_ast_generator.py`) starts with the same `ef bb bf`,
as do all four engineers' candidate files. So the guard has been unreadable against the campaign's main
file for as long as that file has had the BOM.

No test called it (`grep -rln validate_region_generator_signatures tests scripts` → no hits), so the
blindness produced no signal anywhere. A guard that cannot parse its target is not a passing guard.

## 2. What the guard actually says now

With the read fixed to `utf-8-sig`, the verdict on the two sealed states is **identical**:

| target | sha16 | verdict |
|---|---|---|
| gate-29 bytes (pristine backup) | `fd0e4c4d73cf5efc` | 14 errors / 6 warnings |
| gate-30 bytes (landed triple) | `7d336164eff5bf65` | 14 errors / 6 warnings |

So gate 30's +296 lines contributed **none** of the reds. The 14 are 1 `multiple_primary_methods`
(`_generate_try_body`, `_generate_try`, `_handler_body_statements` family) and 13 `forbidden_pattern`
name hits (`merge_pattern` on `_merge_block_is_then_exclusive:20557`, `_boolop_merge_owner_for:21038`,
`_flatten_dict_merge_to_keywords:23292`, `_wrap_boolop_with_merge_compare:37955`,
`_merge_block_is_loop_back_edge:42253`, `_try_build_ternary_merge_consumer_expr:49293`;
`from_block_pattern` on `_extract_imports_from_block_prefix:625`, `_loop_extract_pre_stmts_from_block:8882`,
`_try_build_literal_middle_from_blocks:16697`, `_try_build_call_middle_from_blocks:16796`,
`_try_build_attr_middle_from_blocks:16963`,
`_try_build_complex_operand_chained_compare_from_blocks:17062`, `_is_child_reachable_from_blocks:28149`).

The reds are **registered, not relaxed**: the ruler stays as written and the file stays red on it. Two of
its complaints are substantively about the anti-pattern the spec forbids (methods that rebuild an
expression by reading a *block collection* — `*_from_blocks` — instead of using declared region data),
which is the same family as the R21-14 deviation filed as R21-22. Clearing them is refactor work, not
this round's ticket; no flip has ever been paid for by them.

## 3. The permanent arm that replaced the one-time reading

Added `TestSignatureValidatorHasTeeth` to `tests/test_repo_tool_hygiene.py`:

- `test_validator_actually_parses_its_target` — fails if the tool prints `语法错误` or loses its `统计:` line,
  i.e. it can no longer be blind without the gate noticing (this suite runs in the gate's `checks` stage).
- `test_registered_red_count_does_not_grow` — clamps errors ≤ 14 and warnings ≤ 6 with the measured
  baseline in the message, so a NEW patch-style method name turns red instead of joining the background.

Deform proofs (each arm shown to bite, then restored byte-exactly):

| arm | deformation | result | restore |
|---|---|---|---|
| parse arm | validator `utf-8-sig` → `utf-8` (needle hits = 1, bytes changed) | `1 failed` naming exactly that test | `byte_exact=YES` vs `07f1482266a62e3f` |
| clamp arm | `BASELINE_ERRORS = 14` → `13` (needle hits = 1, bytes changed) | `1 failed` naming exactly that test | `byte_exact=YES` vs `ef47623e3ff18498` |

Suite after both restores: `5 passed` (was 3).

## 4. Standing property to remember

`core/cfg/region_ast_generator.py` (and the other sealed core files) begin with a BOM and mix CRLF/LF.
Any tool that reads them must use `utf-8-sig`, and any comparison against a `git show` blob must account
for checkout-CRLF vs blob-LF. Writing them back requires `newline=''` so untouched lines keep their own
ending — the merge tool used for gate 30 (`D:/Temp/t30/mkmix.py`) does exactly that.
