# 训记APP API调用说明

## 接口信息
- **Base URL**: `https://trains.xunjiapp.cn`
- **Method**: `POST`
- **Path**: `/api_trains_for_llm`
- **返回**: gzip JSON，核心数据在 `res` 字段
- **说明**: `apikey` 的申请与读取属于会员专属能力

## 鉴权方式（四种任选其一）
- `Authorization: Bearer <YOUR_TUNJI_API_KEY>`
- `x-api-key: <YOUR_TUNJI_API_KEY>`
- body 里带 `apikey` 字段
- query 里带 `apikey` 参数

## 必填参数
- `datestr`: 字符串，格式 `YYYY-MM-DD`

## 推荐请求示例

```http
POST https://trains.xunjiapp.cn/api_trains_for_llm
Authorization: Bearer <YOUR_TUNJI_API_KEY>
Content-Type: application/json

{
  "datestr": "2026-04-02"
}
```

## 返回格式
- 成功：`{"success": true, "res": [...]}`
- `res` 是数组，每项是一条训练文本
- 格式示例：`260402,id:123456,胸部训练,train_time:1744010000000-1744013600000,状态不错,1.卧推,1组,60kg,10次`
  - `id:123456` — 训练记录的 `localid`，后续写回时可用
  - `train_time:start-end` — 训练开始和结束时间戳，建议保留
- 鉴权失败：`apikey missing` / `apikey invalid`
- 频率限制：同一训练日90秒内只能读取一次，返回 `too frequent, retry after 90s`

## 使用注意事项
- `apikey` 放在 `Authorization: Bearer ...`
- `datestr` 必须按 `YYYY-MM-DD` 传
- 解析时读取 `res` 数组
- 保留每条里的 `id:...` 和 `train_time:...`
- **数据缓存在本地，不要重复调用API**（90秒频率限制）
- 缓存目录：`<DATA_DIR>/tunji_cache/{date}.json`
- 缓存格式需包含 `source: "api_trains_for_llm"` 字段标识

## 缓存格式示例

```json
{
  "source": "api_trains_for_llm",
  "date": "2026-04-17",
  "timestamp": "2026-04-18T12:00:00",
  "data": {
    "success": true,
    "res": ["260417,id:xxx,背部与腿部训练,..."]
  }
}
```