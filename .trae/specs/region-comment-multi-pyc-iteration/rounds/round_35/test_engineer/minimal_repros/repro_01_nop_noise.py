"""R35 最小复现实例 1: NOP 指令噪声"""
# 原始: 编译器插入 NOP 对齐填充
# 反编译: NOP 丢失导致位置错位
# 预期: 过滤 NOP 后字节码一致

class TestClass:
    def method_with_nop(self):
        if self.value > 0:
            return self.data
        else:
            return None
