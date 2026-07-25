"""
Defect R3-04 (R1/R2 残留) — LOOP：STORE_SUBSCR 退化为裸 Name / 变量注解 + spurious break
================================================================
关联 R1/R2 repro：repro_04_loop_store_subscr_lost / repro_04_loop_store_subscr_to_annotation

R3 复现状态：**R2 未修复，quotation.pyc::get_fundflow_day (line 2179-2182) 仍复现**。
  R3 表现（quotation.pyc::get_fundflow_day）：
        for item in prod_code:
            returninfo = {}
            returninfo[item]: returninfo = get_fundflow_day_single(...)   # ← STORE_SUBSCR→变量注解
            break                                                            # ← spurious break
  最小复现（无 isinstance 前置链）暴露形态略简：`returninfo[item] = call(...)` 的 RHS 丢失，
  仅剩 `item` 裸 Expr；并出现 spurious for-else `else: return returninfo`。

触发区域类型：LOOP（for 循环）+ STORE_SUBSCR
根因初判：
    `core/cfg/region_analyzer.py::_generate_loop` / `_build_effective_stmts`
    把 `LOAD_FAST d; LOAD_FAST k; <CALL>; STORE_SUBSCR` 误判为 `STORE_ANNOTATION`（PEP 526 变量注解），
    发射 `d[k]: d = call(...)`；在简化场景下 RHS 整体丢失只留 `k` 裸 Expr。
    `_identify_loop_regions` 的 else 归属判定把循环后语句误识别为 for-else body。
    违反「每块唯一归属」。

最小字节码模式（Python 3.11）：
    BUILD_MAP
    STORE_FAST returninfo
    GET_ITER
    FOR_ITER to <end>
      STORE_FAST item
      LOAD_GLOBAL get_fundflow_day_single
      LOAD_FAST item
      ...
      CALL
      LOAD_FAST returninfo          # ← STORE_SUBSCR 目标 dict
      LOAD_FAST item                # ← STORE_SUBSCR 下标
      STORE_SUBSCR                  # ← returninfo[item] = call(...)  ← 被丢失/误注解
    JUMP_BACKWARD

R3 反编译产物（错误）：
    def get_fundflow_day(prod_code, get_type, start_date, end_date):
        if start_date:
            check_datetime(start_date)
        if isinstance(prod_code, str):
            return get_fundflow_day_single(prod_code, get_type, start_date, end_date)
        elif isinstance(prod_code, list):
            returninfo = {}
            prod_code                                # ← 裸 Expr
            returninfo = {}                          # ← 重复赋值
            for item in prod_code:
                item                                 # ← 裸 Name（RHS 丢失）
            else:
                return returninfo                    # ← spurious for-else

期望产物：
    def get_fundflow_day(prod_code, get_type, start_date, end_date):
        ...
        elif isinstance(prod_code, list):
            returninfo = {}
            for item in prod_code:
                returninfo[item] = get_fundflow_day_single(item, get_type, start_date, end_date)
            return returninfo

验证：
    $ python3 -c "import py_compile; py_compile.compile('repro_03_loop_store_subscr_to_annotation.py', 'repro_03_loop_store_subscr_to_annotation.pyc', doraise=True)"
    $ python pycdc.py repro_03_loop_store_subscr_to_annotation.pyc
    # 观察 returninfo[item] = ... 丢失为裸 item，并出现 spurious for-else
"""
def get_fundflow_day(prod_code, get_type, start_date, end_date):
    if start_date:
        check_datetime(start_date)
    if isinstance(prod_code, str):
        return get_fundflow_day_single(prod_code, get_type, start_date, end_date)
    elif isinstance(prod_code, list):
        returninfo = {}
        for item in prod_code:
            returninfo[item] = get_fundflow_day_single(item, get_type, start_date, end_date)
        return returninfo
