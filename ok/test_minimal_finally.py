#!/usr/bin/env python3
def test_finally_order():
    """测试finally块中if语句的顺序"""
    context = None
    socket = None
    try:
        context = object()
        socket = object()
        return "data"
    finally:
        if socket:
            socket.close()
        if context:
            context.term()
