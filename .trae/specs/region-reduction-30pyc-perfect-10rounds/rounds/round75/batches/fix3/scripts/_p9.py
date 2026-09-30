# -*- coding: utf-8 -*-
import io
p = r'D:\Temp\opencode\r75gate\center\mirr_exp9\core\cfg\region_analyzer.py'
t = io.open(p, encoding='utf-8').read()
old = """                _f_cond_pred = any(
                    p.get_last_instruction() is not None
                    and ('IF_' in p.get_last_instruction().opname)
                    for p in (block.predecessors or []))
                if not (_f_else_is_sink and _f_then_terminal and _f_cond_pred
                        and ((_main_inline_boolop_chain or {}).get('op') == 'or')):"""
assert t.count(old) == 1, t.count(old)
new = """                _f_cond_pred = any(
                    p.get_last_instruction() is not None
                    and ('IF_' in p.get_last_instruction().opname)
                    for p in (block.predecessors or []))
                _f_outer_chain = False
                if _f_cond_pred:
                    for _fp in (block.predecessors or []):
                        _fl = _fp.get_last_instruction()
                        if _fl is None or 'IF_' not in _fl.opname:
                            continue
                        for _fs in (_fp.successors or []):
                            if _fs is block:
                                continue
                            _fsl = _fs.get_last_instruction()
                            if _fsl is not None and 'IF_' in _fsl.opname:
                                _f_outer_chain = True
                                break
                        if _f_outer_chain:
                            break
                if not (_f_else_is_sink and _f_then_terminal and _f_cond_pred
                        and _f_outer_chain
                        and ((_main_inline_boolop_chain or {}).get('op') == 'or')):"""
t = t.replace(old, new)
io.open(p, 'w', encoding='utf-8', newline='\n').write(t)
print('exp9 patched')
