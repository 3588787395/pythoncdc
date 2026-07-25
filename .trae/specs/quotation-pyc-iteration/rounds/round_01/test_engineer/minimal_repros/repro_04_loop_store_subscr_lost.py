"""
Defect 04 — LOOP: STORE_SUBSCR 赋值在 for 循环体内丢失 + spurious for-else
================================================================
触发区域类型：LOOP (for 循环) + STORE_SUBSCR (下标赋值)
根因初判：
    core/cfg/region_ast_generator.py `_generate_loop` /
    `_build_effective_stmts` (L1698+) 在处理 for 循环 fall-through
    块中的 `STORE_SUBSCR` (d[k] = call(...)) 时，把 RHS 的 CALL
    表达式当作孤立的 expr 语句丢弃，只保留了 LOAD_FAST k 作为
    bare Name 表达式；同时把循环后的下一条 return 语句错误归入
    一个不存在的 for-else 分支（_identify_loop_regions 的 else
    归属判定偏离「每块唯一归属」原则）。

最小字节码模式（Python 3.11，for + STORE_SUBSCR + return）：
    FOR_ITER to <end>
      STORE_FAST item
      LOAD_FAST returninfo
      LOAD_FAST item                       # subscript key
      <RHS call: LOAD_GLOBAL + LOAD_FAST item, ...>
      STORE_SUBSCR                         # returninfo[item] = call(...)
      JUMP_BACKWARD to <for_iter>
  <end>:
    LOAD_FAST returninfo
    RETURN_VALUE

反编译产物（错误）：
    if isinstance(prod_code, list):
        returninfo = {}
        for item in prod_code:
            item                          # ← bare Name, RHS 丢失
        else:
            return returninfo             # ← spurious for-else
    else:
        return prod_code
期望产物：
    if isinstance(prod_code, list):
        returninfo = {}
        for item in prod_code:
            returninfo[item] = get_fundflow_day_single(item, get_type)
        return returninfo
    return prod_code

验证：python pycdc.py <this>.pyc  # 观察 STORE_SUBSCR 丢失与 for-else
"""
def get_fundflow_day(prod_code, get_type='range'):
    if isinstance(prod_code, list):
        returninfo = {}
        for item in prod_code:
            returninfo[item] = get_fundflow_day_single(item, get_type)
        return returninfo
    return prod_code
