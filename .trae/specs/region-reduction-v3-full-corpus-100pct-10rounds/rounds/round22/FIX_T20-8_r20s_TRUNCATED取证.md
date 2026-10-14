# FIX_T20-8 — r20s — victim: fly/data/quote.pyc :: <module>.Quote.run_individual_transform

Ticket: ONE mechanism, file owned = `core/cfg/region_ast_generator.py` ONLY. Repo is READ-ONLY for me.
Bar: >=1 named unit flip on quote.pyc (87/92 -> 88/92, i.e. run_individual_transform Equal), zero decreases on the other 10 panel files + sentinels 153/153 / 17/17 / 37/37, six batteries at recorded values. `del 84 -> del 40` without flip = FALSIFIED-but-supporting.

Status: IN PROGRESS. This doc is appended live.

## Mirror build proof
- Copy-time sealed re-read (task numbers trusted only if files agree): `region_ast_generator.py` sha16=`4f295dfc6ebd2caa` (59559 lines; this equals r20r's DELIVERED file — the second landing being certified by the coordinator may be these bytes or newer; I patch ONLY against the bytes in my mirror), `pycdc.py`=`cf4e2705ab042732`, `region_analyzer.py`=`640d33a77dcb71c2`. Note: ast_generator_v2.py lives at `core/cfg/ast_generator_v2.py` (task quoted it read-only anyway).
- `cp -r pycdc.py core parsers utils bytecode scripts /d/Temp/r20s/wt/` + `cp --parents -r` of the 6 battery dirs (round14/{repro,repro_arm,repro_ccneg}, round18/repro_retbreak, round19/{repro_orderapi,repro_tail}) at identical relative depth + `cp --parents` of unit_diff.py + the 14 panel `.pyc` inputs. All `__pycache__` dirs deleted from mirror.
- Self-certify: `diff -rq --exclude=__pycache__` of core/parsers/utils/bytecode/scripts vs mirror => **MIRROR_TREE_IDENTICAL**; per-file sha256(16) for pycdc.py / region_ast_generator.py / region_analyzer.py repo==mirror MATCH.
- Regenerated corpus product INSIDE mirror: `python -X utf8 pycdc.py --region site-packages/fly/data/quote.pyc -o out/pristine/quote_base_OK.py` (4.4s) then `cmp` vs repo committed `site-packages/fly/data/quoteOK.py` => **REGEN_CMP_IDENTICAL**. Mirror executes the copied bytes.
- `.pyc` inputs: panel pycs are repo bytes (copied). All products in `D:/Temp/r20s/out/{pristine,patched}` only. No repo writes, no gate runs, no git writes.


## Stage 1 baseline
- Panel, UNPATCHED mirror-generated products, judged `pyc_verify single --source <mirror product>` (per-file logs in `/d/Temp/r20s/out/pristine/*_judge.txt`):
  quote **87/92** · klinedata 63/64 · handlers 29/30 · wizard_quant_api 55/58 · trade_info_utils 38/41 · api_base 27/28 · real_quote 43/45 · strategy 26/27 · realtime_event_source 12/13 · risk/__init__ 42/43 · trade_live_broker 118/128 · [SENT] quotation **153/153** · matcher 17/17 · order_api 37/37. ALL match the quoted baseline exactly (quote is 87, i.e. mirror is fresh, not stale).
- Quote mirror product `cmp`-identical to `out/committed_quoteOK.py` (repo sealed copy).
- Victim unit baseline re-measured against sealed product: `len orig=407 prod=355 delta=-52 hunks=10 landings=3 judge_diff=True` (full dump: `out/victim_unidadiff_base.txt`).
  **Hash/number drift note:** the coordinator ledger quoted the victim diff as a large `del 84` single hunk; the SEALED bytes reproduce instead `delta=-52` across hunks del=15 / del=5 / del=3 / del=21 / ins=9 / del=21 plus 2×1-instruction replaces. I trust the files: my target shape is `delta=-52 hunks=10 landings=3`, and the three same-shape hunks (recv→message→`if not message` warning→list(keys)[0]) are exactly the del=15 / del=5+3 / del=21(+ins9) group.


## Per-unit 取证
(pending)

## 判据实现 (exact file:line + predicate)
(pending)

## Stage readings
(pending)

## 负面证据
(pending)

## Final declaration
(pending)
