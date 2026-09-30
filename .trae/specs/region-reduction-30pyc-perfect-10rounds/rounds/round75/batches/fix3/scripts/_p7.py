# -*- coding: utf-8 -*-
import io, sys
sys.stdout.reconfigure(encoding='utf-8')
p = r'D:\Temp\opencode\r75gate\center\mirr_exp7\core\cfg\region_analyzer.py'
t = io.open(p, encoding='utf-8').read()
old = "                if not (_f_else_is_sink and ((_main_inline_boolop_chain or {}).get('op') == 'or')):"
assert t.count(old) == 1, t.count(old)
new = ("                _f_then_last = then_succ.get_last_instruction() if then_succ else None\n"
       "                _f_then_exc = getattr(then_succ, 'exception_successors', None) or set()\n"
       "                _f_then_terminal = (\n"
       "                    then_succ is not None\n"
       "                    and not [s for s in then_succ.successors if s not in _f_then_exc])\n"
       "                if not (_f_else_is_sink and _f_then_terminal\n"
       "                        and ((_main_inline_boolop_chain or {}).get('op') == 'or')):")
t = t.replace(old, new)
io.open(p, 'w', encoding='utf-8', newline='\n').write(t)
print('exp7 patched')
