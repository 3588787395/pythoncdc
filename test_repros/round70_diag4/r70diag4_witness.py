# -*- coding: utf-8 -*-
"""R70 diag4 witness: `return` as the last statement of a `with` body, preceded by a
returning `if` arm and body-level statements. CPython 3.11 splits the with body's
exception-table range into depth-1 segments separated by depth-0 inline
`__exit__(None,None,None)` + `RETURN` groups; a decompiler that stops the body range
at the first inline-`__exit__` block lifts the trailing `return False` out of the with
(its recompile then emits `JUMP_FORWARD` over the with handler instead of
`LOAD_CONST False; RETURN_VALUE` right before it).
"""
def wret(path, kind):
    try:
        with open(path, 'w', encoding='utf-8') as fw:
            if kind == 'a':
                fw.write('a')
                return True
            fw.write('tail')
            return False
    except BaseException:
        return False
