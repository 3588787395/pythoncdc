"""R23-N6: 测试 Python 编译器对 return 在 if-then 中的处理"""
import dis

# 测试1: 末尾 return，if-then 内 return
def f1(date, report_types):
    dict_temp = {1: '03-31', 2: '06-30', 3: '09-30', 4: '12-31'}
    date_temp = date.replace('-', '')
    year_temp = int(date_temp[0:4])
    month_temp = 1
    if report_types is None:
        if month_temp == 1:
            month_temp = 4
            year_temp -= 1
        else:
            month_temp -= 1
        data_return = str(year_temp) + '-' + dict_temp[month_temp]
        return data_return  # explicit return inside if-then
    elif month_temp <= report_types:
        month_temp = report_types
        year_temp -= 1
    else:
        month_temp = report_types
    data_return = str(year_temp) + '-' + dict_temp[month_temp]
    return data_return

# 测试2: 无 return 在 if-then 内
def f2(date, report_types):
    dict_temp = {1: '03-31', 2: '06-30', 3: '09-30', 4: '12-31'}
    date_temp = date.replace('-', '')
    year_temp = int(date_temp[0:4])
    month_temp = 1
    if report_types is None:
        if month_temp == 1:
            month_temp = 4
            year_temp -= 1
        else:
            month_temp -= 1
        data_return = str(year_temp) + '-' + dict_temp[month_temp]
    elif month_temp <= report_types:
        month_temp = report_types
        year_temp -= 1
    else:
        month_temp = report_types
    data_return = str(year_temp) + '-' + dict_temp[month_temp]
    return data_return

print("=== f1 (return in if-then) ===")
dis.dis(f1)
print("\n=== f2 (no return in if-then) ===")
dis.dis(f2)
