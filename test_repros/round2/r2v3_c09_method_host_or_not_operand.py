# round-2 r2v3 specimen (synthetic, minimal)
class C:
    def m(self, username, uinfo):
        if username not in uinfo or not uinfo[username]:
            raise Exception('no user')
        return 1
