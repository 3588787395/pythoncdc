import sys, types
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
import core.cfg.region_ast_generator as rag
from core.cfg import decompile

orig_val = rag.RegionASTGenerator._build_ternary_value_expr
def wrapped_val(self, block):
    r = orig_val(self, block)
    print(f"  [dbg] _build_ternary_value_expr({block.start_offset if hasattr(block,'start_offset') else block}) -> {r}")
    return r
rag.RegionASTGenerator._build_ternary_value_expr = wrapped_val

orig_store = rag.RegionASTGenerator._try_build_ternary_store_assign
def wrapped_store(self, region, te):
    r = orig_store(self, region, te)
    print(f"  [dbg] _try_build_ternary_store_assign(te={te}) -> {r}")
    return r
rag.RegionASTGenerator._try_build_ternary_store_assign = wrapped_store

orig_cons = rag.RegionASTGenerator._build_ternary_no_target_consumer_stmt
def wrapped_cons(self, region, te):
    r = orig_cons(self, region, te)
    print(f"  [dbg] _no_target_consumer(te={te}) -> {r}")
    return r
rag.RegionASTGenerator._build_ternary_no_target_consumer_stmt = wrapped_cons

src_f7 = '''class A:
    def __init__(self, total_cash, positions, processed_trade=None):
        self._total_cash = total_cash
        self._processed_trade = processed_trade if processed_trade is not None else set()
        self._transaction_cost = 0
        self.register_event()
'''
print(decompile(src_f7, '<f7>'))
