#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""[r8v8rev3] finalize variant results evidence (C part) with all three waves."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
out = {
    "generated_by": "r8v8rev3 final review (d4cf7b23) - C part variant attacks",
    "protocol": "RV2 = pycdc regen + pyc_verify single; py_compile 3.11.7",
    "waves": [
        {
            "probe": "r8v8rev3_b104_chain5_battery",
            "units": "5/5",
            "variants": {
                "v1": "5-elem chain while + and bare-tail (arity extrapolation) PASS",
                "v2": "H5 ORIGINAL design case `while 0 < x < n < 100 and n < 100:` PASS - no fold, no phantom",
                "v3": "and-lead mirror `while flag and 0 < a < b < c < d:` PASS",
                "v4": "R2a x R2b intersection: 4-elem chain + and-tail + 2-stmt body PASS",
            },
            "judgment": "PASS",
        },
        {
            "probe": "r8v8rev3_b104_foror_battery",
            "units": "3/3",
            "variants": {
                "v1": "for-host 4-elem chain + or-tail (`if 0<a<b<c<d or e: pass`) PASS",
                "v2": "for-host 4-elem chain + or-tail with bindings PASS",
            },
            "judgment": "PASS (or-tail in if-context handled by existing machinery; domain-adjacent)",
        },
        {
            "probe": "r8v8rev3_b105_walrus3_battery",
            "units": "3/3",
            "variants": {
                "v1": "triple-nested walrus depth 3 `f((a := g((b := h((c := i()))))), a+b+c)` PASS",
                "v2": "walrus as chained-compare operand `if 0 < (n := len(x)) < 10:` PASS",
            },
            "judgment": "PASS",
        },
        {
            "probe": "r8v8rev3_b107_mixed4_battery",
            "units": "4/4",
            "variants": {
                "v1": "4-target mixed chain `a = b.c = d[k] = e.f = v` (simple head + 3 complex) PASS",
                "v2": "3-target complex chain + following `return v` PASS",
                "v3": "4-target all-complex chain PASS",
            },
            "judgment": "PASS",
        },
        {
            "probe": "r8v8rev3_bmatch_or4_battery",
            "units": "4/4",
            "variants": {
                "v1": "or 4-arm + bare-name guard `case 1|2|3|4 if g:` guard preserved PASS",
                "v2": "or arm + compound guard `case 1|2 if (g and h):` PASS",
                "v3": "or 4-arm + comparison guard (w1 control extrapolation) PASS",
            },
            "judgment": "PASS",
        },
        {
            "probe": "r8v8rev3_b104_opdeep_battery",
            "units": "4/4",
            "variants": {
                "v1": "walrus as and-tail operand `while 0 < x < 10 and (y := f(x)):` PASS",
                "v2": "multi-operand tail `... and flag and x < limit:` PASS",
                "v3": "multi-operand leads `while flag and g2 and 0 < a < b < c:` PASS",
            },
            "judgment": "PASS (None-skip latent path not triggered for these forms)",
        },
        {
            "probe": "r8v8rev3_b104_exprtail_battery",
            "units": "HEAD 4/5 (v3 FAIL); baseline 49603022 = 2/5 (v1+v2+v3 FAIL)",
            "variants": {
                "v1": "f-string and-tail: baseline FAIL (fold+phantom recheck) -> HEAD PASS (improved)",
                "v2": "dict-comprehension and-tail: baseline FAIL -> HEAD PASS (improved)",
                "v3": "IfExp and-tail `while 0<x<10 and (y if y else x):` FAIL at BOTH trees"
                      " (HEAD: `while 0<x<10: if y: continue; y; continue; ...`;"
                      " baseline: `while 0<x<10: break; if y: continue; y; continue; n+=1`)",
            },
            "judgment": "v3 = pre-existing domain-outside gap (multi-block IfExp diamond operand not in"
                        " single-block tail absorption scope; no remediation-caused regression;"
                        " remediation strictly improved this probe 2/5->4/5) -> register Bn candidate (B123), hand over",
        },
    ],
    "b122_stock_forms": {
        "r8v8rev_bmatch_guards_battery (whole file)": "HANG >90s at BOTH 49603022 and HEAD (B122 stock maintained)",
        "r8v8rev_bmatch_v2 (split)": "HANG >90s at BOTH trees",
        "r8v8rev_bmatch_nestnoguard n1": "HANG at BOTH trees (B122 stock maintained)",
        "note": "REVIEW2 recorded '0-byte crash' for the v2 form; current runs hang at both trees - same B122 catastrophic family, identical across trees, zero remediation damage; green units confirmed via split probes (v1 2/2, v4 2/2) and fixed probe (v3 2/2)",
    },
}

path = os.path.join(HERE, 'r8v8rev3_variant_results.json')
json.dump(out, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('saved', path)
