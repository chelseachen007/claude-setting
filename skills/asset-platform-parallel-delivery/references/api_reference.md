# 系统菜单接口参考

## 适用范围

用于资产管理平台中通过 `icfs-member` 菜单管理接口新增前端菜单。只在用户明确要求写入菜单时执行；只读查询优先于写入。

## 接口

常见地址：

```text
GET  /icfsboot/icfs-member/admin/menu/get?menuCode=<menuCode>&_t=<timestamp>
POST /icfsboot/icfs-member/admin/menu/add
```

实际 host、租户和认证方式以用户当前环境为准，不把 host、JWT 或签名值写入代码、Skill、日志或提交记录。

## 查询流程

1. 查询父菜单，确认 `menuCode`、`subSystemCode`、`appCode` 和已有子菜单信息。
2. 查询拟新增编码，若返回成功且已有记录，停止并报告冲突；不要重复新增。
3. 选择用户指定或项目既有的编码规则，不能凭空修改已有菜单编码。

查询成功的关键字段通常包括：

```json
{
  "menuCode": "60000100",
  "subSystemCode": "fund",
  "menuName": "账户中心",
  "parentCode": "fund",
  "appCode": "payment"
}
```

## 新增 payload

按项目现有菜单页面的字段结构发送，至少确认这些字段：

```json
{
  "parentCode": "60000100",
  "menuCode": "60000103",
  "menuName": "交易明细",
  "parentId": "60000100",
  "subSystemCode": "fund",
  "menuArg": "",
  "menuIcon": "",
  "menuUrl": "/payment/account/transaction",
  "remark": "",
  "kindCode": "",
  "kindType": "",
  "windowType": "",
  "menuPluginName": "",
  "menuPluginDll": "",
  "appCode": "payment",
  "isHidden": "0",
  "isKeepAlivea": "1",
  "parentName": "",
  "orderNo": 2,
  "subtrans": []
}
```

字段应根据当前父菜单和用户需求替换。`subSystemCode` 是容易漏传的必填字段；接口返回“不能为空”时先核对必填字段，不要盲目重试。

## 签名

客户端已有 `src/utils/encryption/signMd5Utils.js`，应直接复用它的规则。一般请求头包括：

```text
Authorization: <当前会话凭证>
X-Access-Token: <当前会话凭证>
X-Sign: <项目签名工具计算值>
X-TIMESTAMP: <当前毫秒时间戳>
X-Tenant-Id: <当前租户>
X-Version: v3
```

签名注意事项：

- 签名输入要与最终 URL 查询参数和 JSON body 完全一致。
- 数字、布尔值的转换规则以项目签名工具为准。
- `_t` 通常不参与签名，不能自行推断；以项目工具实现为准。
- 不要手写或复制签名密钥；不要把认证头保存到文件。
- 如果签名校验失败，打印脱敏后的字段名和请求结构，重新核对序列化、字段遗漏和时间戳，不输出 token/secret。

## 回查与结果判断

新增接口返回 `code: 200` 只说明写入请求成功，还必须用 `menu/get` 回查目标编码，确认：

- `menuCode` 正确
- `menuName` 正确
- `parentCode` 指向目标父菜单
- `menuUrl` 与客户端路由一致
- `appCode`、`subSystemCode` 与目标端一致
- `isHidden` 和排序符合预期

若回查失败，报告接口响应和下一步，不重复提交可能造成重复菜单。
