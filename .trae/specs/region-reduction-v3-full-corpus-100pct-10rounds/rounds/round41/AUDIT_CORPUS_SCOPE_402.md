# AUDIT - corpus scope for the completion check (2026-10-14 01:37)

The objective is every pyc decompiled and judged Equal. This audit fixes the denominator, measured from disk:

- `site-packages/` walk excluding `__pycache__`: **406** files named `.pyc`.
- Roster of record: **402** (the list every gate consumes; `rounds/round40/r95/corpus402.txt`, 402 lines, all resolve under ROOT).
- **405** of the 406 have a sibling `*OK.py` product; one does not.

The four non-roster files, classified by their own bytes:

| file | size | first 4 bytes | class |
|---|---|---|---|
| IQCommon/util/email_utils.py.pyc | 3866 | 23 20 53 6f | **not bytecode at all** - ASCII text starting with the line "Source Generated with Decompyle++ (Python version)", i.e. one of our decompiled products mis-suffixed as .pyc. It has no sibling product because it *is* a product. `pycdc.py` refuses it: Unsupported magic number 0x6F532023. |
| fly/dumpload/_load_algo_recomp.pyc | 2563 | a7 0d 0d 0a | real 3.11 bytecode, compiled artifact of a re-compilation scratch, not an original distribution input; already has a sibling OK product from an earlier round |
| IQCommon/api/klinedataOK.pyc | 117326 | a7 0d 0d 0a | compiled from our own klinedataOK.py output, not an input |
| IQCommon/api/klinedataOK_check.pyc | 117340 | a7 0d 0d 0a | same family, a check artifact |

Consequence for the completion audit: **the denominator stays 402 files / 6617 units**. None of the four adds an unmet obligation - one is a misnamed product and three are compiled caches of our own or a scratch source, which is the same classification the round-38 worktree audit reached (407 = 402 + 3 + 2 orphans; the 867 long-path files never materialize, see the worktree-staging note).

So 100 percent means: `realtime_event_source.clock_worker` at 13/13, corpus 6617/6617 with 402/402 files green, certified by `gate_chain.py 41 40` (regen `ok=402 bad=0` plus per-file unit compare), not by `pyc_verify` alone, which is compare-only and reads stale products as green.