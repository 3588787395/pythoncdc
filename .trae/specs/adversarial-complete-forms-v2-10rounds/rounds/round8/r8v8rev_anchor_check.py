# -*- coding: utf-8 -*-
"""R8 review2: I.6 anchor verification for FIX_A §4 / FIX_B §13 / FIX_C §9 tables.
Each entry: (file, expected_line, marker_snippet). Marker must be found within
window [line-W, line+W] of the CURRENT working tree (HEAD state)."""
import sys, io

W = 18  # window half-width for "approx" line numbers

ANCHORS = [
    # ---- FIX_A §4 (region_analyzer.py) ----
    ("core/cfg/region_analyzer.py", 1834, "B121-secondary"),
    ("core/cfg/region_analyzer.py", 4246, "Step 4"),
    ("core/cfg/region_analyzer.py", 4356, "_is_while_guard_continue_only_backedge"),
    ("core/cfg/region_analyzer.py", 7631, "def _is_while_guard_continue_only_backedge"),
    ("core/cfg/region_analyzer.py", 7633, "def _is_while_guard_continue_only_backedge"),
    ("core/cfg/region_analyzer.py", 5196, "def _cleanup_try_else_in_loop_body"),
    ("core/cfg/region_analyzer.py", 5418, "RegionType.WHILE_LOOP"),
    ("core/cfg/region_analyzer.py", 5443, "_b109_conv_target"),
    # ---- FIX_B §13 ----
    ("core/cfg/region_analyzer.py", 30700, "B99-C3"),
    ("core/cfg/region_analyzer.py", 30700, "_b99_absorb"),
    ("core/cfg/region_analyzer.py", 30966, "_b99_absorb=False"),
    ("core/cfg/region_ast_generator.py", 42537, "def _try_build_orprefix_and_boolop_from_ternary"),
    ("core/cfg/region_ast_generator.py", 43701, "B98-R1"),
    ("core/cfg/region_ast_generator.py", 36395, "def _try_build_match_case_ternary_stmt"),
    ("core/cfg/region_ast_generator.py", 37292, "B77"),
    ("core/cfg/region_ast_generator.py", 28084, "B82"),
    ("core/cfg/region_ast_generator.py", 29748, "B83"),
    ("core/cfg/region_ast_generator.py", 29798, "B83"),
    # ---- FIX_C §9 B81 ----
    ("core/cfg/region_analyzer.py", 17193, "B81"),
    ("core/cfg/region_analyzer.py", 17210, "B81"),
    ("core/cfg/pattern_parser.py", 351, "B81"),
    ("core/cfg/pattern_parser.py", 452, "B81"),
    ("core/cfg/region_analyzer.py", 2172, "B81"),
    ("core/cfg/region_analyzer.py", 2293, "B81"),
    ("core/cfg/region_analyzer.py", 2260, "B81"),
    ("core/cfg/region_analyzer.py", 14880, "fail_case_offset"),
    ("core/cfg/region_analyzer.py", 16758, "fail_case_offset"),
    ("core/cfg/region_analyzer.py", 17324, "fail_case_offset"),
    # ---- FIX_C §9 B103 ----
    ("core/cfg/pattern_parser.py", 1536, "B103"),
    ("core/cfg/pattern_parser.py", 1209, "def _pure_jf_argval"),
    ("core/cfg/pattern_parser.py", 1224, "def _collect_or_arm_chain_instrs"),
    ("core/cfg/pattern_parser.py", 307, "B103"),
    ("core/cfg/region_analyzer.py", 15981, "B103"),
    ("core/cfg/region_analyzer.py", 15766, "B103"),
    ("core/cfg/region_analyzer.py", 15958, "B103"),
    ("core/cfg/region_analyzer.py", 17181, "B103"),
    ("core/cfg/region_analyzer.py", 17159, "B103"),
    ("core/cfg/region_analyzer.py", 14800, "B103"),
    ("core/cfg/region_analyzer.py", 15805, "B103"),
    ("core/cfg/region_ast_generator.py", 35322, "MatchRegion"),
    ("core/cfg/region_ast_generator.py", 35352, "MatchRegion"),
    ("core/cfg/region_ast_generator.py", 37557, "WithRegion"),
    ("core/cfg/pattern_parser.py", 424, "B103"),
    ("core/cfg/pattern_parser.py", 1516, "B103"),
    ("core/cfg/region_analyzer.py", 17488, "_mr_head_has_wildcard_discard"),
    ("core/cfg/region_analyzer.py", 2239, "B81"),
    # ---- FIX_C §9 B102 ----
    ("core/cfg/region_analyzer.py", 8908, "B102"),
    ("core/cfg/region_analyzer.py", 8607, "def _b102_degenerate_chain_pairs_finally"),
    ("core/cfg/region_analyzer.py", 8568, "def _b102_chain_reachable_blocks"),
    ("core/cfg/region_analyzer.py", 8649, "_b102_cleanup_target_of"),
    ("core/cfg/region_analyzer.py", 8548, "_B102_ZONE_FRAME_OPS"),
    ("core/cfg/region_analyzer.py", 10010, "B102"),
    ("core/cfg/region_analyzer.py", 11992, "def _find_star_else_blocks"),
    ("core/cfg/region_analyzer.py", 9898, "B102"),
    ("core/cfg/region_analyzer.py", 10171, "B102"),
    ("core/cfg/region_ast_generator.py", 35373, "B102"),
    ("core/cfg/region_ast_generator.py", 35512, "B102"),
    # ---- FIX_C §9 B113 ----
    ("core/cfg/comprehension_generator.py", 1892, "def _b113_extract_flat_clauses"),
    ("core/cfg/comprehension_generator.py", 1487, "B113"),
    ("core/cfg/comprehension_generator.py", 1574, "B113"),
    ("core/cfg/comprehension_generator.py", 1225, "B113"),
    ("core/cfg/comprehension_generator.py", 1254, "B113"),
    ("core/cfg/comprehension_generator.py", 1291, "B113"),
    # ---- FIX_C §9 B96 ----
    ("core/cfg/comprehension_generator.py", 119, "B96"),
    ("core/cfg/comprehension_generator.py", 136, "B96"),
    ("core/cfg/comprehension_generator.py", 2868, "B96"),
    ("core/cfg/ast_converter.py", 1826, "B96"),
    ("core/cfg/comprehension_generator.py", 2048, "B96"),
    # ---- FIX_C §9 B106 ----
    ("core/cfg/ast_converter.py", 1362, "B106"),
    ("core/cfg/ast_converter.py", 1925, "B106"),
    ("core/cfg/comprehension_generator.py", 2027, "B106"),
    ("core/cfg/comprehension_generator.py", 1169, "B106"),
    ("core/cfg/comprehension_generator.py", 1405, "B106"),
    ("core/cfg/comprehension_generator.py", 1696, "B106"),
    ("core/cfg/comprehension_generator.py", 1764, "B106"),
]

cache = {}
def lines_of(path):
    if path not in cache:
        with io.open(path, "r", encoding="utf-8", errors="replace") as f:
            cache[path] = f.read().splitlines()
    return cache[path]

def find_line(path, expect, marker):
    ls = lines_of(path)
    lo = max(0, expect - 1 - W); hi = min(len(ls), expect - 1 + W + 1)
    for i in range(lo, hi):
        if marker in ls[i]:
            return i + 1
    # fallback: whole-file search (drift > W)
    for i, l in enumerate(ls):
        if marker in l:
            return -(i + 1)  # negative = drifted
    return 0

fails, drifts, oks = [], [], 0
for path, expect, marker in ANCHORS:
    n = find_line(path, expect, marker)
    if n == 0:
        fails.append((path, expect, marker))
    elif n < 0:
        drifts.append((path, expect, marker, -n))
    else:
        oks += 1

print("TOTAL anchors:", len(ANCHORS), " in-window OK:", oks, " drifted:", len(drifts), " NOT FOUND:", len(fails))
for f in fails:
    print("NOT FOUND:", f)
for d in drifts:
    print("DRIFTED: %s claimed :%s marker %r actually at :%d" % (d[0].split('/')[-1], d[1], d[2], d[3]))
