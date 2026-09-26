class ModifyExceptionFromType(object):
    def __init__(self, exc_from_type, force=False):
        self.exc_from_type = exc_from_type
        self.force = force
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is not None:
            exc_from_type = getattr(exc_val, const.EXC_EXT_NAME, const.ExcType.NOTSET)
            if self.force or exc_from_type == const.ExcType.NOTSET:
                setattr(exc_val, const.EXC_EXT_NAME, self.exc_from_type)
