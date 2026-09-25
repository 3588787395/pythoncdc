
def p(datetime_list, freq, frequency, dts):
    offset = int(freq) // 5 if int(freq) // 5 else 1
    datetime_list = datetime_list[offset:]
    if datetime_list and int(frequency[:-1]) >= 5:
        del datetime_list[0]
    if dts[-1] in datetime_list:
        datetime_list.append(dts[-1])
    datetime_list = list(set(datetime_list))
    datetime_list.sort()
    x = datetime_list[0] if datetime_list else 0
    return (x, datetime_list)
