# 自定义 Webhook 通知配置指南

## 概述

TrendRadar 现已支持自定义 Webhook 通知功能，允许您将热点新闻推送到任意 HTTP POST 接口。

## 配置方法

### 方法一：通过环境变量配置（推荐用于 Docker 部署）

编辑 `docker/.env` 文件，设置 `CUSTOM_WEBHOOK_URL`：

```bash
# 自定义 Webhook 推送配置（多账号用 ; 分隔）
# 支持任意 HTTP POST 接口，将发送 JSON 格式数据
CUSTOM_WEBHOOK_URL=http://ruzhu.icu/newsfortodayh1n1
```

### 方法二：通过配置文件配置

编辑 `config/config.yaml` 文件，在 `notification.webhooks` 部分添加：

```yaml
notification:
  webhooks:
    custom_webhook_url: "http://ruzhu.icu/newsfortodayh1n1"
```

## 多账号支持

如果需要同时推送到多个自定义 webhook，使用分号 `;` 分隔：

```bash
CUSTOM_WEBHOOK_URL=http://webhook1.example.com;http://webhook2.example.com;http://webhook3.example.com
```

## 数据格式

自定义 Webhook 将接收 JSON 格式的 POST 请求，数据结构如下：

```json
{
  "report_type": "当日汇总",
  "timestamp": "2025-12-09 10:42:00",
  "mode": "daily",
  "batch_index": 1,
  "total_batches": 1,
  "content": "📊 TrendRadar 热点分析报告...",
  "data": {
    "total_keywords": 15,
    "total_new_count": 23,
    "failed_platforms": []
  },
  "update_info": {
    "has_update": false
  }
}
```

### 字段说明

- `report_type`: 报告类型（如 "当日汇总"、"实时增量" 等）
- `timestamp`: 推送时间戳（北京时间）
- `mode`: 运行模式（daily/incremental/current）
- `batch_index`: 当前批次索引（从 1 开始）
- `total_batches`: 总批次数
- `content`: 格式化后的文本内容（Markdown 格式）
- `data`: 结构化数据
  - `total_keywords`: 关键词总数
  - `total_new_count`: 新增新闻总数
  - `failed_platforms`: 抓取失败的平台列表
- `update_info`: 版本更新信息（可选）

## Docker 部署示例

1. 编辑 `docker/.env` 文件：

```bash
# 启用通知
ENABLE_NOTIFICATION=true

# 配置自定义 Webhook
CUSTOM_WEBHOOK_URL=http://ruzhu.icu/newsfortodayh1n1
```

2. 启动 Docker 容器：

```bash
cd docker
docker-compose up -d
```

3. 查看日志确认推送成功：

```bash
docker logs -f trend-radar
```

您应该能看到类似以下的日志输出：

```
通知渠道配置来源: 自定义Webhook(环境变量, 1个账号)
自定义Webhook消息分为 1 批次发送 [当日汇总]
发送自定义Webhook第 1/1 批次，大小：1234 字节 [当日汇总]
自定义Webhook第 1/1 批次发送成功 [当日汇总]，状态码：200
自定义Webhook所有 1 批次发送完成 [当日汇总]
```

## 接口要求

您的自定义 Webhook 接口需要：

1. 支持 HTTP POST 请求
2. 接受 `Content-Type: application/json` 格式的数据
3. 返回 2xx 状态码表示成功（200-299）
4. 建议在 30 秒内响应

## 故障排查

### 推送失败

如果看到 "发送失败" 的日志：

1. 检查 URL 是否正确
2. 确认接口是否可访问
3. 查看接口返回的错误信息
4. 检查网络连接和防火墙设置

### 未收到推送

1. 确认 `ENABLE_NOTIFICATION=true`
2. 检查 `CUSTOM_WEBHOOK_URL` 是否已配置
3. 查看容器日志：`docker logs trend-radar`
4. 确认报告模式和推送条件是否满足

## 示例：简单的接收服务器

如果您需要测试，可以使用以下 Python 脚本创建一个简单的接收服务器：

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/newsfortodayh1n1', methods=['POST'])
def receive_webhook():
    data = request.json
    print(f"收到推送: {data['report_type']}")
    print(f"时间: {data['timestamp']}")
    print(f"关键词数: {data['data']['total_keywords']}")
    print(f"新增数: {data['data']['total_new_count']}")
    print(f"内容预览: {data['content'][:100]}...")
    
    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
```

## 注意事项

1. **安全性**: 请勿将 Webhook URL 公开，建议使用认证机制
2. **性能**: 大量数据可能会分批发送，注意处理 `batch_index` 和 `total_batches`
3. **超时**: 接口响应时间建议在 30 秒以内
4. **重试**: 当前版本不支持自动重试，失败后需等待下次推送

## 更多信息

- 项目地址: https://github.com/sansan0/TrendRadar
- 问题反馈: 请在 GitHub Issues 中提交
