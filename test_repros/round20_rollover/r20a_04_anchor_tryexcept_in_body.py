import errno
import os
import sys


def rollover_tryexcept_body(name, count, rename):
    for x in range(count, 0, -1):
        src = '%s.%d' % (name, x)
        try:
            rename(src, src + '.t')
        except OSError:
            e = sys.exc_info()[1]
            if e.errno != errno.ENOENT:
                raise
        if os.path.exists(src):
            break
    else:
        finish(name)
        return
    tail(name)
