# Source Generated with Decompyle++ (Python version)
# File: c01_try_in_elif_arm.pyc (Python 3.11)

from __future__ import annotations
import six
class CommissionHelp:
    def set_commission(self, commission, _type):
        if not isinstance(commission, AbstractCommission):
            return None
        elif isinstance(_type, six.string_types):
            _type = _type.upper()
            try:
                AssetType(_type)
                self._commissions[_type] = commission
                return None
            except ValueError:
                system_log.error(get_traceback_message())
                return None
