# [R21-75] orchestrator's own two guard variants on `_r58_collect_break_target_stmts`

Platform: analyzer `9ba2d8afe9e96fc1` (r100a, terminator half CLOSED) + generator `0f4c3898298e6f2e` (r95a).
Site: `region_ast_generator.py:6904-6913`, the break-target collector's foreign-region branch.
Trigger measured by r102a and by me independently: loop 1 (`hdr=704`) has `break_blocks=[2064,2066,2168]`,
each owned by `LoopRegion@1890` (the HOST's later sibling loop), and `:6913 _generate_region(bb_region)`
emits that sibling inside loop 1's pass.

Guard (region data only, no names/offsets/counters): a `bb_region` whose `entry` is not in `region.blocks`
is not a descendant of this loop, so this pass must not emit it.

| variant | action | broker units | `_sync_worker` windows | product lines vs GOLD 45 | gold hunks | panel |
|---|---|---|---|---|---|---|
| base (`0f4c3898`) | - | 127/128 | 5 | 42 | 2 (`-18,0 +19,8` / `-37,6 +44,0`) | all hold |
| (a) `6660f3a5f9c2dc81` | `bb_region = None` | 127/128 | 8 | 45 | 2 (`-19,12 +19,12` / `-32,13 +32,13`) | all hold |
| (b) `bd57b0f6e2d81b25` | `continue` (skip block) | 127/128 | 7 | **46** | **1** (`-19,27 +19,26`) | all hold |

Neither flips; the flip bar is judge `128/128`, so both are BANKED, not installed. Reading of (b), which is the
better direction: the reconnect chain is now emitted *before* loop 2 (position half reached), but loop 2 is
attached as the `else:` arm of the third guard test and the innermost body (`system_log.debug` /
`if not reconnect(...)` / `self.reconnect_flag = True`) is emitted *after* the whole if/else, with
`return None` instead of a bare `return`. So the residual is the arm/merge attachment of the sibling region,
one step past where the analyzer census can see it. Variant (a) additionally shows the leftover-operand
statement `time_difference = abs(...)` printed between loop 1 and the chain (r98a's fact) - so (b) also
removed that line, which is why it reaches a single hunk.


## Cross-arm measurement of r102a's live candidate (pinned, moving hash)

`gen 91c16e1636dddd14` (3,867,755 B, BOM+CRLF clean, py_compile PASS), pinned content-addressed at
`D:/Temp/pins/` and banked here while r102a was still running - a moving hash is never a verdict.

| arm | analyzer | broker units | `_sync_worker` windows | lines vs GOLD 45 | gold hunks | panel |
|---|---|---|---|---|---|---|
| A (r102a's own base) | `1471c92eca157e46` | not reached in that run | - | 46 | **1** (`-19,27 +19,26`) | battery RED=8/9 |
| B (cross with r100a) | `9ba2d8afe9e96fc1` | **127/128** | **5** | - | - | realtime 12/13, function 15/15, replace_utils 9/9, quote 92/92, quotation 153/153, order_api 37/37, battery RED=8/9 |

Reading: r102a's generator independently reaches the SAME shape my variant (b) reached - 46 lines and one
hunk - which is strong corroboration that the position half is actuated by refusing the foreign-region
emission in `_r58_collect_break_target_stmts`. Adding r100a's terminator half restores windows to 5 but
does not flip. The residual visible in the single hunk is the arm/merge attachment: loop 2 sits in the
`else:` of the third guard test and the innermost body prints after the if/else as `return None`.
Nothing installed from either hand.
