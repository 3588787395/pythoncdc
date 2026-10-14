"""R21-43 candidate builder: elif-chain tail arms converge on a pure continue block.

MEASURED DEFECT (base = landed generator 20fa73b4e8231f0f + landed analyzer
c069d359cbfe76b0 + analyzer [R21-40] f7d849e974904492, mirror D:/Temp/r69):
`site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` ->
`_process_cancel_order` is 57 co_code bytes off.  r68a enumerated 25 whole-module
source shapes and shape S05 (`if A / else: (if B / else: C) / continue`) is
BYTE-IDENTICAL to the original (diffs=0, jumps_eq, exc_eq); the product's shape
(`if A / elif B / else: C`, the continue hoisted to after the try) is not.

Ablation (abl.py, byte-exact in-process harness, products below) names the folder:
`_if_generate_elif_chain` (region_ast_generator.py:19589) builds
`{'type':'If','_is_elif':True,...}` at :20783 and `_if_generate_full_elif_chain`
hangs it on the parent If's orelse at :16465 (`_ft3_orelse`).  Swapping
`_if_generate_full_elif_chain` out for `_if_generate_normal` keeps the flat
`if/elif/else`, so the fold lives in the elif-chain builder, not the dispatcher.

CFG facts read at identification time (region_analyzer data + opcode class only):
  IfRegion@946 IF_ELIF_CHAIN  cond=@946  elif_conditions=[@1608]  elif_bodies[0]=[@1710]
                            elif_final_else=[@1712]  merge_block=@1826
  @1710 terminal JUMP_FORWARD -> @1822 ; @1712 falls through -> @1822 (@1828 is the
  exception edge) ; @1822 = [EXTENDED_ARG, JUMP_BACKWARD -> @44] with predecessors
  {@1710, @1712} only ; @44 is the pure-noise single-successor predecessor of the
  loop header @46 ; @1826 has forward successors and is NOT reached by those two arms.
A flat elif chain makes its last two arms exit at the chain merge, so merge != the
arms' exit target is the proof that the two arms share one source suite whose tail
is the continue: the arm must be rendered `else: If(...)`, with the Continue inside
that suite.  Fix = statement assembly (drop `_is_elif`, set `_is_nested_if`, append
Continue, claim the convergence block), no jump-target arithmetic.

usage: python -X utf8 build_cand_r69a_R21-43_nested_else_continue.py <generator-file>
"""
import hashlib
import py_compile
import sys

CRLF = b"\r\n"
PRE_HASH = "20fa73b4e8231f0f"          # landed gate-37 generator

ANCHOR_HELPER = b"    def _if_generate_full_elif_chain(self, region: IfRegion) -> Dict[str, Any]:"
ANCHOR_TRIGGER = (b"        result = {'type': 'If', 'test': condition, 'body': then_stmts"
                  b" if then_stmts else [{'type': 'Pass'}], 'orelse': _ft3_orelse}")

HELPER = '''    # \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
    # [R21-43] elif \u94fe\u5c3e\u4e24\u81c2\u6536\u655b\u4e8e\u300c\u7eaf continue \u5757\u300d\u21d2 \u7b2c\u4e09\u81c2\u4e0d\u5f97\u6298\u53e0\u6210 elif
    # \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
    def _r2143_block_is_pure_continue(self, block, hdr):
        """[R21-43] \u7ed3\u6784\u4e8b\u5b9e\u2460\uff1a`block` \u662f\u4e00\u6761\u6e90\u7801\u7ea7 `continue` \u8bed\u53e5\u7684\u552f\u4e00\u5b9e\u4f53\u5757\u3002

        \u53bb\u6389\u566a\u58f0\u6307\u4ee4\uff08NOISE_OPS\uff0c\u4ee5\u53ca\u4f5c\u4e3a\u8df3\u8f6c\u64cd\u4f5c\u6570\u524d\u7f00\u7684 EXTENDED_ARG\uff09\u540e\uff0c
        \u5757\u91cc\u5269\u4e0b\u7684**\u552f\u4e00**\u4e00\u6761\u6307\u4ee4\u5c31\u662f\u5b83\u7684\u7ec8\u7ed3\u5b50\uff0c\u4e14\u8be5\u7ec8\u7ed3\u5b50\u662f\u56de\u8df3\uff1b\u5176\u843d\u70b9
        \u8981\u4e48\u662f\u5faa\u73af header \u672c\u8eab\uff0c\u8981\u4e48\u662f header \u7684\u300c\u7eaf\u566a\u58f0\u5355\u540e\u7ee7\u524d\u9a71\u5757\u300d\uff08CPython 3.11
        \u4e3a while \u5faa\u73af\u653e\u5728 header \u524d\u7684 NOP\uff0ccontinue \u8df3\u7684\u5c31\u662f\u5b83\uff09\u2014\u2014\u540e\u8005\u4e0e\u5df2\u843d\u5730\u7684
        [R21-40]\uff08\u5206\u6790\u7aef\u540c\u4e00\u8c13\u8bcd\uff09\u9010\u5b57\u4e00\u81f4\uff0c\u4e0d\u662f\u65b0\u8c13\u8bcd\u3002
        \u4e0d\u8bfb\u51fd\u6570\u540d\u3001\u5e38\u91cf\u3001\u7edd\u5bf9\u504f\u79fb\uff1b\u300c\u5269\u4e0b\u552f\u4e00\u4e00\u6761\u6307\u4ee4 = \u7ec8\u7ed3\u5b50\u300d\u662f\u5757\u7684\u89d2\u8272\u5b9a\u4e49\uff0c
        \u4e0d\u662f\u6307\u4ee4\u6570\u9608\u503c\u3002
        """
        _r2143_rest = [i for i in (getattr(block, 'instructions', None) or [])
                       if i.opname not in NOISE_OPS and i.opname != 'EXTENDED_ARG']
        if len(_r2143_rest) != 1:
            return False
        _r2143_one = _r2143_rest[0]
        if _r2143_one.opname not in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'):
            return False
        if not isinstance(_r2143_one.argval, int):
            return False
        _r2143_tgt = self.cfg.get_block_by_offset(_r2143_one.argval)
        if _r2143_tgt is None:
            return False
        if _r2143_tgt is hdr:
            return True
        _r2143_reentry = list(_r2143_tgt.successors or [])
        if (_r2143_tgt.start_offset >= hdr.start_offset
                or [i for i in (_r2143_tgt.instructions or [])
                    if i.opname not in NOISE_OPS and i.opname != 'EXTENDED_ARG']
                or len(_r2143_reentry) != 1 or hdr not in _r2143_reentry):
            return False
        return True

    def _r2143_arm_exit_target(self, tail):
        """[R21-43] \u7ed3\u6784\u4e8b\u5b9e\u2461\uff1a\u81c2\u5757\u5e8f\u5217\u672b\u5757 `tail` \u7684**\u6b63\u5e38\u51fa\u53e3\u5757**\u3002

        - `tail` \u7684\u7ec8\u7ed3\u5b50\u662f\u65e0\u6761\u4ef6\u524d\u8df3\uff08JUMP_FORWARD / JUMP_ABSOLUTE\uff09\u21d2 \u51fa\u53e3 = \u8df3\u8f6c\u76ee\u6807\u5757\uff1b
        - `tail` \u7684\u7ec8\u7ed3\u5b50\u4e0d\u662f\u8df3\u8f6c\uff08\u81c2\u76f4\u843d\uff09\u21d2 \u51fa\u53e3 = \u552f\u4e00\u7684\u975e\u5f02\u5e38\u540e\u7ee7\uff08\u6392\u9664\u4ee5
          PUSH_EXC_INFO / WITH_EXCEPT_START \u5f00\u5934\u7684\u5757\uff0c\u4e0e\u5df2\u843d\u5730 [R39-B] \u540c\u4e00\u6392\u9664\uff09\uff1b
        - \u5176\u5b83\u5f62\u6001\uff08\u6761\u4ef6\u8df3\u8f6c\u7ed3\u5c3e\u3001\u56de\u8fb9\u3001return\u3001raise\uff09\u21d2 None\uff0c\u5224\u636e\u4e0d\u6210\u7acb\u3002
        """
        _r2143_last = tail.get_last_instruction()
        if _r2143_last is None:
            return None
        if _r2143_last.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE'):
            if not isinstance(_r2143_last.argval, int):
                return None
            return self.cfg.get_block_by_offset(_r2143_last.argval)
        if 'JUMP' in _r2143_last.opname:
            return None
        _r2143_succs = [s for s in (list(getattr(tail, 'successors', None) or []))
                        if s.start_offset > tail.start_offset
                        and not (list(getattr(s, 'instructions', None) or [])
                                 and s.get_first_instruction().opname in
                                 ('PUSH_EXC_INFO', 'WITH_EXCEPT_START'))]
        return _r2143_succs[0] if len(_r2143_succs) == 1 else None

    def _r2143_last_arms_converge_on_continue(self, region: IfRegion):
        """[R21-43] \u5224\u636e\uff1a\u672c elif \u94fe\u7684\u300c\u6700\u540e\u4e00\u4e2a elif \u81c2\u300d\u4e0e\u300c\u94fe\u5c3e else \u81c2\u300d\u662f\u5426\u5171\u540c\u843d\u5230
        \u540c\u4e00\u4e2a\u7eaf continue \u5757 T\uff0c\u4e14 T \u4e0d\u662f\u672c\u94fe\u7684 merge_block\u3002

        \u4e3a\u4ec0\u4e48\u8fd9\u662f\u300c\u5fc5\u987b\u5d4c\u5957\u300d\u7684\u8bc1\u660e\uff0c\u800c\u4e0d\u662f\u4e00\u4e2a\u504f\u597d\uff1aCPython \u7684\u5757\u5e03\u5c40\u91cc\uff0c\u5199\u6210
        `if A / elif B / else C` \u65f6 B\u3001C \u4e24\u81c2\u7684\u51fa\u53e3\u6070\u597d\u662f**\u6574\u6761\u94fe\u7684\u6c47\u5408\u70b9**\uff08\u5373
        region.merge_block\uff09\uff1b\u5199\u6210 `if A / else: (if B / else: C) / continue` \u65f6\uff0cB\u3001C
        \u7684\u51fa\u53e3\u662f\u90a3\u4e2a\u5d4c\u5957 if \u81ea\u5df1\u7684\u6c47\u5408\u70b9\uff0c\u800c\u8be5\u70b9\u6b63\u662f\u540e\u7ee7\u8bed\u53e5 `continue` \u7684\u5b9e\u4f53\u5757 T\uff0c
        \u94fe\u7684 merge_block \u53e6\u6709\u5176\u5757\uff08A \u81c2\u51fa\u53e3\u8df3\u7684\u5c31\u662f\u5b83\uff09\u3002\u4e8e\u662f\u300c\u4e24\u81c2\u51fa\u53e3\u76f8\u540c\u4e14\u4e3a\u7eaf
        continue \u5757\u3001\u4e14\u4e0d\u7b49\u4e8e merge_block\u300d\u5728 flat \u5e03\u5c40\u4e0b\u4e0d\u53ef\u80fd\u51fa\u73b0\uff1a\u5b83\u53ea\u80fd\u662f\u5d4c\u5957\u5f62\u72b6\u3002

        \u53ef\u7528\u6570\u636e\u5168\u90e8\u6765\u81ea\u533a\u57df\u58f0\u660e\u4e0e opcode \u7c7b\u522b / \u524d\u9a71\u540e\u7ee7\u5173\u7cfb\uff1a
          \u2462 \u94fe\u53ea\u6709\u4e00\u4e2a elif \u6761\u4ef6\u5757\u4e0e\u4e00\u7ec4 elif \u81c2\u5757\uff08\u6b64\u65f6\u88ab\u6298\u53e0\u7684\u8282\u70b9\u6070\u597d\u662f
             \u300c\u8fd9\u4e00\u4e2a elif \u81c2 + \u94fe\u5c3e else \u81c2\u300d\uff0c\u5176\u4f59\u591a elif \u94fe\u7684\u6839\u8282\u70b9\u4e0d\u662f\u8be5\u4e24\u81c2\uff0c\u6545\u610f\u4e0d\u70e9\uff09\uff1b
          \u2463 \u4e24\u81c2\u5757\u5e8f\u5217\u7684\u6b63\u5e38\u51fa\u53e3\u5757\u5b58\u5728\u4e14\u4e3a\u540c\u4e00\u5757 T\uff08\u2461\uff09\uff1b
          \u2464 T \u4e0d\u662f\u672c\u94fe merge_block\u3001\u4e0d\u5728\u672c\u94fe blocks \u5185\u3001\u4e0d\u662f\u5faa\u73af\u6307\u5b9a\u7684
             back_edge_block / back_edge_blocks\uff08\u90a3\u662f\u5faa\u73af\u4f53\u81ea\u7136\u5c3e\uff0c\u4e0d\u662f\u6e90\u7801 continue\uff09\uff0c
             \u4e5f\u5c1a\u672a\u88ab\u53d1\u5c04\uff08\u539f\u5219 2 \u6bcf\u5757\u552f\u4e00\u5f52\u5c5e\uff09\uff1b
          \u2465 T \u662f\u7eaf continue \u5757\uff08\u2460\uff0c\u843d\u70b9 = \u5f53\u524d\u5faa\u73af header \u6216\u5176\u7eaf\u566a\u58f0\u5355\u540e\u7ee7\u524d\u9a71\uff09\uff1b
          \u2466 T \u7684\u524d\u9a71\uff08\u9664\u81ea\u8eab\uff09>= 2 \u4e2a\u3001\u5168\u90e8\u5c5e\u4e8e\u8fd9\u4e24\u4e2a\u81c2\uff0c\u4e14\u6bcf\u4e2a\u81c2\u81f3\u5c11\u8d21\u732e\u4e00\u4e2a
             \uff08\u300c\u88ab\u591a\u4e2a\u81c2\u5171\u4eab\u300d\u7684\u51c6\u786e\u542b\u4e49\uff1a\u5171\u4eab\u8005\u662f\u94fe\u7684\u81c2\uff0c\u4e0d\u662f\u522b\u5904\u642c\u6765\u7684\u8fb9\uff09\u3002

        \u4fdd\u5b88\u6027\uff1a\u4efb\u4e00\u6761\u4e0d\u6210\u7acb\u5373\u8fd4\u56de None \u21d2 \u8c03\u7528\u65b9\u4fdd\u6301\u73b0\u6709 flat elif \u6e32\u67d3\uff0c\u4ea7\u7269\u9010\u5b57\u8282\u4e0d\u53d8\u3002
        \u672c\u65b9\u6cd5**\u65e0\u526f\u4f5c\u7528**\uff08\u4e0d\u6539 generated_blocks\u3001\u4e0d\u6539\u533a\u57df\u6570\u636e\uff09\uff0c\u56e0\u6b64\u53ef\u88ab\u63a2\u9488\u5305\u88f9\u505a
        \u70b9\u540d\u6570\u6d3e\uff0c\u4e14\u63a2\u9488\u53ef\u8bc1\u660e\u60ef\u6027\u3002
        """
        _r2143_loop = getattr(self, '_current_loop', None)
        _r2143_hdr = getattr(_r2143_loop, 'header_block', None) if _r2143_loop else None
        if _r2143_hdr is None:
            return None
        _r2143_conds = list(getattr(region, 'elif_conditions', None) or [])
        _r2143_bodies = list(getattr(region, 'elif_bodies', None) or [])
        if len(_r2143_conds) != 1 or len(_r2143_bodies) != 1:
            return None
        _r2143_elif_arm = list(_r2143_bodies[0] or [])
        _r2143_else_arm = list(getattr(region, 'elif_final_else', None) or [])
        if not _r2143_elif_arm or not _r2143_else_arm:
            return None
        _r2143_merge = getattr(region, 'merge_block', None)
        if _r2143_merge is None:
            return None
        _r2143_T = self._r2143_arm_exit_target(_r2143_elif_arm[-1])
        if _r2143_T is None or _r2143_T is not self._r2143_arm_exit_target(_r2143_else_arm[-1]):
            return None
        if _r2143_T is _r2143_merge:
            return None
        _r2143_be = set(getattr(_r2143_loop, 'back_edge_blocks', None) or [])
        if getattr(_r2143_loop, 'back_edge_block', None) is not None:
            _r2143_be.add(_r2143_loop.back_edge_block)
        if _r2143_T in _r2143_be:
            return None
        if _r2143_T in (getattr(region, 'blocks', None) or set()):
            return None
        if _r2143_T in self.generated_blocks:
            return None
        if not self._r2143_block_is_pure_continue(_r2143_T, _r2143_hdr):
            return None
        _r2143_preds = [p for p in (list(getattr(_r2143_T, 'predecessors', None) or []))
                        if p is not _r2143_T]
        if len(_r2143_preds) < 2:
            return None
        _r2143_es = set(_r2143_elif_arm) | set(_r2143_else_arm)
        if not all(p in _r2143_es for p in _r2143_preds):
            return None
        if not (any(p in set(_r2143_elif_arm) for p in _r2143_preds)
                and any(p in set(_r2143_else_arm) for p in _r2143_preds)):
            return None
        return _r2143_T

'''.split("\n")

TRIGGER = '''        # [R21-43] \u94fe\u5c3e\u4e24\u81c2\u6536\u655b\u4e8e\u7eaf continue \u5757 \u21d2 \u89e3\u9664 elif \u6298\u53e0\uff0c\u6539\u53d1 else \u5b50\u53e5\u3002
        # \u8bc6\u522b\u6761\u4ef6\uff08\u5168\u90e8\u4e3a\u7ed3\u6784\u4e8b\u5b9e\uff0c\u89c1 _r2143_last_arms_converge_on_continue\uff09\uff1a
        #   \u2460 \u6b64\u523b\u6302\u5230\u672c if \u5047\u8fb9\u7684 orelse \u53ea\u6709\u4e00\u4e2a\u8282\u70b9\uff0c\u5b83\u662f\u5e26 _is_elif \u7684 If\uff0c
        #      \u4e14\u81ea\u8eab\u5e26\u975e\u7a7a orelse\uff08= \u300c\u6700\u540e\u4e00\u4e2a elif \u81c2 + \u94fe\u5c3e else \u81c2\u300d\u4e24\u7ea7\u7ed3\u6784\uff09\uff1b
        #   \u2461 \u8fd9\u4e24\u4e2a\u81c2\u7684\u6b63\u5e38\u51fa\u53e3\u662f\u540c\u4e00\u4e2a\u7eaf continue \u5757 T\uff0cT \u4e0d\u662f\u672c\u94fe merge_block\u3002
        # \u5f52\u7ea6\u65b9\u5f0f\uff1a\u2461\u6210\u7acb\u65f6 flat elif \u5e03\u5c40\u53ef\u8bc1\u4f2a \u2014\u2014 flat \u94fe\u7684\u8fd9\u4e24\u81c2\u51fa\u53e3\u5fc5\u7136\u662f\u94fe\u7684
        #   merge_block\uff0c\u800c CFG \u5b9e\u6d4b\u5b83\u4eec\u843d\u5728 T\u3002\u6e90\u7801\u91cc\u8fd9\u4e24\u81c2\u540c\u5c5e\u4e00\u4e2a\u8bed\u53e5\u5e8f\u5217\uff0c\u5176\u5c3e\u662f
        #   continue\uff0c\u56e0\u6b64\u7b2c\u4e09\u81c2\u5fc5\u987b\u5199\u6210 `else: If(...)`\u3002\u50cf\u5df2\u843d\u5730 _ft3_elif_shared
        #   \u540c\u4e00\u60ef\u7528\u5199\u6cd5\uff1a\u6458\u6389 _is_elif\u3001\u6807 _is_nested_if\uff08\u53d1\u5c04\u5668\u8d70 code_generator
        #   _generate_elif_or_else \u7684\u300c\u5d4c\u5957 if \u2260 elif\u300d\u5206\u652f\uff0c\u628a orelse \u6574\u4e2a\u5217\u8868\u4f5c\u4e3a else
        #   \u5b50\u53e5\u4f9d\u6b21\u53d1\u5c04\uff09\uff0c\u5e76\u5728 orelse \u672b\u5c3e\u6309\u5e8f\u8865\u4e00\u6761 Continue\uff1b\u540c\u65f6\u6309\u539f\u5219 2 \u8ba4\u9886 T
        #   \uff08\u6807\u8bb0\u5df2\u751f\u6210\uff09\uff0c\u5426\u5219\u5b83\u4f1a\u88ab\u7236\u5e8f\u5217\u5f53\u4f5c\u94fe\u540e/try \u540e\u7684\u5144\u5f1f\u8bed\u53e5\u91cd\u590d\u53d1\u5c04\u3002
        #   \u4e0d\u6539\u52a8\u4efb\u4f55\u8df3\u8f6c\u76ee\u6807\u3001\u4e0d\u8bfb\u540d\u5b57/\u504f\u79fb/\u9608\u503c\uff1b\u4e0d\u70e9\u65f6\u96f6\u526f\u4f5c\u7528 \u21d2 \u4ea7\u7269\u4e0d\u53d8\u3002
        # AST \u6620\u5c04\uff1aIf(test, body, orelse=[If(_is_nested_if), Continue])
        #   \u21d2 `if test: ... / else: if ...: ... / else: ... / continue`\u3002
        _r2143_hit = None
        if isinstance(_ft3_orelse, list) and len(_ft3_orelse) == 1:
            _r2143_root = _ft3_orelse[0]
            if (isinstance(_r2143_root, dict) and _r2143_root.get('type') == 'If'
                    and _r2143_root.get('_is_elif')
                    and (_r2143_root.get('orelse') or [])):
                _r2143_hit = self._r2143_last_arms_converge_on_continue(region)
        if _r2143_hit is not None:
            _r2143_new_root = dict(_r2143_root)
            _r2143_new_root.pop('_is_elif', None)
            _r2143_new_root['_is_nested_if'] = True
            _ft3_orelse = [_r2143_new_root, {'type': 'Continue'}]
            self.generated_blocks.add(_r2143_hit)
            self.generated_offsets.add(_r2143_hit.start_offset)
'''.split("\n")


def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]


def insert(lines, anchor, new_lines, label):
    hits = [n for n in range(len(lines)) if lines[n] == anchor]
    assert len(hits) == 1, '%s: anchor hits=%d (must be exactly 1)' % (label, len(hits))
    n = hits[0]
    return lines[:n] + new_lines + lines[n:]


def main():
    target = sys.argv[1]
    raw = open(target, 'rb').read()
    pre = sha16(raw)
    assert pre == PRE_HASH, 'base generator sha16=%s, expected %s' % (pre, PRE_HASH)
    assert raw.startswith(b'\xef\xbb\xbf'), 'expected UTF-8 BOM'
    assert raw.count(b'\n') == raw.count(b'\r\n'), 'mixed newlines - refuse'
    lines = raw.split(CRLF)
    hb = [x.encode('utf-8') for x in HELPER if True]
    tb = [x.encode('utf-8') for x in TRIGGER]
    lines = insert(lines, ANCHOR_HELPER, hb, 'helper')
    lines = insert(lines, ANCHOR_TRIGGER, tb, 'trigger')
    out = CRLF.join(lines)
    open(target, 'wb').write(out)
    py_compile.compile(target, doraise=True)
    print('inserted %d helper + %d trigger lines ; size=%d sha16=%s (was %s) py_compile=OK'
          % (len(HELPER), len(TRIGGER), len(out), sha16(out), pre))


if __name__ == '__main__':
    main()
