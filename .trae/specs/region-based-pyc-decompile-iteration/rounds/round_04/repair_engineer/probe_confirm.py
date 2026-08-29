import dis, marshal

# (A) Recompile the EXACT lambda the OK.py emitted for local_finance and check its jump.
# OK.py lambda (per summary):  str(int(x['company_type'])) if filter_nan_and_none(x['company_type']) else x['company_type']
def filter_nan_and_none(v):
    return v
src_ok = "lambda x: str(int(x['company_type'])) if filter_nan_and_none(x['company_type']) else x['company_type']"
c = compile(src_ok, "<ok>", "eval")
print("=== OK.py lambda recompiled (canonical expected) ===")
for cc in c.co_consts:
    if hasattr(cc, 'co_code'):
        dis.dis(cc)

print()
