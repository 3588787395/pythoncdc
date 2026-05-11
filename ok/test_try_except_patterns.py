#!/usr/bin/env python3
"""
测试异常处理模式 - 从quote.pyc提取

原始代码包含多种异常处理模式:
- try-except
- try-except-finally
- 嵌套try-except
"""

def api_get_from_zeromq(request_data, timeout=30):
    """模拟从ZeroMQ获取数据 - 带异常处理"""
    context = None
    socket = None
    
    try:
        import zmq
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        socket.setsockopt(zmq.RCVTIMEO, timeout * 1000)
        socket.connect("tcp://localhost:5555")
        
        socket.send_json(request_data)
        response = socket.recv_json()
        
        if response.get('code') != 0:
            raise ValueError(f"API error: {response.get('msg')}")
        
        return response.get('data')
    
    except zmq.ZMQError as e:
        print(f"ZMQ error: {e}")
        raise
    except ValueError as e:
        print(f"Value error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise
    finally:
        if socket:
            socket.close()
        if context:
            context.term()

def api_get_from_multi_zeromq(requests, timeout=30):
    """从多个ZeroMQ端点获取数据"""
    results = []
    errors = []
    
    for request in requests:
        try:
            result = api_get_from_zeromq(request, timeout)
            results.append(result)
        except Exception as e:
            errors.append((request, str(e)))
    
    if errors:
        print(f"Some requests failed: {errors}")
    
    return results

def get_individual_data(stock, data_type, start, end, fields, frequency):
    """获取个股数据 - 复杂异常处理"""
    try:
        # 参数检查
        if not stock:
            raise ValueError("Stock code is required")
        
        if not data_type:
            raise ValueError("Data type is required")
        
        # 构建请求
        request = {
            'stock': stock,
            'type': data_type,
            'start': start,
            'end': end,
            'fields': fields,
            'frequency': frequency
        }
        
        # 获取数据
        try:
            data = api_get_from_zeromq(request)
        except Exception as e:
            print(f"Failed to get data for {stock}: {e}")
            data = None
        
        # 数据处理
        if data:
            try:
                processed = process_data(data)
                return processed
            except Exception as e:
                print(f"Failed to process data: {e}")
                return data
        
        return None
    
    except Exception as e:
        print(f"Error in get_individual_data: {e}")
        return None

def process_data(data):
    """数据处理"""
    if not data:
        return None
    
    try:
        # 数据转换
        result = {}
        for key, value in data.items():
            if isinstance(value, list):
                result[key] = [float(v) if isinstance(v, (int, float)) else v for v in value]
            else:
                result[key] = value
        return result
    except (TypeError, ValueError) as e:
        print(f"Data processing error: {e}")
        return data

def safe_execute(func, *args, default=None, **kwargs):
    """安全执行函数"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"Error executing {func.__name__}: {e}")
        return default

if __name__ == "__main__":
    # 测试异常处理
    try:
        result = safe_execute(process_data, {'a': [1, 2, 3]})
        print(f"safe_execute result: {result}")
    except Exception as e:
        print(f"Test error: {e}")
