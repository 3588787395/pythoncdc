"""
Defect 14 (R2 新增) — IF/ELIF：`elif A and B:` 分支后整个函数体被截断（9+ 函数塌缩到 ~64 指令）
================================================================
R1 关联：repro_10_if_nested_block_dropped（同源：if/elif 归约后整段语句丢失）。

R2 复现状态：**新出现（大面积，9 个财务函数）**。
  quotation.pyc R2 产物中以下函数均被截断到 ~64 指令（orig 250~469），
  截断点统一停在 `elif date and isVaildDate(str(date)): date = change_date_format(date)`：
    get_balance_statement  (orig=469 → r2=64)
    get_income_statement   (orig=369 → r2=278? 实际同截断)
    get_cashflow_statement (orig=461 → r2=64)
    get_eps / get_cash_collection_ability / get_debt_paying_ability /
    get_growth_ability / get_operating_ability / get_profit_ability (orig=458 → r2=64)
  —— `elif date and isVaildDate(str(date)):`（A= LOAD_FAST date 真值判定，
     B= CALL isVaildDate）分支体之后的全部语句（for 循环、return）被整体丢弃。

触发区域类型：IF/ELIF (elif A and B:) + 函数体截断
根因初判：
    `core/cfg/region_analyzer.py::_identify_if_regions` 在归约
    `if error: return X elif A and B: stmt` 时，elif 条件的 `and` 短路
    （A 真值 + B CALL）归约后，elif body 之后的 fall-through 块（含 for/return）
    被错误吸收为不可达子区域，导致函数体截断。
    违反「自底向上归约」+「每块唯一归属」：fall-through 后续语句应作为
    函数体的顺序子节点保留。

最小字节码模式（Python 3.11）：
    <if error_re['error_no'] != 0>:
      return re_empty_data
    <elif date and isVaildDate(str(date))>:
      LOAD_FAST date
      POP_JUMP_IF_FALSE to <next>          # A: date 真值
      LOAD_GLOBAL isVaildDate / LOAD_GLOBAL str / LOAD_FAST date / CALL / CALL
      POP_JUMP_IF_FALSE to <next>          # B: isVaildDate(str(date))
      <elif body: date = change_date_format(date)>
    <next>:                                 # ← fall-through 整段丢失
      <for ...; return re_data>

R2 反编译产物（错误，elif 后整段丢失）：
    def get_balance_statement(...):
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
    def <next-func>: ...
期望产物：
    def get_balance_statement(...):
        ...（上述前缀）
        elif date and isVaildDate(str(date)):
            date = change_date_format(date)
        for secu in security:
            ...
        return re_data

验证：python pycdc.py <this>.pyc  # 观察 elif A and B 后函数体被截断
"""
def get_balance_statement(security, date=None, fields=None):
    re_empty_data = pandas.DataFrame()
    error_re, re_security = convert_to_list(security)
    if error_re['error_no'] != 0:
        return re_empty_data
    elif date and isVaildDate(str(date)):
        date = change_date_format(date)
    for secu in re_security:
        row = fetch_row(secu, date)
        re_empty_data = re_empty_data.append(row)
    return re_empty_data
