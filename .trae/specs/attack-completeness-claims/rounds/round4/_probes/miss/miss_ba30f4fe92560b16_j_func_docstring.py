# Source Generated with Decompyle++ (Python version)
# File: i18n.pyc (Python 3.11)

import os.path
import traceback
from gettext import NullTranslations, translation
from IQCommon.logger import system_log
from IQCommon.util.pycompatibility import to_utf8
class Localization(object):
    def __init__(self, trans=None):
        self.trans = NullTranslations() if trans is None else trans
    def set_locale(self, locales, trans_dir=None):
        if locales[0] is None or 'en' in locales[0].lower():
            self.trans = NullTranslations()
            return None
        elif 'cn' in locales[0].lower():
            locales = ['zh_Hans_CN']
        try:
            if trans_dir is None:
                trans_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'translations')
            self.trans = translation(domain='messages', localedir=trans_dir, languages=locales)
            return None
        except BaseException:
            system_log.error('异常信息: %s' % traceback.format_exc())
            self.trans = NullTranslations()
            return None
localization = Localization()
def get_local_text(message):
    '\n    用于本地化多国语言函数\n    :param message:\n    :return:\n    Y'
    trans_txt = localization.trans.gettext(message)
    return to_utf8(trans_txt)
