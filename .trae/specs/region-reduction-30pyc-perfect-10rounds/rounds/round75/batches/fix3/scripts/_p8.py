# -*- coding: utf-8 -*-
import io
p = r'D:\Temp\opencode\r75gate\center\mirr_exp8\core\cfg\region_analyzer.py'
t = io.open(p, encoding='utf-8').read()
old = ("                if not (_f_else_is_sink and _f_then_terminal\n"
       "                        and ((_main_inline_boolop_chain or {}).get('op') == 'or')):")
assert t.count(old) == 1, t.count(old)
new = ("                _f_cond_pred = any(\n"
       "                    p.get_last_instruction() is not None\n"
       "                    and ('IF_' in p.get_last_instruction().opname)\n"
       "                    for p in (block.predecessors or []))\n"
       "                if not (_f_else_is_sink and _f_then_terminal and _f_cond_pred\n"
       "                        and ((_main_inline_boolop_chain or {}).get('op') == 'or')):")
t = t.replace(old, new)
io.open(p, 'w', encoding='utf-8', newline='\n').write(t)
print('exp8 patched')
