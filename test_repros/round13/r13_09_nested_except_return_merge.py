# -*- coding: utf-8 -*-
"""R13-H 复现：嵌套 except 里两处 `return None` 的退出块
（POP_EXCEPT ×2 + LOAD_CONST None + RETURN_VALUE）在原始字节码里是**两份副本**，
反编译产物合并成了**一份共享尾**。

对应真实目标：
  IQEngine/plugins/plugin_system_risk_calculation/function.pyc
      <module>.save_testds_to_json  [seq_len] orig=314 decomp=310

实测 dis（尾部）：
  ORIG   #292 1956 POP_EXCEPT ; #293 1958 JUMP_FORWARD '->1976'   <- 一个 handler 正常收尾
               #298 1968 POP_EXCEPT ; #299 1970 POP_EXCEPT ; #300 1972 LOAD_CONST None ; #301 1974 RETURN_VALUE
               #302 1976 POP_EXCEPT ; #303 1978 POP_EXCEPT ; #304 1980 LOAD_CONST None ; #305 1982 RETURN_VALUE
               （两份逐条相同，第二份才是 #293 的跳转落点）
  DECOMP 只有 1970 那一份，#293 的 JUMP_FORWARD 改成落在它上面 —— 少 4 条指令。
"""


def variant_a(ds, strategy_log, system_log, to_json_path, csv_path, txt_path):
    try:
        ds.to_json(to_json_path, orient='split')
        return None
    except BaseException:
        strategy_log.error('json failed')
        try:
            strategy_log.error(ds)
            return None
        except BaseException:
            system_log.error('print failed')
            try:
                ds.to_csv(csv_path, index=False)
                return None
            except BaseException:
                system_log.error('csv failed')
                try:
                    open(txt_path, 'w').write(ds.to_string())
                    return None
                except BaseException:
                    system_log.error('txt failed')
                    return None


def variant_b(ds, strategy_log, system_log, to_json_path, csv_path, txt_path):
    try:
        ds.to_json(to_json_path, orient='split')
        return None
    except BaseException:
        strategy_log.error('json failed')
        try:
            strategy_log.error(ds)
            return None
        except BaseException:
            system_log.error('print failed')
            try:
                ds.to_csv(csv_path, index=False)
            except BaseException:
                system_log.error('csv failed')
                try:
                    open(txt_path, 'w').write(ds.to_string())
                except BaseException:
                    system_log.error('txt failed')
                return None
