import difflib
import os

src_d = "test_repros/round5"
stage_d = ".trae/specs/attain-true-completeness/test_repros/round5"
pairs = [
    ("rec1_synth_g1a_guard_depth.py", "rec1_g1a_rec1_synth_g1a_guard_depthOK.py"),
    ("rec1_synth_g1b_guard_depth.py", "rec1_g1b_rec1_synth_g1b_guard_depthOK.py"),
    ("rec1_synth_g2a_with_match_cross.py", "rec1_g2a_rec1_synth_g2a_with_match_crossOK.py"),
    ("rec1_synth_g2b_with_match_cross.py", "rec1_g2b_rec1_synth_g2b_with_match_crossOK.py"),
    ("rec1_synth_g3a_b61_deephost.py", "rec1_g3a_rec1_synth_g3a_b61_deephostOK.py"),
    ("rec1_synth_g3b_b61_deephost.py", "rec1_g3b_rec1_synth_g3b_b61_deephostOK.py"),
    ("rec1_synth_b74d_guard_depth.py", "rec1_b74d_rec1_synth_b74d_guard_depthOK.py"),
    ("rec1_synth_b74e_guard_battery2.py", "rec1_b74e_rec1_synth_b74e_guard_battery2OK.py"),
    ("rec1_synth_b70a_wt_with_bc.py", "rec1_b70a_rec1_synth_b70a_wt_with_bcOK.py"),
]
for src_name, ok_name in pairs:
    a = open(os.path.join(src_d, src_name), encoding="utf-8").read().splitlines()
    b_path = os.path.join(stage_d, ok_name)
    if not os.path.exists(b_path):
        print("MISSING", b_path)
        continue
    b = open(b_path, encoding="utf-8").read().splitlines()
    diff = list(difflib.unified_diff(a, b, lineterm="", n=1, fromfile="orig", tofile="regen"))
    print("=" * 20, src_name, "=" * 20)
    if not diff:
        print("(no text diff — control-flow/bytecode-level difference)")
    for line in diff[:80]:
        print(line)
    print()
