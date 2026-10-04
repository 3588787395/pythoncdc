"""B71e 取证：_loop_generate_for 返回值 + FOR_LOOP 区域生成结果 — 定位 orelse=[Return(total)] 拼装点"""
import sys, io, json
sys.path.insert(0, r"f:\Downloads\pythoncdc-main")
import core.cfg.region_ast_generator as rag

CO = "fin_break"
LOG = []


def co(self):
    return self.cfg.code.co_name if self.cfg.code else "?"


def offs(blocks):
    return [getattr(b, "start_offset", b) for b in (blocks or [])]


orig_lgf = rag.RegionASTGenerator._loop_generate_for
def patched_lgf(self, region):
    eb_before = offs(getattr(region, "else_blocks", None))
    r = orig_lgf(self, region)
    if co(self) == CO:
        orelse = r.get("orelse") if isinstance(r, dict) else None
        LOG.append({"fn": "_loop_generate_for", "entry": getattr(region.entry, "start_offset", None),
                    "else_blocks_at_entry": eb_before,
                    "else_blocks_at_exit": offs(getattr(region, "else_blocks", None)),
                    "has_orelse": orelse is not None,
                    "orelse": repr(orelse)[:200]})
    return r
rag.RegionASTGenerator._loop_generate_for = patched_lgf

orig_gl = rag.RegionASTGenerator._generate_loop
def patched_gl(self, region, *a, **k):
    r = orig_gl(self, region, *a, **k)
    if co(self) == CO:
        LOG.append({"fn": "_generate_loop", "type": str(getattr(region, "region_type", None)),
                    "entry": getattr(region.entry, "start_offset", None),
                    "res": repr(r)[:400]})
    return r
rag.RegionASTGenerator._generate_loop = patched_gl

orig_gr = rag.RegionASTGenerator._generate_region
def patched_gr(self, region):
    r = orig_gr(self, region)
    if co(self) == CO:
        LOG.append({"fn": "_generate_region", "type": str(getattr(region, "region_type", None)),
                    "entry": getattr(region.entry, "start_offset", None),
                    "res": repr(r)[:400]})
    return r
rag.RegionASTGenerator._generate_region = patched_gr

from pycdc import PycDecompiler
dec = PycDecompiler()
dec.load_file(r"f:\Downloads\pythoncdc-main\test_repros\round10\r10_21_fin_loopctrl.pyc")
out = io.StringIO()
dec.decompile(out, use_region=True)
with open(r"f:\Downloads\pythoncdc-main\.trae\specs\adversarial-complete-forms-v2-10rounds\rounds\round1\probes_fixB\b71e_trace.json", "w", encoding="utf-8") as f:
    json.dump(LOG, f, indent=1, default=str)
print("log_n=", len(LOG))
