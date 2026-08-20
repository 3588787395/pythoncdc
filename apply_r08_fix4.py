"""Apply R8 fix 4: Filter RERAISE and COPY in handler body statements."""
filepath = 'core/cfg/region_ast_generator.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = """        handler_instrs = [i for i in block.instructions
                          if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL',
                                               'PUSH_EXC_INFO', 'POP_EXCEPT', 'POP_TOP',
                                               'CHECK_EXC_MATCH', 'CHECK_EG_MATCH',
                                               'WITH_EXCEPT_START', 'EXTENDED_ARG')
                          and i.opname not in _EXC_STAR_FRAMEWORK_OPS]"""

new = """        handler_instrs = [i for i in block.instructions
                          if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL',
                                               'PUSH_EXC_INFO', 'POP_EXCEPT', 'POP_TOP',
                                               'CHECK_EXC_MATCH', 'CHECK_EG_MATCH',
                                               'WITH_EXCEPT_START', 'EXTENDED_ARG',
                                               'RERAISE', 'COPY')
                          and i.opname not in _EXC_STAR_FRAMEWORK_OPS]"""

if old not in content:
    print("ERROR: old code not found")
else:
    content = content.replace(old, new, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fix applied successfully!")
