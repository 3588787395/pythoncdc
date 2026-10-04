"""B71c 取证：循环区域事实（has_break/break_blocks/else_blocks 前驱）+ 块归属 dump"""
import sys, io, json
sys.path.insert(0, r"f:\Downloads\pythoncdc-main")
import core.cfg.region_ast_generator as rag

CO = "fin_break"
LOG = []


def offs(blocks):
    return [getattr(b, "start_offset", b) for b in (blocks or [])]


orig_gl = rag.RegionASTGenerator._generate_loop
def patched_gl(self, region, *a, **k):
    if co(self) == CO:
        bb = {}
        for b in (getattr(region, "break_blocks", None) or []):
            bb[getattr(b, "start_offset", None)] = offs(b.successors)
        eb_preds = {}
        for b in (getattr(region, "else_blocks", None) or []):
            eb_preds[getattr(b, "start_offset", None)] = offs(b.predecessors)
        LOG.append({"fn": "_generate_loop", "type": str(getattr(region, "region_type", None)),
                    "entry": getattr(region.entry, "start_offset", None),
                    "has_break": getattr(region, "has_break", None),
                    "header": offs([getattr(region, "header_block", None)]),
                    "cond": offs([getattr(region, "condition_block", None)]),
                    "back_edge": offs([getattr(region, "back_edge_block", None)]),
                    "body": offs(getattr(region, "body_blocks", None)),
                    "blocks": offs(getattr(region, "blocks", None)),
                    "else_blocks": offs(getattr(region, "else_blocks", None)),
                    "else_preds": eb_preds,
                    "break_blocks_succ": bb})
    return orig_gl(self, region, *a, **k)
rag.RegionASTGenerator._generate_loop = patched_gl


def co(self):
    return self.cfg.code.co_name if self.cfg.code else "?"


# 函数结束时 dump 全区域归属 + block_to_region
orig_bfd = getattr(rag.RegionASTGenerator, "_build_function_def", None)
if orig_bfd is not None:
    def patched_bfd(self, *a, **k):
        r = orig_bfd(self, *a, **k)
        if co(self) == CO:
            regs = []
            for _tr in self.region_analyzer.regions:
                regs.append({"type": str(getattr(_tr, "region_type", None)),
                             "entry": getattr(_tr.entry, "start_offset", None),
                             "blocks": offs(getattr(_tr, "blocks", None)),
                             "try_blocks": offs(getattr(_tr, "try_blocks", None)),
                             "finally_blocks": offs(getattr(_tr, "finally_blocks", None))})
            b2r = {}
            for _b, _rg in self.region_analyzer.block_to_region.items():
                b2r[getattr(_b, "start_offset", _b)] = (
                    str(getattr(_rg, "region_type", None)) + "@" +
                    str(getattr(_rg.entry, "start_offset", None)))
            gen = sorted(o for o in (getattr(b, "start_offset", b) for b in self.generated_blocks))
            LOG.append({"fn": "_build_function_def", "regions": regs, "block_to_region": b2r,
                        "generated": gen})
        return r
    rag.RegionASTGenerator._build_function_def = patched_bfd

from pycdc import PycDecompiler
dec = PycDecompiler()
dec.load_file(r"f:\Downloads\pythoncdc-main\test_repros\round10\r10_21_fin_loopctrl.pyc")
out = io.StringIO()
dec.decompile(out, use_region=True)
with open(r"f:\Downloads\pythoncdc-main\.trae\specs\adversarial-complete-forms-v2-10rounds\rounds\round1\probes_fixB\b71c_trace.json", "w", encoding="utf-8") as f:
    json.dump(LOG, f, indent=1, default=str)
print("log_n=", len(LOG))
