# diag5 synthetic witness for R65-D5 (both lost statements in one shape)
def r65d5_probe(datetime_list, offset, frequency, datetime_list_section):
    datetime_list = datetime_list[offset:]
    if datetime_list and int(frequency[:-1]) >= 5:
        del datetime_list[0]
    if datetime_list_section[-1] in datetime_list:
        datetime_list.append(datetime_list_section[-1])
    return datetime_list
