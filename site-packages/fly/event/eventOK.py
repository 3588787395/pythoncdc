# Source Generated with Decompyle++ (Python version)
# File: event.pyc (Python 3.11)

from event_priority import EVENT_NORM_PRIORITY
class Event(object):
    __doc__ = """
    *   事件对象定义，主要包括事件类型，优先级和参数
    *   目前在注册事件时，需要实例化
    """
    def __init__(self, event_type, event_priority=EVENT_NORM_PRIORITY, **kwargs):
        """
                         创建事件对象
        event_type : 事件类型
        event_priority ：事件优先级,默认优先级为一般
        parameter ： 参数
        """
        self.event_type = event_type
        self.event_priority = event_priority
        self.parameter = kwargs
    def __repr__(self):
        return 'Event({0})'.format(self.__dict__)
