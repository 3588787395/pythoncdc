# 列表构建 + 异常
# Minimal reproduction for Round 61 - Pattern Analysis
#
# Target Pattern: 列表构建 + 异常
#
def list_build_with_exception(data):
    fields = data.keys() if data else []
    try:
        result = [process(f, data) for f in fields]
        return result
    except:
        return []

