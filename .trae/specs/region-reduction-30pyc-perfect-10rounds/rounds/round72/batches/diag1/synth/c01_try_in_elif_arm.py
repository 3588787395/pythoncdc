# F-EXCTABLE (commission.CommissionHelp.set_commission): `try/except ValueError`
# nested inside an `elif` arm whose body also assigns + returns.  The instruction
# stream stays byte-identical (18/18 bytes of exception table) but the protected
# range is emitted differently, so the ruler reports "Different bytecode" with
# instr identical / exception table differs.
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
