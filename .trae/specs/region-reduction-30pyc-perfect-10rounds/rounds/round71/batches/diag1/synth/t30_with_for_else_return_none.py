# F-THENOVER/adjacent-return (trade_info_utils query_trade_strategy_info /
# query_strategy_id): `if exists: try(with+for)/except / else: return None` compiles
# to two adjacent return-None blocks (614/618) with the guard targeting the first;
# decompiler re-attaches the arm so the guard targets the second (A@196 -> 614 vs
# B@196 -> 618).
import os


class FileLock:
    def __init__(self, path, mode=''):
        self.path = path

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FileIO:
    def __init__(self, path):
        self.path = path

    def read(self, return_type=None):
        return []


def query(path, trade_status):
    if os.path.exists(path):
        try:
            with FileLock(path, mode='shared'):
                file_io = FileIO(path)
                csv_reader = file_io.read(return_type='csv_reader')
            for items in csv_reader:
                if len(items) > 0 and items[2] in trade_status:
                    return True
        except BaseException:
            system_log.error('error')
    else:
        return None
