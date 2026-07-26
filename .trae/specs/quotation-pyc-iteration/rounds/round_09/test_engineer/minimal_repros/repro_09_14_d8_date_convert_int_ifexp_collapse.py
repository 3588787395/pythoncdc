"""Repro 09-14: D8 variant — date_convert with int() + IfExp collapse (quotation.pyc actual path).

The quotation.pyc::date_convert defect (line 2144-2146) collapses the
entire function body into:
    int(month_temp == 1 if report_types is None else month_temp <= report_types)
The dict_temp / year_temp / month_temp assignments are discarded, and
the if/elif/else chain is replaced by an IfExp inside int(...).

This repro is the closest minimal form of the quotation.pyc::
date_convert defect: a function with a dict literal, three local
assignments (including int()), a nested if/else over `report_types`,
and a return.

Expected defect: the body is collapsed to `int(<IfExp>)` and the
return is lost.
"""


def date_convert(date, report_types):
    dict_temp = {'03-31': 'Q1', '06-30': 'Q2', '09-30': 'Q3', '12-31': 'Q4'}
    date_temp = date.replace('-', '')
    year_temp = int(date_temp[0:4])
    month_temp = int(date_temp[4:6])
    if report_types is None:
        if month_temp == 1:
            quarter = dict_temp['03-31']
        else:
            quarter = dict_temp['06-30']
    else:
        if month_temp <= report_types:
            quarter = dict_temp['09-30']
        else:
            quarter = dict_temp['12-31']
    data_return = str(year_temp) + '-' + quarter
    return data_return
