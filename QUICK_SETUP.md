# 快速配置：使用 ntfy (http://ruzhu.icu)

## 配置说明

由于目标地址 `http://ruzhu.icu` 是 ntfy 服务，请使用如下配置以获得最佳体验。

### 1. 编辑 Docker 环境变量文件

打开 `docker/.env` 文件，修改以下配置：

```bash
# 启用通知功能
ENABLE_NOTIFICATION=true

# ============================================
# ntfy 配置 (推荐)
# ============================================

# ntfy 服务器地址
NTFY_SERVER_URL=http://ruzhu.icu

# ntfy 主题 (URL 最后一部分)
NTFY_TOPIC=newsfortodayh1n1

# ============================================
# (可选) 自定义 Webhook 配置
# ============================================
# 如果使用 ntfy，建议注释掉下面这一行，避免重复或格式错误
# CUSTOM_WEBHOOK_URL=...
```

### 2. 重启服务

```bash
cd docker
docker-compose down
docker-compose up -d
```

### 3. 验证

查看日志：

```bash
docker logs -f trend-radar
```

## 为什么使用 ntfy 配置而不使用自定义 Webhook?

| 特性 | ntfy 原生配置 | 自定义 Webhook |
|------|--------------|----------------|
| **协议** | ntfy API | 通用 JSON POST |
| **Markdown** | ✅ 原生支持 | 取决于接收端 |
| **优先级** | ✅ 支持 | ❌ 不支持 |
| **标签/Emoji** | ✅ 支持 | ❌ 不支持 |
| **标题** | ✅ 独立字段 | ❌ 混在内容中 |
| **适用场景** | ntfy 服务 | 自研后端/其他服务 |

因此，对于 `http://ruzhu.icu/newsfortodayh1n1`，使用 ntfy 配置是最佳选择。
