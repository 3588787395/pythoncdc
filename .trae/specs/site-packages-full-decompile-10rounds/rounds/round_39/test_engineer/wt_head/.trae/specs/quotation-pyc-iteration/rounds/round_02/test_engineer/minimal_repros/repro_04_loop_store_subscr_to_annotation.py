"""
Defect 04 (R1 残留，已演化) — LOOP: STORE_SUBSCR 被误发射为变量注解 `d[k]: d = call(...)` + spurious break
================================================================
关联 R1 repro：repro_04_loop_store_subscr_lost（R1：RHS CALL 丢失 + spurious for-else）。

R2 复现状态：**复现（形态演化）**。
  R1 表现：`for item in prod_code: item  else: return returninfo`（RHS 丢失 + for-else）
  R2 表现：`for item in prod_code: returninfo = {}; returninfo[item]: returninfo = call(...); break`
    —— `STORE_SUBSCR`（`returninfo[item] = call(...)`）被误重建为 PEP 526 变量注解
       `returninfo[item]: returninfo = call(...)`（语法上 `target: annotation = value`），
       且循环体被加上 spurious `break`，原 `return returninfo` 丢失。

触发位置：quotation.pyc::get_fundflow_day (R2 line 2182-2185)

触发区域类型：LOOP (for 循环) + STORE_SUBSCR (下标赋值)
根因初判：
    `core/cfg/region_ast_generator.py::_generate_loop` / `_build_effective_stmts`
    在处理 for 循环体内的 `STORE_SUBSCR`（d[k] = call(...)）时，把
    `LOAD_FAST d; LOAD_FAST k; <RHS CALL>; STORE_SUBSCR` 序列误判为
    `STORE_ANNOTATION`（变量注解），发射 `d[k]: d = call(...)`；
    同时 `_identify_loop_regions` 仍把循环后语句误归为 spurious break/else。
    违反「每块唯一归属」：STORE_SUBSCR 的 RHS CALL 应整体归赋值语句。

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

R2 反编译产物（错误，STORE_SUBSCR → 变量注解 + spurious break）：
    for item in prod_code:
        returninfo = {}
        returninfo[item]: returninfo = get_fundflow_day_single(item, get_type)
        break
期望产物：
    for item in prod_code:
        returninfo[item] = get_fundflow_day_single(item, get_type)
    return returninfo

验证：python pycdc.py <this>.pyc  # 观察 d[k]=call 退化为 d[k]: d = call + break
"""
def get_fundflow_day(prod_code, get_type='range'):
    if isinstance(prod_code, list):
        returninfo = {}
        for item in prod_code:
            returninfo[item] = get_fundflow_day_single(item, get_type)
        return returninfo
    return prod_code
