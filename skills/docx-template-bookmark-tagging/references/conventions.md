# 实测约定（金鼎担保类 / 审查意见类）

来源：`/Users/chenjie/Documents/work/AI/智能模板/template 2/`

## 书签

```xml
<w:p><w:pPr>…</w:pPr><w:bookmarkStart w:id="104" w:name="issuerLtBsLdzc"/><w:bookmarkEnd w:id="104"/></w:p>
```

- 零长度、无文字，紧跟在 `</w:pPr>` 之后
- 书签名 == JSON 的 code
- 现有 `_GoBack` 书签是 Word 自己加的，不算字段

## 键值表（json 里 `"render": "2"`）

```
R0: [申请人]  [<书签 applicantApplicant>]
R1: [规模分类] [<书签 scaleClassification>]
```
- 标签格：可见文字，无书签
- 值格：只有书签
- 表锚点（= 表 code，如 `customerInfo`）**必须独占一个空行**，挂在该行 C0；
  这一行紧贴在字段定义行之前、表头行之后
  - ⚠️ **不要图省事把锚点塞进表头行**！渲染引擎会把「含锚点的那一行」当成数据行，
    直接用值覆盖 → **表头被吃掉**（金鼎审查意见类踩过这个坑）
  - 若原表没有这样一行，**必须克隆字段行插一个空行**，不能借用表头行

## 网格表（json 里无 `render`）

```
R0: [序号][公司名称][关联关系][注册资本][持股比例]     ← 表头，可见文字，无书签
R1: [<书签 basicInfoMergerTheIssuer>][][][][]        ← 表锚点行，C0 挂表 code
R2: [<书签 subsidiarySerialNumber>][<书签 subsidiaryCompanyName>]…  ← 列定义行
R3: [][][][][]                                        ← 空数据行
```
- 数据行由回填系统按列定义追加

## 字段分类 json

- **不含**表本身的 code，只含叶子字段
- 表内字段 `desc` = `父级desc-子级desc`，如 `整体授信方案概要-申请人`
- 6 个字段：`code` / `desc` / `category` / `field_type` / `hint_doc_types` / `narrative_cells`

## 担保类实测规模

- `担保类尽调报告.docx`：1180 个书签（含 `_Hlk*` 与 `_GoBack`）
- `担保类模板书签json文档.json`：82 条顶层（37 表型 + 45 叙述型）
- `担保类模板字段分类.json`：1133 条叶子字段
