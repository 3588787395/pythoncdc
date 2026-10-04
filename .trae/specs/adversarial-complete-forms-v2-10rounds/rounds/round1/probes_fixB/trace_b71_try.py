"""B71 取证 4：_generate_try 装配取证（nc_blocks + generated_blocks 增量 + finalbody 来源）"""
import sys, io, json, traceback
sys.path.insert(0, r"f:\Downloads\pythoncdc-main")
import core.cfg.region_ast_generator as rag

LOG = []
CO_WATCH = {"fin_break", "fin_continue"}


def co(self):
    return self.cfg.code.co_name if self.cfg.code else "?"


orig_nc = rag.RegionASTGenerator._find_finally_normal_copy_blocks
def patched_nc(self, region):
    r = orig_nc(self, region)
    if co(self) in CO_WATCH:
        LOG.append({"kind": "nc", "co": co(self), "region_entry": region.entry.start_offset if region.entry else None,
                    "nc": sorted(b.start_offset for b in r)})
    return r
rag.RegionASTGenerator._find_finally_normal_copy_blocks = patched_nc

orig_try = rag.RegionASTGenerator._generate_try
def patched_try(self, region):
    before = set(self.generated_blocks)
    r = orig_try(self, region)
    if co(self) in CO_WATCH:
        added = sorted(b.start_offset for b in (self.generated_blocks - before))
        fb = r.get('finalbody') if isinstance(r, dict) else None
        LOG.append({"kind": "try", "co": co(self), "region_entry": region.entry.start_offset if region.entry else None,
                    "added_blocks": added, "finalbody": repr(fb)[:600] if fb is not None else None})
    return r
rag.RegionASTGenerator._generate_try = patched_try

orig_hbs = rag.RegionASTGenerator._generate_handler_body_statements
def patched_hbs(self, *a, **k):
    r = orig_hbs(self, *a, **k)
    if co(self) in CO_WATCH:
        blocks = a[1] if len(a) > 1 else None
        offs = sorted(b.start_offset for b in blocks) if blocks else None
        if offs and any(o in (38, 42, 58, 72, 74, 90, 104) for o in offs):
            LOG.append({"kind": "hbs", "co": co(self), "blocks": offs, "result": repr(r)[:400]})
    return r
rag.RegionASTGenerator._generate_handler_body_statements = patched_hbs

orig_gr = rag.RegionASTGenerator._generate_region
def patched_gr(self, region):
    r = orig_gr(self, region)
    c = co(self)
    if c in CO_WATCH and getattr(region, 'entry', None) is not None and region.entry.start_offset in (26, 58, 16):
        LOG.append({"kind": "gen_region", "co": c, "type": str(getattr(region, 'region_type', None)),
                    "entry": region.entry.start_offset, "result": repr(r)[:500]})
    return r
rag.RegionASTGenerator._generate_region = patched_gr

from pycdc import PycDecompiler
dec = PycDecompiler()
dec.load_file(r"f:\Downloads\pythoncdc-main\test_repros\round10\r10_21_fin_loopctrl.pyc")
out = io.StringIO()
dec.decompile(out, use_region=True)
with open(r"f:\Downloads\pythoncdc-main\.trae\specs\adversarial-complete-forms-v2-10rounds\rounds\round1\probes_fixB\b71_trytrace.json", "w", encoding="utf-8") as f:
    json.dump(LOG, f, indent=1, default=str)
print("entries:", len(LOG))
