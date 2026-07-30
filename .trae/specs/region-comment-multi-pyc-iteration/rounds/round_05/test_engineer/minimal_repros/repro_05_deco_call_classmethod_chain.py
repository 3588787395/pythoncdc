# Pattern M: @deco() + @classmethod chain — the exact BaseStorage pattern
# Original failing function: BaseStorage (cache_clear/cache_info use @classmethod,
#   __new__ uses @lru_cache()). Tests decorator call collapse in a chain context.
def deco():
    def inner(f):
        return f
    return inner

class BaseStorage(object):
    @deco()
    def __new__(cls, path):
        return super(BaseStorage, cls).__new__(cls)
    @classmethod
    def cache_clear(cls):
        cls.__new__.cache_clear()
    @classmethod
    def cache_info(cls):
        return cls.__new__.cache_info()
# verification: DEFECT-REPRO / NO-DEFECT
