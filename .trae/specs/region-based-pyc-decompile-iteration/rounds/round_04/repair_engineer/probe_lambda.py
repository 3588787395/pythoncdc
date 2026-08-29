import dis, marshal, types

# 1) What does CPython 3.11 ACTUALLY compile for `B if C else A`?
src = "lambda x: str(int(x['company_type'])) if filter_nan_and_none(x['company_type']) else x['company_type']"
code = compile(src, "<test>", "eval")
print("=== CPython 3.11 canonical IfExp (`B if C else A`) ===")
for c in code.co_consts:
    if hasattr(c, 'co_code'):
        print("lambda code:")
        dis.dis(c)
PY
