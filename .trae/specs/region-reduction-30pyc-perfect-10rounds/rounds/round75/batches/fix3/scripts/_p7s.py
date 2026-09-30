# -*- coding: utf-8 -*-
import io
p = r'D:\Temp\opencode\r75gate\fix3\scripts\mkspecs.py'
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
# update G0 guard note
old_note = "                #   \u6536\u7a84] \u4ec5 op=='or'"
i = t.find("                #   [\u6536\u7a84]")
assert i > 0, 'note anchor'
j = t.find("                _f_then_last", i)
assert j > i
add = ("                #   [\u6536\u7a84-2] \u518d\u52a0 then \u81c2\u65e0\u6b63\u5e38\u540e\u7ee7\uff08\u7ec8\u70b9\u81c2\uff09\uff1a\u82e5 then \u53ef\u8fbe\u5230\u5171\u4eab\u7eed\u884c\u70b9\n"
       "                #   \uff08Round33 \u539f\u573a\u666f time_validator.can_cancel_order \u7684 then\u2192else \u53ef\u8fbe\uff09\uff0c\n"
       "                #   merge=else_succ \u662f\u6b63\u786e\u6c47\u5408\u70b9\uff0c\u8df3\u8fc7\u4f1a\u6539\u53d8\u533a\u57df\u5f62\u6001\uff08history_data_source.\n"
       "                #   get_price 15/18\u3001custom_tools 5/6 \u5373\u6b64\u7c7b\uff09\uff1b\u4e24\u81c2\u7ec8\u70b9\u65f6\u624d\u662f\u72ec\u7acb\u7ec8\u70b9\u81c2\u3002\n")
t = t[:j] + add + t[j:]
io.open(p, 'w', encoding='utf-8', newline='\n').write(t)
print('mkspecs f_repl updated')
