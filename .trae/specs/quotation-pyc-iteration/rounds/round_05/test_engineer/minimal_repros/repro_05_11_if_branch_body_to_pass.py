# R5 minimal repro: else 块首条 Call 语句丢失 + 嵌套 if 被提升为 elif (新发现)
# 关联缺陷：quotation.pyc get_stock_exrights line 2302-2310 / get_opt_objects line 2450 (新发现, R4 未覆盖)
# 触发区域：IF / _generate_if + _generate_block_statements (else 块首条 exrights.rename() Call 丢失, 嵌套 if date is None 被提升为 elif)
# 预期：if exrights.empty: return exrights
#       else: exrights.rename(columns={...}, inplace=True);  if date is None: return exrights; ...
# R5 实际产物：
#   if exrights.empty: return exrights
#   elif date is None: return exrights          <- exrights.rename() Call 丢失, 嵌套 if 被提升为 elif
#   else: date = ...; exrights = exrights[...]; return exrights


def get_stock_exrights(stock_code, date=None):
    exrights = load_exrights(stock_code)[stock_code]
    exrights = exrights.copy()
    if exrights.empty:
        return exrights
    else:
        exrights.rename(columns={'a': 'b', 'c': 'd'}, inplace=True)
        if date is None:
            return exrights
        date = date.replace('-', '')[:8]
        exrights = exrights[exrights.index <= date]
        return exrights
