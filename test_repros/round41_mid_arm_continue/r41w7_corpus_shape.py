# -*- coding: utf-8 -*-
"""Round 41 positive witness for R41-B -- reduced from the corpus shape that the predicate
targets: an if-arm whose mid-list escaping tail block (statements + JUMP_BACKWARD to the
innermost loop header, nested if-chain merging into it) loses its `continue`.

The function below is the product of the landed arm for `fly/data/quote.pyc` with the
defect repaired by R41-B, i.e. it is the shape of the true source.  Landed bytes must be
DEFECT on it (one JUMP_BACKWARD short); the candidate arm must be CLEAN.
"""


class _R41W7Host(object):

        def one_prod_to_dataframe(self, data, prod_code, data_type=None):
            self.log.quote.debug('调用函数 one_prod_to_dataframe,参数为:prod_code=' + str(prod_code) + 'data=' + str(str(data)[:50]) + '...,data_type=' + str(data_type))
            df = {}
            fields = data.get('fields')
            index = []
            time_index = None
            try:
                time_index = fields.index('business_time')
            except BaseException:
                system_log.error(get_traceback_message())
            try:
                time_index = fields.index('min_time')
            except BaseException:
                system_log.error(get_traceback_message())
            for i, item in enumerate(fields):
                if time_index != i:
                    df[self.get_real_param(item)] = []
            prod = data.get(prod_code)
            if prod:
                for item in prod:
                    for i, v in enumerate(item):
                        if i == time_index:
                            v = str(v)
                            if len(v) == 8:
                                temp_time = f"{v[0:4]!s}-{v[4:6]!s}-{v[6:8]!s} {'00'!s}:{'00'!s}:{'00'!s}"
                            else:
                                if len(v) == 12:
                                    temp_time = f"{v[0:4]!s}-{v[4:6]!s}-{v[6:8]!s} {v[8:10]!s}:{v[10:12]!s}:{'00'!s}"
                                elif len(v) == 11:
                                    temp_time = f"{v[0:4]!s}-{v[4:6]!s}-{v[6:8]!s} 0{v[8:9]!s}:{v[9:11]!s}:{'00'!s}"
                                elif len(v) == 9:
                                    temp_time = f"{v[0:4]!s}-{v[4:6]!s}-{v[6:8]!s} {'00'!s}:0{v[8:9]!s}:{'00'!s}"
                                elif len(v) == 10:
                                    temp_time = f"{v[0:4]!s}-{v[4:6]!s}-{v[6:8]!s} {'00'!s}:{v[8:10]!s}:{'00'!s}"
                                elif len(v) == 14:
                                    temp_time = f'{v[0:4]!s}-{v[4:6]!s}-{v[6:8]!s} {v[8:10]!s}:{v[10:12]!s}:{v[12:14]!s}'
                                else:
                                    break
                                if int(temp_time[11:13]) >= 16 or int(temp_time[11:13]) < 9:
                                    break
                            index.append(temp_time)
                            continue
                        df[self.get_real_param(fields[i])].append(v)
            index = pandas.DatetimeIndex(index)
            columns = []
            if data_type is None:
                for i, item in enumerate(fields):
                    if time_index != i:
                        columns.append(self.get_real_param(item))
            else:
                columns = ['open', 'close', 'high', 'low', 'volume', 'money']
            return pandas.DataFrame(df, columns=columns, index=index)
