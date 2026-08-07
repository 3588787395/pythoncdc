# Source Generated with Decompyle++ (Python version)
# File: fly_exception.pyc (Python 3.11)

class FlyException(Exception):
    pass
class FlyVariableException(FlyException):
    pass
class CompileError(FlyException):
    def __init__(self, msg):
        self.message = msg
class UnknownError(FlyException):
    def __init__(self, msg):
        self.message = msg
class DateOutLimit(Exception):
    pass
class ParamsError(Exception):
    pass
