"""
构建指标字典 → 模型 → 字段 的映射表
输出: indicator_mapping.csv (供用户确认)
"""
import csv
import json
import re

CSV_PATH = "/Users/chenjie/Downloads/001 指标字典（日更）-20260622.csv"
FIELDS_PATH = "/Users/chenjie/Documents/study/github/Obsidian/投资研究/youdata/models_fields.json"
OUTPUT_PATH = "/Users/chenjie/Documents/study/github/Obsidian/投资研究/youdata/indicator_mapping.csv"

# 加载模型字段
with open(FIELDS_PATH, "r", encoding="utf-8") as f:
    models_data = json.load(f)

# 模型路径 → 关键词映射 (用于自动匹配)
MODEL_KEYWORDS = {}
for mid, m in models_data.items():
    path = m.get("path", "")
    title = m.get("title", "")
    MODEL_KEYWORDS[mid] = {
        "path": path,
        "title": title,
        "dim_names": [d.get("alias", d.get("field", "")) for d in m.get("dimensions", [])],
        "meas_names": [me.get("alias", me.get("field", "")) for me in m.get("measures", [])],
    }


def parse_csv():
    """解析指标字典 CSV，提取有效指标行"""
    rows = []
    with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)  # skip row 1
        header2 = next(reader)  # skip row 2 (sub-header)

        for row in reader:
            if len(row) < 7:
                continue
            name = row[5].strip() if len(row) > 5 else ""
            if not name:
                continue

            # 提取关键字段
            indicator = {
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
                "指标类型": row[17].strip() if len(row) > 17 else "",  # 指标分级列
                "对应原子指标": row[18].strip() if len(row) > 18 else "",
                "数据源": row[20].strip() if len(row) > 20 else "",
                "数据模型": row[21].strip() if len(row) > 21 else "",
                "统计字段": row[22].strip() if len(row) > 22 else "",
            }
            rows.append(indicator)
    return rows


def guess_model(indicator):
    """根据指标名称和业务口径，尝试匹配到模型"""
    name = indicator["指标中文名称"]
    caliber = indicator.get("业务口径", "")
    domain = indicator.get("业务域", "")
    block = indicator.get("业务板块", "")
    func = indicator.get("管理职能", "")
    scene = indicator.get("业务场景", "")
    data_source = indicator.get("数据源", "")
    data_model = indicator.get("数据模型", "")
    stat_field = indicator.get("统计字段", "")

    # 关键词 → 模型路径映射
    keyword_model_map = {
        # 人力
        "花名册": ["人力/人力资源", "人力/hr 核心指标"],
        "员工数": ["人力/人力资源", "人力/hr 核心指标"],
        "正式员工": ["人力/人力资源", "人力/hr 核心指标"],
        "入职": ["人力/人力资源"],
        "离职": ["人力/离职员工信息表", "人力/人力资源"],
        "异动": ["人力/员工异动表", "人力/人员变动趋势表"],
        "职业资格": ["人力/职业资格证书表"],
        "人均营收": ["人力/营收表"],
        "固投发生额": ["人力/营收表"],
        # 工程项目
        "工程项目数": ["工程/项目概况/工程项目明细表"],
        "立项项目": ["工程/项目概况/工程项目明细表"],
        "建设项目": ["工程/项目概况/工程项目明细表"],
        "开工": ["工程/项目概况/项目进度统计表"],
        "完工": ["工程/项目概况/项目进度统计表"],
        "停工": ["工程/项目概况/项目进度统计表"],
        "准时开工率": ["工程/项目概况/项目进度统计表"],
        "准时完工率": ["工程/项目概况/项目进度统计表"],
        "三色预警": ["工程/项目概况/项目进度统计表"],
        "里程碑": ["工程/项目概况/项目进度统计表", "工程/项目概况/建管单位项目进度统计表"],
        "全口径项目": ["工程/项目概况/项目进度统计表"],
        "过程进度": ["工程/项目概况/项目进度统计表"],
        "结算完成项目": ["工程/项目成本/项目结算表", "工程/项目成本/项目合同结算表"],
        "已结算项目": ["工程/项目成本/项目结算表", "工程/项目成本/项目合同结算表"],
        "工程变更": ["工程/项目成本/项目变更表"],
        "概算": ["工程/项目成本/项目概预算表"],
        "预算": ["工程/项目成本/项目概预算表"],
        "固投": ["工程/项目成本/项目固投计划表"],
        "投资完成率": ["工程/项目成本/项目固投计划表"],
        "无价材料": ["工程/项目成本/物价材料备案表"],
        "质安": ["工程/项目质安分析/项目质量安全表"],
        "巡检": ["工程/项目质安分析/项目质量安全表"],
        "整改": ["工程/项目质安分析/项目质量安全表"],
        "结算送审": ["工程/项目成本/项目合同结算表"],
        "结算审定": ["工程/项目成本/项目合同结算表"],
        "造价": ["工程/项目成本/公司项目成本指标汇总表"],
        "每平米": ["工程/项目成本/公司项目成本指标汇总表"],
        "每公里": ["工程/项目成本/公司项目成本指标汇总表"],
        # 招采
        "招标": ["成本/招采/招采计划", "成本/招采/招采流程审批"],
        "中标": ["成本/招采/招采中标信息"],
        "合同金额": ["成本/招采/招采合同审批"],
        "服务单位": ["成本/招采/招采中标信息"],
        "内控委托": ["成本/招采/招采流程审批"],
        # 财务
        "资金余额": ["财务/资金预算情况/期初期末余额表"],
        "资金流入": ["财务/资金计划执行分析/资金流入执行分析"],
        "资金流出": ["财务/资金计划执行分析/资金流出执行分析"],
        "资金缺口": ["财务/资金计划执行分析/统计汇总表"],
        "预算执行": ["财务/资金预算情况/公司预算执行情况表", "财务/资金预算情况/预算情况总结表"],
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
        "逾期应收": ["财务/其他应收账款/应收款项汇总表", "财务/业务营收账款/业务营收账款"],
        "周转天数": ["财务/业务营收账款/业务营收账款"],
        "货币资金": ["财务/资产状况分析/资产状况表"],
        "长期股权投资": ["财务/资产状况分析/项目资产规模表"],
        "应收&其他应收": ["财务/资产状况分析/项目资产规模表"],
        # 资产
        "房产资产": ["资产/资产概况/资产台帐表"],
        "停车场资产": ["资产/资产概况/管理停车场台账表", "资产/资产概况/资产台帐表"],
        "车位": ["资产/资产概况/管理停车场台账表", "资产/资产概况/资产台帐表"],
        "资产台账": ["资产/资产概况/资产台帐表"],
        "去化": ["资产/资产去化/资产去化情况表"],
        "出租": ["资产/资产去化/资产去化情况表", "资产/资产去化/资产房源信息表"],
        "出售": ["资产/资产去化/资产去化情况表"],
        "空置": ["资产/资产去化/资产去化情况表"],
        "租赁合同": ["资产/资产去化/资产合同信息表"],
        "租金": ["资产/资产去化/月度租售收入表", "资产/资产去化/资产去化情况表"],
        "租售": ["资产/资产去化/房源租售趋势表", "资产/资产去化/资产去化情况表"],
        "账单": ["资产/资产去化/月度租售收入表"],
        "运营收入": ["资产/资产去化/月度租售收入表"],
        # 做地
        "做地": ["做地/做地详情", "做地/做地考核目标填报"],
        "收储": ["做地/做地详情", "数据填报/地块收储出让进展填报"],
        "出让": ["做地/做地详情", "数据填报/地块收储出让进展填报"],
        "出让金": ["做地/做地详情", "数据填报/地块收储出让进展填报"],
        # 工程补充匹配 - 未匹配的指标
        "结算送审": ["工程/项目成本/项目合同结算表", "工程/项目成本/项目结算/合同结算表"],
        "送审合同": ["工程/项目成本/项目合同结算表"],
        "结算完成项目": ["工程/项目成本/项目结算表", "工程/项目成本/公司项目成本指标汇总表"],
        "固投实际": ["工程/项目成本/项目固投计划表"],
        "固投计划": ["工程/项目成本/项目固投计划表"],
        "固定资产投资": ["工程/项目成本/项目固投计划表"],
        "固定资产实际投资额": ["工程/项目成本/项目固投计划表"],
        "固定资产计划投资额": ["工程/项目成本/项目固投计划表"],
        "固投项目数": ["工程/项目成本/项目固投计划表"],
        "送审额": ["工程/项目成本/项目合同结算表", "工程/项目成本/公司项目成本指标汇总表"],
        "审定额": ["工程/项目成本/项目合同结算表", "工程/项目成本/公司项目成本指标汇总表"],
        "核减率": ["工程/项目成本/项目合同结算表", "工程/项目成本/公司项目成本指标汇总表"],
        "管理送审": ["工程/项目成本/项目合同结算表"],
        "审核时长": ["工程/项目成本/项目合同结算表"],
        "超概": ["工程/项目成本/项目结算/合同结算表", "工程/项目成本/项目结算表"],
        # 做地补充
        "在手土地": ["做地/做地详情"],
        "做地业务收入": ["做地/做地详情"],
        # 财务补充
        "流入执行率": ["财务/资金计划执行分析/资金流入执行分析", "财务/资金计划执行分析/统计汇总表"],
        "流出执行率": ["财务/资金计划执行分析/资金流出执行分析", "财务/资金计划执行分析/统计汇总表"],
        "预计流入": ["财务/资金计划执行分析/资金流入执行分析"],
        "实际流入": ["财务/资金计划执行分析/资金流入执行分析"],
        "预计流出": ["财务/资金计划执行分析/资金流出执行分析"],
        "实际流出": ["财务/资金计划执行分析/资金流出执行分析"],
        "流入资金额": ["财务/资金计划执行分析/资金流入执行分析", "数据填报/实际流入详情"],
        "流出资金额": ["财务/资金计划执行分析/资金流出执行分析"],
        "流入偏差": ["财务/资金计划执行分析/统计汇总表"],
        "流出偏差": ["财务/资金计划执行分析/统计汇总表"],
        "资金缺口": ["财务/资金计划执行分析/统计汇总表"],
        # 工会经费 → 人力
        "工会经费": ["人力/人力资源"],
        "会员会费": ["人力/人力资源"],
        "工会": ["人力/人力资源"],
        # 客商
        "合作方": [],  # 无模型
        "涉诉": [],    # 无模型
        "客商": [],    # 无模型
        "履约": [],    # 无模型
    }

    # 尝试匹配
    candidates = []
    all_text = f"{name} {caliber} {block} {func} {scene} {data_source}"

    for keyword, model_paths in keyword_model_map.items():
        if keyword in all_text:
            for mp in model_paths:
                for mid, info in MODEL_KEYWORDS.items():
                    if info["path"] == mp or info["title"] == mp.split("/")[-1]:
                        if mid not in [c["id"] for c in candidates]:
                            candidates.append({"id": mid, "path": info["path"], "title": info["title"]})

    return candidates[:3]  # 最多3个候选


def main():
    indicators = parse_csv()
    print(f"共解析 {len(indicators)} 条指标\n")

    # 按指标类型分类
    atomic = [i for i in indicators if i["指标类型"] == "原子指标"]
    derived = [i for i in indicators if i["指标类型"] == "派生指标"]
    compound = [i for i in indicators if i["指标类型"] == "复合指标"]
    other = [i for i in indicators if i["指标类型"] not in ("原子指标", "派生指标", "复合指标")]
    print(f"  原子指标: {len(atomic)}")
    print(f"  派生指标: {len(derived)}")
    print(f"  复合指标: {len(compound)}")
    print(f"  其他: {len(other)}")
    print()

    # 生成映射表
    rows = []
    for ind in indicators:
        candidates = guess_model(ind)
        model_str = " | ".join([f"[{c['id']}]{c['path']}/{c['title']}" for c in candidates]) if candidates else ""

        # 获取候选模型的可选字段列表
        meas_options = ""
        dim_options = ""
        date_dim_options = ""
        dim_list = []
        if candidates:
            top_model = candidates[0]
            mid = top_model["id"]
            m = models_data.get(mid, {})
            meas_list = m.get("measures", [])
            dim_list = m.get("dimensions", [])
            meas_options = " | ".join([
                f"{me.get('alias','')}({me.get('fieldId','')},{me.get('defaultAggregator','SUM')})"
                for me in meas_list
            ])
            # 对于0度量模型，维度字段也可以作为度量来统计
            if not meas_list and dim_list:
                meas_options = "(无度量，可用维度: " + " | ".join([
                    f"{d.get('alias','')}({d.get('fieldId','')},CNT)"
                    for d in dim_list[:15]
                ]) + ")"
            dim_options = " | ".join([
                f"{d.get('alias','')}({d.get('fieldId','')})"
                for d in dim_list[:15]
            ])
            date_dim_options = " | ".join([
                f"{d.get('alias','')}({d.get('fieldId','')})"
                for d in dim_list if d.get("dataType") == "DateTime"
            ])

        rows.append({
            "指标中文名称": ind["指标中文名称"],
            "指标类型": ind["指标类型"],
            "对应原子指标": ind["对应原子指标"],
            "业务域": ind["业务域"],
            "业务板块": ind["业务板块"],
            "管理职能": ind["管理职能"],
            "自动匹配模型": model_str,
            "确认dataModelId": candidates[0]["id"] if candidates else "",
            "确认fieldId": "",  # 需要用户确认模型后再填
            "确认aggregator": "",  # SUM/CNT/AVG
            "可选度量字段(fieldId,agg)": meas_options,
            "可选维度字段(fieldId)": dim_options,
            "可选时间维度(DateTime)": date_dim_options,
            "业务口径摘要": ind["业务口径"][:80] if ind["业务口径"] else "",
            "计算公式": ind["计算公式"][:80] if ind["计算公式"] else "",
            "分析维度": ind["分析维度"][:60] if ind["分析维度"] else "",
        })

    # 按指标类型排序: 原子指标 → 派生指标 → 复合指标 → 复核指标 → 其他
    type_order = {"原子指标": 0, "派生指标": 1, "复合指标": 2, "复核指标": 3}
    rows.sort(key=lambda r: (type_order.get(r["指标类型"], 9), r["指标中文名称"]))

    # 写 CSV
    with open(OUTPUT_PATH, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"映射表已保存到: {OUTPUT_PATH}")

    # 统计匹配率
    matched = sum(1 for r in rows if r["确认dataModelId"])
    print(f"自动匹配率: {matched}/{len(rows)} ({matched*100//len(rows)}%)")
    print(f"需手动确认: {len(rows) - matched}")


if __name__ == "__main__":
    main()
