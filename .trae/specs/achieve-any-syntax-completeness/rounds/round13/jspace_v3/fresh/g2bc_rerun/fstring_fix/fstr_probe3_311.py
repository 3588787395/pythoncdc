# Round13 probe 3: precise 3.11 f-string boundary behavior for fix design.
def probe(tag, code, ns=None):
    try:
        compile(code, '<t>', 'eval')
        v = eval(code, ns) if ns is not None else None
        print(f'{tag}: OK eval={v!r}')
    except SyntaxError as e:
        print(f'{tag}: SYNTAX {e.msg}')
    except Exception as e:
        print(f'{tag}: OKRUNTIME {type(e).__name__}: {e}')

probe('P1 expr={""} delim=triple-single', "f'''{''}'''", {})
probe('P2 expr={\'\' + x} delim=triple-single', "f'''{'' + 'a'}'''", {})
probe('P3 content starts with quote', "f''''abc'''")
probe('P4 content ends with quote (raw)', "f'''abc''''")
probe('P5 content ends with escaped quote', "f'''abc\\''''")
probe('P6 delim=triple-double expr={""}', 'f"""{""}"""', {})
probe('P7 expr triple-single string with newline', "f'''{'''a\nb'''.join(['x'])}'''", {})
probe('P8 backslash in SPEC region', "f'{x:.\\x32f}'", {'x': 1.2345})
probe('P9 backslash in EXPR region', "f'{x + chr(92)}'", {'x': 1})
probe('P11 literal with single quote + delim triple-single', "f'''abc' {x}'''", {'x': 1})
probe('P12 literal quote run interior', "f'''a''b'''")
probe('P13 expr contains triple-double + newline, delim triple-single',
      'f\'\'\'{"""a\nb""".join([\'x\'])}\'\'\'', {})
probe('P14 expr contains triple-single with delim triple-single (boundary G)',
      "f'''{'''a''' + 'b'}'''", {})
probe('P15 expr contains triple-single, delim triple-double',
      'f"""{\'+\'\'\'a\'\'\'}"""', {})
