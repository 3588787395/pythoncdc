"""Repro 09-10: D8 (P2) date_convert body collapsed to int(IfExp).

The quotation.pyc::date_convert defect (line 2144-2146) collapses:
    dict_temp = {'03-31':, '06-30':, ...}
    date_temp = date.replace('-', '')
    year_temp = int(date_temp[0:4])
    month_temp = pandas.Period(date, 'Q-DEC').quarter
    if report_types is not None:
        if month_temp == 1:
            ...
        else:
            ...
    else:
        if month_temp <= report_types:
            ...
        else:
            ...
    data_return = str(year_temp) + '-' + dict_temp[month_temp]
    return data_return
into a single bare Expr:
    int(month_temp == 1 if report_types is None else month_temp <= report_types)
The dict_temp / year_temp / month_temp assignments are discarded, and
the if/elif/else chain is replaced by an IfExp inside int(...).

This repro is the minimal form: a function with a dict literal, three
local assignments, a nested if/else, and a return.

Expected defect: the body is collapsed to `int(<IfExp>)` and the
return is lost.
"""


def date_convert(date, report_types):
    dict_temp = {'03-31': 1, '06-30': 2}
    date_temp = date.replace('-', '')
    year_temp = int(date_temp[0:4])
    month_temp = int(date_temp[4:6])
    if report_types is not None:
        if month_temp == 1:
            quarter = 1
        else:
            quarter = 2
    else:
        if month_temp <= report_types:
            quarter = 1
        else:
            quarter = 2
    data_return = str(year_temp) + '-' + dict_temp.get(str(quarter), '')
    return data_return
