import os


class RotatingFileHandler(object):
    def __init__(self, fn, bc):
        self._filename = fn
        self.backup_count = bc

    def perform_rollover(self, rename, do_open):
        self.stream.close()
        for x in range(self.backup_count - 1, 0, -1):
            src = '%s.%d' % (self._filename, x)
            if os.path.exists(src):
                break
        else:
            rename(self._filename, self._filename + '.1')
            do_open('w')
            return
        for i in range(x, 0, -1):
            src = '%s.%d' % (self._filename, i)
            dst = '%s.%d' % (self._filename, i + 1)
            try:
                rename(src, dst)
            except OSError:
                e = sys.exc_info()[1]
                if e.errno != errno.ENOENT:
                    raise
        rename(self._filename, self._filename + '.1')
        do_open('w')
