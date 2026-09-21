import errno
import os
import sys


def perform_rollover(filename, backup_count, rename, do_open):
    close()
    for x in range(backup_count - 1, 0, -1):
        src = '%s.%d' % (filename, x)
        if os.path.exists(src):
            break
    else:
        rename(filename, filename + '.1')
        do_open('w')
        return
    for i in range(x, 0, -1):
        src = '%s.%d' % (filename, i)
        dst = '%s.%d' % (filename, i + 1)
        try:
            rename(src, dst)
        except OSError:
            e = sys.exc_info()[1]
            if e.errno != errno.ENOENT:
                raise
    rename(filename, filename + '.1')
    do_open('w')
