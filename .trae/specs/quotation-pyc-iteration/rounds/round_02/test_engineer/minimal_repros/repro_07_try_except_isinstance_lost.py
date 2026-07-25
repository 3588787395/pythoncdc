"""
Defect 07 (R1 残留，部分已修) — TRY/EXCEPT：except handler 内 `isinstance(e, X)` 检查丢失，退化为裸 `if X:`
================================================================
关联 R1 repro：repro_07_try_except_pass_to_del（R1 已修复 return(tuple) 退化；
残留 `pass`→`del e2`）。

R2 复现状态：**`pass`→`del` 在本处已解除（R2 显示 `pass`），但 isinstance 检查丢失（新形态）**。
  quotation.pyc::api_get_financial line 141-145（R2 产物）：
        except HTTPError as e2:
            if HTTPError:           # ← 原 `if isinstance(e2, HTTPError):`
                pass
            else:
                if BaseException:   # ← 原 `elif isinstance(e2, BaseException):`
                    pass
    —— `isinstance(e2, HTTPError)` 的 CALL + POP_JUMP_IF_FALSE 序列中，
       `LOAD_GLOBAL isinstance + LOAD_FAST e2 + LOAD_GLOBAL HTTPError + CALL`
       被部分丢弃，只剩 `LOAD_GLOBAL HTTPError`，退化为裸 `if HTTPError:`
       （恒真，语义完全错误）。

触发区域类型：TRY (try/except) + CALL (isinstance)
根因初判：
    `core/cfg/region_ast_generator.py::_generate_try` 在 except handler 内重建
    `if isinstance(e, cls):` 时，把 `LOAD_GLOBAL isinstance + LOAD_FAST e + CALL`
    的 Call 节点拆解后只保留 `LOAD_GLOBAL cls`，receiver 与 arg 丢失，
    退化为裸 `if cls:`。
    违反「嵌套即抽象节点」：isinstance(e, cls) 应作为 Call 子节点整体作 If 条件。

最小字节码模式（Python 3.11，except handler 内 isinstance 链）：
    <except HTTPError>:
    STORE_FAST e2
    LOAD_GLOBAL isinstance
    LOAD_FAST e2
    LOAD_GLOBAL HTTPError
    PRECALL 2
    CALL 2
    POP_JUMP_IF_FALSE to <elif-branch>
    <if-body: pass>
    JUMP_FORWARD to <end>
  <elif-branch>:
    LOAD_GLOBAL isinstance
    LOAD_FAST e2
    LOAD_GLOBAL BaseException
    PRECALL 2
    CALL 2
    POP_JUMP_IF_FALSE to <end>
    <elif-body: pass>

R2 反编译产物（错误）：
    except HTTPError as e2:
        if HTTPError:
            pass
        else:
            if BaseException:
                pass
期望产物：
    except HTTPError as e2:
        if isinstance(e2, HTTPError):
            pass
        elif isinstance(e2, BaseException):
            pass

验证：python pycdc.py <this>.pyc  # 观察 isinstance(e, X) → 裸 if X:
"""
def api_get_financial(url, params=None):
    try:
        response = requests.get(url)
        return_data = response.json()
    except HTTPError as e2:
        if isinstance(e2, HTTPError):
            pass
        elif isinstance(e2, BaseException):
            pass
        return None
