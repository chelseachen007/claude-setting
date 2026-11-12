"""
自动生成指标映射表 v2：
- 自动匹配 fieldId（关键词匹配 + 相似度）
- 输出 Excel（带下拉验证）
"""
import csv
import json
import re
from difflib import SequenceMatcher

CSV_PATH = "/Users/chenjie/Downloads/001 指标字典（日更）-20260622.csv"
FIELDS_PATH = "/Users/chenjie/Documents/study/github/Obsidian/投资研究/youdata/models_fields.json"
OUTPUT_XLSX = "/Users/chenjie/Documents/study/github/Obsidian/投资研究/youdata/indicator_mapping_v2.xlsx"
OUTPUT_CSV = "/Users/chenjie/Documents/study/github/Obsidian/投资研究/youdata/indicator_mapping_v2.csv"

with open(FIELDS_PATH, "r", encoding="utf-8") as f:
    models_data = json.load(f)


def parse_csv():
    rows = []
    with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        next(reader)
        next(reader)
        for row in reader:
            if len(row) < 7:
                continue
            name = row[5].strip() if len(row) > 5 else ""
            if not name:
                continue
            rows.append({
                "序号": row[0].strip(),
                "业务域": row[1].strip(),
                "业务板块": row[2].strip(),
                "管理职能": row[3].strip(),
                "业务场景": row[4].strip(),
                "指标中文名称": name,
                "指标英文名称": row[6].strip() if len(row) > 6 else "",
                "业务描述": row[7].strip() if len(row) > 7 else "",
                "业务口径": row[8].strip() if len(row) > 8 else "",
                "计算公式": row[12].strip() if len(row) > 12 else "",
                "分析维度": row[13].strip() if len(row) > 13 else "",
                "时间周期": row[14].strip() if len(row) > 14 else "",
                "指标类型": row[17].strip() if len(row) > 17 else "",
                "对应原子指标": row[18].strip() if len(row) > 18 else "",
                "数据源": row[20].strip() if len(row) > 20 else "",
                "数据模型": row[21].strip() if len(row) > 21 else "",
                "统计字段": row[22].strip() if len(row) > 22 else "",
            })
    return rows


def guess_model(indicator):
    """匹配模型（同 v1 逻辑）"""
    name = indicator["指标中文名称"]
    caliber = indicator.get("业务口径", "")
    domain = indicator.get("业务域", "")
    block = indicator.get("业务板块", "")
    func = indicator.get("管理职能", "")
    scene = indicator.get("业务场景", "")

    keyword_model_map = {
        "花名册": ["人力/人力资源", "人力/hr 核心指标"],
        "员工数": ["人力/人力资源", "人力/hr 核心指标"],
        "正式员工": ["人力/人力资源", "人力/hr 核心指标"],
        "入职": ["人力/人力资源"],
        "离职": ["人力/离职员工信息表", "人力/人力资源"],
        "异动": ["人力/员工异动表", "人力/人员变动趋势表"],
        "职业资格": ["人力/职业资格证书表"],
        "人均营收": ["人力/营收表"],
        "固投发生额": ["人力/营收表"],
        "工程项目数": ["工程/项目概况/工程项目明细表"],
        "立项项目": ["工程/项目概况/工程项目明细表"],
        "建设项目": ["工程/项目概况/工程项目明细表"],
        "开工": ["工程/项目概况/项目进度统计表"],
        "完工": ["工程/项目概况/项目进度统计表"],
        "停工": ["工程/项目概况/项目进度统计表"],
        "准时开工率": ["工程/项目概况/项目进度统计表"],
        "准时完工率": ["工程/项目概况/项目进度统计表"],
        "三色预警": ["工程/项目概况/项目进度统计表"],
        "里程碑": ["工程/项目概况/项目进度统计表"],
        "全口径项目": ["工程/项目概况/项目进度统计表"],
        "过程进度": ["工程/项目概况/项目进度统计表"],
        "结算完成项目": ["工程/项目成本/项目结算表", "工程/项目成本/项目合同结算表"],
        "已结算项目": ["工程/项目成本/项目结算表", "工程/项目成本/项目合同结算表"],
        "工程变更": ["工程/项目成本/项目变更表"],
        "概算": ["工程/项目成本/项目概预算表"],
        "预算": ["工程/项目成本/项目概预算表"],
        "固投": ["工程/项目成本/项目固投计划表"],
        "固定资产投资": ["工程/项目成本/项目固投计划表"],
        "固定资产实际投资额": ["工程/项目成本/项目固投计划表"],
        "固定资产计划投资额": ["工程/项目成本/项目固投计划表"],
        "固投项目数": ["工程/项目成本/项目固投计划表"],
        "投资完成率": ["工程/项目成本/项目固投计划表"],
        "无价材料": ["工程/项目成本/物价材料备案表"],
        "质安": ["工程/项目质安分析/项目质量安全表"],
        "巡检": ["工程/项目质安分析/项目质量安全表"],
        "整改": ["工程/项目质安分析/项目质量安全表"],
        "结算送审": ["工程/项目成本/项目合同结算表"],
        "送审合同": ["工程/项目成本/项目合同结算表"],
        "结算审定": ["工程/项目成本/项目合同结算表"],
        "造价": ["工程/项目成本/公司项目成本指标汇总表"],
        "每平米": ["工程/项目成本/公司项目成本指标汇总表"],
        "每公里": ["工程/项目成本/公司项目成本指标汇总表"],
        "送审额": ["工程/项目成本/项目合同结算表", "工程/项目成本/公司项目成本指标汇总表"],
        "审定额": ["工程/项目成本/项目合同结算表", "工程/项目成本/公司项目成本指标汇总表"],
        "核减率": ["工程/项目成本/项目合同结算表", "工程/项目成本/公司项目成本指标汇总表"],
        "管理送审": ["工程/项目成本/项目合同结算表"],
        "审核时长": ["工程/项目成本/项目合同结算表"],
        "超概": ["工程/项目成本/项目结算/合同结算表"],
        "招标": ["成本/招采/招采计划", "成本/招采/招采流程审批"],
        "中标": ["成本/招采/招采中标信息"],
        "合同金额": ["成本/招采/招采合同审批"],
        "服务单位": ["成本/招采/招采中标信息"],
        "内控委托": ["成本/招采/招采流程审批"],
        "资金余额": ["财务/资金预算情况/期初期末余额表"],
        "资金流入": ["财务/资金计划执行分析/资金流入执行分析"],
        "资金流出": ["财务/资金计划执行分析/资金流出执行分析"],
        "资金缺口": ["财务/资金计划执行分析/统计汇总表"],
        "预算执行": ["财务/资金预算情况/公司预算执行情况表"],
        "营业收入": ["财务/盈利能力分析/盈利能力分析表", "财务/盈利能力分析/考核营业收入明细"],
        "营业成本": ["财务/盈利能力分析/营收成本结构", "财务/盈利能力分析/营业成本明细表"],
        "毛利": ["财务/盈利能力分析/盈利能力分析表"],
        "期间费用": ["财务/盈利能力分析/期间费用汇总表", "财务/盈利能力分析/期间费用明细表"],
        "利润": ["财务/盈利能力分析/利润明细表", "财务/盈利能力分析/盈利能力分析表"],
        "资产总额": ["财务/资产状况分析/资产状况表"],
        "负债总额": ["财务/资产状况分析/资产状况表"],
        "所有者权益": ["财务/资产状况分析/资产状况表"],
        "资产负债率": ["财务/资产状况分析/资产状况表"],
        "有息负债": ["财务/资产状况分析/资产状况表"],
        "经营性资产": ["财务/资产状况分析/项目资产规模表"],
        "非经营性资产": ["财务/资产状况分析/项目资产规模表"],
        "流动资产": ["财务/资产状况分析/资产结构表"],
        "非流动资产": ["财务/资产状况分析/资产结构表"],
        "流动负债": ["财务/资产状况分析/资产结构表"],
        "非流动负债": ["财务/资产状况分析/资产结构表"],
        "销售费用": ["财务/税费分析/纳税分析明细", "财务/盈利能力分析/期间费用汇总表"],
        "管理费用": ["财务/税费分析/纳税分析明细", "财务/盈利能力分析/期间费用汇总表"],
        "财务费用": ["财务/税费分析/纳税分析明细", "财务/盈利能力分析/期间费用汇总表"],
        "资本化利息": ["财务/税费分析/三公费用和资本化利息表"],
        "三公费用": ["财务/税费分析/三公费用和资本化利息表"],
        "税费缴纳": ["财务/税费分析/纳税分析"],
        "应收账款": ["财务/其他应收账款/应收款项汇总表", "财务/业务营收账款/业务营收账款"],
        "逾期应收": ["财务/其他应收账款/应收款项汇总表"],
        "周转天数": ["财务/业务营收账款/业务营收账款"],
        "货币资金": ["财务/资产状况分析/资产状况表"],
        "房产资产": ["资产/资产概况/资产台帐表"],
        "停车场资产": ["资产/资产概况/管理停车场台账表", "资产/资产概况/资产台帐表"],
        "车位": ["资产/资产概况/管理停车场台账表"],
        "去化": ["资产/资产去化/资产去化情况表"],
        "出租": ["资产/资产去化/资产去化情况表"],
        "出售": ["资产/资产去化/资产去化情况表"],
        "空置": ["资产/资产去化/资产去化情况表"],
        "租赁合同": ["资产/资产去化/资产合同信息表"],
        "租金": ["资产/资产去化/月度租售收入表", "资产/资产去化/资产去化情况表"],
        "租售": ["资产/资产去化/房源租售趋势表"],
        "账单": ["资产/资产去化/月度租售收入表"],
        "运营收入": ["资产/资产去化/月度租售收入表"],
        "做地": ["做地/做地详情"],
        "收储": ["做地/做地详情"],
        "出让金": ["做地/做地详情"],
        "出让": ["做地/做地详情"],
        "流入执行率": ["财务/资金计划执行分析/资金流入执行分析"],
        "流出执行率": ["财务/资金计划执行分析/资金流出执行分析"],
        "预计流入": ["财务/资金计划执行分析/资金流入执行分析"],
        "实际流入": ["财务/资金计划执行分析/资金流入执行分析", "数据填报/实际流入详情"],
        "预计流出": ["财务/资金计划执行分析/资金流出执行分析"],
        "实际流出": ["财务/资金计划执行分析/资金流出执行分析"],
        "流入资金额": ["财务/资金计划执行分析/资金流入执行分析"],
        "工会经费": ["人力/人力资源"],
        "会员会费": ["人力/人力资源"],
        "工会": ["人力/人力资源"],
    }

    candidates = []
    all_text = f"{name} {caliber} {block} {func} {scene}"
    for keyword, model_paths in keyword_model_map.items():
        if keyword in all_text:
            for mp in model_paths:
                for mid, info in models_data.items():
                    full_path = f"{info.get('path', '')}/{info.get('title', '')}"
                    target_title = mp.split("/")[-1]
                    # 多种匹配策略
                    if (info.get("path", "") == mp
                        or info.get("title", "") == target_title
                        or full_path == mp
                        or mp.endswith(info.get("title", ""))
                        or info.get("title", "") in mp
                        or mp in full_path):
                        if mid not in [c["id"] for c in candidates]:
                            candidates.append({"id": mid, "path": info["path"], "title": info["title"]})
    return candidates[:3]


def similarity(a, b):
    """中文字符串相似度"""
    return SequenceMatcher(None, a, b).ratio()


def match_field(indicator, model_id):
    """
    自动匹配 fieldId + aggregator + dateDimension
    返回: (fieldId, aggregator, dateFieldId, confidence)
    """
    m = models_data.get(str(model_id), {})
    measures = m.get("measures", [])
    dims = m.get("dimensions", [])
    name = indicator["指标中文名称"]
    caliber = indicator.get("业务口径", "")
    stat_field = indicator.get("统计字段", "")
    formula = indicator.get("计算公式", "")

    # --- 1. 匹配度量字段 ---
    best_meas = None
    best_score = 0

    for me in measures:
        alias = me.get("alias", "")
        field = me.get("field", "")
        fid = me.get("fieldId", "")

        # 直接包含匹配
        if alias and alias in name:
            score = 1.0
        elif alias and name in alias:
            score = 0.9
        elif alias and any(kw in alias for kw in name.split("数") if len(kw) >= 2):
            score = 0.6
        else:
            # 相似度匹配
            score = max(similarity(alias, name), similarity(field, name)) * 0.5
            # 口径中提到的关键词
            if caliber:
                for kw in [alias, field]:
                    if kw and len(kw) >= 2 and kw in caliber:
                        score = max(score, 0.7)

        if score > best_score:
            best_score = score
            best_meas = me

    # 如果没有好的度量匹配，尝试用维度字段（COUNT 模式）
    if not best_meas or best_score < 0.3:
        for d in dims:
            alias = d.get("alias", "")
            fid = d.get("fieldId", "")
            # 维度中匹配项目编码、人员ID等
            if any(kw in alias for kw in ["编码", "ID", "编号", "id"]):
                score = 0.4
            elif alias and alias in name:
                score = 0.5
            else:
                score = similarity(alias, name) * 0.3

            if score > best_score:
                best_score = score
                best_meas = d
                # 标记用 CNT

    if not best_meas:
        return ("", "", "", "none")

    field_id = best_meas.get("fieldId", "")
    default_agg = best_meas.get("defaultAggregator", "SUM")

    # 确定聚合方式
    # 名称含"数/个/次/人次/数量" → CNT（或 SUM 如果字段是数值型预聚合）
    # 名称含"金额/额/率/面积/长度/天数" → SUM
    # 名称含"均价/平均" → AVG
    agg = default_agg
    if any(kw in name for kw in ["均价", "平均", "人均", "单方"]):
        agg = "AVG"
    elif any(kw in name for kw in ["率", "占比"]):
        agg = "SUM"  # 比率通常是预计算好的

    # --- 2. 匹配日期维度 ---
    date_fields = [d for d in dims if d.get("dataType") == "DateTime"]
    date_fid = ""
    if date_fields:
        # 优先选择名称含"日期/时间/报告日期"的
        for df in date_fields:
            alias = df.get("alias", "")
            if any(kw in alias for kw in ["报告日期", "统计日期", "填报日期"]):
                date_fid = df.get("fieldId", "")
                break
        if not date_fid:
            # 选第一个日期字段
            date_fid = date_fields[0].get("fieldId", "")

    confidence = "high" if best_score >= 0.6 else ("medium" if best_score >= 0.3 else "low")
    return (field_id, agg, date_fid, confidence)


def main():
    indicators = parse_csv()
    print(f"共解析 {len(indicators)} 条指标")

    # 按类型排序
    type_order = {"原子指标": 0, "派生指标": 1, "复合指标": 2, "复核指标": 3}
    indicators.sort(key=lambda r: (type_order.get(r["指标类型"], 9), r["指标中文名称"]))

    results = []
    stats = {"high": 0, "medium": 0, "low": 0, "none": 0}

    for ind in indicators:
        candidates = guess_model(ind)
        model_id = candidates[0]["id"] if candidates else ""
        model_path = candidates[0]["path"] if candidates else ""
        model_title = candidates[0]["title"] if candidates else ""

        field_id, agg, date_fid, confidence = ("", "", "", "none")
        if model_id:
            field_id, agg, date_fid, confidence = match_field(ind, model_id)

        stats[confidence] = stats.get(confidence, 0) + 1

        # 构造 setting JSON（预填）
        setting_json = ""
        if model_id and field_id:
            setting = {
                "projectId": 5,
                "name": ind["指标中文名称"],
                "nameEn": ind.get("指标英文名称", ""),
                "dataModelId": int(model_id),
                "folderId": 0,  # 后面按业务域填
                "enableChatBi": 1,
                "enableMetricExploration": 0,
                "type": "Existed",
                "setting": {
                    "field": {
                        "$type": "Measure",
                        "role": "Measure",
                        "fieldId": field_id,
                        "aggregator": agg,
                        "tableId": 1,
                        "logicalTableId": 1,
                        "partition": False,
                    },
                    "dimensions": [],
                    "filters": [],
                    "timePoint": {"enable": False, "type": "periodStart"},
                    "attributionSetting": {
                        "enableParameter": False,
                        "direction": "positive",
                        "dateCalcSetting": {
                            "detectFilter": {
                                "$type": "DiscreteDimensionFilter",
                                "date": {
                                    "$type": "DateTimeFilter",
                                    "dynamicMode": 3,
                                    "mode": {"$type": "RelativeTime", "count": 1, "unit": "month", "anchor": 0},
                                }
                            },
                            "dimensionsGroup": []
                        },
                        "planActualSetting": {"enable": False},
                    },
                    "customAttributes": [],
                },
                "caliber": ind.get("业务口径", "")[:500],
                "publishRelatedId": None,
                "parameterList": [],
            }
            # 添加日期维度
            if date_fid:
                # 找到日期维度的完整信息
                m = models_data.get(str(model_id), {})
                for d in m.get("dimensions", []):
                    if d.get("fieldId") == date_fid:
                        setting["setting"]["dateDimension"] = {
                            "$type": "Dimension",
                            "role": "Dimension",
                            "fieldId": date_fid,
                            "field": d.get("field", ""),
                            "alias": d.get("alias", ""),
                            "tableId": d.get("tableId", 1),
                            "tableName": d.get("tableName", ""),
                            "mapFunction": "YEAR-MONTH-DAY",
                            "granularity": "g0",
                            "logicalTableId": d.get("logicalTableId", 1),
                            "bigtable": False,
                            "partition": False,
                        }
                        break
            setting_json = json.dumps(setting, ensure_ascii=False)

        results.append({
            "指标中文名称": ind["指标中文名称"],
            "指标类型": ind["指标类型"],
            "对应原子指标": ind["对应原子指标"],
            "业务域": ind["业务域"],
            "管理职能": ind["管理职能"],
            "dataModelId": model_id,
            "模型路径": f"{model_path}/{model_title}" if model_path else "",
            "fieldId": field_id,
            "aggregator": agg,
            "dateFieldId": date_fid,
            "置信度": confidence,
            "业务口径摘要": ind.get("业务口径", "")[:80],
            "时间周期": ind.get("时间周期", ""),
            "业务口径全文": ind.get("业务口径", ""),
            "setting_json": setting_json,
        })

    # 写 CSV
    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    # 写 Excel（带下拉验证）
    try:
        import openpyxl
        from openpyxl.worksheet.datavalidation import DataValidation

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "指标映射"

        headers = list(results[0].keys())
        # 写表头
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=h)
            cell.font = openpyxl.styles.Font(bold=True)

        # 写数据
        for row_idx, r in enumerate(results, 2):
            for col_idx, h in enumerate(headers, 1):
                ws.cell(row=row_idx, column=col_idx, value=r[h])

        # 置信度下拉
        dv_conf = DataValidation(type="list", formula1='"high,medium,low,none"', allow_blank=True)
        dv_conf.error = "请选择: high/medium/low/none"
        ws.add_data_validation(dv_conf)
        conf_col = headers.index("置信度") + 1
        dv_conf.add(f"{chr(64+conf_col)}2:{chr(64+conf_col)}{len(results)+1}")

        # aggregator 下拉
        dv_agg = DataValidation(type="list", formula1='"SUM,CNT,AVG,COUNT_DISTINCT"', allow_blank=True)
        ws.add_data_validation(dv_agg)
        agg_col = headers.index("aggregator") + 1
        dv_agg.add(f"{chr(64+agg_col)}2:{chr(64+agg_col)}{len(results)+1}")

        # 列宽
        ws.column_dimensions["A"].width = 25  # 指标名
        ws.column_dimensions["B"].width = 10  # 类型
        ws.column_dimensions["F"].width = 12  # modelId
        ws.column_dimensions["G"].width = 30  # 模型路径
        ws.column_dimensions["H"].width = 15  # fieldId
        ws.column_dimensions["I"].width = 12  # aggregator
        ws.column_dimensions["K"].width = 10  # 置信度
        ws.column_dimensions["L"].width = 40  # 口径

        # 冻结首行
        ws.freeze_panes = "A2"

        # 筛选
        ws.auto_filter.ref = f"A1:{chr(64+len(headers))}{len(results)+1}"

        wb.save(OUTPUT_XLSX)
        print(f"Excel 已保存: {OUTPUT_XLSX}")
    except ImportError:
        print("openpyxl 未安装，跳过 Excel 生成。pip install openpyxl")

    # 统计
    print(f"\n=== 匹配统计 ===")
    print(f"总指标: {len(results)}")
    print(f"  高置信度(high):  {stats['high']}")
    print(f"  中置信度(medium): {stats['medium']}")
    print(f"  低置信度(low):   {stats['low']}")
    print(f"  未匹配(none):    {stats['none']}")

    # 按类型统计
    for t in ["原子指标", "派生指标", "复合指标", "复核指标"]:
        typed = [r for r in results if r["指标类型"] == t]
        matched = [r for r in typed if r["fieldId"]]
        print(f"  {t}: {len(typed)} 条, {len(matched)} 已匹配字段")

    print(f"\nCSV 已保存: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
