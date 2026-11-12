"""
网易有数 - 批量扫描所有数据模型的字段信息
输出: models_fields.json (模型ID → 字段列表)
"""
import json
import time
import requests

BASE = "https://bi.qtjsjt.cn"
COOKIES = {
    "YOUDATA.sameSite": "1",
    "model_token": "83747535a0cc4c1880b999d30f198e6d",
    "SESSION_YOUDATA": "ydsession-9a4878d4-a60e-4129-be74-5f4ba30ce505",
    "SESSION_YOUDATA.sig": "-m9kz64T28jHx7G8221-vVcJ35A",
    "YDNESIO": "8146b7a22ffb4340da60fa8027b26c7ad29b7c91",
}
HEADERS = {
    "accept": "*/*",
    "x-csrf-token": "600108000",
    "x-time-zone": "8",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "referer": f"{BASE}/dash/metrics/5",
}


def get_model_list():
    """获取所有数据模型列表"""
    resp = requests.get(
        f"{BASE}/api/dash/folder/list",
        params={
            "trigger": "User", "projectId": 5, "type": 1,
            "needComponent": "false", "refresh": "false",
            "mobile": "false", "noEmptyFolder": "false",
            "ignoreVirtualFolder": "true", "needFieldAlias": "false",
            "needAllList": "false", "buildUserPermission": "true",
            "category": 0, "sort": "title:1",
        },
        cookies=COOKIES, headers=HEADERS,
    )
    data = resp.json()

    models = []

    def extract(folders, path=""):
        for f in folders:
            cur = f"{path}/{f['name']}" if path else f["name"]
            for item in f.get("items", []):
                models.append({
                    "id": item["id"],
                    "title": item["title"],
                    "folderId": item.get("folderId"),
                    "path": cur,
                })
            extract(f.get("folders", []), cur)

    extract(data.get("result", {}).get("folders", []))
    return models


def get_model_fields(model_id):
    """获取模型的字段信息（通过 metrics/get 接口获取完整 pivotSchema）"""
    # 用 metrics/get 获取关联此模型的指标，从中提取 dataModel 的 pivotSchema
    # 先尝试直接 dataModel/get
    resp = requests.get(
        f"{BASE}/api/dash/dataModel/get",
        params={"trigger": "User", "id": model_id},
        cookies=COOKIES, headers=HEADERS,
    )
    data = resp.json()
    result = data.get("result", {})

    fields = {"dimensions": [], "measures": []}

    # 从 pivotSchema 提取
    schema = result.get("pivotSchema", {})
    for d in schema.get("dimensions", []):
        fields["dimensions"].append({
            "fieldId": d.get("fieldId"),
            "field": d.get("field"),
            "alias": d.get("alias", d.get("field", "")),
            "dataType": d.get("dataType"),
            "role": d.get("role"),
            "tableId": d.get("tableId"),
            "logicalTableId": d.get("logicalTableId"),
            "tableName": d.get("tableName"),
            "$type": d.get("$type"),
        })
    for m in schema.get("measures", []):
        fields["measures"].append({
            "fieldId": m.get("fieldId"),
            "field": m.get("field"),
            "alias": m.get("alias", m.get("field", "")),
            "dataType": m.get("dataType"),
            "role": m.get("role"),
            "tableId": m.get("tableId"),
            "logicalTableId": m.get("logicalTableId"),
            "tableName": m.get("tableName"),
            "$type": m.get("$type"),
            "defaultAggregator": m.get("defaultAggregator"),
        })

    # 从 config.tables 获取表名
    config = result.get("config", {})
    tables_info = []
    for t in config.get("tables", []):
        for st in t.get("tables", []):
            tables_info.append({
                "tableId": st.get("tableId"),
                "tableName": st.get("tableAlias") or st.get("tableName"),
            })

    return {
        "modelId": model_id,
        "modelName": result.get("title", ""),
        "tables": tables_info,
        "fields": fields,
    }


def main():
    print("=== 获取模型列表 ===")
    models = get_model_list()
    print(f"共 {len(models)} 个模型\n")

    all_fields = {}
    for i, m in enumerate(models):
        mid = m["id"]
        print(f"[{i+1}/{len(models)}] {m['title']} (id={mid}, path={m['path']})")
        try:
            info = get_model_fields(mid)
            dims = len(info["fields"]["dimensions"])
            meas = len(info["fields"]["measures"])
            print(f"  → {dims} 维度, {meas} 度量")
            all_fields[mid] = {
                "id": mid,
                "title": m["title"],
                "path": m["path"],
                "folderId": m["folderId"],
                "tables": info["tables"],
                "dimensions": info["fields"]["dimensions"],
                "measures": info["fields"]["measures"],
            }
        except Exception as e:
            print(f"  → ERROR: {e}")
            all_fields[mid] = {"id": mid, "title": m["title"], "path": m["path"], "error": str(e)}
        time.sleep(0.3)

    output = "/Users/chenjie/Documents/study/github/Obsidian/投资研究/youdata/models_fields.json"
    with open(output, "w", encoding="utf-8") as f:
        json.dump(all_fields, f, ensure_ascii=False, indent=2)
    print(f"\n=== 已保存到 {output} ===")


if __name__ == "__main__":
    main()
