"""B71 取证 5：块角色 + chain children + finalbody 装配定位"""
import sys, io, json
sys.path.insert(0, r"f:\Downloads\pythoncdc-main")
import core.cfg.region_ast_generator as rag

LOG = []
CO_WATCH = {"fin_break", "fin_continue"}
OFFS = (16, 26, 28, 38, 42, 44, 58, 60, 72, 74, 76, 90, 96, 104)


def co(self):
    return self.cfg.code.co_name if self.cfg.code else "?"


orig_gen = rag.RegionASTGenerator.generate
def patched_gen(self):
    r = orig_gen(self)
    c = co(self)
    if c in CO_WATCH:
        for reg in self.regions:
            et = getattr(reg, "entry", None)
            if et is None or et.start_offset != 16:
                continue
            kids = []
            for ch in (getattr(reg, "children", None) or []):
                kids.append((str(getattr(ch, "region_type", None)),
                             ch.entry.start_offset if getattr(ch, "entry", None) else None))
            LOG.append({"co": c, "type": str(getattr(reg, "region_type", None)),
                        "children": kids,
                        "blocks": sorted(b.start_offset for b in getattr(reg, "blocks", []))})
        # 块角色
        for b in self.cfg.blocks:
            if b.start_offset in OFFS:
                LOG.append({"co": c, "kind": "role", "off": b.start_offset,
                            "role": str(self.region_analyzer.get_block_role(b)),
                            "instrs": [i.opname for i in b.instructions if i.opname not in ("RESUME", "NOP", "CACHE")],
                            "preds": sorted(p.start_offset for p in b.predecessors),
                            "loop_header": bool(getattr(b, "loop_header", None))})
    return r
rag.RegionASTGenerator.generate = patched_gen

# 定位 finalbody 装配：hook _generate_try 期间搜 If 构造——改为直接在 _generate_try 内部
# 用 traceback 抓 Return(total) 的产生点成本高，先记录 pib 全调用（无 WATCH 过滤）
orig_pib = rag.RegionASTGenerator._process_if_blocks
def patched_pib(self, blocks, region, branch="then", anchor_stmts=None):
    r = orig_pib(self, blocks, region, branch, anchor_stmts)
    if co(self) in CO_WATCH:
        offs = [b.start_offset for b in blocks]
        if any(o in OFFS for o in offs):
            LOG.append({"co": co(self), "kind": "pib", "blocks": offs, "branch": branch,
                        "region_t": str(getattr(region, "region_type", None)),
                        "n": len(r) if isinstance(r, list) else repr(r)[:80]})
    return r
rag.RegionASTGenerator._process_if_blocks = patched_pib

from pycdc import PycDecompiler
dec = PycDecompiler()
dec.load_file(r"f:\Downloads\pythoncdc-main\test_repros\round10\r10_21_fin_loopctrl.pyc")
out = io.StringIO()
dec.decompile(out, use_region=True)
with open(r"f:\Downloads\pythoncdc-main\.trae\specs\adversarial-complete-forms-v2-10rounds\rounds\round1\probes_fixB\b71_roles.json", "w", encoding="utf-8") as f:
    json.dump(LOG, f, indent=1, default=str)
print("entries:", len(LOG))
