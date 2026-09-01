"""R14 CTRL 09: isVaildDate variant — shared trailing call after if/elif/else.

CTRL (NO-DEFECT after R14 fix): variant of the isVaildDate pattern where the
shared trailing statement is a function call (not a return) after the
if/elif/else chain inside a try body. Verifies the R14 shared-merge-block fix
handles non-return trailing statements correctly.
"""


def check_value(date):
    try:
        if '-' in date:
            if len(date) != 10:
                log('bad')
            else:
                process(date, '%Y-%m-%d')
        elif len(date) != 8:
            log('bad')
        else:
            process(date, '%Y%m%d')
        log('ok')
    except BaseException:
        log('err')


def log(msg):
    pass


def process(date, fmt):
    pass
