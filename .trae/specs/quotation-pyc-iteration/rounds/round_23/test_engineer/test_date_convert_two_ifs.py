"""R23-N6: 测试两个独立 if 语句 (非 elif) 的编译结果"""
import dis

# 两个独立 if 语句
def f3(date, report_types):
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
        return data_return
    if month_temp <= report_types:  # 注意：这里是独立的 if，不是 elif
        month_temp = report_types
        year_temp -= 1
    else:
        month_temp = report_types
    data_return = str(year_temp) + '-' + dict_temp[month_temp]
    return data_return

print("=== f3 (两个独立 if) ===")
dis.dis(f3)
