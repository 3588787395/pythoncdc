# -*- coding: utf-8 -*-
import io
p = r'D:\Temp\opencode\r75gate\fix3\scripts\mkspecs.py'
t = io.open(p, encoding='utf-8').read()
# 1) fix the typo note (块° -> 块 0)
old_note = '\u9876\u5c42 if\uff08\u5757\u00b0 \u51fd\u6570\u5165\u53e3\u3001\u65e0\u524d\u9a71\u6216\u4ec5\u8bed\u53e5\u524d\u9a71\uff09'
assert old_note in t, 'typo note not found'
t = t.replace(old_note, '\u9876\u5c42 if\uff08\u5757 0 = \u51fd\u6570\u5165\u53e3\u3001\u65e0\u524d\u9a71\u6216\u4ec5\u8bed\u53e5\u524d\u9a71\uff09')
# 2) replace cond_pred-only gate with cond_pred + outer-chain BFS gate
old = """                _f_cond_pred = any(
                    p.get_last_instruction() is not None
                    and ('IF_' in p.get_last_instruction().opname)
                    for p in (block.predecessors or []))
                if not (_f_else_is_sink and _f_then_terminal and _f_cond_pred
                        and ((_main_inline_boolop_chain or {}).get('op') == 'or')):"""
assert t.count(old) == 1, t.count(old)
new = """                #   [\u6536\u7a84-4] \u518d\u52a0\u201c\u7956\u5148\u94fe\u4e0a\u6eaf\u5b58\u5728\u94fe\u8bc1\u636e\u201d\uff1a\u6cbf\u524d\u9a71\u56de\u6eaf\u627e\u5230\u67d0\u4e2a\u6761\u4ef6\u5757
                #   \u7684\u5176\u4ed6\u540e\u7ee7\u4e5f\u662f\u6761\u4ef6\u5757\uff08elif \u94fe\u7eed\u63a5\uff09\u624d\u8ba4\u5b9a\u672c if \u5d4c\u5728\u591a\u81c2\u94fe\u5185\u3002
                #   \u5355\u5c40\u5916\u5c42 if/else\uff08\u5176\u4ed6\u540e\u7ee7\u662f RETURN\uff0c\u65e0\u94fe\u7eed\u63a5\u4e5f\u65e0\u7956\u5148\u94fe\u8bc1\u636e\uff0c\u5982
                #   \u540c\u5c42 `if not A or B: return 1 else: return 2` \u72ec\u7acb\u5f62\u6001\uff09\u4e2d
                #   merge=else_succ \u672c\u5c31\u6b63\u786e\uff1b\u53ea\u6709\u94fe\u6210\u5458\u7684 else \u81c2\u624d\u4f1a\u88ab\u94fe\u533a\u6392\u9664\u3002
                _f_cond_pred = any(
                    p.get_last_instruction() is not None
                    and ('IF_' in p.get_last_instruction().opname)
                    for p in (block.predecessors or []))
                _f_outer_chain = False
                _f_seen = set()
                _f_stack = list(block.predecessors or [])
                while _f_stack and not _f_outer_chain:
                    _fp = _f_stack.pop()
                    if id(_fp) in _f_seen:
                        continue
                    _f_seen.add(id(_fp))
                    _fl = _fp.get_last_instruction()
                    if _fl is not None and 'IF_' in _fl.opname:
                        for _fs in (_fp.successors or []):
                            if _fs is block:
                                continue
                            _fsl = _fs.get_last_instruction()
                            if _fsl is not None and 'IF_' in _fsl.opname:
                                _f_outer_chain = True
                                break
                    if not _f_outer_chain:
                        _f_stack.extend(_fp.predecessors or [])
                if not (_f_else_is_sink and _f_then_terminal and _f_cond_pred
                        and _f_outer_chain
                        and ((_main_inline_boolop_chain or {}).get('op') == 'or')):"""
t = t.replace(old, new)
io.open(p, 'w', encoding='utf-8', newline='\n').write(t)
print('mkspecs updated (收窄-4 + typo fix)')
