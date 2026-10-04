"""B76b 诊断：块布局 + 归属 + generated 全 dump"""
import sys, io, json
sys.path.insert(0, r"f:\Downloads\pythoncdc-main")
import core.cfg.region_ast_generator as rag

WATCH = {"v_aug_boolop_rhs"}
LOG = []


def co(self):
    return self.cfg.code.co_name if self.cfg.code else "?"


orig_bfd = rag.RegionASTGenerator._build_function_def
def patched_bfd(self, *a, **k):
    r = orig_bfd(self, *a, **k)
    print("bfd called, co=", co(self), file=sys.stderr)
    if co(self) in WATCH:
        blocks = []
        for b in self.cfg.get_blocks_in_order():
            blocks.append({"off": b.start_offset,
                           "instrs": [i.opname for i in b.instructions],
                           "succs": [s.start_offset for s in b.successors],
                           "preds": [p.start_offset for p in b.predecessors]})
        regs = []
        for _tr in self.region_analyzer.regions:
            regs.append({"type": str(getattr(_tr, "region_type", None)),
                         "entry": getattr(_tr.entry, "start_offset", None),
                         "blocks": [getattr(b, "start_offset", b) for b in (getattr(_tr, "blocks", None) or [])]})
        b2r = {}
        for _b, _rg in self.region_analyzer.block_to_region.items():
            b2r[getattr(_b, "start_offset", _b)] = (str(getattr(_rg, "region_type", None)) + "@" +
                                                    str(getattr(_rg.entry, "start_offset", None)))
        gen = sorted(o for o in (getattr(b, "start_offset", b) for b in self.generated_blocks))
        gen_off = sorted(self.generated_offsets)
        LOG.append({"fn": co(self), "blocks": blocks, "regions": regs,
                    "block_to_region": b2r, "generated_blocks": gen,
                    "generated_offsets": gen_off})
    return r
rag.RegionASTGenerator._build_function_def = patched_bfd

from pycdc import PycDecompiler
dec = PycDecompiler()
dec.load_file(r"f:\Downloads\pythoncdc-main\test_repros\round10\rv10_32_augassign_variant.pyc")
out = io.StringIO()
dec.decompile(out, use_region=True)
with open(r"f:\Downloads\pythoncdc-main\.trae\specs\adversarial-complete-forms-v2-10rounds\rounds\round1\probes_fixB\b76b_trace.json", "w", encoding="utf-8") as f:
    json.dump(LOG, f, indent=1, default=str)
print("log_n=", len(LOG))
