# -*- coding: utf-8 -*-
"""Write specs/cand_r67_b1.json (B1: diamond-join merge_block recovery in
_detect_ternary_pattern) and verify anchor count on the landed bytes."""
import io
import json

TARGET = r'F:/Downloads/pythoncdc-main/core/cfg/region_analyzer.py'

ANCHOR = (
"                            merge_block = _t_ft\n"
"\n"
"            value_target = None\n"
"            merge_context = None  # \u65b0\u589e: \u8bb0\u5f55merge\u5757\u7684\u4e0a\u4e0b\u6587\u7c7b\u578b\n"
)

NEW = (
"            # [R67-diag1 B1 \u5f02\u5e38\u8fb9\u7a00\u91ca\u7684\u83f1\u5f62\u6c47\u5408\u70b9\u56de\u6536]\n"
"            # \u8bc6\u522b\u6761\u4ef6\uff1a\u56db\u6761\u5168\u90e8\u53ea\u8bfb**\u672c\u5019\u9009\u4e09\u5143\u81ea\u8eab**\u7684\u4e09\u4e2a\u5757\uff08\u6761\u4ef6\u5757 block \u4e0e\u5176\n"
"            #   true/false \u503c\u5757\uff09\uff0c\u4e0d\u8bfb\u4efb\u4f55\u5176\u5b83\u533a\u57df\u7684 blocks\uff0c\u65e0\u540d\u5b57/\u6587\u4ef6/\u504f\u79fb\u5b57\u9762\u91cf/\u9608\u503c\uff1a\n"
"            #   (1) \u80fd\u8d70\u5230\u6b64\u5904 \u21d2 merge_block \u5df2\u88ab find_nearest_common_post_dominator\n"
"            #       (L21581) \u4e0e\u56db\u6761\u65e2\u6709 fallback\uff08L21588 / L21609 / L21671 / L21713\uff09\u5224\u4e3a None\uff1b\n"
"            #   (2) \u6bcf\u4e2a\u503c\u5757\u7684\u300c\u6b63\u5e38\u540e\u7ee7\u300d= successors - \u8be5\u5757\u81ea\u8eab\u7684 exception_successors\n"
"            #       \u2014\u2014 \u4e0e dominator_analyzer._compute_post_dominators Option C\uff08L157-167\uff09\n"
"            #       \u540c\u4e00\u6761\u8fc7\u6ee4\u5668\uff0c\u4e0d\u65b0\u5efa\u8bed\u4e49\uff1b\n"
"            #   (3) \u4e24\u4e2a\u503c\u5757\u5404\u6070\u6709\u4e00\u6761\u6b63\u5e38\u540e\u7ee7\u4e14\u6307\u5411\u540c\u4e00\u4e2a\u5757 J\uff08\u83f1\u5f62\u6c47\u5408\uff09\uff1b\n"
"            #   (4) J \u4e0d\u662f\u6761\u4ef6\u5757\u672c\u8eab\u3001\u4e5f\u4e0d\u662f\u4efb\u4e00\u503c\u5757\uff08\u6392\u9664\u81ea\u73af\u4e0e\u76f8\u90bb\u56de\u8fb9\uff09\u3002\n"
"            #   \u5b9e\u6d4b\uff1asynth/r67_r47_exitless.py \u7684 u1-u4 \u4e0e _process_order \u7684 6 \u4e2a\u503c\u4e0a\u4e0b\u6587\n"
"            #   \u4e09\u5143\u5747\u6ee1\u8db3 (2)(3)(4)\uff0c(1) \u6210\u7acb\u7684\u6839\u56e0\u662f `while True:` \u65e0\u6b63\u5e38\u53ef\u8fbe\u51fa\u53e3 \u21d2\n"
"            #   63 \u4e2a\u5757\u91cc 61 \u4e2a post_dominators \u9000\u5316\u4e3a\u5168\u96c6\uff0c\u4efb\u610f\u5757\u5bf9\u7684\u6700\u8fd1\u516c\u5171\u540e\u652f\u914d\u8005\n"
"            #   \u4e0d\u5b58\u5728\uff1bJ \u5373 try/except \u4e4b\u540e\u7684\u5faa\u73af\u5e95\u5757\u3002\n"
"            #   \u53cd\u4f8b\uff08(3) \u4e0d\u6210\u7acb \u21d2 \u4e0d\u56de\u6536\uff09\uff1a\u4efb\u4e00\u503c\u5757\u4ee5 RETURN_VALUE/RAISE_VARARGS \u7ed3\u5c3e\u7684\n"
"            #   \u8bed\u53e5\u7ea7 if/else\uff0c\u5176\u6b63\u5e38\u540e\u7ee7\u96c6\u4e3a\u7a7a\uff1b\u53cc\u503c\u5757\u5404\u81ea\u6c47\u5165\u4e0d\u540c\u5757\u7684\u5d4c\u5957\u5f62\u72b6\u4ea6\u62d2\u3002\n"
"            # \u5f52\u7ea6\u65b9\u5f0f\uff1a\u53ea\u8865\u4e00\u6761\u65e2\u6709 merge_block fallback\uff08\u4e0e\u4e0a\u9762\u56db\u6761\u540c\u65cf\u3001\u540c\u4f4d\u7f6e\u3001\u540c\n"
"            #   \u8d4b\u503c\u76ee\u6807\uff09\uff0c\u8d4b\u503c\u540e\u539f\u6837\u4ea4\u7ed9\u65e2\u6709 `if merge_block:` \u5206\u7c7b\u5faa\u73af\uff08L21769+\uff09\u51b3\u5b9a\n"
"            #   merge_context/value_target\uff0c\u5176\u540e [R39]/[R39b] \u503c\u5757\u7eaf\u5ea6\u5b88\u536b\u4e0e all_blocks \u8ba4\u9886\n"
"            #   \u4e00\u5f8b\u4e0d\u53d8\u3002\u4e0d\u5220\u9664\u3001\u4e0d\u6291\u5236\u4efb\u4f55\u53d1\u5c04\uff0c\u4e0d\u65b0\u589e\u5b9e\u4f8b\u72b6\u6001\uff0c\u4e0d\u6539\u53d1\u5c04\u6b21\u5e8f\u3002\n"
"            # AST \u6620\u5c04\uff1a\u4e24\u6761\u7eaf\u503c\u81c2\u5728\u5b57\u8282\u7801\u4e0a\u8df3\u5f80\u540c\u4e00\u6d88\u8d39\u5757 J \u7684 IfRegion\uff0c\u5176\u6e90\u7801\u5f62\u6001\u672c\u5c31\n"
"            #   \u662f ast.Expr/ast.Assign(value=ast.IfExp(test, body=\u503c1, orelse=\u503c2))\uff1bJ \u7684\u8bed\u53e5\n"
"            #   \u8282\u70b9\u662f\u8be5 ast.IfExp \u6240\u5728**\u8bed\u53e5**\u4e4b\u540e\u7684\u5144\u5f1f\u8282\u70b9\uff0c\u800c\u975e\u533a\u57df body \u7684\u5b50\u8282\u70b9\u3002\n"
"            #   \u73b0\u72b6\u56e0 J \u7f3a\u5931\u88ab [R47] \u6d88\u8d39\u70b9\u5b88\u536b\u9000\u56de IfRegion\uff0c\u628a\u4e24\u6761\u503c\u81c2\u53d1\u5c04\u6210\n"
"            #   `if c: \"\"\"X\"\"\" else: \"\"\"Y\"\"\"` \u8bed\u53e5\u9aa8\u67b6\uff0c\u5916\u5c42\u8c03\u7528\u8bed\u53e5\u968f\u4e4b\u4e22\u5931\u3002\n"
"            if merge_block is None:\n"
"                _b1_exc_t = getattr(true_block, 'exception_successors', None) or set()\n"
"                _b1_exc_f = getattr(false_block, 'exception_successors', None) or set()\n"
"                _b1_norm_t = [s for s in true_block.successors if s not in _b1_exc_t]\n"
"                _b1_norm_f = [s for s in false_block.successors if s not in _b1_exc_f]\n"
"                if (len(_b1_norm_t) == 1 and len(_b1_norm_f) == 1\n"
"                        and _b1_norm_t[0] is _b1_norm_f[0]\n"
"                        and _b1_norm_t[0] is not block\n"
"                        and _b1_norm_t[0] is not true_block\n"
"                        and _b1_norm_t[0] is not false_block):\n"
"                    merge_block = _b1_norm_t[0]\n"
"\n"
)

spec = {
    "name": "cand_r67_b1_diamond_join_merge_block",
    "file": "core/cfg/region_analyzer.py",
    "anchor": ANCHOR,
    "repl": ANCHOR + NEW,
    "note": ("R67-diag1 B1: recover the diamond join as merge_block when "
             "exception edges make post-dominators degenerate"),
}

u = io.open(TARGET, encoding='utf-8-sig', newline='').read().replace('\r\n', '\n')
print('anchor count =', u.count(ANCHOR))
print('repl adds lines =', spec['repl'].count('\n') - ANCHOR.count('\n'))
assert u.count(ANCHOR) == 1
io.open('specs/cand_r67_b1.json', 'w', encoding='utf-8').write(
    json.dumps(spec, ensure_ascii=False, indent=1))
print('wrote specs/cand_r67_b1.json')
