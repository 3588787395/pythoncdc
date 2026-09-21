# -*- coding: utf-8 -*-
"""R21 锚点 10 —— 第二份孪生（HSIDOAuthCallbackHandler.post）的同构克隆。

目标函数 orig=175 decomp=166，与 01 逐指令同形（差在 `redirect` 与 `write_login_time`
前缀语句），用于验证"两条孪生必须同一结论"。
"""


class HSIDOAuthCallbackHandler(object):
    def post(self):
        user_name = self.get_argument('username', False)
        user = self.get_current_user()
        if user is None:
            user_id = yield self.authenticate()
            if user_id:
                user = self.user_from_username(user_id)
                self.set_login_cookie(user)
                self.redirect(self.home_url)
                self.write_login_time(user_id)
                if user.spawner:
                    if user.spawn_pending:
                        return
                    status = yield user.spawner.poll()
                    if status is not None:
                        yield self.spawn_single_user(user)
                        if self.cgroupmode == '1':
                            self.set_cgroup_config(user_id)
                            return
                        return
                    return
                else:
                    yield self.spawn_single_user(user)
                    if self.cgroupmode == '1':
                        self.set_cgroup_config(user_id)
                        return
                    return
            else:
                self.finish('login failed %s' % user_name)
                return
        else:
            self.redirect(self.home_url)
            return
