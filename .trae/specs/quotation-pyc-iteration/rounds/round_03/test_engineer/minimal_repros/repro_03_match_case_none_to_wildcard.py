"""
Defect R3-01 (R1/R2 残留) — MATCH：`case None` 塌缩为 `case _`（保真失败）
================================================================
关联 R1/R2 repro：repro_01_match_singleton_case_merge / repro_01_match_case_none_to_wildcard

R3 复现状态：**R2 未修复，quotation.pyc::process (line 1712-1714) 仍复现**。
  R3 表现（quotation.pyc::process）：
        match date:
            case _:                  # ← 原 case None:
                date = time.strftime('%Y-%m-%d')
  最小复现更进一步暴露 case None / case str() / case _ 三 case 全部退化为 case _ / case str() / case _，
  且首个 case None 被替换为 case _，导致 wildcard 重复（SyntaxError: wildcard makes remaining patterns unreachable）。

触发区域类型：MATCH（match/case 语句）
根因初判：
    `core/cfg/region_analyzer.py` / `pattern_parser.py` / `_generate_match`
    未把 `MATCH_CLASS` + `COMPARE_OP is None`（case None）重建为 `MatchSingleton(None)`，
    也未把 `MATCH_CLASS str` 重建为 `MatchClass(str, [])`，统一回退 `MatchAs(None)`（`case _`）。
    违反「嵌套即抽象节点」：case pattern 应作为独立抽象节点保留语义。

最小字节码模式（Python 3.11）：
    LOAD_FAST date
    MATCH_CLASS                 # match date:
      LOAD_CONST None           # case None:  ← 被替换为 case _
      COMPARE_OP is
    POP_JUMP_IF_FALSE
      LOAD_CONST 'none'
      RETURN_VALUE
    MATCH_CLASS str             # case str():
      POP_JUMP_IF_FALSE
      LOAD_FAST date
      RETURN_VALUE
    MATCH_CLASS                 # case _:  (wildcard)
      POP_JUMP_IF_FALSE
      ...

R3 反编译产物（错误）：
    def process(date):
        match date:
            case _:              # ← 原 case None:
                return 'none'
            case str():
                return date
            case _:               # ← 重复 case _（原 case _）
                date = date.replace('-', '')
                return date

期望产物：
    def process(date):
        match date:
            case None:
                return 'none'
            case str():
                return date
            case _:
                date = date.replace('-', '')
                return date

验证：
    $ python3 -c "import py_compile; py_compile.compile('repro_03_match_case_none_to_wildcard.py', 'repro_03_match_case_none_to_wildcard.pyc', doraise=True)"
    $ python pycdc.py repro_03_match_case_none_to_wildcard.pyc
    # 观察首个 case None 被替换为 case _，且与末尾 case _ 重复
"""
def process(date):
    match date:
        case None:
            return 'none'
        case str():
            return date
        case _:
            date = date.replace('-', '')
            return date
