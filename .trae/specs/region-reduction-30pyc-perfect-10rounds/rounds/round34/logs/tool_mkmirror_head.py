# -*- coding: utf-8 -*-
"""Create the head mirror (a pristine copy of the landed core) without a candidate spec.
run --arm=head needs mirr_head to exist; _load_arm asserts pycdc resolves inside it."""
import sys
sys.path.insert(0, r"D:/Temp/r34gate/r34")
import r34c
rel = "core/cfg/region_ast_generator.py"
p = r34c._mkmirror(r34c.ROOT + "/mirr_head", rel)
import io, hashlib
b = io.open(p, "rb").read()
assert b == io.open(r"F:/Downloads/pythoncdc-main/core/cfg/region_ast_generator.py", "rb").read(), "head mirror != worktree core"
print("mirr_head ready", p, len(b), hashlib.sha256(b).hexdigest()[:20])
