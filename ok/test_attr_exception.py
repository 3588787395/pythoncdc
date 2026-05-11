"""测试属性访问异常类型的最小实例"""
import zmq

def test_attr_exception():
    try:
        x = 1 / 0
    except zmq.ZMQError as e:
        print(f'ZMQ error: {e}')
        raise
    except ValueError as e:
        print(f'Value error: {e}')
        raise
