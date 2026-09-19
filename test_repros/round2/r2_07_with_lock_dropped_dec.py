# Source Generated with Decompyle++ (Python version)
# File: r2_07_with_lock_dropped.pyc (Python 3.11)

__doc__ = """Repro: trade_operation with-statement mis-reduction.

Original shape (with inside if inside if, inside an outer with):
    if len(write_info) > 0:
        file_io.write(write_info)
        if len(delete_write_info) > 0:
            mode = 'w' if new_file_flag else 'a'
            with FileLock(delete_path):
                FileIO(delete_path).write(delete_info, mode=mode)
        return True
    else:
        log('empty')
        return False

The decompiler dropped the `with FileLock(...):` wrapper (its header
reappears later as dead code `with FileLock(...): pass` after the
if/else) and left the FileIO write unindented. Bytecode loses the
BEFORE_WITH/PUSH_EXC_INFO/WITH_EXCEPT_START cluster and gains a
JUMP_FORWARD / return-None in the wrong place.
"""
class FileLock:
    def __init__(self, path):
        self.path = path
    def __enter__(self):
        return self
    def __exit__(self, *exc):
        return False
class FileIO:
    def __init__(self, path):
        self.path = path
    def write(self, rows, mode='w'):
        return len(rows)
_app_log = print
def trade_operation(file_io, write_info, delete_info, delete_path, new_file_flag):
    if len(write_info) > 0:
        file_io.write(write_info)
        if len(delete_info) > 0:
            mode = 'w' if new_file_flag else 'a'
            with FileLock(delete_path):
                FileIO(delete_path).write(delete_info, mode=mode)
        return True
    else:
        _app_log('empty rows')
        return False
