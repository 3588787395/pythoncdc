import dis

# Candidate source: original lambda is `x['company_type'] if C else str(int(...))`
# (POP_JUMP_IF_TRUE jumps to x['company_type'] = body / true branch)
candidates = [
    "lambda x: x['company_type'] if filter_nan_and_none(x['company_type']) else str(int(x['company_type']))",
    "lambda x: str(int(x['company_type'])) if filter_nan_and_none(x['company_type']) else x['company_type']",
]
for src in candidates:
    code = compile(src, "<test>", "eval")
    print("==== ", src)
    for c in code.co_consts:
        if hasattr(c, 'co_code'):
            dis.dis(c)
    print()
