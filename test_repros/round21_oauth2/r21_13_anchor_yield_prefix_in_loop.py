# -*- coding: utf-8 -*-
"""R21 锚点 13 —— A/B 同族形状出现在 **for 循环体内**（与 R20-A 的循环站点复合）。

R20-A 落在 `_collect_natural_loop_body`（region_analyzer.py:6169-6212）与生成层
W15-C（region_ast_generator.py:16934-16942/16988）；本复现的谓词落在
`_detect_boolop_conditional_chain` / `_check_elif_chain`（同文件 24186-24200、
18216-18243），**站点互不相交**。若两规则冲突，本项在候选核上会退化。
"""


class H(object):
    def yield_prefix_in_loop(self, users, user_id):
        for user in users:
            if user.spawner:
                yield self.poll(user)
                continue
            else:
                yield self.spawn_single_user(user)
                if self.cgroupmode == '1':
                    self.set_cgroup_config(user_id)
                    break
        return
