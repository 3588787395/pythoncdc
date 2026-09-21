import os


def create_daily_stats(sdir, date_str, files, write):
    for x in range(30, 0, -1):
        fname = '%s/daily_%d.csv' % (sdir, x)
        if not os.path.exists(fname):
            break
    else:
        x = 0
    out = '%s/daily_%d.csv' % (sdir, x)
    write(out, date_str, files)
    return out
