"""
Defect R3-14 (R2 声称已修，实际未修) — IF/ELIF：elif 链后整个函数体截断（9 个财务函数 + 多处）
================================================================
关联 R1/R2 repro：repro_14_function_body_truncation_after_elif

R3 复现状态：**R2 修复声称已解除，但 quotation.pyc 中 9 个财务函数（get_balance_statement /
            get_income_statement / get_cashflow_statement / get_eps / get_cash_collection_ability /
            get_debt_paying_ability / get_growth_ability / get_operating_ability / get_profit_ability）
            仍全部截断到 64 指令（orig 458~469 → new 64）**。
  R3 表现（quotation.pyc::get_balance_statement line 1552-1564）：
        def get_balance_statement(security, date=None, report_types=None, ...):
            re_empty_data = pandas.DataFrame()
            re_data = pandas.DataFrame()
            error_re, re_security = convert_to_list(security)
            if error_re['error_no'] != 0:
                return re_empty_data
            else:
                security = re_security
                error_re, re_fields = convert_to_list(fields)
                if error_re['error_no'] != 0:
                    return re_empty_data
                elif date and isVaildDate(str(date)):
                    date = change_date_format(date)
        —— 截断点统一停在 `elif date and isVaildDate(str(date)): date = change_date_format(date)`，
           其后的 `if report_types is None: ...; for x in security: ...; return re_data` 整段丢失。
  R2 fix_report 称「9 个财务函数体不再截断 ✓」，但 R3 实测仍截断 —— R2 修复仅在最小复现上验证，
  未在 quotation.pyc 全量验证（或修复被后续改动回归）。

触发区域类型：IF/ELIF（elif A and B:）+ 函数体截断
根因初判：
    `region_ast_generator.py::_identify_conditional_regions` 的 R2 守卫（elif BoolOp 条件 + 结构区域
    入口 merge 点检测）未覆盖 quotation.pyc::get_balance_statement 的实际 CFG 结构——elif 条件
    `date and isVaildDate(str(date))` 的 `and` 短路归约后，elif body 之后的 fall-through 块
    （含 if report_types / for / return）仍被错误吸收为不可达子区域。
    违反「自底向上归约」+「每块唯一归属」。

最小字节码模式（Python 3.11）：
    LOAD_FAST date
    POP_JUMP_IF_FALSE                  # date and ...（第一支）
    LOAD_GLOBAL isVaildDate
    LOAD_GLOBAL str
    LOAD_FAST date
    CALL
    CALL
    POP_JUMP_IF_FALSE                  # elif date and isVaildDate(str(date)):
      LOAD_GLOBAL change_date_format
      LOAD_FAST date
      CALL
      STORE_FAST date                  #   date = change_date_format(date)
    <fall-through>:                    # ← 后续语句应在此顺序排列
      LOAD_FAST report_types
      POP_JUMP_IF_NOT_NONE             #   if report_types is None: ...
      ...
      GET_ITER
      FOR_ITER                         #   for x in security: ...
      LOAD_FAST re_data
      RETURN_VALUE                     #   return re_data
    —— fall-through 块被错误吸收为不可达子区域，整段丢失。

R3 反编译产物（错误，截断到 64 instr）：
    def get_balance_statement(security, date=None, ...):
        re_empty_data = pandas.DataFrame()
        re_data = pandas.DataFrame()
        error_re, re_security = convert_to_list(security)
        if error_re['error_no'] != 0:
            return re_empty_data
        else:
            security = re_security
            error_re, re_fields = convert_to_list(fields)
            if error_re['error_no'] != 0:
                return re_empty_data
            elif date and isVaildDate(str(date)):
                date = change_date_format(date)
    —— 后续 405 条指令整段丢失。

期望产物：
    def get_balance_statement(security, date=None, ...):
        ...
        elif date and isVaildDate(str(date)):
            date = change_date_format(date)
        if report_types is None:
            DEFAULT_REPORT_TYPES = [1, 2, 3, 4]
        ...
        for x in security:
            result = fetch(x, date)
            re_data = re_data.append(result)
        return re_data

验证：
    $ python3 -c "import py_compile; py_compile.compile('repro_03_elif_chain_func_body_truncation.py', 'repro_03_elif_chain_func_body_truncation.pyc', doraise=True)"
    $ python pycdc.py repro_03_elif_chain_func_body_truncation.pyc
    # 观察函数体在 elif A and B: 后整段截断（headers / try / return 丢失）
"""
def api_get(url, params=None):
    token_value = get_token()
    if not token_value:
        print('ERROR:获取token失败！')
        return None
    elif params:
        encode_params = urllib.parse.urlencode(params, encoding='gbk')
        real_url = url + '?' + encode_params
    else:
        real_url = url
    headers = {'Authorization': 'Bearer %s' % token_value}
    try:
        response = HTTPClient().request(real_url, headers)
        return response
    except HTTPError as x:
        error_info = str(x)
        return None
