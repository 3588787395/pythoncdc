def growth_factors_sql_get(self, security, table, start_year, end_year, fields=None, report_types=None):
        if table == 'growth_ability':
            if fields is None:
                sql_code = """
                select case when SecuMarket= '83' then secucode || '.SS' when SecuMarket = '90' then secucode || 
                '.SZ' else secucode END secucode, SecuAbbr, TO_CHAR(ENDDATE, 'yyyy-MM-dd') EndDate, 
                TO_CHAR(InfoPublDate, 'yyyy-MM-dd') as InfoPublDate, BasicEPSYOY, DilutedEPSYOY, 
                OperatingRevenueGrowRate, NPParentCompanyYOY, NetOperateCashFlowYOY, OperProfitGrowRate, 
                TotalProfeiGrowRate, EPSGrowRateYTD, SEWithoutMIGrowRateYTD, TAGrowRateYTD, NPParentCompanyCutYOY, 
                AvgNPYOYPastFiveYear, OperCashPSGrowRate, NAORYOY, NetAssetGrowRate, TotalAssetGrowRate, 
                SustainableGrowRate, NetProfitGrowRate  """
                fields_list = const.TABLE_FIELDS['growth_ability']
                sql_code += """ from (select A.*, B.SecuCode, SecuAbbr, SecuMarket, C.InfoPublDate, ROW_NUMBER() over(PARTITION 
        BY C.CompanyCode, C.EndDate ORDER BY C.IfAdjusted desc, C.IfMerged, C.InfoPublDate) as row_index from 
        LC_MainIndexNew A join SecuMain B on A.CompanyCode = B.CompanyCode left join LC_IncomeStatementAll C ON 
        C.CompanyCode = A.CompanyCode where B.SecuCategory IN ('1', '2') AND B.ListedSector IN ('1', '2', '6') and 
        B.SecuCode in ("""
                for stock in security:
                    if stock != security[-1]:
                        sql_code += "'%s', " % stock
                        continue
                    sql_code += "'%s') " % stock
            else:
                fields_list = const.DEFAULT_FIELDS['growth_ability'].copy()
                sql_code = """select case when SecuMarket= '83' then secucode || '.SS' when SecuMarket = '90' then 
                secucode  || '.SZ' else secucode END secucode, SecuAbbr, TO_CHAR(ENDDATE, 'yyyy-MM-dd') 
                EndDate, TO_CHAR(InfoPublDate, 'yyyy-MM-dd') as InfoPublDate"""
                for field in fields:
                    if field in const.DEFAULT_FIELDS[table]:
                        continue
                    elif field in const.FIELDS_EXCHANGE_ENUM[table].keys():
                        code = const.FIELDS_EXCHANGE_ENUM[table][field]
                    else:
                        code = field.replace('_', '')
                    sql_code += ', %s' % code
                    fields_list.append(field)
        elif table == 'profit_ability':
            if fields is None:
                sql_code = """
                    select case when SecuMarket= '83' then secucode || '.SS' when SecuMarket = '90' then secucode || 
                    '.SZ' else secucode END secucode, SecuAbbr, TO_CHAR(ENDDATE, 'yyyy-MM-dd') EndDate, 
                    TO_CHAR(InfoPublDate, 'yyyy-MM-dd') as InfoPublDate, ROEAvg, ROEWeighted, ROE, ROECut, 
                    ROECutWeighted, ROETTM, ROA_EBIT, ROA_EBITTTM, ROA, ROATTM, ROIC, NetProfitRatio, NetProfitRatioTTM, 
                    GrossIncomeRatio,GrossIncomeRatioTTM, SalesCostRatio, PeriodCostsRate, PeriodCostsRateTTM, NPToTOR, 
                    NPToTORTTM, OperatingProfitToTOR, OperatingProfitToTORTTM, EBITToTOR, EBITToTORTTM, 
                    TOperatingCostToTOR, TOperatingCostToTORTTM, OperatingExpenseRate, OperatingExpenseRateTTM, 
                    AdminiExpenseRate, AdminiExpenseRateTTM, FinancialExpenseRate, FinancialExpenseRateTTM, 
                    AssetImpaLossToTOR, AssetImpaLossToTORTTM, NetProfit, NetProfitCut, EBIT, EBITDA, 
                    OperatingProfitRatio, TotalProfitCostRatio """
                fields_list = const.TABLE_FIELDS[table]
            else:
                fields_list = const.DEFAULT_FIELDS[table].copy()
                sql_code = """select case when SecuMarket= '83' then secucode || '.SS' when SecuMarket = '90' then 
                    secucode  || '.SZ' else secucode END secucode, SecuAbbr, TO_CHAR(ENDDATE, 'yyyy-MM-dd') 
                    EndDate, TO_CHAR(InfoPublDate, 'yyyy-MM-dd') as InfoPublDate"""
                for field in fields:
                    if field in const.DEFAULT_FIELDS[table]:
                        continue
                    elif field in const.FIELDS_EXCHANGE_ENUM[table].keys():
                        code = const.FIELDS_EXCHANGE_ENUM[table][field]
                    else:
                        code = field.replace('_', '')
                    sql_code += ', %s' % code
                    fields_list.append(field)
        elif table == 'eps':
            if fields is None:
                sql_code = """
                select case when SecuMarket= '83' then secucode || '.SS' when SecuMarket = '90' then 
                secucode  || '.SZ' else secucode END secucode, SecuAbbr, TO_CHAR(ENDDATE, 'yyyy-MM-dd') 
                EndDate, TO_CHAR(InfoPublDate, 'yyyy-MM-dd') as InfoPublDate, BasicEPS, DilutedEPS, EPS, 
                EPSTTM, NetAssetPS, TotalOperatingRevenuePS, MainIncomePS, OperatingRevenuePSTTM, OperProfitPS, 
                EBITPS, CapitalSurplusFundPS, SurplusReserveFundPS, AccumulationFundPS, UndividedProfit, 
                RetainedEarningsPS, OperCashFlowPS, OperCashFlowPSTTM, CashFlowPS, CashFlowPSTTM, EnterpriseFCFPS, 
                ShareHolderFCFPS"""
                fields_list = const.TABLE_FIELDS[table]
            else:
                fields_list = const.DEFAULT_FIELDS[table].copy()
                sql_code = """select case when SecuMarket= '83' then secucode || '.SS' when SecuMarket = '90' then 
                secucode  || '.SZ' else secucode END secucode, SecuAbbr, TO_CHAR(ENDDATE, 'yyyy-MM-dd') 
                EndDate, TO_CHAR(InfoPublDate, 'yyyy-MM-dd') as InfoPublDate"""
                for field in fields:
                    if field in const.DEFAULT_FIELDS[table]:
                        continue
                    elif field in const.FIELDS_EXCHANGE_ENUM[table].keys():
                        code = const.FIELDS_EXCHANGE_ENUM[table][field]
                    else:
                        code = field.replace('_', '')
                    sql_code += ', %s' % code
                    fields_list.append(field)
        elif table == 'operating_ability':
            if fields is None:
                sql_code = """
                select case when SecuMarket= '83' then secucode || '.SS' when SecuMarket = '90' then 
                secucode  || '.SZ' else secucode END secucode, SecuAbbr, TO_CHAR(ENDDATE, 'yyyy-MM-dd') 
                EndDate, TO_CHAR(InfoPublDate, 'yyyy-MM-dd') as InfoPublDate, OperCycle, InventoryTRate, 
                InventoryTDays, ARTRate, ARTDays, AccountsPayablesTRate, AccountsPayablesTDays, CurrentAssetsTRate, 
                FixedAssetTRate, EquityTRate, TotalAssetTRate"""
                fields_list = const.TABLE_FIELDS[table]
            else:
                fields_list = const.DEFAULT_FIELDS[table].copy()
                sql_code = """select case when SecuMarket= '83' then secucode || '.SS' when SecuMarket = '90' then 
                secucode  || '.SZ' else secucode END secucode, SecuAbbr, TO_CHAR(ENDDATE, 'yyyy-MM-dd') 
                EndDate, TO_CHAR(InfoPublDate, 'yyyy-MM-dd') as InfoPublDate"""
                for field in fields:
                    if field in const.DEFAULT_FIELDS[table]:
                        continue
                    elif field in const.FIELDS_EXCHANGE_ENUM[table].keys():
                        code = const.FIELDS_EXCHANGE_ENUM[table][field]
                    else:
                        code = field.replace('_', '')
                    sql_code += ', %s' % code
                    fields_list.append(field)
        elif table == 'debt_paying_ability':
            if fields is None:
                sql_code = """
                 select case when SecuMarket= '83' then secucode || '.SS' when SecuMarket = '90' then 
                 secucode  || '.SZ' else secucode END secucode, SecuAbbr, TO_CHAR(ENDDATE, 'yyyy-MM-dd') 
                 EndDate, TO_CHAR(InfoPublDate, 'yyyy-MM-dd') as InfoPublDate, CurrentRatio, QuickRatio, 
                 SuperQuickRatio, DebtEquityRatio, SEWithoutMIToTL, SEWMIToInterestBearDebt, DebtTangibleEquityRatio, 
                 TangibleAToInteBearDebt, TangibleAToNetDebt, round(EBITDAToTLiability,2), round(NOCFToTLiability,2), 
                 round(NOCFToInterestBearDebt,2), round(NOCFToCurrentLiability,2), round(NOCFToNetDebt,2), 
                 InterestCover, LongDebtToWorkingCapital, OperCashInToCurrentDebt"""
                fields_list = const.TABLE_FIELDS[table]
            else:
                fields_list = const.DEFAULT_FIELDS[table].copy()
                sql_code = """select case when SecuMarket= '83' then secucode || '.SS' when SecuMarket = '90' then 
                 secucode  || '.SZ' else secucode END secucode, SecuAbbr, TO_CHAR(ENDDATE, 'yyyy-MM-dd') 
                 EndDate, TO_CHAR(InfoPublDate, 'yyyy-MM-dd') as InfoPublDate"""
                for field in fields:
                    if field in const.DEFAULT_FIELDS[table]:
                        continue
                    elif field in const.FIELDS_EXCHANGE_ENUM[table].keys():
                        code = const.FIELDS_EXCHANGE_ENUM[table][field]
                    else:
                        code = field.replace('_', '')
                    sql_code += ', %s' % code
                    fields_list.append(field)
        sql_code += """ from (select A.*, B.SecuCode, SecuAbbr, SecuMarket, C.InfoPublDate, ROW_NUMBER() over(PARTITION 
        BY C.CompanyCode, C.EndDate ORDER BY C.IfAdjusted desc, C.IfMerged, C.InfoPublDate) as row_index from 
        LC_MainIndexNew A join SecuMain B on A.CompanyCode = B.CompanyCode left join LC_IncomeStatementAll C ON 
        C.CompanyCode = A.CompanyCode where B.SecuCategory IN ('1', '2') AND B.ListedSector IN ('1', '2', '6') and 
        B.SecuCode in ("""
        security
        if start_year == end_year or report_types == None:
            start_date, end_date = self.get_year_params(start_year, end_year, report_types)
            sql_code += f'\n            AND A.EndDate between to_date(\'{start_date!s}\', \'yyyy-mm-dd\') and to_date(\'{end_date!s}\', \'yyyy-mm-dd\') and C.EndDate = A.EndDate \n            and C.IfAdjusted IN (\'1\', \'2\')) WHERE row_index = 1 order by EndDate desc'
        else:
            sql_code += 'AND ('
            year_count = -1
            year_difference = int(end_year) - int(start_year)
            for year in range(int(start_year), int(end_year) + 1):
                year_count += 1
                start_date, end_date = self.get_year_params(str(year), str(year), report_types)
                if year_count != year_difference:
                    sql_code += f'A.EndDate between to_date(\'{start_date!s}\', \'yyyy-mm-dd\') and to_date(\'{end_date!s}\', \'yyyy-mm-dd\') or\n                    '
                    continue
                sql_code += f'A.EndDate between to_date(\'{start_date!s}\', \'yyyy-mm-dd\') and to_date(\'{end_date!s}\', \'yyyy-mm-dd\')) and \n                    C.EndDate = A.EndDate and C.IfAdjusted IN (\'1\', \'2\')) WHERE row_index = 1 order by EndDate desc \n                    '
        return (sql_code, fields_list)
    def get_financial_date_mode(self, security, table, date, report_types, column, list_base, date_type, merge_type):
        """
        鎸夋棩鏈熻幏鍙栬储鍔℃暟鎹ā寮忔帴鍙?
        """
        if column == None:
            column_default = const.TABLE_FIELDS[table]
        else:
            column_default = column
        dataframe_default = pandas.DataFrame(index=security, columns=column_default).drop('secu_code', axis=1)
        dataframe_default.index.name = 'secu_code'
        start_year, end_year, report_types = self.date_to_quarter(str(date), report_types)
        error_msg, financial_data_tmp = self.get_open_api_data(security=str(security), table=table, start_year=start_year, end_year=end_year, report_types=report_types, fields=str(column), date_type=date_type, merge_type=merge_type)
        if error_msg['error_no'] != '0':
            return EMPTY_DF
        elif financial_data_tmp.empty:
            return dataframe_default
        elif date_type is None:
            date_tmp = self.change_date_type(date)
            financial_data_tmp1 = financial_data_tmp[financial_data_tmp.publ_date < date_tmp]
            financial_data_tmp = financial_data_tmp1
        financial_data_tmp.index = financial_data_tmp['secu_code'].tolist()
        dataframe_default.update(financial_data_tmp)
        financial_data = dataframe_default.replace('--', str(numpy.nan))
        for field in financial_data.columns:
            if field not in list_base and field != 'company_type':
                if table in const.GROWTH_FACTORS_2f:
                    financial_data[field] = financial_data[field].astype('float64').round(2).replace(numpy.float64(-0.0), numpy.float64(0))
                    continue
                if table in const.GROWTH_FACTORS_4f:
                    financial_data[field] = financial_data[field].astype('float64').round(4).replace(numpy.float64(-0.0), numpy.float64(0))
                    continue
                financial_data[field] = financial_data[field].astype('float64').replace(numpy.float64(-0.0), numpy.float64(0))
        financial_data.index.name = 'secu_code'
        return financial_data
    def get_financial_year_mode(self, security, table, start_year, end_year, report_types, column, list_base, merge_type):
        """
        鎸夊勾浠借幏鍙栬储鍔℃暟鎹ā寮忔帴鍙?
        """
        error_msg, financial_data_tmp = self.get_open_api_data(security=str(security), table=table, start_year=start_year, end_year=end_year, report_types=str(report_types), fields=str(column), merge_type=merge_type)
        if error_msg['error_no'] != '0':
            financial_data = {}
            for code in security:
                financial_data[code] = EMPTY_DF
            financial_data = pandas.Panel(financial_data)
            return financial_data
        elif financial_data_tmp.empty:
            financial_data = {}
            for code in security:
                financial_data[code] = EMPTY_DF
            financial_data = pandas.Panel(financial_data)
            return financial_data
        else:
            financial_data_tmp.index = financial_data_tmp['end_date'].tolist()
            financial_data = financial_data_tmp.replace('--', str(numpy.nan))
            for field in financial_data.columns:
                if field not in list_base and field != 'company_type':
                    if table in const.GROWTH_FACTORS_2f:
                        financial_data[field] = financial_data[field].astype('float64').round(2).replace(numpy.float64(-0.0), numpy.float64(0))
                        continue
                    if table in const.GROWTH_FACTORS_4f:
                        financial_data[field] = financial_data[field].astype('float64').round(4).replace(numpy.float64(-0.0), numpy.float64(0))
                        continue
                    financial_data[field] = financial_data[field].astype('float64').replace(numpy.float64(-0.0), numpy.float64(0))
            financial_data = financial_data.set_index(['end_date', 'secu_code'])
            financial_data = financial_data.to_panel().swapaxes('items', 'minor')
            return financial_data
    def get_financial_and_growth_factors(self, security, table, date=None, start_year=None, end_year=None, report_types=None, fields=None, date_type=None, merge_type=None):
        """
        涓夊ぇ璐㈡姤銆佸叚澶ф垚闀挎寚鏍囨暟鎹幏鍙栨帴鍙?
        """
        error_msg, fields_tmp = self.convert_to_list(fields)
        if error_msg['error_no'] != 0:
            system_log.error(error_msg['error_info'])
            return EMPTY_DF
        else:
            if fields_tmp is not None:
                fields_tmp = list(set(const.DEFAULT_FIELDS[table]).union(fields_tmp))
            if report_types is not None:
                default_report_types = [1, 2, 3, 4]
                if isinstance(report_types, str):
                    report_types = int(report_types)
                if report_types not in default_report_types:
                    return EMPTY_DF
            list_base = const.UN_CONVERT_FIELDS['financial']
            try:
                if date is not None:
                    return self.get_financial_date_mode(security=security, table=table, date=date, report_types=report_types, column=fields_tmp, list_base=list_base, date_type=date_type, merge_type=merge_type)
                else:
                    return self.get_financial_year_mode(security=security, table=table, start_year=start_year, end_year=end_year, report_types=report_types, column=fields_tmp, list_base=list_base, merge_type=merge_type)
            except Exception as x:
                system_log.error(get_traceback_message())
                raise x
    def get_valuation(self, security, table, fields=None, date=None):
        """
        鑲℃湰淇℃伅銆佷及鍊兼暟鎹暟鎹幏鍙?
        """
        error_msg, fields_tmp = self.convert_to_list(fields)
        if error_msg['error_no'] != 0:
            system_log.error(error_msg['error_info'])
            return EMPTY_DF
        elif fields_tmp is not None:
            fields_tmp = list(set(const.DEFAULT_FIELDS[table]).union(fields_tmp))
            column_default = list(set(const.DEFAULT_FIELDS[table]).union(fields_tmp))
        else:
            column_default = const.TABLE_FIELDS[table]
        list_base = const.UN_CONVERT_FIELDS[table]
        try:
            dataframe_default = pandas.DataFrame(index=security, columns=column_default).drop(['secu_code'], axis=1)
            dataframe_default.index.name = 'secu_code'
            error_msg, financial_data_tmp = self.get_open_api_data(security=str(security), table='valuation', date=str(date), fields=str(fields_tmp))
            if error_msg['error_no'] != '0':
                return EMPTY_DF
            elif financial_data_tmp.empty:
                return dataframe_default
            else:
                financial_data = financial_data_tmp
                if financial_data.empty:
                    return dataframe_default
                else:
                    financial_data.index = financial_data['secu_code'].tolist()
                    dataframe_default.update(financial_data_tmp)
                    financial_data = dataframe_default.replace('--', str(numpy.nan))
                    for field in financial_data.columns:
                        if field not in list_base:
                            financial_data[field] = financial_data[field].astype('float64').round(2)
                    financial_data.index.name = 'secu_code'
                    return financial_data
            return None
        except Exception as x:
            system_log.error(get_traceback_message())
            raise x
    def get_fundamentals(self, security, table, fields=None, date=None, start_year=None, end_year=None, report_types=None, date_type=None, merge_type=None):
        """
        璐㈠姟鏁版嵁鑾峰彇鎺ュ彛锛氬寘鎷笁澶ц储鎶ャ€佸叚澶ф垚闀挎寚鏍囥€佽偂鏈俊鎭€佷及鍊兼暟鎹?
        :param security锛氳偂绁ㄤ唬鐮侊紝str/list锛岄潪绌?
        :param table锛氳〃鍚?
        :param fields锛氳幏鍙栧瓧娈碉紝str/list锛岄潪绌?
        :param date锛氭棩鏈?
        :param start_year锛氬紑濮嬪勾浠?
        :param end_year锛氭埅姝㈠勾浠?
        :param report_types锛氬搴?
        :param date_type锛氭槸鍚﹀彲浠ヤ负鏈潵鏁版嵁
        :param merge_type锛氭洿鏀瑰墠/鏇存敼鍚庣殑鏁版嵁
        :return锛欴ataFrame/Panel绫诲瀷
        """
        if isinstance(security, str):
            security = [security]
        security = [s.replace('XSHG', 'SS').replace('XSHE', 'SZ') for s in security]
        if table in const.FINANCIAL_STATEMENTS + const.GROWTH_FACTORS:
            return self.get_financial_and_growth_factors(security=security, table=table, date=date, start_year=start_year, end_year=end_year, report_types=report_types, fields=fields, date_type=date_type, merge_type=merge_type)
        elif table == 'valuation':
            if not (start_year is None and end_year is None and report_types is None and date_type is None) or merge_type is not None:
                return EMPTY_DF
            else:
                return self.get_valuation(security=security, table=table, fields=fields, date=date)
        else:
            system_log.error('鏌ヨ鏁版嵁鎶ラ敊锛岄敊璇師鍥狅細琛ㄥ悕绉?s涓嶆敮鎸? % table)
            return EMPTY_DF

