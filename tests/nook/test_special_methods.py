"""
第5批：类和对象测试 - 特殊方法
测试__str__、__repr__、__getitem__、__setitem__、__iter__、__next__等特殊方法
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.cfg import build_cfg, generate_ast

# 为了保持兼容性，添加build_cfg_from_source别名
def build_cfg_from_source(source, func_name=None):
    code_obj = compile(source, '<string>', 'exec')
    return build_cfg(code_obj)


# 测试用例1: __str__和__repr__
class WithStrRepr:
    def __str__(self):
        return 'str'
    
    def __repr__(self):
        return 'repr'


def test_str_repr():
    obj = WithStrRepr()
    return str(obj), repr(obj)


# 测试用例2: __getitem__和__setitem__
class WithItemAccess:
    def __init__(self):
        self.data = {}
    
    def __getitem__(self, key):
        return self.data[key]
    
    def __setitem__(self, key, value):
        self.data[key] = value


def test_item_access():
    obj = WithItemAccess()
    obj['key'] = 'value'
    return obj['key']


# 测试用例3: __iter__和__next__
class WithIteration:
    def __init__(self, n):
        self.n = n
        self.i = 0
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if self.i >= self.n:
            raise StopIteration
        self.i += 1
        return self.i


def test_iteration():
    return list(WithIteration(5))


# 测试用例4: __len__和__contains__
class WithLengthAndContain:
    def __init__(self, items):
        self.items = items
    
    def __len__(self):
        return len(self.items)
    
    def __contains__(self, item):
        return item in self.items


def test_len_contains():
    obj = WithLengthAndContain([1, 2, 3, 4, 5])
    return len(obj), 3 in obj


# 测试用例5: 比较方法
class WithComparison:
    def __init__(self, value):
        self.value = value
    
    def __eq__(self, other):
        if isinstance(other, WithComparison):
            return self.value == other.value
        return False
    
    def __lt__(self, other):
        if isinstance(other, WithComparison):
            return self.value < other.value
        return False
    
    def __hash__(self):
        return hash(self.value)


def test_comparison():
    obj1 = WithComparison(10)
    obj2 = WithComparison(20)
    obj3 = WithComparison(10)
    return obj1 == obj3, obj1 < obj2


# 测试用例6: 算术运算符
class WithArithmetic:
    def __init__(self, value):
        self.value = value
    
    def __add__(self, other):
        if isinstance(other, WithArithmetic):
            return WithArithmetic(self.value + other.value)
        return WithArithmetic(self.value + other)
    
    def __mul__(self, other):
        if isinstance(other, WithArithmetic):
            return WithArithmetic(self.value * other.value)
        return WithArithmetic(self.value * other)
    
    def __repr__(self):
        return f'WithArithmetic({self.value})'


def test_arithmetic():
    obj1 = WithArithmetic(5)
    obj2 = WithArithmetic(3)
    result = obj1 + obj2
    return result.value


# 测试用例7: 上下文管理器
class WithContext:
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        return False
    
    def do_something(self):
        return 'done'


def test_context_manager():
    with WithContext() as ctx:
        return ctx.do_something()


# 测试用例8: 可调用对象
class CallableClass:
    def __init__(self, prefix):
        self.prefix = prefix
    
    def __call__(self, name):
        return f'{self.prefix}: {name}'


def test_callable():
    greeter = CallableClass('Hello')
    return greeter('World')


class TestSpecialMethods(unittest.TestCase):
    """测试特殊方法"""
    
    def test_str_repr(self):
        """测试__str__和__repr__"""
        source = '''
class WithStrRepr:
    def __str__(self):
        return 'str'
    
    def __repr__(self):
        return 'repr'

def test_str_repr():
    obj = WithStrRepr()
    return str(obj), repr(obj)
'''
        cfg = build_cfg_from_source(source, 'test_str_repr')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_item_access(self):
        """测试__getitem__和__setitem__"""
        source = '''
class WithItemAccess:
    def __init__(self):
        self.data = {}
    
    def __getitem__(self, key):
        return self.data[key]
    
    def __setitem__(self, key, value):
        self.data[key] = value

def test_item_access():
    obj = WithItemAccess()
    obj['key'] = 'value'
    return obj['key']
'''
        cfg = build_cfg_from_source(source, 'test_item_access')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_iteration(self):
        """测试__iter__和__next__"""
        source = '''
class WithIteration:
    def __init__(self, n):
        self.n = n
        self.i = 0
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if self.i >= self.n:
            raise StopIteration
        self.i += 1
        return self.i

def test_iteration():
    return list(WithIteration(5))
'''
        cfg = build_cfg_from_source(source, 'test_iteration')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_len_contains(self):
        """测试__len__和__contains__"""
        source = '''
class WithLengthAndContain:
    def __init__(self, items):
        self.items = items
    
    def __len__(self):
        return len(self.items)
    
    def __contains__(self, item):
        return item in self.items

def test_len_contains():
    obj = WithLengthAndContain([1, 2, 3, 4, 5])
    return len(obj), 3 in obj
'''
        cfg = build_cfg_from_source(source, 'test_len_contains')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_comparison(self):
        """测试比较方法"""
        source = '''
class WithComparison:
    def __init__(self, value):
        self.value = value
    
    def __eq__(self, other):
        if isinstance(other, WithComparison):
            return self.value == other.value
        return False
    
    def __lt__(self, other):
        if isinstance(other, WithComparison):
            return self.value < other.value
        return False

def test_comparison():
    obj1 = WithComparison(10)
    obj2 = WithComparison(20)
    obj3 = WithComparison(10)
    return obj1 == obj3, obj1 < obj2
'''
        cfg = build_cfg_from_source(source, 'test_comparison')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_arithmetic(self):
        """测试算术运算符"""
        source = '''
class WithArithmetic:
    def __init__(self, value):
        self.value = value
    
    def __add__(self, other):
        if isinstance(other, WithArithmetic):
            return WithArithmetic(self.value + other.value)
        return WithArithmetic(self.value + other)

def test_arithmetic():
    obj1 = WithArithmetic(5)
    obj2 = WithArithmetic(3)
    result = obj1 + obj2
    return result.value
'''
        cfg = build_cfg_from_source(source, 'test_arithmetic')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_context_manager(self):
        """测试上下文管理器"""
        source = '''
class WithContext:
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        return False
    
    def do_something(self):
        return 'done'

def test_context_manager():
    with WithContext() as ctx:
        return ctx.do_something()
'''
        cfg = build_cfg_from_source(source, 'test_context_manager')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_callable(self):
        """测试可调用对象"""
        source = '''
class CallableClass:
    def __init__(self, prefix):
        self.prefix = prefix
    
    def __call__(self, name):
        return f'{self.prefix}: {name}'

def test_callable():
    greeter = CallableClass('Hello')
    return greeter('World')
'''
        cfg = build_cfg_from_source(source, 'test_callable')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


if __name__ == '__main__':
    unittest.main()
