# -*- coding: utf-8 -*-
"""Build the class-B probe spec (stderr prints) from LIVE repo bytes, read-only."""
import io
import json

P = r'F:/Downloads/pythoncdc-main/core/cfg/region_ast_generator.py'
OUT = r'D:/Temp/opencode/r65gate/diag2/specs/probe_b.json'

u = io.open(P, encoding='utf-8-sig', newline='').read().replace('\r\n', '\n')
L = u.split('\n')


def seg(a, b):
    return '\n'.join(L[a - 1:b])


def chk(s, txt):
    assert seg(*s) == txt, (s, repr(seg(*s)))


# 1) _register_prefix_emitted: print what a consumer claims
chk((48239, 48240), "        _last = max(_offs)\n"
                    "        if _last > self.prefix_emitted_upto.get(block, -1):")
e1r = ("        _last = max(_offs)\n"
       "        import sys as _r65d2s\n"
       "        print('RPE blk=%s last=%s n=%s caller=%s@%s' % (getattr(block, 'start_offset', None),"
       " _last, len(instrs), _r65d2s._getframe(1).f_code.co_name, _r65d2s._getframe(1).f_lineno),"
       " file=_r65d2s.stderr)\n"
       "        if _last > self.prefix_emitted_upto.get(block, -1):")

# 2) _build_prefix_stmt_list: print input + produced
chk((48277, 48278), "        if not pre_instrs:\n"
                    "            return []")
e2r = ("        import sys as _r65d2t\n"
       "        print('BPL blk=%s in=%s' % (getattr(block, 'start_offset', None),"
       " [i.opname for i in pre_instrs]), file=_r65d2t.stderr)\n"
       "        if not pre_instrs:\n"
       "            return []")

# 3) boolop chain-head slice decision
chk((32587, 32587), "                _pemu = self.prefix_emitted_upto.get(first_chain_block, -1)")
e3r = ("                _pemu = self.prefix_emitted_upto.get(first_chain_block, -1)\n"
       "                import sys as _r65d2u\n"
       "                print('BOP blk=%s pemu=%s npre=%s' % ("
       "getattr(first_chain_block, 'start_offset', None), _pemu, len(pre_instrs)),"
       " file=_r65d2u.stderr)")

patched = u.replace(seg(48239, 48240), e1r).replace(seg(48277, 48278), e2r).replace(seg(32587, 32587), e3r)
assert patched.count('RPE blk=') == 1 and patched.count('BPL blk=') == 1 and patched.count('BOP blk=') == 1
compile(patched, P, 'exec')
spec = {'file': 'core/cfg/region_ast_generator.py',
        'edits': [{'anchor': seg(48239, 48240), 'repl': e1r},
                  {'anchor': seg(48277, 48278), 'repl': e2r},
                  {'anchor': seg(32587, 32587), 'repl': e3r}]}
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(spec, ensure_ascii=False))
print('wrote', OUT, 'net inserted lines',
      sum(e['repl'].count('\n') - e['anchor'].count('\n') for e in spec['edits']))
