"""B71 动态取证：hook _process_if_blocks / 区域树导出（fin_break blk@38 / fin_continue blk@72）"""
import sys, io, json
sys.path.insert(0, r"f:\Downloads\pythoncdc-main")

import core.cfg.region_ast_generator as rag

WATCH = {38, 58, 72, 90, 74, 10, 104, 42, 44, 66, 76, 96, 28}  # fin_break/fin_continue 关键块
LOG = []


def dump_block(b):
    if b is None:
        return None
    return {
        "off": b.start_offset,
        "end": getattr(b, "end_offset", None),
        "instrs": [i.opname for i in b.instructions if i.opname not in ("RESUME", "NOP", "CACHE")],
        "semantics": getattr(b, "semantics", None).__class__.__name__ if getattr(b, "semantics", None) is not None else None,
        "role": getattr(getattr(b, "semantics", None), "name", None) if hasattr(getattr(b, "semantics", None), "name") else str(getattr(b, "semantics", None)),
        "succs": sorted(s.start_offset for s in getattr(b, "successors", []) or []),
    }


orig_pib = rag.RegionASTGenerator._process_if_blocks
def patched_pib(self, blocks, region, branch="then", anchor_stmts=None):
    offs = [b.start_offset for b in blocks]
    pre_gen = [b.start_offset for b in blocks if b in self.generated_blocks]
    r = orig_pib(self, blocks, region, branch, anchor_stmts)
    if any(o in WATCH for o in offs):
        LOG.append({
            "kind": "pib", "co": self.cfg.code.co_name if self.cfg.code else "?",
            "blocks": offs, "branch": branch, "pre_generated": pre_gen,
            "region": str(getattr(region, "region_type", None)),
            "region_entry": region.entry.start_offset if getattr(region, "entry", None) else None,
            "result_n": len(r) if isinstance(r, list) else repr(r),
            "result": repr(r)[:400] if any(o in (38, 58, 72, 90, 28) for o in offs) else None,
        })
    return r
rag.RegionASTGenerator._process_if_blocks = patched_pib

orig_gen_region = rag.RegionASTGenerator._generate_region
def patched_gr(self, region):
    r = orig_gen_region(self, region)
    try:
        et = getattr(region, "entry", None)
        if et is not None and et.start_offset in WATCH:
            info = {
                "kind": "region", "co": self.cfg.code.co_name if self.cfg.code else "?",
                "type": str(getattr(region, "region_type", None)),
                "entry": et.start_offset,
                "blocks": sorted(b.start_offset for b in getattr(region, "blocks", []) or []),
                "try_blocks": sorted(b.start_offset for b in getattr(region, "try_blocks", None) or []),
                "finally_blocks": sorted(b.start_offset for b in getattr(region, "finally_blocks", None) or []),
                "finally_copy": sorted((k.start_offset if hasattr(k, "start_offset") else k) for k in (getattr(region, "finally_copy_blocks", None) or {}).keys()),
                "result": repr(r)[:500],
            }
            for attr in ("break_blocks", "continue_blocks"):
                v = getattr(region, attr, None)
                if v:
                    info[attr] = sorted(getattr(b, "start_offset", b) for b in v)
            LOG.append(info)
    except Exception as e:
        LOG.append({"kind": "err", "e": repr(e)})
    return r
rag.RegionASTGenerator._generate_region = patched_gr

from pycdc import PycDecompiler
dec = PycDecompiler()
dec.load_file(r"f:\Downloads\pythoncdc-main\test_repros\round10\r10_21_fin_loopctrl.pyc")
out = io.StringIO()
ok = dec.decompile(out, use_region=True)
src = out.getvalue()
with open(r"f:\Downloads\pythoncdc-main\.trae\specs\adversarial-complete-forms-v2-10rounds\rounds\round1\probes_fixB\b71_gen_src.py", "w", encoding="utf-8") as f:
    f.write(src)
with open(r"f:\Downloads\pythoncdc-main\.trae\specs\adversarial-complete-forms-v2-10rounds\rounds\round1\probes_fixB\b71_trace.json", "w", encoding="utf-8") as f:
    json.dump(LOG, f, indent=1, default=str)
print("ok=", ok, "log_n=", len(LOG))
