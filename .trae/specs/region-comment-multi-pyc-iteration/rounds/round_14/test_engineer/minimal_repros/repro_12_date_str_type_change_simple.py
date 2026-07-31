"""R14 CTRL 12: simple return with method chain (date_str_type_change).

CTRL (NO-DEFECT): mirrors tools.pyc date_str_type_change — a single-line
return with a strptime().strftime() method chain. Simplest structure in
tools.pyc, already matching 100%. Control group for baseline decompilation.
"""
import datetime


def date_str_type_change(date, in_type, out_type):
    return datetime.datetime.strptime(str(date), in_type).strftime(out_type)
