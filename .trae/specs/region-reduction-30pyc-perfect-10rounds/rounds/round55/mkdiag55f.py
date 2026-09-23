# -*- coding: utf-8 -*-
"""Diagnostic spec #7: instrument every bail inside the new stack-assembly helper."""
import io
import json

spec = json.load(io.open(r'D:/Temp/r55diag/spec_r55b.json', encoding='utf-8'))
edits = spec['edits']
helper = edits[2]['repl']

PAIRS = [
    ("                if (_i.arg or 0) != 1:\n"
     "                    return None\n",
     "                if (_i.arg or 0) != 1:\n"
     "                    print('[F1] wrap arity %r' % (_i.arg,))\n"
     "                    return None\n"),
    ("        if not _r55_closed:\n"
     "            return None\n",
     "        if not _r55_closed:\n"
     "            print('[F2] no POP_TOP close; wraps=%d' % _r55_wraps)\n"
     "            return None\n"),
    ("        if len(_r55_prefix0) < _r55_n_callee:\n"
     "            return None\n",
     "        if len(_r55_prefix0) < _r55_n_callee:\n"
     "            print('[F3] prefix0=%d < n_callee=%d' % (len(_r55_prefix0), _r55_n_callee))\n"
     "            return None\n"),
    ("        if len(_r55_operands) != total_args:\n"
     "            return None\n",
     "        if len(_r55_operands) != total_args:\n"
     "            print('[F4] operands=%d total_args=%d kw=%d chain=%d'\n"
     "                  % (len(_r55_operands), total_args, kwarg_count, len(ternary_chain)))\n"
     "            return None\n"),
    ("        return _r55_expr\n",
     "        print('[F5] built call total_args=%d kw=%d wraps=%d'\n"
     "              % (total_args, kwarg_count, _r55_wraps))\n"
     "        return _r55_expr\n"),
]
for a, r in PAIRS:
    assert helper.count(a) == 1, a[:44]
    helper = helper.replace(a, r, 1)

new = list(edits)
new[2] = {'anchor': edits[2]['anchor'], 'repl': helper}
json.dump({'file': spec['file'], 'edits': new},
          io.open(r'D:/Temp/r55diag/spec_diag55f.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('spec f ok')
