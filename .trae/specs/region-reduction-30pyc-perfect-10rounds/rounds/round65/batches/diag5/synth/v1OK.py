# Source Generated with Decompyle++ (Python version)
# File: v1.pyc (Python 3.11)

def p(datetime_list, freq, frequency, dts):
    offset = int(freq) // 5 if int(freq) // 5 else 1
    datetime_list = datetime_list[offset:]
    if datetime_list and int(frequency[:-1]) >= 5:
        del datetime_list[0]
    return datetime_list
