# -*- coding: utf-8 -*-
"""R17-A 02 anchor for + call tail.

与 01 同一区域结构，但尾随语句换成 **日志调用 + 构造字典**（真实 plugin_manager
形态：else 臂嵌套 if 之后是 log.debug(...) 与 plugin_module = ...）。

角色：锚点（anchor）—— 尾随语句的「种类」不应影响判据④的删除结论。
"""


def publish(records, log, encoder):
    for rid, item in records.items():
        if item.get('draft'):
            payload = {}
        else:
            if item.get('binary'):
                blob = encoder(item['data'])
            else:
                blob = item['data']
            log.info('encoded rid=%s size=%s', rid, len(blob))
            payload = {'id': rid, 'body': blob}
        records[rid] = payload
    return records
