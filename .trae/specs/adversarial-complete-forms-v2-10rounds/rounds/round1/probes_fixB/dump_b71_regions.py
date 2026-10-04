"""B71 取证 2：导出 fin_break/fin_continue 全部区域结构字段 + 完整函数 AST"""
import sys, io, json
sys.path.insert(0, r"f:\Downloads\pythoncdc-main")
import core.cfg.region_ast_generator as rag

TARGET = {"fin_break", "fin_continue"}
DUMP = []


def dump_region(r, co):
    d = {
        "co": co, "type": str(getattr(r, "region_type", None)),
        "entry": r.entry.start_offset if getattr(r, "entry", None) else None,
        "merge": r.merge_block.start_offset if getattr(r, "merge_block", None) else None,
        "blocks": sorted(b.start_offset for b in getattr(r, "blocks", []) or []),
        "id": id(r) % 100000,
    }
    for attr in ("try_blocks", "else_blocks", "finally_blocks", "cleanup_blocks",
                 "handler_entry_blocks", "break_blocks", "continue_blocks",
                 "then_blocks", "elif_conditions", "exit_block"):
        v = getattr(r, attr, None)
        if v:
            if isinstance(v, list):
                d[attr] = sorted(getattr(b, "start_offset", b) for b in v)
            elif isinstance(v, dict):
                d[attr] = sorted((getattr(k, "start_offset", k), getattr(v, "start_offset", None)) for k in v.keys())
            else:
                d[attr] = str(v)[:120]
    fcb = getattr(r, "finally_copy_blocks", None)
    if fcb:
        d["finally_copy_keys"] = sorted(getattr(k, "start_offset", k) for k in fcb.keys())
        d["finally_copy_vals"] = sorted(getattr(v, "start_offset", None) for v in fcb.values())
    hs = getattr(r, "except_handlers", None)
    if hs:
        d["handlers"] = [(h[0].start_offset if getattr(h[0], "start_offset", None) is not None else str(h[0]),
                          sorted(getattr(b, "start_offset", b) for b in h[2])) for h in hs]
    for attr in ("has_finally", "try_offset_end", "parent", "is_augassign"):
        v = getattr(r, attr, None)
        if v is not None and attr != "parent":
            d[attr] = v
    p = getattr(r, "parent", None)
    if p is not None:
        d["parent"] = str(getattr(p, "region_type", None)) + "@" + str(p.entry.start_offset if getattr(p, "entry", None) else None)
    return d


orig_gen = rag.RegionASTGenerator.generate
def patched_gen(self):
    r = orig_gen(self)
    co = self.cfg.code.co_name if self.cfg.code else "?"
    if co in TARGET:
        for reg in self.regions:
            DUMP.append(dump_region(reg, co))
        DUMP.append({"co": co, "kind": "AST", "ast": repr(r)[:6000]})
    return r
rag.RegionASTGenerator.generate = patched_gen

from pycdc import PycDecompiler
dec = PycDecompiler()
dec.load_file(r"f:\Downloads\pythoncdc-main\test_repros\round10\r10_21_fin_loopctrl.pyc")
out = io.StringIO()
dec.decompile(out, use_region=True)
with open(r"f:\Downloads\pythoncdc-main\.trae\specs\adversarial-complete-forms-v2-10rounds\rounds\round1\probes_fixB\b71_regions.json", "w", encoding="utf-8") as f:
    json.dump(DUMP, f, indent=1, default=str)
print("regions dumped:", len(DUMP))
