"""[B75c] 取证：完整 generate() 驱动 + _generate_try 认领点插桩回放。"""
import sys
import traceback

sys.path.insert(0, r'F:\Downloads\pythoncdc-main')

import marshal

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

PYC = r'F:\Downloads\pythoncdc-main\test_repros\round10\r10_15_global_hosts.pyc'


def load_code(pyc):
    with open(pyc, 'rb') as f:
        data = f.read()
    return marshal.loads(data[16:])


mod = load_code(PYC)

# 插桩：wrap _b75_consume_arm_return_copies 与 _generate_try_body / handler 认领
_orig_b75 = RegionASTGenerator._b75_consume_arm_return_copies
_orig_trybody = RegionASTGenerator._generate_try_body


def _wrap_b75(self, region):
    print(f'[B75] enter region@{getattr(region.entry, "start_offset", "?")} '
          f'has_finally={getattr(region, "has_finally", False)}')
    try:
        _orig_b75(self, region)
    except Exception:
        traceback.print_exc()
        raise
    print(f'[B75] exit try_arm_rets={getattr(region, "_b75_try_arm_returns", None)} '
          f'handler_rets={getattr(region, "_b75_handler_returns", None)}')


def _wrap_trybody(self, region):
    stmts = _orig_trybody(self, region)
    print(f'[B75] _generate_try_body@{getattr(region.entry, "start_offset", "?")} '
          f'-> {len(stmts)} stmts: {[s.get("type") for s in stmts]}')
    return stmts


RegionASTGenerator._b75_consume_arm_return_copies = _wrap_b75
RegionASTGenerator._generate_try_body = _wrap_trybody

try:
    cfg = build_cfg(mod)
    gen = RegionASTGenerator(cfg, top_level_code=mod)
    ast_dict = gen.generate()
    fns = ast_dict.get('functions', []) if isinstance(ast_dict, dict) else []
    print(f'=== module stmts keys: {list(ast_dict.keys()) if isinstance(ast_dict, dict) else type(ast_dict)}')
    body = ast_dict.get('body', []) if isinstance(ast_dict, dict) else []
    for s in body:
        if s.get('type') == 'FunctionDef' and s.get('name') == 'g_in_try_except':
            print('=== g_in_try_except ast ===')
            print(repr(s.get('body')))
except Exception:
    traceback.print_exc()
