"""B71 取证 3：ghbs 消费 finally_blocks 时的角色/loop_depth/结果，定位 D1（blk58 未发 Break）"""
import sys, io, json
sys.path.insert(0, r"f:\Downloads\pythoncdc-main")
import core.cfg.region_ast_generator as rag

TARGET = {"fin_break", "fin_continue"}
WATCH = {44, 58, 60, 66, 68, 74, 76, 90, 92, 96, 98}
LOG = []

orig_ghbs = rag.RegionASTGenerator._generate_handler_body_statements


def patched_ghbs(self, block, *a, **kw):
    b0 = block.start_offset if hasattr(block, "start_offset") else None
    r = orig_ghbs(self, block, *a, **kw)
    if b0 in WATCH:
        co = self.cfg.code.co_name if self.cfg.code else "?"
        if co in TARGET:
            role = None
            try:
                role = str(self.region_analyzer.get_block_role(block))
            except Exception as e:
                role = f"ERR:{e}"
            LOG.append({
                "co": co,
                "blk": b0,
                "role": role,
                "loop_depth": getattr(self, "_loop_depth", None),
                "cur_loop": (self._current_loop.header_block.start_offset
                             if getattr(self, "_current_loop", None) else None),
                "last_ops": [i.opname for i in block.instructions][-7:],
                "result": repr(r)[:160],
            })
    return r


rag.RegionASTGenerator._generate_handler_body_statements = patched_ghbs

from pycdc import PycDecompiler
dec = PycDecompiler()
dec.load_file(r"f:\Downloads\pythoncdc-main\test_repros\round10\r10_21_fin_loopctrl.pyc")
out = io.StringIO()
dec.decompile(out, use_region=True)
with open(r"f:\Downloads\pythoncdc-main\.trae\specs\adversarial-complete-forms-v2-10rounds\rounds\round1\probes_fixB\b71_role.json", "w", encoding="utf-8") as f:
    json.dump(LOG, f, indent=1)
print("ghbs calls logged:", len(LOG))
for e in LOG:
    print(e["co"], "blk@", e["blk"], "role=", e["role"], "ld=", e["loop_depth"],
          "loop@", e["cur_loop"], "->", e["result"][:80])
