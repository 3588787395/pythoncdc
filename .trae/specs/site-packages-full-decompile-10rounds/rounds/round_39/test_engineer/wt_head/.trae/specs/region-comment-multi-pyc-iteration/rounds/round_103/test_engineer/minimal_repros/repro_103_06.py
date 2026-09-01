def complex_boolean_or(fields, tmp_fields):
    need_exrights = 1
    if isinstance(fields, str) and fields not in tmp_fields or isinstance(fields, list):
        if len(set(fields).intersection(set(tmp_fields))) == 0:
            need_exrights = 0
    return need_exrights
