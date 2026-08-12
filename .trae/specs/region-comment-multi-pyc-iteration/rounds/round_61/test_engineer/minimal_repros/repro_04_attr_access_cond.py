# 属性访问 + 条件
# Minimal reproduction for Round 61 - Pattern Analysis
#
# Target Pattern: 属性访问 + 条件
#
def attr_access_with_cond(obj):
    fields = obj.fields if hasattr(obj, 'fields') else []
    for f in fields:
        try:
            val = getattr(obj, f)
            if val:
                print(val)
        except:
            pass

