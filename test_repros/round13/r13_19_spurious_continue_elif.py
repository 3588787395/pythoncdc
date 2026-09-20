# -*- coding: utf-8 -*-
"""R13-B 变体：链式 if 的某个分支内部还有 `if ...: continue`，该分支的 fall-through
本该接到链之后的共享尾，反编译器却在分支尾部又补一条 `continue`（多一条回边）。

对应真实目标：
  IQEngine/config/config.pyc  <module>.parse_config  [seq_len] orig=293 decomp=294

实测 dis：
  ORIG   #86 504 POP_JUMP_FORWARD_IF_FALSE '->512' | #87 506 LOAD_FAST 'v' ;
               #88 508 POP_JUMP_FORWARD_IF_TRUE '->512' | #89 510 JUMP_BACKWARD '->478'
               #90 512 LOAD_FAST 'k' ; #91 LOAD_METHOD 'split' ...
  DECOMP #86 504 POP_JUMP_FORWARD_IF_FALSE '->514' | #87-#89 同上
         #90 512 JUMP_BACKWARD '->478'   <- 多余：configOK.py:35 多写的那行 `continue`
         #91 514 LOAD_FAST 'k' ...

【2026-09-20 测试工程师复核：未复现，且原目标已翻正】
  * 对 site-packages/IQEngine/config/config.pyc 直接跑严格尺子：
    <module>.parse_config 293 -> 293 **MATCH**（本轮基线里的 +1 已消失，
    归因于并发进行的 R13-A3/R13-A 修复）。
  * 另测 4 个「elif 臂内嵌 `if ...: continue`」变体（链有/无 else、嵌套 continue
    在 if 臂/elif 臂）全部 MATCH。
  * 同族的 R13-B（r13_02：循环体尾被写成多余 continue）仍稳定复现，
    真实目标 IQCommon/util/user_info_utils.pyc remove_lock_files 96 -> 97 仍缺陷。
  * 结论：**未复现**（子形状不活跃）；EXPECT 标为 UNCONFIRMED。
    修复 R13-B 时以 r13_02 为准，不要拿本文件当依据。
"""


def parse_config(six, conf, click_type, config_args):
    if click_type:
        for k, v in six.iteritems(config_args):
            if v is None:
                continue
            elif k == 'strategy__accounts':
                if v:
                    continue
            else:
                key_path = k.split('__')
                sub_dict = conf
                for p in key_path[:-1]:
                    if p not in sub_dict:
                        sub_dict[p] = {}
                    sub_dict = sub_dict[p]
            sub_dict[key_path[-1]] = v
    return conf


def parse_config_wide(six, conf, click_type, config_args):
    for k, v in six.iteritems(config_args):
        if v is None:
            continue
        elif k == 'accounts':
            if v:
                continue
        elif k == 'symbols':
            if not v:
                continue
        else:
            key_path = k.split('__')
            sub_dict = conf
            for p in key_path[:-1]:
                if p not in sub_dict:
                    sub_dict[p] = {}
                sub_dict = sub_dict[p]
        sub_dict[key_path[-1]] = v
    return conf
