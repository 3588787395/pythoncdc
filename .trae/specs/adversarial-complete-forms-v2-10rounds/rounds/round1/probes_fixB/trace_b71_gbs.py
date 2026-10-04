"""B71 取证 3：_generate_block_statements 对 blk38/blk72 的行为 + _current_loop 状态"""
import sys, io, json
sys.path.insert(0, r"f:\Downloads\pythoncdc-main")
import core.cfg.region_ast_generator as rag

WATCH_BLOCKS = {28, 38, 72}
LOG = []

orig = rag.RegionASTGenerator._generate_block_statements
def patched(self, block, _cjb_parent=None):
    r = orig(self, block, _cjb_parent)
    if block.start_offset in WATCH_BLOCKS:
        cl = self._current_loop
        LOG.append({
            "blk": block.start_offset,
            "co": self.cfg.code.co_name if self.cfg.code else "?",
            "result": repr(r)[:300],
            "current_loop": (cl.header_block.start_offset if cl is not None and getattr(cl, 'header_block', None) else None) if cl is not None else None,
            "in_generated": block in self.generated_blocks,
            "role": str(self.region_analyzer.get_block_role(block)),
        })
    return r
rag.RegionASTGenerator._generate_block_statements = patched

from pycdc import PycDecompiler
dec = PycDecompiler()
dec.load_file(r"f:\Downloads\pythoncdc-main\test_repros\round10\r10_21_fin_loopctrl.pyc")
out = io.StringIO()
dec.decompile(out, use_region=True)
with open(r"f:\Downloads\pythoncdc-main\.trae\specs\adversarial-complete-forms-v2-10rounds\rounds\round1\probes_fixB\b71_gbs.json", "w", encoding="utf-8") as f:
    json.dump(LOG, f, indent=1, default=str)
print("calls:", len(LOG))
