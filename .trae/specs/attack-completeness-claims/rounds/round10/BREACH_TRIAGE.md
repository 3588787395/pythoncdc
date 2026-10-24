# Breach Triage — B163–B219 and v9 Findings

## Headline

- **B163–B219: 57 identifiers, 0 formally closed in Task 10.**
- B142: reclassified by B181 from “rare residual, not elevated” to **shape-level gap**.
  **UPDATE (rr-v5r02, achieve-any-syntax-completeness Task 2): B142 fixed at family
  level** — finally-copy lineage signature + transparent-chain search + ownership
  inheritance + ledger-priority rebuild + fc exit materialization. Evidence: frozen
  comparator 4/4 on `v_b71_face.pyc` (was 3/4); R1 `v_nest_fin_continue([[0,1]])/([[1,2]])`
  return sequences equal item-by-item. Family predicate and probes:
  `.trae/specs/achieve-any-syntax-completeness/rounds/round12/probes_b142/README.md`.
  Remaining family members (break-exit arm, triple finally, finally-return) stay
  tracked under B207/B208 and Task 4.4.
- B143: **reduction-level gap** (shape pipeline exists; finalbody dispatch order is wrong).
- No new B number was opened for the four Task 9.5 fuzz findings. They are mapped to existing families pending deduplication.
- B200’s registry row is truncated in `rounds/round3/BREACH_REGISTRY.md`; the identifier is still counted, but its row needs repair before any closure claim.

The authoritative per-item table remains `rounds/round3/BREACH_REGISTRY.md`. This file does not replace it.

## Status by layer

| layer | identifiers | status |
|---|---|---|
| L0 theory / mechanism | B172–B176, B179–B193 | open / qualitative; B142 (B181) elevated; B143 (B182) reduction-level |
| L1 measure | B163–B171, B177–B178 | qualitative: denominator, variant, dual-reading, marker-count gaps |
| L2 judge | B194–B201 | open: judge blind spots, shared target, stale ledger |
| L4 runtime | B202–B213 | open: uncompileable output, local-write loss, try-else, polarity, finally, continue, scale |
| L5 evidence | B214–B219, U-06 | open: source loss, common cause, corpus bias, metric nature, denominator duplication |

“Qualitative” does not mean closed. It means the item is registered as a measurement/definition defect rather than a product patch target.

## Task 9.5 fuzz findings — dedup map

| repro | differential | candidate family | dedup question | state |
|---|---|---|---|---|
| `FZ-raresyntax-015-11d70844` / `starred-unpack` | R6/R7; product drops `data = [...]`, later `NameError` | B203 (local write lost / NameError) | Is star-unpack assignment a new mechanism or a B203 instance? | open, minimized 6→3 |
| `FZ-semantictrap-020-1d4bb36d` / `generator-send` | R1/R7 | B210 (yield / separator family) | B210 is “yield constant lost”; generator send resume semantics may be distinct | open, minimized 15→14 |
| `FZ-raresyntax-021-5433fdc8` / `annotations-posonly` | R7; positional-only `/` lost | B197 (arg slots) / B202 (signature/compile metadata) | R7-only metadata loss vs. callable behavior; needs a callable probe | open, minimized 2→2 |
| `FZ-semantictrap-023-cb72b56d` / `finally-return` | R1/R5/R7; `return ("ret", i)` lost, `global` hoisted | B207 / B142 (finally copy/return) | Is this the same finalbody copy defect as B207, or a return-value variant? | open, minimized 14→10 |

No B220+ is allocated until the dedup question is answered with a probe that distinguishes the mechanisms. This avoids inflating the registry with duplicates.

## J sample R7 findings

| id | dimensions | visible product issue | family |
|---|---|---|---|
| `JS-IF-017` | R7 | `v_nest_fin_continue` code object differs (`co_consts[2].code_sha`); call probe shows R1 difference | **B142** |
| `JS-IF-021` | R7 | same `v_b71_face` product; same code object difference | **B142** |
| `JS-IF-076` | R7 ×5 | `x01_if_deep_hosts` products `if_in_while` / `if_in_try` / `if_shallow` have different `co_consts` code objects; `if_in_while` loses `break`; module-only R1–R6 equal | x01 structural |
| `JS-IF-088` | R7 | same `v_b71_face` product; same code object difference | **B142** |
| `JS-IF-090` | R7 | same `v_b71_face` product; same code object difference | **B142** |
| `JS-IF-097` | R7 | same `v_b71_face` product; same code object difference | **B142** |

The earlier “module docstring / metadata only” triage is **retracted**. Five of six R7 records are B142 code-object differences; the sixth is an independent x01 structural difference. None is explained by module docstring alone. Call probe on `v_nest_fin_continue([[0, 1]])` gives original return length 5 vs product 7, so B142 is an executable semantic difference. `JS-IF-076` shows that module-only C4 misses function-body differences and only R7 catches them.

Until the runner consumes `input_model.calls` and treats R7 code-object differences as blocking, G2a remains FAIL and no “semantic complete” claim is allowed. Details: `ATTACK_RESULTS_AND_RECOMMENDATIONS.md`.

## Closure criteria still missing

For each B163–B219 item, a valid closure needs:

1. a general mechanism, not a corpus/function-name special case;
2. I.4 whitelist evidence (opcode order / jump polarity / pred-succ / exception edge / members / registration state);
3. a synthetic non-corpus probe plus a negative control;
4. a re-run of the affected gate plus the full E gate;
5. a registry status change with commit and evidence path.

None of these were completed in Task 10. Therefore Task 10.1 is **not complete**, and the v9 terminal state cannot be “all breaches closed.”
