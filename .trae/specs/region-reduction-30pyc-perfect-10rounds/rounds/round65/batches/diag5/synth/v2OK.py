# Source Generated with Decompyle++ (Python version)
# File: v2.pyc (Python 3.11)

def p(datetime_list, freq, frequency, dts):
    offset = int(freq) // 5 if int(freq) // 5 else 1
    if datetime_list and int(frequency[:-1]) >= 5:
        del datetime_list[0]
    datetime_list = list(set(datetime_list))
    datetime_list.sort()
    x = datetime_list[0] if datetime_list else 0
    return (x, datetime_list)
