"""B76 诊断：v_aug_boolop_rhs 最终 AST dump"""
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
    if co(self) in WATCH:
        LOG.append({"fn": co(self), "ast": r})
    return r
rag.RegionASTGenerator._build_function_def = patched_bfd

orig_gr = rag.RegionASTGenerator._generate_region
def patched_gr(self, region):
    r = orig_gr(self, region)
    if co(self) in WATCH:
        LOG.append({"fn": "_generate_region", "type": str(getattr(region, "region_type", None)),
                    "entry": getattr(region.entry, "start_offset", None),
                    "blocks": [getattr(b, "start_offset", b) for b in (getattr(region, "blocks", None) or [])],
                    "res": repr(r)[:300]})
    return r
rag.RegionASTGenerator._generate_region = patched_gr

from pycdc import PycDecompiler
dec = PycDecompiler()
dec.load_file(r"f:\Downloads\pythoncdc-main\test_repros\round10\rv10_32_augassign_variant.pyc")
out = io.StringIO()
dec.decompile(out, use_region=True)
with open(r"f:\Downloads\pythoncdc-main\.trae\specs\adversarial-complete-forms-v2-10rounds\rounds\round1\probes_fixB\b76_trace.json", "w", encoding="utf-8") as f:
    json.dump(LOG, f, indent=1, default=str)
print("log_n=", len(LOG))
