#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Patch kit copies for R2 gate paths (HERE/OUT -> attain-true-completeness/rounds/round2)."""
import io

P1 = r'.trae/specs/attain-true-completeness/rounds/round2/final_verify_run_r2.py'
P2 = r'.trae/specs/attain-true-completeness/rounds/round2/iv2_recheck_r2.py'

s = io.open(P1, encoding='utf-8').read()
old1 = ("HERE = os.path.join(ROOT, '.trae', 'specs', "
        "'adversarial-complete-forms-v2-10rounds', 'rounds', 'round10')")
new1 = ("HERE = os.path.join(ROOT, '.trae', 'specs', "
        "'attain-true-completeness', 'rounds', 'round2')")
assert old1 in s, 'final_verify_run HERE anchor missing'
s = s.replace(old1, new1)
io.open(P1, 'w', encoding='utf-8').write(s)
print('final_verify_run_r2.py: HERE ->', new1)

s = io.open(P2, encoding='utf-8').read()
old2 = ("OUT = os.path.join(ROOT, '.trae', 'specs', "
        "'adversarial-complete-forms-v2-10rounds',\n"
        "                   'rounds', 'round10', 'r10v10_fv_iv2.json')")
new2 = ("OUT = os.path.join(ROOT, '.trae', 'specs', "
        "'attain-true-completeness',\n"
        "                   'rounds', 'round2', 'r2_fv_iv2.json')")
assert old2 in s, 'iv2 OUT anchor missing'
s = s.replace(old2, new2)
io.open(P2, 'w', encoding='utf-8').write(s)
print('iv2_recheck_r2.py: OUT ->', new2)
