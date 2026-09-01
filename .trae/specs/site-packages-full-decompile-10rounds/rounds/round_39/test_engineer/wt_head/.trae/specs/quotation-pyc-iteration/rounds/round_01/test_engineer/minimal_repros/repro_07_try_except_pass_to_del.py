"""
Defect 07 — TRY/EXCEPT: `pass` 被误重建为 `del`，`return (tuple)` 退化为裸表达式
================================================================
触发区域类型：TRY (try/except)
根因初判：
    (a) `pass` → `del e2`:
        core/cfg/region_ast_generator.py `_generate_try` 在处理
        except handler 中 `pass` (对应 POP_TOP/NOP) 时，把
        except 变量清理指令 (DELETE_NAME e2 / POP_TOP) 误识别为
        用户语句 `del e2`，违反「每块唯一归属」：except 变量的
        隐式清理应归 except 机制，不应发射为源码 del。
    (b) `return (tuple)` → 裸 tuple + `return None`:
        `_generate_return` 在 except handler 内遇到
        `LOAD_CONST tuple + RETURN_VALUE` 时，把 RETURN_VALUE
        错误归约成 RETURN_CONST None，原 tuple 表达式被作为
        孤立 Expr 语句留在前面。

最小字节码模式（Python 3.11，except handler）：
    SETUP_FINALLY / SETUP_EXCEPT
    <try body>
    JUMP_FORWARD to <end>
  <except ConnectionRefusedError>:
    STORE_FAST e1
    <handler body>
    BUILD_TUPLE 2 / BUILD_MAP
    RETURN_VALUE
  <except HTTPError>:
    STORE_FAST e2
    LOAD_FAST e2
    <isinstance check>
    POP_JUMP_IF_FALSE
    <pass body: NOP>
    DELETE_FAST e2                      # except 变量清理
    <handler body>

反编译产物（错误）：
    except ConnectionRefusedError as e1:
        ...
        ({'error_no': error_no, 'error_info': error_info}, {})   # ← 裸表达式
        return None                                               # ← 错误 return
    except HTTPError as e2:
        if isinstance(e2, HTTPError):
            del e2                                                # ← pass 被改写
        elif isinstance(e2, BaseException):
            pass
期望产物：
    except ConnectionRefusedError as e1:
        ...
        return ({'error_no': error_no, 'error_info': error_info}, {})
    except HTTPError as e2:
        if isinstance(e2, HTTPError):
            pass
        elif isinstance(e2, BaseException):
            pass

验证：python pycdc.py <this>.pyc
"""
def api_get(url, params=None):
    try:
        response = requests.get(url)
        return_data = response.json()
    except ConnectionRefusedError as e1:
        system_log.error(get_traceback_message())
        error_no = -1
        error_info = e1
        return ({'error_no': error_no, 'error_info': error_info}, {})
    except HTTPError as e2:
        if isinstance(e2, HTTPError):
            pass
        elif isinstance(e2, BaseException):
            pass
        error_no = e2.code
        return ({'error_no': error_no}, {})
