---
name: honny-photov2
description: |
  Honny 照片生成技能 V2 - 使用 RunningHub 工作流根据文本提示词生成照片。
  支持自动优化迭代，每天首次使用自动上传参考图。
  
  触发关键词：生成照片、生成图片、照片生成、AI写真
allowed-tools:
  - read
  - write
  - edit
  - exec
allowed-edit-paths:
  - ~/.openclaw/skills/honny-photov2
  - ~/.openclaw/workspace/memory
---

# HonnyPhotoV2 Skill

使用 RunningHub Wan2.2 API 进行图生视频生成。

## 功能

| 功能 | 说明 |
|------|------|
| **文生图** | 使用参考图 + 提示词生成图片 |
| **自动优化** | 根据生成结果自动优化提示词 |
| **参考图管理** | 每天首次自动上传并缓存参考图 |

## 配置

### 环境变量

在 `~/.openclaw/skills/honny-photov2/.env` 中配置：

```bash
# RunningHub API Key
RUNNINGHUB_API_KEY=你的API密钥

# 工作流 ID（默认：文生图-参考图）
WORKFLOW_ID=2047002838944980993
```

### 获取 API Key

1. 访问 https://www.runninghub.cn
2. 登录 → 个人中心 → API
3. 创建 API Key

## 使用方法

### 基本命令

```
生成一张帅气的照片
生成一张美美的写真
帮我做一张AI照片
```

### 高级用法

```
生成照片：可爱风格的
优化提示词后再生成
```

## 自动流程

1. **检查参考图缓存**
   - 读取当天记忆中的参考图 URL
   - 如果没有，执行第2步

2. **上传参考图**（每天首次）
   - 查找用户 avatar 文件
   - 上传到 RunningHub
   - 保存 URL 到记忆

3. **生成图片**
   - 使用参考图 + 优化后的提示词
   - 调用工作流 API
   - 返回生成结果

4. **自动迭代**（可选）
   - 分析生成结果
   - 优化提示词
   - 重新生成

## 输出格式

```
🎨 照片生成成功！

📝 提示词：{优化后的提示词}
🖼️ 图片：{图片URL}

💡 优化说明：{如有优化}
```

## 注意事项

- 需要配置 RUNNINGHUB_API_KEY
- 首次使用需要提供参考图（avatar）
- 生成可能需要等待队列

---

*基于 RunningHub API v2*
