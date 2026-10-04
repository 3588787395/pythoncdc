"""B71f 取证：else_blocks 全程变化 + Fix B2 host-loop lookup 监听 + 返回列表正确检查"""
import sys, io, json, traceback
sys.path.insert(0, r"f:\Downloads\pythoncdc-main")
import core.cfg.region_ast_generator as rag
import core.cfg.region_analyzer as ranalyzer

CO = "fin_break"
LOG = []


def co(self):
    return self.cfg.code.co_name if self.cfg.code else "?"


def offs(blocks):
    return [getattr(b, "start_offset", b) for b in (blocks or [])]


def snap(region):
    return {"id": id(region), "else": offs(getattr(region, "else_blocks", None)),
            "finally": offs(getattr(region, "finally_blocks", None))}


# 监听 get_region_for_block(10)
orig_grfb = ranalyzer.RegionAnalyzer.get_region_for_block
def patched_grfb(self, block):
    r = orig_grfb(self, block)
    if co(self) == CO and getattr(block, "start_offset", None) == 10:
        LOG.append({"ev": "get_region_for_block(10)", "ret_id": id(r) if r is not None else None,
                    "ret_type": str(getattr(getattr(r, "region_type", None), "name", None))})
    return r
ranalyzer.RegionAnalyzer.get_region_for_block = patched_grfb

orig_tf = rag.RegionASTGenerator._generate_region
def patched_gr(self, region):
    is_tf = co(self) == CO and "TRY_FINALLY" in str(getattr(region, "region_type", None))
    is_loop = co(self) == CO and "LOOP" in str(getattr(region, "region_type", None))
    if is_tf:
        LOG.append({"ev": "TRY_FINALLY gen ENTER", **snap(region)})
    if is_loop:
        LOG.append({"ev": "LOOP gen ENTER", **snap(region)})
    r = orig_tf(self, region)
    if is_tf:
        LOG.append({"ev": "TRY_FINALLY gen EXIT", **snap(region)})
    if is_loop:
        LOG.append({"ev": "LOOP gen EXIT", **snap(region),
                    "has_orelse_in_res": "'orelse'" in repr(r)})
    return r
rag.RegionASTGenerator._generate_region = patched_gr

from pycdc import PycDecompiler
dec = PycDecompiler()
dec.load_file(r"f:\Downloads\pythoncdc-main\test_repros\round10\r10_21_fin_loopctrl.pyc")
out = io.StringIO()
dec.decompile(out, use_region=True)
with open(r"f:\Downloads\pythoncdc-main\.trae\specs\adversarial-complete-forms-v2-10rounds\rounds\round1\probes_fixB\b71f_trace.json", "w", encoding="utf-8") as f:
    json.dump(LOG, f, indent=1, default=str)
print("log_n=", len(LOG))
