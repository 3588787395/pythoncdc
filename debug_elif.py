import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.engine import Decompiler
import dis

# 测试用的简单if-elif-else源代码
source_code = """def f(a):
    if a > 10:
        a = 10
    elif a > 5:
        a = 5
    elif a > 0:
        a = 0
"""

# 编译源码
compiled = compile(source_code, '<string>', 'exec')

# 获取函数对象
namespace = {}
exec(compiled, namespace)
func = namespace['f']

# 打印原始字节码
print("=== 原始字节码 ===")
dis.dis(func.__code__)

# 反编译
decompiler = Decompiler()
decompiled = decompiler.decompile(func.__code__)

print("\n=== 反编译结果 ===")
print(decompiled)

# 重编译反编译结果
print("\n=== 重编译字节码 ===")
try:
    recompiled = compile(decompiled, '<recompiled>', 'exec')
    recompiled_namespace = {}
    exec(recompiled, recompiled_namespace)
    recompiled_func = recompiled_namespace['f']
    dis.dis(recompiled_func.__code__)
except Exception as e:
    print(f"重编译失败: {e}")
