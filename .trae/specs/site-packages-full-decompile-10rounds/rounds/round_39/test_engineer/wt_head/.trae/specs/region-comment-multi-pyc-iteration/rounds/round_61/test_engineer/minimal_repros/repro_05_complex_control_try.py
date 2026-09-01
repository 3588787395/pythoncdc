# 复杂控制流 + try
# Minimal reproduction for Round 61 - Pattern Analysis
#
# Target Pattern: 复杂控制流 + try
#
def complex_control_flow_with_try(query_date, fields):
    result = []
    try:
        if query_date:
            for f in fields:
                data = fetch(f, query_date)
                result.append(data)
        else:
            result = get_default(fields)
        return result
    except Exception as e:
        log(e)
        return []

