# Source Generated with Decompyle++ (Python version)
# File: repro_09_method_kwonly.pyc (Python 3.11)

class Logger(object):
    def __init__(self, name='default'):
        self.name = name
    def log(self, msg, *args, level='INFO'):
        return (self.name, msg, args, level)
logger = Logger()
result = logger.log('hello', 'extra', level='DEBUG')
