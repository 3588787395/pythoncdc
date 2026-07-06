import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))

from tests.control_flow_completeness.base import ControlFlowCompletenessTest

class TestN15_WhileIfWhileIfBreak(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(grids, target):
    pos = None
    gi = 0
    while gi < len(grids):
        grid = grids[gi]
        if any(target in row for row in grid):
            gj = 0
            while gj < len(grid):
                row = grid[gj]
                ri = 0
                while ri < len(row):
                    if row[ri] == target:
                        pos = (gi, gj, ri)
                        break
                    ri += 1
                if pos:
                    break
                gj += 1
        if pos:
            break
        gi += 1
    return pos
"""

if __name__ == '__main__':
    test = TestN15_WhileIfWhileIfBreak()

    print("=== 原始代码 ===")
    print(test.SOURCE_CODE)

    print("\n=== 反编译结果 ===")
    original = test.compile_source()
    decompiled = test.decompile(original)
    print(decompiled)

    print("\n=== 语法验证 ===")
    print(f"语法正确: {test.verify_syntax_valid()}")

    print("\n=== 字节码等价性 ===")
    print(f"字节码等价: {test.verify_bytecode_equivalence()}")

    # 详细对比字节码
    import dis
    func_code = test._extract_func_code(original)
    recompiled = compile(decompiled, '<recompiled>', 'exec')
    recomp_func = test._extract_func_code(recompiled)

    if func_code and recomp_func:
        print("\n=== 原始字节码 ===")
        dis.dis(func_code)
        print("\n=== 重编译字节码 ===")
        dis.dis(recomp_func)
