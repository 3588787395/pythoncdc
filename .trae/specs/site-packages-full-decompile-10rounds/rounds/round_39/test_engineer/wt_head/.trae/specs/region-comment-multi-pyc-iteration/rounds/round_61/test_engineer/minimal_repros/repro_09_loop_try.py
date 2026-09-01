# 循环 + try-except
# Minimal reproduction for Round 61 - Pattern Analysis
#
# Target Pattern: 循环 + try-except
#
def loop_try_except(items, fields):
    results = []
    for item in items:
        try:
            for f in fields:
                val = item.get(f)
                results.append(val)
        except:
            continue
    return results

