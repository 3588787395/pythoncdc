# -*- coding: utf-8 -*-
"""R13-B 复现：循环体末端 region 被判成 `continue`，多出一条 JUMP_BACKWARD。

对应真实目标：
  IQCommon/util/user_info_utils.pyc   <module>.remove_lock_files   [seq_len] orig=96 decomp=97
  IQEngine/config/config.pyc          <module>.parse_config        [seq_len] orig=293 decomp=294

user_info_utils 实测 dis（尾部）：
  ORIG   #91 JUMP_BACKWARD 420 | #92 JUMP_BACKWARD 404 | #93 JUMP_BACKWARD 298
  DECOMP #91 JUMP_BACKWARD 420 | #92 JUMP_BACKWARD 420 <- 多余 | #93 JB 404 | #94 JB 298
即：try/except 作为最内层 for 体最后的语句，其后的 if 尾块被写成 `continue`，
除了真正的回边外又多派生出一条回边。

config.parse_config 实测 dis：
  ORIG   #89 JUMP_BACKWARD 478 | (#90) 512 LOAD_FAST 'k' ...
  DECOMP #89 JUMP_BACKWARD 478 | #90 JUMP_BACKWARD 478 <- 多余 | #91 514 LOAD_FAST 'k'
对应 OK.py 里被多写出来的那一行 `continue`（configOK.py:35）。

【2026-09-20 复核】对真实 pyc 直接跑严格尺子：
  IQCommon/util/user_info_utils.pyc  remove_lock_files 96 -> 97  **仍缺陷**（本类唯一存活真实成员）
  IQEngine/config/config.pyc         parse_config     293 -> 293 **已翻正**（并发 R13-A3 修复所致）
故 R13-B 目前的 18 文件收益 = 1（user_info_utils），不再是 2。
"""


def remove_lock_files(os, system_log, user_id, base_dirs, get_traceback_message):
    for base_dir in base_dirs:
        if os.path.exists(base_dir):
            for root, dirs, files in os.walk(base_dir):
                for file in files:
                    if file.endswith('.lock'):
                        file_path = os.path.join(root, file)
                        try:
                            os.unlink(file_path)
                        except BaseException:
                            system_log.error('clean fail {} {}'.format(user_id, get_traceback_message()))


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
