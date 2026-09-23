# -*- coding: utf-8 -*-
"""Diagnostic spec: what does _try_build_ternary_kwarg_call see for the 2-ternary-kwarg shape?"""
import io
import json

REPO = r'F:\Downloads\pythoncdc-main'
P = 'core/cfg/region_ast_generator.py'
src = io.open(REPO + '/' + P, encoding='utf-8', newline='').read().replace(chr(13), '')

EDITS = []

# (1) after the chain walk: chain length, final merge, chosen KW_NAMES/CALL pair
A1 = ("        if kw_names_instr is None or call_instr is None:\n"
      "            return None\n")
R1 = ("        print('[D1] chain=%d final_merge=%s kw@%s call@%s call.arg=%s'\n"
      "              % (len(ternary_chain),\n"
      "                 None if final_merge is None else final_merge.start_offset,\n"
      "                 None if kw_names_instr is None else kw_names_instr.offset,\n"
      "                 None if call_instr is None else call_instr.offset,\n"
      "                 None if call_instr is None else call_instr.arg))\n"
      "        if kw_names_instr is None or call_instr is None:\n"
      "            return None\n")
EDITS.append((A1, R1))

# (2) func_call_info availability at the point the builder needs the callee
A2 = ("        func_call_info = region.func_call_info\n"
      "        if func_call_info:\n"
      "            func_expr = func_call_info.get('func')\n")
R2 = ("        func_call_info = region.func_call_info\n"
      "        print('[D2] fci=%s keys=%s kwarg_count=%d total_args=%d n_tern=%d'\n"
      "              % (bool(func_call_info),\n"
      "                 sorted(func_call_info) if isinstance(func_call_info, dict) else None,\n"
      "                 kwarg_count, total_args, num_ternaries))\n"
      "        if func_call_info:\n"
      "            func_expr = func_call_info.get('func')\n")
EDITS.append((A2, R2))

# (3) caller-side: was the builder even reached, and what did it return?
A3 = ("                            _kwarg_call = self._try_build_ternary_kwarg_call(\n")
R3 = ("                            print('[D3] call-site reached, entry=%s' % (\n"
      "                                None if region is None else getattr(\n"
      "                                    region, 'start_offset', None)))\n"
      "                            _kwarg_call = self._try_build_ternary_kwarg_call(\n")
EDITS.append((A3, R3))

for a, r in EDITS:
    n = src.count(a)
    print('anchor count %d :: %r' % (n, a[:58]))
    assert n == 1, 'anchor not unique'
    src = src.replace(a, r, 1)

json.dump({'file': P, 'edits': [{'anchor': a, 'repl': r} for a, r in EDITS]},
          io.open(r'D:/Temp/r55diag/spec_diag55.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('spec ok')
