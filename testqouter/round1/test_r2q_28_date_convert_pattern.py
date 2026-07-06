def test(date, report_types):
    dict_temp = {1: '03-31', 2: '06-30', 3: '09-30', 4: '12-31'}
    date_temp = date.replace(month=dict_temp[1][:2], day=dict_temp[1][3:])
    year_temp = int(str(date_temp)[:4])
    month_temp = 1
    if report_types <= 2:
        month_temp = report_types
    if report_types > 2:
        year_temp = year_temp + 1
    return year_temp, month_temp
