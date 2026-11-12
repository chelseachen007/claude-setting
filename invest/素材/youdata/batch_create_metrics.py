"""
网易有数 - 批量创建原子指标
用法:
  python3 batch_create_metrics.py                # dry-run，只输出请求 JSON
  python3 batch_create_metrics.py --execute      # 真正执行创建
  python3 batch_create_metrics.py --execute --start 50 --end 60  # 指定范围
"""
import csv
import json
import sys
import time
import requests

# ========== 配置 ==========
MAPPING_CSV = "/Users/chenjie/Documents/study/github/Obsidian/投资研究/youdata/indicator_mapping_v2.csv"
FIELDS_JSON = "/Users/chenjie/Documents/study/github/Obsidian/投资研究/youdata/models_fields.json"
LOG_FILE = "/Users/chenjie/Documents/study/github/Obsidian/投资研究/youdata/batch_create_log.json"

BASE = "https://bi.qtjsjt.cn"
COOKIES = {
    "YOUDATA.sameSite": "1",
    "model_token": "83747535a0cc4c1880b999d30f198e6d",
    "SESSION_YOUDATA": "ydsession-9a4878d4-a60e-4129-be74-5f4ba30ce505",
    "SESSION_YOUDATA.sig": "-m9kz64T28jHx7G8221-vVcJ35A",
    "YDNESIO": "8146b7a22ffb4340da60fa8027b26c7ad29b7c91",
}
HEADERS = {
    "accept": "application/json",
    "content-type": "application/json",
    "x-csrf-token": "600108000",
    "x-time-zone": "8",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "referer": f"{BASE}/dash/metrics/5",
}
PROJECT_ID = 5
# ========== 配置结束 ==========

# 业务域 → 指标目录 folderId 映射（type=21）
DOMAIN_FOLDER_MAP = {
    "党群人力": 45,   # 人力
    "人力": 45,
    "建管中心": 46,   # 工程
    "工程": 46,
    "成本管理": 48,   # 成本
    "招采成本": 48,
    "财务": 49,       # 需要确认，或用 0 (公共文件夹)
    "投资发展": 47,   # 资产
    "风控法务": 0,
    "客商": 0,
}

# CSV 时间周期 → dataPeriod 映射
PERIOD_MAP = {
    "时点": "day",
    "时点值": "day",
    "日": "day",
    "月": "month",
    "年": "year",
    "季": "quarter",
    "本年": "year",
    "年、月": "month",
    "年、季、月": "month",
    "年累计": "year",
    "月累计": "month",
    "年累计、月累计": "month",
}

# 加载模型字段
with open(FIELDS_JSON, "r", encoding="utf-8") as f:
    MODELS_DATA = json.load(f)


def get_field_meta(model_id, field_id):
    """从模型字段字典中获取完整字段元数据"""
    m = MODELS_DATA.get(str(model_id), {})
    # 先找度量
    for me in m.get("measures", []):
        if me.get("fieldId") == field_id:
            return {
                "$type": "Measure",
                "role": "Measure",
                "fieldId": field_id,
                "interpretation": "Continuous",
                "dataType": me.get("dataType", "Decimal"),
                "field": me.get("field", ""),
                "alias": me.get("alias", ""),
                "tableId": me.get("tableId", 1),
                "logicalTableId": me.get("logicalTableId", 1),
                "partition": False,
                "indexed": False,
                "defaultAggregator": me.get("defaultAggregator", "SUM"),
            }
    # 再找维度（COUNT 模式）
    for d in m.get("dimensions", []):
        if d.get("fieldId") == field_id:
            return {
                "$type": "Dimension",
                "role": "Dimension",
                "fieldId": field_id,
                "interpretation": d.get("interpretation", "Discrete"),
                "dataType": d.get("dataType", "String"),
                "field": d.get("field", ""),
                "alias": d.get("alias", ""),
                "tableId": d.get("tableId", 1),
                "logicalTableId": d.get("logicalTableId", 1),
                "partition": False,
                "indexed": False,
                "defaultAggregator": "CNT",
            }
    return None


def get_date_dimension(model_id):
    """从模型中获取最佳日期维度字段"""
    m = MODELS_DATA.get(str(model_id), {})
    dims = m.get("dimensions", [])
    # 优先选 "报告日期"
    for d in dims:
        if d.get("alias") == "报告日期":
            return d
    # 其次选 DateTime 类型
    for d in dims:
        if d.get("dataType") == "DateTime":
            return d
    # 再选含 convertArg (String 但可转 Date) 的
    for d in dims:
        if d.get("convertArg"):
            return d
    # 最后选含 "日期" 或 "时间" 的
    for d in dims:
        alias = d.get("alias", "")
        if any(kw in alias for kw in ["日期", "时间", "date"]):
            return d
    return None


def build_date_dimension(dim_info):
    """构建 dateDimension 对象"""
    if not dim_info:
        return None
    table_name = dim_info.get("tableName", "")
    if not table_name:
        # 从模型的 tables 中获取
        # 用第一个表名
        pass
    return {
        "$type": "Dimension",
        "role": "Dimension",
        "fieldId": dim_info.get("fieldId", ""),
        "interpretation": "Discrete",
        "dataType": dim_info.get("dataType", "String"),
        "field": dim_info.get("field", ""),
        "alias": dim_info.get("alias", ""),
        "tableId": dim_info.get("tableId", 1),
        "tableName": table_name,
        "mapFunction": "YEAR-MONTH-DAY",
        "granularity": "g0",
        "logicalTableId": dim_info.get("logicalTableId", 1),
        "bigtable": False,
        "partition": False,
    }


def build_request_body(row):
    """根据映射行构建 API 请求体"""
    name = row["指标中文名称"]
    name_en = row.get("指标英文名称", "")
    model_id = int(row["dataModelId"]) if row["dataModelId"] else 0
    field_id = row["fieldId"]
    aggregator = row["aggregator"] or "SUM"
    caliber = row.get("业务口径全文", "") or row.get("业务口径摘要", "")
    domain = row.get("业务域", "")
    period_text = row.get("时间周期", "")

    if not model_id or not field_id:
        return None

    # 获取字段元数据
    field_meta = get_field_meta(model_id, field_id)
    if not field_meta:
        return None

    # 设置聚合方式：Dimension 字段强制用 CNT
    if field_meta.get("$type") == "Dimension":
        field_meta["aggregator"] = "CNT"
    else:
        field_meta["aggregator"] = aggregator

    # 获取日期维度
    date_dim_info = get_date_dimension(model_id)
    date_dimension = build_date_dimension(date_dim_info)

    # 映射 dataPeriod
    data_period = "day"
    for key, val in PERIOD_MAP.items():
        if key in period_text:
            data_period = val
            break

    # 获取 folderId
    folder_id = 0
    for key, fid in DOMAIN_FOLDER_MAP.items():
        if key in domain:
            folder_id = fid
            break

    # 构建请求体
    body = {
        "projectId": PROJECT_ID,
        "name": name,
        "nameEn": name_en,
        "dataModelId": model_id,
        "folderId": folder_id,
        "enableChatBi": 1,
        "enableMetricExploration": 0,
        "type": "Existed",
        "setting": {
            "field": field_meta,
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
                            "mode": {
                                "$type": "RelativeTime",
                                "count": 1,
                                "unit": "month",
                                "anchor": 0,
                            },
                        },
                    },
                    "dimensionsGroup": [],
                },
                "planActualSetting": {"enable": False},
            },
            "customAttributes": [],
        },
        "caliber": caliber,
        "publishRelatedId": None,
        "parameterList": [],
    }

    # 加入日期维度和周期
    if date_dimension:
        body["setting"]["dateDimension"] = date_dimension
    body["setting"]["dataPeriod"] = data_period

    return body


def create_metric(body):
    """调用创建接口"""
    resp = requests.post(
        f"{BASE}/api/dash/metrics/add?trigger=User",
        json=body,
        cookies=COOKIES,
        headers=HEADERS,
        timeout=30,
    )
    return resp.json()


def main():
    # 解析参数
    execute = "--execute" in sys.argv
    start_idx = 0
    end_idx = 9999
    for i, arg in enumerate(sys.argv):
        if arg == "--start" and i + 1 < len(sys.argv):
            start_idx = int(sys.argv[i + 1])
        if arg == "--end" and i + 1 < len(sys.argv):
            end_idx = int(sys.argv[i + 1])

    # 加载映射表
    with open(MAPPING_CSV, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    # 只处理原子指标
    atomic = [r for r in rows if r["指标类型"] == "原子指标" and r["fieldId"]]
    print(f"原子指标（已匹配字段）: {len(atomic)} 条")

    if execute:
        print(">>> 执行模式：将真正调用 API 创建指标")
    else:
        print(">>> 预览模式：只输出请求 JSON，加 --execute 执行")

    # 加载已有日志（支持断点续跑）
    log = []
    created_names = set()
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            log = json.load(f)
            created_names = {l["name"] for l in log if l.get("success")}
            print(f"已有日志: {len(log)} 条记录, {len(created_names)} 已创建")
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    success = 0
    fail = 0
    skip = 0

    for idx, row in enumerate(atomic):
        if idx < start_idx or idx >= end_idx:
            continue

        name = row["指标中文名称"]

        # 跳过已创建的
        if name in created_names:
            skip += 1
            continue

        body = build_request_body(row)
        if not body:
            print(f"[{idx}] SKIP {name} - 无法构建请求体")
            log.append({"idx": idx, "name": name, "success": False, "error": "无法构建请求体"})
            fail += 1
            continue

        if not execute:
            # 预览模式：打印第一条的 JSON
            if idx == start_idx:
                print(f"\n--- 预览 [{idx}] {name} ---")
                print(json.dumps(body, ensure_ascii=False, indent=2)[:2000])
                print("...\n")
            print(f"[{idx}] {name} → model={body['dataModelId']} field={body['setting']['field']['fieldId']}({body['setting']['field']['aggregator']}) folder={body['folderId']} period={body['setting']['dataPeriod']}")
            continue

        # 执行创建
        try:
            result = create_metric(body)
            code = result.get("code")
            metric_id = result.get("result")
            if code == 200:
                print(f"[{idx}] ✓ {name} → id={metric_id}")
                log.append({"idx": idx, "name": name, "metric_id": metric_id, "success": True})
                success += 1
            else:
                msg = result.get("message", "未知错误")
                print(f"[{idx}] ✗ {name} → code={code} {msg}")
                log.append({"idx": idx, "name": name, "success": False, "error": f"code={code} {msg}"})
                fail += 1
        except Exception as e:
            print(f"[{idx}] ✗ {name} → {e}")
            log.append({"idx": idx, "name": name, "success": False, "error": str(e)})
            fail += 1

        # 每条之间间隔，避免限流
        time.sleep(0.5)

        # 每 10 条保存一次日志
        if (success + fail) % 10 == 0:
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                json.dump(log, f, ensure_ascii=False, indent=2)

    # 保存最终日志
    if execute:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=2)
        print(f"\n=== 完成 ===")
        print(f"成功: {success}")
        print(f"失败: {fail}")
        print(f"跳过(已存在): {skip}")
        print(f"日志: {LOG_FILE}")
    else:
        print(f"\n=== 预览完成，共 {len(atomic)} 条 ===")
        print(f"跳过(已创建): {skip}")
        print(f"加 --execute 执行创建")


if __name__ == "__main__":
    main()
