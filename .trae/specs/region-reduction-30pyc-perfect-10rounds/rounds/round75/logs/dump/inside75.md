# R75 diag1 · 9 个 inside-try 单元行级对照（dump/inside75.md）

口径：原 pyc 异常表 `dis._parse_exception_table`；产品侧 = OK.py 重编译 code 的异常表 + `ast.Try` 行区间；行号取 `co_lines()`；`lineA/lineB` 取 `center/fam75.json` 首分歧行。

## fly/data/quote.pyc | <module>.Quote.run_tick_socket

- family=F-PAD verdict=Different control flow lenA=308 lenB=308 lineA=2156 lineB=1431
- firstA=`22 POP_JUMP_FORWARD_IF_FALSE to 158`  firstB=`22 POP_JUMP_FORWARD_IF_FALSE to 364`
- **orig ET**: entries=13 distinct_targets=6 nest=1  byte_len=81
  - [L2157-L2160 -> handler L2195 d0]; [L2162-L2162 -> handler L2163 d0]; [L2162-L2162 -> handler L2195 d0]; [L2163-L2163 -> handler L2172 d1]; [L2164-L2169 -> handler L2163 d1]; [L2170-L2170 -> handler L2195 d0]; [L2163-L2163 -> handler L2172 d1]; [L2172-L2175 -> handler L2195 d0]; [L2177-L2194 -> handler L2195 d0]; [L2195-L2198 -> handler L2208 d1]; [L2199-L2199 -> handler L2208 d1]; [L2200-L2207 -> handler L2199 d1]; [L2199-L2199 -> handler L2208 d1]
- **prod ET**: entries=12 distinct_targets=6 nest=1  byte_len=74  bytes_equal=False
  - [L1432-L1433 -> handler L1467 d0]; [L1435-L1435 -> handler L1436 d0]; [L1435-L1435 -> handler L1467 d0]; [L1436-L1436 -> handler L1444 d1]; [L1437-L1442 -> handler L1436 d1]; [L1443-L1443 -> handler L1467 d0]; [L1436-L1436 -> handler L1444 d1]; [L1444-L1465 -> handler L1467 d0]; [L1467-L1470 -> handler L1480 d1]; [L1471-L1471 -> handler L1480 d1]; [L1472-L1479 -> handler L1471 d1]; [L1471-L1471 -> handler L1480 d1]
- **prod ast.Try**: n=2 nest_max=2
  - Try L1431-L1479 depth=1 body=L(1432, 1433) handlers=[(1467, 1470, 'zmq.error.Again'), (1471, 1479, 'BaseException')] orelse=None final=None
  - Try L1434-L1443 depth=2 body=L(1435, 1435) handlers=[(1436, 1443, 'BaseException')] orelse=None final=None
- **product lines around lineB=1431**:
     1428     def run_tick_socket(self, socket, deques, dataDict, userLock, flag):
     1429         imagedata = dataDict['imagedata']
     1430         panelt = None
  >> 1431         try:
     1432             message = socket.recv()
     1433             if message:
     1434                 try:
     1435                     message = eval(message.decode())

## IQCommon/util/trade_info_utils.pyc | <module>.trade_operation

- family=F-ABSORB verdict=Different control flow lenA=303 lenB=303 lineA=288 lineB=133
- firstA=`186 POP_JUMP_FORWARD_IF_FALSE to 324`  firstB=`186 POP_JUMP_FORWARD_IF_FALSE to 334`
- **orig ET**: entries=18 distinct_targets=6 nest=1  byte_len=109
  - [L296-L297 -> handler L338 d0]; [L297-L329 -> handler L297 d1]; [L329-L330 -> handler L329 d2]; [L329-L329 -> handler L297 d1]; [L329-L329 -> handler L329 d4]; [L329-L329 -> handler L297 d1]; [L329-L329 -> handler L329 d4]; [L329-L331 -> handler L297 d1]; [L297-L297 -> handler L338 d0]; [L333-L334 -> handler L297 d1]; [L297-L297 -> handler L338 d0]; [L297-L297 -> handler L297 d3]; [L297-L297 -> handler L338 d0]; [L297-L297 -> handler L297 d3]; [L297-L297 -> handler L338 d0]; [L336-L336 -> handler L338 d0]; [L338-L339 -> handler L338 d1]; [L338-L338 -> handler L338 d1]
- **prod ET**: entries=18 distinct_targets=6 nest=1  byte_len=109  bytes_equal=True
  - [L141-L142 -> handler L182 d0]; [L142-L173 -> handler L142 d1]; [L173-L174 -> handler L173 d2]; [L173-L173 -> handler L142 d1]; [L173-L173 -> handler L173 d4]; [L173-L173 -> handler L142 d1]; [L173-L173 -> handler L173 d4]; [L173-L175 -> handler L142 d1]; [L142-L142 -> handler L182 d0]; [L176-L177 -> handler L142 d1]; [L142-L142 -> handler L182 d0]; [L142-L142 -> handler L142 d3]; [L142-L142 -> handler L182 d0]; [L142-L142 -> handler L142 d3]; [L142-L142 -> handler L182 d0]; [L180-L180 -> handler L182 d0]; [L182-L183 -> handler L182 d1]; [L182-L182 -> handler L182 d1]
- **prod ast.Try**: n=1 nest_max=1
  - Try L140-L184 depth=1 body=L(141, 141) handlers=[(182, 184, 'BaseException')] orelse=None final=None
- **product lines around lineB=133**:
      130     """
      131     trade_list_file = os.path.join(TRADE_DIR_PATH, user_id, SIM_TRADING_LIST_FILE)
      132     delete_trade_list_file = os.path.join(TRADE_DIR_PATH, user_id, DELETE_SIM_TRADING_LIST_FILE)
  >>  133     if isinstance(trade_id, str):
      134         trade_id_list = [trade_id]
      135     elif isinstance(trade_id, list):
      136         trade_id_list = trade_id
      137     else:

## IQData/plugins/plugin_system_realquote/real_quote.pyc | <module>.RealQuoteData.get_real_minute_kline

- family=F-ABSORB verdict=Different control flow lenA=250 lenB=253 lineA=584 lineB=370
- firstA=`28 POP_JUMP_FORWARD_IF_FALSE to 116`  firstB=`28 POP_JUMP_FORWARD_IF_FALSE to 390`
- **orig ET**: entries=7 distinct_targets=3 nest=1  byte_len=44
  - [L586-L593 -> handler L627 d0]; [L595-L602 -> handler L627 d0]; [L605-L626 -> handler L627 d0]; [L627-L627 -> handler L627 d1]; [L628-L629 -> handler L627 d1]; [L629-L629 -> handler L627 d1]; [L627-L627 -> handler L627 d1]
- **prod ET**: entries=8 distinct_targets=3 nest=1  byte_len=50  bytes_equal=False
  - [L372-L380 -> handler L408 d0]; [L382-L400 -> handler L408 d0]; [L401-L401 -> handler L408 d0]; [L403-L407 -> handler L408 d0]; [L408-L408 -> handler L408 d1]; [L409-L410 -> handler L408 d1]; [L410-L410 -> handler L408 d1]; [L408-L408 -> handler L408 d1]
- **prod ast.Try**: n=1 nest_max=1
  - Try L371-L410 depth=1 body=L(372, 372) handlers=[(408, 410, 'Exception')] orelse=None final=None
- **product lines around lineB=370**:
      367             system_log.debug(get_traceback_message())
      368         return EMPTY_DAY_BAR_NP_ARRAY
      369     def get_real_minute_kline(self, symbol, include, fq=None, ex_info=None, frequency_int=1):
  >>  370         symbol = symbol.replace('.XSHE', '.SZ').replace('.XSHG', '.SS')
      371         try:
      372             if self.cache == 1:
      373                 symbol = symbol.replace('.XSHE', '.SZ').replace('.XSHG', '.SS')
      374                 redata = []

## IQCommon/data/finance.pyc | <module>.get_fields

- family=F-ABSORB verdict=Different control flow lenA=157 lenB=157 lineA=655 lineB=432
- firstA=`36 JUMP_FORWARD to 90`  firstB=`36 JUMP_FORWARD to 254`
- **orig ET**: entries=8 distinct_targets=3 nest=1  byte_len=49
  - [L652-L660 -> handler L687 d0]; [L662-L681 -> handler L687 d0]; [L683-L684 -> handler L687 d0]; [L686-L686 -> handler L687 d0]; [L687-L687 -> handler L687 d1]; [L688-L689 -> handler L687 d1]; [L689-L689 -> handler L687 d1]; [L687-L687 -> handler L687 d1]
- **prod ET**: entries=8 distinct_targets=3 nest=1  byte_len=49  bytes_equal=False
  - [L430-L435 -> handler L458 d0]; [L437-L454 -> handler L458 d0]; [L455-L456 -> handler L458 d0]; [L457-L457 -> handler L458 d0]; [L458-L458 -> handler L458 d1]; [L459-L460 -> handler L458 d1]; [L460-L460 -> handler L458 d1]; [L458-L458 -> handler L458 d1]
- **prod ast.Try**: n=1 nest_max=1
  - Try L429-L460 depth=1 body=L(430, 457) handlers=[(458, 460, 'BaseException')] orelse=None final=None
- **product lines around lineB=432**:
      429     try:
      430         if fields is None:
      431             if table == 'valuation':
  >>  432                 error_msg, financial_data_tmp = get_finance_open_api_data(security=str(['600570.SS']), table=table, date='20180511')
      433             elif table in const.PIT_FINANCIAL_STATEMENTS_INFO:
      434                 financial_data_tmp = const.PIT_FINANCIAL_STATEMENTS_INFO[table]
      435                 return financial_data_tmp
      436             else:

## IQCommon/util/cgroup_utils.pyc | <module>.set_cgroup_config

- family=F-ABSORB verdict=Different control flow lenA=540 lenB=541 lineA=75 lineB=34
- firstA=`834 POP_JUMP_FORWARD_IF_FALSE to 1024`  firstB=`834 POP_JUMP_FORWARD_IF_FALSE to 1026`
- **orig ET**: entries=4 distinct_targets=2 nest=1  byte_len=23
  - [L51-L54 -> handler L176 d0]; [L58-L174 -> handler L176 d0]; [L176-L177 -> handler L176 d1]; [L176-L176 -> handler L176 d1]
- **prod ET**: entries=5 distinct_targets=2 nest=1  byte_len=29  bytes_equal=False
  - [L20-L22 -> handler L96 d0]; [L24-L93 -> handler L96 d0]; [L95-L95 -> handler L96 d0]; [L96-L97 -> handler L96 d1]; [L96-L96 -> handler L96 d1]
- **prod ast.Try**: n=1 nest_max=1
  - Try L19-L98 depth=1 body=L(20, 81) handlers=[(96, 98, 'BaseException')] orelse=None final=None
- **product lines around lineB=34**:
       31         else:
       32             delete_cgroup_config(user_id, 'backtest_cpu')
       33         if BACKTEST_MEMORY_SWITCH == 1:
  >>   34             if not os.path.exists('/sys/fs/cgroup/memory/docker/{}/backtest'.format(container_id)):
       35                 os.system('sudo cgcreate -t root:root -a root:root -g memory:/docker/{}/backtest'.format(container_id))
       36                 os.system('sudo chown -R fly:fly /sys/fs/cgroup/memory/docker/{}/backtest'.format(container_id))
       37                 os.system('sudo chmod -R 777 /sys/fs/cgroup/memory/docker/{}/backtest'.format(container_id))
       38             os.system('sudo echo {} > /sys/fs/cgroup/memory/docker/{}/backtest/memory.limit_in_bytes'.format(int(BACKTEST_MEMORY_SIZE * 1024 * 1024 * 1024), con

## IQCommon/util/email_utils.pyc | <module>.send_email

- family=F-ABSORB verdict=Different control flow lenA=193 lenB=195 lineA=57 lineB=38
- firstA=`44 POP_JUMP_FORWARD_IF_FALSE to 206`  firstB=`44 POP_JUMP_FORWARD_IF_FALSE to 332`
- **orig ET**: entries=5 distinct_targets=2 nest=1  byte_len=32
  - [L56-L62 -> handler L83 d0]; [L63-L67 -> handler L83 d0]; [L68-L82 -> handler L83 d0]; [L83-L87 -> handler L83 d1]; [L83-L83 -> handler L83 d1]
- **prod ET**: entries=5 distinct_targets=2 nest=1  byte_len=32  bytes_equal=False
  - [L37-L43 -> handler L64 d0]; [L45-L48 -> handler L64 d0]; [L49-L63 -> handler L64 d0]; [L64-L68 -> handler L64 d1]; [L64-L64 -> handler L64 d1]
- **prod ast.Try**: n=1 nest_max=1
  - Try L36-L68 depth=1 body=L(37, 40) handlers=[(64, 68, 'BaseException')] orelse=None final=None
- **product lines around lineB=38**:
       35     return_info = {'error_no': -1, 'error_info': ''}
       36     try:
       37         msg = MIMEMultipart()
  >>   38         body = MIMEText(email_info, 'plain', 'utf-8')
       39         msg.attach(body)
       40         if attachment_path != '':
       41             if SEND_EMAIL_FILE_PERMISSION == '1':
       42                 return_info['error_info'] = '系统配置不允许发送邮件附件, 本次发送过程附件将不会被发送'

## IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc | <module>.Strategy.tick_worker_thread

- family=F-ABSORB verdict=Different control flow lenA=267 lenB=267 lineA=311 lineB=223
- firstA=`122 POP_JUMP_FORWARD_IF_TRUE to 156`  firstB=`122 POP_JUMP_FORWARD_IF_TRUE to 282`
- **orig ET**: entries=3 distinct_targets=2 nest=1  byte_len=18
  - [L308-L308 -> handler L345 d0]; [L345-L346 -> handler L345 d1]; [L345-L345 -> handler L345 d1]
- **prod ET**: entries=3 distinct_targets=2 nest=1  byte_len=18  bytes_equal=True
  - [L222-L222 -> handler L249 d0]; [L249-L250 -> handler L249 d1]; [L249-L249 -> handler L249 d1]
- **prod ast.Try**: n=1 nest_max=1
  - Try L221-L251 depth=1 body=L(222, 222) handlers=[(249, 251, 'Exception')] orelse=None final=None
- **product lines around lineB=223**:
      220         accounts = self._engine.config.strategy.accounts
      221         try:
      222             while True:
  >>  223                 if not self._engine.data_proxy.is_trading_date(datetime.date.today()):
      224                     time.sleep(60)
      225                     continue
      226                 now = datetime.datetime.now()
      227                 dt_strf = now.strftime('%H:%M:%S')

## IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc | <module>.RealtimeEventSource.clock_worker

- family=F-ABSORB verdict=Different control flow lenA=1274 lenB=1281 lineA=189 lineB=100
- firstA=`1328 POP_JUMP_FORWARD_IF_FALSE to 2494`  firstB=`1328 POP_JUMP_FORWARD_IF_FALSE to 2476`
- **orig ET**: entries=24 distinct_targets=9 nest=1  byte_len=175
  - [L125-L434 -> handler L577 d0]; [L439-L439 -> handler L440 d0]; [L439-L439 -> handler L577 d0]; [L440-L441 -> handler L442 d1]; [L441-L441 -> handler L577 d0]; [L440-L440 -> handler L442 d1]; [L442-L476 -> handler L577 d0]; [L478-L489 -> handler L577 d0]; [L491-L492 -> handler L494 d1]; [L493-L493 -> handler L577 d0]; [L494-L497 -> handler L498 d2]; [L494-L494 -> handler L577 d0]; [L494-L494 -> handler L498 d2]; [L498-L501 -> handler L577 d0]; [L504-L504 -> handler L577 d0]; [L507-L507 -> handler L508 d0]; [L507-L507 -> handler L577 d0]; [L508-L509 -> handler L511 d1]; [L509-L509 -> handler L577 d0]; [L508-L508 -> handler L511 d1]; [L511-L399 -> handler L577 d0]; [L577-L577 -> handler L577 d1]; [L578-L578 -> handler L577 d1]; [L577-L577 -> handler L577 d1]
- **prod ET**: entries=24 distinct_targets=9 nest=1  byte_len=177  bytes_equal=False
  - [L59-L237 -> handler L317 d0]; [L239-L239 -> handler L241 d0]; [L240-L240 -> handler L317 d0]; [L241-L242 -> handler L245 d1]; [L243-L243 -> handler L317 d0]; [L241-L241 -> handler L245 d1]; [L245-L258 -> handler L317 d0]; [L260-L264 -> handler L317 d0]; [L266-L267 -> handler L268 d1]; [L273-L273 -> handler L317 d0]; [L268-L271 -> handler L274 d2]; [L268-L268 -> handler L317 d0]; [L268-L268 -> handler L274 d2]; [L274-L292 -> handler L317 d0]; [L294-L294 -> handler L317 d0]; [L296-L296 -> handler L297 d0]; [L296-L296 -> handler L317 d0]; [L297-L298 -> handler L299 d1]; [L298-L298 -> handler L317 d0]; [L297-L297 -> handler L299 d1]; [L299-L315 -> handler L317 d0]; [L317-L317 -> handler L317 d1]; [L318-L318 -> handler L317 d1]; [L317-L317 -> handler L317 d1]
- **prod ast.Try**: n=4 nest_max=2
  - Try L58-L319 depth=1 body=L(59, 216) handlers=[(317, 319, 'Exception')] orelse=None final=None
  - Try L238-L243 depth=2 body=L(239, 240) handlers=[(241, 243, 'AttributeError')] orelse=None final=None
  - Try L265-L273 depth=2 body=L(266, 267) handlers=[(268, 271, 'BaseException')] orelse=(273, 273) final=None
  - Try L295-L298 depth=2 body=L(296, 296) handlers=[(297, 298, 'AttributeError')] orelse=None final=None
- **product lines around lineB=100**:
       97                 hks_after_trading = HKS_AFTER_TRADING_TIME
       98                 hks_am_open = HKS_AM_OPEN
       99                 hks_am_close = HKS_AM_CLOSE
  >>  100                 hks_pm_open = HKS_PM_OPEN
      101                 hks_pm_close = HKS_PM_CLOSE
      102                 hks_pm_over = HKS_PM_OVER
      103             else:
      104                 hks_before_trading = hks_schedule.get('before_trading_time', BEFORE_TRADING_TIME)

## fly/common/flytools.pyc | <module>.ProcessWrite.modify_batcktes_info

- family=F-PAD verdict=Different control flow lenA=216 lenB=216 lineA=1133 lineB=796
- firstA=`324 POP_JUMP_FORWARD_IF_FALSE to 380`  firstB=`324 POP_JUMP_FORWARD_IF_FALSE to 404`
- **orig ET**: entries=22 distinct_targets=9 nest=1  byte_len=133
  - [L1131-L1131 -> handler L1143 d0]; [L1131-L1133 -> handler L1131 d1]; [L1133-L1133 -> handler L1133 d2]; [L1133-L1141 -> handler L1133 d3]; [L1133-L1133 -> handler L1133 d2]; [L1133-L1133 -> handler L1133 d5]; [L1133-L1133 -> handler L1133 d2]; [L1133-L1133 -> handler L1133 d5]; [L1133-L1133 -> handler L1133 d2]; [L1133-L1133 -> handler L1131 d1]; [L1133-L1133 -> handler L1133 d4]; [L1133-L1133 -> handler L1131 d1]; [L1133-L1133 -> handler L1133 d4]; [L1133-L1142 -> handler L1131 d1]; [L1131-L1131 -> handler L1143 d0]; [L1131-L1131 -> handler L1131 d3]; [L1131-L1131 -> handler L1143 d0]; [L1131-L1131 -> handler L1131 d3]; [L1131-L1131 -> handler L1143 d0]; [L1143-L1143 -> handler L1143 d1]; [L1144-L1148 -> handler L1143 d1]; [L1143-L1143 -> handler L1143 d1]
- **prod ET**: entries=22 distinct_targets=9 nest=1  byte_len=133  bytes_equal=False
  - [L793-L793 -> handler L807 d0]; [L793-L795 -> handler L793 d1]; [L795-L796 -> handler L795 d2]; [L796-L804 -> handler L796 d3]; [L796-L796 -> handler L795 d2]; [L796-L796 -> handler L796 d5]; [L796-L796 -> handler L795 d2]; [L796-L796 -> handler L796 d5]; [L796-L796 -> handler L795 d2]; [L795-L795 -> handler L793 d1]; [L795-L795 -> handler L795 d4]; [L795-L795 -> handler L793 d1]; [L795-L795 -> handler L795 d4]; [L795-L806 -> handler L793 d1]; [L793-L793 -> handler L807 d0]; [L793-L793 -> handler L793 d3]; [L793-L793 -> handler L807 d0]; [L793-L793 -> handler L793 d3]; [L793-L793 -> handler L807 d0]; [L807-L807 -> handler L807 d1]; [L808-L812 -> handler L807 d1]; [L807-L807 -> handler L807 d1]
- **prod ast.Try**: n=1 nest_max=1
  - Try L792-L818 depth=1 body=L(793, 793) handlers=[(807, 818, 'Exception')] orelse=None final=None
- **product lines around lineB=796**:
      793             with FileLock(user_id, filename, os.path.join(BACKTEST_DIR_PATH, f'{user_id!s}.{filename!s}.lock')):
      794                 backtest_tmp_path = os.path.join(os.path.split(file_path_name)[0], 'backtest_tmp.csv')
      795                 with open(file_path_name, 'r', newline='') as fp:
  >>  796                     with open(backtest_tmp_path, 'w', newline='') as fq:
      797                         csv_reader = csv.reader(fp)
      798                         csv_writer = csv.writer(fq)
      799                         for _row in csv_reader:
      800                             if _row[0] == backtestid:

## 10. 汇总与逐单元判决（本批 9 个）

| file | unit | family | ET orig→prod | bytes_equal | prod ast.Try n/nest | lineB 在 try 内 | lineA/lineB | 判决 |
|---|---|---|---|---|---|---|---|---|
| fly/data/quote.pyc | run_tick_socket | F-PAD | 13→12 | False | 2/2 | True | 2156/1431 | 异常表条目数 13→12 ⇒ try 边界/层次有差，try 结构是差异来源之一 |
| IQCommon/util/trade_info_utils.pyc | trade_operation | F-ABSORB | 18→18 | True | 1/1 | False | 288/133 | 异常表字节相同 ⇒ 根因不在 try，try 是**载体** |
| IQData/plugins/plugin_system_realquote/real_quote.pyc | get_real_minute_kline | F-ABSORB | 7→8 | False | 1/1 | False | 584/370 | 异常表条目数 7→8 ⇒ try 边界/层次有差，try 结构是差异来源之一 |
| IQCommon/data/finance.pyc | get_fields | F-ABSORB | 8→8 | False | 1/1 | True | 655/432 | 条目数相同(=8)但字节不同 ⇒ handler 落点/depth 有差，try 结构是差异来源之一 |
| IQCommon/util/cgroup_utils.pyc | set_cgroup_config | F-ABSORB | 4→5 | False | 1/1 | True | 75/34 | 异常表条目数 4→5 ⇒ try 边界/层次有差，try 结构是差异来源之一 |
| IQCommon/util/email_utils.pyc | send_email | F-ABSORB | 5→5 | False | 1/1 | True | 57/38 | 条目数相同(=5)但字节不同 ⇒ handler 落点/depth 有差，try 结构是差异来源之一 |
| IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc | tick_worker_thread | F-ABSORB | 3→3 | True | 1/1 | True | 311/223 | 异常表字节相同 ⇒ 根因不在 try，try 是**载体** |
| IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc | clock_worker | F-ABSORB | 24→24 | False | 4/2 | True | 189/100 | 条目数相同(=24)但字节不同 ⇒ handler 落点/depth 有差，try 结构是差异来源之一 |
| fly/common/flytools.pyc | modify_batcktes_info | F-PAD | 22→22 | False | 1/1 | True | 1133/796 | 条目数相同(=22)但字节不同 ⇒ handler 落点/depth 有差，try 结构是差异来源之一 |

- 异常表字节相同的 2/9：**try 是载体**（根因在 try 内的区域归约），这些单元不必动 try 生成路径。
- 异常表有差的 7/9：条目数差 3 个、仅字节差 4 个 → 需在 fix 批按 `lineB` 落点逐条对照 handler 起止行。
- `lineB` 落在产品 `ast.Try` 行区间内的 7/9（首分歧即产品 try 的行上）；其余单元首分歧在 try 之外的语句行。

