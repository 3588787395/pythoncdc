# Source Generated with Decompyle++ (Python version)
# File: function_dict.pyc (Python 3.11)

class FuncDict(dict):
    __doc__ = """

    """
    def __getattr__(item, self):
        """

        :param item:
        :return:
        """
        return self.get(item, None)
