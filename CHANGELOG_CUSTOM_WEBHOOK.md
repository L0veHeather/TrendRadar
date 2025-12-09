# TrendRadar 自定义 Webhook 功能修改说明

## 修改概述

已成功为 TrendRadar 项目添加自定义 Webhook 通知功能，支持通过 Docker 部署时向 `http://ruzhu.icu/newsfortodayh1n1` 发送热点新闻通知。

## 修改的文件

### 1. `config/config.yaml`
- **位置**: 第 109 行
- **修改内容**: 在 `notification.webhooks` 部分添加了 `custom_webhook_url` 配置项
- **作用**: 支持在配置文件中设置自定义 webhook URL

```yaml
custom_webhook_url: "" # 自定义 Webhook URL（多账号用 ; 分隔，支持任意 HTTP POST 接口）
```

### 2. `main.py`
添加了三处修改：

#### a) 配置读取部分（第 389-399 行）
- **修改内容**: 添加 `CUSTOM_WEBHOOK_URL` 配置读取逻辑
- **作用**: 从环境变量或配置文件读取自定义 webhook URL，并在日志中显示配置来源

```python
# 自定义Webhook配置
config["CUSTOM_WEBHOOK_URL"] = os.environ.get("CUSTOM_WEBHOOK_URL", "").strip() or webhooks.get(
    "custom_webhook_url", ""
)

if config["CUSTOM_WEBHOOK_URL"]:
    accounts = parse_multi_account_config(config["CUSTOM_WEBHOOK_URL"])
    count = min(len(accounts), max_accounts)
    custom_source = "环境变量" if os.environ.get("CUSTOM_WEBHOOK_URL") else "配置文件"
    notification_sources.append(f"自定义Webhook({custom_source}, {count}个账号)")
```

#### b) 通知发送部分（第 3969-3981 行）
- **修改内容**: 在 `send_to_notifications` 函数中添加自定义 webhook 发送逻辑
- **作用**: 支持多账号自定义 webhook 推送

```python
# 发送到自定义Webhook（多账号）
custom_urls = parse_multi_account_config(CONFIG["CUSTOM_WEBHOOK_URL"])
if custom_urls:
    custom_urls = limit_accounts(custom_urls, max_accounts, "自定义Webhook")
    custom_results = []
    for i, url in enumerate(custom_urls):
        if url:
            account_label = f"账号{i+1}" if len(custom_urls) > 1 else ""
            result = send_to_custom_webhook(
                url, report_data, report_type, update_info_to_send, proxy_url, mode, account_label
            )
            custom_results.append(result)
    results["custom_webhook"] = any(custom_results) if custom_results else False
```

#### c) 发送函数实现（第 4902-4986 行）
- **修改内容**: 添加 `send_to_custom_webhook` 函数
- **作用**: 实现向自定义 webhook 发送 JSON 格式数据的功能

**功能特点**:
- 支持分批发送大量数据
- 发送 JSON 格式的结构化数据
- 包含报告类型、时间戳、批次信息、文本内容和统计数据
- 支持代理配置
- 2xx 状态码即视为成功
- 批次间自动间隔，避免请求过快

### 3. `docker/docker-compose.yml`
- **位置**: 第 55-56 行
- **修改内容**: 添加 `CUSTOM_WEBHOOK_URL` 环境变量支持
- **作用**: 允许通过环境变量配置自定义 webhook URL

```yaml
# 自定义Webhook配置
- CUSTOM_WEBHOOK_URL=${CUSTOM_WEBHOOK_URL:-}
```

### 4. `docker/.env`
添加了两处修改：

#### a) 配置项定义（第 89-92 行）
- **修改内容**: 添加 `CUSTOM_WEBHOOK_URL` 配置项并设置默认值
- **作用**: 提供配置示例和说明

```bash
# 自定义 Webhook 推送配置（多账号用 ; 分隔）
# 支持任意 HTTP POST 接口，将发送 JSON 格式数据
CUSTOM_WEBHOOK_URL=http://ruzhu.icu/newsfortodayh1n1
```

#### b) 启用通知（第 8 行）
- **修改内容**: 将 `ENABLE_NOTIFICATION` 设置为 `true`
- **作用**: 确保通知功能已启用

```bash
ENABLE_NOTIFICATION=true
```

## 新增文件

### 1. `CUSTOM_WEBHOOK_GUIDE.md`
- **作用**: 详细的自定义 Webhook 配置和使用指南
- **内容**: 
  - 配置方法（环境变量和配置文件）
  - 多账号支持说明
  - 数据格式详解
  - Docker 部署示例
  - 接口要求
  - 故障排查
  - 示例接收服务器代码

### 2. `QUICK_SETUP.md`
- **作用**: 快速配置指南
- **内容**:
  - 一键配置步骤
  - 完整的 .env 配置示例
  - 推送数据格式说明
  - 常见问题解答

## 功能特性

### 1. 多账号支持
- 支持配置多个自定义 webhook URL
- 使用分号 `;` 分隔多个 URL
- 自动限制最大账号数（默认 3 个）

### 2. 灵活配置
- 支持环境变量配置（优先级更高）
- 支持配置文件配置
- 环境变量和配置文件可以混合使用

### 3. 数据格式
发送的 JSON 数据包含：
- `report_type`: 报告类型
- `timestamp`: 推送时间（北京时间）
- `mode`: 运行模式
- `batch_index`: 批次索引
- `total_batches`: 总批次数
- `content`: 格式化的文本内容（Markdown）
- `data`: 结构化统计数据
  - `total_keywords`: 关键词总数
  - `total_new_count`: 新增新闻总数
  - `failed_platforms`: 失败平台列表
- `update_info`: 版本更新信息（可选）

### 4. 分批发送
- 自动将大量数据分批发送
- 批次间自动间隔（默认 3 秒）
- 避免单次请求数据过大

### 5. 错误处理
- 详细的日志输出
- 2xx 状态码视为成功
- 发送失败时记录错误信息
- 支持超时控制（30 秒）

## 使用方法

### 快速开始

1. 确保 `docker/.env` 文件中已配置：
```bash
ENABLE_NOTIFICATION=true
CUSTOM_WEBHOOK_URL=http://ruzhu.icu/newsfortodayh1n1
```

2. 启动 Docker 容器：
```bash
cd docker
docker-compose up -d
```

3. 查看日志验证：
```bash
docker logs -f trend-radar
```

### 预期日志输出

```
通知渠道配置来源: 自定义Webhook(环境变量, 1个账号)
每个渠道最大账号数: 3
自定义Webhook消息分为 1 批次发送 [当日汇总]
发送自定义Webhook第 1/1 批次，大小：1234 字节 [当日汇总]
自定义Webhook第 1/1 批次发送成功 [当日汇总]，状态码：200
自定义Webhook所有 1 批次发送完成 [当日汇总]
```

## 测试建议

1. **测试 webhook 接口**:
```bash
curl -X POST http://ruzhu.icu/newsfortodayh1n1 \
  -H "Content-Type: application/json" \
  -d '{"test": "data", "timestamp": "2025-12-09 10:42:00"}'
```

2. **查看实时日志**:
```bash
docker logs -f trend-radar | grep "自定义Webhook"
```

3. **手动触发一次推送**:
```bash
docker exec -it trend-radar python main.py
```

## 兼容性

- ✅ 与现有通知渠道（飞书、钉钉、企业微信等）完全兼容
- ✅ 支持与其他通知渠道同时使用
- ✅ 不影响现有配置和功能
- ✅ 向后兼容，不配置时不影响原有功能

## 注意事项

1. **URL 格式**: 必须是完整的 HTTP/HTTPS URL
2. **接口要求**: 接口需要支持 POST 请求并接受 JSON 数据
3. **响应时间**: 建议接口在 30 秒内响应
4. **成功标准**: 返回 2xx 状态码即视为成功
5. **安全性**: 请勿公开 webhook URL，建议添加认证机制

## 后续优化建议

1. 添加重试机制
2. 支持自定义请求头（如认证 token）
3. 支持自定义请求体格式
4. 添加请求签名验证
5. 支持异步发送

## 相关文档

- `CUSTOM_WEBHOOK_GUIDE.md` - 详细配置指南
- `QUICK_SETUP.md` - 快速配置指南
- `config/config.yaml` - 配置文件示例
- `docker/.env` - 环境变量配置

## 总结

通过以上修改，TrendRadar 现在完全支持自定义 Webhook 通知功能。用户只需在 `docker/.env` 文件中设置 `CUSTOM_WEBHOOK_URL=http://ruzhu.icu/newsfortodayh1n1`，即可实现热点新闻的自动推送。

该功能具有以下优势：
- ✅ 配置简单，一行配置即可启用
- ✅ 功能强大，支持多账号、分批发送
- ✅ 数据丰富，提供结构化 JSON 数据
- ✅ 兼容性好，不影响现有功能
- ✅ 易于调试，详细的日志输出
