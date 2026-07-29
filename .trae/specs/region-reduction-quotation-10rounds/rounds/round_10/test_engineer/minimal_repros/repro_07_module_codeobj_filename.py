"""R10 repro_07: <module> code 对象 filename 元数据差异（instr_diff@394）。
缺陷: 嵌套 code 对象的 co_filename 在原始为 './fly_docker_py311/fly/data/quotation.py'，
反编译产物为 '<decompiled>'，导致 LOAD_CONST code 对象比较不等(非语句丢失，元数据差异)。
区域类型: Sequence/Module  违反原则: 无（元数据差异，非算法缺陷）
"""
CONST = 1
def helper(x):
    return x + CONST
def main():
    return helper(2)
