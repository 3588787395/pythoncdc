# Source Generated with Decompyle++ (Python version)
# File: r2_08_loop_tail_branches_dec_dec.pyc (Python 3.11)

__doc__ = """Repro: trade_operation duplicated loop back-edge (extra `continue`).

Original shape: for-loop nested inside `if -> try -> with`, body ends
with a plain statement (NO trailing continue); an earlier branch uses
`continue`:
    for items in csv_reader:
        if items[0] in trade_id_list:
            if operation == 'delete':
                items[2] = '2'
                delete_write_info.append(items)
                logger(items[0], items[1]).write(operation)
                continue
            if operation == 'pause':
                items[2] = '3'
            logger(items[0], items[1]).write(operation)
            write_info.append(items)
CPython emits ONE JUMP_BACKWARD at the loop tail; the decompiler adds
an explicit `continue` after the tail statement, so the recompiled loop
has TWO consecutive JUMP_BACKWARD (first_diff idx169: LOAD_GLOBAL(len)
vs JUMP_BACKWARD(654)).
"""
class FileLock:
    def __enter__(self):
        return self
    def __exit__(self, *exc):
        return False
class Logger:
    def __init__(self, user, item):
        self.args = (user, item)
    def write(self, op):
        return self.args
def trade_operation(path, csv_reader, trade_id_list, operation, write_info, delete_write_info):
    if len(csv_reader) > 0:
        try:
            with FileLock(path):
                for items in csv_reader:
                    if items[0] in trade_id_list:
                        if operation == 'delete':
                            items[2] = '2'
                            delete_write_info.append(items)
                            Logger(items[0], items[1]).write(operation)
                            continue
                        if operation == 'pause':
                            items[2] = '3'
                        if operation == 'reload':
                            items[2] = '4'
                        Logger(items[0], items[1]).write(operation)
                        write_info.append(items)
                        continue
        except BaseException:
            Logger(path, operation).write('error')
    return write_info
