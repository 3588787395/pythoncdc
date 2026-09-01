"""R23-N6: 测试 if/else 嵌套 if/else 结构"""
import dis

# 用 else: if 代替 elif
def f4(date, report_types):
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
    else:
        if month_temp <= report_types:
            month_temp = report_types
            year_temp -= 1
        else:
            month_temp = report_types
        data_return = str(year_temp) + '-' + dict_temp[month_temp]
    return data_return

print("=== f4 (if/else 嵌套 if/else) ===")
dis.dis(f4)
