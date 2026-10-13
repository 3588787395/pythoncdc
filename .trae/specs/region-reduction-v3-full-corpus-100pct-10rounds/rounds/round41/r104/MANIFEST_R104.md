# MANIFEST_R104 — r104a, round 41, TICKET_R21-77 (clock_worker six-fact conjunction)

Mirror: `D:/Temp/r104`. Deliverables: `D:/Temp/r104/DELIVER/`.
Repo `core/` byte-untouched (re-hashed at the end: `1471c92eca157e46` / `566ff5c502276e48`).
No `*OK.py` written, no repo-mutating git command run.

## Headline

**Pipeline did NOT reach 13/13.** It ships one landed-quality analyzer rule ([R21-77-F5]) that
removes the spurious `while True:` wrapper (step 5) and, with it, the mis-claimed holiday blocks
(steps 1 first half and 2 mostly) — measured: judge unchanged at 12/13, allwin hunks 7 -> 6,
win_r91 windows 15 -> 9, text distance to the oracle +84/-74 -> +66/-53, panel all rows hold,
402-file sweep `files_compared=402 MISSING/FAIL=0 CHANGED=1 = {realtime_event_source}`.
Steps 3, 4, 6 and the 112-instruction half of step 1 remain unimplemented (reasons in the FIX doc §6).

## Pipeline files

| file | sha16 | role |
|---|---|---|
| `DELIVER/region_analyzer_R21-77-F5_996a1b1acf143458.py` | `996a1b1acf143458` | DELIVERABLE patched analyzer (BOM + all-CRLF, py_compile OK) |
| `DELIVER/region_analyzer_LANDED_1471c92eca157e46.py` | `1471c92eca157e46` | byte-exact landed copy (= mandated platform, restore target) |
| `core/cfg/region_ast_generator.py` | `566ff5c502276e48` | UNTOUCHED (never edited this round) |
| first variant (over-firing, NOT delivered) | `da5d6b3717657f86` | falsified: broke quote 92/92 -> 91/92 and risk `__init__` 43/43 -> 42/43; kept as `logs/sweep_f5_*` record |

## Builders / rigs / evidence scripts (all in DELIVER/)

* `build_f5_r104.py` — byte-exact builder: 4 unique-anchor replacements, re-emits
  `b'\xef\xbb\xbf' + '\r\n'.join(lines)`, asserts `count(b'\r\r\n')==0` and zero bare LF, `py_compile`.
  Supports `--revert` (byte-exact restore from `backup/`).
* `census_f5_r104.py` — fire census; measures the shipped predicate on the PRE-removal region set
  (runs `analyze()` with the predicate inert — valid because the patch is additive).
* `sweep_r104.py` — 402-file collateral sweep; repo-relative list joined to the repo ROOT, mirror
  `pycdc.py`, CR-stripped compare against committed `*OK.py` (read-only), prints
  `files_compared / MISSING-FAIL / CHANGED_COUNT`.
* `panel_r104.py` — the 7 named panel rows, fresh regen + `pyc_verify single --source` + failing units.
* `measure_r104.py` — realtime judge + broker judge + allwin + win_r91 + gold distance.
* `dump_cw_r104.py`, `dump_loops_r104.py`, `probe_loops_r104.py`, `probe_f5_r104.py`, `mklists.py`.
* `rigs/allwin_r63.py`, `rigs/win_r91.py` (repointed copies), `rigs/gold_diff_r104.py` (new: distance
  to `GOLD_varF.py`, the judged-13/13 oracle text).

## Products

* `DELIVER/rt_base_under_landed_platform.py` (12/13, `-113/7`, 15 windows, oracle distance 4 hunks +84/-74)
* `DELIVER/rt_product_under_R21-77-F5.py` (12/13, `-113/6`, 9 windows, oracle distance 4 hunks +66/-53)

## Logs (DELIVER/logs/)

`base_measure.txt`, `win_base.txt`, `dump_cw.txt`, `dump_loops.txt`,
`census_f5_panel.txt` (pre-narrowing), `census_f5_panel2.txt`, `census_f5_narrow_panel.txt`,
`census_f5_corp_{0,51,102,153,204,255,306,351}.txt` (all 402),
`sweep_f5_{0,101,202,303}.log` (over-firing variant, CHANGED=3),
`sweep_f5b_{0,101,202,303}.log` (delivered variant, CHANGED=1),
`panel_narrow.txt`, `measure_narrow.txt`, `ladder_r104.txt`, `definition_of_done.txt`.

## Reproduce

```
cd D:/Temp/r104
D:/Python/python.exe -X utf8 build_f5_r104.py --revert && D:/Python/python.exe -X utf8 build_f5_r104.py
D:/Python/python.exe -X utf8 panel_r104.py            # 7 rows, broker 128/128 must hold
D:/Python/python.exe -X utf8 sweep_r104.py 0 402 logs/sweep_verify.log
```
