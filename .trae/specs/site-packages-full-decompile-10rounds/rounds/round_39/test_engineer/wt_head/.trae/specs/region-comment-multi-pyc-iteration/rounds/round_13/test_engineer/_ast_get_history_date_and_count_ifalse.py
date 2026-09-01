# AST dump for get_history_date_and_count_ifalse
def get_history_date_and_count_ifalse(query_date, count, frequency):
    if frequency == '1w':
        a = query_date.isocalendar()
        start_date = datetime.datetime.strftime(query_date - datetime.timedelta(7 * count + a[2] - 1), '%Y%m%d')
        end_date = datetime.datetime.strftime(query_date - datetime.timedelta(7 + a[2] - 5), '%Y%m%d')
        query_date = query_date - datetime.timedelta(a[2] - 1)
        count_daily = (1 + count) * 5
    elif frequency == 'mo':
        year = query_date.year
        month = query_date.month
        query_date = datetime.datetime.strftime(query_date, '%Y%m%d')
        query_date = query_date[:6] + '01'
        end_date = query_date - datetime.timedelta(1)
        end_date = datetime.datetime.strftime(end_date, '%Y%m%d')
        while count > 0:
            if month - count <= 0:
                year -= 1
                count -= month
                month = 12
            else:
                month = month - count
                count = 0
        if month in (10, 11, 12):
            start_date = str(year) + str(month) + '01'
        else:
            start_date = str(year) + '0' + str(month) + '01'
        count_daily = len(trading_dates.get_trading_calendar(start_date, end_date))
    elif frequency == '1y':
        query_date = datetime.datetime.strftime(query_date, '%Y%m%d')
        start_date = str(int(query_date[0:4]) - count) + '0101'
        end_date = str(int(query_date[0:4]) - 1) + '1231'
        query_date = str(int(query_date[0:4])) + '0101'
        query_date = datetime.datetime.strptime(query_date, '%Y%m%d')
        count_daily = len(trading_dates.get_trading_calendar(start_date, end_date))
    elif frequency == '1q':
        year = query_date.year
        month = query_date.month
        end_quater = (month - 1) // 3
        if end_quater == 0:
            end_date = str(year - 1) + '1231'
            query_date = str(year) + '0101'
        elif end_quater == 1:
            end_date = str(year) + '0331'
            query_date = str(year) + '0401'
        elif end_quater == 2:
            end_date = str(year) + '0630'
            query_date = str(year) + '0701'
        elif end_quater == 3:
            end_date = str(year) + '0930'
            query_date = str(year) + '1001'
        month = int(query_date[4:6])
        while count > 0:
            if month // 3 - count < 0:
                year -= 1
                count -= month // 3
                month = 13
            else:
                month = month - count * 3
                count = 0
        if month in (10, 11, 12):
            start_date = str(year) + str(month) + '01'
        else:
            start_date = str(year) + '0' + str(month) + '01'
        query_date = datetime.datetime.strptime(query_date, '%Y%m%d')
        count_daily = len(trading_dates.get_trading_calendar(start_date, end_date))
    return (query_date, count_daily)
