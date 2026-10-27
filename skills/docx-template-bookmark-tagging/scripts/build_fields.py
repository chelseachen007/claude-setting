# -*- coding: utf-8 -*-
"""
生成「审查意见类模板打标预处理.json」—— 打标流程的输入清单。

每条 field 描述一个待填充点：
  slot=cell  -> 表格单元格，按 (table,row,cell) 定位（row/cell 为 tc 序号）
  slot=para  -> 正文段落，after 给出「插在哪个段落之后」（或 after_table 表示插在某表之后）
"""
import json, os

OUT = '/Users/chenjie/Documents/work/AI/智能模板/template 2/审查意见类模板打标预处理.json'

SEC1 = '一、申报方案'
SEC2 = '二、发行人、反担保人股权结构及经营情况'
SEC3 = '三、发行人、反担保人主营业务模式'
SEC4 = '四、合规性审查'
SEC5 = '五、本笔业务合作模式'
SEC6 = '六、项目风险提示'
SEC7 = '七、结论'
SEC8 = '附件'

# ---------- 表格锚点 ----------
# ⚠️ shape 是**纯描述性元数据**（无脚本读取），且它和 render 是两回事：
#    shape 描述表格长什么样（keyvalue / grid），render 才是喂给渲染引擎的功能开关。
#    修「静态标签被抹掉」只能动 render，**不要顺手改 shape** —— 改了会让 json 结构和
#    之前不一致（用户明确要求「不要改数据结构」）。T2/T5/T6/T7/T8 保持初始的 grid。
TABLES = [
    dict(index=1, code='applyPlan',      desc='申报方案',            shape='keyvalue', render='2', section=SEC1, rows=21, cols=2),
    dict(index=2, code='equityStructure',desc='发行人、反担保人股权结构', shape='grid', render='2', section=SEC2, rows=4,  cols=6),
    dict(index=3, code='issuerRevenue',  desc='发行人各业务板块收入构成', shape='grid',   render=None, section=SEC3, rows=8,  cols=10),
    dict(index=4, code='cgRevenue',      desc='反担保人各业务板块收入构成', shape='grid', render=None, section=SEC3, rows=8,  cols=10),
    dict(index=5, code='complianceReview',desc='合规性审查',          shape='grid', render='2', section=SEC4, rows=7,  cols=4),
    dict(index=6, code='fundProject',    desc='募投项目明细',         shape='grid', render='2', section=SEC6, rows=7,  cols=3),
    dict(index=7, code='debtRepayPlan',  desc='还本付息计划测算',      shape='grid', render='2', section=SEC6, rows=4,  cols=6),
    dict(index=8, code='regionPlatform', desc='区域主要投融资平台对比', shape='grid', render='2', section=SEC6, rows=8,  cols=9),
]

# ---------- 表锚点空行带来的行号偏移 ----------
# clean_template.py 会在 ANCHOR_BEFORE[t] 行之前插一个空锚点行，
# 所以该行及其后的所有行号都要 +1。下面写的 row 一律是「插入前」的行号。
ANCHOR_BEFORE = {1: 0, 2: 1, 3: 2, 4: 2, 5: 1, 6: 1, 7: 1, 8: 2}


def R(t, r):
    """把「插入前的行号」换算成「打标签后文档里的行号」"""
    return r + (1 if r >= ANCHOR_BEFORE[t] else 0)


# ---------- 字段清单 ----------
# (slot, loc, code, desc, field_type, category, hint_doc_types, sample)
F = []
def cell(t, r, c, code, desc, ft, cat, hints, sample, note=None):
    F.append(dict(slot='cell', table=t, row=R(t, r), cell=c, code=code, desc=desc,
                  field_type=ft, category=cat, hint_doc_types=hints,
                  sample=sample, **({'note': note} if note else {})))
def para(after, code, desc, cat, hints, sample, after_table=None):
    # hints 允许传 ['x'] 或 [['x'],['y']]，统一展平
    flat = []
    for h in hints:
        flat.extend(h if isinstance(h, list) else [h])
    d = dict(slot='para', code=code, desc=desc, field_type='narrative',
             category=cat, hint_doc_types=flat, sample=sample)
    if after_table: d['after_table'] = after_table
    else: d['after'] = after
    F.append(d)

SH = ['担保文件']; CW = ['公司章程']; BL = ['营业执照']; FS = ['财务报表']
CR = ['征信报告']; PD = ['企业简介与项目说明']; OT = ['其他']

# ===== 表1 申报方案（键值表）=====
cell(1,0,1,'applyUnit','申报单位','structured','信用与担保类',SH,'四川省金玉融资担保有限公司（以下简称“金玉担保”）')
cell(1,1,1,'issuerName','企业名称','structured','工商信息类',BL,'XX城投集团有限公司（以下简称“发行人”或“XX城投”）')
cell(1,2,1,'issuerRating','主体信用评级','structured','信用与担保类',CR,'AA+（大公国际）')
cell(1,3,1,'issuerIndustry','所属行业','structured','工商信息类',BL,'水利、环境和公共设施管理业')
cell(1,4,1,'applyBusinessType','申请业务类型','structured','信用与担保类',SH,'人民币境外债')
cell(1,5,1,'applyBusinessStructure','申请业务结构','structured','信用与担保类',SH,'由上海银行出具备用信用证对债券进行担保，金玉担保为备证提供反担保')
cell(1,6,1,'applyGuaranteeAmount','申请担保金额','structured','信用与担保类',SH,'不超过5亿元人民币（含）')
cell(1,7,1,'approvalDeptBondType','审批部门/发行债券种类','structured','信用与担保类',SH,'发改委/人民币境外债')
cell(1,8,1,'underwriter','承销商','structured','经营与合同类',OT,'东海国际金融控股有限公司')
cell(1,9,1,'issueChannel','发行渠道','structured','信用与担保类',SH,'香港证券交易所或澳门证券交易所')
cell(1,10,1,'isInstallment','是否分期发行','structured','信用与担保类',SH,'否',
     note='勾选型：模板已保留“□是 / □否”选项框')
cell(1,11,1,'repaymentMethod','债券本息偿付方式','structured','信用与担保类',SH,'每半年付息，到期一次性还本（以最终募集说明书为准）')
cell(1,12,1,'repaymentSource','还款来源','structured','信用与担保类',SH,'募投项目现金流；2.公司自身经营收入、新增融资。')
cell(1,13,1,'fundPurpose','募集资金用途','structured','项目与背景类',PD,'发行人获批债券募集资金总额不超过等值人民币20亿元，拟用于公司项目建设和补充流动性资金。其中等值人民币16亿拟用于项目建设，等值人民币4亿元用于补充流动性资金。\n本期拟发行人民币计价债券5亿元，用于项目建设（以最终募集说明书为准）。')
cell(1,14,1,'creditAmountGuaranteeScope','授信金额及担保范围','structured','信用与担保类',SH,'金玉担保向备证开立行提供反担保。担保范围包括：债券持有人基于上述备用信用证而有权要求备证开立行支付的保函垫付金额、利息、违约金、保函费用等一切根据《保函授信合同》应由发行人支付的费用、备证开立行实现担保权利的费用，以及发行人给备证开立行造成的其他损失。代偿金额以人民币5亿元（含）为限额，即最高债权限额5亿元人民币。')
cell(1,15,1,'guaranteePeriod','担保期限','structured','信用与担保类',SH,'不超过3年（含），金玉担保与备证开立行签订的担保合同的债权确定期间/合同期限为不超过38个月（含）')
cell(1,16,1,'guaranteeFeeRate','担保费率/收取方式','structured','信用与担保类',SH,'担保费率不低于1.0%/年。债券发行成功后一次性收取三年担保费。')
cell(1,17,1,'riskControlMeasures','风控措施','structured','信用与担保类',SH,'法人保证：眉山天府新区投资集团有限公司AA+（以下简称“反担保人”或“眉山天投”）提供连带责任保证反担保。')
cell(1,18,1,'isComplyRiskOpinion','是否符合《…地方投融资平台公司债券增信业务产品（2023年版）的风险提示意见》','structured','信用与担保类',SH,
     '□符合                ☑不符合\n（集团对金玉的债券增信业务审批权授权未包含境外债这一品种）',
     note='勾选型：模板已保留“□符合 / □不符合”选项框，回填时只需置勾并补理由')
cell(1,19,1,'historyCooperation','历史合作情况','structured','信用与担保类',SH,'本次为新增，存量有金玉担保为发行人子公司XX发展投资集团有限公司8.5亿元公司债、及反担保人子公司眉山环天实业有限公司5.04亿元PPN提供了担保')

# ===== 表2 股权结构 =====
for r, pre, zh in ((1,'issuer','发行人'), (2,'counterGuarantor','反担保人')):
    cell(2,r,1,pre+'FullName','%s名称'%zh,'structured','工商信息类',BL,'XX城投集团有限公司' if r==1 else '眉山天府新区投资集团有限公司')
    cell(2,r,2,pre+'RegisteredCapital','%s注册/实缴资本金'%zh,'structured','工商信息类',BL,'40/40亿元' if r==1 else '50/50亿元')
    cell(2,r,3,pre+'EstablishDate','%s成立时间'%zh,'structured','工商信息类',BL,'2017.12' if r==1 else '2018.12')
    cell(2,r,4,pre+'Shareholders','%s股东'%zh,'structured','工商信息类',CW,'XX县国有资产和金融工作局' if r==1 else '眉山市国有资产监督管理委员会和四川省财政厅')
    cell(2,r,5,pre+'ActualController','%s实际控制人'%zh,'structured','工商信息类',CW,'XX县人民政府' if r==1 else '眉山市人民政府')

# ===== 表3 / 表4 业务板块收入构成（列定义挂在首个数据行 R2，行数动态）=====
years = [('1','2022年'), ('2','2021年'), ('3','2020年')]
for tno, pre, zh in ((3,'issuer','发行人'), (4,'cg','反担保人')):
    cell(tno,2,0,pre+'SegmentName','业务板块','structured','财务信息类',FS,'导线光缆销售')
    for k, yr in years:
        cell(tno,2,int(k)*3-2, pre+'SegmentRevenue'+k,'%s-收入'%yr,'structured','财务信息类',FS,'16.17')
        cell(tno,2,int(k)*3-1, pre+'SegmentRatio'+k,  '%s-占比'%yr,'structured','财务信息类',FS,'25.0%')
        cell(tno,2,int(k)*3,   pre+'SegmentGrossMargin'+k,'%s-毛利率'%yr,'structured','财务信息类',FS,'8.7%')

# ===== 表5 合规性审查（编号与审查依据固定，只填内容与结论）=====
comp_samples = [
    ('如认定为直融业务，发行人准入、区域准入、额度、费率、反担保措施符合，但对金玉担保的债券增信业务审批权授权未包含境外债这一品种','不符合，超过本级授权，须上报至董事会'),
    ('如认定为间融业务，则按照指引规定执行“用信期限不得超过2年，超过1年的一般应设立分期还款计划”，本笔业务授信期限3年','不符合'),
    ('金鼎集团所属公司对同一区域所有国有投融资类客户的全部用信余额不得超过该区域上年一般公共预算收入的100%和上年金鼎集团归母净资产40%的孰低值……存量用信余额折算后合计8.16亿元，加计本笔授信5亿元后为13.16亿元，未超过上述限额，但超过了集团归母净资产的20%。','未达到40%，应上报董事会'),
    ('经查询集团关联客户名单，发行人（AA+）与XX发展投资集团有限公司（AA）系集团关联客户，合计授信13.5亿元，担保责任余额按照60%计算为8.1亿元，超过金鼎集团归母净资产的10%，未超过金鼎集团归母净资产的15%。','属于集团关联客户，超过总经理权限，须报至董事会'),
    ('（1）本笔发债金额5亿元，发行主体信用评级AA+，担保责任余额按照60%计算为3亿元，同一被担保人的担保责任余额未超过金玉担保净资产的10%。（2）对同一被担保人及其关联方的融资担保责任余额不得超过其净资产的15%。','符合'),
]
for i, (c2, c3) in enumerate(comp_samples, start=1):
    cell(5,i,2,'complianceContent%d'%i,'%d-具体内容'%i,'narrative','分析说明类',PD,c2)
    cell(5,i,3,'complianceConclusion%d'%i,'%d-结论'%i,'narrative','分析说明类',PD,c3)

# ===== 表6 募投项目（列定义，行数动态）=====
cell(6,1,0,'fundProjectName','项目名称','structured','项目与背景类',PD,'XX县健康管理中心建设项目')
cell(6,1,1,'fundProjectTotalInvestment','投资总额（万元）','structured','项目与背景类',PD,'25,006.20')
cell(6,1,2,'fundProjectPlannedAmount','拟用款规模（万元）','structured','项目与背景类',PD,'20,000.00')
cell(6,5,1,'fundProjectTotalInvestmentSum','投资总额合计','structured','项目与背景类',PD,'203,981.20')
cell(6,5,2,'fundProjectPlannedAmountSum','拟用款规模合计','structured','项目与背景类',PD,'166,975.00')

# ===== 表7 还本付息计划 =====
for k, yr in (('1','2024'),('2','2025'),('3','2026'),('4','2027年及以后'),('5','合计')):
    cell(7,1,int(k),'debtRepayTotal'+k,'%s-合计（亿元）'%yr,'structured','财务信息类',FS,'99.97')
    cell(7,2,int(k),'debtRepayRatio'+k,'%s-占比'%yr,'structured','财务信息类',FS,'36.18%')

# ===== 表8 区域主要投融资平台对比（列定义）=====
cell(8,2,0,'regionPlatformNo','序号','structured','其他类',OT,'1')
cell(8,2,1,'regionPlatformName','主体','structured','工商信息类',BL,'XX城投集团有限公司（发行人）')
cell(8,2,2,'regionPlatformFunction','职能定位','structured','项目与背景类',PD,'主要负责XX县城市基础设施建设和土地开发整理、水务等业务')
cell(8,2,3,'regionPlatformRating','评级','structured','信用与担保类',CR,'AA+')
cell(8,2,4,'regionPlatformTotalAsset','总资产','structured','财务信息类',FS,'633.4')
cell(8,2,5,'regionPlatformDebtRatio','资产负债率','structured','财务信息类',FS,'42.63%')
for k, yr in (('1','2022'),('2','2021'),('3','2020')):
    cell(8,2,5+int(k),'regionPlatformInterestDebt'+k,'%s-有息负债'%yr,'structured','财务信息类',FS,'230.46')
for k, yr in (('1','2022'),('2','2021'),('3','2020')):
    cell(8,6,2+int(k),'regionPlatformSumInterestDebt'+k,'合计-%s-有息负债'%yr,'structured','财务信息类',FS,'478.46')

# ===== 段落型字段（narrative）=====
para('（一）发行人、反担保人股权结构及对外投资','equityHoldingDesc','发行人、反担保人股权结构说明','分析说明类',[CW,BL],
     '发行人—XX城投成立于2017年12月，截至目前其注册资本为40亿元，其股东为XX县国有资产和金融工作局，持股100%。反担保人眉山天府新区投资集团有限公司，注册资本为50亿元，股东为眉山市国有资产监督管理委员会和四川省财政厅，持股分别为97.92%和2.08%。')
para('（二）发行人对外投资情况','issuerOutboundInvestmentDesc','发行人对外投资情况说明','分析说明类',[CW,PD],
     '据调查显示，发行人XX城投前身为XX县黑龙潭阳光文化旅游发展有限责任公司。2022年XX县国资金融局/XX财政局陆续将大量砂石资源采矿经营权、XX县公共资源管理公司、XX发展投资集团有限公司100%股权划拨给发行人，重组完成后公司成为区域内总资产排名第二的城投公司。')
para('（一）发行人主营业务模式','issuerBusinessModelDesc','发行人主营业务模式说明','项目与背景类',[PD],
     '发行人“XX城投”作为XX县重要的城市基础设施建设投融资和土地开发整理主体，业务涵盖XX县城市基础建设、土地开发整理、水务、公交运营、导线光缆销售、显示屏销售等业务，收入结构较为多元。')
para('（二）反担保人主营业务模式','cgBusinessModelDesc','反担保人主营业务模式说明','项目与背景类',[PD],
     '反担保人“眉山天投”作为眉山天府新区最主要的片区开发和投融资主体（实际为XX的城投平台），主要承建政府交付的重大基础设施建设及民生任务。近年来收入的主要来源以委托代建业务、贸易销售业务、房地产销售业务为主，合计占比在70%以上。')
para(None,'complianceConclusionDesc','合规性审查结论','分析说明类',[PD],
     '本笔业务交易结构是由银行开立备用信用证对境外债进行担保，金玉担保为备证提供反担保……虽然从业务结构上看疑似间融担保，但从业务实质上来看，发行人仍是在债券市场进行直接融资，以直接融资担保来认定该业务的风险权重更为合理。\n综上所述，本笔业务超过金玉担保本级授权权限，同时属于集团关联客户且限额超过了董事会对总经理的授权权限，须由金鼎集团总经理签批后上报至金鼎集团董事会进行审批。',
     after_table=5)
para('（一）主承销商：','leadUnderwriterDesc','主承销商情况说明','项目与背景类',[PD],
     '主承销商东海国际金融控股有限公司（以下简称“东海金控”）成立于2015年8月，是东海证券股份有限公司的全资子公司，在香港证监会的管理下持有1、4、9号牌照。')
para('（二）备证开立行：','lguIssuingBankDesc','备证开立行情况说明','项目与背景类',[PD],
     '上海银行股份有限公司（以下简称“上海银行”）成立于1995年12月29日，总部位于上海，是上海证券交易所主板上市公司，股票代码601229。')
para('（三）境外债（包含中资美元债和点心债，及以人民币、欧元、日元等其他货币计价的债券）大致情况','offshoreBondMarketDesc','境外债市场情况分析','分析说明类',[PD],
     '中资美元债存量规模较大的行业包括房地产、银行、城投、金融服务和互联网媒体行业……城投美元债已成为中资美元债的主要品种之一。当前美债利率仍处在一个较高水平……建议申报单位优先关注大成都区域或地级市市级的城投平台。')
para(None,'fundUseRiskDesc','募集资金用途及募投项目风险分析','分析说明类',[PD],
     '再根据申报单位提供的《办理外债审核登记的补充材料》，4个募投项目均已动工建设……上述收入可覆盖债券利息，却不能覆盖债券本金，本笔申请发债的还本付息将主要依靠发行人的再融资来进行置换。',
     after_table=6)
para('（二）发行人经营与财务风险分析','issuerOperationFinancialRiskDesc','发行人经营与财务风险分析','分析说明类',[FS,PD],
     '1.由于发行人未在公开市场上发行过债券，2023年度财报还未出具，这里仅以2022年末经审计的财报数据进行分析……土地转让业务受到区域房地产和土地市场行情影响，存在较大的不确定性。\n2.发行人在建的代建和自营项目较多且未来投资金额较大，面临较大的资本支出压力。\n3.截至到2023年9月末，发行人总资产669.19亿元、总负债301.78亿元、营收49.62亿元、净利润2.23亿元，资产流动性较弱。\n4.发行人经营性净现金流持续为净流出状态，缺乏对债务和利息的保障能力。')
para('（三）发行人债务风险分析','issuerDebtRiskDesc','发行人债务风险分析','分析说明类',[FS,CR],
     '1.发行人总负债规模持续大幅增长，但资产负债率与同行业相比尚处于较低水平（2022年42.63%、2023年9月末45.1%），负债以有息债务为主，货币资金对短期有息负债的覆盖率仅为0.31，短期偿债压力较大。\n截至到2023年9月末，发行人有息负债余额至少达276.29亿元……发行人24-27年有息债务分别需偿付99.97亿元、40.74亿元、33.39亿元及102.19亿元。')
para(None,'issuerDebtRiskExtraDesc','发行人偿债压力与征信情况分析','分析说明类',[CR,FS],
     '考虑到发行人营业收入支撑能力有限，综合融资成本相对较高且当前政策的限制和管控，2024年债务集中偿还压力最大，不排除出现流动性风险的可能。\n根据申报单位提供2023.11.30人行企业征信报告显示：发行人未结清贷款5笔，贷款余额5.1亿元……征信状况良好。\n综合考虑区域财力情况，整体来看信用资质偏弱。',
     after_table=7)
para('（四）反担保措施风险分析','cgRiskDesc','反担保措施风险分析','分析说明类',[FS,CR],
     '反担保人“眉山天投”近年来资产和债务规模持续增长（截止到2023年9月末总资产790.82亿元、总负债481.98亿元、营收71.06亿元、净利润2.61亿元），资产可变现能力和流动性较弱。\n根据申报单位提供2023.12.18人行企业征信报告显示：反担保人未结清贷款50笔，贷款余额82.17亿元，信用记录良好。')
para('1.从经营方面来看','cgOperationRiskDesc','反担保人经营风险分析','分析说明类',[PD],
     '①基建板块，22年末公司在建代建项目总投资213.56亿元，累计完成投资85.59亿元，尚需投资130.53亿元，未来资金压力较大。\n②水务板块，售水覆盖区域包括XX视高区域和清水镇、兴盛乡，收入增长明显。\n③房地产板块，截至22年末在建房地产项目总投资合计331.13亿元，尚需投资体量较大。\n④其他板块收入占比较小，但仍需关注基金投资、小额贷款、融资租赁等金融类业务的款项回收风险。')
para('2.从财务方面来看','cgFinancialRiskDesc','反担保人财务风险分析','分析说明类',[FS],
     '截至2022年末，眉山天投总资产为673.66亿，增长较快主要由债务驱动，公益性资产占比约为62%，城投成色一般。同期末资产负债率为59.15%，有息债务规模为235.14亿，短债压力较大。\n综合来看，眉山天投职能定位有所提升，但杠杆水平快速提升，整体资质一般。')
para('（五）发行人所在区域经济和财政风险分析','regionEconomyFiscalRiskDesc','发行人所在区域经济和财政风险分析','分析说明类',[PD,FS],
     '1.眉山市紧邻成都南部，受益于成德眉资同城化战略和天府新区整体规划，土地出让收入激增，财政对土地出让收入依赖极高……整体债务率不高，但平台较多，融资略显无序。\n2.发行人所在XX县2022年GDP排名位列眉山市6个区县第2位……地方综合财力持续下降。\n3.经初步测算，2022年XX县公开可查的政府和城投有息债务规模至少达到658.4亿元，未来3年区域整体偿债压力明显。')
para('七、结论','conclusionDesc','审查结论','分析说明类',[PD],
     '在本项目审查过程中我们注意到该笔担保业务存在发行人主体资质较弱（属于资产整合后的区县级平台，且未公开发行过债券），反担保人主体资质一般。同时，两者的资产流动性和自身还款能力较弱、短期偿债压力和所属区域整体债务负担明显，以及修建项目自身还款来源不足在内的潜在不利因素。')
para('（一）前提条件','preconditionDesc','风控措施-前提条件','分析说明类',[PD],
     '建议增加XX发展投资集团有限公司提供连带责任保证担保。')
para('（二）保后管理','postLoanManagementDesc','风控措施-保后管理','分析说明类',[PD],
     '鉴于对该区域授信集中度较高，建议加强保后监管和检查。同时，密切关注境内外融资政策的变化带来的流动性压力、美联储降息政策变化可能的影响。')

# ---------- 输出 ----------
for i, f in enumerate(F, start=1):
    f['seq'] = i

SEC_OF_ANCHOR = {
    '（一）发行人、反担保人股权结构及对外投资': SEC2,
    '（二）发行人对外投资情况': SEC2,
    '（一）发行人主营业务模式': SEC3,
    '（二）反担保人主营业务模式': SEC3,
    '（一）主承销商：': SEC5,
    '（二）备证开立行：': SEC5,
    '（三）境外债（包含中资美元债和点心债，及以人民币、欧元、日元等其他货币计价的债券）大致情况': SEC5,
    '（二）发行人经营与财务风险分析': SEC6,
    '（三）发行人债务风险分析': SEC6,
    '（四）反担保措施风险分析': SEC6,
    '1.从经营方面来看': SEC6,
    '2.从财务方面来看': SEC6,
    '（五）发行人所在区域经济和财政风险分析': SEC6,
    '七、结论': SEC7,
    '（一）前提条件': SEC7,
    '（二）保后管理': SEC7,
}
TBL_SEC = {1: SEC1, 2: SEC2, 3: SEC3, 4: SEC3, 5: SEC4, 6: SEC6, 7: SEC6, 8: SEC6}
for f in F:
    if f['slot'] == 'cell':
        f['section'] = TBL_SEC[f['table']]
    elif 'after_table' in f:
        f['section'] = TBL_SEC[f['after_table']]
    else:
        f['section'] = SEC_OF_ANCHOR[f['after']]
    # 字段顺序：section 在前，便于阅读
    f_ordered = {'seq': f.pop('seq'), 'section': f.pop('section')}
    f_ordered.update(f)
    f.clear(); f.update(f_ordered)

doc = dict(
    meta=dict(
        doc_type='审查意见类',
        template_file='（金鼎集团）审查意见类模板（空白）.docx',
        based_on='1.（金鼎集团）XX城投集团有限公司审查意见.docx',
        generated_at='2026-09-29',
        desc='打标预处理清单：fields 为全部待填充点。slot=cell 的按 (table,row,cell) 定位（row/cell 为 tc 序号，含合并单元格）；'
             'slot=para 的为叙述型字段，after 表示插在该段落之后、after_table 表示插在该表之后。'
             'code 为建议书签名，sample 为原文档样例值（仅作理解参考，不写入模板）。',
        total_fields=len(F),
        total_tables=len(TABLES),
    ),
    tables=TABLES,
    fields=F,
)

with open(OUT, 'w', encoding='utf-8') as fp:
    json.dump(doc, fp, ensure_ascii=False, indent=2)

print('字段总数:', len(F))
from collections import Counter
print('slot 分布:', Counter(f['slot'] for f in F))
print('field_type 分布:', Counter(f['field_type'] for f in F))
print('category 分布:', Counter(f['category'] for f in F))
print('written:', OUT, os.path.getsize(OUT), 'B')
