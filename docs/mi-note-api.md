# Mi Note Todo API 逆向文档

> 通过 Chrome DevTools Protocol 抓包分析，日期: 2026-05-02

## 概览

小米云笔记的 Web 前端 (`https://i.mi.com/note/`) 通过 REST API 与后端通信。
所有 API 的 base URL 为 `https://i.mi.com/`。

### 认证方式

- **Cookie-based**: 浏览器自动携带 Cookie，无需额外 Authorization header
- **serviceToken**: 需要同时在请求体 (body) 中传递，值从 Cookie `serviceToken` 中读取
- 关键 Cookie:
  - `serviceToken` (domain: `.mi.com`) — 主认证 token
  - `userId` (domain: `.mi.com`) — 用户 ID
  - `i.mi.com_isvalid_servicetoken` (domain: `.mi.com`) — token 有效性标记
  - `i.mi.com_slh` (domain: `.i.mi.com`)
  - `i.mi.com_ph` (domain: `.i.mi.com`)

### Content-Type

所有 POST 请求使用:
```
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
```

前端使用 `qs.stringify()` 序列化请求体（不是 JSON）。

### 通用响应格式

```json
{
  "result": "ok" | "error",
  "code": 0,
  "data": { ... },
  "description": "成功",
  "ts": 1777645831899,
  "retriable": false
}
```

错误码:
- `0` — 成功
- `10008` — record invalid / entity content is empty
- `10016` — record 不能为空 / 缺失必选参数

---

## 已验证的读取 API

### 1. 获取全部 Todo 记录

```
GET /todo/v1/user/records?syncToken={}&limit=200
```

**请求示例:**
```
GET https://i.mi.com/todo/v1/user/records?syncToken=%7B%7D&limit=200&ts=1777645831899
Cookie: serviceToken=xxx; userId=2968547766; ...
```

**URL 参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| `syncToken` | string (JSON) | 同步令牌，首次传 `{}`，后续用上次返回的值 |
| `limit` | number | 每页条数，通常 200 |
| `ts` | number | 时间戳 `Date.now()` |

**响应示例:**
```json
{
  "result": "ok",
  "code": 0,
  "data": {
    "syncToken": {
      "syncExtraInfo": "FgAWgMCIqfaj1C-G7MaDjxYCyAEcEhaAwIip9qPULxwAAAA",
      "watermark": "13414659035041793"
    },
    "records": [
      {
        "contentJson": {
          "assets": [],
          "entity": {
            "serverStatus": 0,
            "lastModifiedTime": 1777548211208,
            "source": 0,
            "localStatus": 0,
            "listType": 0,
            "content": "llmwiki gbrain",
            "syncId": "13414659035041792",
            "remindTime": 0,
            "syncEtag": 0,
            "contentSHA1": "ebfbf0d1bbdb54849732f3a9b64477202b58bedd",
            "markFinishTime": 0,
            "remindRepeatType": 0,
            "hideType": 0,
            "plainText": "llmwiki gbrain",
            "inputType": 0,
            "colorLabel": 0,
            "id": 75,
            "firstRemindTime": 0,
            "audioFileField": "",
            "audioFileSize": 0,
            "audioFileName": "",
            "isFinish": 0,
            "folderId": 0,
            "expireTime": 0,
            "createTime": 1777548211207,
            "is_finish": false,
            "customSortId": 59768832,
            "remindType": 0
          }
        },
        "eTag": "13414659035041792",
        "id": "13414659035041792",
        "type": "entity",
        "status": "normal"
      }
    ],
    "hasMore": false
  }
}
```

**记录类型说明:**
| `type` 值 | 说明 |
|-----------|------|
| `"entity"` | Todo 条目 |
| `"folder"` | 文件夹/排序记录 (id=0) |

### 2. 获取单条记录

```
GET /todo/v1/user/records/{id}
```

**请求示例:**
```
GET https://i.mi.com/todo/v1/user/records/13414659035041792?ts=1777645850977
Cookie: serviceToken=xxx; ...
```

**响应示例:**
```json
{
  "result": "ok",
  "code": 0,
  "data": {
    "record": { ... },
    "purged": false,
    "existed": true
  }
}
```

### 3. 获取文件夹排序记录 (id=0)

```
GET /todo/v1/user/records/0?ts=...
```

返回包含排序顺序的 folder 记录:

```json
{
  "result": "ok",
  "code": 0,
  "data": {
    "record": {
      "contentJson": {
        "folder": { "syncId": 0 },
        "sort": {
          "eTag": "13414659068727360",
          "orders": [
            "13414659035041792",
            "13410052894752768",
            "13404993250394112"
          ]
        }
      },
      "eTag": 0,
      "id": 0,
      "type": "folder",
      "status": "normal"
    }
  }
}
```

`orders` 数组中的 ID 即为 todo 的排序顺序（从上到下）。

### 4. 笔记同步

```
GET /note/v2/sync/full/?ts=...&data={"note_view":{"syncTag":""}}&inactiveTime=10
```

**响应示例:**
```json
{
  "result": "ok",
  "code": 0,
  "data": {
    "note_view": {
      "result": "ok",
      "code": 0,
      "data": {
        "entries": [],
        "folders": [],
        "syncTag": ""
      }
    }
  }
}
```

---

## Todo 记录数据模型

### TodoItem (type="entity") 完整字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 雪花 ID，如 `"13414659035041792"` |
| `type` | string | 固定 `"entity"` |
| `status` | string | `"normal"` 正常 |
| `eTag` | string | 乐观锁版本号，通常等于 id |
| `contentJson.assets` | array | 附件，通常 `[]` |
| `contentJson.entity.content` | string | **Todo 标题内容** |
| `contentJson.entity.plainText` | string | 纯文本，通常同 content |
| `contentJson.entity.isFinish` | number | `0`=未完成, `1`=已完成 |
| `contentJson.entity.is_finish` | boolean | 同上，布尔版本 |
| `contentJson.entity.folderId` | number | 文件夹 ID，默认 `0` |
| `contentJson.entity.syncId` | string | 同步 ID，等于记录 id |
| `contentJson.entity.createTime` | number | 创建时间戳 (ms) |
| `contentJson.entity.lastModifiedTime` | number | 最后修改时间戳 (ms) |
| `contentJson.entity.remindTime` | number | 提醒时间，`0`=无提醒 |
| `contentJson.entity.remindType` | number | 提醒类型 |
| `contentJson.entity.remindRepeatType` | number | 重复提醒类型 |
| `contentJson.entity.contentSHA1` | string | 内容 SHA1 校验 |
| `contentJson.entity.customSortId` | number | 自定义排序 ID |
| `contentJson.entity.listType` | number | `0`=普通, `1`=带子任务 |
| `contentJson.entity.inputType` | number | 输入类型 |
| `contentJson.entity.colorLabel` | number | 颜色标签 |
| `contentJson.entity.hideType` | number | 隐藏类型 |
| `contentJson.entity.source` | number | 来源 |
| `contentJson.entity.serverStatus` | number | 服务端状态 |
| `contentJson.entity.localStatus` | number | 本地状态 |
| `contentJson.entity.audioFileField` | string | 音频文件 |
| `contentJson.entity.audioFileName` | string | 音频文件名 |
| `contentJson.entity.audioFileSize` | number | 音频文件大小 |
| `contentJson.entity.expireTime` | number | 过期时间 |
| `contentJson.entity.firstRemindTime` | number | 首次提醒时间 |
| `contentJson.entity.markFinishTime` | number | 标记完成时间 |

### 带子任务的 Todo (listType=1)

`content` 字段是 JSON 字符串:
```json
{
  "isExpand": true,
  "subTodoEntities": [
    { "content": "子任务1", "isFinish": false },
    { "content": "子任务2", "isFinish": false }
  ],
  "title": "购物清单"
}
```

---

## 已验证的写操作 API

> 通过 Selenium performance log 抓取的真实 CRUD 请求体。

### 1. 创建 Todo

```
POST /todo/v1/user/records
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
```

**请求体 (URL-decoded):**
```
record={"type":"entity","contentJson":{"listType":0,"content":"__SEL_CREATE__","plainText":"__SEL_CREATE__","isFinish":0,"markFinishTime":0,"remindType":0,"remindRepeatType":0,"remindTime":0,"firstRemindTime":0,"audioFileField":"","audioFileName":"","audioFileSize":0,"createTime":1777652264627,"lastModifiedTime":1777652264627,"inputType":0,"id":79,"customSortId":63963136,"expireTime":0,"hideType":0,"folderId":0,"colorLabel":0,"source":0,"localStatus":0,"serverStatus":0,"is_finish":false,"assets":[]}}&serviceToken=xxx
```

**record 字段解析:**
```json
{
  "type": "entity",
  "contentJson": {
    "listType": 0,
    "content": "todo 标题",
    "plainText": "todo 标题",
    "isFinish": 0,
    "markFinishTime": 0,
    "remindType": 0,
    "remindRepeatType": 0,
    "remindTime": 0,
    "firstRemindTime": 0,
    "audioFileField": "",
    "audioFileName": "",
    "audioFileSize": 0,
    "createTime": 1777652264627,
    "lastModifiedTime": 1777652264627,
    "inputType": 0,
    "id": 79,
    "customSortId": 63963136,
    "expireTime": 0,
    "hideType": 0,
    "folderId": 0,
    "colorLabel": 0,
    "source": 0,
    "localStatus": 0,
    "serverStatus": 0,
    "is_finish": false,
    "assets": []
  }
}
```

**关键发现 — 与之前手动构造的区别:**

| 字段 | 手动构造 | 真实请求 |
|------|---------|---------|
| `contentJson` 结构 | `{assets:[], entity:{...}}` | `{listType:0, content:"...", ...}` (扁平!) |
| `entity` 嵌套 | 有 `entity` 层 | **没有 `entity` 层!** 字段直接在 `contentJson` 下 |
| `id` (record 级) | `"0"` | **无 id 字段** |
| `eTag` (record 级) | 无 | **无 eTag 字段** |
| `status` (record 级) | `"normal"` | **无 status 字段** |
| `contentJson.id` | 无 | 有，自增计数器 (79) |
| `contentJson.customSortId` | 无 | 有 |
| `contentJson.createTime` | 无 | 有 |
| `contentJson.lastModifiedTime` | 无 | 有 |
| `contentJson.assets` | `[]` 在外层 | 在 `contentJson` 内部 |

> **这就是之前手动调用失败的原因!** 真实的 `contentJson` 是扁平结构，
> 所有字段直接在 `contentJson` 下，没有嵌套的 `entity` 层。
> 而读取 API 返回的数据有 `entity` 嵌套——读写结构不对称。

### 2. 更新排序 (创建后自动触发)

```
POST /todo/v1/user/records/0/update
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
```

创建 todo 后，前端自动更新排序记录 (id=0):

```
previousETag=0&record={"type":"sort","id":0,"eTag":0,"contentJson":{"eTag":"13421471030640704","orders":["13421478085263616","13421463044882656",...]}}&serviceToken=xxx
```

- `type: "sort"` — 排序记录
- `contentJson.orders` — todo ID 的排序数组（新 ID 在最前面）

### 3. 更新 Todo 标题

```
POST /todo/v1/user/records/{id}/update
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
```

**请求体 (URL-decoded):**
```
previousETag=13421478085263616&record={"id":"13421478085263616","eTag":"13421478085263616","type":"entity","contentJson":{"assets":[],"serverStatus":0,"lastModifiedTime":1777652266718,"source":0,"listType":0,"localStatus":0,"content":"__SEL_UPDATED__","syncId":"13421478085263616","remindTime":0,"markFinishTime":0,"remindRepeatType":0,"hideType":0,"plainText":"__SEL_UPDATED__","inputType":0,"id":79,"colorLabel":0,"firstRemindTime":0,"audioFileField":"","audioFileName":"","audioFileSize":0,"isFinish":0,"folderId":0,"expireTime":0,"createTime":1777652264627,"is_finish":false,"customSortId":63963136,"remindType":0}}&serviceToken=xxx
```

**与创建的区别:**
- record 级别有 `id`, `eTag`, `type` 字段
- `contentJson` 结构变为**嵌套**格式: 有 `assets`, `serverStatus` 等在外层，但**无 `entity` 嵌套**
- `contentJson.syncId` 等于 record 的 `id`
- `previousETag` 等于 record 的 `eTag`（用于乐观锁）

### 4. 完成 Todo (isFinish=1)

```
POST /todo/v1/user/records/{id}/update
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
```

**请求体关键字段差异 (与更新标题对比):**
```json
{
  "eTag": "13421478222495744",
  "previousETag": "13421478222495744",
  "contentJson": {
    "isFinish": 1,
    "is_finish": false,
    "markFinishTime": 1777652271745,
    "lastModifiedTime": 1777652271745
  }
}
```

| 字段 | 未完成 | 已完成 |
|------|--------|--------|
| `contentJson.isFinish` | `0` | `1` |
| `contentJson.is_finish` | `false` | **`false`** (未变!) |
| `contentJson.markFinishTime` | `0` | 完成时间戳 |
| `contentJson.lastModifiedTime` | 创建时间 | 完成时间戳 |

> 注意: `is_finish` 在更新请求中保持 `false`，只有 `isFinish` 变为 `1`。
> 完成操作也会触发排序记录更新 (从 orders 中移除该 ID)。

### 5. 恢复 Todo (isFinish=0，取消完成)

```
POST /todo/v1/user/records/{id}/update
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
```

**请求体 (完整):**
```
previousETag=13430178689449984&record={"id":"13430178558574848","eTag":"13430178689449984","type":"entity","contentJson":{"assets":[],"serverStatus":0,"lastModifiedTime":1777785030571,"source":0,"listType":0,"localStatus":0,"content":"__RESTORE_TEST__","syncId":"13430178558574848","remindTime":0,"markFinishTime":0,"remindRepeatType":0,"hideType":0,"plainText":"__RESTORE_TEST__","inputType":0,"id":86,"colorLabel":0,"firstRemindTime":0,"audioFileField":"","audioFileName":"","audioFileSize":0,"isFinish":0,"folderId":0,"expireTime":0,"createTime":1777785023521,"is_finish":false,"customSortId":60817408,"remindType":0}}&serviceToken=xxx
```

**record (parsed):**
```json
{
  "id": "13430178558574848",
  "eTag": "13430178689449984",
  "type": "entity",
  "contentJson": {
    "assets": [],
    "serverStatus": 0,
    "lastModifiedTime": 1777785030571,
    "source": 0,
    "listType": 0,
    "localStatus": 0,
    "content": "__RESTORE_TEST__",
    "syncId": "13430178558574848",
    "remindTime": 0,
    "markFinishTime": 0,
    "remindRepeatType": 0,
    "hideType": 0,
    "plainText": "__RESTORE_TEST__",
    "inputType": 0,
    "id": 86,
    "colorLabel": 0,
    "firstRemindTime": 0,
    "audioFileField": "",
    "audioFileName": "",
    "audioFileSize": 0,
    "isFinish": 0,
    "folderId": 0,
    "expireTime": 0,
    "createTime": 1777785023521,
    "is_finish": false,
    "customSortId": 60817408,
    "remindType": 0
  }
}
```

**与完成操作的关键区别:**

| 字段 | 完成 (complete) | 恢复 (restore) |
|------|----------------|----------------|
| `contentJson.isFinish` | `1` | **`0`** |
| `contentJson.markFinishTime` | 完成时间戳 | **`0`** |
| `contentJson.lastModifiedTime` | 完成时间戳 | 恢复时间戳 |

> 恢复操作与完成操作使用同一个 API 端点，仅改变 `isFinish` 和 `markFinishTime`。
> 恢复后同样触发排序记录更新 (`POST /todo/v1/user/records/0/update`)，将 todo ID 重新加入 `orders` 数组（置于最前）。

### 6. 搜索

**搜索是纯前端过滤，不触发任何 API 请求。**

前端在搜索时：
1. 已通过 `GET /todo/v1/user/records` 加载了全部数据
2. 用户在搜索框输入关键词时，前端直接在内存中过滤
3. 不会发送任何新的 GET 或 POST 请求

> 轻量化 driver 实现搜索功能时，只需在本地对已获取的记录列表做文本匹配即可。

### 7. 删除 Todo

```
POST /todo/v1/user/records/{id}/delete
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
```

**请求体:**
```
prevETag=13421478551683136&serviceToken=xxx
```

- 参数名为 `prevETag`（不是 `previousETag`）
- 只需要 `prevETag` 和 `serviceToken`，无 record 体

---

## HTTP 客户端 (`iR4f` 模块) 的 POST 处理逻辑

```javascript
// j 函数对 POST 请求的处理:
if (method === 'POST') {
    if (isPlainObject(body)) {
        headers['content-type'] = 'application/x-www-form-urlencoded; charset=UTF-8';
        body.serviceToken = getCookie('serviceToken');  // 自动追加 serviceToken
        body = qs.stringify(body);                       // URL 编码
    }
}
```

## 读写结构不对称

| 操作 | contentJson 结构 |
|------|-----------------|
| **读取** (GET response) | `{assets:[], entity: {content: "...", ...}}` — 有 `entity` 嵌套 |
| **创建** (POST body) | `{listType:0, content:"...", assets:[], ...}` — **扁平，无 `entity`** |
| **更新** (POST body) | `{assets:[], serverStatus:0, content:"...", ...}` — **扁平，无 `entity`** |

> 读取时 `contentJson.entity` 是一个嵌套对象；写入时所有字段直接在 `contentJson` 下。
> 这意味着从读取结果构造更新请求时，需要将 `entity` 的字段提升到 `contentJson` 级别。

## API 覆盖完整清单

| # | Driver 操作 | API 端点 | 验证状态 |
|---|------------|---------|---------|
| 1 | 读取全部 Todo | `GET /todo/v1/user/records` | ✅ 已验证 |
| 2 | 读取单条记录 | `GET /todo/v1/user/records/{id}` | ✅ 已验证 |
| 3 | 读取排序记录 | `GET /todo/v1/user/records/0` | ✅ 已验证 |
| 4 | 创建 Todo | `POST /todo/v1/user/records` | ✅ 已验证 |
| 5 | 更新标题 | `POST /todo/v1/user/records/{id}/update` | ✅ 已验证 |
| 6 | 完成 (isFinish=1) | `POST /todo/v1/user/records/{id}/update` | ✅ 已验证 |
| 7 | 恢复 (isFinish=0) | `POST /todo/v1/user/records/{id}/update` | ✅ 已验证 |
| 8 | 删除 | `POST /todo/v1/user/records/{id}/delete` | ✅ 已验证 |
| 9 | 排序同步 | `POST /todo/v1/user/records/0/update` | ✅ 已验证 |
| 10 | 搜索 | 无 API（前端过滤） | ✅ 已验证 |
| 11 | 列表导航 (sidebar) | 无 API（纯 UI） | N/A |

> **所有 driver 层操作对应的 API 交互已全部捕获。**

## 轻量化 Driver 实现要点

1. **读取**: 直接用 `requests` 库发 GET 请求，带 Cookie 即可
2. **创建**: 需要构造扁平 `contentJson`（无 `entity` 嵌套），含 `createTime`, `lastModifiedTime`, `id`(自增), `customSortId`
3. **更新**: 从读取结果中提取 entity 字段，提升到 contentJson 级别，附加 record 级的 `id`, `eTag`, `type`
4. **完成**: `isFinish=1`, `markFinishTime`=当前时间戳，同时触发排序更新（从 orders 移除）
5. **恢复**: `isFinish=0`, `markFinishTime=0`，同时触发排序更新（加入 orders 最前）
6. **删除**: 只需 `prevETag` + `serviceToken`
7. **搜索**: 本地对已获取的记录做文本匹配，无需 API
8. **排序同步**: 每次创建/恢复后将 todo ID 加入 orders 最前；每次完成后从 orders 移除
