# R5 minimal repro: 复杂 elif 链分支体丢失 -> elif ...: pass
# 关联缺陷：quotation.pyc get_fundamentals line 1123-1128 / valuation_new line 1617-1622 (新发现)
# 触发区域：IF / _identify_conditional_regions + _generate_if (多分支 elif 链中部分分支体退化为 pass)
# 预期：完整 4 分支 elif 链, 每分支有 params 赋值
# R5 实际产物：elif start_year is None: pass / elif start_year is not None: pass  (分支体丢失)


def set_year_params(params, start_year, end_year):
    if start_year is not None and end_year is not None:
        params['start_year'] = start_year
        params['end_year'] = end_year
    elif start_year is None and end_year is not None:
        params['start_year'] = str(int(end_year) - 1)
        params['end_year'] = end_year
    elif start_year is not None and end_year is None:
        params['start_year'] = start_year
        params['end_year'] = str(int(start_year) + 1)
    elif start_year is None and end_year is None:
        params['start_year'] = '2020'
        params['end_year'] = '2024'
    return params
