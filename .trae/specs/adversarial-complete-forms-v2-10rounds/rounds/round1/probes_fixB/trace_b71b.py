"""B71b 取证：fin_break 的 If 生成路径全追踪（_generate_if/_if_generate_normal/pib/GBS）"""
import sys, io, json
sys.path.insert(0, r"f:\Downloads\pythoncdc-main")
import core.cfg.region_ast_generator as rag

CO = "fin_break"
LOG = []


def co(self):
    return self.cfg.code.co_name if self.cfg.code else "?"


def watch_blocks(blocks):
    return [getattr(b, "start_offset", b) for b in (blocks or [])]


orig_gif = rag.RegionASTGenerator._generate_if
def patched_gif(self, region):
    r = orig_gif(self, region)
    if co(self) == CO:
        LOG.append({"fn": "_generate_if", "entry": getattr(region.entry, "start_offset", None),
                    "type": str(getattr(region, "region_type", None)),
                    "then": watch_blocks(getattr(region, "then_blocks", None)),
                    "res": repr(r)[:300]})
    return r
rag.RegionASTGenerator._generate_if = patched_gif

orig_gin = rag.RegionASTGenerator._if_generate_normal
def patched_gin(self, region):
    r = orig_gin(self, region)
    if co(self) == CO:
        LOG.append({"fn": "_if_generate_normal", "entry": getattr(region.entry, "start_offset", None),
                    "res": repr(r)[:300]})
    return r
rag.RegionASTGenerator._if_generate_normal = patched_gin

orig_pib = rag.RegionASTGenerator._process_if_blocks
def patched_pib(self, blocks, region, branch="then", anchor_stmts=None):
    r = orig_pib(self, blocks, region, branch, anchor_stmts)
    if co(self) == CO:
        LOG.append({"fn": "pib", "blocks": watch_blocks(blocks), "branch": branch,
                    "res": repr(r)[:300]})
    return r
rag.RegionASTGenerator._process_if_blocks = patched_pib

orig_gbs = rag.RegionASTGenerator._generate_block_statements
def patched_gbs(self, block, *a, **k):
    r = orig_gbs(self, block, *a, **k)
    if co(self) == CO:
        LOG.append({"fn": "gbs", "blk": getattr(block, "start_offset", None),
                    "res": repr(r)[:200]})
    return r
rag.RegionASTGenerator._generate_block_statements = patched_gbs

orig_ghbs = rag.RegionASTGenerator._generate_handler_body_statements
def patched_ghbs(self, block, *a, **k):
    r = orig_ghbs(self, block, *a, **k)
    if co(self) == CO:
        LOG.append({"fn": "hbs", "blk": getattr(block, "start_offset", None),
                    "res": repr(r)[:200]})
    return r
rag.RegionASTGenerator._generate_handler_body_statements = patched_ghbs

# 角色快照
orig_gr = rag.RegionASTGenerator._generate_region
def patched_gr(self, region):
    rid = id(region)
    self._generating_regions.add(rid)
    try:
        r = orig_gr(self, region)
    finally:
        self._generating_regions.discard(rid)
    if co(self) == CO:
        LOG.append({"fn": "_generate_region", "type": str(getattr(region, "region_type", None)),
                    "entry": getattr(region.entry, "start_offset", None),
                    "blocks": watch_blocks(getattr(region, "blocks", None)),
                    "res": repr(r)[:300]})
    return r
rag.RegionASTGenerator._generate_region = patched_gr

from pycdc import PycDecompiler
dec = PycDecompiler()
dec.load_file(r"f:\Downloads\pythoncdc-main\test_repros\round10\r10_21_fin_loopctrl.pyc")
out = io.StringIO()
dec.decompile(out, use_region=True)
with open(r"f:\Downloads\pythoncdc-main\.trae\specs\adversarial-complete-forms-v2-10rounds\rounds\round1\probes_fixB\b71b_trace.json", "w", encoding="utf-8") as f:
    json.dump(LOG, f, indent=1, default=str)
print("log_n=", len(LOG))
