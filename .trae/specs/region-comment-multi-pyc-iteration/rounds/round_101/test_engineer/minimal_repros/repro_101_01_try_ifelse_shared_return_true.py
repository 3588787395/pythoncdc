# R101-Pattern-A-core: isVaildDate shape - try + if/else + shared `return True`
# tail inside try; except handler logs and re-raises. Regression since R98:
# decompiled output drops the shared-tail `return True` entirely.


def is_valid(date, parse):
    try:
        if '-' in date:
            parse(date, 'a')
        else:
            parse(date, 'b')
        return True
    except BaseException as x:
        raise x


def run(date):
    def parse(d, fmt):
        if not d:
            raise ValueError(d)
    return is_valid(date, parse)
