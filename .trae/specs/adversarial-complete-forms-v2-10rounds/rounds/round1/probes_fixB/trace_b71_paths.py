"""B71 取证 4：确认修复分支是否被触发 + 链/If 的实际发射入口"""
import sys, io
sys.path.insert(0, r"f:\Downloads\pythoncdc-main")
import core.cfg.region_ast_generator as rag

LOG = []

# 1) _generate_if 入口：打印链结构与 elif_conditions 成员归属判定
orig_gif = rag.RegionASTGenerator._generate_if


def patched_gif(self, region):
    rt = str(getattr(region, 'region_type', None))
    if 'IF' in rt:
        ecs = getattr(region, 'elif_conditions', None)
        info = {"rt": rt, "entry": region.entry.start_offset,
                "elifs": [getattr(e, 'start_offset', None) for e in (ecs or [])],
                "else_blocks": [getattr(b, 'start_offset', None) for b in (getattr(region, 'else_blocks', None) or [])]}
        LOG.append(("gif", info))
    r = orig_gif(self, region)
    if 'IF' in str(getattr(region, 'region_type', None)):
        LOG.append(("gif_ret", repr(r)[:150]))
    return r


rag.RegionASTGenerator._generate_if = patched_gif

# 2) D1 断点检查：blk74 前驱的 loop_header 标志
from core.cfg import build_cfg
import dis, types

orig_try = rag.RegionASTGenerator._generate_try


def patched_try(self, region):
    r = orig_try(self, region)
    co = self.cfg.code.co_name if self.cfg.code else "?"
    if co == "fin_break":
        fbs = getattr(region, 'finally_blocks', None) or []
        for fb in fbs:
            if fb.start_offset == 74:
                preds = [(p.start_offset, bool(getattr(p, 'loop_header', False)))
                         for p in (getattr(fb, 'predecessors', None) or [])]
                LOG.append(("blk74_preds", preds))
    return r


rag.RegionASTGenerator._generate_try = patched_try

from pycdc import PycDecompiler
dec = PycDecompiler()
dec.load_file(r"f:\Downloads\pythoncdc-main\test_repros\round10\r10_21_fin_loopctrl.pyc")
out = io.StringIO()
dec.decompile(out, use_region=True)

for kind, info in LOG:
    if kind in ("blk74_preds",):
        print(kind, info)
for kind, info in LOG:
    if kind == "gif" and info.get("elifs"):
        print(kind, info)
