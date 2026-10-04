"""B71d 取证：最终函数 AST 完整 dump（不截断）— 定位 Break 丢失/return 蒸发的确切位置"""
import sys, io, json
sys.path.insert(0, r"f:\Downloads\pythoncdc-main")
import core.cfg.region_ast_generator as rag

WATCH = {"fin_break", "fin_continue", "fin_continue_stmt"}
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

# hbs(44)/hbs(26) 完整输出
orig_hbs = rag.RegionASTGenerator._generate_handler_body_statements
def patched_hbs(self, block, *a, **k):
    r = orig_hbs(self, block, *a, **k)
    if co(self) in WATCH and getattr(block, "start_offset", None) in (26, 44):
        LOG.append({"fn": co(self), "hbs_blk": getattr(block, "start_offset", None), "res": r})
    return r
rag.RegionASTGenerator._generate_handler_body_statements = patched_hbs

from pycdc import PycDecompiler
dec = PycDecompiler()
dec.load_file(r"f:\Downloads\pythoncdc-main\test_repros\round10\r10_21_fin_loopctrl.pyc")
out = io.StringIO()
dec.decompile(out, use_region=True)
with open(r"f:\Downloads\pythoncdc-main\.trae\specs\adversarial-complete-forms-v2-10rounds\rounds\round1\probes_fixB\b71d_trace.json", "w", encoding="utf-8") as f:
    json.dump(LOG, f, indent=1, default=str)
print("log_n=", len(LOG))
