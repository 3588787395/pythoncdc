# Round13 probe 4: escape-free construction via chr() to avoid quoting confusion.
BS = chr(92)  # backslash
NL = chr(10)
TQ = chr(34)  # double quote
SQ = chr(39)  # single quote

def probe(tag, code, ns=None):
    try:
        compile(code, '<t>', 'eval')
        v = eval(code, ns) if ns is not None else None
        print(f'{tag}: OK eval={v!r}')
    except SyntaxError as e:
        print(f'{tag}: SYNTAX {e.msg} | src={code!r}')
    except Exception as e:
        print(f'{tag}: OKRUNTIME {type(e).__name__}: {e} | src={code!r}')

# P9b: real backslash inside a string literal within EXPR region, single-quote delim
#      target source: f'{x + '\n'}'
probe('P9b backslash-in-expr-string single-delim',
      'f' + SQ + '{x + ' + SQ + BS + 'n' + SQ + '}' + SQ, {'x': 'a'})
# P9c: backslash inside string literal within EXPR region, triple-double delim
#      target source: f"""{x + '\n'}"""
probe('P9c backslash-in-expr-string triple-double-delim',
      'f' + TQ*3 + '{x + ' + SQ + BS + 'n' + SQ + '}' + TQ*3, {'x': 'a'})

# P15b: triple-double delim, expr contains triple-single string
probe('P15b triple-double delim, expr=+triple-single-string',
      'f' + TQ*3 + '{+' + SQ*3 + 'a' + SQ*3 + '}' + TQ*3, {})
# P15c: triple-double delim, expr contains a normal string then triple-single
probe('P15c triple-double delim, expr=triple-single-string in call',
      'f' + TQ*3 + '{' + SQ*3 + 'a' + SQ*3 + '.join(' + TQ*3 + 'z' + TQ*3 + ')}' + TQ*3, {})

# P16: triple-single delim, expr contains triple-double with newline (REAL46-004 shape)
#      confirm exact shape compiles and evaluates correctly
src16 = ('f' + SQ*3 + '{name!r} member mismatch:' + BS + 'n      {'
         + TQ*3 + NL + '      ' + TQ*3 + '.join(failed_member)!s}' + SQ*3)
probe('P16 REAL46-004 exact shape (escaped newline literal part)',
      src16, {'name': 'SPAM', 'failed_member': ['m1', 'm2']})

# P17: REAL46-004 with REAL newline in expr + triple-single delim
src17 = ('f' + SQ*3 + '{name!r} member mismatch: {'
         + TQ*3 + NL + '      ' + TQ*3 + '.join(failed_member)!s}' + SQ*3)
probe('P17 REAL46-004 exact shape (real newline in expr)',
      src17, {'name': 'SPAM', 'failed_member': ['m1', 'm2']})

# P18: literal ending with quote before closing triple-single delim -> must escape
probe('P18 literal trailing quote triple-delim',
      'f' + SQ*3 + 'abc' + BS + SQ + SQ*3, {})
probe('P18b literal trailing quote triple-delim UNESCAPED (expect fail)',
      'f' + SQ*3 + 'abc' + SQ + SQ*3, {})
