# R20 repro_09: 类方法 kwonly 签名
class Logger(object):
    def __init__(self, name='default'):
        self.name = name

    def log(self, msg, *args, level='INFO'):
        return self.name, msg, args, level


logger = Logger()
result = logger.log('hello', 'extra', level='DEBUG')
