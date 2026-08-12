# 字段赋值 + try-except
# Minimal reproduction for Round 61 - Pattern Analysis
#
# Target Pattern: 字段赋值 + try-except
#
def fields_assignment_with_try(data):
    fields = ['a', 'b', 'c']
    try:
        result = process_fields(fields, data)
        return result
    except:
        return None

