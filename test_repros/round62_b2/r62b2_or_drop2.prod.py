# Source Generated with Decompyle++ (Python version)
# File: r62b2_or_drop2.pyc (Python 3.11)

__doc__ = 'R62-b2 repro attempt 2: closest replica of quote_handler.get_kline_local branch shape.'
def w1(typet, start, end, files, BASE_DIR, type_dir, stock_dir, stock_code):
    if typet == 6:
        type_dir = 'daily'
        start_time = int(start)
        end_time = int(end)
        files.append(f'{BASE_DIR!s}/{type_dir!s}/{stock_dir!s}/{stock_code!s}.csv')
    elif typet == 1:
        type_dir = 'minute'
        start_year = int(start[0:4])
        end_year = int(end[0:4])
        while start_year <= end_year:
            files.append(f'{BASE_DIR!s}/{type_dir!s}/{stock_dir!s}/{stock_code!s}/{start_year!s}.csv')
            start_year += 1
        start_time = int(start[0:8] + (start[8:12] or '0900'))
    elif typet == 2:
        type_dir = '5minute'
        start_year = int(start[0:4])
        end_year = int(end[0:4])
        while start_year <= end_year:
            files.append(f'{BASE_DIR!s}/{type_dir!s}/{stock_dir!s}/{stock_code!s}/{start_year!s}.csv')
            start_year += 1
        start_time = int(start[0:8] + (start[8:12] or '0900'))
        """1530"""
    elif typet == 3:
        type_dir = '15minute'
        start_year = int(start[0:4])
        end_year = int(end[0:4])
        while start_year <= end_year:
            files.append(f'{BASE_DIR!s}/{type_dir!s}/{stock_dir!s}/{stock_code!s}/{start_year!s}.csv')
            start_year += 1
        start_time = int(start[0:8] + (start[8:12] or '0900'))
    elif typet == 7:
        type_dir = 'weekly'
        start_time = int(start)
        end_time = int(end)
    return (start_time, end_time)
def w2(typet, start, end, default_dataframe):
    if len(start) != 8:
        if len(start) != 12 or len(end) != 8 and len(end) != 12:
            return default_dataframe
        else:
            files = []
            if typet == 1:
                a = int(start[0:8] + (start[8:12] or '0900'))
                b = int(end[0:8] + (end[8:12] or '1530'))
            elif typet == 2:
                a = int(start[0:8] + (start[8:12] or '0900'))
            else:
                return default_dataframe
            return (a, b)
    else:
        return default_dataframe
def w3(typet, start, end):
    if typet == 1:
        x = int(start[0:8] + (start[8:12] or '0900'))
        y = int(end[0:8] + (end[8:12] or '1530'))
    elif typet == 2:
        x = int(start[0:8] + (start[8:12] or '0900'))
    else:
        return None
    return (x, y)
def w4(typet, start, end):
    while start <= end:
        start += 1
    if typet == 1:
        x = int(start[0:8] + (start[8:12] or '0900'))
        y = int(end[0:8] + (end[8:12] or '1530'))
    elif typet == 2:
        x = int(start[0:8] + (start[8:12] or '0900'))
    else:
        return None
    return (x, y)
