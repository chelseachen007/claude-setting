#!/usr/bin/env python3
"""
国家队持仓追踪器
拉取2015-2026年中央汇金、证金公司、社保基金的季度持仓数据
数据源：东方财富（通过 AKShare）
"""

import akshare as ak
import pandas as pd
import time
import json
from datetime import datetime
from pathlib import Path

# ==================== 配置 ====================

# 国家队机构关键词（用于从股东名称中匹配）
NATIONAL_TEAM_KEYWORDS = {
    "中央汇金": ["中央汇金投资有限责任公司", "中央汇金资产管理有限责任公司", "汇金公司"],
    "证金公司": ["中国证券金融股份有限公司", "证金公司"],
    "社保基金": ["全国社会保障基金理事会", "全国社保基金", "社保基金"],
}

# 主要蓝筹股（汇金/证金重仓股，扫描范围）
BLUE_CHIP_STOCKS = [
    # 四大行
    "601398",  # 工商银行
    "601939",  # 建设银行
    "601288",  # 农业银行
    "601988",  # 中国银行
    # 股份制银行
    "600036",  # 招商银行
    "601166",  # 兴业银行
    "600016",  # 民生银行
    "600000",  # 浦发银行
    "000001",  # 平安银行
    "601818",  # 光大银行
    "600015",  # 华夏银行
    # 保险
    "601318",  # 中国平安
    "601628",  # 中国人寿
    "601601",  # 中国太保
    "002001",  # 新和成 (保险概念)
    # 券商
    "600030",  # 中信证券
    "601211",  # 国泰君安
    "601688",  # 华泰证券
    # 石油石化
    "601857",  # 中国石油
    "600028",  # 中国石化
    # 电力
    "600900",  # 长江电力
    # 消费
    "600519",  # 贵州茅台
    "000858",  # 五粮液
    # 医药
    "600276",  # 恒瑞医药
    # 通信
    "600941",  # 中国移动
    # 基建
    "601668",  # 中国建筑
    "601390",  # 中国中铁
    # 汽车
    "600104",  # 上汽集团
    # 家电
    "000651",  # 格力电器
    "000333",  # 美的集团
]

# 季度报告日期列表（2015Q1 - 2026Q1）
def generate_quarter_dates(start_year=2015, end_year=2026):
    """生成季度报告日期列表"""
    dates = []
    quarters = ["0331", "0630", "0930", "1231"]
    for year in range(start_year, end_year + 1):
        for q in quarters:
            dates.append(f"{year}{q}")
    return dates


# ==================== 数据拉取 ====================

def fetch_social_security_data(quarter_dates):
    """拉取社保基金季度持仓数据"""
    all_data = []

    for date in quarter_dates:
        try:
            df = ak.stock_report_fund_hold(symbol="社保持仓", date=date)
            if df is not None and len(df) > 0:
                df['报告日期'] = date
                all_data.append(df)
                print(f"  ✓ 社保 {date}: {len(df)} 只股票")
            else:
                print(f"  - 社保 {date}: 无数据")
            time.sleep(0.5)
        except Exception as e:
            print(f"  ✗ 社保 {date}: {e}")
            time.sleep(1)

    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()


def fetch_stock_holder_data(stock_codes, institution_keywords):
    """从个股十大股东中提取国家队持仓"""
    all_data = []

    for code in stock_codes:
        try:
            df = ak.stock_main_stock_holder(stock=code)
            if df is None or len(df) == 0:
                continue

            # 匹配国家队机构
            for inst_name, keywords in institution_keywords.items():
                for kw in keywords:
                    mask = df['股东名称'].str.contains(kw, na=False)
                    if mask.any():
                        matched = df[mask].copy()
                        matched['机构分类'] = inst_name
                        matched['股票代码'] = code
                        all_data.append(matched)
                        break  # 每个机构分类只匹配一次

            time.sleep(0.3)
            print(f"  ✓ 股东 {code}")
        except Exception as e:
            print(f"  ✗ 股东 {code}: {e}")
            time.sleep(0.5)

    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()


# ==================== 数据处理 ====================

def analyze_social_security(df):
    """分析社保基金持仓数据"""
    if df.empty:
        return {}

    results = {
        "总记录数": len(df),
        "季度数": df['报告日期'].nunique(),
        "涉及股票数": df['股票代码'].nunique(),
    }

    # 按季度统计持仓市值
    quarterly = df.groupby('报告日期').agg({
        '持股市值': 'sum',
        '股票代码': 'count'
    }).rename(columns={'股票代码': '持股数量'})

    results['季度持仓'] = quarterly.to_dict('index')

    # 找出长期重仓股（出现次数最多的）
    stock_freq = df['股票简称'].value_counts().head(20)
    results['长期重仓股'] = stock_freq.to_dict()

    return results


def analyze_national_team(df):
    """分析汇金/证金持仓数据"""
    if df.empty:
        return {}

    results = {}
    for inst in df['机构分类'].unique():
        inst_df = df[df['机构分类'] == inst]
        results[inst] = {
            "总记录数": len(inst_df),
            "涉及股票数": inst_df['股票代码'].nunique(),
            "持仓股票": inst_df.groupby('股票代码').agg({
                '持股数量': 'last',
                '持股比例': 'last',
                '截至日期': 'last'
            }).to_dict('index')
        }

    return results


# ==================== 主程序 ====================

def main():
    output_dir = Path(__file__).parent
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    quarter_dates = generate_quarter_dates(2015, 2026)
    print(f"📊 国家队持仓追踪器")
    print(f"📅 数据范围: 2015Q1 - 2026Q1")
    print(f"📋 季度数: {len(quarter_dates)}")
    print()

    # 1. 拉取社保基金数据
    print("=" * 50)
    print("🏦 拉取社保基金季度持仓数据...")
    ss_data = fetch_social_security_data(quarter_dates)

    if not ss_data.empty:
        # 保存原始数据
        ss_file = output_dir / f"社保基金持仓_2015-2026_{timestamp}.csv"
        ss_data.to_csv(ss_file, index=False, encoding='utf-8-sig')
        print(f"\n💾 社保数据已保存: {ss_file}")

        # 分析
        ss_analysis = analyze_social_security(ss_data)
        print(f"\n📊 社保基金分析:")
        print(f"   总记录数: {ss_analysis.get('总记录数', 0)}")
        print(f"   季度数: {ss_analysis.get('季度数', 0)}")
        print(f"   涉及股票数: {ss_analysis.get('涉及股票数', 0)}")
    else:
        print("\n⚠️  未获取到社保基金数据")

    # 2. 拉取汇金/证金数据
    print("\n" + "=" * 50)
    print("🏛️  拉取汇金/证金股东数据...")
    nt_data = fetch_stock_holder_data(BLUE_CHIP_STOCKS, NATIONAL_TEAM_KEYWORDS)

    if not nt_data.empty:
        # 保存原始数据
        nt_file = output_dir / f"汇金证金持仓_2015-2026_{timestamp}.csv"
        nt_data.to_csv(nt_file, index=False, encoding='utf-8-sig')
        print(f"\n💾 汇金/证金数据已保存: {nt_file}")

        # 分析
        nt_analysis = analyze_national_team(nt_data)
        print(f"\n📊 汇金/证金分析:")
        for inst, data in nt_analysis.items():
            print(f"   {inst}: {data['涉及股票数']} 只股票, {data['总记录数']} 条记录")
    else:
        print("\n⚠️  未获取到汇金/证金数据")

    # 3. 生成汇总报告
    print("\n" + "=" * 50)
    print("📝 生成汇总报告...")

    report = {
        "生成时间": datetime.now().isoformat(),
        "数据范围": "2015Q1 - 2026Q1",
        "社保基金": ss_analysis if not ss_data.empty else {},
        "汇金证金": nt_analysis if not nt_data.empty else {},
    }

    # 处理不可序列化的类型
    def convert_value(v):
        if isinstance(v, (pd.Timestamp, datetime)):
            return v.isoformat()
        if hasattr(v, 'isoformat'):
            return v.isoformat()
        if isinstance(v, float) and pd.isna(v):
            return None
        return v

    report_file = output_dir / f"国家队持仓分析_汇总_{timestamp}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    print(f"💾 汇总报告已保存: {report_file}")

    print("\n✅ 完成！")


if __name__ == "__main__":
    main()
