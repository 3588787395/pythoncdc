"""
Defect R3-04b (R2 残留) — IF/TRY：try 块前 `file = ...` 赋值丢失（repro_04 文件赋值缺失）
================================================================
关联 R2 repro：repro_04_loop_store_subscr_to_annotation（R2 §9.5 残留：get_market_detail 内 `file = '...' % finance_mic` 赋值缺失）
                + R1 repro_04_loop_store_subscr_lost（STORE_SUBSCR/赋值目标丢失同源）

R3 复现状态：**R2 §9.5 已记录残留，quotation.pyc::get_market_detail (line 1994-2010) 仍复现**。
  R3 表现（quotation.pyc::get_market_detail）：
        def get_market_detail(finance_mic):
            df = pandas.DataFrame()
            if not isinstance(finance_mic, str):
                return df
            else:
                finance_mic = finance_mic.replace('XSHG', 'SS').replace('XSHE', 'SZ')
                if finance_mic not in FINANCE_MIC_INFO:
                    user_log.warning('请入参合法的市场代码')
                    return df
                else:
                    try:
                        with open(file, 'rb') as f:        # ← file 引用但未赋值
                            loaded_dict = pickle.load(f)
                        return pandas.DataFrame.from_dict(loaded_dict).T
                    except:
                        system_log.error(get_traceback_message())
                        return df
    —— try 块前的 `file = '/home/.../market_detail_%s_info.pickle' % finance_mic` 赋值整段丢失，
       导致 with open(file, ...) 中的 file 引用悬空（NameError）。
       R2 fix_report.md §9.5 明确将此列为残留：『get_market_detail 内 file = '...' % finance_mic 赋值仍缺失
       （try 体内首条赋值丢失）—— 属 STORE_SUBSCR/赋值目标丢失类缺陷（与 repro_04/08 同源），留待后续轮次』。

触发区域类型：IF + TRY（嵌套 IfRegion else 分支内 TryExcept）
根因初判：
    `core/cfg/region_ast_generator.py::_generate_try` / `_build_effective_stmts`
    在 TryRegion 与外层 IfRegion else 分支挂接时，把 try 入口前的顺序赋值语句（LOAD_CONST fmt /
    LOAD_FAST finance_mic / BINARY_OP % / STORE_FAST file）误识别为 TryExcept 的 setup/header 块
    而吞并，未作为 else 分支的顺序子节点保留。
    违反「自底向上归约」+「每块唯一归属」：try 入口前的顺序赋值应作为 IfRegion.else 分支的兄弟节点
    （顺序语句），不应被 TryExcept 吸收为 setup。

最小字节码模式（Python 3.11）：
    LOAD_GLOBAL isinstance
    LOAD_FAST finance_mic
    LOAD_GLOBAL str
    CALL
    POP_JUMP_IF_TRUE                  # if not isinstance(finance_mic, str): return df
      LOAD_FAST df
      RETURN_VALUE
    LOAD_FAST finance_mic
    LOAD_ATTR replace
    ...
    LOAD_GLOBAL FINANCE_MIC_INFO
    CONTAINS_OP 0
    POP_JUMP_IF_FALSE                 # if finance_mic not in FINANCE_MIC_INFO:
      ...
      RETURN_VALUE
    LOAD_CONST '/home/.../market_detail_%s_info.pickle'   # ← file = ... 整段丢失
    LOAD_FAST finance_mic
    BINARY_OP %
    STORE_FAST file                                          # ← STORE_FAST file 被吞并
    SETUP_FINALLY to <except_handler>                        # try:
      LOAD_GLOBAL open
      LOAD_FAST file                                         # ← 悬空引用
      LOAD_CONST 'rb'
      CALL
      ...

R3 反编译产物（错误，file 赋值丢失）：
    def get_market_detail(finance_mic):
        df = pandas.DataFrame()
        if not isinstance(finance_mic, str):
            return df
        else:
            finance_mic = finance_mic.replace('XSHG', 'SS').replace('XSHE', 'SZ')
            if finance_mic not in FINANCE_MIC_INFO:
                user_log.warning('请入参合法的市场代码')
                return df
            else:
                try:
                    with open(file, 'rb') as f:        # ← file 未定义
                        loaded_dict = pickle.load(f)
                    return pandas.DataFrame.from_dict(loaded_dict).T
                except:
                    system_log.error(get_traceback_message())
                    return df

期望产物：
    def get_market_detail(finance_mic):
        df = pandas.DataFrame()
        if not isinstance(finance_mic, str):
            return df
        else:
            finance_mic = finance_mic.replace('XSHG', 'SS').replace('XSHE', 'SZ')
            if finance_mic not in FINANCE_MIC_INFO:
                user_log.warning('请入参合法的市场代码')
                return df
            else:
                file = '/home/.../market_detail_%s_info.pickle' % finance_mic   # ← 应保留
                try:
                    with open(file, 'rb') as f:
                        loaded_dict = pickle.load(f)
                    return pandas.DataFrame.from_dict(loaded_dict).T
                except:
                    system_log.error(get_traceback_message())
                    return df

验证：
    $ python3 -c "import py_compile; py_compile.compile('repro_03_repro04_file_assignment_lost.py', 'repro_03_repro04_file_assignment_lost.pyc', doraise=True)"
    $ python pycdc.py repro_03_repro04_file_assignment_lost.pyc
    # 观察 file = '...' % finance_mic 赋值丢失，with open(file, ...) 引用悬空

R2 残留追踪：
    - R2 fix_report.md §9.5：『get_market_detail 内 file = '...' % finance_mic 赋值仍缺失
      （try 体内首条赋值丢失）—— 属 STORE_SUBSCR/赋值目标丢失类缺陷（与 repro_04/08 同源），留待后续轮次』。
    - R3 验证：缺陷仍存在（line 1994-2010 的反编译产物中 file 未定义即被引用）。
    - R2 §9.4.2 中『try/except 结构正确恢复』部分通过，但 try 入口前的顺序赋值仍丢失。
"""
def get_market_detail(finance_mic):
    df = make_dataframe()
    if not isinstance(finance_mic, str):
        return df
    else:
        finance_mic = finance_mic.replace('XSHG', 'SS').replace('XSHE', 'SZ')
        if finance_mic not in FINANCE_MIC_INFO:
            log_warning('请入参合法的市场代码')
            return df
        else:
            file = '/home/data/market_detail_%s_info.pickle' % finance_mic
            try:
                with open(file, 'rb') as f:
                    loaded_dict = pickle_load(f)
                return make_dataframe_from_dict(loaded_dict).T
            except Exception:
                log_error(get_traceback_message())
                return df
