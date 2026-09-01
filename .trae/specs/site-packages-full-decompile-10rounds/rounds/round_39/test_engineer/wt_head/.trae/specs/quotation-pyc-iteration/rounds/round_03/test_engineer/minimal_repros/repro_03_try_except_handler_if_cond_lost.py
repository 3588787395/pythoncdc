"""
Defect R3-07 (R1/R2 残留) — TRY/EXCEPT：except handler 内 `if e.attr == N:` 条件丢失→裸 `if GlobalClass:`
================================================================
关联 R1/R2 repro：repro_07_try_except_pass_to_del / repro_07_try_except_isinstance_lost

R3 复现状态：**R2 未修复，quotation.pyc::api_get_financial (line 141-146) 仍复现，且形态比 R2 描述更严重**。
  R3 表现（quotation.pyc::api_get_financial）：
        except HTTPError as e2:
            if HTTPError:           # ← 原 if e2.code == 401:
                pass
            else:
                if BaseException:   # ← 原 elif e2.code == 599 / elif ...:
                    pass
            error_no = e2.code
  原 R2 报告误以为是 `isinstance(e2, X)` 丢失；实际原字节码是 `e2.code == 401` / `e2.code == 599` 等
  `LOAD_FAST e2; LOAD_ATTR code; LOAD_CONST N; COMPARE_OP ==` 比较链，被整体替换为 except 子句的
  异常类全局名（`HTTPError` / `BaseException`），if 体塌缩为 `pass`。

触发区域类型：TRY + IF（except handler 内 if/elif 链）
根因初判：
    `region_ast_generator.py::_generate_try` 在 except handler 内重建 `if e.code == N:` 时，
    把 `LOAD_FAST e + LOAD_ATTR code + LOAD_CONST N + COMPARE_OP` 的 Compare 节点丢弃，
    改为引用 except 子句的 `LOAD_GLOBAL ExceptionClass`（HTTPError/BaseException），
    退化为裸 `if HTTPError:`（恒真）。违反「嵌套即抽象节点」+「入口引用语义」。

最小字节码模式（Python 3.11）：
    PUSH_EXC_INFO
    LOAD_GLOBAL HTTPError
    CHECK_EXC_MATCH
    POP_JUMP_IF_FALSE
    STORE_FAST e2
      LOAD_FAST e2
      LOAD_ATTR code
      LOAD_CONST 401
      COMPARE_OP ==              # ← if e2.code == 401:  ← 整段被丢弃
      POP_JUMP_IF_FALSE
        <body: time.sleep; return api_get_financial(...)>
      LOAD_FAST e2
      LOAD_ATTR code
      LOAD_CONST 599
      COMPARE_OP ==              # ← elif e2.code == 599:  ← 整段被丢弃
      ...

R3 反编译产物（错误）：
    except HTTPError as e2:
        if HTTPError:            # ← 原 if e2.code == 401:
            pass
        else:
            if BaseException:    # ← 原 elif e2.code == 599:
                pass

期望产物：
    except HTTPError as e2:
        if e2.code == 401:
            if request_times <= 2:
                time.sleep(10)
                return api_get_financial(url, params, request_times + 1)
            ...
        elif e2.code == 599:
            ...

验证：
    $ python3 -c "import py_compile; py_compile.compile('repro_03_try_except_handler_if_cond_lost.py', 'repro_03_try_except_handler_if_cond_lost.pyc', doraise=True)"
    $ python pycdc.py repro_03_try_except_handler_if_cond_lost.pyc
    # 观察 except handler 内 if e2.code == 401 条件丢失，退化为裸 if HTTPError / if BaseException
"""
def api_get_financial(url, params):
    token_value = get_token()
    try:
        response = requests.get(url)
        return_data = response.json()
    except HTTPError as e2:
        if e2.code == 401:
            time.sleep(10)
            return api_get_financial(url, params)
        elif e2.code == 599:
            error_info = str(e2)
            return ({'error_no': -1, 'error_info': error_info}, {})
        error_no = e2.code
    return ({'error_no': 0}, return_data)
