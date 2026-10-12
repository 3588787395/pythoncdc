# COVERAGE_AUDIT — every real `.pyc` input has its same-directory `<name>OK.py` product (evidence, not inference)

Run on the gate-36 landed bytes, 2026-10-12. Scripts committed alongside: `coverage_audit.py`
(classifies nothing, kept as the cautionary version) and `coverage_audit2.py` (the one to re-run).

## Why the naive walk is wrong

`coverage_audit.py` reports `pyc=1748 OK.py=407 → 1343 pyc WITHOUT adjacent OK.py` and looks like a
massive shortfall. Inspecting the first 18 rows shows they are all
`<dir>/__pycache__/<mod>OK.cpython-311.pyc`: Python wrote them when it **imported our own
`<mod>OK.py` products**. They are derived caches, not decompiler inputs, and they were never
supposed to have products. `coverage_audit2.py` therefore classifies by path first:

```
total .pyc            = 1748
derived (__pycache__) = 1342   (Python caches of our own *OK.py, not inputs)
real inputs           = 406
INPUTS missing <name>OK.py : 1
   IQCommon/util/email_utils.py.pyc
```

## The 4 inputs outside the 402-file gate roster — none is an unserved input

Roster rebuilt from `rounds/round36/after/shard*_report.json` rows (= 402, the authoritative gate
input), intersected with the walk:

| file | bytes at offset 0 | what it actually is |
|---|---|---|
| `IQCommon/api/klinedataOK.pyc` | `\xa7\r\r\n` (3.11) | scratch pyc produced by compiling our own `klinedataOK.py` |
| `IQCommon/api/klinedataOK_check.pyc` | `\xa7\r\r\n` | scratch from a `compile()`-check run |
| `IQCommon/util/email_utils.py.pyc` | `# Source Generated with ` | **not bytecode at all** — an OK.py-style *source text* written under a `.pyc` name (hence the "magic" `23 20 53 6f`); the only entry that shows as missing a product, and it is not an input |
| `fly/dumpload/_load_algo_recomp.pyc` | `\xa7\r\r\n` | scratch pyc of a recompiled product (the name says so) |

So the 402 roster is exactly the set of real inputs, and **all 402 have a same-directory
`<name>OK.py` product** — the objective's per-file generation requirement is met and the
outstanding work is entirely the judge-Equal requirement (5 failing units in 3 files: 6612/6617).

## Two naming-slip products, recorded not deleted

`IQCommon/util/cgroup_utils OK.py` and `IQCommon/util/email_utils OK.py` contain a space before
`OK.py`, so they do **not** satisfy `<name>OK.py` on their own — but the audit checks each one and
reports `proper twin exists=True` for both, i.e. the correctly named products are present too. They
are committed clutter from an old hand-rename. Not deleted here because removing anything under
`site-packages/` mid-round would rewrite the sealed product tree and de-certify the gate; queue it
for the post-100% cleanup pass instead, where it can be done with a gate on both sides of it.

## Rule to keep

Any coverage statement about this corpus must come from `coverage_audit2.py`'s classified numbers,
never from a raw `.pyc` count: the derived-cache population is ~1340 and dwarfs the 402 inputs, so a
raw walk overstates the shortfall by more than three times.
